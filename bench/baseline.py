"""Cached eyecite runs, committed under baselines/eyecite/ and reused while their key holds.

Usage:
  uv run bench/baseline.py key [TIER ...]            print each tier's current key
  uv run bench/baseline.py check [TIER ...]          exit 1 if a committed run is stale or missing
  uv run bench/baseline.py stale                     print the tiers whose run is stale or missing
  uv run bench/baseline.py save TIER RUN.json        store a saved eyecite run as TIER's baseline
  uv run bench/baseline.py restore TIER OUT.json     rebuild the saved run; exit 3 on a key miss
  uv run bench/baseline.py restore --or-run TIER OUT.json   run eyecite live on a key miss
  uv run bench/baseline.py run TIER OUT.json         run eyecite over TIER's inputs now
  uv run bench/baseline.py version                   the eyecite version the adapter pins

eyecite's answers to a fixed set of inputs only change when eyecite or the harness does,
so an engine's CI can diff against a stored eyecite run instead of running eyecite each
time. Each tier's key is a sha256 over the eyecite version the adapter pins and the
bytes of every file that decides the run:

- every tier: adapters/eyecite/*.py and bench/run.py
- vectors: the vector set's *.jsonl (vectors/eyecite-<version>/)
- stare-pub: the stare.pub sample's manifest (corpora/stare-pub-<version>.json, the
  version tools/fetch_stare.py pins, which pins every case by sha256) and
  tools/fetch_stare.py, which turns it into requests
- corpus-1pct, corpus-10pct: eyecite's comparison sample's manifest
  (corpora/courtlistener-*.json, which pins the download by sha256) and
  tools/fetch_corpus.py, which turns it into requests

The key also covers RUNNER, the CI runner class the runs are timed on, since engines'
CI reports its own ms/KB beside eyecite's; changing it makes every tier stale.

baselines/eyecite/MANIFEST.json records, per tier, the key, the files and hashes it was
made from, and the run's headline numbers, so a refresh shows up in review as a diff of
that file. The runs themselves are <tier>.json.gz: the run's metadata and each input's
response and timing, without the input text, which restore joins back in from the
vectors or the fetched corpus.
"""

import argparse
import datetime
import gzip
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import fetch_stare
from run import SAVE_FORMAT, compare, load_vectors

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "baselines" / "eyecite"
MANIFEST = STORE / "MANIFEST.json"
BASELINE_FORMAT = "citation-bench-baseline/1"
ADAPTER = ROOT / "adapters" / "eyecite"
COMMON = ("adapters/eyecite/*.py", "bench/run.py")
CORPUS_SIZES = ("1", "10")
STARE = "stare-pub"  # the stare.pub sample, at the version tools/fetch_stare.py pins
TIERS = ("vectors", STARE, *(f"corpus-{s}pct" for s in CORPUS_SIZES))
MISS = 3  # restore's exit code when the stored run doesn't match the current key
EYECITE = "uv run -q --script adapters/eyecite/adapter.py"
TIMEOUT = "900"  # seconds on one input before the adapter is restarted
RUNNER = "homelab"  # the runs-on of .github/workflows/eyecite-baseline.yml


def eyecite_version():
    """The eyecite release adapters/eyecite/adapter.py pins."""
    m = re.search(r'"eyecite==([^"]+)"', (ADAPTER / "adapter.py").read_text())
    if not m:
        raise SystemExit("adapters/eyecite/adapter.py pins no eyecite version")
    return m.group(1)


def vectors_dir():
    return ROOT / "vectors" / f"eyecite-{eyecite_version()}"


def corpus_size(tier):
    return tier.removeprefix("corpus-").removesuffix("pct")


def stare_name():
    """The pinned stare.pub sample's name, e.g. stare-pub-v2026.10.22."""
    return fetch_stare.corpus_name(fetch_stare.VERSION)


def tier_patterns(tier):
    if tier == "vectors":
        own = (f"{vectors_dir().relative_to(ROOT)}/*.jsonl",)
    elif tier == STARE:
        own = (f"corpora/{stare_name()}.json", "tools/fetch_stare.py")
    elif tier in TIERS:
        own = (
            f"corpora/courtlistener-{corpus_size(tier)}pct.json",
            "tools/fetch_corpus.py",
        )
    else:
        raise SystemExit(f"unknown tier {tier!r}; one of {', '.join(TIERS)}")
    return COMMON + own


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def key_inputs(tier):
    """What the key hashes: the eyecite version and each file's sha256."""
    files = {}
    for pattern in tier_patterns(tier):
        matched = sorted(ROOT.glob(pattern))
        if not matched:
            raise SystemExit(f"{tier}: nothing matches {pattern}")
        for path in matched:
            files[str(path.relative_to(ROOT))] = sha256_bytes(path.read_bytes())
    return {
        "engine": "eyecite",
        "version": eyecite_version(),
        "tier": tier,
        "runner": RUNNER,
        "files": dict(sorted(files.items())),
    }


def compute_key(inputs):
    return sha256_bytes(json.dumps(inputs, sort_keys=True).encode())


def load_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}


def stale_reason(tier, manifest=None):
    """None if the stored run matches the current key, else why it doesn't."""
    entry = (load_manifest() if manifest is None else manifest).get(tier)
    if not entry:
        return "no stored run"
    if entry["version"] != eyecite_version():
        return f"eyecite {entry['version']} stored, adapter pins {eyecite_version()}"
    if entry.get("runner") != RUNNER:
        stored = entry.get("runner") or "a GitHub-hosted runner"
        return f"timed on {stored}, CI runs on {RUNNER}"
    inputs = key_inputs(tier)
    if entry["key"] == compute_key(inputs):
        return None
    old, new = entry["files"], inputs["files"]
    changed = sorted(p for p in old.keys() | new.keys() if old.get(p) != new.get(p))
    return "changed: " + ", ".join(changed)


def tier_path(tier):
    """Where a tier's requests are, fetching the corpus first if it isn't cached."""
    if tier == "vectors":
        return vectors_dir()
    if tier == STARE:
        path = ROOT / ".cache" / "corpora" / stare_name()
        if not (path / "find.jsonl").exists():
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "fetch_stare.py")], check=True
            )
        return path
    size = corpus_size(tier)
    path = ROOT / ".cache" / "corpora" / f"courtlistener-{size}pct"
    if not (path / "find.jsonl").exists():
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "fetch_corpus.py"), "--size", size],
            check=True,
        )
    return path


def tier_vectors(tier):
    return load_vectors(tier_path(tier))


def run_eyecite(tier, out):
    """Run eyecite over a tier's inputs, the way every stored run was made."""
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "bench" / "run.py"),
            "--adapter",
            EYECITE,
            "--vectors",
            str(tier_path(tier).relative_to(ROOT)),
            "--timeout",
            TIMEOUT,
            "--label",
            f"eyecite-{eyecite_version()}",
            "--save",
            str(Path(out).resolve()),
        ],
        cwd=ROOT,
        check=True,
    )
    return 0


def gzip_bytes(data):
    return gzip.compress(data, compresslevel=9, mtime=0)


def save(tier, run_path):
    run = json.loads(Path(run_path).read_text(encoding="utf-8"))
    meta = run["meta"]
    if "adapters/eyecite" not in meta.get("adapter", ""):
        raise SystemExit(f"{run_path}: adapter {meta.get('adapter')!r} isn't eyecite's")
    want = [v["id"] for v in tier_vectors(tier)]
    got = [i["id"] for i in run["inputs"]]
    if got != want:
        raise SystemExit(
            f"{run_path}: its inputs aren't the {tier} tier's ({len(got)} vs {len(want)})"
        )
    inputs = key_inputs(tier)
    key = compute_key(inputs)
    stored = {
        "format": BASELINE_FORMAT,
        "key": key,
        "meta": meta,
        "responses": [[i["id"], i["response"], i["seconds"]] for i in run["inputs"]],
    }
    data = gzip_bytes(
        (json.dumps(stored, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    )
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / f"{tier}.json.gz").write_bytes(data)
    citations = sum(
        len((i["response"] or {}).get("citations") or []) for i in run["inputs"]
    )
    manifest = load_manifest()
    manifest[tier] = {
        "key": key,
        **{k: inputs[k] for k in ("version", "runner", "files")},
        "run": f"{tier}.json.gz",
        "sha256": sha256_bytes(data),
        "bench_commit": meta.get("bench_commit"),
        "started": meta.get("started"),
        "host": meta.get("host"),
        "inputs": meta.get("inputs"),
        "passed": meta.get("passed"),
        "scored": meta.get("scored"),
        "errors": meta.get("errors"),
        "citations": citations,
        "ms_per_input": meta.get("ms_per_input"),
        "ms_per_kb": meta.get("ms_per_kb"),
        "cold_start_s": meta.get("cold_start_s"),
    }
    MANIFEST.write_text(
        json.dumps(dict(sorted(manifest.items())), indent=2, ensure_ascii=False) + "\n"
    )
    print(f"stored {tier} under key {key[:12]} ({len(data) / 1e6:.1f} MB)")
    return 0


def restore(tier, out):
    """Write the stored run back out in bench/run.py --save format. MISS if stale."""
    manifest = load_manifest()
    reason = stale_reason(tier, manifest)
    if reason:
        print(f"{tier}: no usable eyecite run ({reason})", file=sys.stderr)
        return MISS
    entry = manifest[tier]
    data = (STORE / entry["run"]).read_bytes()
    if sha256_bytes(data) != entry["sha256"]:
        raise SystemExit(f"{entry['run']}: sha256 doesn't match MANIFEST.json")
    stored = json.loads(gzip.decompress(data))
    if stored["key"] != entry["key"]:
        raise SystemExit(f"{entry['run']}: key doesn't match MANIFEST.json")
    vectors = tier_vectors(tier)
    responses = {i: (r, s) for i, r, s in stored["responses"]}
    if [v["id"] for v in vectors] != [i for i, _, _ in stored["responses"]]:
        raise SystemExit(f"{tier}: the stored run's inputs don't match the tier's")
    meta = {
        **stored["meta"],
        "cached": {
            "key": entry["key"],
            "restored": datetime.datetime.now(datetime.UTC).isoformat(
                timespec="seconds"
            ),
        },
    }
    inputs = []
    for v in vectors:
        response, seconds = responses[v["id"]]
        inputs.append(
            {
                "id": v["id"],
                "kind": v.get("kind", "find"),
                "input": v["input"],
                "options": v.get("options", {}),
                "response": response,
                "seconds": seconds,
                "mismatches": compare(v, response) if "expected" in v else None,
            }
        )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"format": SAVE_FORMAT, "meta": meta, "inputs": inputs},
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"restored {tier} ({meta['label']}, key {entry['key'][:12]}) to {out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("key", "check"):
        p = sub.add_parser(name)
        p.add_argument("tiers", nargs="*", default=list(TIERS))
    sub.add_parser("stale")
    p = sub.add_parser("save")
    p.add_argument("tier", choices=TIERS)
    p.add_argument("run", type=Path)
    p = sub.add_parser("restore")
    p.add_argument("--or-run", action="store_true", help="run eyecite on a key miss")
    p.add_argument("tier", choices=TIERS)
    p.add_argument("out", type=Path)
    p = sub.add_parser("run")
    p.add_argument("tier", choices=TIERS)
    p.add_argument("out", type=Path)
    sub.add_parser("version")
    args = ap.parse_args(argv)

    if args.command == "version":
        print(eyecite_version())
        return 0
    if args.command == "run":
        return run_eyecite(args.tier, args.out)
    if args.command == "key":
        for tier in args.tiers:
            print(f"{tier} {compute_key(key_inputs(tier))}")
        return 0
    if args.command == "stale":
        manifest = load_manifest()
        for tier in TIERS:
            if stale_reason(tier, manifest):
                print(tier)
        return 0
    if args.command == "check":
        manifest = load_manifest()
        bad = 0
        for tier in args.tiers:
            reason = stale_reason(tier, manifest)
            print(f"{tier}: {'stale, ' + reason if reason else 'current'}")
            bad += bool(reason)
        if bad:
            print(
                "Refresh with `mise run baseline:eyecite`, or commit the eyecite-baseline "
                "artifact that CI's baseline job built.",
                file=sys.stderr,
            )
        return 1 if bad else 0
    if args.command == "save":
        return save(args.tier, args.run)
    status = restore(args.tier, args.out)
    if status == MISS and args.or_run:
        print(f"{args.tier}: running eyecite now", file=sys.stderr)
        return run_eyecite(args.tier, args.out)
    return status


if __name__ == "__main__":
    sys.exit(main())
