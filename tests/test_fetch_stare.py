"""fetch_stare.py tests on a tiny synthetic stare.pub: a manifest, two volume indexes,
a CAP volume zip and a CourtListener record, served from memory."""

import gzip
import io
import json
import zipfile

import fetch_stare
import pytest

VERSION = "v2099.01.01"

CAP_CASE = {
    "name_abbreviation": "Foo v. Bar",
    "casebody": {"opinions": [{"text": "See 1 U.S. 1."}, {"text": "Dissent."}]},
}
CL_RECORD = {
    "name_abbreviation": "Baz v. Qux",
    "casebody": {"opinions": [{"text": "Cf. 2 F.4th 3."}]},
    "license": {"id": "CC-PDM-1.0"},
    "attribution": {"name": "CourtListener", "publisher": "Free Law Project"},
}
MANIFEST = {
    "version": VERSION,
    "reporters": {"a2d": ["10", "11", "11-2"], "f4th": ["2"]},
    "parts": {
        "a2d": {
            "11": [
                {"volume": "11", "first_page": 1, "last_page": 50},
                {"volume": "11-2", "first_page": 51, "last_page": 99},
            ]
        }
    },
}
INDEXES = {
    # own cases, an alias of a case filed elsewhere, and a CourtListener record on a page
    # that has a CAP case (the same decision), which isn't drawn
    "a2d/10": "1,cap,0001-01\n5,cap,0005-01\n5,cl,7/aaaa\n9,cap,ri/1/0009-01,via=cl:8\n",
    # a split volume: the second folder's cases carry the folder in their ref
    "a2d/11": "#parts,60\n1,cap,0001-01\n",
    "a2d/11.1": "60,cap,11-2/0060-01\n",
    # CourtListener only; record 9 is cited on two pages and counts once
    "f4th/2": "3,cl,9/bbbb\n4,cl,9/bbbb\n7,cl,10/cccc\n",
}


def zip_bytes(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


@pytest.fixture
def site(monkeypatch):
    """Serve the synthetic stare.pub from memory, honouring Range like the real hosts."""
    files = {
        f"{fetch_stare.IDX}v/{VERSION}/manifest.json": json.dumps(MANIFEST).encode(),
        f"{fetch_stare.DATA}cap/a2d/10.zip": zip_bytes(
            {
                "json/0001-01.json": json.dumps(CAP_CASE),
                "json/0005-01.json": json.dumps(CAP_CASE),
            }
        ),
        f"{fetch_stare.DATA}cl/c/9/bbbb.json.gz": gzip.compress(
            json.dumps(CL_RECORD).encode()
        ),
    }
    for key, text in INDEXES.items():
        name = key.replace(".1", ".1.idx.gz") if ".1" in key else key + ".idx.gz"
        files[f"{fetch_stare.IDX}v/{VERSION}/{name}"] = gzip.compress(text.encode())
    hits = []

    def get(url, headers=None, tries=4):
        hits.append(url)
        data = files[url]
        rng = (headers or {}).get("Range")
        if rng:
            start, end = map(int, rng.removeprefix("bytes=").split("-"))
            return data[start : end + 1]
        return data

    monkeypatch.setattr(fetch_stare, "get", get)
    monkeypatch.setattr(fetch_stare, "remote_size", lambda url: len(files[url]))
    return files, hits


def test_parse_index_skips_comments_and_keeps_fields():
    entries = fetch_stare.parse_index("#parts,60\n\n9,cap,ri/1/0009-01,via=cl:8\n")
    assert entries == [
        {"page": "9", "source": "cap", "ref": "ri/1/0009-01", "via": "cl:8"}
    ]
    assert not fetch_stare.own_cap(entries[0])
    assert fetch_stare.own_cap({"source": "cap", "ref": "11-2/0060-01"})


def test_index_volumes_folds_split_folders():
    assert fetch_stare.index_volumes(MANIFEST) == [
        ("a2d", "10"),
        ("a2d", "11"),
        ("f4th", "2"),
    ]


def test_pools_and_draw(site, tmp_path):
    stare = fetch_stare.Stare(VERSION, tmp_path)
    vols = fetch_stare.index_volumes(MANIFEST)
    cap, cl = fetch_stare.pools(vols, stare.index)
    assert [fetch_stare.case_id(e) for e in cap] == [
        "cap/a2d/10/0001-01",
        "cap/a2d/10/0005-01",
        "cap/a2d/11/0001-01",
        "cap/a2d/11-2/0060-01",
    ]
    assert [fetch_stare.case_id(e) for e in cl] == ["cl/9/bbbb", "cl/10/cccc"]
    first = fetch_stare.draw(MANIFEST, stare.index, 1, 3, 2, 1)
    assert first == fetch_stare.draw(MANIFEST, stare.index, 1, 3, 2, 1)
    with pytest.raises(SystemExit):
        fetch_stare.draw(MANIFEST, stare.index, 1, 3, 9, 1)


def test_cap_case_reads_one_member_by_range(site, tmp_path):
    _files, hits = site
    stare = fetch_stare.Stare(VERSION, tmp_path)
    data = stare.cap_case("a2d", "10", "0005-01")
    assert json.loads(data) == CAP_CASE
    zip_url = f"{fetch_stare.DATA}cap/a2d/10.zip"
    assert hits and set(hits) == {zip_url}
    hits.clear()
    assert stare.cap_case("a2d", "10", "0005-01") == data  # cached
    assert not hits


def pinned(files, tmp_path):
    stare = fetch_stare.Stare(VERSION, tmp_path)
    entries = [
        fetch_stare.cap_entry("a2d", "10", {"page": "5", "ref": "0005-01"}),
        fetch_stare.cl_entry("f4th", "2", {"page": "3", "ref": "9/bbbb"}),
    ]
    cases = []
    for e in entries:
        data = stare.case(e)
        cases.append(
            {
                "id": fetch_stare.case_id(e),
                **e,
                **fetch_stare.case_urls(e),
                "sha256": fetch_stare.sha256(data),
            }
        )
    return stare, {"name": "stare-pub-tiny", "rows": 2, "cases": cases}


def test_convert_writes_plain_requests(site, tmp_path):
    files, _ = site
    stare, pin = pinned(files, tmp_path)
    out = tmp_path / "out"
    assert fetch_stare.convert(pin, out, stare.case) == 2
    reqs = [json.loads(line) for line in (out / "find.jsonl").open()]
    assert [r["id"] for r in reqs] == [
        "stare-pub-tiny/cap/a2d/10/0005-01",
        "stare-pub-tiny/cl/9/bbbb",
    ]
    cap, cl = reqs
    assert cap["input"] == {
        "text": "See 1 U.S. 1.\n\nDissent.",
        "format": "plain",
        "clean_steps": [],
    }
    assert cap["source"]["url"] == "https://stare.pub/c/a2d/10/5/"
    assert cap["source"]["data"] == "https://data.stare.pub/cap/a2d/10.zip"
    assert cap["source"]["member"] == "json/0005-01.json"
    assert cl["source"]["url"] == "https://data.stare.pub/cl/c/9/bbbb.json.gz"
    assert cl["source"]["license"] == "CC-PDM-1.0"
    assert cl["source"]["attribution"]["publisher"] == "Free Law Project"
    for r in reqs:
        assert r["kind"] == "find" and "expected" not in r
    source = json.loads((out / "SOURCE.json").read_text())
    assert source["converter"] == "tools/fetch_stare.py" and source["rows"] == 2


def test_convert_refuses_changed_bytes(site, tmp_path):
    files, _ = site
    stare, pin = pinned(files, tmp_path)
    pin["cases"][1]["sha256"] = "0" * 64
    with pytest.raises(SystemExit):
        fetch_stare.convert(pin, tmp_path / "out", stare.case)


def test_convert_checks_row_count(site, tmp_path):
    files, _ = site
    stare, pin = pinned(files, tmp_path)
    pin["rows"] = 3
    with pytest.raises(SystemExit):
        fetch_stare.convert(pin, tmp_path / "out", stare.case)


def test_pinned_corpus():
    m = json.loads(fetch_stare.manifest_path().read_text())
    assert m["name"] == fetch_stare.corpus_name(fetch_stare.VERSION)
    assert len(m["manifest_sha256"]) == 64 and m["rows"] == len(m["cases"]) > 0
    assert all(len(c["sha256"]) == 64 for c in m["cases"])
    assert len({c["id"] for c in m["cases"]}) == len(m["cases"])
    assert {c["source"] for c in m["cases"]} == {"cap", "cl"}
