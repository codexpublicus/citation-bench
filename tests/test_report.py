"""report.py tests on tiny synthetic saved runs."""

import json

import report


def cite(volume, page="1"):
    return {
        "type": "full_case",
        "span": [0, 8],
        "groups": {"volume": volume, "reporter": "U.S.", "page": page},
        "metadata": {},
    }


def run(path, label, inputs, **meta):
    path.write_text(
        json.dumps(
            {
                "format": "citation-bench-results/1",
                "meta": {
                    "label": label,
                    "adapter": "x",
                    "vectors": "v",
                    "inputs": len(inputs),
                    "source": {"name": "corpus-x"},
                    "ms_per_kb": 2.0,
                    **meta,
                },
                "inputs": inputs,
            }
        )
    )
    return path


def item(iid, response, kind="find", mismatches=None):
    return {
        "id": iid,
        "kind": kind,
        "input": {"text": "1 U.S. 1; 2 U.S. 1", "format": "plain"},
        "response": response,
        "seconds": 0.001,
        "mismatches": mismatches,
    }


def test_report_files(tmp_path):
    vec = run(
        tmp_path / "v.json",
        "citare-x",
        [item("a", {}, "find", []), item("b", {}, "annotate", ["text"])],
    )
    vec0 = run(
        tmp_path / "v0.json",
        "eyecite-9",
        [item("a", {}, "find", []), item("b", {}, "annotate", [])],
    )
    corpus = run(
        tmp_path / "c.json",
        "citare-x",
        [item("o", {"citations": [cite("1")]})],
        engine={"name": "citare", "version": "0.4.1", "commit": "abcdef1234567890"},
    )
    corpus0 = run(
        tmp_path / "c0.json",
        "eyecite-9",
        [item("o", {"citations": [cite("1"), cite("2")]})],
        cached={"key": "f" * 64},
    )
    prev = run(tmp_path / "p.json", "v0.1.0", [item("o", {"citations": []})])
    known = tmp_path / "known"
    known.write_text("b\nc\n")
    out = tmp_path / "out"
    assert (
        report.main(
            [
                *("--vectors", str(vec), "--vectors-base", str(vec0)),
                *("--corpus", str(corpus), "--corpus-base", str(corpus0)),
                *("--previous-corpus", str(prev), "--known-failures", str(known)),
                *("--out", str(out), "--link", "https://example.test/run"),
            ]
        )
        == 0
    )
    md = (out / "bench-report.md").read_text()
    assert "| vectors: find | 1/1 (100.0%) | 1/1 (100.0%) |  |" in md
    assert "| vectors: annotate | 0/1 (0.0%) | 1/1 (100.0%) |  |" in md
    assert "| agreement with eyecite | 50.0% |  | 0.0% |" in md
    assert "no regressions, 1 newly passing" in md
    assert "stored run (key `ffffffffffff`)" in md
    assert "built from citare 0.4.1 at `abcdef123456`" in md
    assert "+0 gained, −1 lost" in md and "+1 gained, −0 lost" in md
    assert md.endswith("https://example.test/run\n")
    summary = json.loads((out / "summary.json").read_text())
    assert summary["ratchet"] == {"regressions": [], "fixed": ["c"]}
    assert summary["previous"]["gained"] == 1
    assert "50.0% agreement with eyecite-9" in (out / "headline.md").read_text()
    assert (out / "comment.md").read_text() == md
    assert (out / "vs-eyecite.csv").exists() and (out / "vs-previous.csv").exists()


def test_comment_drops_diff_tables_when_too_long(tmp_path, monkeypatch):
    many = [item(f"o{i}", {"citations": [cite(str(i))]}) for i in range(30)]
    none = [item(f"o{i}", {"citations": []}) for i in range(30)]
    paths = [
        run(tmp_path / "v.json", "c", []),
        run(tmp_path / "v0.json", "e", []),
        run(tmp_path / "c.json", "c", many),
        run(tmp_path / "c0.json", "e", none),
    ]
    monkeypatch.setattr(report, "COMMENT_LIMIT", 1500)
    out = tmp_path / "out"
    report.main(
        [
            *("--vectors", str(paths[0]), "--vectors-base", str(paths[1])),
            *("--corpus", str(paths[2]), "--corpus-base", str(paths[3])),
            *("--out", str(out), "--previous-note", "no earlier release"),
        ]
    )
    comment = (out / "comment.md").read_text()
    assert len(comment) <= 1500 and "<details>" not in comment
    assert "no earlier release" in comment
    assert "<details>" in (out / "bench-report.md").read_text()


def test_report_includes_statute_metrics(tmp_path):
    law = {
        "type": "full_law",
        "span": [4, 29],
        "groups": {"reporter": "General Statutes", "section": "52-577"},
        "reporter_normalized": "Conn. Gen. Stat.",
        "metadata": {"jurisdiction": "Connecticut"},
    }
    sets = tmp_path / "statutes"
    sets.mkdir()
    (sets / "SOURCE.json").write_text(
        json.dumps({"name": "statutes", "provenance": {"status": "hand-checked"}})
    )
    (sets / "find.jsonl").write_text(
        json.dumps(
            {
                "id": "s/1",
                "kind": "find",
                "source": {"corpus": "x"},
                "input": {"text": "See General Statutes § 52-577.", "format": "plain"},
                "expected": {"citations": [law]},
            }
        )
        + "\n"
    )
    citare = run(tmp_path / "sc.json", "citare-x", [item("s/1", {"citations": [law]})])
    eyecite = run(tmp_path / "se.json", "eyecite-9", [item("s/1", {"citations": []})])
    paths = [
        run(tmp_path / "v.json", "c", []),
        run(tmp_path / "v0.json", "e", []),
        run(tmp_path / "c.json", "c", []),
        run(tmp_path / "c0.json", "e", []),
    ]
    out = tmp_path / "out"
    report.main(
        [
            *("--vectors", str(paths[0]), "--vectors-base", str(paths[1])),
            *("--corpus", str(paths[2]), "--corpus-base", str(paths[3])),
            *("--statute-vectors", str(sets)),
            *("--statute-runs", str(citare), str(eyecite)),
            *("--out", str(out)),
        ]
    )
    md = (out / "bench-report.md").read_text()
    assert "### Statute and court-rule citations" in md
    assert "| **all** | `citare-x` | 1 | 1 | 100.0% | 100.0% | 100.0% | 1 |" in md
    assert "This is agreement, not accuracy" in md
    assert "### Statute and court-rule citations" in (out / "comment.md").read_text()
    summary = json.loads((out / "summary.json").read_text())
    ref = summary["statutes"]["groups"]["reference"]["engines"]
    assert ref["eyecite-9"]["all"]["found"] == 0
    headline = (out / "headline.md").read_text()
    assert (
        "Statutes and court rules (1 reference vectors, fields right): F1" in headline
    )
    assert "citare-x 100.0%" in headline


def test_comparison_sample_is_a_labelled_secondary(tmp_path):
    def corpus(name, label, volumes, **meta):
        inputs = [item("o", {"citations": [cite(v) for v in volumes]})]
        path = run(tmp_path / f"{name}-{label}.json", label, inputs, **meta)
        data = json.loads(path.read_text())
        data["meta"]["source"] = {"name": name}
        path.write_text(json.dumps(data))
        return path

    stare, sample = "stare-pub-v2026.10.22", "courtlistener-1pct"
    paths = [
        run(tmp_path / "v.json", "citare-x", [item("a", {}, "find", [])]),
        run(tmp_path / "v0.json", "eyecite-9", [item("a", {}, "find", [])]),
        corpus(stare, "citare-x", ["1"]),
        corpus(stare, "eyecite-9", ["1"], cached={"key": "a" * 64}),
        corpus(sample, "citare-x", ["1", "2"]),
        corpus(sample, "eyecite-9", ["1"], cached={"key": "b" * 64}),
        corpus(sample, "v0.1.0", ["3"]),
    ]
    out = tmp_path / "out"
    report.main(
        [
            *("--vectors", str(paths[0]), "--vectors-base", str(paths[1])),
            *("--corpus", str(paths[2]), "--corpus-base", str(paths[3])),
            *("--comparison", str(paths[4]), "--comparison-base", str(paths[5])),
            *("--previous-comparison", str(paths[6]), "--out", str(out)),
            *("--previous-note", "never shown: a previous run exists"),
        ]
    )
    md = (out / "bench-report.md").read_text()
    primary, secondary = md.split("**Secondary: eyecite's comparison sample**")
    assert f"| {stare}: citations | 1 | 1 |  |" in primary
    assert "| agreement with eyecite | 100.0% |  |  |" in primary
    assert f"(`{sample}`, 1 opinions)" in secondary
    assert f"| {sample}: citations | 2 | 1 | 1 |" in secondary
    assert "| agreement with eyecite | 50.0% |  | 0.0% |" in secondary
    assert f"eyecite on `{stare}`: the stored run (key `aaaaaaaaaaaa`)" in md
    assert f"eyecite on `{sample}`: the stored run (key `bbbbbbbbbbbb`)" in md
    assert f"`v0.1.0` has no saved run on `{stare}`" in md
    assert "never shown" not in md
    assert f"on <code>{sample}</code>" in md
    summary = json.loads((out / "summary.json").read_text())
    assert summary["corpus"] == stare and "previous" not in summary
    comparison = summary["comparison"]
    assert comparison["name"] == "eyecite's comparison sample"
    assert comparison["corpus"] == sample and comparison["eyecite"]["gained"] == 1
    assert comparison["previous"]["label"] == "v0.1.0"
    headline = (out / "headline.md").read_text()
    assert f"- {stare} (1 opinions): 100.0% agreement" in headline
    assert (
        f"- Secondary, eyecite's comparison sample ({sample}, 1 opinions)" in headline
    )
    assert f"- Against v0.1.0 on {sample}:" in headline
    assert {p.name for p in out.glob("*.csv")} == {
        "vs-eyecite.csv",
        "vs-eyecite-sample.csv",
        "vs-previous-sample.csv",
    }
