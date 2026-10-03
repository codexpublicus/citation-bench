"""baseline.py tests on a tiny stand-in for the repository."""

import json

import baseline
import pytest

VECTORS = [
    {
        "id": "v/1",
        "kind": "find",
        "input": {"text": "1 U.S. 1", "format": "plain", "clean_steps": []},
        "expected": {"citations": []},
    },
    {
        "id": "v/2",
        "kind": "find",
        "input": {"text": "no citation", "format": "plain", "clean_steps": []},
        "expected": {"citations": []},
    },
]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    files = {
        "adapters/eyecite/adapter.py": '# "eyecite==9.9.9",\n',
        "adapters/eyecite/serialize.py": "",
        "bench/run.py": "",
        "tools/fetch_corpus.py": "",
        "corpora/courtlistener-1pct.json": "{}",
        "corpora/courtlistener-10pct.json": "{}",
        "vectors/eyecite-9.9.9/find.jsonl": "".join(
            json.dumps(v) + "\n" for v in VECTORS
        ),
    }
    for path, text in files.items():
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(text)
    store = tmp_path / "baselines" / "eyecite"
    monkeypatch.setattr(baseline, "ROOT", tmp_path)
    monkeypatch.setattr(baseline, "ADAPTER", tmp_path / "adapters" / "eyecite")
    monkeypatch.setattr(baseline, "STORE", store)
    monkeypatch.setattr(baseline, "MANIFEST", store / "MANIFEST.json")
    return tmp_path


def saved_run(path, answers):
    run = {
        "format": "citation-bench-results/1",
        "meta": {"label": "eyecite-9.9.9", "adapter": "uv run adapters/eyecite/x.py"},
        "inputs": [
            {"id": v["id"], "kind": "find", "input": v["input"], "response": a}
            | {"seconds": 0.01, "options": {}, "mismatches": []}
            for v, a in zip(VECTORS, answers)
        ],
    }
    path.write_text(json.dumps(run))
    return run


def test_key_follows_the_version_and_the_files(repo):
    key = baseline.compute_key(baseline.key_inputs("vectors"))
    assert key == baseline.compute_key(baseline.key_inputs("vectors"))
    (repo / "bench/run.py").write_text("# changed\n")
    assert key != baseline.compute_key(baseline.key_inputs("vectors"))


def test_corpus_key_ignores_the_vectors(repo):
    key = baseline.compute_key(baseline.key_inputs("corpus-1pct"))
    (repo / "vectors/eyecite-9.9.9/find.jsonl").write_text("")
    assert key == baseline.compute_key(baseline.key_inputs("corpus-1pct"))
    (repo / "corpora/courtlistener-1pct.json").write_text('{"sha256": "x"}')
    assert key != baseline.compute_key(baseline.key_inputs("corpus-1pct"))


def test_save_then_restore_round_trips(repo, tmp_path):
    run = saved_run(tmp_path / "run.json", [{"citations": []}, {"error": "boom"}])
    baseline.save("vectors", tmp_path / "run.json")
    assert baseline.stale_reason("vectors") is None
    entry = json.loads(baseline.MANIFEST.read_text())["vectors"]
    assert entry["version"] == "9.9.9" and entry["errors"] is None
    assert baseline.restore("vectors", tmp_path / "out.json") == 0
    out = json.loads((tmp_path / "out.json").read_text())
    assert out["meta"]["cached"]["key"] == entry["key"]
    assert [i["response"] for i in out["inputs"]] == [
        i["response"] for i in run["inputs"]
    ]
    assert [i["mismatches"] for i in out["inputs"]] == [[], ["error"]]


def test_stale_run_is_a_miss_with_a_reason(repo, tmp_path):
    saved_run(tmp_path / "run.json", [{"citations": []}, {"citations": []}])
    baseline.save("vectors", tmp_path / "run.json")
    (repo / "adapters/eyecite/serialize.py").write_text("# changed\n")
    assert baseline.stale_reason("vectors") == (
        "changed: adapters/eyecite/serialize.py"
    )
    assert baseline.restore("vectors", tmp_path / "out.json") == baseline.MISS
    assert not (tmp_path / "out.json").exists()
    (repo / "adapters/eyecite/adapter.py").write_text('"eyecite==9.9.10"\n')
    assert "9.9.10" in baseline.stale_reason("vectors")


def test_check_and_stale(repo, tmp_path, capsys):
    assert baseline.main(["check", "vectors"]) == 1
    saved_run(tmp_path / "run.json", [{"citations": []}, {"citations": []}])
    baseline.save("vectors", tmp_path / "run.json")
    assert baseline.main(["check", "vectors"]) == 0
    capsys.readouterr()
    baseline.main(["stale"])
    assert capsys.readouterr().out.split() == ["corpus-1pct", "corpus-10pct"]


def test_save_refuses_another_engine_or_other_inputs(repo, tmp_path):
    run = saved_run(tmp_path / "run.json", [{"citations": []}, {"citations": []}])
    run["meta"]["adapter"] = "target/release/citare-bench-adapter"
    (tmp_path / "run.json").write_text(json.dumps(run))
    with pytest.raises(SystemExit, match="isn't eyecite's"):
        baseline.save("vectors", tmp_path / "run.json")
    run["meta"]["adapter"] = "adapters/eyecite/adapter.py"
    run["inputs"] = run["inputs"][:1]
    (tmp_path / "run.json").write_text(json.dumps(run))
    with pytest.raises(SystemExit, match="inputs aren't"):
        baseline.save("vectors", tmp_path / "run.json")


def test_stored_file_is_reproducible(repo, tmp_path):
    saved_run(tmp_path / "run.json", [{"citations": []}, {"citations": []}])
    baseline.save("vectors", tmp_path / "run.json")
    first = (baseline.STORE / "vectors.json.gz").read_bytes()
    baseline.save("vectors", tmp_path / "run.json")
    assert (baseline.STORE / "vectors.json.gz").read_bytes() == first
