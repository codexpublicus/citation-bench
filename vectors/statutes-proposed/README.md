# Proposed statute vectors

Statute, court-rule, constitution, regulation and sentencing-guideline citations for the forms
[`vectors/statutes`](../statutes/README.md) covers thinly or not at all (#22): federal
court rules, state court rules besides Connecticut's Practice Book, the U.S. and state
constitutions, state administrative codes, `Treas. Reg.`, `U.S.S.G.`, `Fed. Reg.`, `Stat.`,
`Pub. L.`, `et seq.` and section ranges.

**None of these has been reviewed.** Each expected citation was written by hand from its
excerpt, not taken from an engine's output, and every vector has `provenance.status`
`proposed` (docs/protocol.md, "Vector provenance"). Until a vector is reviewed it is not a
reference: `bench/statutes.py` scores this set in a table of its own, and no baseline
gates it, so `bench:statutes` doesn't run it. A reviewed vector moves into
`vectors/statutes` (with its id renamed and its `provenance` dropped or set to
`verified`), and into the two baselines there if an engine misses it.

```bash
mise run report:statutes             # both engines, reference and proposed sets
```

## Conventions

No reporters-db entry or earlier vector settled these choices; the maintainer accepted
them on 2026-10-18 (docs/protocol.md, "Statute and court-rule citations"). The vectors
themselves still need review, one by one.

- Court rules: the rule number is the `rule` group (`Fed.R.Civ.P. 12(b)(6)`: rule `12`,
  pin cite `(b)(6)`), and `reporter_normalized` is the Bluebook abbreviation (`Fed. R.
  Civ. P.`, `Tex. R. App. P.`, `Mich. Ct. R.` for `MCR`).
- Constitutions: `article`, `amendment` and `section` groups, the article or amendment
  as written (`I`, `1`, `XIV`), and a clause as the pin cite (`cl. 3`). The span ends at
  the section, as a statute's does.
- `Fed. Reg.` normalizes to `Fed. Reg.`; reporters-db keys it `FR`, which both engines
  return.
- `U.S.C.A.` normalizes to `U.S.C.`, as reporters-db has it (a variation of `U.S.C.`).
- A range keeps both ends in `section` (`21 U.S.C. §§ 801-904`: section `801-904`), as
  both engines give it; a hyphenated section number looks the same (`§ 2000e-5`).
- `et seq.` is the pin cite, as in eyecite's own test vectors.
- `U.S.S.G.` is its own kind in `bench/statutes.py`, guideline, not a regulation.
- The span of `Pub.L. No. 93-233.` ends before the sentence's period; both engines take
  the period in.

## Vectors

Each is an excerpt of one opinion holding one citation, first taken from the
CourtListener ten-percent sample. Where the excerpt appears verbatim in the case
[stare.pub](https://stare.pub) serves for the same decision, `source` names that case
(see "Provenance" below); otherwise `source.offset` indexes the opinion's text after
the clean steps `html` and `inline_whitespace`, as citare's `clean` command produces it
(the convention `vectors/statutes` uses). What each engine returns: eyecite 2.7.8 and citare at
`787dedf` (0.6.0). "Right" means found at the expected place with the expected code and
parts; "bare `§`" means an unknown citation for the section sign and no law citation.

| Vector | Kind | Citation | Expected code; parts | eyecite | citare |
|---|---|---|---|---|---|
| `fed_r_civ_p/0` | court rule | `Fed.R.Civ.P. 52` | `Fed. R. Civ. P.`; rule `52` | none | none |
| `fed_r_civ_p/1` | court rule | `Fed.R.Civ.P. 12` | `Fed. R. Civ. P.`; rule `12` | none | none |
| `fed_r_civ_p/2` | court rule | `Fed. R. Civ. P. 60` | `Fed. R. Civ. P.`; rule `60` | none | none |
| `fed_r_evid/0` | court rule | `Fed.R.Evid. 801` | `Fed. R. Evid.`; rule `801` | none | none |
| `fed_r_evid/1` | court rule | `Fed. R. Evid. 801` | `Fed. R. Evid.`; rule `801` | none | none |
| `fed_r_crim_p/0` | court rule | `Fed.R.Crim.P. 8` | `Fed. R. Crim. P.`; rule `8` | none | none |
| `fed_r_crim_p/1` | court rule | `Fed.R.Crim.P. 33` | `Fed. R. Crim. P.`; rule `33` | none | none |
| `fed_r_app_p/0` | court rule | `Fed. R. App. P. 34` | `Fed. R. App. P.`; rule `34` | none | none |
| `fed_r_app_p/1` | court rule | `Fed. R. App. P. 4` | `Fed. R. App. P.`; rule `4` | none | none |
| `tex_r_p/0` | court rule | `Tex. R. Civ. P. 185` | `Tex. R. Civ. P.`; rule `185` | none | none |
| `tex_r_p/1` | court rule | `Tex. R. App. P. 25.2` | `Tex. R. App. P.`; rule `25.2` | none | none |
| `pa_r_civ_p/0` | court rule | `Pa. R.Civ.P. 1035.2` | `Pa. R. Civ. P.`; rule `1035.2` | none | none |
| `mich_ct_r/0` | court rule | `MCR 3.101` | `Mich. Ct. R.`; rule `3.101` | none | none |
| `us_const/0` | constitution | `U.S. Const. amend. VIII` | `U.S. Const.`; amendment `VIII` | none | none |
| `us_const/1` | constitution | `U.S. Const., amend. XIV` | `U.S. Const.`; amendment `XIV` | none | none |
| `us_const/2` | constitution | `U.S. Const. art. I, § 8` | `U.S. Const.`; article `I`, section `8` | bare `§` | bare `§` |
| `us_const/3` | constitution | `U.S. Const. Art. I, § 8` | `U.S. Const.`; article `I`, section `8` | bare `§` | bare `§` |
| `state_const/0` | constitution | `Ohio Const. art. I, § 11` | `Ohio Const.`; article `I`, section `11` | bare `§` | bare `§` |
| `state_const/1` | constitution | `Ind. Const. Art. 1 § 18` | `Ind. Const.`; article `1`, section `18` | bare `§` | bare `§` |
| `state_const/2` | constitution | `N.M.Const., Art. II, § 10` | `N.M. Const.`; article `II`, section `10` | bare `§` | bare `§` |
| `nycrr/0` | regulation | `22 NYCRR 806.9` | `N.Y. Comp. Codes R. & Regs.`; title `22`, section `806.9` | none | none |
| `njac/0` | regulation | `N.J.A.C. 10:129A-3.4` | `N.J. Admin. Code`; section `10:129A-3.4` | none | none |
| `treas_reg/0` | regulation | `Treas.Reg. § 1.170A-1` | `Treas. Reg.`; section `1.170A-1` | section `1` | right |
| `treas_reg/1` | regulation | `Treas.Reg. § 1.48-1` | `Treas. Reg.`; section `1.48-1` | right | right |
| `ussg/0` | guideline | `U.S.S.G. § 3B1.2` | `U.S.S.G.`; section `3B1.2` | bare `§` | bare `§` |
| `ussg/1` | guideline | `U.S.S.G. § 4B1.1` | `U.S.S.G.`; section `4B1.1` | bare `§` | bare `§` |
| `fed_reg/0` | regulation | `11 Fed. Reg. 5593` | `Fed. Reg.`; volume `11`, page `5593` | code `FR` | code `FR` |
| `fed_reg/1` | regulation | `50 Fed.Reg. 40,293` | `Fed. Reg.`; volume `50`, page `40,293` | code `FR` | code `FR` |
| `stat/0` | federal statute | `112 Stat. 3227` | `Stat.`; volume `112`, page `3227` | right | right |
| `stat/1` | federal statute | `88 Stat. 829` | `Stat.`; volume `88`, page `829` | right | right |
| `pub_l/0` | federal statute | `Pub.L. No. 93-233` | `Pub. L.`; title `93-233` | right, span takes the period | right, span takes the period |
| `pub_l/1` | federal statute | `Pub.L. 93-406` | `Pub. L.`; title `93-406` | right | right, span takes the space after |
| `usc_et_seq/0` | federal statute | `45 U.S.C.A. § 151` | `U.S.C.`; title `45`, section `151` | right | right |
| `usc_et_seq/1` | federal statute | `29 U.S.C.A. § 201` | `U.S.C.`; title `29`, section `201` | right | right |
| `usc_range/0` | federal statute | `21 U.S.C. §§ 801-904` | `U.S.C.`; title `21`, section `801-904` | right | right |
| `usc_range/1` | federal statute | `10 U.S.C. §§ 1201-1221` | `U.S.C.`; title `10`, section `1201-1221` | right | right |

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

Nine of the 36 point at a CAP case that way, each at a new offset, with
`courtlistener_opinion` keeping the CourtListener opinion id: `fed_r_evid/0`,
`njac/0`, `nycrr/0`, `pub_l/0`, `state_const/1`, `treas_reg/1`, `us_const/1`,
`usc_et_seq/0` and `usc_et_seq/1`. Two point at a CourtListener record stare.pub serves,
which `source` names with `source` `cl`, the record's `ref` (`<cluster>/<hash>`), its
`url` and the `sha256` of its JSON; stare.pub states each record's terms in its own
`license` (Public Domain Mark 1.0) and `attribution` (CourtListener, Free Law Project,
export 2026-09-30). `fed_r_crim_p/0` is on its own opinion's record. `usc_range/0`'s
opinion is in a cluster the 2026-09-30 export doesn't have; the opinion cites itself as
`2022 OK 30`, and the record at that citation, cluster 8242608, holds three copies of the
same opinion, each with the excerpt verbatim, so its offset is the occurrence nearest the
one it had. The other 25 stay on the CourtListener sample (`corpus`
`courtlistener-10pct`):

- stare.pub serves the decision from CAP, a different transcription (CAP's OCR text, with typographic quotes and its own misreadings) in which the excerpt doesn't appear verbatim; `source.stare_pub` names that case: `fed_r_app_p/0`, `fed_r_app_p/1`, `fed_r_civ_p/0`, `fed_r_civ_p/1`, `fed_r_crim_p/1`, `fed_reg/0`, `fed_reg/1`, `pa_r_civ_p/0`, `pub_l/1`, `stat/0`, `state_const/2`, `treas_reg/0`, `us_const/0`, `us_const/2`, `us_const/3`, `usc_range/1`, `ussg/0`, `ussg/1`.
- stare.pub's CourtListener record of the decision differs from the excerpt in spacing or whitespace; `source.stare_pub` names the record: `fed_r_evid/1`, `stat/1`.
- CourtListener lists no citation for the decision, so nothing in stare.pub's index leads to it: `state_const/0`, `tex_r_p/0`, `tex_r_p/1`.
- the opinion's cluster isn't in CourtListener's 2026-09-30 export, so no citation of it leads into stare.pub's index: `fed_r_civ_p/2`, `mich_ct_r/0`.

## Not covered yet

State constitutions beyond three, more state court rules (only Texas, Pennsylvania and
Michigan here), Idaho's and Indiana's shared `I.C. §`, Maryland's article abbreviations
(`CP § 8-301`), lists (`§§ 17a-101(b)(9) and 17a-101a`) and Id. chains into a statute.
