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

The probe's reply may also say what the adapter runs, which the bench prints and keeps
in a saved run's metadata, so a report names the build it measured:

```json
{"id": "citation-bench/probe", "citations": [...],
 "engine": {"name": "citare", "version": "0.4.1", "commit": "b48f3359f8a2..."}}
```

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
| `cap_slug` | Case citations, optional: the [Caselaw Access Project](https://case.law)'s slug for the reporter series the cited volume is in, so that `data.stare.pub/cap/<cap_slug>/<volume>.zip` is that volume as [stare.pub](https://stare.pub) serves it (the same slug as CAP's own `static.case.law/<cap_slug>/<volume>`); null when CAP has no such series. `2019-Ohio-1234` is null (CAP's `ohio` is the Ohio Reports, volumes 1 to 20), `100 Ct. Cl. 123` from the federal Court of Claims is `us-ct-cl`. An engine without CAP data leaves it out. Scored only where an expected citation has it. |
| `metadata` | String values only. The bench scores `pin_cite`, `court`, `plaintiff`, `defendant`, `antecedent_guess`, `parenthetical`, `extra`, `year`, `month`, `day`, `publisher` and `volume`. Other keys are allowed and not scored. For a `full_law` citation, `jurisdiction` names the jurisdiction whose law it is (`Connecticut`, `United States`); `bench/run.py` doesn't score it, and `bench/statutes.py` reports it per field. |

Citations come in document order. Expected citations leave out `span` and `full_span`
when their source has no trustworthy offsets (eyecite's factory-built test citations);
the scorer only checks the fields an expected citation has.

## Case citation conventions

The maintainer accepted these conventions on 2026-10-25, in the review of the case vectors
([#45](https://github.com/codexpublicus/citation-bench/issues/45)), for the readings the
field definitions above leave open:

- **A parallel run's full span.** When a run of parallel citations ends in a year
  parenthetical, every citation in it has the whole run as its `full_span`, from the run's
  start (its case name, or its first citation when it has no name) to the parenthetical's
  end: `392 U.S. 928, 88 S.Ct. 2287, 20 L.Ed.2d 1387 (1968)`. When the run has no closing
  year, each citation's `full_span` runs from the run's start to that citation's own end:
  in `Riding Academy v. Miller (1934), 127 Ohio 545, 189 N. E. 647,` the first citation's
  full span ends after `545` and the second's after `647`.
- **The year as printed.** `year` is the year the input prints for the citation, not the
  cited decision's date: `11 Ct. Cl. 150 (1977)` has year 1977 although CAP dates the
  decision 1976-07-19, and a citation printed without a year has none, even when the
  decision's year is known. The decision date is in the cited case's record.
- **`Id.` before a full citation.** An `Id.` followed directly by a full citation (`Id.,
  9 Cir., 152 F.2d 298`) is an `id` citation of its own, and a `resolve` vector groups it
  with the full citation that follows it, not with the authority cited before it.
- **Inputs written from case metadata.** An input written from a case's own record rather
  than taken from an opinion (`source.fields`, under Vector sources) can be verified like
  any other vector, but it is not ground truth for a dataset of citations found in opinion
  text: its `provenance` has `ground_truth: false` (Vector provenance).

A second first page printed like a pin cite (`436 U.S. 929, 949`, where 949 is another
order) has no reading in this protocol yet; the vector that has one stays `proposed` until
it does.

## Statute and court-rule citations

A statute, regulation, court rule or constitution is a `full_law` citation. Its parts are
groups, named as reporters-db's laws data names them where it has the code: `reporter`
(as written), `section`, `title`, `chapter` and `subject`, `volume` and `page` for a
session law or register (`88 Stat. 829`), `title` for a public law number (`Pub. L. No.
93-233`). `reporter_normalized` names the code whatever the spelling (`Conn. Gen. Stat.`
for `General Statutes`), and `metadata.jurisdiction` its jurisdiction.

`reporter_normalized` is an identifier, not a style choice (owner ruling D114,
2026-10-25). It is reporters-db's key where reporters-db's laws data has one for the
code (`Ga. Code Ann.`, `La. Stat. Ann.`), or the code matches one of its patterns
(`N.Y. Penal Law`, `Cal. Civ. Proc. Code`); otherwise it is the form the jurisdiction's
own courts use (`N.Y. Family Ct Act`, `Conn. Practice Book`). Every code the vectors
name has an entry in [`data/law-codes.json`](../data/law-codes.json) with its
jurisdiction, its Bluebook form as an alias, and reporters-db's key as an alias where the
identifier differs from it (`Pa. Stat. Ann.` keeps its name, with `Pa. Stat. and Cons.
Stat. Ann.` and the Bluebook's `Pa. Stat. Ann. tit. N, § x (West)` recorded), so a tool
can show or match either. Each Bluebook alias says where it comes from: most are from
memory of the Bluebook's tables, not checked against the book, and say so (`source`
`memory`); `confirmed_by` names a public source where one confirms the pattern.
`tests/test_law_codes.py` fails when a vector names a code with no entry. `Pa. Stat.
Ann.` keeps its name by ruling (A63). `Fed. Reg.`, from the 2026-10-18 conventions, is
the one code whose identifier the rule would make reporters-db's `FR`; it stays `Fed.
Reg.` by ruling (D116, 2026-10-25), with `FR` recorded as its reporters-db alias.

The maintainer accepted these conventions on 2026-10-18 for the forms reporters-db
doesn't settle:

- A court rule's number is the `rule` group (`Fed.R.Civ.P. 12(b)(6)`: rule `12`, pin
  cite `(b)(6)`), and `reporter_normalized` is the Bluebook abbreviation (`Fed. R. Civ.
  P.`, `Mich. Ct. R.` for `MCR`).
- A constitution has `article`, `amendment` and `section` groups (`U.S. Const. art. I, §
  8`), each as written, with a clause as the pin cite (`cl. 3`).
- `Fed. Reg.` normalizes to `Fed. Reg.` as written, not reporters-db's `FR` (kept by
  ruling D116; `FR` is its alias in `data/law-codes.json`).
- `U.S.C.A.` normalizes to `U.S.C.`.
- A range stays whole in `section` (`21 U.S.C. §§ 801-904`: section `801-904`).
- `et seq.` is the pin cite.
- The U.S. Sentencing Guidelines (`U.S.S.G.`) are their own kind of law, a guideline, not
  a regulation.

`vectors/statutes-proposed` follows them. Its vectors are still `proposed` until each is
reviewed: settling the conventions doesn't make the answers checked.

`bench/statutes.py` scores law citations per kind of law (federal statute, state
statute, regulation, guideline, court rule, constitution): precision, recall and F1 for
finding them at the right place, and for getting the code and every part right. See its
docstring.

## Vector provenance

A vector's `provenance.status` says where its expected answer came from, and so whether
it can serve as a reference:

| Status | Meaning | Reference? |
|---|---|---|
| `verified` | Reviewed by the maintainer against the input | yes |
| `hand-checked` | Read by hand against the input when it was added; not yet verified | yes, until verified or corrected |
| `proposed` | Drafted and waiting for review | no |
| `engine-output` | Copied from an engine's output (`engine` names it) | no |
| `engine-tests` | Exported from an engine's own test suite (`engine` names it) | no |

A vector without `provenance` takes its set's, from the `provenance` in the set's
`SOURCE.json`; a set without one is unrecorded. `bench/statutes.py` scores only `verified`
and `hand-checked` vectors as the reference and reports every other status in a table of
its own. An engine's output is never ground truth, the reference engine's included:
agreement between two engines is reported as agreement, apart from the scores.

`provenance.ground_truth: false` marks a vector that is checked and scored as its status
says but is not ground truth for a dataset of citations found in opinion text, such as
stare-builder's tier 0, because its input wasn't taken from an opinion. The two
`cap-slugs` `mass_app_div_numbered` vectors have it: no opinion in either corpus cites
that series, so their inputs are written from the cited cases' CAP records. Without the
field, the status alone decides.

`bench/verify_statutes.py` (`mise run verify:statutes`) checks the statute vectors' parts
against official sources (the U.S. Code, eCFR, the Statutes at Large, the Federal Register,
the Guidelines Manual, GPO's Constitution and state legislatures' code pages) and lists
what still needs a person ([`verification/statutes/`](../verification/statutes/README.md)).
Its verdicts don't change a vector's provenance.

## Vector sources

A vector's `source` says where its input text came from, so it can be checked again. The
opinion text is [stare.pub](https://stare.pub)'s, and `source.corpus` is `stare-pub`:

| `source.source` | Fields | The text `offset` indexes |
|---|---|---|
| `cap` | `slug`, `volume`, `page`, `case`; `url` the case page (`https://stare.pub/c/<slug>/<volume>/<page>/`), `data` the volume zip on `data.stare.pub/cap/` and `member` the case's JSON in it | `casebody.opinions[].text` joined with blank lines, or the one opinion `opinion` names |
| `cl` | `ref` (`<cluster>/<hash>`); `url` the record, `https://data.stare.pub/cl/c/<cluster>/<hash>.json.gz` | the same, from the record |

`sha256` is the hash of the case's JSON as stare.pub serves it (gunzipped, for a
CourtListener record), and `courtlistener_opinion` the CourtListener opinion id an
excerpt was first taken from, when it was. An input written from a case's metadata
rather than its text has `fields` in place of `offset`. The case page is the permanent
address stare.pub gives every case; until case pages ship, `data` and `member` are where
a CAP case's text is. `uv run tools/fetch_stare.py check-vectors` checks every vector
taken from stare.pub against the text stare.pub serves: the case's sha256 and the input
at its offset.

stare.pub names the terms of each source in the files themselves: CAP's case files are
CC0 1.0, the terms CAP published them under, and each CourtListener record carries the
Public Domain Mark 1.0 that CourtListener puts on its bulk data (`license`) and credits
CourtListener (Free Law Project) and the export it came from (`attribution`).

A vector whose excerpt doesn't appear verbatim in any case stare.pub serves keeps the
source it was made from:
`courtlistener-10pct`, an opinion of eyecite's comparison sample (`opinion` is the
CourtListener opinion id, `offset` indexes its text after the clean steps `html` and
`inline_whitespace`). Its set's README says why, and `stare_pub` names the same decision
on stare.pub where stare.pub has it.

## Running an adapter

```bash
uv run bench/run.py --adapter "path/to/your-adapter --flags" --vectors vectors/eyecite-2.7.8
```
