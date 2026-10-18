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
  is the code's own abbreviation, or (for a CAP excerpt) a citing court in the code's
  jurisdiction
- existence: the section (rule, article, page, public law) exists in the official
  source for that code, and a year agrees with it
- excerpt: for a CAP excerpt, the input is the opinion's text at the recorded offset

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
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from statutes import law_kind, load_sets

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETS = (ROOT / "vectors" / "statutes", ROOT / "vectors" / "statutes-proposed")
CACHE = ROOT / ".cache" / "statute-sources"
OUT = ROOT / "verification" / "statutes"
LOCK = OUT / "sources.json"
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

# Why there's no machine check yet, per code with no source wired in. Facts about the
# sources as found on 2026-10-18; see verification/statutes/README.md.
NO_SOURCE = {
    "Conn. Gen. Stat.": "cga.ct.gov didn't answer from here on 2026-10-18, and it "
    "publishes sections inside chapter pages",
    "Conn. Practice Book": "the Practice Book is a PDF on jud.ct.gov; not wired in",
    "Ga. Code Ann.": "Georgia's official code is online through LexisNexis; not used",
    "Tenn. Code Ann.": "Tennessee's official code is online through LexisNexis; not used",
    "Ark. Code Ann.": "Arkansas's official code is online through LexisNexis; not used",
    "Haw. Rev. Stat.": "capitol.hawaii.gov answered HTTP 403 to scripted requests",
    "N.D. Cent. Code": "ndlegis.gov publishes chapter PDFs; PDF text isn't read here",
    "Vt. Stat. Ann.": "legislature.vermont.gov paths need the chapter; not wired in",
    "Okla. Stat.": "OSCN addresses sections by document id; not wired in",
    "N.M. Stat. Ann.": "nmonesource.com addresses sections by document id; not wired in",
    "Ala. Code": "alison.legislature.state.al.us renders sections client-side",
    "La. Stat. Ann.": "legis.la.gov addresses sections by document id; not wired in",
    "Pa. Stat. Ann.": "Purdon's title and section numbers have no official per-section "
    "source; palegis.us indexes unconsolidated statutes by act",
    "N.Y. Penal Law": "nysenate.gov answered HTTP 403 to scripted requests; its Open "
    "Legislation API needs a key",
    "N.Y. Judiciary Law": "as N.Y. Penal Law",
    "N.Y. Family Ct Act": "as N.Y. Penal Law",
    "N.Y. Comp. Codes R. & Regs.": "the official NYCRR is online through Thomson Reuters "
    "Westlaw; not used",
    "N.J. Admin. Code": "the N.J.A.C. is online through LexisNexis; not used",
    "Cal. Pen. Code": "leginfo.legislature.ca.gov answered HTTP 403 to scripted "
    "requests; its bulk pubinfo archive isn't wired in",
    "Cal. Civ. Proc. Code": "as Cal. Pen. Code",
    "Cal. Evid. Code": "as Cal. Pen. Code",
    "Cal. Civ. Code": "as Cal. Pen. Code",
    "Ohio Const.": "codes.ohio.gov renders sections client-side",
    "Ind. Const.": "no official source wired in",
    "N.M. Const.": "no official source wired in",
    "Tex. R. Civ. P.": "the rules are a PDF on txcourts.gov; not wired in",
    "Tex. R. App. P.": "the rules are a PDF on txcourts.gov; not wired in",
    "Mich. Ct. R.": "the rules are a PDF on courts.michigan.gov; not wired in",
    "Pa. R. Civ. P.": "pacodeandbulletin.gov returned no rule text without scripting",
}


# --- fetching, caching and pinning -------------------------------------------------


class SourceUnavailable(Exception):
    pass


class SourceChanged(Exception):
    pass


@dataclasses.dataclass
class Fetcher:
    """Fetches sources once, caches them, and pins each by SHA-256 in a lock file."""

    cache: Path
    lock: dict
    offline: bool = False
    refresh: bool = False
    opener: object = None  # callable(url, follow) -> (status, body bytes, location)
    used: dict = dataclasses.field(default_factory=dict)
    changed: dict = dataclasses.field(
        default_factory=dict
    )  # url -> sha256 it was pinned at

    def _path(self, url):
        return self.cache / hashlib.sha256(url.encode()).hexdigest()[:32]

    def get(self, url, follow=True):
        """(status, body) for url, with redirects followed or not.

        Without follow, the body is the redirect's Location (empty if none).
        """
        path = self._path(url)
        meta_path = path.with_suffix(".json")
        cached = path.exists() and meta_path.exists() and not self.refresh
        if cached:
            body = path.read_bytes()
            meta = json.loads(meta_path.read_text())
        elif self.offline:
            raise SourceUnavailable(f"not cached (offline): {url}")
        else:
            status, body, location = (self.opener or _urlopen)(url, follow)
            meta = {
                "url": url,
                "retrieved": datetime.date.today().isoformat(),
                "status": status,
            }
            if location:
                meta["location"] = location
            if not follow:
                body = (location or "").encode()
            self.cache.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            meta_path.write_text(json.dumps(meta))
        digest = hashlib.sha256(body).hexdigest()
        pinned = self.lock.get(url)
        if pinned and pinned["sha256"] != digest:
            if cached:
                raise SourceChanged(
                    f"{url}: the cached copy's sha256 {digest[:12]} differs from the "
                    f"pinned {pinned['sha256'][:12]} (rerun with --refresh to refetch)"
                )
            # The source changed upstream since it was pinned: use what it says now,
            # record the new hash and report the change.
            self.changed[url] = pinned["sha256"]
            pinned = None
        if not pinned or self.refresh:
            pinned = {**meta, "sha256": digest, "bytes": len(body)}
            pinned.pop("url", None)
        self.used[url] = pinned
        return meta["status"], body


def _urlopen(url, follow):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    handlers = [] if follow else [NoRedirect()]
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(req, timeout=120) as r:
            return r.status, r.read(), r.headers.get("Location")
    except urllib.error.HTTPError as e:
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

    def __init__(self, fetcher):
        self.f = fetcher
        self._memo = {}
        self.page_texts = {}  # url -> visible text of an official page that held a section

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

    # Caselaw Access Project case metadata and text
    def cap_case(self, reporter, volume, case):
        url = f"https://static.case.law/{reporter}/{volume}/cases/{case}.json"
        status, body = self.f.get(url)
        if status != 200:
            raise SourceUnavailable(f"{url}: HTTP {status}")
        return url, json.loads(body)

    def page(self, url):
        return self.f.get(url)


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


def span_checks(text, cite):
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
    if entry is None:
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
    court = None
    src = vector.get("source") or {}
    if form_ok is None and src.get("corpus") == "cap":
        try:
            _url, case = sources.cap_case(src["reporter"], src["volume"], src["case"])
            court = (case.get("jurisdiction") or {}).get("name_long")
        except SourceUnavailable:
            court = None
        if court and court == jurisdiction:
            form_ok = f"cited by a court in {court} (CAP case metadata)"
            form_source = "cap-case-metadata"
    if form_ok:
        out.append(Check("form", "pass", form_ok, source=form_source))
    else:
        out.append(
            Check(
                "form",
                "none",
                f"`{written}` read as `{code}`",
                human=("form", f"`{written}` means `{code}` ({jurisdiction})"),
            )
        )
    return out


def excerpt_check(sources, vector):
    src = vector.get("source") or {}
    if src.get("corpus") != "cap":
        return []
    try:
        url, case = sources.cap_case(src["reporter"], src["volume"], src["case"])
    except SourceUnavailable as e:
        return [Check("excerpt", "none", str(e))]
    ops = case["casebody"]["opinions"]
    if "opinion" in src:
        full = ops[int(src["opinion"])]["text"]
    else:
        full = "\n\n".join(o["text"] for o in ops)
    text = vector["input"]["text"]
    off = src["offset"]
    if full[off : off + len(text)] == text:
        return [
            Check("excerpt", "pass", "input is the opinion text at the offset", "cap")
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
        state = exists_state(sources, code, groups)
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


def verify_vector(sources, vector):
    checks = excerpt_check(sources, vector)
    text = vector["input"]["text"]
    for cite in vector["expected"]["citations"]:
        if cite.get("type") != "full_law":
            continue
        checks += span_checks(text, cite)
        existence = existence_check(sources, cite)
        checks += code_and_form_checks(sources, vector, cite, existence)
        checks.append(existence)
    return checks


def verdict(checks):
    failed = [c for c in checks if c.result == "fail"]
    if failed:
        return "contradicted:" + "; ".join(f"{c.claim}: {c.detail}" for c in failed)
    open_ = [c for c in checks if c.result == "none"]
    if open_:
        claims = sorted({c.claim for c in open_})
        return "unverifiable:" + ", ".join(claims)
    sources = sorted({c.source for c in checks if c.source})
    return "verified-by-source:" + "+".join(sources)


def run(dirs, fetcher):
    sources = Sources(fetcher)
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
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--json", type=Path, default=OUT / "verdicts.json")
    ap.add_argument("--md", type=Path, default=OUT / "report.md")
    args = ap.parse_args(argv)
    lock = json.loads(args.lock.read_text()) if args.lock.exists() else {}
    fetcher = Fetcher(args.cache, lock, offline=args.offline, refresh=args.refresh)
    try:
        results = run(args.vectors or DEFAULT_SETS, fetcher)
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
