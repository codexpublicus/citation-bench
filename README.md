# citation-bench

An engine-neutral benchmark for legal citation extraction.

citation-bench asks any engine the same questions and scores how closely its answers match
the expected citations: type, volume, reporter, page, pin cite, parties, court and year.
The reference engine is [eyecite](https://github.com/freelawproject/eyecite).
[citare](https://github.com/codexpublicus/citare) is the first engine scored against it.
Engines join through a small stdin/stdout [adapter protocol](docs/protocol.md), so a closed
or commercial tool can be benchmarked without sharing any code.

## Tiers

1. **Conformance vectors** (`vectors/`): known inputs with expected outputs. The first set
   is exported from eyecite's own test suite, pinned to an eyecite release
   (`vectors/eyecite-<version>/`). An engine's score is the share of vectors it reproduces
   exactly, reported per request kind:
   - `find`: extract citations and their fields (`find.jsonl`)
   - `resolve`: group citations by the resource they refer to (`resolve.jsonl`)
   - `annotate`: wrap each citation in markers (`annotate.jsonl`)
2. **Corpus comparison**: run engines over real opinions and report where they agree, how
   fast they run, and which citations and fields differ. No hand-made answers needed. The
   corpus is the CourtListener sample eyecite benchmarks itself on (779 opinions, or 7,632
   with `--size 10`), pinned by sha256 in `corpora/` and prepared exactly as eyecite's
   `benchmark/benchmark.py` prepares it, so the numbers line up with eyecite's own. The
   Harvard CAP text that [stare.pub](https://stare.pub) serves is the next corpus.

## Layout

| Path | Contents |
|---|---|
| `docs/protocol.md` | The adapter protocol, and how citations are represented |
| `schema/` | JSON Schemas for vectors, requests, responses and citations |
| `vectors/` | Conformance vectors, one directory per source and version |
| `tools/export_eyecite.py` | Regenerates `vectors/eyecite-*` from an eyecite release's tests (`tools/_capture_<kind>.py`) |
| `corpora/` | Corpus manifests: URL, sha256, row count and provenance of each pinned file |
| `tools/fetch_corpus.py` | Downloads a pinned corpus into `.cache/corpora/`, verifies it, and converts it to find requests |
| `adapters/eyecite/` | Reference adapter for eyecite |
| `adapters/citare/` | Adapter for citare (Rust) |
| `bench/run.py` | Sends vectors to an adapter, scores the replies, prints a report; `--save` keeps the run |
| `bench/diff.py` | Compares two saved runs: citations gained, lost and changed per input |
| `tests/` | Unit tests for the scorer, the diff and the corpus conversion (`mise run check`) |

## Usage

```bash
mise install
mise run bench:eyecite        # eyecite against its own vectors (should be 100%)
mise run bench:citare         # citare against the same vectors
mise run export:eyecite 2.7.8 # regenerate the vectors from an eyecite tag
mise run check                # lint and unit tests
```

Compare two runs, of different engines or of two versions of one engine, on the same
inputs:

```bash
mise run bench:eyecite -- --save results/eyecite.json
mise run bench:citare -- --save results/citare.json
mise run diff results/eyecite.json results/citare.json                 # Markdown to stdout
mise run diff results/eyecite.json results/citare.json --out results/diff  # report.md + output.csv
```

The diff matches citations by type, volume, reporter and page (by span for id., supra and
references), lists the ones each run found alone, and the fields that changed on the ones
both found: spans, pin cite, parties, court, year, normalized reporter and so on. Inputs
without expected answers are run and saved but not scored, so the same works on a corpus.

### Corpus

```bash
mise run corpus:fetch               # download, verify and convert the 1% file (--size 10 for the larger one)
mise run corpus:run eyecite         # results/corpus-1pct/eyecite.json
mise run corpus:run citare          # results/corpus-1pct/citare.json (CITARE_PATH=../citare for a checkout)
mise run corpus:diff                # reports/corpus-1pct/report.md and output.csv
```

The corpus isn't committed: `corpus:fetch` downloads it into `.cache/` and refuses a file
whose sha256 doesn't match its manifest. Each opinion goes in as one `find` request, the
way eyecite's benchmark sends it: the first non-empty column of `xml_harvard`,
`html_lawbox`, `html_columbia`, `html_anon_2020` and `html` with any `<?xml ?>`
declaration removed, or else `plain_text`, all of it as `html` with the `html` and
`inline_whitespace` clean steps.

The report gives each engine's time per opinion and per KB of input, the median, the
slowest opinion and a cold start (process start to the reply to a one-citation probe,
reported apart from the per-opinion times). Then the agreement rate (citations found by
both over citations found by either, on opinions neither engine answered with an error),
the reporters and fields that differ most with an example of each, every opinion an
engine answered with an error, and a capped table of changes; `output.csv` lists them
all. Spans of `html` input index each engine's own cleaned text, so the report shows a
citation by finding its volume, reporter and page in the tag-stripped opinion. If an
adapter crashes, or takes longer than `--timeout` on one opinion, the bench records that
opinion and restarts the adapter for the rest.

Any other engine:

```bash
uv run bench/run.py --adapter "./my-adapter" --vectors vectors/eyecite-2.7.8 --show 5
```

## License

The code, schemas and protocol are licensed under the [PolyForm Shield License 1.0.0](LICENSE.md).
The vectors in `vectors/eyecite-*` keep their BSD 2-Clause license (see [NOTICE](NOTICE)).

## Data provenance

The vectors in `vectors/eyecite-*` come from eyecite's test suite, © Free Law Project,
under the BSD 2-Clause License. See [NOTICE](NOTICE).

The corpus files come from Free Law Project's CourtListener bulk data at
storage.courtlistener.com. They are downloaded at run time and not stored in this
repository; `corpora/*.json` records where each came from and its checksum.
