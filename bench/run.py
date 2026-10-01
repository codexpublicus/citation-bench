"""Feed conformance vectors to an adapter and score its answers.

Usage:
  uv run bench/run.py --adapter CMD --vectors DIR [--show N] [--json OUT]
                      [--known-failures FILE [--update-known-failures]]

With --known-failures, the run fails only on vectors that aren't listed in FILE, and it
reports listed vectors that now pass, so an engine's CI can ratchet toward full parity.
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
            req = {"id": v["id"], "input": v["input"], "options": v.get("options", {})}
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


def compare(vector, response):
    """Return a list of mismatch labels; empty means the vector passes."""
    if response is None:
        return ["no-response"]
    if "error" in response:
        return ["error"]
    exp, got = vector["expected"]["citations"], response.get("citations", [])
    if [c["type"] for c in exp] != [c["type"] for c in got]:
        return ["citations"]
    bad = []
    for e, g in zip(exp, got):
        if e.get("groups", {}) != g.get("groups", {}):
            bad.append("groups")
        for field in ("reporter_normalized", "year"):
            if field in e and e[field] != g.get(field):
                bad.append(field)
        if (
            "span" in e
            and vector["input"].get("format") == "plain"
            and e["span"] != g.get("span")
        ):
            bad.append("span")
        em, gm = e.get("metadata", {}), g.get("metadata", {})
        bad += [
            f"metadata.{k}"
            for k in sorted(SCORED_METADATA & (em.keys() | gm.keys()))
            if em.get(k) != gm.get(k)
        ]
    return sorted(set(bad))


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
        f"{passed}/{len(vectors)} vectors pass ({100 * passed / max(len(vectors), 1):.1f}%)"
        f" · {1000 * elapsed / max(len(vectors), 1):.2f} ms/vector · adapter exit {rc}"
    )
    by_test = collections.defaultdict(lambda: [0, 0])
    for v in vectors:
        key = f"{v['source']['file']}::{v['source']['test']}"
        by_test[key][0] += v["id"] not in failing
        by_test[key][1] += 1
    for key, (ok, n) in sorted(by_test.items()):
        print(f"  {ok:4}/{n:<4} {key}")
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
            print(
                f"  expected: {json.dumps(v['expected']['citations'], ensure_ascii=False)[:800]}"
            )
            got = responses.get(v["id"], {})
            print(
                f"  got:      {json.dumps(got.get('citations', got), ensure_ascii=False)[:800]}"
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
