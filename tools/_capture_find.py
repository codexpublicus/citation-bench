"""Runs inside an eyecite checkout's environment; writes FindTest's vectors as JSONL.

Nearly every eyecite find test feeds (text, expected citations, kwargs) triples through
FindTest.run_test_pairs. Swapping that method for a recorder turns the suite into data.

A few tests call get_citations directly and check spans or counts (STANDALONE_TESTS).
Their expectations live in assertions rather than data, so for those the recorder wraps
get_citations and stores what eyecite really returns, spans included. The tests still
run their assertions against those results, and a failing test's vectors are dropped.

Usage: python _capture_find.py <eyecite checkout> <version> <out.jsonl>
"""

import json
import os
import sys
import unittest
from pathlib import Path

checkout, version, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, checkout)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "adapters" / "eyecite"))

from serialize import citation
from tests import test_FindTest

# Tests that exercise eyecite-specific API rather than extraction behaviour.
SKIP_TESTS = {"test_custom_tokenizer"}

# Tests outside run_test_pairs whose get_citations calls become vectors with real spans.
# Not exported: test_date_in_editions (reporter database API, no text),
# test_citation_filtering (hand-built citation objects) and
# test_reference_extraction_using_resolved_names (injects names mid-pipeline).
STANDALONE_TESTS = {
    "test_citation_fullspan",
    "test_nominative_reporter_overlaps",
    "test_no_duplicate_editions",
    "test_reference_extraction_from_markup",
    "test_reference_filtering",
    "test_citation_in_parenthetical_does_not_emit_warning",
}

out = {}  # test name -> vectors
current = {"test": None}


def vector(test, i, note, text, clean_steps, remove_ambiguous, markup, citations):
    return {
        "id": f"eyecite-{version}/find/{test}/{i}",
        "kind": "find",
        "source": {
            "engine": "eyecite",
            "version": version,
            "file": "tests/test_FindTest.py",
            "test": test,
            "note": note,
        },
        "input": {
            "text": text,
            "format": "html" if markup else "plain",
            "clean_steps": clean_steps,
        },
        "options": {"remove_ambiguous": remove_ambiguous},
        "expected": {"citations": citations},
    }


def record(self, test_pairs, message, tokenizers=None):
    test = self._testMethodName
    if test in SKIP_TESTS:
        return
    vectors = out.setdefault(test, [])
    for i, (text, expected, *kwargs) in enumerate(test_pairs):
        kwargs = kwargs[0] if kwargs else {}
        clean_steps = list(kwargs.get("clean_steps", []))
        vectors.append(
            vector(
                test,
                i,
                message,
                text,
                clean_steps,
                bool(kwargs.get("remove_ambiguous", False)),
                "html" in clean_steps,
                # Factory-built citations carry fake offsets, so expected spans are omitted.
                [citation(c, with_span=False) for c in expected],
            )
        )


real_get_citations = test_FindTest.get_citations


def recording_get_citations(plain_text="", *args, **kwargs):
    cites = real_get_citations(plain_text, *args, **kwargs)
    test = current["test"]
    if test in STANDALONE_TESTS:
        markup = kwargs.get("markup_text", "")
        vectors = out.setdefault(test, [])
        vectors.append(
            vector(
                test,
                len(vectors),
                "Real eyecite output, spans included",
                markup or plain_text,
                list(kwargs.get("clean_steps") or []),
                bool(kwargs.get("remove_ambiguous", args[0] if args else False)),
                bool(markup),
                # Spans index the cleaned text, which only plain input shares with us.
                [citation(c, with_span=not markup) for c in cites],
            )
        )
    return cites


class Result(unittest.TextTestResult):
    def startTest(self, test):
        current["test"] = test._testMethodName
        super().startTest(test)

    def addFailure(self, test, err):
        out.pop(test._testMethodName, None)
        super().addFailure(test, err)

    def addError(self, test, err):
        out.pop(test._testMethodName, None)
        super().addError(test, err)


test_FindTest.FindTest.run_test_pairs = record
test_FindTest.get_citations = recording_get_citations
suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_FindTest.FindTest)
with open(os.devnull, "w") as devnull:
    result = unittest.TextTestRunner(stream=devnull, resultclass=Result).run(suite)
for test, err in result.failures + result.errors:
    print(f"find: {test._testMethodName} failed, not exported\n{err}", file=sys.stderr)
lines = [json.dumps(v, ensure_ascii=False) + "\n" for t in sorted(out) for v in out[t]]
Path(out_path).write_text("".join(lines), encoding="utf-8")
print(f"find: {len(lines)} vectors from {result.testsRun} tests", file=sys.stderr)
