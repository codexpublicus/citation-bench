# CAP slug vectors

Case citations whose reporter name the Caselaw Access Project (CAP) files under more than one
series, each with the CAP slug the cited volume is filed under (`cap_slug`, docs/protocol.md):
`data.stare.pub/cap/<cap_slug>/<volume>.zip` is the book, as stare.pub serves it. An engine
that maps citations to CAP gets these wrong in ways that `groups` and `reporter_normalized`
don't show, since every series here is written with the same letters.

```bash
mise run bench:cap-slugs eyecite   # fails only on vectors not in baselines/eyecite.known-differences
mise run bench:cap-slugs citare    # fails only on vectors not in baselines/citare.known-failures
```

| Test | Inputs | What the volume is filed under |
|---|---|---|
| `ct_cl_federal` | 2 | `us-ct-cl`: the U.S. Court of Claims Reports (vols 1-231, 1853-1982), here written `C. Cls.` |
| `ct_cl_wv` | 3 | `wv-ct-cl`: West Virginia's Court of Claims reports (vols 1-28, 1941-2011), written `Ct. Cl.` like the federal ones |
| `ohio_neutral` | 2 | none: `2020-Ohio-1213` is a neutral citation, and CAP's `ohio` is the Ohio Reports, vols 1-20 |
| `ohio_reports` | 1 | `ohio`: the Ohio Reports |
| `mass_app_div_annual` | 2 | `mass-app-div-annual`: the Massachusetts Appellate Division's annual series, volume = year (1980-2015) |
| `mass_app_div_numbered` | 2 | `mass-app-div`: its numbered series, vols 1-15 (1936-1950) |

`ct_cl_wv/2` cites a 1977 decision. Both courts of claims sat in 1977, so the year doesn't say
which one a bare `11 Ct. Cl. 150 (1977)` is; the reporter does (the federal volume 11 is from
1875), and an engine that goes by the year alone picks wrong.

## What a vector expects

Each input is an excerpt holding one citation of the form under test (the federal one may
also carry a parallel cite). The expected citation gives `type`, `span` (plain text, so spans
are scored), `groups`, `reporter_normalized`, `metadata` and `year` as for any vector, and
`cap_slug` on the citation under test. Every field but `cap_slug` was read against its excerpt
by hand, and eyecite 2.7.8 agrees on all of them. `cap_slug` comes from CAP: the series whose
volumes and dates the citation's volume and year fall in (CAP's `ReportersMetadata.json` and
each series' `VolumesMetadata.json`), and for the CAP excerpts, the series the citing opinion
itself is filed under. `year` is left out for neutral and annual citations without a
parenthetical, whose year is their volume.

eyecite has no CAP data and leaves `cap_slug` out, so it passes only the two `ohio_neutral`
vectors, whose expected `cap_slug` is null.

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

No opinion in either corpus cites the numbered `Mass. App. Div.` series, so its two
inputs are written from the cited case's own CAP record, as stare.pub serves it:
`name_abbreviation`, the official citation in `citations`, and the year of
`decision_date` (`source.fields`); they have no `offset`.

Three vectors were first taken from the CourtListener ten-percent sample. `ohio_reports/0`'s
excerpt appears verbatim in the CAP case stare.pub serves for the same decision, at a new
offset; `courtlistener_opinion` keeps the opinion id. Two stay on the CourtListener sample
(`corpus` `courtlistener-10pct`, `opinion` the CourtListener opinion id, `offset` into
its text after the clean steps `html` and `inline_whitespace`):

- stare.pub's CourtListener record of the decision differs from the excerpt in spacing or whitespace; `source.stare_pub` names the record: `ohio_neutral/1`.
- not yet checked: CourtListener's API quota ran out before the decision's citations were looked up: `ohio_neutral/0`.
