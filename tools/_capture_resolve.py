"""Runs inside an eyecite checkout's environment; writes ResolveTest's vectors as JSONL.

ResolveTest states its expectations through two helpers:

- checkResolution((group, snippet), ...): each snippet holds one citation; group is the
  index of the resource it resolves to, or None.
- checkReferenceResolution(groups, text): groups lists citation indices per resource.

Both become a resolve vector: a text and, for each citation in document order, the
index of its resource group (numbered by first appearance) or null. checkResolution
extracts each snippet on its own; the vector joins the snippets into one text, and the
exporter checks that eyecite reads the joined text the same way (same citations, same
resolution) before writing it, so eyecite still scores 100%.

Usage: python _capture_resolve.py <eyecite checkout> <version> <out.jsonl>
"""

import json
import logging
import os
import sys
import unittest
from pathlib import Path

checkout, version, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, checkout)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "adapters" / "eyecite"))

from eyecite import get_citations, resolve_citations
from serialize import citation, resolution

from tests import test_ResolveTest

# Tried in order. A plain space is the most natural document, but eyecite reads some
# snippet runs differently once they touch (two Id.s merge, a short cite's antecedent
# guess reaches into the previous snippet), and an ellipsis keeps them apart.
SEPARATORS = (" ", "\n\n", " ... ")

# Joined snippets trip eyecite's "Unknown overlap case" warning; the check below decides.
logging.getLogger("eyecite").setLevel(logging.ERROR)

out = {}  # test name -> vectors
skipped = []


def canonical(groups):
    """Renumber group labels by first appearance; None stays None."""
    seen = {}
    return [None if g is None else seen.setdefault(g, len(seen)) for g in groups]


def reproduces(text, groups):
    cites = get_citations(text)
    return cites, len(cites) == len(groups) and canonical(groups) == resolution(
        cites, resolve_citations(cites)
    )


def add(self, text, groups, helper):
    test = self._testMethodName
    cites, ok = reproduces(text, groups)
    if not ok:
        skipped.append(f"{test}: {text!r} doesn't reproduce {groups}")
        return
    vectors = out.setdefault(test, [])
    vectors.append(
        {
            "id": f"eyecite-{version}/resolve/{test}/{len(vectors)}",
            "kind": "resolve",
            "source": {
                "engine": "eyecite",
                "version": version,
                "file": "tests/test_ResolveTest.py",
                "test": test,
                "note": helper,
            },
            "input": {"text": text, "format": "plain", "clean_steps": []},
            "options": {},
            "expected": {
                "citations": [citation(c) for c in cites],
                "resolution": canonical(groups),
            },
        }
    )


def check_resolution(self, *expected_resolutions):
    groups = [g for g, _ in expected_resolutions]
    snippets = [snippet for _, snippet in expected_resolutions]
    for sep in SEPARATORS:
        if reproduces(sep.join(snippets), groups)[1]:
            break
    add(
        self, sep.join(snippets), groups, f"checkResolution, snippets joined by {sep!r}"
    )


def check_reference_resolution(
    self, expected_indices, citation_text, resolved_case_name_short=None
):
    if resolved_case_name_short:
        # Injects a resolved case name between extraction and resolution: eyecite API.
        skipped.append(f"{self._testMethodName}: {citation_text!r} (resolved name)")
        return
    n = len(get_citations(citation_text))
    groups = [None] * n
    for g, members in enumerate(expected_indices):
        for i in members:
            groups[i] = g
    add(self, citation_text, groups, "checkReferenceResolution")


test_ResolveTest.ResolveTest.checkResolution = check_resolution
test_ResolveTest.ResolveTest.checkReferenceResolution = check_reference_resolution
suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_ResolveTest.ResolveTest)
with open(os.devnull, "w") as devnull:
    result = unittest.TextTestRunner(stream=devnull).run(suite)
for test, err in result.failures + result.errors:
    print(f"resolve: {test._testMethodName} failed\n{err}", file=sys.stderr)
    out.pop(test._testMethodName, None)
for s in skipped:
    print(f"resolve: skipped {s}", file=sys.stderr)
lines = [json.dumps(v, ensure_ascii=False) + "\n" for t in sorted(out) for v in out[t]]
Path(out_path).write_text("".join(lines), encoding="utf-8")
print(f"resolve: {len(lines)} vectors from {result.testsRun} tests", file=sys.stderr)
