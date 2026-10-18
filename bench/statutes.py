"""Statute and court-rule metrics: precision, recall and F1 per kind of law, from saved runs.

Usage:
  uv run bench/statutes.py --vectors vectors/statutes [--vectors vectors/statutes-proposed] \\
      RUN.json [RUN.json ...] [--md OUT.md] [--json OUT.json]

Each RUN is a run saved by bench/run.py --save over one of the vector sets. Runs with the
same label are one engine's answers and are merged, so an engine can be run over each set
separately. The expected citations come from the vectors.

Every law citation an engine reports (type full_law) is matched to an expected one by
overlapping span, one to one. Per kind of law (see law_kind), and per engine:

- found: precision, recall and F1 of law citations at the right place in the text
- fields: the same, counting a citation as right only when its code
  (reporter_normalized) and every group but the reporter as written (section, title,
  chapter, subject, rule, volume, page and so on) match the expected citation
- per-field accuracy over the matched citations, jurisdiction and exact span included,
  with the citations where the engine reported no value for a field counted apart
- bare §: unknown citations whose text starts with a section sign, which is how a
  statute an engine doesn't recognize usually comes through

Scores are against the reference vectors only: those whose provenance (see
docs/protocol.md, "Vector provenance") is `verified` or `hand-checked`. Vectors with any
other provenance are scored in tables of their own, labelled with it, and never folded
into the reference numbers. Where two engines both answered a vector, the report also
shows how often they agree with each other, whatever the provenance; agreement says
nothing about which engine is right.
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import load_vectors

LAW_KINDS = (
    "federal statute",
    "state statute",
    "regulation",
    "guideline",
    "court rule",
    "constitution",
)
REFERENCE = ("verified", "hand-checked")
STATUSES = (
    "verified",
    "hand-checked",
    "proposed",
    "engine-output",
    "engine-tests",
    "unrecorded",
)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETS = (ROOT / "vectors" / "statutes", ROOT / "vectors" / "statutes-proposed")
FIELDS = (
    "jurisdiction",
    "code",
    "subject",
    "title",
    "chapter",
    "section",
    "rule",
    "pin_cite",
    "span",
)

CONSTITUTION = re.compile(r"\bConst\b")
# The U.S. Sentencing Guidelines are their own kind, not a regulation (ruling of 2026-10-18).
GUIDELINE = re.compile(r"^U\.? ?S\.? ?S\.? ?G\.?$|Sentencing Guidelines")
REGULATION = re.compile(
    r"C\.F\.R\.|Fed\. ?Reg\.|^F\.?R\.?$|Treas\. ?Reg\.|Admin\.|\bRegs?\.|"
    r"Code R\.|NYCRR|N\.J\.A\.C\."
)
COURT_RULE = re.compile(
    r"\bR\. ?(?:Civ|Crim|Evid|App|Prof)\b|\bCt\. ?R\.|Practice Book|\bRules?\b|^MCR$"
)
FEDERAL = {"U.S.C.", "U.S.C.A.", "U.S.C.S.", "Stat.", "Pub. L."}


def law_kind(code, jurisdiction=None):
    """The kind of law a code is, from its standard abbreviation and jurisdiction."""
    code = code or ""
    if CONSTITUTION.search(code):
        return "constitution"
    if GUIDELINE.search(code):
        return "guideline"
    if REGULATION.search(code):
        return "regulation"
    if COURT_RULE.search(code):
        return "court rule"
    if code in FEDERAL or jurisdiction == "United States":
        return "federal statute"
    return "state statute"


def cite_kind(c):
    return law_kind(
        c.get("reporter_normalized"), (c.get("metadata") or {}).get("jurisdiction")
    )


def provenance(vector, source):
    """The vector's provenance status, else its set's (SOURCE.json), else unrecorded."""
    for p in (vector.get("provenance"), (source or {}).get("provenance")):
        if p and p.get("status"):
            return p["status"]
    return "unrecorded"


def load_sets(dirs):
    """{vector id: (vector, set name, provenance status)} over the vector directories."""
    out = {}
    for d in dirs:
        d = Path(d)
        source_file = (d if d.is_dir() else d.parent) / "SOURCE.json"
        source = json.loads(source_file.read_text()) if source_file.exists() else {}
        name = source.get("name") or d.name
        for v in load_vectors(d):
            if v.get("kind", "find") == "find" and "expected" in v:
                out[v["id"]] = (v, name, provenance(v, source))
    return out


def load_runs(paths):
    """{label: {vector id: response}}, merging runs that share a label."""
    runs = {}
    for p in paths:
        run = json.loads(Path(p).read_text(encoding="utf-8"))
        label = run["meta"]["label"]
        answers = runs.setdefault(label, {})
        for i in run["inputs"]:
            answers[i["id"]] = i.get("response") or {}
    return runs


def laws(cites):
    return [c for c in cites or [] if c.get("type") == "full_law"]


def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def match(expected, got):
    """Pair expected and reported law citations one to one: (pairs, unmatched reported).

    Citations pair by overlapping span when both sides have spans, else in order.
    """
    pairs, free = [], list(got)
    for e in expected:
        p = None
        if e.get("span"):
            p = next(
                (g for g in free if g.get("span") and overlaps(e["span"], g["span"])),
                None,
            )
        elif free and not free[0].get("span"):
            p = free[0]
        if p is not None:
            free.remove(p)
        pairs.append((e, p))
    return pairs, free


def field(c, name):
    if name == "code":
        return c.get("reporter_normalized")
    if name == "span":
        return tuple(c["span"]) if c.get("span") else None
    if name in ("jurisdiction", "pin_cite"):
        return (c.get("metadata") or {}).get(name)
    return (c.get("groups") or {}).get(name)


def fields_right(e, p):
    """Code and every group but the reporter as written agree."""
    eg = {k: v for k, v in (e.get("groups") or {}).items() if k != "reporter"}
    pg = {k: v for k, v in (p.get("groups") or {}).items() if k != "reporter"}
    return e.get("reporter_normalized") == p.get("reporter_normalized") and eg == pg


def bare_sections(vector, response):
    """Spans of unknown citations whose text starts with §."""
    text = vector["input"].get("text", "")
    plain = vector["input"].get("format", "plain") == "plain"
    return [
        c.get("span")
        for c in (response or {}).get("citations") or []
        if c.get("type") == "unknown"
        and plain
        and c.get("span")
        and text[c["span"][0] : c["span"][1]].lstrip().startswith("§")
    ]


def new_tally():
    return {
        "expected": 0,
        "reported": 0,
        "found": 0,
        "fields_right": 0,
        "bare_section": 0,
    }


def score(vectors, answers):
    """One engine over the vectors: tallies per kind, field accuracy, failing ids."""
    kinds = collections.defaultdict(new_tally)
    acc = {f: {"right": 0, "wrong": 0, "missing": 0} for f in FIELDS}
    misses = []
    for vid, (v, _, _) in vectors.items():
        response = answers.get(vid)
        if response is None:
            continue
        expected = laws(v["expected"]["citations"])
        got = laws(response.get("citations"))
        pairs, extra = match(expected, got)
        ok = not extra
        for e, p in pairs:
            t = kinds[cite_kind(e)]
            t["expected"] += 1
            if p is None:
                ok = False
                continue
            t["reported"] += 1
            t["found"] += 1
            right = fields_right(e, p)
            t["fields_right"] += right
            ok &= right
            for f in FIELDS:
                want, have = field(e, f), field(p, f)
                if want is None and have is None:
                    continue
                if have is None:
                    acc[f]["missing"] += 1
                else:
                    acc[f]["right" if want == have else "wrong"] += 1
        for p in extra:
            kinds[cite_kind(p)]["reported"] += 1
        for span in bare_sections(v, response):
            near = next(
                (e for e in expected if e.get("span") and overlaps(e["span"], span)),
                expected[0] if expected else None,
            )
            kinds[cite_kind(near) if near else "state statute"]["bare_section"] += 1
        if not ok:
            misses.append(vid)
    return {"kinds": dict(kinds), "fields": acc, "misses": sorted(misses)}


def prf(right, reported, expected):
    p = right / reported if reported else None
    r = right / expected if expected else None
    if p is None or r is None:
        return p, r, None
    return p, r, 2 * p * r / (p + r) if p + r else 0.0


def total(kinds):
    out = new_tally()
    for t in kinds.values():
        for k in out:
            out[k] += t[k]
    return out


def law_key(c):
    groups = {k: v for k, v in (c.get("groups") or {}).items() if k != "reporter"}
    return (
        tuple(c.get("span") or ()),
        c.get("reporter_normalized"),
        tuple(sorted(groups.items())),
    )


def agreement(vectors, a, b):
    """Per kind: vectors both answered, same law citations, same places, and neither
    reporting any law citation (agreement on nothing, counted in both of the others)."""
    out = collections.defaultdict(
        lambda: {"vectors": 0, "same": 0, "same_place": 0, "neither": 0}
    )
    for vid, (v, _, _) in vectors.items():
        if vid not in a or vid not in b:
            continue
        expected = laws(v["expected"]["citations"])
        kind = cite_kind(expected[0]) if expected else "none expected"
        la, lb = laws(a[vid].get("citations")), laws(b[vid].get("citations"))
        t = out[kind]
        t["vectors"] += 1
        t["same"] += sorted(map(law_key, la)) == sorted(map(law_key, lb))
        t["same_place"] += sorted(tuple(c.get("span") or ()) for c in la) == sorted(
            tuple(c.get("span") or ()) for c in lb
        )
        t["neither"] += not la and not lb
    return dict(out)


def groups_of(vectors):
    """Provenance groups to score apart: the reference first, then each other status."""
    by = collections.defaultdict(dict)
    for vid, entry in vectors.items():
        status = entry[2]
        by["reference" if status in REFERENCE else status][vid] = entry
    order = ["reference", *(s for s in STATUSES if s not in REFERENCE)]
    return {g: by[g] for g in order if by.get(g)}


def analyse(vectors, runs):
    groups = groups_of(vectors)
    labels = list(runs)
    out = {
        "engines": labels,
        "provenance": provenance_counts(vectors),
        "groups": {},
        "agreement": {},
    }
    for g, vs in groups.items():
        out["groups"][g] = {
            "vectors": len(vs),
            "statuses": dict(collections.Counter(e[2] for e in vs.values())),
            "engines": {label: score(vs, runs[label]) for label in labels},
        }
    for i, a in enumerate(labels):
        for b in labels[i + 1 :]:
            out["agreement"][f"{a} | {b}"] = agreement(vectors, runs[a], runs[b])
    return out


def provenance_counts(vectors):
    counts = collections.defaultdict(collections.Counter)
    for _, name, status in vectors.values():
        counts[name][status] += 1
    return {name: dict(c) for name, c in counts.items()}


def pct(x):
    return "" if x is None else f"{100 * x:.1f}%"


GROUP_TITLES = {
    "reference": "Reference vectors",
    "proposed": "Proposed vectors (not reviewed, not a reference)",
    "engine-output": "Vectors whose expected answer is an engine's output (not a reference)",
    "engine-tests": "Vectors from an engine's own test suite (not a reference)",
    "unrecorded": "Vectors with no recorded provenance (not a reference)",
}


def kind_rows(result, labels, kinds_order):
    lines = [
        "| Kind | Engine | Expected | Found | P | R | F1 | Fields right | P | R | F1 | Bare § |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for kind in kinds_order:
        for label in labels:
            kinds = result["engines"][label]["kinds"]
            t = total(kinds) if kind == "all" else kinds.get(kind)
            if not t:
                continue
            found = prf(t["found"], t["reported"], t["expected"])
            right = prf(t["fields_right"], t["reported"], t["expected"])
            name = f"**{kind}**" if kind == "all" else kind
            lines.append(
                f"| {name} | `{label}` | {t['expected']} | {t['found']} | "
                + " | ".join(map(pct, found))
                + f" | {t['fields_right']} | "
                + " | ".join(map(pct, right))
                + f" | {t['bare_section']} |"
            )
    return lines


def field_rows(result, labels):
    lines = [
        "| Field | " + " | ".join(f"`{label}`" for label in labels) + " |",
        "|---|" + "---:|" * len(labels),
    ]
    for f in FIELDS:
        cells = []
        for label in labels:
            a = result["engines"][label]["fields"][f]
            n = a["right"] + a["wrong"]
            cell = f"{a['right']}/{n} ({pct(a['right'] / n)})" if n else ""
            if a["missing"]:
                cell += f"{', ' if n else ''}{a['missing']} not reported"
            cells.append(cell)
        if any(cells):
            lines.append(f"| {f} | " + " | ".join(cells) + " |")
    return lines


def kinds_present(result):
    present = {k for r in result["engines"].values() for k in r["kinds"]}
    return [k for k in LAW_KINDS if k in present] + ["all"]


def markdown(analysis, heading="##", fields=True, misses=0):
    labels = analysis["engines"]
    lines = [f"{heading} Statute and court-rule citations", ""]
    for g, result in analysis["groups"].items():
        statuses = ", ".join(f"{n} {s}" for s, n in sorted(result["statuses"].items()))
        lines += [
            f"{heading}# {GROUP_TITLES.get(g, g)}",
            "",
            f"{result['vectors']} vectors ({statuses}).",
            "",
            *kind_rows(result, labels, kinds_present(result)),
            "",
        ]
        if fields:
            lines += [
                (
                    "Field accuracy over the citations each engine found, right of those it "
                    'gave a value for; "not reported" counts expected values it left out:'
                ),
                "",
                *field_rows(result, labels),
                "",
            ]
        for label in labels if misses else ():
            ids = result["engines"][label]["misses"]
            if ids:
                shown = ", ".join(f"`{i}`" for i in ids[:misses])
                more = f" and {len(ids) - misses} more" if len(ids) > misses else ""
                lines += [f"`{label}` misses or gets wrong: {shown}{more}", ""]
    if analysis["agreement"]:
        lines += [
            f"{heading}# Agreement between engines",
            "",
            (
                "How often two engines report the same law citations on a vector, over every "
                "vector both answered in the sets above. This is agreement, not accuracy: two "
                "engines can agree on a wrong answer, and when neither finds a law citation "
                "they agree on nothing."
            ),
            "",
            "| Engines | Kind | Vectors | Same citations | Same places | Neither found one |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for pair, kinds in analysis["agreement"].items():
            a, b = pair.split(" | ")
            order = [k for k in LAW_KINDS if k in kinds] + [
                k for k in kinds if k not in LAW_KINDS
            ]
            for kind in order:
                t = kinds[kind]
                lines.append(
                    f"| `{a}`, `{b}` | {kind} | {t['vectors']} | "
                    f"{t['same']} ({pct(t['same'] / t['vectors'])}) | "
                    f"{t['same_place']} ({pct(t['same_place'] / t['vectors'])}) | "
                    f"{t['neither']} |"
                )
        lines.append("")
    lines += [
        (
            "Found: a law citation at the expected place. Fields right: found, with the "
            "expected code and every part (section, title, chapter, subject, rule, volume, "
            "page). P, R and F1 are precision, recall and F1; a law citation an engine "
            "reports where none is expected counts against its precision under its own "
            "kind. Bare §: unknown citations starting with `§`, a statute the engine didn't "
            "recognize. Kinds come from the expected code (`bench/statutes.py`, `law_kind`)."
        ),
    ]
    return "\n".join(lines) + "\n"


def summary(analysis):
    """Headline numbers: per group, engine and kind, P/R/F1 for found and fields right."""
    out = {
        "engines": analysis["engines"],
        "provenance": analysis["provenance"],
        "groups": {},
    }
    for g, result in analysis["groups"].items():
        engines = {}
        for label, r in result["engines"].items():
            kinds = dict(r["kinds"], all=total(r["kinds"]))
            engines[label] = {
                kind: {
                    **t,
                    "found_prf": prf(t["found"], t["reported"], t["expected"]),
                    "fields_prf": prf(t["fields_right"], t["reported"], t["expected"]),
                }
                for kind, t in kinds.items()
            }
            engines[label]["_fields"] = r["fields"]
            engines[label]["_misses"] = r["misses"]
        out["groups"][g] = {
            "vectors": result["vectors"],
            "statuses": result["statuses"],
            "engines": engines,
        }
    out["agreement"] = analysis["agreement"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--vectors",
        type=Path,
        action="append",
        required=True,
        help="a vector set the runs cover; repeat for several",
    )
    ap.add_argument("runs", type=Path, nargs="+", help="runs saved by bench/run.py")
    ap.add_argument("--md", type=Path, help="write the Markdown report here")
    ap.add_argument("--json", type=Path, help="write the numbers here")
    ap.add_argument(
        "--misses", type=int, default=0, help="list up to N missed vector ids"
    )
    args = ap.parse_args(argv)

    analysis = analyse(load_sets(args.vectors), load_runs(args.runs))
    md = markdown(analysis, misses=args.misses)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(summary(analysis), indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
