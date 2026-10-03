"""One engine's benchmark report: vector scores, corpus speed, and diffs against eyecite and
an earlier version of the same engine.

Usage:
  uv run bench/report.py --vectors V.json --vectors-base V0.json \\
      --corpus C.json --corpus-base C0.json --out DIR \\
      [--previous-vectors PV.json --previous-corpus PC.json | --previous-note TEXT] \\
      [--known-failures FILE] [--link URL]

Every input is a run saved by bench/run.py --save (or restored by bench/baseline.py).
The base runs are eyecite's; the previous runs are the engine's last release. DIR gets:

- bench-report.md: scores per request kind, corpus timing, the ratchet against
  --known-failures, and each diff in full (bench/diff.py's report, capped as usual)
- comment.md: the same report with shorter diff tables, sized for a PR comment
- headline.md: a few lines for release notes
- summary.json: the headline numbers
- vs-eyecite.csv, vs-previous.csv: every change in each diff

The report never decides pass or fail; a gate such as bench/run.py --known-failures
does that.
"""

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diff
from run import KINDS

COMMENT_LIMIT = 60000  # GitHub refuses comments over 65,536 characters
COMMENT_CAPS = ((20, 40, 10), (10, 15, 8))  # (inputs, change rows, reporters)


def load(path):
    return diff.load(path) if path else None


def label(run):
    return run["meta"]["label"]


def kind_scores(run):
    """{kind: (passed, scored)} over the inputs that have expected answers."""
    tally = collections.defaultdict(lambda: [0, 0])
    for i in run["inputs"]:
        if i.get("mismatches") is None:
            continue
        tally[i.get("kind", "find")][0] += not i["mismatches"]
        tally[i.get("kind", "find")][1] += 1
    return {k: tuple(v) for k, v in tally.items()}


def failing(run):
    return {i["id"] for i in run["inputs"] if i.get("mismatches")}


def ratchet(run, known_failures):
    known = set(Path(known_failures).read_text().split())
    fails = failing(run)
    return sorted(fails - known), sorted(known - fails)


def citations(run):
    return sum(
        len((i.get("response") or {}).get("citations") or []) for i in run["inputs"]
    )


def errors(run):
    return sum("error" in (i.get("response") or {}) for i in run["inputs"])


def score(ok, n):
    return f"{ok:,}/{n:,} ({100 * ok / n:.1f}%)" if n else ""


def num(v, fmt="{:,.2f}"):
    return "" if v is None else fmt.format(v)


def diff_summary(totals):
    return (
        f"+{totals['gained']:,} gained, −{totals['lost']:,} lost, "
        f"{totals['citations_changed']:,} with changed fields"
    )


def nested(md):
    """bench/diff.py's report, without its title and with headings demoted."""
    lines = md.splitlines()[1:]
    return "\n".join("##" + ln if ln.startswith("#") else ln for ln in lines).strip()


class Report:
    def __init__(self, args):
        self.vectors = load(args.vectors)
        self.vectors_base = load(args.vectors_base)
        self.corpus = load(args.corpus)
        self.corpus_base = load(args.corpus_base)
        self.prev_vectors = load(args.previous_vectors)
        self.prev_corpus = load(args.previous_corpus)
        self.previous_note = args.previous_note
        self.link = args.link
        self.ratchet = (
            ratchet(self.vectors, args.known_failures) if args.known_failures else None
        )
        self.diffs = {}  # name -> (base run, candidate run, rows, totals)
        self.diffs["eyecite"] = self.compare(self.corpus_base, self.corpus)
        if self.prev_corpus:
            self.diffs["previous"] = self.compare(self.prev_corpus, self.corpus)
            self.prev_agreement = self.compare(self.corpus_base, self.prev_corpus)[3]

    @staticmethod
    def compare(base, cand):
        rows, totals = diff.diff_runs(base, cand)
        return base, cand, rows, totals

    def columns(self):
        cols = [(label(self.corpus), self.vectors, self.corpus)]
        cols.append((label(self.corpus_base), self.vectors_base, self.corpus_base))
        if self.prev_corpus:
            cols.append((label(self.prev_corpus), self.prev_vectors, self.prev_corpus))
        return cols

    def agreement(self, corpus):
        if corpus is self.corpus:
            return self.diffs["eyecite"][3]["agreement"]
        if self.prev_corpus is not None and corpus is self.prev_corpus:
            return self.prev_agreement["agreement"]
        return None

    def table(self):
        cols = self.columns()
        lines = [
            "| | " + " | ".join(f"`{name}`" for name, _, _ in cols) + " |",
            "|---|" + "---:|" * len(cols),
        ]

        def row(name, cells):
            lines.append(f"| {name} | " + " | ".join(cells) + " |")

        scores = [kind_scores(v) if v else {} for _, v, _ in cols]
        for kind in KINDS:
            if any(kind in s for s in scores):
                row(f"vectors: {kind}", [score(*s.get(kind, (0, 0))) for s in scores])
        row(
            "vectors: all",
            [
                score(sum(p for p, _ in s.values()), sum(n for _, n in s.values()))
                for s in scores
            ],
        )
        row(
            "vectors: ms/vector",
            [num(v["meta"].get("ms_per_input")) if v else "" for _, v, _ in cols],
        )
        n = self.corpus["meta"]["inputs"]
        corpus_name = (self.corpus["meta"].get("source") or {}).get("name", "corpus")
        row(f"{corpus_name}: citations", [f"{citations(c):,}" for _, _, c in cols])
        row(
            "agreement with eyecite",
            [num(self.agreement(c), "{:.1%}") for _, _, c in cols],
        )
        row("opinions with errors", [f"{errors(c):,} of {n:,}" for _, _, c in cols])
        for key, name, fmt in (
            ("ms_per_kb", "ms/KB", "{:,.2f}"),
            ("ms_per_input", "ms/opinion, mean", "{:,.1f}"),
            ("ms_p50", "ms/opinion, median", "{:,.1f}"),
            ("ms_max", "slowest opinion (ms)", "{:,.0f}"),
            ("cold_start_s", "cold start (s)", "{:,.2f}"),
        ):
            row(name, [num(c["meta"].get(key), fmt) for _, _, c in cols])
        crashed = [len(c["meta"].get("crashed") or []) for _, _, c in cols]
        if any(crashed):
            row("adapter crashes or timeouts", [str(x) for x in crashed])
        return lines

    def provenance(self):
        meta = self.corpus["meta"]
        base = self.corpus_base["meta"]
        cached = base.get("cached")
        host = (base.get("host") or {}).get("platform", "an unrecorded host")
        lines = [
            (
                f"citation-bench `{(meta.get('bench_commit') or '')[:12]}` · "
                f"{meta['inputs']:,} opinions, {meta.get('input_kb', 0):,.0f} KB"
            )
        ]
        if cached:
            lines.append(
                f"eyecite: the stored run (key `{cached['key'][:12]}`), "
                f"measured {base.get('started')} on {host}"
            )
        else:
            lines.append("eyecite: run live, because no stored run matched its key")
        return " · ".join(lines)

    def ratchet_lines(self):
        if self.ratchet is None:
            return []
        new, fixed = self.ratchet
        out = [
            "**Ratchet:** "
            + (f"{len(new)} regressions" if new else "no regressions")
            + (
                f", {len(fixed)} newly passing (remove from `baselines/citare.known-failures`)"
                if fixed
                else ""
            )
        ]
        out += [f"- regression: `{i}`" for i in new[:30]]
        out += [f"- newly passing: `{i}`" for i in fixed[:30]]
        return out

    def section(self, name, caps):
        base, cand, rows, totals = self.diffs[name]
        max_rows, max_changes, max_reporters = caps
        body = diff.markdown(
            base, cand, rows, totals, max_rows, max_reporters, max_changes
        )
        title = f"<code>{label(cand)}</code> against <code>{label(base)}</code>"
        return [
            "<details>",
            f"<summary><b>{title}</b>: {diff_summary(totals)}</summary>",
            "",
            nested(body),
            "",
            "</details>",
        ]

    def markdown(self, caps=None):
        lines = [
            f"## citare benchmark: `{label(self.corpus)}`",
            "",
            self.provenance(),
            "",
            *self.table(),
            "",
            *self.ratchet_lines(),
        ]
        if not self.prev_corpus and self.previous_note:
            lines += ["", self.previous_note]
        lines += [
            "",
            (
                "Times are per input, from the gap between the adapter's replies. Runs "
                "on shared CI runners vary from one run to the next, so compare small "
                "differences in speed with care. This report never fails the build."
            ),
        ]
        if caps is not False:
            for name in self.diffs:
                lines += ["", *self.section(name, caps or (50, 200, 15))]
        if self.link:
            lines += ["", f"Full report, CSVs and saved runs: {self.link}"]
        return "\n".join(lines) + "\n"

    def comment(self):
        for caps in COMMENT_CAPS:
            text = self.markdown(caps)
            if len(text) <= COMMENT_LIMIT:
                return text
        return self.markdown(False)

    def summary(self):
        eyecite = self.diffs["eyecite"][3]
        scores = kind_scores(self.vectors)
        out = {
            "label": label(self.corpus),
            "bench_commit": self.corpus["meta"].get("bench_commit"),
            "corpus": (self.corpus["meta"].get("source") or {}).get("name"),
            "opinions": self.corpus["meta"]["inputs"],
            "vectors": {k: {"passed": p, "scored": n} for k, (p, n) in scores.items()},
            "eyecite": {
                "label": label(self.corpus_base),
                "agreement": eyecite["agreement"],
                "gained": eyecite["gained"],
                "lost": eyecite["lost"],
                "changed": eyecite["citations_changed"],
                "ms_per_kb": self.corpus_base["meta"].get("ms_per_kb"),
                "cached_key": (self.corpus_base["meta"].get("cached") or {}).get("key"),
            },
            "citations": citations(self.corpus),
            "errors": errors(self.corpus),
            "ms_per_kb": self.corpus["meta"].get("ms_per_kb"),
            "ms_per_input": self.corpus["meta"].get("ms_per_input"),
            "cold_start_s": self.corpus["meta"].get("cold_start_s"),
        }
        if self.ratchet is not None:
            out["ratchet"] = {"regressions": self.ratchet[0], "fixed": self.ratchet[1]}
        if "previous" in self.diffs:
            prev = self.diffs["previous"][3]
            out["previous"] = {
                "label": label(self.prev_corpus),
                "gained": prev["gained"],
                "lost": prev["lost"],
                "changed": prev["citations_changed"],
                "ms_per_kb": self.prev_corpus["meta"].get("ms_per_kb"),
            }
        return out

    def headline(self):
        s = self.summary()
        v = s["vectors"]
        passed = sum(x["passed"] for x in v.values())
        scored = sum(x["scored"] for x in v.values())
        kinds = ", ".join(
            f"{k} {v[k]['passed']}/{v[k]['scored']}" for k in KINDS if k in v
        )
        e = s["eyecite"]
        lines = [
            f"- Conformance vectors: {score(passed, scored)} ({kinds})",
            (
                f"- {s['corpus']} ({s['opinions']:,} opinions): "
                f"{num(e['agreement'], '{:.1%}')} agreement with {e['label']}; "
                f"{e['gained']:,} citations found only by citare, {e['lost']:,} only "
                f"by eyecite, {e['changed']:,} found by both with different fields"
            ),
            (
                f"- Speed: {num(s['ms_per_kb'])} ms/KB "
                f"(eyecite {num(e['ms_per_kb'])}), cold start {num(s['cold_start_s'])} s"
            ),
        ]
        if "previous" in s:
            p = s["previous"]
            lines.append(
                f"- Against {p['label']}: +{p['gained']:,} gained, −{p['lost']:,} lost, "
                f"{p['changed']:,} with changed fields; {num(p['ms_per_kb'])} ms/KB then"
            )
        return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--vectors-base", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--corpus-base", type=Path, required=True)
    ap.add_argument("--previous-vectors", type=Path)
    ap.add_argument("--previous-corpus", type=Path)
    ap.add_argument(
        "--previous-note", help="shown in place of the previous run when there is none"
    )
    ap.add_argument("--known-failures", type=Path)
    ap.add_argument("--link", help="where the full report and runs are")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    report = Report(args)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "bench-report.md").write_text(report.markdown(), encoding="utf-8")
    (args.out / "comment.md").write_text(report.comment(), encoding="utf-8")
    (args.out / "headline.md").write_text(report.headline(), encoding="utf-8")
    (args.out / "summary.json").write_text(
        json.dumps(report.summary(), indent=2) + "\n", encoding="utf-8"
    )
    for name, (_, _, rows, _) in report.diffs.items():
        diff.write_csv(args.out / f"vs-{name}.csv", rows)
    print(f"wrote {args.out}/bench-report.md, comment.md, headline.md, summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
