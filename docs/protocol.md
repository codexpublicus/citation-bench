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
  carries on. A crash or a missing line fails every request still outstanding in that
  process. The bench records the request the adapter was on (the first unanswered one)
  as crashed, starts a fresh adapter, and sends it the rest.

Setup work such as loading data or compiling patterns belongs before the first request.
The bench's first request is always a probe, a `find` of `1 U.S. 1` with the id
`citation-bench/probe`; answer it like any other. The time from process start to the
probe's reply is reported as the cold start, and each later request is timed from the
reply before it, so setup counts toward the cold start and not toward any input.

## Version

This is protocol version **2**. Each request carries `"protocol": 2`. Version 1 had no
`protocol` or `kind` field and only knew `find`; a request without `kind` still means
`find`, so a version 1 adapter keeps working on find vectors and answers the other kinds
with an `error`, or with something the scorer marks wrong.

## Request

```json
{"protocol": 2, "kind": "find",
 "id": "eyecite-2.7.8/find/test_find_citations/0",
 "input": {"text": "1 U.S. 1", "format": "plain", "clean_steps": []},
 "options": {"remove_ambiguous": false}}
```

| Field | Meaning |
|---|---|
| `protocol` | Protocol version the bench speaks, currently `2`. |
| `kind` | `find` (default), `resolve` or `annotate`. See [Kinds](#kinds). |
| `id` | Opaque. Echo it back unchanged. |
| `input.text` | The document. |
| `input.format` | `plain` or `html`. If it's `html`, the engine gets the markup and does its own conversion to text. |
| `input.clean_steps` | eyecite cleaning steps (`html`, `inline_whitespace`, `all_whitespace`, `underscores`, `xml`), applied to the text before extraction in either format. Engines that don't model these may ignore them. |
| `options.remove_ambiguous` | Drop citations whose reporter can't be pinned to a single edition. |
| `options.annotate` | `annotate` requests only; see below. |

## Kinds

Every kind starts the same way: find the citations in `input`, as for `find`. The kind
decides what the engine then does with them, and what it sends back.

### find

```json
{"id": "eyecite-2.7.8/find/test_find_citations/0",
 "citations": [{"type": "full_case", "span": [0, 8], "full_span": [0, 8],
                "groups": {"volume": "1", "reporter": "U.S.", "page": "1"},
                "reporter_normalized": "U.S.", "year": null,
                "metadata": {"court": "scotus"}}]}
```

`citations` lists every citation found, in document order (see [Citations](#citations)).

### resolve

Group the citations by the resource they refer to: a full citation starts a resource,
and short forms, `supra`, `Id.` and references point back to one, or to none.

```json
{"id": "eyecite-2.7.8/resolve/test_supra_resolution/0",
 "citations": [{"type": "full_case", ...}, {"type": "supra", ...}],
 "resolution": [0, 0]}
```

`resolution` has one entry per citation, in the same order: the index of its resource
group, or `null` if it resolves to nothing. Only the partition counts: the scorer
renumbers groups by first appearance, so `[1, 1, 0]` and `[0, 0, 1]` are the same answer.
A resolve vector passes if the citation types line up with the expected ones and the
partitions match. Field-level accuracy is the find vectors' job.

### annotate

Wrap each citation in markers and return the annotated document.

```json
{"protocol": 2, "kind": "annotate", "id": "eyecite-2.7.8/annotate/test_annotate/6",
 "input": {"text": "1 U.S. 1. Foo. Id. Bar. Id. at 2.", "format": "plain", "clean_steps": []},
 "options": {"annotate": {"before": "<{i}>", "after": "</{i}>", "unbalanced_tags": "unchecked"}}}
```

```json
{"id": "eyecite-2.7.8/annotate/test_annotate/6",
 "text": "<0>1 U.S. 1</0>. Foo. <1>Id.</1> Bar. <2>Id. at 2</2>."}
```

| Option | Meaning |
|---|---|
| `before`, `after` | Marker templates. `{i}` stands for the citation's index in document order, counting from 0; a template without `{i}` is used as is. |
| `unbalanced_tags` | What to do when a citation's span would cut across HTML tags in the original text. `unchecked`: insert the markers anyway. `skip`: widen the span over adjacent style tags (`<i>`, `<em>`, ...) if that balances it, otherwise leave the citation unannotated. `wrap`: close and reopen the markers around each tag inside the span. These follow eyecite's `annotate_citations`. |

The markers go around each citation's `span` (not its `full_span`). The returned text is
`input.text` itself with markers inserted, not the cleaned text: if clean steps or markup
conversion changed the text, the engine maps each span back onto the original. When
spans overlap, a later one is clipped to start where the earlier one ended, and dropped
if nothing is left. The scorer compares the returned text exactly.

## Errors

On failure, answer `{"id": "...", "error": "message"}`. That includes a `kind` the engine
doesn't support.

## Citations

Each citation is described by [`schema/citation.schema.json`](../schema/citation.schema.json):

| Field | Meaning |
|---|---|
| `type` | One of `full_case`, `short_case`, `supra`, `id`, `reference`, `full_law`, `full_journal`, `unknown`. |
| `span` | `[start, end)` over the input text in **Unicode code points**, not bytes or UTF-16 units: the citation proper, e.g. `1 U.S. 1`. For `html` input it's measured against the engine's own cleaned text, so the scorer compares spans only for `plain` input. |
| `full_span` | Same units: the whole citation, including case name, pin cite and trailing parenthetical, e.g. `Foo v. Bar, 1 U.S. 1, 2 (1999)`. Optional; equal to `span` if the engine has nothing more. |
| `groups` | The citation's parts as found: `volume`, `reporter`, `page`, or for statutes `chapter`, `section` and so on. Leave out anything absent; never send null or a blank placeholder such as `___`. |
| `reporter_normalized` | The canonical reporter abbreviation, e.g. `U. S.` becomes `U.S.` (resource citations only). |
| `year` | Integer year, or null. |
| `metadata` | String values only. The bench scores `pin_cite`, `court`, `plaintiff`, `defendant`, `antecedent_guess`, `parenthetical`, `extra`, `year`, `month`, `day`, `publisher` and `volume`. Other keys are allowed and not scored. |

Citations come in document order. Expected citations leave out `span` and `full_span`
when their source has no trustworthy offsets (eyecite's factory-built test citations);
the scorer only checks the fields an expected citation has.

## Running an adapter

```bash
uv run bench/run.py --adapter "path/to/your-adapter --flags" --vectors vectors/eyecite-2.7.8
```
