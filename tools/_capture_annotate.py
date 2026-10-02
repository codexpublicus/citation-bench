"""Runs inside an eyecite checkout's environment; writes AnnotateTest's vectors as JSONL.

AnnotateTest.test_annotate loops over (source text, expected output, clean steps,
annotate kwargs) tuples held in a local variable, so the recorder listens to the calls
instead: get_citations tells it the input and clean steps, annotate_citations the
markers and the unbalanced-tag mode, and assertEqual the expected output.

Each vector asks the engine to wrap every citation's span in markers built from a
template, where {i} stands for the citation's index in document order. eyecite's own
markers are "<{i}>" and "</{i}>", or a fixed anchor tag.

Not exported: pairs with a Python callable as a clean step or as a custom annotator,
which no other engine can receive, and test_long_diff / test_span_with_pincite /
test_tag_balancing, which test eyecite's helpers on hand-picked offsets.

Usage: python _capture_annotate.py <eyecite checkout> <version> <out.jsonl>
"""

import json
import os
import sys
import unittest
from pathlib import Path

checkout, version, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, checkout)

from tests import test_AnnotateTest

out = []
skipped = []
pending = {}
real_get_citations = test_AnnotateTest.get_citations
real_annotate = test_AnnotateTest.annotate_citations


def template(markers):
    """Turn per-citation markers into one template, or None if they don't fit one."""
    if not markers:
        return None
    candidate = markers[0].replace("0", "{i}") if "0" in markers[0] else markers[0]
    if all(m == candidate.replace("{i}", str(i)) for i, m in enumerate(markers)):
        return candidate
    return None


def recording_get_citations(plain_text="", **kwargs):
    markup = kwargs.get("markup_text", "")
    steps = list(kwargs.get("clean_steps") or [])
    pending.clear()
    pending["input"] = {
        "text": markup or plain_text,
        "format": "html" if markup else "plain",
        "clean_steps": steps,
    }
    if any(not isinstance(s, str) for s in steps):
        pending["skip"] = "callable clean step"
    return real_get_citations(plain_text, **kwargs)


def recording_annotate(plain_text, annotations, source_text="", **kwargs):
    annotations = list(annotations)
    before = template([b for _, b, _ in annotations])
    after = template([a for _, _, a in annotations])
    if kwargs.get("annotator") is not None:
        pending["skip"] = "custom annotator"
    elif before is None or after is None:
        pending["skip"] = "markers don't follow a template"
    pending["options"] = {
        "annotate": {
            "before": before,
            "after": after,
            "unbalanced_tags": kwargs.get("unbalanced_tags", "unchecked"),
        }
    }
    return real_annotate(plain_text, annotations, source_text=source_text, **kwargs)


def recording_assert_equal(self, first, second, msg=None):
    unittest.TestCase.assertEqual(self, first, second, msg)
    if "options" not in pending:
        return
    if "skip" in pending:
        skipped.append(f"{pending['input']['text'][:60]!r} ({pending['skip']})")
    else:
        i = len(out)
        out.append(
            {
                "id": f"eyecite-{version}/annotate/test_annotate/{i}",
                "kind": "annotate",
                "source": {
                    "engine": "eyecite",
                    "version": version,
                    "file": "tests/test_AnnotateTest.py",
                    "test": "test_annotate",
                },
                "input": pending["input"],
                "options": pending["options"],
                "expected": {"text": second},
            }
        )
    pending.clear()


test_AnnotateTest.get_citations = recording_get_citations
test_AnnotateTest.annotate_citations = recording_annotate
test_AnnotateTest.AnnotateTest.assertEqual = recording_assert_equal
suite = unittest.TestSuite([test_AnnotateTest.AnnotateTest("test_annotate")])
with open(os.devnull, "w") as devnull:
    result = unittest.TextTestRunner(stream=devnull).run(suite)
if not result.wasSuccessful():
    for _, err in result.failures + result.errors:
        print(f"annotate: test_annotate failed\n{err}", file=sys.stderr)
    sys.exit(1)
for s in skipped:
    print(f"annotate: skipped {s}", file=sys.stderr)
lines = [json.dumps(v, ensure_ascii=False) + "\n" for v in out]
Path(out_path).write_text("".join(lines), encoding="utf-8")
print(f"annotate: {len(lines)} vectors", file=sys.stderr)
