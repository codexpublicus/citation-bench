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

and reads one the maintainer writes:

- `rulings.json`: the maintainer's answers to what no machine source settles, each under
  the decision it came from and that decision's basis (`owner-ruled 2026-10-25 (A63)`)

The sources themselves are cached under `.cache/statute-sources/` (gitignored, about
235 MB: U.S. Code metadata, California's 32 MB bulk-data prefix and the PDFs). A later run refuses a cached copy whose
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
| form | `G.S.` means `N.C. Gen. Stat.` | The written form is the code's own abbreviation; or the official page cites the section in that form (ncleg.gov writes `G.S. 163-122`); or the citing court sits in the code's jurisdiction (the case metadata stare.pub serves for the excerpt's case, or for the same decision when the excerpt is from the CourtListener sample; CourtListener's API, with a key, when stare.pub doesn't serve the decision) |
| existence | § 163-122 exists | The official source for the code holds the section, rule, article and section, clause, page or public law, and a year agrees with it |
| excerpt | stare.pub vectors | stare.pub serves the bytes the vector pins (`sha256`), and the input is the opinion's text at the recorded offset |

A vector is `verified-by-source:<sources>` when every claim passed, `contradicted:<what>`
when any failed, and `unverifiable:<claims>` when none failed and some had no machine
check. A verdict never changes a vector's provenance.

A vector's `source.corpus` has to be `stare-pub` or `courtlistener-10pct`
(docs/protocol.md, "Vector sources"), and a stare.pub source `cap` or `cl`; any other
stops the run with an error rather than skipping the excerpt and citing-court checks.
`tests/test_verify_statutes.py` checks that every statute vector in the repo gets them.
A CourtListener-sample excerpt has no excerpt check: its text is the sample's after clean
steps, and `tools/fetch_corpus.py` verifies the sample's files by sha256.

## Rulings

`rulings.json` holds the maintainer's answers, one per written form (`form`: `written`
means `code`), code (`code`: the standard abbreviation of `jurisdiction`'s code), span
pattern (`span`: text matching `pattern`, digits as `#`, belongs inside the span with no
field holding it, for the `codes` listed) or vector (`existence`: the section of `vector`
exists or existed as cited). A check a ruling answers passes, with the ruling's basis in
its detail and `owner-ruling-<decision>` as its source; a vector whose other claims all
passed is `verified-by-source`, the ruling among its sources. The form ruling is looked up
before CourtListener's API, so a ruled form spends no quota. An existence ruling replaces
a failed check only when it says `"overrides": "fail"`, as `vt_vsa/0`'s does (the section
was repealed after the events, which the current-code check can't know). An excerpt
ruling (`excerpt`: `vector`'s excerpt was corrected, and why) settles no check; it records
the basis for a vector whose text was changed by hand. Each ruling lists the vectors it
was made for; the test suite checks that they exist.

The maintainer reviewed the 48 vectors the 2026-10-18 run left open and answered them on
2026-10-25 (A63): every one is verified now but `conn_gen_stat/1`, whose `10 -236b` was
left open, and those 47 have `provenance.status` `verified`. The maintainer settled
`conn_gen_stat/1` the same day (D116): the space is in no original (the court's PDF and
CAP's text both print `§ 10-236b(f)`), so its excerpt was taken again from stare.pub's
CAP text and it is verified too.

The checks were tried against seventeen wrong vectors (a section, rule, page, public law,
clause or year that doesn't exist, one per source); all seventeen came out
`contradicted`.
The state sources added later (California through Texas's rules in the table below) are
checked the same way by fixture tests, each with a section or rule that isn't there.

Every state source is the code as in force now. A section that has since been repealed
or renumbered isn't in it, and the vector comes out `contradicted`; the report names
the source and the URL so a person can tell a wrong vector from an old citation.

## Keyed sources

Two sources need a key, and the script reads each from the environment only:

- `COURTLISTENER_API_TOKEN`: CourtListener's REST API v4, sent as
  `Authorization: Token ...`. For a CourtListener vector whose written form no other
  check settles, the script follows the opinion to its cluster, docket and court
  (`/opinions/<id>/`, `/clusters/<id>/`, `/dockets/<id>/`, `/courts/<id>/`, each with
  `fields=` so only the link it needs comes back). A state court whose name gives the
  code's state (`S`, `SA`, `ST`, `SS` courts), or a federal court for a federal code,
  settles the form, as CAP's case metadata does for CAP vectors. A court anywhere else
  is named in the form check and the form stays with a person. The token is limited to
  5 requests a minute, so requests are spaced 12 seconds apart.
- `NY_OPENLEG_API_KEY`: NY Open Legislation API v3
  (`legislation.nysenate.gov/api/3/laws/<law>/<section>?key=...`) for N.Y. Penal Law
  (`PEN`), Family Ct Act (`FCT`) and Judiciary Law (`JUD`) sections. A `SECTION`
  document at that location passes; HTTP 404 is a contradiction.

Both are age-encrypted in `.mise/config.toml` and decrypted only in the operator's
environment, so the run that writes this directory is
`MISE_EXPERIMENTAL=1 mise run verify:statutes`. With a key unset, as in CI, its checks
are recorded as `not-run`, the vector stays `unverifiable`, and the report lists the
checks not run; nothing fails. A key goes into the request only: the cache, the lock,
the verdicts, the report and error messages hold the URL without it. An HTTP 429 is
retried after the wait the server names (`Retry-After`, or CourtListener's "available
in N seconds"), or after 15, 30, 60 seconds and so on, six times at most. A wait over
two minutes (CourtListener's hourly quota asks for about 20) ends requests to that
host for the run: its uncached checks are recorded as `not-run`, and the next run
picks up from the cache. A 5xx answer is neither cached nor pinned.

## Sources

Access as found on 2026-10-18. None needs a key or an account except the two above. PDFs are read with pypdf (pinned in the script's inline metadata), and each PDF's text is kept in the cache next to it.

| Source | Publisher | What it checks | Form and access |
|---|---|---|---|
| U.S. Code, 2024 edition, package metadata (MODS) per title | GPO, GovInfo (`govinfo.gov/metadata/pkg/USCODE-2024-title<N>/mods.xml`) | U.S.C. sections and section ranges; the Federal Rules of Civil Procedure, Evidence and Appellate Procedure (title 28 appendix) and Criminal Procedure (title 18 appendix) | Static XML, 3 to 60 MB a title. OLRC's own download page (uscode.house.gov) answered with an "Under Maintenance" page |
| eCFR structure at 2026-10-01 | Office of the Federal Register (`ecfr.gov/api/versioner/v1/structure/<date>/title-<N>.json`) | C.F.R. and Treas. Reg. (26 C.F.R.) sections | JSON per title at a fixed date. The eCFR is OFR's continuously updated editorial compilation; the annual CFR on GovInfo is the official edition |
| Statutes at Large, package metadata per volume | GPO, GovInfo (`govinfo.gov/metadata/pkg/STATUTE-<vol>/mods.xml`) | `Stat.` volume and page (each law's page range), the law's date against a year; `Pub. L.` numbers (by Congress) | Static XML, 2 to 5 MB a volume |
| GovInfo link service | GPO (`govinfo.gov/link/fr/<vol>/<page>`) | `Fed. Reg.` volume and page resolve to an issue, whose date checks the year | A redirect; only its Location is kept |
| Guidelines Manual 2025, contents | U.S. Sentencing Commission (`ussc.gov/guidelines/2025-guidelines-manual`) | `U.S.S.G.` sections | One HTML page listing every section |
| The Constitution of the United States, H. Doc. 110-50 | GPO, GovInfo (`CDOC-110hdoc50`) | U.S. Const. articles, sections and amendments, and clause pin cites (GPO numbers the clauses) | One text page |
| reporters-db `laws.json` at `v3.2.67` | Free Law Project, maintained by hand on GitHub | The normalized code and its jurisdiction | JSON; the repository's license is BSD-2-Clause |
| Case files as stare.pub serves them | Caselaw Access Project case JSON in `data.stare.pub/cap/<slug>/<vol>.zip`, and CourtListener records at `data.stare.pub/cl/c/<cluster>/<hash>.json.gz` (`tools/fetch_stare.py` reads one zip member by HTTP range requests and caches it under `.cache/stare/`) | The excerpt and its offset; the citing court's jurisdiction (`jurisdiction.name_long`) | Static JSON; each case pinned by the sha256 in the vector and in `sources.json` under `<zip>#<member>` or the record's URL |
| Official state code pages | Arizona (azleg.gov), North Carolina (ncleg.gov), Maine (legislature.maine.gov), Texas Legislative Council (tcss.legis.texas.gov, chapter pages), Michigan (legislature.mi.gov), Rhode Island (rilegislature.gov), West Virginia (code.wvlegislature.gov), Wisconsin (docs.legis.wisconsin.gov), Massachusetts (malegislature.gov), Pennsylvania consolidated statutes (palegis.us) | That the section exists in the state's code | One HTML page per section (Texas: per chapter), addressed from the citation; the page has to hold the section's heading, and a 404 is a contradiction |
| California codes, leginfo bulk data (`pubinfo_2025.zip`) | California Legislative Counsel (`downloads.leginfo.legislature.ca.gov`) | Cal. Pen., Civ. Proc., Evid. and Civ. Code sections (active rows of `LAW_SECTION_TBL`) | A 1.2 GB zip of the session's data, rewritten weekly. The script fetches only its first 32 MB with an HTTP range request (`LAW_SECTION_TBL.dat` sits near the start) and pins that prefix under `<url>#bytes=0-33554431`. No key; the readme (`pubinfo_Readme.pdf`) documents the tables |
| Connecticut General Statutes | Connecticut General Assembly (`cga.ct.gov/current/pub/`) | Conn. Gen. Stat. sections | The title page gives each chapter's section range; the chapter page has to hold `Sec. <n>.`. The server sends its certificate without the GoDaddy intermediate, which is why it "didn't answer" before: the script fetches that intermediate from the URL the certificate names (`certificates.godaddy.com/repository/gdig2.crt`, pinned too) and verifies the chain as usual. robots.txt disallows only scripts and media directories |
| Connecticut Practice Book, 2026 | Connecticut Judicial Branch (`jud.ct.gov/Publications/PracticeBook/PB.pdf`) | Practice Book sections (`Sec. 63-8.` headings) | One 24 MB PDF |
| Hawaii Revised Statutes | Hawaii State Legislature's data host (`data.capitol.hawaii.gov/hrscurrent/`) | Haw. Rev. Stat. sections | A directory listing of volumes, then one HTML page per section. capitol.hawaii.gov answers scripts with HTTP 403; the data host answers, and its robots.txt allows every path except `.axd` handlers |
| Vermont Statutes | Vermont General Assembly (`legislature.vermont.gov/statutes/`) | V.S.A. sections | The title page lists chapters without section ranges, so the script bisects the chapters (sections are numbered in chapter order) and looks for the section in the chapter's list. robots.txt asks for 30 seconds between requests, and the script waits that long |
| North Dakota Century Code | Legislative Assembly (`ndlegis.gov/cencode/t<title>c<chapter>.pdf`) | N.D.C.C. sections | One PDF per chapter; a line starting with the section number |
| New Mexico Statutes, unannotated | New Mexico Compilation Commission, NMOneSource (`nmonesource.com/nmos/nmsa-unanno/`) | N.M. Stat. Ann. sections | The navigation pages map each chapter to a document; the document is a PDF of the chapter. NMCC describes NMOneSource as the official, free legal research service of the New Mexico courts and legislature |
| Constitution of New Mexico | NMCC, NMOneSource (`nmonesource.com/nmos/c/`) | N.M. Const. articles and sections | One 7 MB PDF with annotations; only bracketed section headings (`Sec. 10. [Searches and seizures.]`) count |
| Louisiana Revised Statutes | Louisiana Legislature (`legis.la.gov`) | La. Rev. Stat. sections | The Revised Statutes contents page opens a title by form post (ASP.NET postback, the site's own navigation); the title's list gives each section's document id, and the section page has to hold `§<n>.`. The post is pinned under `<url>#postback=TITLE <n>` |
| Code of Alabama 1975 | Alabama Legislature, ALISON (`alison.legislature.state.al.us/graphql`) | Ala. Code sections | The GraphQL endpoint ALISON's own pages query, read by GET with the query in the URL; no key |
| Constitution of the State of Indiana, as amended 2024 | Indiana General Assembly (`iga.in.gov/publications/indiana_constitution/`) | Ind. Const. articles and sections | One PDF |
| Texas Rules of Civil Procedure (2026-10-01) and Rules of Appellate Procedure (2026-02-06) | Supreme Court of Texas, `txcourts.gov/media/` | Tex. R. Civ. P. and Tex. R. App. P. rules | One PDF each; `RULE 185.`, `Rule 25.`, `25.2.` headings |
| NY Open Legislation API v3 | New York State Senate (`legislation.nysenate.gov/api/3/laws/`) | N.Y. Penal Law, Family Ct Act and Judiciary Law sections | JSON per section; needs `NY_OPENLEG_API_KEY` (free) |
| CourtListener REST API v4 | Free Law Project (`courtlistener.com/api/rest/v4/`) | The court that cited the statute in a CourtListener excerpt, for the form | JSON per opinion, cluster, docket and court; needs `COURTLISTENER_API_TOKEN` (free account), 5 requests a minute |

The verifier doesn't use CAP's `cites_to` or CourtListener's `html_with_citations`:
both are software output (eyecite or its predecessor), not labels.

## Not wired in

Sources for the remaining codes, as found on 2026-10-18 (`NO_SOURCE` in the script):

- Online only through a commercial publisher: Georgia, Tennessee and Arkansas codes
  (LexisNexis), N.J.A.C. (LexisNexis), NYCRR (Thomson Reuters Westlaw)
- Refused scripted requests: constitution.congress.gov (HTTP 403; GPO's text is used
  instead). nysenate.gov's pages answer HTTP 403 too; New York statutes come from the
  Open Legislation API with a key (above)
- robots.txt disallows every path to every crawler (`User-agent: *` / `Disallow: /`),
  so the script doesn't fetch them:
  - Oklahoma: oscn.net (allows only `/rss/` and `/recaptcha/`) and oklegislature.gov
    (whose title downloads are the other official copy)
  - Ohio Constitution: codes.ohio.gov. legislature.ohio.gov allows crawlers but
    links to codes.ohio.gov for the text
  - Michigan Court Rules: courts.michigan.gov
  - Pennsylvania Rules of Civil Procedure: pacodeandbulletin.gov (231 Pa. Code)
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
