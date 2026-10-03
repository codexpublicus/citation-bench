"""Feed conformance vectors to an adapter and score its answers.

Usage:
  uv run bench/run.py --adapter CMD --vectors DIR [--show N] [--json OUT]
                      [--save results/LABEL.json [--label LABEL]] [--timeout S]
                      [--known-failures FILE [--update-known-failures]]

With --known-failures, the run fails only on vectors that aren't listed in FILE, and it
reports listed vectors that now pass, so an engine's CI can ratchet toward full parity.

Vectors carry a request kind (find, resolve or annotate; see docs/protocol.md), and the
report breaks scores down by kind. Inputs without an `expected` answer are sent and
saved but not scored, so the same runner serves corpora that have no answers yet.

With --save, the run also writes every response with its timing and the run's metadata,
which bench/diff.py compares across engines or versions.

Timing: the adapter first answers a probe request, so its startup is reported once as
the cold start, and each input is timed from the reply before it (ms per input and per
KB of input text). If the adapter dies, or sits on one input longer than --timeout, the
bench records that input as crashed and carries on with a fresh adapter.
"""

import argparse
import collections
import dataclasses
import datetime
import json
import platform
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

PROTOCOL = 2
SAVE_FORMAT = "citation-bench-results/1"
ROOT = Path(__file__).resolve().parent.parent
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


PROBE = {
    "protocol": PROTOCOL,
    "kind": "find",
    "id": "citation-bench/probe",
    "input": {"text": "1 U.S. 1", "format": "plain", "clean_steps": []},
    "options": {},
}


@dataclasses.dataclass
class AdapterRun:
    responses: dict  # id -> response
    seconds: dict  # id -> seconds the adapter spent on it, or None
    cold_start: float | None  # process start to the probe's reply, first process only
    exit_codes: list  # one per adapter process
    crashed: list  # ids the adapter died or was killed on
    timed_out: list  # the subset of crashed that hit --timeout
    engine: dict | None = None  # what the adapter says it runs, from its probe reply

    @property
    def elapsed(self):
        return sum(s for s in self.seconds.values() if s is not None)


def request(v):
    return {
        "protocol": PROTOCOL,
        "kind": v.get("kind", "find"),
        "id": v["id"],
        "input": v["input"],
        "options": v.get("options", {}),
    }


def run_once(cmd, vectors, timeout=None):
    """Start the adapter, send a probe and then every vector, collect the replies.

    Returns (responses, seconds, cold_start, exit code, timed out, engine). The probe's reply
    marks the end of startup, so cold_start is process start plus one trivial request,
    and every vector gets a measured time: requests are pipelined and answered in
    order, so the gap between two replies is the time the adapter spent on the second.
    """
    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd if isinstance(cmd, list) else shlex.split(cmd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )

    def feed():
        try:
            for req in [PROBE, *map(request, vectors)]:
                proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            proc.stdin.close()
        except (OSError, ValueError):
            pass  # the adapter exited; the reader sees it and reports what's missing

    last = [t0]
    killed = threading.Event()
    done = threading.Event()

    def watchdog():
        while not done.wait(1):
            if time.perf_counter() - last[0] > timeout:
                killed.set()
                proc.kill()
                return

    threading.Thread(target=feed, daemon=True).start()
    if timeout:
        threading.Thread(target=watchdog, daemon=True).start()
    responses, seconds, cold_start, engine = {}, {}, None, None
    for line in proc.stdout:
        now = time.perf_counter()
        try:
            res = json.loads(line)
        except json.JSONDecodeError:
            print(
                f"adapter wrote a line that isn't JSON: {line[:200]!r}", file=sys.stderr
            )
            continue
        if cold_start is None and res.get("id") == PROBE["id"]:
            cold_start = now - t0
            engine = res.get("engine")
        else:
            responses[res.get("id")] = res
            seconds[res.get("id")] = now - last[0]
        last[0] = now
    done.set()
    proc.wait()
    return responses, seconds, cold_start, proc.returncode, killed.is_set(), engine


def run_adapter(cmd, vectors, timeout=None, max_restarts=10):
    """Run every vector, starting a fresh adapter when one dies mid-run.

    The adapter answers in order, so the first unanswered vector is the one it was on
    when it crashed or was killed. That vector is recorded and skipped, and the rest go
    to a new process, up to max_restarts times.
    """
    run = AdapterRun({}, {}, None, [], [], [])
    pending = list(vectors)
    while pending:
        responses, seconds, cold, rc, killed, engine = run_once(cmd, pending, timeout)
        if not run.exit_codes:
            run.cold_start = cold
            run.engine = engine
        run.exit_codes.append(rc)
        run.responses.update(responses)
        run.seconds.update(seconds)
        missing = next(
            (i for i, v in enumerate(pending) if v["id"] not in responses), None
        )
        if missing is None:
            break
        run.crashed.append(pending[missing]["id"])
        if killed:
            run.timed_out.append(pending[missing]["id"])
        if len(run.exit_codes) > max_restarts:
            break
        pending = pending[missing + 1 :]
    return run


def input_kb(v):
    return len(v["input"].get("text", "").encode("utf-8")) / 1024


def timing(vectors, run):
    """Throughput over the answered inputs, and the slowest one."""
    timed = [
        (run.seconds[v["id"]], v)
        for v in vectors
        if run.seconds.get(v["id"]) is not None
    ]
    kb = sum(input_kb(v) for _, v in timed)
    elapsed = sum(s for s, _ in timed)
    ms = sorted(1000 * s for s, _ in timed)
    slowest = max(timed, key=lambda t: t[0], default=(None, None))[1]
    return {
        "elapsed_s": round(elapsed, 6),
        "cold_start_s": None if run.cold_start is None else round(run.cold_start, 4),
        "timed_inputs": len(timed),
        "input_kb": round(kb, 1),
        "ms_per_input": round(1000 * elapsed / max(len(timed), 1), 4),
        "ms_per_kb": round(1000 * elapsed / kb, 4) if kb else None,
        "ms_p50": round(ms[len(ms) // 2], 4) if ms else None,
        "ms_max": round(ms[-1], 4) if ms else None,
        "slowest": slowest["id"] if slowest else None,
    }


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


def git_commit(path):
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def vector_sources(path):
    """SOURCE.json of the vector set(s), when there is one."""
    directory = path if path.is_dir() else path.parent
    source = directory / "SOURCE.json"
    return json.loads(source.read_text()) if source.exists() else None


def errors(run):
    return sum("error" in r for r in run.responses.values())


def save_results(path, label, args, vectors, run, results):
    """Write one run as JSON: metadata, then each input with its response and timing."""
    meta = {
        "label": label,
        "adapter": args.adapter,
        "engine": run.engine,
        "vectors": str(args.vectors),
        "source": vector_sources(args.vectors),
        "protocol": PROTOCOL,
        "started": args.started,
        **timing(vectors, run),
        "adapter_exit": run.exit_codes[-1],
        "adapter_starts": len(run.exit_codes),
        "inputs": len(vectors),
        "errors": errors(run),
        "crashed": run.crashed,
        "timed_out": run.timed_out,
        "scored": len(results),
        "passed": sum(not bad for bad in results.values()),
        "bench_commit": git_commit(ROOT),
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
    }
    inputs = [
        {
            "id": v["id"],
            "kind": v.get("kind", "find"),
            "input": v["input"],
            "options": v.get("options", {}),
            "response": run.responses.get(v["id"]),
            "seconds": run.seconds.get(v["id"]),
            "mismatches": results.get(v["id"]),
        }
        for v in vectors
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"format": SAVE_FORMAT, "meta": meta, "inputs": inputs},
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True, help="adapter command line")
    ap.add_argument(
        "--vectors", required=True, type=Path, help="vector directory or .jsonl file"
    )
    ap.add_argument("--show", type=int, default=0, help="print N failing examples")
    ap.add_argument("--json", type=Path, help="write per-vector results here")
    ap.add_argument(
        "--save",
        type=Path,
        help="write responses, timing and run metadata here, for bench/diff.py",
    )
    ap.add_argument("--label", help="name for this run in --save (default: file stem)")
    ap.add_argument(
        "--timeout",
        type=float,
        help="kill the adapter after this many seconds without a reply, record the "
        "input it was on, and carry on with a fresh one",
    )
    ap.add_argument("--known-failures", type=Path)
    ap.add_argument("--update-known-failures", action="store_true")
    args = ap.parse_args()

    args.started = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    vectors = load_vectors(args.vectors)
    run = run_adapter(args.adapter, vectors, timeout=args.timeout)
    responses = run.responses
    scored = [v for v in vectors if "expected" in v]
    results = {v["id"]: compare(v, responses.get(v["id"])) for v in scored}
    failing = {i for i, bad in results.items() if bad}

    if args.save:
        label = args.label or args.save.stem
        save_results(args.save, label, args, vectors, run, results)

    passed = len(scored) - len(failing)
    unscored = len(vectors) - len(scored)
    if run.engine:
        e = run.engine
        print(
            "engine: "
            + " ".join(str(e[k]) for k in ("name", "version") if e.get(k))
            + (f" at {e['commit']}" if e.get("commit") else "")
        )
    t = timing(vectors, run)
    print(
        (
            f"{passed}/{len(scored)} vectors pass ({pct(passed, len(scored))})"
            + (f" · {unscored} inputs without answers" if unscored else "")
            if scored
            else f"{len(vectors)} inputs, none with answers to score"
        )
        + f" · {t['ms_per_input']:.2f} ms/vector"
        + (f", {t['ms_per_kb']:.2f} ms/KB" if t["ms_per_kb"] else "")
        + (f" · cold start {t['cold_start_s']:.2f} s" if t["cold_start_s"] else "")
        + f" · adapter exit {run.exit_codes[-1]}"
    )
    if errors(run):
        print(f"{errors(run)} inputs answered with an error")
    for i in run.crashed:
        how = "timed out" if i in run.timed_out else "crashed"
        print(f"adapter {how} on {i}; restarted for the rest", file=sys.stderr)
    if args.save:
        print(f"saved {len(vectors)} responses to {args.save}")
    by_kind = collections.defaultdict(lambda: [0, 0])
    by_test = collections.defaultdict(lambda: [0, 0])
    for v in scored:
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
    for v in scored:
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
