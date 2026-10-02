"""Feed conformance vectors to an adapter and score its answers.

Usage:
  uv run bench/run.py --adapter CMD --vectors DIR [--show N] [--json OUT]
                      [--known-failures FILE [--update-known-failures]]

With --known-failures, the run fails only on vectors that aren't listed in FILE, and it
reports listed vectors that now pass, so an engine's CI can ratchet toward full parity.

Vectors carry a request kind (find, resolve or annotate; see docs/protocol.md), and the
report breaks scores down by kind.
"""

import argparse
import collections
import json
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

PROTOCOL = 2
KINDS = ("find", "resolve", "annotate")

SCORED_METADATA = {
    "pin_cite",
    "court",
    "plaintiff",
    "defendant",
    "antecedent_guess",
    "parenthetical",
    "extra",
    "year",
    "month",
    "day",
    "publisher",
    "volume",
}


def load_vectors(path):
    files = sorted(path.glob("*.jsonl")) if path.is_dir() else [path]
    return [
        json.loads(line)
        for f in files
        for line in f.open(encoding="utf-8")
        if line.strip()
    ]


def run_adapter(cmd, vectors):
    proc = subprocess.Popen(
        cmd if isinstance(cmd, list) else shlex.split(cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    def feed():
        for v in vectors:
            req = {
                "protocol": PROTOCOL,
                "kind": v.get("kind", "find"),
                "id": v["id"],
                "input": v["input"],
                "options": v.get("options", {}),
            }
            proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
        proc.stdin.close()

    threading.Thread(target=feed, daemon=True).start()
    responses, first = {}, None
    for line in proc.stdout:
        now = time.perf_counter()
        if first is None:
            first = now  # timing starts at the first reply, so the adapter's startup isn't counted
        res = json.loads(line)
        responses[res["id"]] = res
    end = time.perf_counter()
    proc.wait()
    return responses, (end - first) if first else 0.0, proc.returncode


def canonical_resolution(groups):
    """Renumber resource groups by first appearance, so only the partition counts."""
    seen = {}
    return [None if g is None else seen.setdefault(g, len(seen)) for g in groups or []]


def compare_citations(vector, exp, got):
    if [c["type"] for c in exp] != [c["type"] for c in got]:
        return ["citations"]
    plain = vector["input"].get("format") == "plain"
    bad = []
    for e, g in zip(exp, got):
        if e.get("groups", {}) != g.get("groups", {}):
            bad.append("groups")
        for field in ("reporter_normalized", "year"):
            if field in e and e[field] != g.get(field):
                bad.append(field)
        for field in ("span", "full_span"):
            if field in e and plain and e[field] != g.get(field):
                bad.append(field)
        em, gm = e.get("metadata", {}), g.get("metadata", {})
        bad += [
            f"metadata.{k}"
            for k in sorted(SCORED_METADATA & (em.keys() | gm.keys()))
            if em.get(k) != gm.get(k)
        ]
    return bad


def compare(vector, response):
    """Return a list of mismatch labels; empty means the vector passes."""
    if response is None:
        return ["no-response"]
    if "error" in response:
        return ["error"]
    kind, exp = vector.get("kind", "find"), vector["expected"]
    if kind == "find":
        bad = compare_citations(vector, exp["citations"], response.get("citations", []))
    elif kind == "resolve":
        # Resolution is scored on its own: which citations share a resource. The
        # citations only have to line up by type, or the indices would mean nothing.
        exp_types = [c["type"] for c in exp["citations"]]
        if exp_types != [c["type"] for c in response.get("citations", [])]:
            return ["citations"]
        got = response.get("resolution")
        bad = (
            []
            if got is not None
            and canonical_resolution(got) == canonical_resolution(exp["resolution"])
            else ["resolution"]
        )
    elif kind == "annotate":
        bad = [] if response.get("text") == exp["text"] else ["text"]
    else:
        bad = [f"unknown-kind:{kind}"]
    return sorted(set(bad))


def pct(ok, n):
    return f"{100 * ok / max(n, 1):.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True, help="adapter command line")
    ap.add_argument(
        "--vectors", required=True, type=Path, help="vector directory or .jsonl file"
    )
    ap.add_argument("--show", type=int, default=0, help="print N failing examples")
    ap.add_argument("--json", type=Path, help="write per-vector results here")
    ap.add_argument("--known-failures", type=Path)
    ap.add_argument("--update-known-failures", action="store_true")
    args = ap.parse_args()

    vectors = load_vectors(args.vectors)
    responses, elapsed, rc = run_adapter(args.adapter, vectors)
    results = {v["id"]: compare(v, responses.get(v["id"])) for v in vectors}
    failing = {i for i, bad in results.items() if bad}

    passed = len(vectors) - len(failing)
    print(
        f"{passed}/{len(vectors)} vectors pass ({pct(passed, len(vectors))})"
        f" · {1000 * elapsed / max(len(vectors), 1):.2f} ms/vector · adapter exit {rc}"
    )
    by_kind = collections.defaultdict(lambda: [0, 0])
    by_test = collections.defaultdict(lambda: [0, 0])
    for v in vectors:
        kind = v.get("kind", "find")
        for tally, key in (
            (by_kind, kind),
            (by_test, f"{kind:8} {v['source']['file']}::{v['source']['test']}"),
        ):
            tally[key][0] += v["id"] not in failing
            tally[key][1] += 1
    order = {k: i for i, k in enumerate(KINDS)}
    for kind, (ok, n) in sorted(by_kind.items(), key=lambda kv: order.get(kv[0], 99)):
        print(f"  {kind:8} {ok:4}/{n:<4} ({pct(ok, n)})")
    for key, (ok, n) in sorted(
        by_test.items(), key=lambda kv: (order.get(kv[0].split()[0], 99), kv[0])
    ):
        print(f"    {ok:4}/{n:<4} {key}")
    reasons = collections.Counter(r for bad in results.values() for r in bad)
    if reasons:
        print("mismatches:", ", ".join(f"{k} {n}" for k, n in reasons.most_common()))

    shown = 0
    for v in vectors:
        if shown >= args.show:
            break
        if v["id"] in failing:
            shown += 1
            print(f"\n✗ {v['id']}  [{', '.join(results[v['id']])}]")
            print(f"  text:     {v['input']['text'][:300]!r}")
            got = responses.get(v["id"]) or {}
            if "error" in got:
                print(f"  error:    {got['error']}")
            for field in ("citations", "resolution", "text"):
                if field in v["expected"]:
                    exp = json.dumps(v["expected"][field], ensure_ascii=False)
                    print(f"  expected {field}: {exp[:800]}")
                    print(
                        f"  got {field}:      {json.dumps(got.get(field), ensure_ascii=False)[:800]}"
                    )

    if args.json:
        args.json.write_text(
            json.dumps({"results": results, "responses": responses}, indent=1)
        )

    if args.known_failures:
        if args.update_known_failures:
            args.known_failures.write_text("".join(f"{i}\n" for i in sorted(failing)))
            print(f"\nwrote {len(failing)} known failures to {args.known_failures}")
            return 0
        known = (
            set(args.known_failures.read_text().split())
            if args.known_failures.exists()
            else set()
        )
        new, fixed = sorted(failing - known), sorted(known - failing)
        for i in fixed:
            print(f"newly passing (remove from known failures): {i}")
        for i in new:
            print(f"REGRESSION: {i}  [{', '.join(results[i])}]")
        return 1 if new else 0
    return 0 if not failing else 1


if __name__ == "__main__":
    sys.exit(main())
