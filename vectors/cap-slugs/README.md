# CAP slug vectors

Case citations whose reporter name the Caselaw Access Project (CAP) files under more than one
series, each with the CAP slug the cited volume is filed under (`cap_slug`, docs/protocol.md):
`static.case.law/<cap_slug>/<volume>` is the book. An engine that maps citations to CAP gets
these wrong in ways that `groups` and `reporter_normalized` don't show, since every series here
is written with the same letters.

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

`source` names the corpus, the opinion and the character offset of the excerpt, as in
`vectors/statutes`:

- `courtlistener-10pct`: `opinion` is the CourtListener opinion id; `offset` indexes the text
  after the clean steps `html` and `inline_whitespace` that `tools/fetch_corpus.py` asks for.
- `cap`: `reporter`, `volume` and `case` name the CAP case file
  (`static.case.law/<reporter>/<volume>`, `json/<case>.json`); `offset` indexes
  `casebody.opinions[].text` joined with blank lines.
- `cap-metadata`: no opinion in either corpus cites the numbered `Mass. App. Div.` series, so
  its two inputs are written from the cited case's own CAP record: `name_abbreviation`, the
  official citation in `citations`, and the year of `decision_date`.
