# Curated vectors

Hand-made vectors whose expected answers a person read against the opinion they come from
and the cited cases' own records. No engine's output is the reference here, eyecite's
included: where a ruling or the source text and an engine disagree, the vector follows the
ruling and the text. The set records its provenance in `SOURCE.json` (`hand-checked`); the
maintainer verified seven of the eight in
[#45](https://github.com/codexpublicus/citation-bench/issues/45) (2026-10-25), and each of
those says so in its own `provenance` (`verified`). A vector that couldn't be checked in
full says so in its own `provenance` (`proposed`), with the reason.

```bash
mise run bench:curated eyecite   # fails only on vectors not in baselines/eyecite.known-differences
mise run bench:curated citare    # fails only on vectors not in baselines/citare.known-failures
```

The first vectors implement the owner's ruling D50 (2026-10-18): the two readings of
`<volume> Ohio <page>` from [citare#86](https://github.com/codexpublicus/citare/pull/86), and
the six vectors [#32](https://github.com/codexpublicus/citation-bench/issues/32) proposed from
[citare#84](https://github.com/codexpublicus/citare/pull/84).

| Vector | Provenance | What it checks | Source |
|---|---|---|---|
| `find/ohio_reports/0` | verified | `5 Ohio 187` is the Ohio Reports (reporter `Ohio`, normalized `Ohio`, `cap_slug` `ohio`): Putnam v. Valentine (Ohio 1831), CAP `ohio/5/cases/0170-01.json` | Lincoln County v. Fish, 38 Wash. 105 (1905), stare.pub CAP `wash/38/105` |
| `find/ohio_state_variation/0` | verified | `127 Ohio 545` is the Ohio State Reports, read through `Ohio` as an inferred abbreviation (variation) of `Ohio St.`: reporter `Ohio` as written, normalized `Ohio St.`, `cap_slug` `ohio-st`. Troop A Riding Academy v. Miller (1934), CAP `ohio-st/127/cases/0545-01.json` | stare.pub CAP `wis-2d/32/464` (CourtListener 1612618) |
| `find/nameless_parallel_run/0` | verified | #32 row 1 (Flaksa): the three certiorari citations share one full span and the year 1968, and take no case name | stare.pub CAP `so2d/585/842` (CourtListener 1706597) |
| `find/consecutive_runs_own_year/0` | verified | #32 row 2 (Elchibegoff): two nameless runs in a row, the first 1946 and the second 1947 | stare.pub CAP `f-supp/355/29` (CourtListener 1447928) |
| `find/runs_split_at_semicolon/0` | proposed | #32 row 3 (Pope): two runs split at the semicolon; only the second has a year, 1978 | stare.pub CAP `f2d/731/440` (CourtListener 433585) |
| `resolve/id_as_case_name/0` | verified | #32 row 4 (Murray): `Id., (1990), 52 Ohio St.3d 155` resolves with In re Murray: `[0, 1, 0, 0, 2]` | CourtListener [3759943](https://www.courtlistener.com/opinion/3759943/) |
| `resolve/id_as_case_name/1` | verified | #32 row 5 (Grain Cleaner): `Id., 34 Hun, 91` is the General Term's decision, apart from the Court of Appeals': `[0, 1, 2, 2]` | CourtListener [5509821](https://www.courtlistener.com/opinion/5509821/) |
| `resolve/id_as_case_name/2` | verified | #32 row 6 (First National Benefit Society): `Id., 9 Cir., 152 F.2d 298` is the second decision of that name: `[0, 1, 1, 2]` | stare.pub CAP `f2d/183/191` (CourtListener 225404) |

Each vector's `source.note` names the CAP record of every case it relies on, so the reading
can be checked again from the record.

## How each was checked

I took each excerpt from the opinion's text, as described under Provenance, and computed
every span from the excerpt rather than copying an engine's. Every cited volume and page was
looked up in CAP's `CasesMetadata.json` for that volume: the case name, the court and the
decision date gave the year of each run and which decision an id. citation names. `34 Hun
91` is Throop Grain Cleaner Co. v. Smith, 41 N.Y. Sup. Ct. 91 (General Term, 1884): CAP
files it as `ny-sup-ct/41/0091-01`, since Hun's volume 34 is the series' volume 41, and
CourtListener has it as [6262891](https://www.courtlistener.com/opinion/6262891/throop-grain-cleaner-co-v-smith/).

The check changed four things from what #32 quoted, which was citare's output on its own
copy of each input:

- Elchibegoff: the opinion has `cert. granted`, not `cert. denied`, so every span after it
  is one later.
- First National Benefit Society: the opinion's last citation is `Commissioner of Internal
  Revenue v. National Reserve Ins. Co., 9 Cir., 160 F.2d 956`, not `Commissioner v. National
  Reserve Ins. Co., 7 Cir., 129 F.2d 1`. The partition is the same.
- Flaksa and Pope: the first citation's `full_span` takes in its court parenthetical,
  `(5th Cir.)` and `(6th Cir.)`, as docs/protocol.md defines `full_span` (case name, pin cite
  and trailing parenthetical), and its `metadata.court` is `ca5` and `ca6`. #32 gave `[0, 60]`
  and no court, which is what both engines return: neither reads a court parenthetical that
  has no year.
- Murray and Grain Cleaner are the cleaned text verbatim: Murray keeps the opinion's spaces
  before commas, its line breaks and footnote 4's number before `Id.`; Grain Cleaner stops at
  `34 Hun, 91`, before `, 3 How. Frac. (N. S.) 290`, an OCR misreading of a Howard's Practice
  citation whose volume I couldn't confirm.

`runs_split_at_semicolon/0` stays `proposed`. Its second run cites two orders in each
reporter (`436 U.S. 929, 949`, `98 S.Ct. 2828, 2856`, `56 L.Ed.2d 774, 792`): page 949 is
twenty pages past a one-paragraph order denying certiorari, so it is a second order, not a
pin cite. The owner review in #45 confirmed it: 436 U.S. 949 is codefendant Williamson's
own denial of certiorari (CAP `us/436/0949-05`, 1978-06-05). The protocol has no way to say that, so `pin_cite` holds the second page as both
engines read it. The runs and their years are checked; the pin cites are not a reading I
can stand behind.

## What each engine gets wrong

eyecite 2.7.8, and citare at `929ecd1` (main with citare#84 and #86). citare passes 5 of the
8 and eyecite none. Every miss is in the baselines: eyecite's in
`baselines/eyecite.known-differences`, citare's in `baselines/citare.known-failures`, which
also lists four vectors the locked commit (`f68d227`, before citare#84) misses and main
passes, until the lock moves.

| Vector | eyecite | citare |
|---|---|---|
| `ohio_reports/0` | no `cap_slug` (eyecite has no CAP data) | right |
| `ohio_state_variation/0` | normalized `Ohio`, no `cap_slug` | defendant `Miller (1934)` and no year: the year between the name and the citation goes into the name |
| `nameless_parallel_run/0` | `88 S.Ct. 2287` and `20 L.Ed.2d 1387` start their full spans at themselves; the `(5th Cir.)` miss below | `389 F.2d 885`'s full span stops before `(5th Cir.)`, and no court |
| `consecutive_runs_own_year/0` | the second run gets 1946, the first run's year; full spans start at each citation | right |
| `runs_split_at_semicolon/0` | the second run gets no year; full spans start at each citation; the `(6th Cir.)` miss | `574 F.2d 320`'s full span stops before `(6th Cir.)`, and no court |
| `id_as_case_name/0` | names the second Ohio citation `Stanley v. Illinois` and puts it before the id. citation, so the citations don't line up (its partition is the same) | right |
| `id_as_case_name/1` | `[0, 1, 1, 2]`: the id. citation with the Court of Appeals' decision | right |
| `id_as_case_name/2` | `[0, 0, 1, 2]`: the id. citation with the first decision | right |

## What a vector expects

`find` vectors are plain text, so spans are scored. Each excerpt starts at the first
citation's case name. Both engines start a full span one word early when the sentence's
first words come before the name (`of Putnam v. Valentine`, `In Riding Academy v. Miller`);
these vectors don't test that.

Every field is what the excerpt says under the protocol's definitions. Two fields follow
eyecite's definitions, which the earlier sets use too: `metadata.court` is the court in a
parenthetical, or `scotus` for a reporter that is federal and has "Supreme" in its name
(`U.S.`, `S. Ct.`, not `L. Ed.`); `metadata.extra` is the text between a citation and its
parenthetical. A citation in a parallel run without a name of its own takes the run's full
span, from the run's first citation to its year, as citare#84 and #32 define it; in a run
with no year, each citation's full span runs from the run's start to its own end
(docs/protocol.md, Case citation conventions). `cap_slug`
is given only on the two Ohio citations.

`resolve` vectors score the citation types and the partition, nothing else
(docs/protocol.md). Their citations give `type`, and for full citations `span`, `groups`
and `reporter_normalized`, all checked. Their `metadata` is empty because it isn't scored
there and wasn't checked; read it as unspecified, not as "none". As in the other sets, each
parallel citation is its own resource, so `110 N. Y. 83` and `17 N. E. 671` are `0` and `1`.

## Provenance

The text comes from [stare.pub](https://stare.pub). `source` names the case there and the
character offset of the excerpt in it, as docs/protocol.md ("Vector sources") defines:
`corpus` `stare-pub`, `source` `cap`, the case's `slug`, `volume`, `page` and `case`, its
case page as `url`, and the volume zip and member that hold its JSON as `data` and
`member`; `offset` indexes `casebody.opinions[].text` joined with blank lines, and
`sha256` pins the JSON. stare.pub publishes the CAP case files under CC0 1.0, the terms
CAP published them under. `tools/fetch_stare.py check-vectors` checks every offset
against the text stare.pub serves. A case page (`https://stare.pub/c/<slug>/<volume>/<page>/`)
is the permanent address stare.pub gives each case; until case pages ship, `data` and
`member` are where the text is.

Five vectors were first taken from the CourtListener ten-percent sample. In four, the
excerpt appears verbatim in the CAP case stare.pub serves for the same decision, and they
point there now, at a new offset, with `courtlistener_opinion` keeping the opinion id.
One stays on the CourtListener sample (`corpus` `courtlistener-10pct`, `opinion` the
CourtListener opinion id, `offset` into its text after the clean steps `html` and
`inline_whitespace`, as citare's `clean` command produces it):

- CourtListener lists no citation for the decision, so nothing in stare.pub's index leads to it: `resolve/id_as_case_name/0`.

The set's provenance is in `SOURCE.json`; a vector's own `provenance` overrides it, as
[#28](https://github.com/codexpublicus/citation-bench/pull/28) defines the field.

## Adding a vector

Take the excerpt from the text stare.pub serves, as above, check every expected value against it and the
cited cases' records, and cite those records in `source.note`. Mark a vector `proposed`, with
the reason in its `provenance.note`, when any value can't be checked. Then run `mise run
bench:curated <engine> -- --update-known-failures` for each engine and say in the PR why
each new entry fails.
