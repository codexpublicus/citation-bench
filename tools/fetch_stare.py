"""Build, fetch and convert the stare.pub corpus: CAP cases and CourtListener records.

Usage:
  uv run tools/fetch_stare.py [--out DIR]          fetch the pinned sample, verify, convert
  uv run tools/fetch_stare.py name                 print the pinned corpus's name
  uv run tools/fetch_stare.py check-vectors [DIR ...]
                                                    check every vector taken from stare.pub
                                                    against the text stare.pub serves
  uv run tools/fetch_stare.py build [--version V] [--seed S] [--volumes N] [--cap N] [--cl N]
                                                    draw a new sample and pin it in corpora/

stare.pub publishes everything as static files: the citation index on idx.stare.pub
(a manifest per build, then one gzipped index per reporter volume, lines
page,source,ref) and the case text on data.stare.pub (CAP's volume zips under cap/, and
the CourtListener records it republishes under cl/c/<cluster>/<hash>.json.gz).

The sample is drawn from one index build, named by its version (v2026.10.22): N volumes
picked at random (seeded) from the build's own manifest, then a fixed number of CAP
cases and of CourtListener records picked at random from every case those volumes'
indexes list. Every volume is as likely as any other and every case in the drawn
volumes as likely as any other, so every case has about the same chance of being drawn.
CAP cases are the volume's own entries (a ref without a reporter in front); a
CourtListener record is a `cl` line on a page with no CAP case, which stare.pub says is
the same decision from another source. A record cited in two volumes counts once.

corpora/stare-pub-<version>.json pins the sample: the build's manifest by sha256, the
seed, and for every case its address and the sha256 of the JSON stare.pub serves for
it. A fetch that doesn't match is refused. Downloads are cached in .cache/stare/,
CAP cases are read out of their volume zip with HTTP range requests, so no whole
volume is downloaded, and every request names citation-bench in its User-Agent.

The output is .cache/corpora/stare-pub-<version>/find.jsonl, one protocol-v2 find
request per case with no `expected` answer, plus a SOURCE.json copied from the
manifest. A case's text is its casebody.opinions[].text joined with blank lines, as
plain text with no clean steps: the convention the vectors' CAP offsets use, so a span
an engine returns indexes the text stare.pub serves.
"""

import argparse
import gzip
import hashlib
import io
import json
import random
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
IDX = "https://idx.stare.pub/"
DATA = "https://data.stare.pub/"
SITE = "https://stare.pub/"
USER_AGENT = "citation-bench (+https://github.com/codexpublicus/citation-bench)"
VERSION = "v2026.10.22"
SEED = 40
VOLUMES = 600
CAP_CASES = 500
CL_RECORDS = 500
CLEAN_STEPS = []


def corpus_name(version):
    return f"stare-pub-{version}"


def manifest_path(version=VERSION):
    return ROOT / "corpora" / f"{corpus_name(version)}.json"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def request(url, headers=None):
    return urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, **(headers or {})}
    )


def get(url, headers=None, tries=4):
    """GET url's bytes, retrying a few times on a server error or a dropped line."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(request(url, headers), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429 or attempt == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == tries - 1:
                raise
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def cached(path, url, gunzip=False):
    """url's bytes, from path when it's there, downloaded into it when it isn't."""
    if path.exists():
        return path.read_bytes()
    data = get(url)
    if gunzip:
        data = gzip.decompress(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_bytes(data)
    partial.replace(path)
    return data


class RangeFile(io.RawIOBase):
    """A remote file read with HTTP range requests, enough for zipfile to seek in."""

    def __init__(self, url, size):
        self.url, self.size, self.pos = url, size, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def readinto(self, buf):
        if self.pos >= self.size or not len(buf):
            return 0
        end = min(self.pos + len(buf), self.size) - 1
        data = get(self.url, {"Range": f"bytes={self.pos}-{end}"})
        buf[: len(data)] = data
        self.pos += len(data)
        return len(data)


def remote_size(url):
    req = request(url)
    req.method = "HEAD"
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


class Stare:
    """stare.pub's static files, cached under cache/stare/."""

    def __init__(self, version, cache=CACHE):
        self.version = version
        self.cache = Path(cache) / "stare"
        self.zips = {}

    def manifest_bytes(self):
        url = f"{IDX}v/{self.version}/manifest.json"
        return cached(self.cache / "idx" / self.version / "manifest.json", url)

    def index(self, slug, volume):
        """A volume's index lines, every part of a split volume included."""
        lines = self.index_part(slug, volume, 0)
        if lines and lines[0].startswith("#parts,"):
            for n in range(1, len(lines[0].split(","))):
                lines += self.index_part(slug, volume, n)
        return parse_index("\n".join(lines))

    def index_part(self, slug, volume, part):
        name = f"{volume}.idx.gz" if part == 0 else f"{volume}.{part}.idx.gz"
        url = f"{IDX}v/{self.version}/{slug}/{name}"
        path = self.cache / "idx" / self.version / slug / name.removesuffix(".gz")
        return cached(path, url, gunzip=True).decode().splitlines()

    def cap_case(self, slug, folder, ref):
        """The bytes of a CAP case's JSON, read out of its volume zip."""
        path = self.cache / "cap" / slug / folder / f"{ref}.json"
        if path.exists():
            return path.read_bytes()
        url = cap_zip_url(slug, folder)
        if url not in self.zips:
            remote = RangeFile(url, remote_size(url))
            self.zips[url] = zipfile.ZipFile(io.BufferedReader(remote, 1 << 16))
        data = self.zips[url].read(f"json/{ref}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data

    def cl_record(self, ref):
        """The bytes of a CourtListener record's JSON (gunzipped)."""
        path = self.cache / "cl" / f"{ref}.json"
        return cached(path, cl_record_url(ref), gunzip=True)

    def case(self, entry):
        if entry["source"] == "cap":
            return self.cap_case(entry["slug"], entry["folder"], entry["case"])
        return self.cl_record(entry["ref"])


def parse_index(text):
    """Index lines as dicts: page, source, ref and any key=value fields after them."""
    out = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        page, source, ref, *rest = line.split(",")
        entry = {"page": page, "source": source, "ref": ref}
        for field in rest:
            key, _, value = field.partition("=")
            entry[key] = value
        out.append(entry)
    return out


def own_cap(entry):
    """A CAP case filed in this volume: no reporter in front of its ref, no `via`."""
    return (
        entry["source"] == "cap" and entry["ref"].count("/") <= 1 and "via" not in entry
    )


def cap_zip_url(slug, folder):
    return f"{DATA}cap/{slug}/{folder}.zip"


def cl_record_url(ref):
    return f"{DATA}cl/c/{ref}.json.gz"


def case_page_url(slug, volume, page):
    """The case page stare.pub gives every case: the bare page path, which lists every
    case that starts on the page when there is more than one."""
    return f"{SITE}c/{slug}/{volume}/{page}/"


def cap_entry(slug, volume, entry):
    folder, _, case = entry["ref"].rpartition("/")
    return {
        "source": "cap",
        "slug": slug,
        "volume": volume,
        "page": entry["page"],
        "folder": folder or volume,
        "case": case,
    }


def cl_entry(slug, volume, entry):
    return {
        "source": "cl",
        "slug": slug,
        "volume": volume,
        "page": entry["page"],
        "ref": entry["ref"],
    }


def index_volumes(manifest):
    """Every (slug, volume) the build indexes; a split volume's folders count once."""
    vols = set()
    for slug, folders in manifest["reporters"].items():
        parts = manifest.get("parts", {}).get(slug, {})
        split = {p["volume"]: v for v, ps in parts.items() for p in ps}
        vols.update((slug, split.get(f, f)) for f in folders)
    return sorted(vols)


def pools(volumes, index):
    """The CAP cases and CourtListener records the drawn volumes' indexes list."""
    cap, cl, seen = [], [], set()
    for slug, volume in volumes:
        entries = index(slug, volume)
        cap_pages = {e["page"] for e in entries if e["source"] == "cap"}
        for e in entries:
            if own_cap(e):
                cap.append(cap_entry(slug, volume, e))
            elif (
                e["source"] == "cl"
                and e["page"] not in cap_pages
                and e["ref"] not in seen
            ):
                seen.add(e["ref"])
                cl.append(cl_entry(slug, volume, e))
    return cap, cl


def draw(manifest, index, seed, n_volumes, n_cap, n_cl):
    """The sample: seeded volumes, then seeded cases from their indexes."""
    rng = random.Random(seed)
    volumes = rng.sample(index_volumes(manifest), n_volumes)
    cap, cl = pools(volumes, index)
    if len(cap) < n_cap or len(cl) < n_cl:
        raise SystemExit(
            f"{n_volumes} volumes list {len(cap)} CAP cases and {len(cl)} records; "
            f"asked for {n_cap} and {n_cl}"
        )
    picked = rng.sample(cap, n_cap) + rng.sample(cl, n_cl)
    return volumes, (len(cap), len(cl)), picked


def case_id(entry):
    if entry["source"] == "cap":
        return f"cap/{entry['slug']}/{entry['folder']}/{entry['case']}"
    return f"cl/{entry['ref']}"


def case_urls(entry):
    if entry["source"] == "cap":
        data = cap_zip_url(entry["slug"], entry["folder"])
        return {
            "url": case_page_url(entry["slug"], entry["volume"], entry["page"]),
            "data": data,
            "member": f"json/{entry['case']}.json",
        }
    return {"url": cl_record_url(entry["ref"])}


def case_text(record):
    """casebody.opinions[].text joined with blank lines."""
    return "\n\n".join(op.get("text") or "" for op in record["casebody"]["opinions"])


def build(args):
    stare = Stare(args.version)
    manifest_bytes = stare.manifest_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("version") != args.version:
        raise SystemExit(
            f"manifest names {manifest.get('version')}, not {args.version}"
        )
    _volumes, pool_sizes, picked = draw(
        manifest, stare.index, args.seed, args.volumes, args.cap, args.cl
    )
    cases = []
    for n, entry in enumerate(sorted(picked, key=case_id), 1):
        data = stare.case(entry)
        record = json.loads(data)
        cases.append(
            {
                "id": case_id(entry),
                **entry,
                **case_urls(entry),
                "sha256": sha256(data),
                "chars": len(case_text(record)),
            }
        )
        if n % 100 == 0:
            print(f"{n}/{len(picked)} cases", file=sys.stderr)
    pinned = {
        "name": corpus_name(args.version),
        "index_version": args.version,
        "manifest_url": f"{IDX}v/{args.version}/manifest.json",
        "manifest_sha256": sha256(manifest_bytes),
        "seed": args.seed,
        "volumes_drawn": args.volumes,
        "pool": {"cap": pool_sizes[0], "cl": pool_sizes[1]},
        "rows": len(cases),
        "pinned": time.strftime("%Y-%m-%d", time.gmtime()),
        "based_on": manifest.get("based_on", []),
        "text": "casebody.opinions[].text joined with blank lines; plain, no clean steps",
        "provenance": (
            "A sample of the case text stare.pub serves, drawn by tools/fetch_stare.py "
            "build from index build "
            f"{args.version}: {args.volumes} volumes at random (seed {args.seed}) from "
            "the build's manifest, then CAP cases and CourtListener records at random "
            "from the drawn volumes' indexes. CAP cases come from the volume zips on "
            "data.stare.pub/cap/; CourtListener records from data.stare.pub/cl/c/, "
            "each carrying its own license and attribution."
        ),
        "cases": cases,
    }
    path = manifest_path(args.version)
    path.write_text(json.dumps(pinned, indent=1, ensure_ascii=False) + "\n")
    print(f"pinned {len(cases)} cases in {path.relative_to(ROOT)}")
    return 0


def requests(pinned, fetch_case):
    """One find request per pinned case, refusing any case whose bytes changed."""
    for case in pinned["cases"]:
        data = fetch_case(case)
        got = sha256(data)
        if got != case["sha256"]:
            raise SystemExit(
                f"{case['id']}: sha256 {got}, expected {case['sha256']}; "
                "stare.pub serves different bytes for a case pinned by this corpus"
            )
        record = json.loads(data)
        source = {"corpus": pinned["name"], "source": case["source"]}
        source.update(
            {k: case[k] for k in ("slug", "volume", "page", "case", "ref") if k in case}
        )
        source.update({k: case[k] for k in ("url", "data", "member") if k in case})
        if case["source"] == "cl":
            source["license"] = (record.get("license") or {}).get("id")
            source["attribution"] = record.get("attribution")
        yield {
            "id": f"{pinned['name']}/{case['id']}",
            "kind": "find",
            "source": source,
            "input": {
                "text": case_text(record),
                "format": "plain",
                "clean_steps": CLEAN_STEPS,
            },
            "options": {"remove_ambiguous": False},
        }


def convert(pinned, out_dir, fetch_case):
    """Write find.jsonl and SOURCE.json; return the number of requests written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out_dir / "find.jsonl", "w", encoding="utf-8") as f:
        for req in requests(pinned, fetch_case):
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
            n += 1
    if n != pinned["rows"]:
        raise SystemExit(f"{n} cases, manifest says {pinned['rows']}")
    keep = (
        "name",
        "index_version",
        "manifest_url",
        "manifest_sha256",
        "seed",
        "rows",
        "based_on",
        "text",
    )
    source = {k: pinned[k] for k in keep if k in pinned}
    source["converter"] = "tools/fetch_stare.py"
    (out_dir / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n")
    return n


def source_case(source):
    """The case a vector's stare.pub source names, as fetch_case takes it."""
    if source["source"] == "cl":
        return {"source": "cl", "ref": source["ref"]}
    folder = source["data"].rsplit("/", 1)[1].removesuffix(".zip")
    return {
        "source": "cap",
        "slug": source["slug"],
        "folder": folder,
        "case": source["case"],
    }


def source_text(source, record):
    if "opinion" in source:
        return record["casebody"]["opinions"][int(source["opinion"])]["text"]
    return case_text(record)


def check_vector(vector, fetch_case):
    """None if a vector's stare.pub source still holds its input, else what's wrong."""
    source = vector["source"]
    data = fetch_case(source_case(source))
    if sha256(data) != source["sha256"]:
        return "stare.pub serves different bytes for the case"
    if "offset" not in source:
        return None
    text = source_text(source, json.loads(data))
    start = source["offset"]
    want = vector["input"]["text"]
    if text[start : start + len(want)] != want:
        return f"the input isn't at offset {start}"
    return None


def check_vectors(dirs, fetch_case):
    """(checked, problems) over every vector whose source is stare.pub."""
    checked, problems = 0, []
    for d in dirs:
        for path in sorted(Path(d).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                vector = json.loads(line)
                source = vector.get("source") or {}
                if source.get("corpus") != "stare-pub":
                    continue
                checked += 1
                problem = check_vector(vector, fetch_case)
                if problem:
                    problems.append(f"{vector['id']}: {problem}")
    return checked, problems


def fetch(args):
    pinned = json.loads(manifest_path(args.version).read_text())
    stare = Stare(pinned["index_version"])
    got = sha256(stare.manifest_bytes())
    if got != pinned["manifest_sha256"]:
        raise SystemExit(
            f"{pinned['manifest_url']}: sha256 {got}, expected {pinned['manifest_sha256']}"
        )
    out_dir = args.out or CACHE / "corpora" / pinned["name"]
    n = convert(pinned, out_dir, stare.case)
    print(f"{n} find requests in {out_dir / 'find.jsonl'} (sha256 verified)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command")
    b = sub.add_parser("build", help="draw a new sample and pin it in corpora/")
    b.add_argument("--version", default=VERSION, help="index build, e.g. v2026.10.22")
    b.add_argument("--seed", type=int, default=SEED)
    b.add_argument("--volumes", type=int, default=VOLUMES)
    b.add_argument("--cap", type=int, default=CAP_CASES)
    b.add_argument("--cl", type=int, default=CL_RECORDS)
    sub.add_parser("name", help="print the pinned corpus's name")
    c = sub.add_parser("check-vectors", help="check vectors against stare.pub's text")
    c.add_argument("dirs", nargs="*", type=Path)
    ap.add_argument("--version", default=VERSION, help="the pinned corpus to fetch")
    ap.add_argument("--out", type=Path, help="output directory")
    args = ap.parse_args(argv)
    if args.command == "check-vectors":
        dirs = args.dirs or sorted(
            p for p in (ROOT / "vectors").iterdir() if p.is_dir()
        )
        checked, problems = check_vectors(dirs, Stare(args.version).case)
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"{checked} vectors from stare.pub, {len(problems)} that don't match")
        return 1 if problems else 0
    if args.command == "name":
        print(corpus_name(args.version))
        return 0
    return build(args) if args.command == "build" else fetch(args)


if __name__ == "__main__":
    sys.exit(main())
