"""fetch_corpus.py tests on a tiny synthetic CourtListener CSV."""

import bz2
import csv
import hashlib
import io
import json

import fetch_corpus
import pytest

COLUMNS = (
    "id",
    "plain_text",
    "html",
    "html_lawbox",
    "html_columbia",
    "html_anon_2020",
    "xml_harvard",
)
ROWS = [
    # xml_harvard wins over everything, and loses its XML declaration
    {
        "id": "1",
        "plain_text": "p",
        "html": "<p>h</p>",
        "xml_harvard": (
            '<?xml version="1.0" encoding="utf-8"?>\n<opinion>1 U.S. 1</opinion>'
        ),
    },
    # html_lawbox beats html_columbia, html_anon_2020 and html
    {
        "id": "2",
        "html": "<p>h</p>",
        "html_columbia": "<p>c</p>",
        "html_lawbox": "<p>l</p>",
    },
    {"id": "3", "html": "<p>h</p>", "html_anon_2020": "<p>a</p>"},
    # plain text still goes in as markup, unchanged
    {"id": "4", "plain_text": "Foo, 1 U.S. 1 (1999) <?xml x?>"},
    # nothing at all: an empty document, as eyecite's benchmark would send it
    {"id": "5"},
]


def write_archive(path, rows=ROWS):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in COLUMNS})
    path.write_bytes(bz2.compress(buf.getvalue().encode()))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(path, sha, rows=5):
    return {"name": "tiny", "url": path.as_uri(), "sha256": sha, "rows": rows}


def test_convert_follows_eyecite_benchmark(tmp_path):
    archive = tmp_path / "tiny.csv.bz2"
    sha = write_archive(archive)
    assert fetch_corpus.convert(archive, tmp_path / "out", manifest(archive, sha)) == 5
    reqs = [json.loads(line) for line in (tmp_path / "out" / "find.jsonl").open()]
    assert [r["id"] for r in reqs] == [f"tiny/{n}" for n in "12345"]
    assert [r["source"]["column"] for r in reqs] == [
        "xml_harvard",
        "html_lawbox",
        "html_anon_2020",
        "plain_text",
        "plain_text",
    ]
    assert [r["input"]["text"] for r in reqs] == [
        "\n<opinion>1 U.S. 1</opinion>",
        "<p>l</p>",
        "<p>a</p>",
        "Foo, 1 U.S. 1 (1999) <?xml x?>",
        "",
    ]
    for r in reqs:
        assert r["kind"] == "find" and "expected" not in r
        assert r["input"]["format"] == "html"
        assert r["input"]["clean_steps"] == ["html", "inline_whitespace"]
    source = json.loads((tmp_path / "out" / "SOURCE.json").read_text())
    assert source["sha256"] == sha and source["rows"] == 5


def test_convert_checks_row_count(tmp_path):
    archive = tmp_path / "tiny.csv.bz2"
    sha = write_archive(archive)
    with pytest.raises(SystemExit):
        fetch_corpus.convert(archive, tmp_path / "out", manifest(archive, sha, rows=6))


def test_fetch_verifies_sha256(tmp_path):
    source = tmp_path / "src.csv.bz2"
    sha = write_archive(source)
    dest = tmp_path / "cache" / "tiny.csv.bz2"
    assert fetch_corpus.fetch(manifest(source, sha), dest) == dest
    assert dest.read_bytes() == source.read_bytes()
    with pytest.raises(SystemExit):
        fetch_corpus.fetch(manifest(source, "0" * 64), tmp_path / "other.csv.bz2")
    assert not (tmp_path / "other.csv.bz2").exists()


def test_manifests_are_pinned():
    for size in ("1", "10"):
        m = json.loads(fetch_corpus.manifest_path(size).read_text())
        assert len(m["sha256"]) == 64 and m["rows"] > 0
        assert m["name"] == f"courtlistener-{size}pct"
