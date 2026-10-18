"""bench/statutes.py: law kinds, matching, P/R/F1, provenance groups and agreement."""

import json

import pytest
import statutes

ROOT = statutes.ROOT


@pytest.mark.parametrize(
    "code, jurisdiction, kind",
    [
        ("U.S.C.", "United States", "federal statute"),
        ("Stat.", "United States", "federal statute"),
        ("Pub. L.", None, "federal statute"),
        ("Conn. Gen. Stat.", "Connecticut", "state statute"),
        ("N.Y. Penal Law", "New York", "state statute"),
        ("C.F.R.", "United States", "regulation"),
        ("Fed. Reg.", "United States", "regulation"),
        ("FR", "United States", "regulation"),
        ("Treas. Reg.", "United States", "regulation"),
        ("N.Y. Comp. Codes R. & Regs.", "New York", "regulation"),
        ("N.J. Admin. Code", "New Jersey", "regulation"),
        ("U.S.S.G.", "United States", "guideline"),
        ("USSG", "United States", "guideline"),
        ("U.S. Sentencing Guidelines Manual", "United States", "guideline"),
        ("Conn. Practice Book", "Connecticut", "court rule"),
        ("Fed. R. Civ. P.", "United States", "court rule"),
        ("Tex. R. App. P.", "Texas", "court rule"),
        ("Mich. Ct. R.", "Michigan", "court rule"),
        ("U.S. Const.", "United States", "constitution"),
        ("N.M. Const.", "New Mexico", "constitution"),
    ],
)
def test_law_kind(code, jurisdiction, kind):
    assert statutes.law_kind(code, jurisdiction) == kind


def law(span, code="Conn. Gen. Stat.", section="52-577", **meta):
    return {
        "type": "full_law",
        "span": span,
        "groups": {"reporter": "General Statutes", "section": section},
        "reporter_normalized": code,
        "metadata": meta,
    }


def unknown(span):
    return {"type": "unknown", "span": span, "groups": {}, "metadata": {}}


def test_match_pairs_by_overlapping_span():
    e1, e2 = law([0, 10]), law([20, 30])
    g1, g2 = law([22, 28]), law([40, 45])
    pairs, extra = statutes.match([e1, e2], [g1, g2])
    assert pairs == [(e1, None), (e2, g1)]
    assert extra == [g2]


def test_fields_right_ignores_the_reporter_as_written():
    e = law([0, 10])
    p = law([0, 10])
    p["groups"]["reporter"] = "C.G.S."
    assert statutes.fields_right(e, p)
    p["groups"]["section"] = "52"
    assert not statutes.fields_right(e, p)


def test_prf():
    assert statutes.prf(1, 2, 4) == (0.5, 0.25, pytest.approx(1 / 3))
    assert statutes.prf(0, 0, 3) == (None, 0.0, None)
    assert statutes.prf(0, 2, 3) == (0.0, 0.0, 0.0)


def vector(vid, text, cites, provenance=None):
    v = {
        "id": vid,
        "kind": "find",
        "source": {"corpus": "x"},
        "input": {"text": text, "format": "plain", "clean_steps": []},
        "expected": {"citations": cites},
    }
    if provenance:
        v["provenance"] = {"status": provenance}
    return v


TEXT = "See General Statutes § 52-577."  # the citation is [4, 29), the § at 21


def write_set(path, name, vectors, status=None):
    path.mkdir()
    source = {"name": name}
    if status:
        source["provenance"] = {"status": status}
    (path / "SOURCE.json").write_text(json.dumps(source))
    (path / "find.jsonl").write_text("".join(json.dumps(v) + "\n" for v in vectors))
    return path


def save(path, label, answers):
    path.write_text(
        json.dumps(
            {
                "format": "citation-bench-results/1",
                "meta": {"label": label},
                "inputs": [
                    {"id": i, "kind": "find", "response": r} for i, r in answers.items()
                ],
            }
        )
    )
    return path


@pytest.fixture
def sets(tmp_path):
    ref = write_set(
        tmp_path / "ref",
        "ref",
        [
            vector("ref/a", TEXT, [law([4, 29], jurisdiction="Connecticut")]),
            vector("ref/b", TEXT, [law([4, 29], jurisdiction="Connecticut")]),
            # A vector-level provenance overrides the set's.
            vector("ref/c", TEXT, [law([4, 29])], provenance="engine-output"),
        ],
        status="hand-checked",
    )
    new = write_set(
        tmp_path / "new",
        "new",
        [vector("new/a", TEXT, [law([4, 29], jurisdiction="Connecticut")])],
    )
    return statutes.load_sets([ref, new])


def test_provenance_groups(sets):
    groups = statutes.groups_of(sets)
    assert list(groups) == ["reference", "engine-output", "unrecorded"]
    assert set(groups["reference"]) == {"ref/a", "ref/b"}
    assert set(groups["engine-output"]) == {"ref/c"}
    assert set(groups["unrecorded"]) == {"new/a"}


def test_score_counts_found_fields_and_bare_sections(sets, tmp_path):
    good = law([4, 29], jurisdiction="Connecticut")
    wrong_section = law([4, 29], section="52")
    runs = statutes.load_runs(
        [
            save(
                tmp_path / "x1.json",
                "x",
                {"ref/a": {"citations": [good]}, "ref/b": {"citations": []}},
            ),
            # A second run with the same label merges into the first.
            save(
                tmp_path / "x2.json",
                "x",
                {"new/a": {"citations": [wrong_section, law([0, 3])]}},
            ),
            save(
                tmp_path / "y.json",
                "y",
                {
                    "ref/a": {"citations": [unknown([21, 22])]},
                    "ref/b": {"citations": [unknown([21, 22])]},
                },
            ),
        ]
    )
    assert set(runs["x"]) == {"ref/a", "ref/b", "new/a"}
    analysis = statutes.analyse(sets, runs)
    ref = analysis["groups"]["reference"]
    assert ref["vectors"] == 2
    x = ref["engines"]["x"]
    assert x["kinds"]["state statute"] == {
        "expected": 2,
        "reported": 1,
        "found": 1,
        "fields_right": 1,
        "bare_section": 0,
    }
    assert x["fields"]["jurisdiction"] == {"right": 1, "wrong": 0, "missing": 0}
    assert x["misses"] == ["ref/b"]
    y = ref["engines"]["y"]["kinds"]["state statute"]
    assert (y["found"], y["bare_section"]) == (0, 2)

    unrec = analysis["groups"]["unrecorded"]["engines"]["x"]
    t = unrec["kinds"]["state statute"]
    # Found at the right place with the wrong section, plus a law citation nobody expected.
    assert (t["expected"], t["reported"], t["found"], t["fields_right"]) == (1, 2, 1, 0)
    assert unrec["fields"]["jurisdiction"]["missing"] == 1


def test_agreement_is_reported_apart_and_labelled(sets, tmp_path):
    good = law([4, 29], jurisdiction="Connecticut")
    runs = statutes.load_runs(
        [
            save(tmp_path / "a.json", "a", {"ref/a": {"citations": [good]}}),
            save(
                tmp_path / "b.json",
                "b",
                {"ref/a": {"citations": [good]}, "ref/b": {"citations": []}},
            ),
        ]
    )
    analysis = statutes.analyse(sets, runs)
    # Only vectors both engines answered count.
    assert analysis["agreement"]["a | b"]["state statute"] == {
        "vectors": 1,
        "same": 1,
        "same_place": 1,
        "neither": 0,
    }
    md = statutes.markdown(analysis)
    assert "### Agreement between engines" in md
    assert "This is agreement, not accuracy" in md
    assert "### Reference vectors" in md
    assert "(not a reference)" in md


def test_main_writes_markdown_and_json(sets, tmp_path):
    run = save(tmp_path / "x.json", "x", {"ref/a": {"citations": []}})
    md, js = tmp_path / "out.md", tmp_path / "out.json"
    statutes.main(
        [
            "--vectors",
            str(tmp_path / "ref"),
            str(run),
            "--md",
            str(md),
            "--json",
            str(js),
        ]
    )
    summary = json.loads(js.read_text())
    assert summary["groups"]["reference"]["engines"]["x"]["all"]["expected"] == 1
    assert "Statute and court-rule citations" in md.read_text()


def test_committed_sets_have_known_provenance():
    for source in (ROOT / "vectors").glob("*/SOURCE.json"):
        status = json.loads(source.read_text()).get("provenance", {}).get("status")
        assert status in statutes.STATUSES, source
    for v in statutes.load_vectors(ROOT / "vectors" / "statutes-proposed"):
        assert v["provenance"]["status"] == "proposed", v["id"]


def test_proposed_vectors_cover_the_thin_kinds():
    vectors = statutes.load_sets([ROOT / "vectors" / "statutes-proposed"])
    kinds = {
        statutes.cite_kind(c)
        for v, _, _ in vectors.values()
        for c in v["expected"]["citations"]
    }
    assert {
        "federal statute",
        "regulation",
        "guideline",
        "court rule",
        "constitution",
    } <= kinds
    for v, _, _ in vectors.values():
        text = v["input"]["text"]
        for c in v["expected"]["citations"]:
            start, end = c["span"]
            assert c["groups"]["reporter"] in text[start:end], v["id"]
