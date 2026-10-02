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

The Markdown summary (stdout, or --md) holds the totals and a table capped at --rows
inputs; the CSV (--csv) lists every change, one row each.
"""

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import SCORED_METADATA, canonical_resolution

KEY_GROUPS = ("volume", "reporter", "page", "title", "chapter", "section")
FIELDS = ("span", "full_span", "groups", "reporter_normalized", "year") + tuple(
    f"metadata.{k}" for k in sorted(SCORED_METADATA)
)
MAX_CHANGE_ROWS = 200  # Markdown detail rows, across the inputs in the summary table
CSV_COLUMNS = ("input", "kind", "change", "citation", "field", "base", "candidate")


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


def matched_text(item, c):
    span = c.get("span")
    if not span or item.get("input", {}).get("format") != "plain":
        return ""
    return item["input"]["text"][span[0] : span[1]]


def diff_input(base, cand):
    """All changes for one input, as dicts with CSV_COLUMNS keys (plus text)."""
    rows = []
    iid, kind = base["id"], base.get("kind", "find")

    def row(change, citation="", field="", b="", c="", text=""):
        rows.append(
            {
                "input": iid,
                "kind": kind,
                "change": change,
                "citation": citation,
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
    for k in bc.keys() - cc.keys():
        row("lost", describe_key(k[0]), text=matched_text(base, bc[k]))
    for k in cc.keys() - bc.keys():
        row("gained", describe_key(k[0]), text=matched_text(cand, cc[k]))
    for k in bc.keys() & cc.keys():
        for field, b, c in field_changes(bc[k], cc[k]):
            row(
                "changed",
                describe_key(k[0]),
                field,
                json.dumps(b, ensure_ascii=False),
                json.dumps(c, ensure_ascii=False),
                matched_text(base, bc[k]),
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
    }
    return rows, totals


def md_cell(value, limit=80):
    value = str(value).replace("\n", " ").replace("|", "\\|")
    return value if len(value) <= limit else value[: limit - 1] + "…"


def markdown(base, cand, rows, totals, max_rows):
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
        f"| ms/input | {bm.get('ms_per_input')} | {cm.get('ms_per_input')} |",
        f"| citations | {totals['citations_base']} | {totals['citations_candidate']} |",
        f"| passed | {bm.get('passed')}/{bm.get('scored')} | {cm.get('passed')}/{cm.get('scored')} |",
        "",
        "## Totals",
        "",
        f"- {totals['inputs']} inputs compared, {totals['inputs_changed']} changed",
        (
            f"- citations: **+{totals['gained']}** gained, **−{totals['lost']}** lost, "
            f"{totals['citations_changed']} found by both with changed fields"
        ),
    ]
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
            cells = (r["input"], r["change"], r["citation"], r["field"], b, c)
            lines.append("| " + " | ".join(md_cell(x) or " " for x in cells) + " |")
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
    args = ap.parse_args(argv)

    base, cand = load(args.base), load(args.candidate)
    rows, totals = diff_runs(base, cand)
    report = markdown(base, cand, rows, totals, args.rows)
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
