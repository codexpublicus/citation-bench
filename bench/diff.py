"""Compare two saved runs (bench/run.py --save) input by input.

Usage:
  uv run bench/diff.py BASE.json CANDIDATE.json [--md FILE] [--csv FILE] [--rows N]

The runs can come from two versions of one engine or from two different engines, as
long as they answered the same inputs (matched by id). For each input it reports:

- citations gained (only in the candidate) and lost (only in the base), matched by
  type + volume + reporter + page (plus title, chapter and section for statutes), or by
  span when a citation has none of those, as with id., supra and references;
- field-level changes on citations both runs found: span, groups, normalized reporter,
  year and the scored metadata (pin cite, parties, court, ...);
- for resolve inputs, a changed grouping; for annotate inputs, changed output text;
- errors that appear or go away.

The Markdown summary (stdout, or --md) holds each run's timing, the totals, the
agreement rate (citations found by both runs over those found by either), the reporters
and fields that differ most with an example of each, the inputs either run answered
with an error, and a table capped at --rows inputs; the CSV (--csv) lists every change,
one row each. For html inputs, where spans index each engine's own cleaned text, a
citation's text is found by searching the tag-stripped input for its volume, reporter
and page, and shown with some context.
"""

import argparse
import collections
import csv
import difflib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import SCORED_METADATA, canonical_resolution

KEY_GROUPS = ("volume", "reporter", "page", "title", "chapter", "section")
FIELDS = ("span", "full_span", "groups", "reporter_normalized", "year") + tuple(
    f"metadata.{k}" for k in sorted(SCORED_METADATA)
)
MAX_CHANGE_ROWS = 200  # Markdown detail rows, across the inputs in the summary table
CSV_COLUMNS = (
    "input",
    "kind",
    "change",
    "citation",
    "reporter",
    "field",
    "base",
    "candidate",
)
CONTEXT = 50  # characters either side of a citation located in markup
TAG = re.compile(r"<[^>]*>")
SPACE = re.compile(r"\s+")


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not str(data.get("format", "")).startswith("citation-bench-results/"):
        raise SystemExit(f"{path}: not a saved run (bench/run.py --save)")
    return data


def citation_key(c):
    """Identity of a citation across runs: what it cites, or where it sits."""
    groups = c.get("groups") or {}
    if any(groups.get(k) for k in KEY_GROUPS):
        return (c.get("type"),) + tuple(groups.get(k) for k in KEY_GROUPS)
    return (c.get("type"), "span", tuple(c.get("span") or ()))


def describe_key(key):
    if key[1] == "span":
        return f"{key[0]} @{list(key[2])}"
    parts = [v for v in key[1:] if v]
    return f"{key[0]} {' '.join(parts)}"


def keyed(citations):
    """Key each citation, numbering repeats so the nth match pairs with the nth."""
    seen = collections.Counter()
    out = {}
    for c in citations:
        k = citation_key(c)
        out[(k, seen[k])] = c
        seen[k] += 1
    return out


def pair(bc, cc):
    """Match two keyed citation lists. Returns (pairs, lost keys, gained keys).

    Citations with a volume, reporter or page match on those. The rest (id., supra,
    references, unknowns) are keyed by span, and a span moves whenever two engines clean
    the text before it differently; those left over are paired by aligning their types
    in document order, so a shifted id. shows as a changed span, not as lost and gained.
    """
    pairs = [(k, k) for k in bc if k in cc]
    lost = [k for k in bc if k not in cc]
    gained = [k for k in cc if k not in bc]

    def positional(keys):
        return sorted((k for k in keys if k[0][1] == "span"), key=lambda k: k[0][2])

    lb, gc = positional(lost), positional(gained)
    matcher = difflib.SequenceMatcher(
        None, [k[0][0] for k in lb], [k[0][0] for k in gc], autojunk=False
    )
    for block in matcher.get_matching_blocks():
        for j in range(block.size):
            b, c = lb[block.a + j], gc[block.b + j]
            pairs.append((b, c))
            lost.remove(b)
            gained.remove(c)
    return pairs, lost, gained


def field_value(c, field):
    if field.startswith("metadata."):
        return (c.get("metadata") or {}).get(field.split(".", 1)[1])
    return c.get(field)


def field_changes(base, cand):
    """(field, base value, candidate value) for each field that differs."""
    out = []
    for field in FIELDS:
        b, c = field_value(base, field), field_value(cand, field)
        if field in ("span", "full_span") and (b is None or c is None):
            continue  # an engine that doesn't report a span hasn't changed it
        if b != c:
            out.append((field, b, c))
    return out


def reporter_of(c):
    """What a citation cites, for grouping: its reporter, or its type when it has none."""
    return (c.get("groups") or {}).get("reporter") or f"({c.get('type')})"


class Located:
    """Find a citation's text in an input, for showing it in the report.

    Spans index the engine's own cleaned text, which the bench doesn't have for html
    input, so there the citation is searched for by its volume, reporter and page in
    the input with tags removed, and shown with some text either side.
    """

    def __init__(self, item):
        self.item = item
        self._text = None

    @property
    def text(self):
        if self._text is None:
            raw = self.item.get("input", {}).get("text", "")
            if self.item.get("input", {}).get("format") == "html":
                raw = html.unescape(TAG.sub(" ", raw))
            self._text = SPACE.sub(" ", raw)
        return self._text

    def __call__(self, c, nth=0):
        inp = self.item.get("input", {})
        span = c.get("span")
        if inp.get("format") == "plain":
            return inp["text"][span[0] : span[1]] if span else ""
        groups = c.get("groups") or {}
        parts = [groups[k] for k in ("volume", "title", "reporter") if groups.get(k)]
        parts += [groups[k] for k in ("chapter", "section", "page") if groups.get(k)]
        if not parts:
            return ""
        pattern = r"\W{0,12}".join(
            r"\s*".join(map(re.escape, p.split())) for p in parts
        )
        matches = list(re.finditer(r"(?<!\w)" + pattern + r"(?!\w)", self.text))
        if not matches:
            return ""
        m = matches[min(nth, len(matches) - 1)]
        start, end = max(m.start() - CONTEXT, 0), m.end() + CONTEXT
        return (
            ("…" if start else "")
            + self.text[start:end].strip()
            + ("…" if end < len(self.text) else "")
        )


def diff_input(base, cand):
    """All changes for one input, as dicts with CSV_COLUMNS keys (plus text)."""
    rows = []
    iid, kind = base["id"], base.get("kind", "find")

    def row(change, citation="", field="", b="", c="", text="", reporter=""):
        rows.append(
            {
                "input": iid,
                "kind": kind,
                "change": change,
                "citation": citation,
                "reporter": reporter,
                "field": field,
                "base": b,
                "candidate": c,
                "text": text,
            }
        )

    br, cr = base.get("response") or {}, cand.get("response") or {}
    if "error" in br or "error" in cr or not br or not cr:
        if br.get("error") != cr.get("error") or bool(br) != bool(cr):
            row(
                "error",
                b=br.get("error", "" if br else "no response"),
                c=cr.get("error", "" if cr else "no response"),
            )
        return rows

    bc, cc = keyed(br.get("citations") or []), keyed(cr.get("citations") or [])
    locate_b, locate_c = Located(base), Located(cand)
    pairs, lost, gained = pair(bc, cc)
    for k in lost:
        row(
            "lost",
            describe_key(k[0]),
            text=locate_b(bc[k], k[1]),
            reporter=reporter_of(bc[k]),
        )
    for k in gained:
        row(
            "gained",
            describe_key(k[0]),
            text=locate_c(cc[k], k[1]),
            reporter=reporter_of(cc[k]),
        )
    for kb, kc in pairs:
        for field, b, c in field_changes(bc[kb], cc[kc]):
            row(
                "changed",
                describe_key(kb[0]),
                field,
                json.dumps(b, ensure_ascii=False),
                json.dumps(c, ensure_ascii=False),
                locate_b(bc[kb], kb[1]),
                reporter_of(bc[kb]),
            )
    if kind == "resolve" and canonical_resolution(
        br.get("resolution")
    ) != canonical_resolution(cr.get("resolution")):
        row(
            "resolution",
            b=json.dumps(br.get("resolution")),
            c=json.dumps(cr.get("resolution")),
        )
    if kind == "annotate" and br.get("text") != cr.get("text"):
        row("text", b=br.get("text", ""), c=cr.get("text", ""))
    order = {"error": 0, "lost": 1, "gained": 2, "changed": 3}
    rows.sort(key=lambda r: (order.get(r["change"], 4), r["citation"], r["field"]))
    return rows


def diff_runs(base, cand):
    """Compare two loaded runs. Returns (rows, totals)."""
    bi = {i["id"]: i for i in base["inputs"]}
    ci = {i["id"]: i for i in cand["inputs"]}
    shared = [i for i in bi if i in ci]
    rows = [r for i in shared for r in diff_input(bi[i], ci[i])]
    counts = collections.Counter(r["change"] for r in rows)
    fields = collections.Counter(r["field"] for r in rows if r["change"] == "changed")

    def n_citations(items):
        return sum(
            len((items[i].get("response") or {}).get("citations") or []) for i in shared
        )

    def answered(item):
        r = item.get("response")
        return bool(r) and "error" not in r

    # Agreement counts citations on inputs both runs answered without an error.
    both = collections.Counter()
    found = {"base": collections.Counter(), "candidate": collections.Counter()}
    for i in shared:
        if not (answered(bi[i]) and answered(ci[i])):
            continue
        bc = keyed(bi[i]["response"].get("citations") or [])
        cc = keyed(ci[i]["response"].get("citations") or [])
        found["base"].update(reporter_of(c) for c in bc.values())
        found["candidate"].update(reporter_of(c) for c in cc.values())
        both.update(reporter_of(bc[k]) for k, _ in pair(bc, cc)[0])
    by_reporter = {}
    for r in rows:
        if r["change"] in ("lost", "gained"):
            entry = by_reporter.setdefault(
                r["reporter"],
                {
                    "base": found["base"][r["reporter"]],
                    "candidate": found["candidate"][r["reporter"]],
                    "both": both[r["reporter"]],
                    "lost": 0,
                    "gained": 0,
                    "example": {},
                },
            )
            entry[r["change"]] += 1
            entry["example"].setdefault(r["change"], r)
    field_examples = {}
    for r in rows:
        if r["change"] == "changed":
            field_examples.setdefault(r["field"], r)
    agreed = sum(both.values())
    either = sum(found["base"].values()) + sum(found["candidate"].values()) - agreed

    def errored(items):
        return {
            i: items[i]["response"]["error"]
            for i in shared
            if "error" in (items[i].get("response") or {})
        }

    totals = {
        "inputs": len(shared),
        "only_in_base": len(bi.keys() - ci.keys()),
        "only_in_candidate": len(ci.keys() - bi.keys()),
        "inputs_changed": len({r["input"] for r in rows}),
        "citations_base": n_citations(bi),
        "citations_candidate": n_citations(ci),
        "gained": counts["gained"],
        "lost": counts["lost"],
        "citations_changed": len(
            {(r["input"], r["citation"]) for r in rows if r["change"] == "changed"}
        ),
        "field_changes": dict(fields.most_common()),
        "resolution_changed": counts["resolution"],
        "text_changed": counts["text"],
        "errors_changed": counts["error"],
        "found_by_both": agreed,
        "found_by_either": either,
        "agreement": agreed / either if either else None,
        "by_reporter": dict(
            sorted(
                by_reporter.items(),
                key=lambda kv: (-(kv[1]["lost"] + kv[1]["gained"]), kv[0]),
            )
        ),
        "field_examples": field_examples,
        "errors_base": errored(bi),
        "errors_candidate": errored(ci),
    }
    return rows, totals


def md_cell(value, limit=80):
    value = str(value).replace("\n", " ").replace("|", "\\|")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def meta_row(label, bm, cm, key, fmt=str):
    b, c = bm.get(key), cm.get(key)
    if b is None and c is None:
        return []
    return [
        f"| {label} | {'' if b is None else fmt(b)} | {'' if c is None else fmt(c)} |"
    ]


def markdown(base, cand, rows, totals, max_rows, max_reporters=15):
    bm, cm = base["meta"], cand["meta"]
    lines = [
        f"# {bm['label']} → {cm['label']}",
        "",
        "| | base | candidate |",
        "|---|---|---|",
        f"| label | {md_cell(bm['label'])} | {md_cell(cm['label'])} |",
        f"| adapter | `{md_cell(bm['adapter'])}` | `{md_cell(cm['adapter'])}` |",
        f"| vectors | {md_cell(bm['vectors'])} | {md_cell(cm['vectors'])} |",
        f"| started | {bm.get('started')} | {cm.get('started')} |",
        *meta_row("input KB", bm, cm, "input_kb"),
        *meta_row("ms/input", bm, cm, "ms_per_input", lambda v: f"{v:.2f}"),
        *meta_row("ms/KB", bm, cm, "ms_per_kb", lambda v: f"{v:.2f}"),
        *meta_row("ms/input, median", bm, cm, "ms_p50", lambda v: f"{v:.2f}"),
        *meta_row("cold start (s)", bm, cm, "cold_start_s"),
        *meta_row("slowest input", bm, cm, "slowest", lambda v: f"`{v}`"),
        f"| citations | {totals['citations_base']} | {totals['citations_candidate']} |",
        f"| errors | {len(totals['errors_base'])} | {len(totals['errors_candidate'])} |",
        *meta_row("adapter crashes", bm, cm, "crashed", len),
    ]
    if bm.get("scored") or cm.get("scored"):
        lines.append(
            f"| passed | {bm.get('passed')}/{bm.get('scored')} "
            f"| {cm.get('passed')}/{cm.get('scored')} |"
        )
    lines += [
        "",
        (
            "Times are the adapter's own, per input, from the gap between its "
            "replies. Cold start runs from process start to the reply to a "
            "one-citation probe."
        ),
        "",
        "## Totals",
        "",
        f"- {totals['inputs']} inputs compared, {totals['inputs_changed']} changed",
        (
            f"- citations: **+{totals['gained']}** gained, **−{totals['lost']}** lost, "
            f"{totals['citations_changed']} found by both with changed fields"
        ),
    ]
    if totals["agreement"] is not None:
        lines.append(
            f"- agreement: **{100 * totals['agreement']:.1f}%** "
            f"({totals['found_by_both']} citations found by both of "
            f"{totals['found_by_either']} found by either, on inputs neither "
            "run answered with an error)"
        )
    if totals["field_changes"]:
        lines.append(
            "- field changes: "
            + ", ".join(f"{k} {n}" for k, n in totals["field_changes"].items())
        )
    for key, label in (
        ("resolution_changed", "resolve inputs grouped differently"),
        ("text_changed", "annotate inputs with different output"),
        ("errors_changed", "inputs whose error state changed"),
        ("only_in_base", "inputs only in base"),
        ("only_in_candidate", "inputs only in candidate"),
    ):
        if totals[key]:
            lines.append(f"- {totals[key]} {label}")

    reporters = list(totals["by_reporter"].items())
    if reporters:
        lines += [
            "",
            f"## Reporters that differ ({len(reporters)}"
            + (f", top {max_reporters} shown" if len(reporters) > max_reporters else "")
            + ")",
            "",
            "Found by each run, by both, and an example of the larger difference.",
            "",
            "| reporter | base | candidate | both | lost | gained | example |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for name, e in reporters[:max_reporters]:
            change = "lost" if e["lost"] >= e["gained"] else "gained"
            ex = e["example"][change]
            example = f"{change} in `{ex['input']}`: {ex['text'] or ex['citation']}"
            lines.append(
                f"| {md_cell(name, 40)} | {e['base']} | {e['candidate']} | {e['both']} "
                f"| {e['lost']} | {e['gained']} | {md_cell(example, 160)} |"
            )
    if totals["field_changes"]:
        lines += [
            "",
            "## Fields that differ on citations both found",
            "",
            "| field | citations | example |",
            "|---|---:|---|",
        ]
        for field, n in totals["field_changes"].items():
            ex = totals["field_examples"][field]
            example = (
                f"`{ex['input']}` {ex['citation']}: {ex['base']} → {ex['candidate']}"
                + (f" ({ex['text']})" if ex["text"] else "")
            )
            lines.append(f"| {field} | {n} | {md_cell(example, 200)} |")
    for key, who in (("errors_base", "base"), ("errors_candidate", "candidate")):
        errs = totals[key]
        if errs:
            lines += ["", f"## Errors in {who} ({len(errs)})", ""]
            lines += [
                f"- `{iid}`: {md_cell(msg, 160)}"
                for iid, msg in list(errs.items())[:50]
            ]
            if len(errs) > 50:
                lines.append(f"- … {len(errs) - 50} more")

    per_input = collections.defaultdict(collections.Counter)
    for r in rows:
        per_input[r["input"]][r["change"]] += 1
    ranked = sorted(per_input.items(), key=lambda kv: (-sum(kv[1].values()), kv[0]))
    if ranked:
        lines += [
            "",
            f"## Inputs with changes ({len(ranked)}"
            + (f", top {max_rows} shown" if len(ranked) > max_rows else "")
            + ")",
            "",
            "| input | gained | lost | changed fields | other |",
            "|---|---:|---:|---:|---|",
        ]
        for iid, c in ranked[:max_rows]:
            other = ", ".join(k for k in ("resolution", "text", "error") if c.get(k))
            lines.append(
                f"| `{md_cell(iid, 100)}` | {c['gained']} | {c['lost']} | {c['changed']} | {other} |"
            )
        by_input = collections.defaultdict(list)
        for r in rows:
            by_input[r["input"]].append(r)
        shown = [r for iid, _ in ranked[:max_rows] for r in by_input[iid]]
        shown = shown[:MAX_CHANGE_ROWS]
        lines += [
            "",
            "## Changes",
            "",
            "Lost and gained citations show their text under the run that found them.",
            "",
            "| input | change | citation | field | base | candidate |",
            "|---|---|---|---|---|---|",
        ]
        for r in shown:
            b, c = r["base"], r["candidate"]
            if r["change"] == "lost":
                b = r["text"]
            elif r["change"] == "gained":
                c = r["text"]
            cells = (r["input"], r["change"], r["citation"], r["field"])
            lines.append(
                "| "
                + " | ".join(
                    [md_cell(x) or " " for x in cells]
                    + [md_cell(x, 120) or " " for x in (b, c)]
                )
                + " |"
            )
        if len(rows) > len(shown):
            lines += [
                "",
                f"{len(shown)} of {len(rows)} changes shown; the CSV has all.",
            ]
    else:
        lines += ["", "No differences."]
    return "\n".join(lines) + "\n"


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS + ("text",))
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("base", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--md", type=Path, help="write the Markdown summary here")
    ap.add_argument("--csv", type=Path, help="write every change here")
    ap.add_argument("--rows", type=int, default=50, help="inputs in the summary table")
    ap.add_argument(
        "--reporters", type=int, default=15, help="reporters in the summary table"
    )
    args = ap.parse_args(argv)

    base, cand = load(args.base), load(args.candidate)
    rows, totals = diff_runs(base, cand)
    report = markdown(base, cand, rows, totals, args.rows, args.reporters)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(report, encoding="utf-8")
        print(f"wrote {args.md}")
    else:
        sys.stdout.write(report)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        write_csv(args.csv, rows)
        print(f"wrote {len(rows)} changes to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
