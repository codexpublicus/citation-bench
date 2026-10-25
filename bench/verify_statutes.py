# /// script
# requires-python = ">=3.13"
# dependencies = ["pypdf==6.21.1"]
# ///
"""Check statute vectors against official, human-maintained sources.

Usage:
  uv run bench/verify_statutes.py [--vectors DIR ...] [--offline] [--refresh]
      [--json OUT.json] [--md OUT.md] [--lock FILE]

A statute vector's expected citation makes several claims. This script splits them up
and checks each one it can without a person:

- span: the span starts and ends on a word boundary, holds every part as written,
  ends at the section (rule, page, amendment) as docs/protocol.md has it, and leaves
  no text that no field accounts for (`1975,` in `Ala. Code 1975, §`)
- metadata as written: the pin cite follows the span, and the year and parenthetical
  are in the text
- code: reporter_normalized is a code reporters-db's laws data has for that
  jurisdiction, or one the maintainer's conventions name (docs/protocol.md)
- form: the code as written means that code. Machine evidence is a written form that
  is the code's own abbreviation, or a citing court in the code's jurisdiction (the case
  metadata stare.pub serves, or CourtListener's API for an opinion it doesn't serve)
- existence: the section (rule, article, page, public law) exists in the official
  source for that code, and a year agrees with it
- excerpt: for a stare.pub excerpt, the case is the one the vector pins (sha256) and the
  input is its text at the recorded offset

A claim no machine source settles can be settled by a maintainer's ruling, recorded in
verification/statutes/rulings.json: one answer per written form, code, span pattern or
vector, each with its basis (`owner-ruled 2026-10-25 (A63)`). A ruled check passes with
the ruling as its source; it is checked before CourtListener's API, so a ruled form
spends no quota.

Each vector gets one verdict:

- `verified-by-source:<sources>`: every claim was checked and none failed
- `contradicted:<what>`: a check failed; a person has to look
- `unverifiable:<why>`: nothing failed, but some claim has no machine check

A verdict never changes a vector's provenance. Official sources are fetched once and
cached under .cache/statute-sources/ (gitignored); verification/statutes/sources.json
records each one's URL, retrieval date, size and SHA-256. A later run refuses a cached
copy whose hash differs from the record (--refresh refetches everything), and a source
that changed upstream since it was recorded is used as it is now, repinned, and listed
in the report.
--offline uses the cache only and reports a claim whose source isn't cached as
unverifiable. eyecite's and citare's output are never consulted.
"""

import argparse
import collections
import dataclasses
import datetime
import hashlib
import html
import io
import json
import logging
import os
import re
import ssl
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import fetch_stare
from statutes import law_kind, load_sets

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETS = (ROOT / "vectors" / "statutes", ROOT / "vectors" / "statutes-proposed")
CACHE = ROOT / ".cache" / "statute-sources"
OUT = ROOT / "verification" / "statutes"
LOCK = OUT / "sources.json"
RULINGS = OUT / "rulings.json"
# The corpora a vector's text can come from (docs/protocol.md, "Vector sources"). A
# vector from anywhere else stops the run: its excerpt and citing-court checks would
# otherwise be skipped without a word.
STARE_PUB = "stare-pub"
COURTLISTENER_SAMPLE = "courtlistener-10pct"
USER_AGENT = (
    "Mozilla/5.0 (compatible; citation-bench statute verifier; "
    "+https://github.com/codexpublicus/citation-bench)"
)

# Pinned editions. Changing one is a deliberate edit, and the lock records the hashes.
USCODE_EDITION = "2024"  # GovInfo's annual U.S. Code edition (USCODE-2024-title<N>)
ECFR_DATE = "2026-10-01"  # eCFR point-in-time structure
USSG_MANUAL = "2025"  # U.S. Sentencing Commission Guidelines Manual
REPORTERS_DB_TAG = "v3.2.67"

# Conventions the maintainer accepted on 2026-10-18 (docs/protocol.md, "Statute and
# court-rule citations") for codes reporters-db doesn't have: code -> jurisdiction.
CONVENTION_CODES = {
    "Fed. R. Civ. P.": "United States",
    "Mich. Ct. R.": "Michigan",
    "U.S. Const.": "United States",
    "Fed. Reg.": "United States",
    "U.S.S.G.": "United States",
}
# Written forms the conventions map to a code: written (canonical) -> code.
CONVENTION_FORMS = {"usca": "U.S.C.", "fedreg": "Fed. Reg.", "ussg": "U.S.S.G."}

# Federal rule sets in the U.S. Code appendices: code -> (title, set heading).
FEDERAL_RULES = {
    "Fed. R. Civ. P.": ("28", "FEDERAL RULES OF CIVIL PROCEDURE"),
    "Fed. R. Evid.": ("28", "FEDERAL RULES OF EVIDENCE"),
    "Fed. R. App. P.": ("28", "FEDERAL RULES OF APPELLATE PROCEDURE"),
    "Fed. R. Crim. P.": ("18", "FEDERAL RULES OF CRIMINAL PROCEDURE"),
}

# Texas Legislative Council code abbreviations, for building a chapter's URL. The page
# itself is the check: it has to hold the section.
TEXAS_CODES = {
    "Penal": "PE",
    "PENAL": "PE",
    "Fam.": "FA",
    "Prop.": "PR",
    "Gov't": "GV",
    "Health & Safety": "HS",
    "Bus. & Com.": "BC",
    "Civ. Prac. & Rem.": "CP",
    "Educ.": "ED",
    "Lab.": "LA",
    "Transp.": "TN",
    "Ins.": "IN",
    "Tax": "TX",
    "Fin.": "FI",
    "Occ.": "OC",
    "Water": "WA",
    "Agric.": "AG",
    "Alco. Bev.": "AL",
    "Elec.": "EL",
    "Hum. Res.": "HR",
    "Loc. Gov't": "LG",
    "Nat. Res.": "NR",
    "Parks & Wild.": "PW",
    "Util.": "UT",
    "Est.": "ES",
}

# California's bulk data: the session archive holds the whole of every code in
# LAW_SECTION_TBL.dat, near the start of the zip. Only that prefix is fetched.
CA_PUBINFO = "2025"
CA_PUBINFO_PREFIX = 32 * 1024 * 1024
# California code -> its code in leginfo's LAW_SECTION_TBL (law_code column).
CA_CODES = {
    "Cal. Pen. Code": "PEN",
    "Cal. Civ. Proc. Code": "CCP",
    "Cal. Evid. Code": "EVID",
    "Cal. Civ. Code": "CIV",
}

# Hosts that send their certificate without the intermediate that signed it. The
# intermediate is fetched (and pinned) from the URL the certificate itself names in
# its Authority Information Access field; verification is otherwise the usual one.
INTERMEDIATE_CERTS = {
    "www.cga.ct.gov": "http://certificates.godaddy.com/repository/gdig2.crt",
}
# Hosts that offer only a cipher outside OpenSSL's default list (RSA key exchange,
# no forward secrecy): host -> the cipher, added to the defaults for that host only.
EXTRA_CIPHERS = {"www.jud.ct.gov": "AES256-SHA256"}
# Hosts whose robots.txt or API limits ask for a delay between requests, in seconds.
# CourtListener throttles this account's token at 5 requests a minute.
CRAWL_DELAY = {
    "legislature.vermont.gov": 30,
    "www.courtlistener.com": 12,
    "legislation.nysenate.gov": 1,
}
# HTTP 429: wait (Retry-After, or the seconds CourtListener's message names, or a
# doubling delay from 15 seconds) and try again, this many times.
RATE_LIMIT_RETRIES = 6
# A wait longer than this (CourtListener's hourly quota asks for about 20 minutes)
# ends requests to that host for the run: its uncached checks are recorded as not run.
RATE_LIMIT_MAX_WAIT = 120

# Keyed APIs. Each key comes from the environment only (the operator's mise env
# decrypts it from .mise/config.toml); with it unset the check is recorded as not run.
# A key never goes into a URL that is cached, pinned, logged or reported.
COURTLISTENER_API = "https://www.courtlistener.com/api/rest/v4/"
COURTLISTENER_TOKEN_ENV = "COURTLISTENER_API_TOKEN"
NY_OPENLEG_API = "https://legislation.nysenate.gov/api/3/laws/"
NY_OPENLEG_KEY_ENV = "NY_OPENLEG_API_KEY"
# NY Open Legislation law ids (`/api/3/laws` lists them).
NY_LAWS = {
    "N.Y. Penal Law": "PEN",
    "N.Y. Family Ct Act": "FCT",
    "N.Y. Judiciary Law": "JUD",
}
# CourtListener court jurisdiction codes for federal courts (the courts endpoint's
# `jurisdiction`); a state court's state is the state its name gives.
CL_FEDERAL = {"F", "FD", "FB", "FBP", "FS"}
CL_STATE = {"S", "SA", "ST", "SS"}
US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois",
    "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
    "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah",
    "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]  # fmt: skip

# Why there's no machine check yet, per code with no source wired in. Facts about the
# sources as found on 2026-10-18; see verification/statutes/README.md.
NO_SOURCE = {
    "Ga. Code Ann.": "Georgia's official code is online through LexisNexis; not used",
    "Tenn. Code Ann.": "Tennessee's official code is online through LexisNexis; not used",
    "Ark. Code Ann.": "Arkansas's official code is online through LexisNexis; not used",
    "Okla. Stat.": "the robots.txt of both oscn.net and oklegislature.gov disallows "
    "every path to every crawler",
    "Pa. Stat. Ann.": "Purdon's title and section numbers have no official per-section "
    "source; palegis.us indexes unconsolidated statutes by act",
    "N.Y. Penal Law": "nysenate.gov answered HTTP 403 to scripted requests; its Open "
    f"Legislation API needs a key, and {NY_OPENLEG_KEY_ENV} was unset in this run",
    "N.Y. Judiciary Law": "as N.Y. Penal Law",
    "N.Y. Family Ct Act": "as N.Y. Penal Law",
    "N.Y. Comp. Codes R. & Regs.": "the official NYCRR is online through Thomson Reuters "
    "Westlaw; not used",
    "N.J. Admin. Code": "the N.J.A.C. is online through LexisNexis; not used",
    "Ohio Const.": "codes.ohio.gov, the only official text, has a robots.txt that "
    "disallows every path to every crawler",
    "Mich. Ct. R.": "courts.michigan.gov, which publishes the rules, has a robots.txt "
    "that disallows every path to every crawler",
    "Pa. R. Civ. P.": "pacodeandbulletin.gov, which publishes the rules (231 Pa. Code), "
    "has a robots.txt that disallows every path to every crawler",
}

# --- fetching, caching and pinning -------------------------------------------------


class SourceUnavailable(Exception):
    pass


class SourceChanged(Exception):
    pass


class RateLimitExhausted(SourceUnavailable):
    """The host's quota is spent for this run; its uncached checks aren't run."""


class RateLimited(Exception):
    """HTTP 429; wait is the seconds the server asked for, if it said."""

    def __init__(self, url, wait=None):
        super().__init__(f"{url}: HTTP 429")
        self.wait = wait


def _retry_after(headers, body):
    """Seconds to wait from a 429's Retry-After header or CourtListener's message."""
    value = (headers or {}).get("Retry-After")
    if value and value.strip().isdigit():
        return int(value)
    m = re.search(rb"available in (\d+) seconds?", body or b"")
    return int(m.group(1)) if m else None


@dataclasses.dataclass
class Fetcher:
    """Fetches sources once, caches them, and pins each by SHA-256 in a lock file."""

    cache: Path
    lock: dict
    offline: bool = False
    refresh: bool = False
    opener: object = (
        None  # callable(url, follow[, headers=, data=]) -> (status, body, location)
    )
    used: dict = dataclasses.field(default_factory=dict)
    changed: dict = dataclasses.field(
        default_factory=dict
    )  # key -> sha256 it was pinned at
    _last: dict = dataclasses.field(default_factory=dict)  # host -> last request time
    max_wait: float = RATE_LIMIT_MAX_WAIT
    exhausted: set = dataclasses.field(default_factory=set)  # hosts out of quota

    def _path(self, key):
        return self.cache / hashlib.sha256(key.encode()).hexdigest()[:32]

    def get(self, url, follow=True, *, key=None, headers=None, data=None, query=None):
        """(status, body) for url, with redirects followed or not.

        Without follow, the body is the redirect's Location (empty if none). key names
        the request in the cache and the lock when it isn't a plain GET of url (a byte
        range, a form post); it defaults to url. query holds secret query parameters
        (an API key): they're added to the request only, never to the cache key, the
        lock, the cached metadata or an error message.
        """
        key = key or url
        host = urllib.parse.urlsplit(url).hostname
        if host in INTERMEDIATE_CERTS:
            # Pinned with every source from that host, cached or not.
            self.get(INTERMEDIATE_CERTS[host])
        path = self._path(key)
        meta_path = path.with_suffix(".json")
        cached = path.exists() and meta_path.exists() and not self.refresh
        if cached:
            body = path.read_bytes()
            meta = json.loads(meta_path.read_text())
        elif self.offline:
            raise SourceUnavailable(f"not cached (offline): {key}")
        else:
            status, body, location = self._open(url, follow, headers, data, query)
            meta = {
                "url": url,
                "retrieved": datetime.date.today().isoformat(),
                "status": status,
            }
            if location:
                meta["location"] = location
            if not follow:
                body = (location or "").encode()
            if status >= 500:
                # A server error says nothing about the source: neither cached nor
                # pinned, so the next run asks again.
                return status, body
            self.cache.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            meta_path.write_text(json.dumps(meta))
        digest = hashlib.sha256(body).hexdigest()
        # A source repinned earlier in this run is checked against its new pin.
        pinned = self.used.get(key) if key in self.changed else self.lock.get(key)
        if pinned and pinned["sha256"] != digest:
            if cached:
                raise SourceChanged(
                    f"{key}: the cached copy's sha256 {digest[:12]} differs from the "
                    f"pinned {pinned['sha256'][:12]} (rerun with --refresh to refetch)"
                )
            # The source changed upstream since it was pinned: use what it says now,
            # record the new hash and report the change.
            self.changed[key] = pinned["sha256"]
            pinned = None
        if not pinned or self.refresh:
            pinned = {**meta, "sha256": digest, "bytes": len(body)}
            if pinned.get("url") == key:
                pinned.pop("url")
        self.used[key] = pinned
        return meta["status"], body

    def _open(self, url, follow, headers, data, query=None):
        """One request, retried after an HTTP 429 as the server asks."""
        host = urllib.parse.urlsplit(url).hostname
        if host in self.exhausted:
            raise RateLimitExhausted(f"{host}: rate limit reached earlier in this run")
        target = url
        if query:
            target += ("&" if "?" in url else "?") + urllib.parse.urlencode(query)
        delay = 15
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                try:
                    result = self._open_once(target, follow, headers, data)
                except SourceUnavailable:
                    if not query:
                        raise
                    # The message names the URL with the secret in it: drop both.
                    raise SourceUnavailable(f"{url}: unreachable") from None
                if result[0] != 429:
                    return result
                wait = None
            except RateLimited as e:
                wait = e.wait
            if attempt == RATE_LIMIT_RETRIES:
                break
            wait = wait if wait is not None else delay
            delay *= 2
            if wait > self.max_wait:
                self.exhausted.add(host)
                print(
                    f"verify_statutes: {host}: HTTP 429 asks for {wait} s; "
                    "no more requests to it this run",
                    file=sys.stderr,
                )
                raise RateLimitExhausted(f"{host}: HTTP 429, {wait} s wait")
            print(
                f"verify_statutes: {host}: HTTP 429, waiting {wait} s", file=sys.stderr
            )
            time.sleep(wait)
        raise SourceUnavailable(f"{url}: HTTP 429 after {RATE_LIMIT_RETRIES} retries")

    def _open_once(self, url, follow, headers, data):
        if self.opener:
            if headers or data:
                return self.opener(url, follow, headers=headers, data=data)
            return self.opener(url, follow)
        host = urllib.parse.urlsplit(url).hostname
        context = None
        if host in INTERMEDIATE_CERTS or host in EXTRA_CIPHERS:
            context = ssl.create_default_context()
        if host in INTERMEDIATE_CERTS:
            status, der = self.get(INTERMEDIATE_CERTS[host])
            if status != 200:
                raise SourceUnavailable(f"{INTERMEDIATE_CERTS[host]}: HTTP {status}")
            context.load_verify_locations(cadata=der)
        if host in EXTRA_CIPHERS:
            context.set_ciphers(f"DEFAULT:{EXTRA_CIPHERS[host]}")
        delay = CRAWL_DELAY.get(host, 0) - (
            time.monotonic() - self._last.get(host, -1e9)
        )
        if delay > 0:
            time.sleep(delay)
        try:
            return _urlopen(url, follow, headers, data, context)
        finally:
            self._last[host] = time.monotonic()


def _urlopen(url, follow, headers=None, data=None, context=None):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    handlers = [] if follow else [NoRedirect()]
    if context is not None:
        handlers.append(urllib.request.HTTPSHandler(context=context))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(
        url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})}
    )
    try:
        with opener.open(req, timeout=300) as r:
            return r.status, r.read(), r.headers.get("Location")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimited(url, _retry_after(e.headers, e.read())) from None
        return e.code, e.read() if follow else b"", e.headers.get("Location")
    except urllib.error.URLError as e:
        raise SourceUnavailable(f"{url}: {e.reason}") from e


def page_text(body):
    """An HTML page's visible text, whitespace collapsed."""
    s = body.decode("utf-8", errors="replace")
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", s.replace("\xa0", " "))


# --- sources -----------------------------------------------------------------------

MODS = "{http://www.loc.gov/mods/v3}"


class Sources:
    """Lookups against each official source, parsed once per run."""

    def __init__(self, fetcher, stare=None, rulings=None):
        self.f = fetcher
        self._memo = {}
        self.page_texts = {}  # url -> visible text of an official page that held a section
        # stare.pub's case files: callable(case entry) -> bytes, as fetch_stare.Stare.case
        self._stare = stare
        self.rulings = rulings or Rulings()

    def _once(self, key, build):
        if key not in self._memo:
            self._memo[key] = build()
        return self._memo[key]

    # reporters-db laws data (Free Law Project, maintained by hand)
    def laws(self):
        url = (
            "https://raw.githubusercontent.com/freelawproject/reporters-db/"
            f"{REPORTERS_DB_TAG}/reporters_db/data/laws.json"
        )
        return self._once("laws", lambda: json.loads(self.f.get(url)[1]))

    # GovInfo U.S. Code, granule metadata (MODS) per title
    def uscode(self, title):
        def build():
            url = (
                f"https://www.govinfo.gov/metadata/pkg/USCODE-{USCODE_EDITION}-title{title}"
                "/mods.xml"
            )
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return parse_uscode_mods(body)

        return self._once(("uscode", title), build)

    # eCFR structure per title, at a pinned date
    def ecfr(self, title):
        def build():
            url = f"https://www.ecfr.gov/api/versioner/v1/structure/{ECFR_DATE}/title-{title}.json"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return ecfr_sections(json.loads(body))

        return self._once(("ecfr", title), build)

    # GovInfo Statutes at Large, package metadata per volume
    def statute(self, volume):
        def build():
            url = f"https://www.govinfo.gov/metadata/pkg/STATUTE-{volume}/mods.xml"
            status, body = self.f.get(url)
            if status != 200:
                return None
            return parse_statute_mods(body)

        return self._once(("statute", volume), build)

    # GovInfo link service: Federal Register volume and page to the issue
    def fr_issue(self, volume, page):
        url = f"https://www.govinfo.gov/link/fr/{volume}/{page}"
        status, body = self.f.get(url, follow=False)
        m = re.search(r"/pkg/FR-(\d{4})-(\d\d)-(\d\d)/", body.decode())
        return (url, m.group(0).strip("/") if m else None, m and m.group(1), status)

    # U.S. Sentencing Commission, Guidelines Manual contents
    def ussg(self):
        def build():
            url = f"https://www.ussc.gov/guidelines/{USSG_MANUAL}-guidelines-manual"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return set(re.findall(r"§\s?(\d[A-Z]\d\.\d+[A-Za-z]?)\.", page_text(body)))

        return self._once("ussg", build)

    # GPO, The Constitution of the United States (H. Doc. 110-50)
    def constitution(self):
        def build():
            url = "https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/html/CDOC-110hdoc50.htm"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return parse_constitution(body.decode("utf-8", errors="replace"))

        return self._once("constitution", build)

    # stare.pub: a CAP case or a CourtListener record, the JSON stare.pub serves, which
    # has to be the bytes the vector pins (its source's sha256).
    def stare_case(self, src):
        """(address, record, sha256 matches the vector's pin) for a stare.pub source."""
        entry = fetch_stare.source_case(src)
        key = src.get("url") if src.get("source") == "cl" else None
        key = key or f"{src['data']}#{src['member']}"
        if key not in self._memo:
            self._memo[key] = self._stare_bytes(entry)
        body = self._memo[key]
        digest = hashlib.sha256(body).hexdigest()
        self.f.used[key] = {
            "bytes": len(body),
            "retrieved": datetime.date.today().isoformat(),
            "sha256": digest,
            "status": 200,
        }
        return key, json.loads(body), digest == src.get("sha256")

    def _stare_bytes(self, entry):
        if self._stare is None:
            stare = fetch_stare.Stare(fetch_stare.VERSION, cache=self.f.cache.parent)
            if self.f.offline:
                cached = stare.cache / (
                    f"cap/{entry['slug']}/{entry['folder']}/{entry['case']}.json"
                    if entry["source"] == "cap"
                    else f"cl/{entry['ref']}.json"
                )
                if not cached.exists():
                    raise SourceUnavailable(f"not cached (offline): {entry}")
            self._stare = stare.case
        try:
            return self._stare(entry)
        except (OSError, KeyError, SystemExit) as e:
            raise SourceUnavailable(f"stare.pub {entry}: {e}") from e

    def page(self, url):
        return self.f.get(url)

    # A PDF's text, extracted once per file and kept next to the cached copy
    def pdf(self, url):
        def build():
            status, body = self.f.get(url)
            if status in (404, 410):
                return None
            if status != 200 or not body.startswith(b"%PDF"):
                raise SourceUnavailable(f"{url}: HTTP {status}, not a PDF")
            digest = hashlib.sha256(body).hexdigest()
            path = self.f.cache / f"{digest[:32]}.pdf.txt"
            if path.exists():
                return path.read_text()
            text = pdf_text(body)
            path.write_text(text)
            return text

        return self._once(("pdf", url), build)

    # California Legislative Counsel, leginfo bulk data (pubinfo): every code section
    def ca_sections(self):
        def build():
            url = (
                f"https://downloads.leginfo.legislature.ca.gov/pubinfo_{CA_PUBINFO}.zip"
            )
            last = CA_PUBINFO_PREFIX - 1
            status, body = self.f.get(
                url, key=f"{url}#bytes=0-{last}", headers={"Range": f"bytes=0-{last}"}
            )
            if status not in (200, 206):
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return parse_ca_law_sections(zip_member(body, "LAW_SECTION_TBL.dat"))

        return self._once("ca", build)

    # Connecticut General Assembly: a title's chapters and their section ranges
    def ct_title(self, title):
        def build():
            url = f"https://www.cga.ct.gov/current/pub/title_{ct_title_file(title)}.htm"
            status, body = self.f.get(url)
            if status in (404, 410):
                return None
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return parse_ct_title(body.decode("utf-8", errors="replace"))

        return self._once(("ct", title), build)

    # Hawaii State Legislature, HRS volumes on its data host
    def hi_volumes(self):
        def build():
            url = "https://data.capitol.hawaii.gov/hrscurrent/"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            found = re.findall(
                r"(Vol\d+_Ch(\d+[A-Z]*)-(\d+[A-Z]*))/", body.decode("utf-8", "replace")
            )
            return list(dict.fromkeys(found))

        return self._once("hi", build)

    # Vermont General Assembly: a title's chapters, and a chapter's sections
    def vt_chapters(self, title):
        def build():
            url = f"https://legislature.vermont.gov/statutes/title/{title}"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return parse_vt_title(body.decode("utf-8", "replace"), title)

        return self._once(("vt", title), build)

    def vt_chapter(self, title, chapter):
        def build():
            url = f"https://legislature.vermont.gov/statutes/chapter/{title}/{chapter}"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return url, parse_vt_chapter(
                body.decode("utf-8", "replace"), title, chapter
            )

        return self._once(("vt", title, chapter), build)

    # NM Compilation Commission (nmonesource.com): NMSA chapter -> document item
    def nm_chapters(self):
        def build():
            base = "https://nmonesource.com/nmos/nmsa-unanno/en/nav_date.do"
            items, pages, seen = {}, [None], set()
            while pages:
                page = pages.pop(0)
                url = (
                    f"{base}?iframe=true"
                    if page is None
                    else (f"{base}?page={page}&iframe=true")
                )
                status, body = self.f.get(url)
                if status != 200:
                    raise SourceUnavailable(f"{url}: HTTP {status}")
                text = body.decode("utf-8", "replace")
                items.update(parse_nm_nav(text))
                for n in re.findall(r"nav_date\.do\?page=(\d+)", text):
                    if n not in seen:
                        seen.add(n)
                        pages.append(n)
            return items

        return self._once("nm", build)

    # Louisiana Legislature: a Revised Statutes title's sections and document ids
    def la_title(self, title):
        def build():
            url = "https://www.legis.la.gov/legis/Laws_Toc.aspx?folder=75&level=Parent"
            status, body = self.f.get(url)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            form = la_postback(body.decode("utf-8", "replace"), f"TITLE {title}")
            if form is None:
                return None
            status, body = self.f.get(
                url, key=f"{url}#postback=TITLE {title}", data=form
            )
            if status != 200:
                raise SourceUnavailable(f"{url} (TITLE {title}): HTTP {status}")
            return parse_la_toc(body.decode("utf-8", "replace"))

        return self._once(("la", title), build)

    # CourtListener REST API v4: an opinion's court, by opinion -> cluster -> docket.
    # None when COURTLISTENER_API_TOKEN is unset (the check isn't run).
    def cl_court(self, opinion):
        token = os.environ.get(COURTLISTENER_TOKEN_ENV)
        if not token:
            return None
        headers = {"Authorization": f"Token {token}"}

        def get(url):
            if not url.startswith(COURTLISTENER_API):
                raise SourceUnavailable(f"not a CourtListener API URL: {url}")
            status, body = self.f.get(url, headers=headers)
            if status != 200:
                raise SourceUnavailable(f"{url}: HTTP {status}")
            return json.loads(body)

        cluster = get(f"{COURTLISTENER_API}opinions/{int(opinion)}/?fields=cluster")
        docket = get(f"{cluster['cluster']}?fields=docket")
        court_id = get(f"{docket['docket']}?fields=court_id")["court_id"]
        return self._once(
            ("cl-court", court_id),
            lambda: get(
                f"{COURTLISTENER_API}courts/{court_id}/"
                "?fields=id,full_name,jurisdiction"
            ),
        )

    # NY Open Legislation API v3: one section of a consolidated law. None when
    # NY_OPENLEG_API_KEY is unset (the check isn't run).
    def ny_law_doc(self, law, location):
        key = os.environ.get(NY_OPENLEG_KEY_ENV)
        if not key:
            return None
        url = f"{NY_OPENLEG_API}{law}/{urllib.parse.quote(location)}"
        status, body = self.f.get(url, query={"key": key})
        try:
            doc = json.loads(body)
        except ValueError:
            doc = {}
        return url, status, doc


def cl_court_jurisdiction(court):
    """The jurisdiction a CourtListener court sits in, as the vectors name it."""
    kind = court.get("jurisdiction")
    if kind in CL_FEDERAL:
        return "United States"
    if kind in CL_STATE:
        name = court.get("full_name") or ""
        for state in sorted(US_STATES, key=len, reverse=True):
            if re.search(rf"\b{state}\b", name):
                return state
    return None


def parse_uscode_mods(body):
    """{"sections": {number, ...}, "rules": {set heading: {number, ...}}} from MODS."""
    root = ET.fromstring(body)
    nodes = {}
    for ri in root.iter(MODS + "relatedItem"):
        if ri.get("type") != "constituent":
            continue
        parent = ri.find(MODS + "identifier[@type='Parent Id']")
        ti = ri.find(MODS + "titleInfo")
        nodes[ri.get("ID")] = (
            parent.text if parent is not None else None,
            (ti.findtext(MODS + "title") or "").strip() if ti is not None else "",
            (ti.findtext(MODS + "partName") or "").strip() if ti is not None else "",
        )
    sections, rules = set(), collections.defaultdict(set)
    for node_id, (parent, _title, part) in nodes.items():
        if "-app" not in node_id:
            m = re.fullmatch(r"Secs?\. (\S+)(?: to (\S+))?", part)
            if m:
                sections.add(m.group(1))
                if m.group(2):
                    sections.add(f"{m.group(1)} to {m.group(2)}")
            continue
        m = re.fullmatch(r"Rule (\S+)", part)
        if not m:
            continue
        chain, p = [], parent
        while p in nodes:
            chain.append(nodes[p][1])
            p = nodes[p][0]
        if any("SUPPLEMENTAL" in t.upper() for t in chain):
            continue
        for t in chain:
            if t.upper().startswith("FEDERAL RULES OF"):
                rules[t.upper()].add(m.group(1))
                break
    return {"sections": sections, "rules": dict(rules)}


def ecfr_sections(node, out=None):
    out = set() if out is None else out
    if node.get("type") == "section" and node.get("identifier"):
        out.add(node["identifier"])
    for child in node.get("children") or ():
        ecfr_sections(child, out)
    return out


def parse_statute_mods(body):
    """A Statutes at Large volume: its congress, and each granule's pages and law."""
    root = ET.fromstring(body)
    granules = []
    congresses = set()
    for ri in root.iter(MODS + "relatedItem"):
        if ri.get("type") != "constituent":
            continue
        ext = ri.find(MODS + "extension")
        start = ri.findtext(f"{MODS}part/{MODS}extent/{MODS}start")
        end = ri.findtext(f"{MODS}part/{MODS}extent/{MODS}end")
        if ext is None or not (start or "").isdigit():
            continue
        if not (end or "").isdigit():
            end = start
        congress = ext.findtext(MODS + "congress")
        congresses.add(congress)
        granules.append(
            {
                "id": ext.findtext(MODS + "accessId"),
                "start": int(start),
                "end": int(end),
                "date": ext.findtext(MODS + "granuleDate"),
                "class": ext.findtext(MODS + "granuleClass"),
                "congress": congress,
                "number": ext.findtext(MODS + "number"),
            }
        )
    return {"congresses": congresses - {None}, "granules": granules}


ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50}


def roman_to_int(s):
    total = 0
    for a, b in zip(s, s[1:] + " "):
        v = ROMAN[a]
        total += -v if b != " " and ROMAN.get(b, 0) > v else v
    return total


def parse_constitution(text):
    """{"article": {n: {section: clauses}}, "amendment": {n: {section: clauses}}}.

    Articles and amendments are numbered as integers; a part without sections has the
    key 0 for its own clauses. Clause counts come from GPO's bracketed clause numbers.
    """
    out = {"article": {}, "amendment": {}}
    kind, num, sec = None, None, None
    body = collections.defaultdict(str)
    for line in text.splitlines():
        m = re.match(r"\s+Article \[?([IVXL]+)\.\]?", line)
        if m:
            n = roman_to_int(m.group(1))
            if kind == "article" and n == 1 or kind == "amendment":
                kind = "amendment"
            else:
                kind = "article"
            num, sec = n, 0
            out[kind].setdefault(num, {})
            continue
        if kind is None:
            continue
        m = re.match(r"\s+Section (\d+)\.", line)
        if m:
            sec = int(m.group(1))
        body[(kind, num, sec)] += line + "\n"
    for (kind, num, sec), t in body.items():
        n = 0
        for marker in re.findall(r"\\(\d+)\\", t):
            if int(marker) == n + 1:
                n += 1
        if sec or n:
            out[kind][num][sec] = n
    return out


def pdf_text(body):
    """A PDF's text, page after page."""
    from pypdf import PdfReader  # only the network run needs it

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        reader = PdfReader(io.BytesIO(body))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:  # pypdf raises many kinds; any of them means no text
        raise SourceUnavailable(f"PDF text: {e}") from e


def zip_member(prefix, name):
    """One member of a zip archive, from the archive's first bytes (local headers)."""
    pos = 0
    while prefix[pos : pos + 4] == b"PK\x03\x04" and pos + 30 <= len(prefix):
        flag, method, _t, _d, crc, csize, _usize, nlen, xlen = struct.unpack(
            "<HHHHIIIHH", prefix[pos + 6 : pos + 30]
        )
        member = prefix[pos + 30 : pos + 30 + nlen].decode("utf-8", "replace")
        start = pos + 30 + nlen + xlen
        if flag & 8:
            raise SourceUnavailable(f"{member}: sizes follow the data; can't walk on")
        if member == name:
            if start + csize > len(prefix):
                break
            raw = prefix[start : start + csize]
            data = zlib.decompress(raw, -15) if method == 8 else raw
            if zlib.crc32(data) != crc:
                raise SourceUnavailable(f"{name}: CRC mismatch")
            return data
        pos = start + csize
    raise SourceUnavailable(f"{name} isn't within the first {len(prefix)} bytes")


def parse_ca_law_sections(dat):
    """{law_code: {section, ...}} from leginfo's LAW_SECTION_TBL (active rows)."""
    out = collections.defaultdict(set)
    for line in dat.decode("utf-8", "replace").splitlines():
        cols = [c.strip("`") for c in line.split("\t")]
        if len(cols) > 15 and cols[15] == "Y":
            out[cols[1]].add(cols[2].rstrip("."))
    return dict(out)


def section_key(part):
    """Sort key for a section number within a title or chapter: `101k` -> (101, 'k')."""
    m = re.fullmatch(r"(\d+)(.*)", part)
    return (int(m.group(1)), m.group(2)) if m else (-1, part)


def ct_title_file(title):
    """`1` -> `01`, `17a` -> `17a`, as cga.ct.gov names title pages."""
    m = re.fullmatch(r"(\d+)(\D*)", title)
    return m.group(1).zfill(2) + m.group(2) if m else title


def parse_ct_title(text):
    """[(chapter page, first section, last section)] from a CGA title page."""
    rows = re.findall(
        r'href="(chap_[^"]+\.htm)">Chapter [^<]*</a>\s*'
        r'<span class="toc_rng_secs">Secs?\. ([^<]*?)(?: to ([^<]*?))?\s*</span>',
        text,
    )
    return [(page, first, last or first) for page, first, last in rows]


def parse_vt_title(text, title):
    """A Vermont title's chapters, in order, from the title page."""
    return re.findall(rf'href="/statutes/chapter/{title}/([0-9A-Z]+)"', text)


def parse_vt_chapter(text, title, chapter):
    """A Vermont chapter's section numbers (`4469`, `4302a`) from the chapter page."""
    found = re.findall(
        rf'href="/statutes/section/{title}/{chapter}/0*([0-9][0-9A-Za-z.]*)"', text
    )
    return list(dict.fromkeys(found))


def parse_nm_nav(text):
    """{chapter: document item} from an NMOneSource navigation page."""
    return {
        ch: item
        for item, ch in re.findall(
            r'href="/nmos/nmsa-unanno/en/item/(\d+)/index\.do">Chapter ([0-9A-Z]+) -',
            text,
        )
    }


def la_postback(text, label):
    """The form post that opens one entry (`TITLE 9`) of a legis.la.gov contents page."""
    m = re.search(
        r"__doPostBack\(&#39;([^&]+)&#39;,&#39;&#39;\)\">" + re.escape(label) + "</a>",
        text,
    )
    if not m:
        return None
    fields = dict(
        re.findall(
            r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', text
        )
    )
    fields["__EVENTTARGET"] = html.unescape(m.group(1))
    fields["__EVENTARGUMENT"] = ""
    return urllib.parse.urlencode(fields).encode()


def parse_la_toc(text):
    """{`RS 9:2800.54`: document id} from a legis.la.gov title listing."""
    out = {}
    for doc, label in re.findall(r'href="Law\.aspx\?d=(\d+)"[^>]*>([^<]*)<', text):
        out.setdefault(label.strip(), doc)
    return out


def parse_state_constitution(text, article_pattern, section_pattern):
    """{article number: {section, ...}} from a constitution's text, by heading lines."""
    out, article = {}, None
    for line in text.splitlines():
        m = re.match(article_pattern, line)
        if m:
            a = m.group(1)
            article = int(a) if a.isdigit() else roman_to_int(a)
            out.setdefault(article, set())
            continue
        m = re.match(section_pattern, line)
        if m and article is not None:
            out[article].add(m.group(1))
    return out


# --- per-claim checks ---------------------------------------------------------------


@dataclasses.dataclass
class Check:
    claim: str  # span, metadata, code, form, existence, excerpt
    result: str  # pass, fail, none (no machine check)
    detail: str = ""
    source: str = ""
    human: tuple = ()  # (group, key) a person decides once for every vector it covers


CONNECTORS = {
    "§",
    "§§",
    ",",
    "No.",
    "No",
    "ch.",
    "c.",
    "art.",
    "Art.",
    "amend.",
    "Amend.",
}
NUMBERED = (
    "section",
    "rule",
    "title",
    "chapter",
    "volume",
    "page",
    "article",
    "amendment",
)
TERMINAL = ("section", "rule", "page", "amendment", "title", "article")


def canonical(form):
    """A code's spelling reduced for comparison: no case, spacing or punctuation, and
    no trailing Ann./A. (annotated editions)."""
    s = re.sub(r"[^a-z0-9]", "", form.lower())
    return re.sub(r"(ann|a)$", "", s) if len(s) > 3 else s


class Rulings:
    """A maintainer's answers to what no machine source settles (rulings.json).

    Each ruling answers one claim, once for every vector it matches:

    - `form`: `written` (as written) means `code`
    - `code`: `code` is the standard abbreviation of `jurisdiction`'s code
    - `span`: text matching `pattern` (digits as #) belongs inside the span with no field
      holding it, for the `codes` listed
    - `existence`: the section of `vector` exists or existed as cited. Only a ruling
      with `overrides` naming the machine check's result replaces a failed check
    - `excerpt`: `vector`'s excerpt was corrected by hand, and why. It settles no check
      and is kept as the record of the correction
    """

    def __init__(self, data=None):
        data = data or {}
        self.decisions = data.get("decisions") or {}
        self.items = data.get("rulings") or []

    @classmethod
    def load(cls, path):
        path = Path(path)
        return cls(json.loads(path.read_text()) if path.exists() else None)

    def basis(self, ruling):
        return self.decisions[ruling["decision"]]["basis"]

    def source(self, ruling):
        return f"owner-ruling-{ruling['decision']}"

    def check(self, claim, ruling, what):
        return Check(
            claim,
            "pass",
            f"{self.basis(ruling)}: {what}",
            source=self.source(ruling),
        )

    def find(self, claim, **match):
        for r in self.items:
            if r["claim"] != claim:
                continue
            if claim == "form" and (
                canonical(r["written"]) != canonical(match["written"])
                or r["code"] != match["code"]
            ):
                continue
            if claim == "code" and (
                r["code"] != match["code"] or r["jurisdiction"] != match["jurisdiction"]
            ):
                continue
            if claim == "span" and (
                r["pattern"] != match["pattern"] or match["code"] not in r["codes"]
            ):
                continue
            if claim == "existence" and r["vector"] != match["vector"]:
                continue
            return r
        return None


def span_checks(text, cite, rulings=None):
    """Mechanical checks of the span and the as-written fields against the input."""
    out = []
    start, end = cite["span"]
    span = text[start:end]
    groups = cite.get("groups") or {}
    md = cite.get("metadata") or {}
    problems = []
    if span != span.strip():
        problems.append("span has leading or trailing whitespace")
    if start > 0 and text[start - 1].isalnum():
        problems.append(f"span starts inside a word ({text[start - 1 : start + 5]!r})")
    if end < len(text) and text[end].isalnum() and span[-1:].isalnum():
        problems.append(f"span ends inside a word ({text[end - 5 : end + 1]!r})")
    missing = [k for k, v in groups.items() if v not in span]
    if missing:
        problems.append("parts not in the span as written: " + ", ".join(missing))
    terminal = next((groups[k] for k in TERMINAL if k in groups and k != "title"), None)
    if terminal is None:
        terminal = groups.get("title")
    if terminal and not span.endswith(terminal):
        problems.append(f"span doesn't end at the {_terminal_name(groups)} ({span!r})")
    out.append(Check("span", "fail" if problems else "pass", "; ".join(problems)))

    # Text in the span that no field accounts for is a judgment, not an error.
    rest = span
    for v in sorted(groups.values(), key=len, reverse=True):
        rest = rest.replace(v, " ", 1)
    leftover = [t for t in re.split(r"\s+", rest) if t and t not in CONNECTORS]
    leftover = [t for t in leftover if t.strip(",;")]
    if leftover:
        pattern = re.sub(r"\d", "#", " ".join(leftover))
        ruling = (rulings or Rulings()).find(
            "span", pattern=pattern, code=cite.get("reporter_normalized") or ""
        )
        if ruling:
            out.append(
                rulings.check(
                    "span",
                    ruling,
                    f"{' '.join(leftover)!r} belongs in the span, no field holds it",
                )
            )
        else:
            out.append(
                Check(
                    "span",
                    "none",
                    f"text in the span no field holds: {' '.join(leftover)!r}",
                    human=("span", f"in-span text not in any field: `{pattern}`"),
                )
            )
    for k, v in groups.items():
        if k in NUMBERED and re.search(r"\s", v):
            out.append(
                Check(
                    "span",
                    "none",
                    f"{k} {v!r} has whitespace in it",
                    human=("span", f"whitespace inside a {k} (`{v}`)"),
                )
            )

    after = text[end:]
    md_problems = []
    pin = md.get("pin_cite")
    if pin and not re.match(r"[\s,]*" + re.escape(pin), after):
        md_problems.append(f"pin cite {pin!r} doesn't follow the span ({after[:30]!r})")
    year = md.get("year")
    if year and year not in text[start : end + 80]:
        md_problems.append(f"year {year} not in or after the citation")
    paren = md.get("parenthetical")
    if paren and paren not in after:
        md_problems.append(f"parenthetical {paren!r} not after the citation")
    pub = md.get("publisher")
    if pub and pub not in after[:80]:
        md_problems.append(f"publisher {pub!r} not after the citation")
    if pin or year or paren or pub:
        out.append(
            Check("metadata", "fail" if md_problems else "pass", "; ".join(md_problems))
        )
    return out


def _terminal_name(groups):
    return next((k for k in TERMINAL if k in groups and k != "title"), "title")


def code_entry(laws, code):
    """(jurisdiction, how) for a normalized code from reporters-db laws, or None."""
    if code in laws:
        return laws[code][0]["jurisdiction"], f"reporters-db `{code}`"
    for key, entries in laws.items():
        for e in entries:
            for rx in e.get("regexes") or ():
                m = re.match(r"\(\?P<reporter>(.*?)\)", rx)
                if not m:
                    continue
                pat = m.group(1).replace("$law_subject", r"[A-Z][\w.&' ]*?")
                if re.fullmatch(pat, code):
                    return e["jurisdiction"], f"reporters-db `{key}` ({m.group(1)})"
    return None


def code_and_form_checks(sources, vector, cite, existence=None):
    out = []
    code = cite.get("reporter_normalized") or ""
    groups = cite.get("groups") or {}
    md = cite.get("metadata") or {}
    jurisdiction = md.get("jurisdiction")
    entry = code_entry(sources.laws(), code)
    if entry is None and code in CONVENTION_CODES:
        entry = (
            CONVENTION_CODES[code],
            "the 2026-10-18 conventions (docs/protocol.md)",
        )
    ruling = (
        sources.rulings.find("code", code=code, jurisdiction=jurisdiction)
        if entry is None
        else None
    )
    if ruling:
        out.append(
            sources.rulings.check(
                "code", ruling, f"`{code}` is {jurisdiction}'s {ruling['answer']}"
            )
        )
    elif entry is None:
        out.append(
            Check(
                "code",
                "none",
                f"`{code}` is in neither reporters-db's laws nor the conventions",
                human=(
                    "code",
                    (
                        f"`{code}` ({jurisdiction}): is this the code's standard "
                        "abbreviation?"
                    ),
                ),
            )
        )
    elif entry[0] != jurisdiction:
        out.append(
            Check(
                "code",
                "fail",
                f"{entry[1]} gives {entry[0]}, the vector {jurisdiction}",
            )
        )
    else:
        source = (
            f"reporters-db@{REPORTERS_DB_TAG}"
            if entry[1].startswith("reporters-db")
            else ""
        )
        out.append(Check("code", "pass", entry[1], source=source))

    written = groups.get("reporter", "")
    w = canonical(written)
    form_ok = None
    if w == canonical(code) or CONVENTION_FORMS.get(w) == code:
        form_ok = "the written form is the code's abbreviation"
    elif (
        code.startswith(("Cal. ", "Tex. ", "N.Y. "))
        and canonical(groups.get("subject", ""))
        and w.startswith(canonical(code.split()[0]))
        and canonical(groups["subject"]) in w
    ):
        form_ok = "the written form names the state and the subject"
    form_source = ""
    page = (
        existence
        and existence.result == "pass"
        and sources.page_texts.get(existence.detail)
    )
    if form_ok is None and page and written:
        section = groups.get("section") or groups.get("rule") or ""
        if re.search(
            re.escape(written) + r"\s*§?\s*" + re.escape(section) + r"\b", page
        ):
            form_ok = f"the official page cites the section as `{written} {section}`"
            form_source = existence.source
    corpus, src, case_src = vector_source(vector)
    cited_by = ""
    court = None
    if form_ok is None and case_src is not None:
        try:
            _url, case, pinned = sources.stare_case(case_src)
        except SourceUnavailable as e:
            case, pinned = None, False
            cited_by = f"; citing court not found: {e}"
        court = pinned and (case.get("jurisdiction") or {}).get("name_long")
        how = (
            "CAP case metadata"
            if case_src["source"] == "cap"
            else "CourtListener's record as stare.pub serves it"
        )
        if case_src is not src:
            how += ", for the same decision"
        if court and court == jurisdiction:
            form_ok = f"cited by a court in {court} ({how})"
            form_source = (
                "cap-case-metadata" if case_src["source"] == "cap" else "stare-pub-cl"
            )
        elif court:
            cited_by = f"; cited by a court in {court} ({how})"
    ruling = None
    if form_ok is None and written:
        ruling = sources.rulings.find("form", written=written, code=code)
    if ruling:
        form_ok = f"{sources.rulings.basis(ruling)}: `{written}` means `{code}`"
        form_source = sources.rulings.source(ruling)
    if (
        form_ok is None
        and not court
        and corpus == COURTLISTENER_SAMPLE
        and src.get("opinion")
    ):
        why_not = f"{COURTLISTENER_TOKEN_ENV} is unset"
        try:
            cl = sources.cl_court(src["opinion"])
        except RateLimitExhausted:
            cl, why_not = None, "CourtListener's rate limit was reached"
        except SourceUnavailable as e:
            cl = None
            cited_by = f"; citing court not found: {e}"
        if cl is None and not cited_by:
            out.append(
                Check(
                    "form",
                    "not-run",
                    f"citing court not checked: {why_not}",
                    source="courtlistener-api",
                )
            )
        elif cl is not None:
            where = cl_court_jurisdiction(cl)
            name = f"{cl.get('full_name')} (`{cl.get('id')}`)"
            if where and where == jurisdiction:
                form_ok = f"cited by {name}, a court in {where} (CourtListener API)"
                form_source = "courtlistener-api"
            else:
                cited_by = f"; cited by {name}" + (
                    f", a court in {where}" if where else ""
                )
    if form_ok:
        out.append(Check("form", "pass", form_ok, source=form_source))
    else:
        out.append(
            Check(
                "form",
                "none",
                f"`{written}` read as `{code}`{cited_by}",
                human=("form", f"`{written}` means `{code}` ({jurisdiction})"),
            )
        )
    return out


def vector_source(vector):
    """(corpus, source, the stare.pub case for its citing court or None).

    A stare.pub vector's case is its own; a CourtListener-sample vector whose decision
    stare.pub also serves (`stare_pub`) names that case. Any other corpus, or a stare.pub
    source that is neither `cap` nor `cl`, is an error, not a skipped check.
    """
    src = vector.get("source") or {}
    corpus = src.get("corpus")
    if corpus == STARE_PUB:
        if src.get("source") not in ("cap", "cl"):
            raise ValueError(
                f"{vector.get('id')}: stare.pub source {src.get('source')!r} is "
                "neither cap nor cl"
            )
        return corpus, src, src
    if corpus == COURTLISTENER_SAMPLE:
        other = src.get("stare_pub")
        return corpus, src, other if other and "sha256" in other else None
    raise ValueError(
        f"{vector.get('id')}: unknown source corpus {corpus!r}; the excerpt and "
        "citing-court checks know stare-pub and courtlistener-10pct"
    )


def excerpt_check(sources, vector):
    """The input against the text stare.pub serves for the pinned case.

    A CourtListener-sample excerpt has no check here: its text is the sample's, after
    clean steps, and `tools/fetch_corpus.py` verifies the sample's files by sha256.
    """
    corpus, src, _case = vector_source(vector)
    if corpus != STARE_PUB:
        return []
    try:
        url, case, pinned = sources.stare_case(src)
    except SourceUnavailable as e:
        return [Check("excerpt", "none", str(e))]
    if not pinned:
        return [
            Check(
                "excerpt",
                "fail",
                f"{url}: stare.pub serves different bytes from the sha256 pinned",
            )
        ]
    full = fetch_stare.source_text(src, case)
    text = vector["input"]["text"]
    off = src["offset"]
    if full[off : off + len(text)] == text:
        return [
            Check(
                "excerpt",
                "pass",
                "input is the opinion text at the offset",
                "stare-pub-" + src["source"],
            )
        ]
    return [Check("excerpt", "fail", f"input differs from {url} at offset {off}")]


# --- existence, per source ----------------------------------------------------------


def exists_usc(sources, groups):
    title, section = groups.get("title"), groups.get("section")
    secs = sources.uscode(title)["sections"]
    src = f"govinfo-uscode-{USCODE_EDITION}"
    if section in secs:
        return Check("existence", "pass", f"{title} U.S.C. {section}", src)
    ends = section.split("-")
    if len(ends) == 2 and all(e in secs for e in ends):
        return Check(
            "existence", "pass", f"{title} U.S.C. {ends[0]} and {ends[1]}", src
        )
    return Check("existence", "fail", f"no section {section} in title {title}", src)


def exists_cfr(sources, title, section):
    src = f"ecfr-{ECFR_DATE}"
    if section in sources.ecfr(title):
        return Check("existence", "pass", f"{title} C.F.R. § {section}", src)
    return Check(
        "existence", "fail", f"no § {section} in {title} C.F.R. at {ECFR_DATE}", src
    )


def exists_rule(sources, code, rule):
    title, heading = FEDERAL_RULES[code]
    rules = sources.uscode(title)["rules"].get(heading, set())
    src = f"govinfo-uscode-{USCODE_EDITION}"
    if rule in rules:
        return Check("existence", "pass", f"{heading.title()}, Rule {rule}", src)
    return Check("existence", "fail", f"no Rule {rule} in {heading.title()}", src)


def exists_stat(sources, groups, md):
    vol, page = int(groups["volume"]), int(groups["page"].replace(",", ""))
    data = sources.statute(vol)
    src = "govinfo-statute"
    if not data:
        return Check("existence", "fail", f"no Statutes at Large volume {vol}", src)
    hit = next((g for g in data["granules"] if g["start"] <= page <= g["end"]), None)
    if not hit:
        return Check(
            "existence", "fail", f"page {page} is in no granule of volume {vol}", src
        )
    year = md.get("year")
    if year and hit["date"] and not hit["date"].startswith(year):
        return Check(
            "existence", "fail", f"{hit['id']} is dated {hit['date']}, not {year}", src
        )
    return Check("existence", "pass", f"{hit['id']} ({hit['date']})", src)


def stat_volumes(congress):
    """Candidate Statutes at Large volumes for a Congress (two a Congress since the
    82nd); the volumes' own metadata confirms which."""
    return [2 * congress - 99, 2 * congress - 98] if congress >= 82 else []


def exists_pub_l(sources, groups, md):
    m = re.fullmatch(r"(\d+)-(\d+)", groups.get("title", ""))
    src = "govinfo-statute"
    if not m:
        return Check(
            "existence", "fail", f"public law number {groups.get('title')!r}", src
        )
    congress, number = int(m.group(1)), m.group(2)
    for vol in stat_volumes(congress):
        data = sources.statute(vol)
        if not data or str(congress) not in data["congresses"]:
            continue
        for g in data["granules"]:
            if (
                g["class"] == "PUBLICLAW"
                and g["congress"] == str(congress)
                and g["number"] == number
            ):
                return Check(
                    "existence",
                    "pass",
                    f"Pub. L. {congress}-{number} is {g['id']}",
                    src,
                )
    if not stat_volumes(congress):
        return Check(
            "existence", "none", f"Congress {congress} predates the volume rule"
        )
    return Check(
        "existence",
        "fail",
        f"no Pub. L. {congress}-{number} in the Statutes at Large",
        src,
    )


def exists_fr(sources, groups, md):
    vol, page = groups["volume"], groups["page"].replace(",", "")
    url, pkg, year, status = sources.fr_issue(vol, page)
    src = "govinfo-fr-link"
    if not pkg:
        return Check(
            "existence", "fail", f"{url} resolved to no issue (HTTP {status})", src
        )
    if md.get("year") and md["year"] != year:
        return Check(
            "existence",
            "fail",
            f"{vol} Fed. Reg. {page} is in {pkg}, not {md['year']}",
            src,
        )
    return Check("existence", "pass", f"{vol} Fed. Reg. {page} is in {pkg}", src)


def exists_ussg(sources, groups):
    sec = groups.get("section")
    src = f"ussc-guidelines-{USSG_MANUAL}"
    if sec in sources.ussg():
        return Check(
            "existence", "pass", f"§{sec} in the {USSG_MANUAL} Guidelines Manual", src
        )
    return Check(
        "existence", "fail", f"no §{sec} in the {USSG_MANUAL} Guidelines Manual", src
    )


def exists_us_const(sources, groups, md):
    const = sources.constitution()
    src = "gpo-constitution"

    def num(v):
        return int(v) if v.isdigit() else roman_to_int(v.upper())

    kind = "amendment" if "amendment" in groups else "article"
    n = num(groups[kind])
    part = const[kind].get(n)
    label = f"{kind} {groups[kind]}"
    if part is None:
        return Check("existence", "fail", f"no {label}", src)
    sec = groups.get("section")
    if sec:
        if int(sec) not in part:
            return Check("existence", "fail", f"no section {sec} in {label}", src)
        label += f", section {sec}"
        clauses = part[int(sec)]
        m = re.fullmatch(r"cl\. (\d+)", md.get("pin_cite") or "")
        if m and int(m.group(1)) > clauses:
            return Check(
                "existence",
                "fail",
                f"{label} has {clauses} clauses, not {m.group(1)}",
                src,
            )
        if m:
            label += f", clause {m.group(1)} of {clauses}"
    return Check("existence", "pass", label, src)


def _page_has(sources, url, pattern, src):
    status, body = sources.page(url)
    if status in (400, 404, 410):
        return Check("existence", "fail", f"{url}: HTTP {status}", src)
    if status != 200:
        return Check("existence", "none", f"{url}: HTTP {status}, no answer either way")
    text = page_text(body)
    if re.search(pattern, text):
        sources.page_texts[url] = text
        return Check("existence", "pass", url, src)
    return Check("existence", "fail", f"{url} doesn't hold the section", src)


def exists_state(sources, code, groups):
    """Per-section (or per-chapter) pages on official legislature sites."""
    sec = groups.get("section", "")
    e = re.escape(sec)
    if code == "Ariz. Rev. Stat.":
        title, _, rest = sec.partition("-")
        url = f"https://www.azleg.gov/ars/{title}/{rest.zfill(5)}.htm"
        return _page_has(sources, url, rf"\b{e}\b", "azleg")
    if code == "N.C. Gen. Stat.":
        chapter = sec.split("-")[0]
        url = (
            "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/"
            f"Chapter_{chapter}/GS_{sec}.html"
        )
        return _page_has(sources, url, rf"§ {e}\.", "ncleg")
    if code == "Me. Rev. Stat. Ann.":
        title = groups.get("title", "")
        url = (
            f"https://legislature.maine.gov/statutes/{title}/title{title}sec{sec}.html"
        )
        return _page_has(
            sources, url, rf"Title {re.escape(title)}, §{e}\b", "maine-legislature"
        )
    if code.startswith("Tex. ") and code.endswith(" Code Ann."):
        abbr = TEXAS_CODES.get(groups.get("subject", ""))
        if not abbr:
            return Check("existence", "none", f"no Texas code abbreviation for {code}")
        chapter = sec.split(".")[0]
        url = f"https://tcss.legis.texas.gov/resources/{abbr}/htm/{abbr}.{chapter}.htm"
        return _page_has(sources, url, rf"Sec\. {e}\.", "texas-legislative-council")
    if code == "Mich. Comp. Laws":
        url = f"https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-{sec.replace('.', '-')}"
        return _page_has(sources, url, rf"Section {e}\b", "mi-legislature")
    if code == "R.I. Gen. Laws":
        parts = sec.split("-")
        if len(parts) < 3:
            return Check(
                "existence", "none", f"R.I. section {sec} isn't title-chapter-section"
            )
        url = (
            f"https://webserver.rilegislature.gov/Statutes/TITLE{parts[0]}/"
            f"{parts[0]}-{parts[1]}/{sec}.htm"
        )
        return _page_has(sources, url, rf"§ {e}\.", "ri-legislature")
    if code == "W. Va. Code":
        url = f"https://code.wvlegislature.gov/{sec}/"
        return _page_has(sources, url, rf"§{e}\. \S", "wv-legislature")
    if code == "Wis. Stat.":
        url = f"https://docs.legis.wisconsin.gov/statutes/statutes/{sec.replace('.', '/')}"
        return _page_has(sources, url, rf"\b{e}\b", "wi-legislature")
    if code == "Mass. Gen. Laws":
        ch = groups.get("chapter", "")
        url = f"https://malegislature.gov/Laws/GeneralLaws/Chapter{ch}/Section{sec}"
        return _page_has(
            sources, url, rf"Chapter {re.escape(ch)},? Section {e}\b", "ma-legislature"
        )
    if code == "Pa. Cons. Stat.":
        if not sec.isdigit():
            return Check("existence", "none", f"Pa.C.S. section {sec} isn't numeric")
        n = int(sec)
        url = (
            "https://www.palegis.us/statutes/consolidated/view-statute?txtType=HTM"
            f"&ttl={groups.get('title')}&div=0&chapter={n // 100}&section={n % 100}"
            "&subsctn=0&iFrame=true"
        )
        return _page_has(
            sources,
            url,
            rf"Section {e}(\.0)? - Title {re.escape(groups.get('title', ''))}\b",
            "pa-legislature",
        )
    return None


def _pdf_has(sources, url, pattern, src, what):
    text = sources.pdf(url)
    if text is None:
        return Check("existence", "fail", f"{url}: HTTP 404", src)
    if re.search(pattern, text, re.MULTILINE):
        return Check("existence", "pass", f"{what} in {url}", src)
    return Check("existence", "fail", f"no {what} in {url}", src)


def exists_ca(sources, code, sec):
    law = CA_CODES.get(code)
    if not law:
        return Check("existence", "none", f"no leginfo code for {code}")
    src = f"ca-leginfo-pubinfo-{CA_PUBINFO}"
    if sec in sources.ca_sections().get(law, ()):
        return Check("existence", "pass", f"{law} § {sec} in LAW_SECTION_TBL", src)
    return Check("existence", "fail", f"no {law} § {sec} in LAW_SECTION_TBL", src)


def exists_ct(sources, sec):
    sec = re.sub(r"\s", "", sec)  # `10 -236b`: the space is a span question
    title, _, part = sec.partition("-")
    src = "cga"
    chapters = sources.ct_title(title)
    if chapters is None:
        return Check("existence", "fail", f"no title {title} on cga.ct.gov", src)
    key = section_key(part)
    for page, first, last in chapters:
        lo, hi = (section_key(x.partition("-")[2]) for x in (first, last))
        if lo <= key <= hi:
            url = f"https://www.cga.ct.gov/current/pub/{page}"
            return _page_has(sources, url, rf"Sec\. {re.escape(sec)}\. ", src)
    return Check("existence", "fail", f"§ {sec} is in no chapter of title {title}", src)


def exists_hi(sources, sec):
    m = re.fullmatch(r"(\d+)([A-Z]*)-(\d+)(?:\.(\d+))?", sec)
    if not m:
        return Check("existence", "none", f"HRS section {sec} isn't chapter-section")
    num, suffix, n, dec = m.groups()
    key = (int(num), suffix)
    vol = next(
        (
            v
            for v in sources.hi_volumes()
            if section_key(v[1]) <= key <= section_key(v[2])
        ),
        None,
    )
    if vol is None:
        return Check("existence", "fail", f"chapter {num}{suffix} is in no HRS volume")
    chapter = num.zfill(4) + suffix
    name = f"HRS_{chapter}-{n.zfill(4)}" + (f"_{dec.zfill(4)}" if dec else "")
    url = f"https://data.capitol.hawaii.gov/hrscurrent/{vol[0]}/HRS{chapter}/{name}.htm"
    return _page_has(sources, url, rf"§\s?{re.escape(sec)}\b", "hawaii-legislature")


def exists_vt(sources, title, sec):
    """Find the chapter by bisection over the title's chapters (sections are numbered
    in chapter order), then look for the section in the chapter's list."""
    src = "vermont-legislature"
    chapters = sources.vt_chapters(title)
    if not chapters:
        return Check("existence", "fail", f"no title {title} in the V.S.A.", src)
    key = section_key(sec)

    def keys(i):
        return sorted(section_key(s) for s in sources.vt_chapter(title, chapters[i])[1])

    lo, hi, best = 0, len(chapters) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        j = mid
        while j <= hi and not keys(j):
            j += 1
        if j > hi:
            hi = mid - 1
        elif keys(j)[0] <= key:
            best, lo = j, j + 1
        else:
            hi = mid - 1
    if best is None:
        return Check(
            "existence", "none", f"§ {sec} precedes every chapter of title {title}"
        )
    url, secs = sources.vt_chapter(title, chapters[best])
    if sec in secs:
        sources.page_texts[url] = page_text(sources.page(url)[1])
        return Check("existence", "pass", url, src)
    if keys(best)[-1] >= key:
        return Check(
            "existence",
            "fail",
            f"§ {sec} falls inside chapter {chapters[best]}'s sections but isn't one "
            f"({url})",
            src,
        )
    return Check(
        "existence", "none", f"§ {sec} falls between chapters of title {title} ({url})"
    )


def exists_nd(sources, sec):
    parts = sec.split("-")
    if len(parts) != 3:
        return Check("existence", "none", f"N.D.C.C. {sec} isn't title-chapter-section")
    url = f"https://ndlegis.gov/cencode/t{parts[0]}c{parts[1].replace('.', '-')}.pdf"
    return _pdf_has(
        sources, url, rf"^\s*{re.escape(sec)}\.\s", "nd-legislature", f"§ {sec}"
    )


def exists_nm(sources, sec):
    chapter = sec.split("-")[0]
    item = sources.nm_chapters().get(chapter)
    src = "nmcc-nmonesource"
    if item is None:
        return Check("existence", "fail", f"no NMSA chapter {chapter}", src)
    url = f"https://nmonesource.com/nmos/nmsa-unanno/en/{item}/1/document.do"
    return _pdf_has(sources, url, rf"^\s*{re.escape(sec)}\.\s", src, f"§ {sec}")


def exists_la(sources, sec):
    title, _, part = sec.partition(":")
    src = "la-legislature"
    toc = sources.la_title(title)
    if toc is None:
        return Check("existence", "fail", f"no R.S. title {title}", src)
    doc = toc.get(f"RS {sec}")
    if doc is None:
        return Check(
            "existence", "fail", f"RS {sec} isn't in title {title}'s contents", src
        )
    url = f"https://www.legis.la.gov/legis/Law.aspx?d={doc}"
    return _page_has(sources, url, rf"§{re.escape(part)}\. ", src)


ALABAMA_QUERY = (
    "query($displayId: String!){codesOfAlabama(where:{type:{eq:Section},"
    "displayId:{eq:$displayId}}){data{displayId title}}}"
)


def exists_al(sources, sec):
    url = "https://alison.legislature.state.al.us/graphql?" + urllib.parse.urlencode(
        {"query": ALABAMA_QUERY, "variables": json.dumps({"displayId": sec})}
    )
    src = "alison"
    status, body = sources.page(url)
    if status != 200:
        return Check("existence", "none", f"{url}: HTTP {status}, no answer either way")
    try:
        rows = json.loads(body)["data"]["codesOfAlabama"]["data"]
    except (ValueError, KeyError, TypeError):
        return Check("existence", "none", f"{url}: no data in the answer")
    if any(r.get("displayId") == sec for r in rows):
        return Check(
            "existence", "pass", f"Ala. Code § {sec} ({rows[0]['title']})", src
        )
    return Check("existence", "fail", f"no Ala. Code § {sec} in ALISON", src)


# State constitutions as PDFs: code -> (url, article heading, section heading, source).
STATE_CONSTITUTIONS = {
    "Ind. Const.": (
        (
            "https://iga.in.gov/publications/indiana_constitution/"
            "Constitution%20(as%20amended%202024).pdf"
        ),
        r"ARTICLE (\d+)\.\s*$",
        r"\s*Section (\d+)\.",
        "iga-constitution",
    ),
    "N.M. Const.": (
        "https://nmonesource.com/nmos/c/en/5916/1/document.do",
        r"ARTICLE ([IVXL]+)\s*$",
        r"(?:Sec\.|Section) (\d+[A-Z]?)\. \[",
        "nmcc-nmonesource",
    ),
}

# Court rules as PDFs: code -> (url, heading pattern with {rule}, source).
COURT_RULES = {
    "Tex. R. Civ. P.": (
        "https://www.txcourts.gov/media/1463426/texas-rules-of-civil-procedure.pdf",
        r"^\s*RULE {rule}\.\s",
        "txcourts",
    ),
    "Tex. R. App. P.": (
        (
            "https://www.txcourts.gov/media/1463134/"
            "texas-rules-of-appellate-procedure-02062026.pdf"
        ),
        r"^\s*(?:Rule\s+)?{rule}\.\s",
        "txcourts",
    ),
    "Conn. Practice Book": (
        "https://www.jud.ct.gov/Publications/PracticeBook/PB.pdf",
        r"^\s*Sec\. {rule}\.\s",
        "ct-judicial",
    ),
}


def exists_state_const(sources, code, groups):
    url, art_rx, sec_rx, src = STATE_CONSTITUTIONS[code]
    text = sources.pdf(url)
    if text is None:
        return Check("existence", "fail", f"{url}: HTTP 404", src)
    parsed = parse_state_constitution(text, art_rx, sec_rx)
    a = groups.get("article", "")
    n = int(a) if a.isdigit() else roman_to_int(a.upper())
    if n not in parsed:
        return Check("existence", "fail", f"no article {a} in {url}", src)
    sec = groups.get("section")
    if sec and sec not in parsed[n]:
        return Check(
            "existence", "fail", f"no section {sec} in article {a} ({url})", src
        )
    return Check("existence", "pass", f"art. {a}" + (f", § {sec}" if sec else ""), src)


def exists_court_rule(sources, code, rule):
    url, pattern, src = COURT_RULES[code]
    if code == "Tex. R. App. P." and "." not in rule:
        pattern = r"^\s*Rule\s+{rule}\.\s"  # a bare `25.` could be any numbered line
    return _pdf_has(
        sources, url, pattern.format(rule=re.escape(rule)), src, f"rule {rule}"
    )


def exists_more(sources, code, groups):
    """States and rules whose sources need a lookup or a PDF."""
    sec = groups.get("section", "")
    if code in CA_CODES:
        return exists_ca(sources, code, sec)
    if code == "Conn. Gen. Stat.":
        return exists_ct(sources, sec)
    if code == "Haw. Rev. Stat.":
        return exists_hi(sources, sec)
    if code == "Vt. Stat. Ann.":
        return exists_vt(sources, groups.get("title", ""), sec)
    if code == "N.D. Cent. Code":
        return exists_nd(sources, sec)
    if code == "N.M. Stat. Ann.":
        return exists_nm(sources, sec)
    if code == "La. Stat. Ann.":
        return exists_la(sources, sec)
    if code == "Ala. Code":
        return exists_al(sources, sec)
    if code in STATE_CONSTITUTIONS:
        return exists_state_const(sources, code, groups)
    if code in COURT_RULES:
        return exists_court_rule(sources, code, groups.get("rule") or sec)
    return None


def exists_ny(sources, code, sec):
    """NY Open Legislation API: the section's law document."""
    src = "ny-openleg"
    location = sec.upper()
    found = sources.ny_law_doc(NY_LAWS[code], location)
    if found is None:
        why = NO_SOURCE.get(code, "")
        if why.startswith("as "):
            why = NO_SOURCE[why[3:]]
        return Check(
            "existence",
            "not-run",
            f"not checked: {NY_OPENLEG_KEY_ENV} is unset",
            src,
            human=("existence", f"`{code}`: {why}"),
        )
    url, status, doc = found
    result = doc.get("result") or {}
    if status == 404:
        return Check(
            "existence", "fail", f"{url}: HTTP 404 ({doc.get('message')})", src
        )
    if status != 200 or not doc.get("success"):
        return Check("existence", "none", f"{url}: HTTP {status}, no answer either way")
    if result.get("docType") == "SECTION" and result.get("locationId") == location:
        title = result.get("title") or ""
        return Check("existence", "pass", f"{url} ({title})", src)
    return Check("existence", "fail", f"{url} isn't a section document", src)


def existence_check(sources, cite):
    code = cite.get("reporter_normalized") or ""
    groups = cite.get("groups") or {}
    md = cite.get("metadata") or {}
    try:
        if code == "U.S.C.":
            return exists_usc(sources, groups)
        if code == "C.F.R.":
            return exists_cfr(
                sources, groups.get("title") or groups.get("chapter"), groups["section"]
            )
        if code == "Treas. Reg.":
            return exists_cfr(sources, "26", groups["section"])
        if code in FEDERAL_RULES:
            return exists_rule(sources, code, groups["rule"])
        if code == "Stat.":
            return exists_stat(sources, groups, md)
        if code == "Pub. L.":
            return exists_pub_l(sources, groups, md)
        if code == "Fed. Reg.":
            return exists_fr(sources, groups, md)
        if code == "U.S.S.G.":
            return exists_ussg(sources, groups)
        if code == "U.S. Const.":
            return exists_us_const(sources, groups, md)
        if code in NY_LAWS:
            return exists_ny(sources, code, groups.get("section", ""))
        state = exists_state(sources, code, groups) or exists_more(
            sources, code, groups
        )
        if state is not None:
            return state
    except SourceUnavailable as e:
        return Check("existence", "none", f"source unavailable: {e}")
    why = NO_SOURCE.get(code, "no official source wired in")
    return Check(
        "existence",
        "none",
        why,
        human=("existence", f"`{code}`: {why}"),
    )


# --- verdicts -----------------------------------------------------------------------


def ruled_existence(sources, vector, existence):
    """A machine check replaced by the maintainer's ruling on that vector, if any."""
    if existence.result == "pass":
        return existence
    ruling = sources.rulings.find("existence", vector=vector["id"])
    if ruling is None:
        return existence
    if existence.result == "fail" and ruling.get("overrides") != "fail":
        return existence
    what = ruling["answer"]
    if existence.detail:
        what += f" (machine check: {existence.result}, {existence.detail})"
    return sources.rulings.check("existence", ruling, what)


def verify_vector(sources, vector):
    checks = excerpt_check(sources, vector)
    text = vector["input"]["text"]
    for cite in vector["expected"]["citations"]:
        if cite.get("type") != "full_law":
            continue
        checks += span_checks(text, cite, sources.rulings)
        existence = existence_check(sources, cite)
        checks += code_and_form_checks(sources, vector, cite, existence)
        checks.append(ruled_existence(sources, vector, existence))
    return checks


def verdict(checks):
    failed = [c for c in checks if c.result == "fail"]
    if failed:
        return "contradicted:" + "; ".join(f"{c.claim}: {c.detail}" for c in failed)
    open_ = [c for c in checks if c.result in ("none", "not-run")]
    if open_:
        claims = sorted({c.claim for c in open_})
        return "unverifiable:" + ", ".join(claims)
    sources = sorted({c.source for c in checks if c.source})
    return "verified-by-source:" + "+".join(sources)


def run(dirs, fetcher, rulings=None, stare=None):
    sources = Sources(fetcher, stare=stare, rulings=rulings)
    results = []
    for vid, (vector, set_name, status) in load_sets(dirs).items():
        cites = [
            c for c in vector["expected"]["citations"] if c.get("type") == "full_law"
        ]
        if not cites:
            continue
        checks = verify_vector(sources, vector)
        c0 = cites[0]
        results.append(
            {
                "id": vid,
                "set": set_name,
                "provenance": status,
                "kind": law_kind(
                    c0.get("reporter_normalized"),
                    (c0.get("metadata") or {}).get("jurisdiction"),
                ),
                "code": c0.get("reporter_normalized"),
                "verdict": verdict(checks),
                "checks": [dataclasses.asdict(c) for c in checks],
            }
        )
    return results


# --- reports ------------------------------------------------------------------------


def summarize(results):
    by = collections.Counter(r["verdict"].split(":")[0] for r in results)
    human = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in results:
        if r["verdict"].startswith("verified-by-source"):
            continue
        for c in r["checks"]:
            if c["human"]:
                group, key = c["human"]
                human[group][key].append(r["id"])
    return by, human


HUMAN_GROUPS = (
    ("form", "Code forms: one answer covers every vector with the form"),
    ("code", "Code abbreviations not in reporters-db or the conventions"),
    ("span", "Span judgments"),
    ("existence", "No machine source for the section's existence"),
)


def markdown(results, used, changed=None):
    by, human = summarize(results)
    n = len(results)
    lines = [
        "# Statute vectors checked against official sources",
        "",
        (
            "Written by `bench/verify_statutes.py` (`mise run verify:statutes`). A verdict "
            "doesn't change a vector's provenance."
        ),
        "",
        "| Set | Vectors | Verified by source | Contradicted | Unverifiable |",
        "|---|---:|---:|---:|---:|",
    ]
    sets = collections.defaultdict(collections.Counter)
    for r in results:
        sets[r["set"]][r["verdict"].split(":")[0]] += 1
    for name, c in sorted(sets.items()):
        lines.append(
            f"| {name} | {sum(c.values())} | {c['verified-by-source']} | "
            f"{c['contradicted']} | {c['unverifiable']} |"
        )
    lines.append(
        f"| **all** | {n} | {by['verified-by-source']} | {by['contradicted']} | "
        f"{by['unverifiable']} |"
    )
    lines += ["", "## Contradicted", ""]
    bad = [r for r in results if r["verdict"].startswith("contradicted")]
    lines += [f"- `{r['id']}`: {r['verdict'].split(':', 1)[1]}" for r in bad] or [
        "None."
    ]
    ruled = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in results:
        for c in r["checks"]:
            if c["source"].startswith("owner-ruling-") and c["result"] == "pass":
                basis = c["detail"].split(": ", 1)[0]
                ruled[basis][c["claim"]].add(r["id"])
    if ruled:
        lines += [
            "",
            "## Settled by the maintainer's rulings",
            "",
            (
                "Claims no machine source settles, answered once per form, code, span "
                "pattern or vector in `verification/statutes/rulings.json`."
            ),
            "",
        ]
        for basis, claims in sorted(ruled.items()):
            vectors = set().union(*claims.values())
            parts = ", ".join(f"{k} {len(v)}" for k, v in sorted(claims.items()))
            lines.append(f"- {basis}: {len(vectors)} vectors ({parts})")
    not_run = collections.defaultdict(list)
    for r in results:
        for c in r["checks"]:
            if c["result"] == "not-run":
                not_run[c["detail"]].append(r["id"])
    if not_run:
        lines += [
            "",
            "## Checks not run",
            "",
            (
                "Checks against a keyed source that didn't run: its key wasn't in the "
                "environment, or its rate limit ran out. A rerun with the keys set (the "
                "operator's mise env) runs them and reuses what's cached."
            ),
            "",
        ]
        for detail, ids in sorted(not_run.items()):
            lines.append(f"- {detail}: {len(ids)}")
    lines += ["", "## What needs a person", ""]
    for group, title in HUMAN_GROUPS:
        items = human.get(group)
        if not items:
            continue
        lines += [f"### {title}", ""]
        for key, ids in sorted(items.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            shown = ", ".join(f"`{i.split('/find/')[-1]}`" for i in ids)
            lines.append(f"- {key}: {len(ids)} ({shown})")
        lines.append("")
    lines += ["## Verdicts", "", "| Vector | Provenance | Verdict |", "|---|---|---|"]
    for r in results:
        v = r["verdict"].replace("|", "\\|")
        lines.append(f"| `{r['id']}` | {r['provenance']} | {v} |")
    if changed:
        lines += ["", "## Sources changed since they were pinned", ""]
        lines += [
            f"- {url}: was `{old[:16]}`, now `{used[url]['sha256'][:16]}`"
            for url, old in sorted(changed.items())
        ]
    lines += [
        "",
        "## Sources used",
        "",
        "| URL | Retrieved | Bytes | SHA-256 |",
        "|---|---|---:|---|",
    ]
    for url, m in sorted(used.items()):
        lines.append(
            f"| {url} | {m['retrieved']} | {m['bytes']} | `{m['sha256'][:16]}` |"
        )
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", action="append", type=Path)
    ap.add_argument("--offline", action="store_true", help="use cached sources only")
    ap.add_argument(
        "--refresh", action="store_true", help="refetch and repin every source"
    )
    ap.add_argument("--lock", type=Path, default=LOCK)
    ap.add_argument("--rulings", type=Path, default=RULINGS)
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--json", type=Path, default=OUT / "verdicts.json")
    ap.add_argument("--md", type=Path, default=OUT / "report.md")
    args = ap.parse_args(argv)
    lock = json.loads(args.lock.read_text()) if args.lock.exists() else {}
    fetcher = Fetcher(args.cache, lock, offline=args.offline, refresh=args.refresh)
    try:
        results = run(
            args.vectors or DEFAULT_SETS, fetcher, rulings=Rulings.load(args.rulings)
        )
    except SourceChanged as e:
        print(f"verify_statutes: {e}", file=sys.stderr)
        return 2
    used = {u: fetcher.used[u] for u in sorted(fetcher.used)}
    for p in (args.lock, args.json, args.md):
        p.parent.mkdir(parents=True, exist_ok=True)
    args.lock.write_text(json.dumps(used, indent=1, sort_keys=True) + "\n")
    args.json.write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n")
    args.md.write_text(markdown(results, used, fetcher.changed))
    by, _ = summarize(results)
    print(
        f"{len(results)} vectors: {by['verified-by-source']} verified by source, "
        f"{by['contradicted']} contradicted, {by['unverifiable']} unverifiable; "
        f"wrote {args.md}"
    )
    for url in fetcher.changed:
        print(f"verify_statutes: changed since pinned: {url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
