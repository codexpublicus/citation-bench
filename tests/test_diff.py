"""diff.py tests on tiny synthetic saved runs."""

import csv
import json

import diff
import pytest


def cite(volume="1", page="1", type_="full_case", span=(0, 8), **kw):
    c = {
        "type": type_,
        "span": list(span),
        "groups": {"volume": volume, "reporter": "U.S.", "page": page},
        "metadata": {},
    }
    c.update(kw)
    return c


def item(iid, response, kind="find", text="1 U.S. 1 and 2 U.S. 2"):
    return {
        "id": iid,
        "kind": kind,
        "input": {"text": text, "format": "plain", "clean_steps": []},
        "response": response,
        "seconds": 0.001,
    }


def run(label, *inputs):
    return {
        "format": "citation-bench-results/1",
        "meta": {"label": label, "adapter": "x", "vectors": "v", "inputs": len(inputs)},
        "inputs": list(inputs),
    }


def test_key_uses_groups_then_span():
    assert diff.citation_key(cite()) == (
        "full_case",
        "1",
        "U.S.",
        "1",
        None,
        None,
        None,
    )
    id_cite = {"type": "id", "span": [4, 7], "groups": {}}
    assert diff.citation_key(id_cite) == ("id", "span", (4, 7))


def test_gained_lost_and_unchanged():
    base = item("a", {"citations": [cite(), cite("2", "2", span=(13, 21))]})
    cand = item("a", {"citations": [cite(), cite("3", "3", span=(13, 21))]})
    rows = diff.diff_input(base, cand)
    assert [(r["change"], r["citation"], r["text"]) for r in rows] == [
        ("lost", "full_case 2 U.S. 2", "2 U.S. 2"),
        ("gained", "full_case 3 U.S. 3", "2 U.S. 2"),
    ]


def test_field_changes_on_matched_citations():
    base = item("a", {"citations": [cite(metadata={"pin_cite": "2"}, year=None)]})
    cand = item("a", {"citations": [cite(metadata={"court": "scotus"}, year=1999)]})
    rows = diff.diff_input(base, cand)
    assert [(r["change"], r["field"], r["base"], r["candidate"]) for r in rows] == [
        ("changed", "metadata.court", "null", '"scotus"'),
        ("changed", "metadata.pin_cite", '"2"', "null"),
        ("changed", "year", "null", "1999"),
    ]


def test_missing_span_is_not_a_change():
    no_span = cite()
    del no_span["span"]
    rows = diff.diff_input(
        item("a", {"citations": [cite()]}), item("a", {"citations": [no_span]})
    )
    assert rows == []


def test_repeated_citations_pair_in_order():
    two = {"citations": [cite(), cite(span=(13, 21))]}
    one = {"citations": [cite()]}
    rows = diff.diff_input(item("a", two), item("a", one))
    assert [r["change"] for r in rows] == ["lost"]


def test_errors_resolution_and_text():
    rows = diff.diff_input(item("a", {"citations": []}), item("a", {"error": "boom"}))
    assert [(r["change"], r["candidate"]) for r in rows] == [("error", "boom")]
    res_b = item("r", {"citations": [cite()], "resolution": [0]}, kind="resolve")
    res_c = item("r", {"citations": [cite()], "resolution": [None]}, kind="resolve")
    assert [r["change"] for r in diff.diff_input(res_b, res_c)] == ["resolution"]
    same = item("r", {"citations": [cite()], "resolution": [4]}, kind="resolve")
    assert diff.diff_input(res_b, same) == []
    ann_b = item("n", {"text": "<0>x</0>"}, kind="annotate")
    ann_c = item("n", {"text": "x"}, kind="annotate")
    assert [r["change"] for r in diff.diff_input(ann_b, ann_c)] == ["text"]


def test_diff_runs_totals():
    base = run(
        "base",
        item("a", {"citations": [cite()]}),
        item("b", {"citations": [cite(metadata={"court": "x"})]}),
        item("only-base", {"citations": []}),
    )
    cand = run(
        "cand",
        item("a", {"citations": [cite(), cite("2", "2", span=(13, 21))]}),
        item("b", {"citations": [cite(metadata={"court": "y"})]}),
    )
    _, totals = diff.diff_runs(base, cand)
    assert totals["inputs"] == 2
    assert totals["only_in_base"] == 1
    assert totals["inputs_changed"] == 2
    assert (totals["gained"], totals["lost"]) == (1, 0)
    assert totals["citations_changed"] == 1
    assert totals["field_changes"] == {"metadata.court": 1}
    assert (totals["citations_base"], totals["citations_candidate"]) == (2, 3)


def test_main_writes_markdown_and_csv(tmp_path):
    base = run("base", item("a", {"citations": [cite()]}))
    cand = run("cand", item("a", {"citations": []}))
    (tmp_path / "b.json").write_text(json.dumps(base))
    (tmp_path / "c.json").write_text(json.dumps(cand))
    md, out = tmp_path / "report.md", tmp_path / "output.csv"
    assert (
        diff.main(
            [
                str(tmp_path / "b.json"),
                str(tmp_path / "c.json"),
                "--md",
                str(md),
                "--csv",
                str(out),
            ]
        )
        == 0
    )
    report = md.read_text()
    assert report.startswith("# base → cand")
    assert "**−1** lost" in report
    rows = list(csv.DictReader(out.open()))
    assert [(r["input"], r["change"], r["text"]) for r in rows] == [
        ("a", "lost", "1 U.S. 1")
    ]


def test_markdown_caps_rows():
    base = run("b", *[item(f"i{n}", {"citations": [cite()]}) for n in range(5)])
    cand = run("c", *[item(f"i{n}", {"citations": []}) for n in range(5)])
    rows, totals = diff.diff_runs(base, cand)
    report = diff.markdown(base, cand, rows, totals, max_rows=2)
    assert "top 2 shown" in report
    assert "2 of 5 changes shown" in report


def test_rejects_other_json(tmp_path):
    (tmp_path / "x.json").write_text("{}")
    with pytest.raises(SystemExit):
        diff.load(tmp_path / "x.json")


def test_shifted_positional_citations_pair_as_changed_spans():
    def id_cite(start):
        return {"type": "id", "span": [start, start + 3], "groups": {}}

    base = item("a", {"citations": [cite(), id_cite(10), id_cite(30)]})
    cand = item("a", {"citations": [cite(), id_cite(12), id_cite(32), id_cite(50)]})
    rows = diff.diff_input(base, cand)
    assert [(r["change"], r["field"]) for r in rows] == [
        ("gained", ""),
        ("changed", "span"),
        ("changed", "span"),
    ]
    assert rows[0]["reporter"] == "(id)"


def test_agreement_reporters_and_errors():
    other = cite("5", "5", span=(13, 21))
    other["groups"]["reporter"] = "F.2d"
    base = run(
        "base",
        item("a", {"citations": [cite(), other]}),
        item("b", {"citations": [cite()]}),
        item("c", {"citations": [cite()]}),
    )
    cand = run(
        "cand",
        item("a", {"citations": [cite()]}),
        item("b", {"citations": [cite()]}),
        item("c", {"error": "panic: boom"}),
    )
    rows, totals = diff.diff_runs(base, cand)
    # c is left out: the candidate answered it with an error
    assert (totals["found_by_both"], totals["found_by_either"]) == (2, 3)
    assert totals["agreement"] == pytest.approx(2 / 3)
    entry = totals["by_reporter"]["F.2d"]
    assert (entry["base"], entry["candidate"], entry["lost"]) == (1, 0, 1)
    assert totals["errors_candidate"] == {"c": "panic: boom"}
    report = diff.markdown(base, cand, rows, totals, max_rows=10)
    assert "agreement: **66.7%**" in report
    assert "| F.2d | 1 | 0 | 0 | 1 | 0 | lost in `a`: 2 U.S. 2 |" in report
    assert "## Errors in candidate (1)" in report and "panic: boom" in report


def test_html_citations_located_with_context():
    markup = "<p>See <i>Foo v. Bar</i>, 12 F.  Supp. 34 (1999).</p>"
    c = cite("12", "34", span=(0, 99))
    c["groups"]["reporter"] = "F. Supp."
    base = item("h", {"citations": [c]}, text=markup)
    base["input"]["format"] = "html"
    cand = item("h", {"citations": []}, text=markup)
    cand["input"]["format"] = "html"
    (row,) = diff.diff_input(base, cand)
    assert row["text"] == "See Foo v. Bar , 12 F. Supp. 34 (1999)."
    assert diff.Located(base)({"type": "id", "span": [0, 3], "groups": {}}) == ""
