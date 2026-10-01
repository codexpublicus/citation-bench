# /// script
# requires-python = ">=3.11"
# dependencies = ["eyecite==2.7.8"]
# ///
"""citation-bench adapter for eyecite: JSONL requests on stdin, JSONL responses on stdout."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from eyecite import get_citations
from eyecite.tokenizers import AhocorasickTokenizer
from serialize import citation


def main():
    tokenizer = AhocorasickTokenizer()
    get_citations("1 U.S. 1", tokenizer=tokenizer)  # warm up before the timed requests
    for line in sys.stdin:
        req = json.loads(line)
        inp = req["input"]
        kwargs = {
            "tokenizer": tokenizer,
            "clean_steps": inp.get("clean_steps", []),
            "remove_ambiguous": req.get("options", {}).get("remove_ambiguous", False),
        }
        kwargs["markup_text" if inp.get("format") == "html" else "plain_text"] = inp[
            "text"
        ]
        try:
            res = {
                "id": req["id"],
                "citations": [citation(c) for c in get_citations(**kwargs)],
            }
        except Exception as e:  # noqa: BLE001 - report and keep serving
            res = {"id": req["id"], "error": f"{type(e).__name__}: {e}"}
        sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
