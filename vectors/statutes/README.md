# Statute vectors

Statute and court-rule citations as state and federal courts write them, one or two real
inputs per jurisdiction and form, each with a hand-checked expected citation (#22). The set
starts with the forms citare's state-code work measured as the most common misses: in the
CourtListener ten-percent sample and a CAP sample, statutes that came through as bare `§`
unknown citations because neither engine knew the code's name (`General Statutes § 52-557n`,
`OCGA § 16-9-93`, `42 Pa.C.S. § 5322`, `Penal Law § 160.05`). The measurement is written up
in citare's [`docs/laws-local.md`](https://github.com/codexpublicus/citare/blob/main/docs/laws-local.md).

```bash
mise run bench:statutes eyecite   # fails only on vectors not in baselines/eyecite.known-differences
mise run bench:statutes citare    # fails only on vectors not in baselines/citare.known-failures
```

## What a vector expects

Each input is an excerpt of one opinion holding exactly one citation, and the expected
citation gives:

- `type`: `full_law`
- `span`, in code points (the excerpts are plain text, so spans are scored)
- `groups`: the parts as written: `reporter` (`General Statutes`, `OCGA`, `Pa.C.S.`), `section`,
  and `title`, `chapter` or `subject` where the form has one
- `reporter_normalized`: the code's standard abbreviation whatever the spelling (`Conn. Gen.
  Stat.` for `General Statutes`), keeping the subject of a code cited by subject (`N.Y. Penal
  Law`, `Cal. Civ. Proc. Code`, `Tex. Penal Code Ann.`)
- `metadata`: pin cite, parenthetical and year as for any citation, and `jurisdiction`
  (`Connecticut`, `United States`), the jurisdiction reporters-db's laws data gives the code

`bench/run.py` doesn't score `metadata.jurisdiction`: it scores a fixed list of metadata
keys, and adding one changes the key of every stored eyecite run (`baselines/eyecite/`).
`bench/statutes.py` scores it instead, with precision, recall and F1 per kind of law
(`mise run report:statutes`). `full_span` is left out, so the spans a pin cite or
parenthetical adds aren't scored.

## How the inputs were chosen and checked

From every statute citation citare finds (with the state-code forms) in the two corpora, the
candidates for a form were the occurrences in a sentence of at most 260 characters that holds
no other citation and cites a single section (no `§§`). Two were drawn per form at random
(seeded), from different opinions, preferring ones where no spaced or bracketed subsection
follows the section. Every expected citation was then read against its sentence and fixed
where it was wrong; three were:

| Vector | citare's answer | Expected |
|---|---|---|
| `conn_general_statutes_revision/1` | `§ 53a-102 (a)`: parenthetical `a` | pin cite `(a)` |
| `ariz_ars/1` | `§ 12-2101(B), (C), and (F)(1) (2003)`: pin cite `(B)`, no year | pin cite `(B), (C), and (F)(1)`, year 2003 |
| `conn_gen_stat/1` | `§ 10 -236b(f)` (a space from the source): section `10` | section `10 -236b`, pin cite `(f)` |

Those three stay in `baselines/citare.known-failures` after the state-code forms land. The
rest of the set is there too until citation-bench's locked citare commit has them.

## Provenance

The set's `SOURCE.json` gives every vector here the provenance `hand-checked`: the
expected citations were drafted from citare's output and read by hand against their
sentences, as described above, and the maintainer has not yet verified them
(docs/protocol.md, "Vector provenance"). `bench/statutes.py` treats them as the reference
until then.

`source` names the corpus, the opinion and the character offset of the excerpt:

- `courtlistener-10pct`: `opinion` is the CourtListener opinion id; `offset` indexes the text
  after the clean steps `html` and `inline_whitespace` that `tools/fetch_corpus.py` asks for,
  as citare's `clean` command produces it.
- `cap`: `reporter`, `volume` and `case` name the CAP case file
  (`static.case.law/<reporter>/<volume>`, `json/<case>.json`); `offset` indexes
  `casebody.opinions[].text` joined with blank lines, or the one opinion `opinion` names.

## Coverage

What each engine gets right, per form (eyecite 2.7.8; citare with the state-code forms).
"No law citation" means the engine returns the `§` as an unknown citation, or nothing.

| Jurisdiction | Form | Code | eyecite | citare | eyecite's miss |
|---|---|---|---|---|---|
| Connecticut | `General Statutes § 53a-21` | Conn. Gen. Stat. | 0/2 | 2/2 | no law citation |
| Connecticut | `General Statutes (Rev. to 1997) § 17a-101` | Conn. Gen. Stat. | 0/2 | 1/2 | no law citation |
| Connecticut | `Practice Book § 63-8` (court rules) | Conn. Practice Book | 0/2 | 2/2 | no law citation |
| Connecticut | `Conn. Gen. Stat. § 52-577` | Conn. Gen. Stat. | 1/2 | 1/2 | section cut at a space |
| Georgia | `OCGA § 40-6-392`, `O.C.G.A. § 13-11-1` | Ga. Code Ann. | 0/4 | 4/4 | no law citation |
| Arizona | `A.R.S. § 32-1451` | Ariz. Rev. Stat. | 0/2 | 1/2 | no law citation |
| Hawaii | `HRS § 291E-21` | Haw. Rev. Stat. | 0/2 | 2/2 | no law citation |
| North Carolina | `N.C.G.S. § 15A-544.5`, `G.S. § 163-122` | N.C. Gen. Stat. | 0/4 | 4/4 | no law citation |
| North Dakota | `N.D.C.C. § 23-06-03` | N.D. Cent. Code | 0/2 | 2/2 | no law citation |
| Tennessee | `T.C.A. § 37-1-304` | Tenn. Code Ann. | 0/2 | 2/2 | no law citation |
| Pennsylvania | `58 Pa.C.S. § 3202`, `75 Pa.C.S.A. § 1543` | Pa. Cons. Stat. | 0/4 | 4/4 | no law citation |
| Pennsylvania | `26 P.S. § 1-705` | Pa. Stat. Ann. | 0/2 | 2/2 | no law citation |
| Maine | `1 M.R.S. § 402`, `11 M.R.S.A. § 1-203` | Me. Rev. Stat. Ann. | 0/4 | 4/4 | no law citation |
| Vermont | `24 V.S.A. § 4407` | Vt. Stat. Ann. | 0/2 | 2/2 | no law citation |
| Oklahoma | `84 O.S. 2001 § 176` | Okla. Stat. | 0/2 | 2/2 | no law citation |
| New York | `Penal Law § 180.05`, `Judiciary Law § 468-a` | N.Y. Penal Law, N.Y. Judiciary Law | 0/3 | 3/3 | no law citation |
| New York | `Family Ct Act § 352.2` | N.Y. Family Ct Act | 0/2 | 2/2 | no law citation |
| California | `Pen. Code, § 1385`, `Evid. Code, § 1250` | Cal. Pen. Code, Cal. Evid. Code | 0/4 | 4/4 | no law citation |
| California | `Code Civ. Proc., § 325` | Cal. Civ. Proc. Code | 0/2 | 2/2 | no law citation |
| California | `Cal. Civ. Code § 1770` | Cal. Civ. Code | 0/1 | 1/1 | normalized to `Cal. Code` |
| Texas | `TEX. PENAL CODE § 1.07`, `Tex. Fam.Code § 54.02` | Tex. Penal Code Ann., Tex. Fam. Code Ann. | 0/4 | 4/4 | no law citation |
| Texas | `Tex. Penal Code Ann. § 36.06` | Tex. Penal Code Ann. | 0/2 | 2/2 | normalized to `Tex. Code Ann.` |
| Massachusetts | `G. L. c. 184, § 15`, `Mass. Gen. Laws ch. 260 § 2A` | Mass. Gen. Laws | 0/3 | 3/3 | no law citation |
| New Mexico | `NMSA 1978, § 32A-I-29` | N.M. Stat. Ann. | 0/2 | 2/2 | no law citation |
| Michigan | `M.C.L.A. § 257.520` | Mich. Comp. Laws | 0/2 | 2/2 | no law citation |
| Alabama | `Ala. Code 1975, § 12-2-7` | Ala. Code | 0/2 | 2/2 | no law citation |
| Arkansas | `A.C.A. § 4-9-203` | Ark. Code Ann. | 0/2 | 2/2 | no law citation |
| Louisiana | `La.Rev.Stat. § 13:841.3` | La. Stat. Ann. | 0/2 | 2/2 | no law citation |
| Rhode Island | `G.L. 1956, § 24-10-1` | R.I. Gen. Laws | 0/2 | 2/2 | no law citation |
| West Virginia | `West Virginia Code § 31-1-15` | W. Va. Code | 0/2 | 2/2 | no law citation |
| Wisconsin | `WIS. STAT. § 706.09` | Wis. Stat. | 0/1 | 1/1 | no law citation |
| United States | `25 U.S.C. § 1912`, `40 C.F.R. § 261.4` | U.S.C., C.F.R. | 4/4 | 4/4 | |

The `N.Y. Gen. Bus. Law § 394-ccc` split (citare#49) is in `vectors/divergences/`
(`law_section/4`); neither corpus has a single-citation sentence with that code.

## Not covered yet

[`vectors/statutes-proposed`](../statutes-proposed/README.md) has unreviewed vectors for
federal and state court rules, constitutions, state administrative codes, `Treas. Reg.`,
`U.S.S.G.`, `Fed. Reg.`, `Stat.`, `Pub. L.`, `et seq.` and section ranges; they join this
set once reviewed. Still missing from #22's list: Idaho's and Indiana's shared `I.C. §`,
Maryland's article abbreviations (`CP § 8-301`), lists (`§§ 17a-101(b)(9) and 17a-101a`)
and Id. chains into a statute.
