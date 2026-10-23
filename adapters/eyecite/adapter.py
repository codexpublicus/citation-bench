# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "eyecite==2.7.8",
#   # eyecite 2.7.8's own uv.lock, which the vectors were exported under. Newer
#   # reporters-db releases shift some full spans, so the data has to match too.
#   "courts-db==0.10.22",
#   "fast-diff-match-patch==2.0.1",
#   "lxml==6.1.0",
#   "pyahocorasick==2.0.0",
#   "regex==2023.12.25",
#   "reporters-db==3.2.53",
# ]
# ///
"""citation-bench adapter for eyecite: JSONL requests on stdin, JSONL responses on stdout.

Speaks protocol version 2 (docs/protocol.md): request kinds find, resolve and annotate.
"""

import json
import logging
import os
import sys
from pathlib import Path

# eyecite 2.7.8 picks between two tokens that match the same span by the iteration
# order of a set of extractors hashed by their repr, so its output depends on the
# string hash seed: "86 T.C. at 561" is a short cite under PYTHONHASHSEED=1 and a full
# cite under 0 or 2. Pinning the seed keeps every run, stored ones included, the same.
# The seed is fixed at interpreter start, so restart under it when it isn't set.
HASH_SEED = "0"
if os.environ.get("PYTHONHASHSEED") != HASH_SEED:
    os.environ["PYTHONHASHSEED"] = HASH_SEED
    os.execv(sys.executable, [sys.executable, *sys.argv])

sys.path.insert(0, str(Path(__file__).parent))

from eyecite import annotate_citations, get_citations, resolve_citations
from eyecite.models import Document
from eyecite.tokenizers import AhocorasickTokenizer
from serialize import citation, resolution

TOKENIZER = AhocorasickTokenizer()
# Resolve vectors trip eyecite's "Unknown overlap case" warning on every run.
logging.getLogger("eyecite").setLevel(logging.ERROR)


def text_kwargs(inp):
    key = "markup_text" if inp.get("format") == "html" else "plain_text"
    return {key: inp["text"], "clean_steps": list(inp.get("clean_steps", []))}


def find(req):
    return get_citations(
        tokenizer=TOKENIZER,
        remove_ambiguous=req.get("options", {}).get("remove_ambiguous", False),
        **text_kwargs(req["input"]),
    )


def handle(req):
    kind = req.get("kind", "find")
    if kind == "find":
        return {"citations": [citation(c) for c in find(req)]}
    if kind == "resolve":
        cites = find(req)
        return {
            "citations": [citation(c) for c in cites],
            "resolution": resolution(cites, resolve_citations(cites)),
        }
    if kind == "annotate":
        opts = req["options"]["annotate"]
        cites = find(req)
        markers = [
            (
                c.span(),
                opts["before"].replace("{i}", str(i)),
                opts["after"].replace("{i}", str(i)),
            )
            for i, c in enumerate(cites)
        ]
        document = Document(**text_kwargs(req["input"]))
        return {
            "text": annotate_citations(
                document.plain_text,
                markers,
                source_text=req["input"]["text"],
                unbalanced_tags=opts.get("unbalanced_tags", "unchecked"),
            )
        }
    raise ValueError(f"unsupported kind {kind!r}")


def main():
    get_citations("1 U.S. 1", tokenizer=TOKENIZER)  # warm up before the timed requests
    for line in sys.stdin:
        req = json.loads(line)
        try:
            res = {"id": req["id"], **handle(req)}
        except Exception as e:  # noqa: BLE001 - report and keep serving
            res = {"id": req["id"], "error": f"{type(e).__name__}: {e}"}
        sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
