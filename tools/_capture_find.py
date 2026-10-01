"""Runs inside an eyecite checkout's environment; writes FindTest's vectors as JSONL.

Nearly every eyecite find test feeds (text, expected citations, kwargs) triples through
FindTest.run_test_pairs. Swapping that method for a recorder turns the suite into data.

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

out = []
count = 0


def record(self, test_pairs, message, tokenizers=None):
    global count
    test = self._testMethodName
    if test in SKIP_TESTS:
        return
    for i, (text, expected, *kwargs) in enumerate(test_pairs):
        kwargs = kwargs[0] if kwargs else {}
        clean_steps = list(kwargs.get("clean_steps", []))
        vector = {
            "id": f"eyecite-{version}/find/{test}/{i}",
            "source": {
                "engine": "eyecite",
                "version": version,
                "file": "tests/test_FindTest.py",
                "test": test,
                "note": message,
            },
            "input": {
                "text": text,
                "format": "html" if "html" in clean_steps else "plain",
                "clean_steps": clean_steps,
            },
            "options": {
                "remove_ambiguous": bool(kwargs.get("remove_ambiguous", False))
            },
            # Factory-built citations carry fake offsets, so expected spans are omitted.
            "expected": {"citations": [citation(c, with_span=False) for c in expected]},
        }
        out.append(json.dumps(vector, ensure_ascii=False) + "\n")
        count += 1


test_FindTest.FindTest.run_test_pairs = record
suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_FindTest.FindTest)
with open(os.devnull, "w") as devnull:
    result = unittest.TextTestRunner(stream=devnull).run(suite)
Path(out_path).write_text("".join(out), encoding="utf-8")
print(f"find: {count} vectors from {result.testsRun} tests", file=sys.stderr)
