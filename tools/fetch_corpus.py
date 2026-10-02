"""Download a pinned CourtListener opinion sample and convert it to find requests.

Usage:
  uv run tools/fetch_corpus.py [--size 1|10] [--out DIR]

The sample is the one eyecite's own benchmark runs on (benchmark/benchmark.py): a
Bernoulli sample of CourtListener opinions published as CSV under
storage.courtlistener.com/bulk-data/eyecite/tests/. corpora/courtlistener-<size>pct.json
pins the file by sha256; a download that doesn't match is refused.

The output is .cache/corpora/courtlistener-<size>pct/find.jsonl, one protocol-v2 find
request per opinion with no `expected` answer, plus a SOURCE.json copied from the
manifest. Each opinion is prepared exactly as eyecite 2.7.8's benchmark prepares it:
the first non-empty column of xml_harvard, html_lawbox, html_columbia, html_anon_2020
and html, with a leading <?xml ...?> declaration removed, or else plain_text; every
document, plain text included, goes in as markup with clean steps html and
inline_whitespace.
"""

import argparse
import bz2
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "corpora"
MARKUP_COLUMNS = (
    "xml_harvard",
    "html_lawbox",
    "html_columbia",
    "html_anon_2020",
    "html",
)
CLEAN_STEPS = ["html", "inline_whitespace"]
XML_DECLARATION = re.compile(
    r"^<\?xml.*?\?>"
)  # eyecite's pattern, `.` not spanning lines

csv.field_size_limit(sys.maxsize)


def manifest_path(size):
    return ROOT / "corpora" / f"courtlistener-{size}pct.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(manifest, dest):
    """Download the manifest's file to dest unless a verified copy is already there."""
    if dest.exists() and sha256(dest) == manifest["sha256"]:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(manifest["url"]) as r, open(partial, "wb") as f:
        while block := r.read(1 << 20):
            f.write(block)
    got = sha256(partial)
    if got != manifest["sha256"]:
        partial.unlink()
        raise SystemExit(
            f"{manifest['url']}: sha256 {got}, expected {manifest['sha256']}; "
            "the published file changed, so the pinned corpus is gone"
        )
    partial.replace(dest)
    return dest


def read_rows(data):
    """Parse the decompressed CSV bytes the way eyecite's benchmark does."""
    return csv.DictReader(io.StringIO(data.decode()), delimiter=",")


def prepare(row):
    """(column, text) for one opinion, following eyecite's benchmark."""
    for column in MARKUP_COLUMNS:
        if row[column]:
            return column, XML_DECLARATION.sub("", row[column], count=1)
    return "plain_text", row["plain_text"]


def requests(rows, corpus):
    for row in rows:
        column, text = prepare(row)
        yield {
            "id": f"{corpus}/{row['id']}",
            "kind": "find",
            "source": {"corpus": corpus, "opinion": row["id"], "column": column},
            "input": {"text": text, "format": "html", "clean_steps": CLEAN_STEPS},
            "options": {"remove_ambiguous": False},
        }


def convert(archive, out_dir, manifest):
    """Write find.jsonl and SOURCE.json; return the number of requests written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(bz2.decompress(Path(archive).read_bytes()))
    n = 0
    with open(out_dir / "find.jsonl", "w", encoding="utf-8") as f:
        for req in requests(rows, manifest["name"]):
            f.write(json.dumps(req, ensure_ascii=False) + "\n")
            n += 1
    if n != manifest["rows"]:
        raise SystemExit(f"{archive}: {n} rows, manifest says {manifest['rows']}")
    source = {k: manifest[k] for k in ("name", "url", "sha256", "rows")}
    source["converter"] = "tools/fetch_corpus.py"
    (out_dir / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--size", choices=("1", "10"), default="1", help="percent sample")
    ap.add_argument("--out", type=Path, help="output directory")
    args = ap.parse_args(argv)

    manifest = json.loads(manifest_path(args.size).read_text())
    archive = fetch(manifest, CACHE / Path(manifest["url"]).name)
    out_dir = args.out or CACHE / manifest["name"]
    n = convert(archive, out_dir, manifest)
    print(f"{n} find requests in {out_dir / 'find.jsonl'} (sha256 verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
