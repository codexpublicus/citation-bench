"""One engine's benchmark report: vector scores, corpus speed, and diffs against eyecite and
an earlier version of the same engine.

Usage:
  uv run bench/report.py --vectors V.json --vectors-base V0.json \\
      --corpus C.json --corpus-base C0.json --out DIR \\
      [--comparison S.json --comparison-base S0.json] \\
      [--previous-vectors PV.json] [--previous-corpus PC.json] \\
      [--previous-comparison PS.json] [--previous-note TEXT] \\
      [--known-failures FILE] [--link URL] \\
      [--statute-vectors DIR ... --statute-runs RUN ...]

Every input is a run saved by bench/run.py --save (or restored by bench/baseline.py).
The base runs are eyecite's; the previous runs are the engine's last release. --corpus
is the primary corpus, the stare.pub sample; --comparison is eyecite's comparison
sample, reported after it as a secondary score, labelled as such, to read beside
eyecite's own published numbers. With --statute-runs (each engine's runs over the
--statute-vectors sets), the report also has bench/statutes.py's precision, recall and
F1 per kind of law. DIR gets:

- bench-report.md: scores per request kind, corpus timing, the ratchet against
  --known-failures, and each diff in full (bench/diff.py's report, capped as usual)
- comment.md: the same report with shorter diff tables, sized for a PR comment
- headline.md: a few lines for release notes
- summary.json: the headline numbers, the comparison sample's under `comparison`
- vs-eyecite.csv, vs-previous.csv: every change in each diff on the primary corpus;
  vs-eyecite-sample.csv, vs-previous-sample.csv: the same on the comparison sample

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
import statutes
from run import KINDS

COMMENT_LIMIT = 60000  # GitHub refuses comments over 65,536 characters
COMMENT_CAPS = ((20, 40, 10), (10, 15, 8))  # (inputs, change rows, reporters)


def load(path):
    return diff.load(path) if path else None


def label(run):
    return run["meta"]["label"]


def corpus_name(run):
    return (run["meta"].get("source") or {}).get("name", "corpus")


SECONDARY = "eyecite's comparison sample"


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
        self.comparison = load(args.comparison)
        self.comparison_base = load(args.comparison_base)
        if (self.comparison is None) != (self.comparison_base is None):
            raise SystemExit("--comparison and --comparison-base go together")
        self.prev_vectors = load(args.previous_vectors)
        self.prev_corpus = load(args.previous_corpus)
        self.prev_comparison = (
            load(args.previous_comparison) if self.comparison else None
        )
        self.previous_note = args.previous_note
        self.link = args.link
        self.ratchet = (
            ratchet(self.vectors, args.known_failures) if args.known_failures else None
        )
        self.statutes = (
            statutes.analyse(
                statutes.load_sets(args.statute_vectors or statutes.DEFAULT_SETS),
                statutes.load_runs(args.statute_runs),
            )
            if args.statute_runs
            else None
        )
        self.diffs = {}  # name -> (base run, candidate run, rows, totals)
        self.agreements = {}  # id(run) -> its agreement with eyecite on its corpus
        corpora = [("", self.corpus_base, self.corpus, self.prev_corpus)]
        if self.comparison:
            corpora.append(
                ("-sample", self.comparison_base, self.comparison, self.prev_comparison)
            )
        for suffix, base, cand, prev in corpora:
            self.diffs[f"eyecite{suffix}"] = self.compare(base, cand)
            self.agreements[id(cand)] = self.diffs[f"eyecite{suffix}"][3]["agreement"]
            if prev:
                self.diffs[f"previous{suffix}"] = self.compare(prev, cand)
                self.agreements[id(prev)] = self.compare(base, prev)[3]["agreement"]

    @staticmethod
    def compare(base, cand):
        rows, totals = diff.diff_runs(base, cand)
        return base, cand, rows, totals

    def previous_label(self):
        prev = self.prev_corpus or self.prev_comparison
        return label(prev) if prev else None

    def columns(self):
        """(name, vectors run, primary corpus run, comparison sample run) per engine."""
        cols = [(label(self.corpus), self.vectors, self.corpus, self.comparison)]
        cols.append(
            (
                label(self.corpus_base),
                self.vectors_base,
                self.corpus_base,
                self.comparison_base,
            )
        )
        if self.previous_label():
            cols.append(
                (
                    self.previous_label(),
                    self.prev_vectors,
                    self.prev_corpus,
                    self.prev_comparison,
                )
            )
        return cols

    def agreement(self, corpus):
        return None if corpus is None else self.agreements.get(id(corpus))

    @staticmethod
    def header(cols):
        return [
            "| | " + " | ".join(f"`{c[0]}`" for c in cols) + " |",
            "|---|" + "---:|" * len(cols),
        ]

    def table(self):
        cols = self.columns()
        lines = self.header(cols)

        def row(name, cells):
            lines.append(f"| {name} | " + " | ".join(cells) + " |")

        scores = [kind_scores(c[1]) if c[1] else {} for c in cols]
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
            [num(c[1]["meta"].get("ms_per_input")) if c[1] else "" for c in cols],
        )
        lines += self.corpus_rows([c[2] for c in cols])
        return lines

    def comparison_table(self):
        """eyecite's comparison sample, the secondary score, in a table of its own."""
        if not self.comparison:
            return []
        cols = self.columns()
        meta = self.comparison["meta"]
        return [
            (
                f"**Secondary: {SECONDARY}** (`{corpus_name(self.comparison)}`, "
                f"{meta['inputs']:,} opinions). This is the CourtListener sample eyecite "
                "benchmarks itself on; read it beside eyecite's own published numbers. "
                "The table above is the primary score."
            ),
            "",
            *self.header(cols),
            *self.corpus_rows([c[3] for c in cols]),
        ]

    def corpus_rows(self, runs):
        """Rows for one corpus, a run (or None) per column."""
        lines = []

        def row(name, cells):
            lines.append(f"| {name} | " + " | ".join(cells) + " |")

        def cells(fn):
            return ["" if c is None else fn(c) for c in runs]

        n = runs[0]["meta"]["inputs"]
        row(f"{corpus_name(runs[0])}: citations", cells(lambda c: f"{citations(c):,}"))
        row(
            "agreement with eyecite",
            [num(self.agreement(c), "{:.1%}") for c in runs],
        )
        row("opinions with errors", cells(lambda c: f"{errors(c):,} of {n:,}"))
        for key, name, fmt in (
            ("ms_per_kb", "ms/KB", "{:,.2f}"),
            ("ms_per_input", "ms/opinion, mean", "{:,.1f}"),
            ("ms_p50", "ms/opinion, median", "{:,.1f}"),
            ("ms_max", "slowest opinion (ms)", "{:,.0f}"),
            ("cold_start_s", "cold start (s)", "{:,.2f}"),
        ):
            row(name, cells(lambda c, key=key, fmt=fmt: num(c["meta"].get(key), fmt)))
        crashed = cells(lambda c: str(len(c["meta"].get("crashed") or [])))
        if any(x not in ("", "0") for x in crashed):
            row("adapter crashes or timeouts", crashed)
        return lines

    def provenance(self):
        meta = self.corpus["meta"]
        lines = [
            (
                f"citation-bench `{(meta.get('bench_commit') or '')[:12]}` · "
                f"`{corpus_name(self.corpus)}`: {meta['inputs']:,} opinions, "
                f"{meta.get('input_kb', 0):,.0f} KB"
            )
        ]
        engine = meta.get("engine") or {}
        if engine.get("commit"):
            lines.append(
                f"built from {engine.get('name', '')} {engine.get('version', '')} "
                f"at `{engine['commit'][:12]}`"
            )
        bases = [self.corpus_base]
        if self.comparison_base:
            bases.append(self.comparison_base)
        for run in bases:
            base = run["meta"]
            on = f"eyecite on `{corpus_name(run)}`" if len(bases) > 1 else "eyecite"
            cached = base.get("cached")
            host = (base.get("host") or {}).get("platform", "an unrecorded host")
            if cached:
                lines.append(
                    f"{on}: the stored run (key `{cached['key'][:12]}`), "
                    f"measured {base.get('started')} on {host}"
                )
            else:
                lines.append(f"{on}: run live, because no stored run matched its key")
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
        title = (
            f"<code>{label(cand)}</code> against <code>{label(base)}</code> "
            f"on <code>{corpus_name(cand)}</code>"
        )
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
        ]
        if self.comparison:
            lines += [*self.comparison_table(), ""]
        lines += self.ratchet_lines()
        if self.prev_comparison and not self.prev_corpus:
            lines += [
                "",
                (
                    f"`{self.previous_label()}` has no saved run on "
                    f"`{corpus_name(self.corpus)}`, so it is compared on {SECONDARY} "
                    "only."
                ),
            ]
        elif not self.previous_label() and self.previous_note:
            lines += ["", self.previous_note]
        if self.statutes:
            misses = 0 if caps is not None else 10
            lines += [
                "",
                statutes.markdown(self.statutes, "###", misses=misses).strip(),
            ]
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

    def corpus_summary(self, suffix=""):
        """The headline numbers on one corpus: the primary, or the comparison sample."""
        base, cand, _, eyecite = self.diffs[f"eyecite{suffix}"]
        out = {
            "corpus": corpus_name(cand),
            "opinions": cand["meta"]["inputs"],
            "eyecite": {
                "label": label(base),
                "agreement": eyecite["agreement"],
                "gained": eyecite["gained"],
                "lost": eyecite["lost"],
                "changed": eyecite["citations_changed"],
                "ms_per_kb": base["meta"].get("ms_per_kb"),
                "cached_key": (base["meta"].get("cached") or {}).get("key"),
            },
            "citations": citations(cand),
            "errors": errors(cand),
            "ms_per_kb": cand["meta"].get("ms_per_kb"),
            "ms_per_input": cand["meta"].get("ms_per_input"),
            "cold_start_s": cand["meta"].get("cold_start_s"),
        }
        if f"previous{suffix}" in self.diffs:
            prev_run, _, _, prev = self.diffs[f"previous{suffix}"]
            out["previous"] = {
                "label": label(prev_run),
                "gained": prev["gained"],
                "lost": prev["lost"],
                "changed": prev["citations_changed"],
                "ms_per_kb": prev_run["meta"].get("ms_per_kb"),
            }
        return out

    def summary(self):
        scores = kind_scores(self.vectors)
        primary = self.corpus_summary()
        out = {
            "label": label(self.corpus),
            "bench_commit": self.corpus["meta"].get("bench_commit"),
            "corpus": primary.pop("corpus"),
            "opinions": primary.pop("opinions"),
            "vectors": {k: {"passed": p, "scored": n} for k, (p, n) in scores.items()},
            **primary,
        }
        if self.comparison:
            out["comparison"] = {"name": SECONDARY, **self.corpus_summary("-sample")}
        if self.ratchet is not None:
            out["ratchet"] = {"regressions": self.ratchet[0], "fixed": self.ratchet[1]}
        if self.statutes:
            out["statutes"] = statutes.summary(self.statutes)
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
        if "comparison" in s:
            c = s["comparison"]
            ce = c["eyecite"]
            lines.append(
                f"- Secondary, {SECONDARY} ({c['corpus']}, {c['opinions']:,} opinions): "
                f"{num(ce['agreement'], '{:.1%}')} agreement with {ce['label']}; "
                f"{ce['gained']:,} only by citare, {ce['lost']:,} only by eyecite, "
                f"{ce['changed']:,} with different fields; {num(c['ms_per_kb'])} ms/KB "
                f"(eyecite {num(ce['ms_per_kb'])})"
            )
        if self.statutes and "reference" in self.statutes["groups"]:
            ref = self.statutes["groups"]["reference"]
            f1s = []
            for engine, r in ref["engines"].items():
                t = statutes.total(r["kinds"])
                f1 = statutes.prf(t["fields_right"], t["reported"], t["expected"])[2]
                f1s.append(f"{engine} {num(f1, '{:.1%}')}")
            lines.append(
                f"- Statutes and court rules ({ref['vectors']} reference vectors, "
                "fields right): F1 " + ", ".join(f1s)
            )
        for where in (s, s.get("comparison") or {}):
            if "previous" in where:
                p = where["previous"]
                lines.append(
                    f"- Against {p['label']} on {where['corpus']}: +{p['gained']:,} "
                    f"gained, −{p['lost']:,} lost, {p['changed']:,} with changed fields; "
                    f"{num(p['ms_per_kb'])} ms/KB then"
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
        "--comparison",
        type=Path,
        help="the engine's run on eyecite's comparison sample",
    )
    ap.add_argument(
        "--comparison-base", type=Path, help="eyecite's run on its comparison sample"
    )
    ap.add_argument(
        "--previous-comparison",
        type=Path,
        help="the earlier engine's run on eyecite's comparison sample",
    )
    ap.add_argument(
        "--previous-note", help="shown in place of the previous run when there is none"
    )
    ap.add_argument("--known-failures", type=Path)
    ap.add_argument("--link", help="where the full report and runs are")
    ap.add_argument(
        "--statute-vectors",
        type=Path,
        action="append",
        help="a statute vector set (default: vectors/statutes, vectors/statutes-proposed)",
    )
    ap.add_argument(
        "--statute-runs",
        type=Path,
        nargs="+",
        help="each engine's runs over the statute vector sets",
    )
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
