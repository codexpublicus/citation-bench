# Adapter protocol

An **adapter** puts a citation engine behind a process boundary. Any executable that follows
this protocol can be benchmarked, whatever its language or license. Its source never has to
be shared: the bench only sees what crosses stdin and stdout.

## Transport

- The bench starts the adapter once and writes one **request** per line to its stdin as
  UTF-8 JSON (JSON Lines).
- The adapter writes exactly one **response** line to stdout per request, in request
  order. It flushes after each line.
- When stdin closes, the adapter exits 0.
- Anything written to stderr is logged and otherwise ignored.
- If the adapter can't handle one request, it answers that request with an `error` and
  carries on. A crash or a missing line fails every request still outstanding.

Setup work such as loading data or compiling patterns belongs before the first request.
The bench times the requests, not process start.

## Request

```json
{"id": "eyecite-2.7.8/find/test_find_citations/0",
 "input": {"text": "1 U.S. 1", "format": "plain", "clean_steps": []},
 "options": {"remove_ambiguous": false}}
```

| Field | Meaning |
|---|---|
| `id` | Opaque. Echo it back unchanged. |
| `input.text` | The document. |
| `input.format` | `plain` or `html`. If it's `html`, the engine gets the markup and does its own conversion to text. |
| `input.clean_steps` | eyecite cleaning steps (`html`, `inline_whitespace`, `all_whitespace`, `underscores`, `xml`). Engines that don't model these may ignore them. |
| `options.remove_ambiguous` | Drop citations whose reporter can't be pinned to a single edition. |

## Response

```json
{"id": "eyecite-2.7.8/find/test_find_citations/0",
 "citations": [{"type": "full_case", "span": [0, 8],
                "groups": {"volume": "1", "reporter": "U.S.", "page": "1"},
                "reporter_normalized": "U.S.", "year": null,
                "metadata": {"court": "scotus"}}]}
```

Or, on failure: `{"id": "...", "error": "message"}`.

Each citation is described by [`schema/citation.schema.json`](../schema/citation.schema.json):

| Field | Meaning |
|---|---|
| `type` | One of `full_case`, `short_case`, `supra`, `id`, `reference`, `full_law`, `full_journal`, `unknown`. |
| `span` | `[start, end)` over the input text in **Unicode code points**, not bytes or UTF-16 units. For `html` input it's measured against the engine's own cleaned text, so the scorer compares spans only for `plain` input. |
| `groups` | The citation's parts as found: `volume`, `reporter`, `page`, or for statutes `chapter`, `section` and so on. Leave out anything absent; never send null or a blank placeholder such as `___`. |
| `reporter_normalized` | The canonical reporter abbreviation, e.g. `U. S.` becomes `U.S.` (resource citations only). |
| `year` | Integer year, or null. |
| `metadata` | String values only. The bench scores `pin_cite`, `court`, `plaintiff`, `defendant`, `antecedent_guess`, `parenthetical`, `extra`, `year`, `month`, `day`, `publisher` and `volume`. Other keys are allowed and not scored. |

Citations come in document order.

## Running an adapter

```bash
uv run bench/run.py --adapter "path/to/your-adapter --flags" --vectors vectors/eyecite-2.7.8
```
