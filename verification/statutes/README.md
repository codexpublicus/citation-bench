# Statute vectors checked against official sources

`bench/verify_statutes.py` (`mise run verify:statutes`) splits each statute vector's
expected citation into the claims it makes and checks every claim it can against a
human-maintained, official source. eyecite's and citare's output play no part. The run
writes three files here:

- `report.md`: counts, the contradicted vectors, and what still needs a person, grouped
  so one answer covers every vector it applies to
- `verdicts.json`: every vector's verdict and each check behind it
- `sources.json`: every source the run read, with its URL, retrieval date, size and
  SHA-256

The sources themselves are cached under `.cache/statute-sources/` (gitignored, about
150 MB, nearly all of it U.S. Code metadata). A later run refuses a cached copy whose
hash differs from `sources.json`; a source that changed upstream is used as it is now,
repinned, and listed in the report. `--offline` uses the cache only. CI doesn't run the
verifier; `tests/test_verify_statutes.py` tests it on small fixtures with no network.

## Claims and how each is checked

| Claim | Example (`G.S. § 163-122`) | Machine check |
|---|---|---|
| span | `[4, 18)` covers `G.S. § 163-122` | Starts and ends on a word boundary, holds every part as written, ends at the section (rule, page, amendment), as docs/protocol.md has it |
| span, judgment | `Ala. Code 1975, § 12-2-7` | Text in the span that no field holds (`1975,`) and whitespace inside a number (`10 -236b`) go to a person, grouped by pattern |
| metadata as written | pin cite `(a)` | The pin cite follows the span; the year, parenthetical and publisher are in the text after it |
| code | `N.C. Gen. Stat.`, North Carolina | reporters-db's laws data has the code for that jurisdiction (its `$law_subject` patterns cover `N.Y. Penal Law`, `Cal. Pen. Code`, `Tex. Penal Code Ann.`), or the 2026-10-18 conventions name it |
| form | `G.S.` means `N.C. Gen. Stat.` | The written form is the code's own abbreviation; or the official page cites the section in that form (ncleg.gov writes `G.S. 163-122`); or, for a CAP excerpt, the citing court sits in the code's jurisdiction (CAP case metadata) |
| existence | § 163-122 exists | The official source for the code holds the section, rule, article and section, clause, page or public law, and a year agrees with it |
| excerpt | CAP vectors | The input is the opinion's text at the recorded offset |

A vector is `verified-by-source:<sources>` when every claim passed, `contradicted:<what>`
when any failed, and `unverifiable:<claims>` when none failed and some had no machine
check. A verdict never changes a vector's provenance.

The checks were tried against seventeen wrong vectors (a section, rule, page, public law,
clause or year that doesn't exist, one per source); all seventeen came out
`contradicted`.

## Sources

Access as found on 2026-10-18. None needs a key or an account.

| Source | Publisher | What it checks | Form and access |
|---|---|---|---|
| U.S. Code, 2024 edition, package metadata (MODS) per title | GPO, GovInfo (`govinfo.gov/metadata/pkg/USCODE-2024-title<N>/mods.xml`) | U.S.C. sections and section ranges; the Federal Rules of Civil Procedure, Evidence and Appellate Procedure (title 28 appendix) and Criminal Procedure (title 18 appendix) | Static XML, 3 to 60 MB a title. OLRC's own download page (uscode.house.gov) answered with an "Under Maintenance" page |
| eCFR structure at 2026-10-01 | Office of the Federal Register (`ecfr.gov/api/versioner/v1/structure/<date>/title-<N>.json`) | C.F.R. and Treas. Reg. (26 C.F.R.) sections | JSON per title at a fixed date. The eCFR is OFR's continuously updated editorial compilation; the annual CFR on GovInfo is the official edition |
| Statutes at Large, package metadata per volume | GPO, GovInfo (`govinfo.gov/metadata/pkg/STATUTE-<vol>/mods.xml`) | `Stat.` volume and page (each law's page range), the law's date against a year; `Pub. L.` numbers (by Congress) | Static XML, 2 to 5 MB a volume |
| GovInfo link service | GPO (`govinfo.gov/link/fr/<vol>/<page>`) | `Fed. Reg.` volume and page resolve to an issue, whose date checks the year | A redirect; only its Location is kept |
| Guidelines Manual 2025, contents | U.S. Sentencing Commission (`ussc.gov/guidelines/2025-guidelines-manual`) | `U.S.S.G.` sections | One HTML page listing every section |
| The Constitution of the United States, H. Doc. 110-50 | GPO, GovInfo (`CDOC-110hdoc50`) | U.S. Const. articles, sections and amendments, and clause pin cites (GPO numbers the clauses) | One text page |
| reporters-db `laws.json` at `v3.2.67` | Free Law Project, maintained by hand on GitHub | The normalized code and its jurisdiction | JSON; the repository's license is BSD-2-Clause |
| Case files | Caselaw Access Project (`static.case.law/<reporter>/<vol>/cases/<case>.json`) | The excerpt and its offset; the citing court's jurisdiction | Static JSON |
| Official state code pages | Arizona (azleg.gov), North Carolina (ncleg.gov), Maine (legislature.maine.gov), Texas Legislative Council (tcss.legis.texas.gov, chapter pages), Michigan (legislature.mi.gov), Rhode Island (rilegislature.gov), West Virginia (code.wvlegislature.gov), Wisconsin (docs.legis.wisconsin.gov), Massachusetts (malegislature.gov), Pennsylvania consolidated statutes (palegis.us) | That the section exists in the state's code | One HTML page per section (Texas: per chapter), addressed from the citation; the page has to hold the section's heading, and a 404 is a contradiction |

The verifier doesn't use CAP's `cites_to` or CourtListener's `html_with_citations`:
both are software output (eyecite or its predecessor), not labels.

## Not wired in

Sources for the remaining codes, as found on 2026-10-18 (`NO_SOURCE` in the script):

- Online only through a commercial publisher: Georgia, Tennessee and Arkansas codes
  (LexisNexis), N.J.A.C. (LexisNexis), NYCRR (Thomson Reuters Westlaw)
- Refused scripted requests: California (leginfo.legislature.ca.gov, HTTP 403; its bulk
  `pubinfo` archive is the alternative), New York statutes (nysenate.gov, HTTP 403; the
  Open Legislation API needs a free key), Hawaii (capitol.hawaii.gov, HTTP 403),
  constitution.congress.gov (HTTP 403; GPO's text is used instead)
- No answer: cga.ct.gov (Connecticut) didn't answer from here
- Need a lookup the script doesn't do yet: Vermont (paths need the chapter), North Dakota
  (chapter PDFs), Oklahoma (OSCN document ids), New Mexico (nmonesource.com document ids),
  Louisiana (legis.la.gov document ids), Alabama and Ohio's constitution (sections render
  client-side), Practice Book, Texas, Michigan and Pennsylvania court rules (PDFs or
  pages that load the text by script)
- No official per-section source: Purdon's (`P.S.`) title and section numbers

## Independent human-labelled corpora

None found for statute citations in U.S. opinions. What exists, and why it doesn't serve
as ground truth here:

- CAP `cites_to` covers statutes (`laws:leg_statute` and so on) but is software output in
  reporters-db's and eyecite's structure; no CAP document says how it was built.
- CourtListener's `html_with_citations` is generated by eyecite. Whether `html_lawbox` and
  `html_columbia` carry publisher-made statute links is unchecked (the API needs a token).
- LePaRD and CLERC are built from CAP's citation data and eyecite, cover cases only, and
  had only small after-the-fact human samples.
- The Supreme Court Database hand-codes the provision a case turned on (`lawType`,
  `lawSupp`, `lawMinor`), with no spans: usable only as a document-level recall check on
  Supreme Court opinions.
- The German LER corpus and InLegalNER (India) are human-annotated with statute classes,
  but not U.S. law.
- OLRC's Table III and OFR's Parallel Table of Authorities are maintained by hand and
  could check resolution and normalization, not extraction.
