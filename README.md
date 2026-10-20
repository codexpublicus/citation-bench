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

   A second set, `vectors/divergences/`, holds inputs where citare deliberately differs
   from eyecite, with citare's output as the expected answer and the evidence for it
   written up in citare's [`docs/divergences.md`](https://github.com/codexpublicus/citare/blob/main/docs/divergences.md).
   It is scored on its own (`bench:divergences`), so eyecite's score on its own vectors
   stays 100%, and `baselines/eyecite.known-differences` lists the divergence vectors
   eyecite is expected to miss.

   A third set, `vectors/statutes/`, holds statute and court-rule citations by
   jurisdiction and form, taken from real opinions with hand-checked answers
   ([README](vectors/statutes/README.md)). It is scored on its own too (`bench:statutes`),
   with the same two baselines. `bench/statutes.py` breaks it down by kind of law (federal
   statute, state statute, regulation, guideline, court rule, constitution), with precision, recall
   and F1 per engine (`mise run report:statutes`). `vectors/statutes-proposed/` holds
   unreviewed vectors for the forms the set lacks, scored apart and never as a reference
   ([README](vectors/statutes-proposed/README.md)).

   Every set records where its expected answers came from (`provenance` in
   `SOURCE.json`; [protocol](docs/protocol.md#vector-provenance)). Only human-checked
   vectors are a reference. eyecite's output isn't ground truth, and agreement between
   engines is reported as agreement, apart from the scores.

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
| `vectors/curated/` | Hand-curated vectors from real opinions, each checked against the opinion and the cited cases' records; no engine's output is the reference ([README](vectors/curated/README.md)) |
| `vectors/divergences/` | Inputs where citare deliberately differs from eyecite ([README](vectors/divergences/README.md)) |
| `vectors/statutes/` | Statute and court-rule citations by jurisdiction and form, from real opinions ([README](vectors/statutes/README.md)) |
| `vectors/statutes-proposed/` | Unreviewed statute, rule, constitution and regulation vectors for the forms `vectors/statutes` lacks ([README](vectors/statutes-proposed/README.md)) |
| `baselines/` | Known failures per engine: `citare.known-failures`, and `eyecite.known-differences` for the divergence and statute sets |
| `tools/export_eyecite.py` | Regenerates `vectors/eyecite-*` from an eyecite release's tests (`tools/_capture_<kind>.py`) |
| `corpora/` | Corpus manifests: URL, sha256, row count and provenance of each pinned file |
| `tools/fetch_corpus.py` | Downloads a pinned corpus into `.cache/corpora/`, verifies it, and converts it to find requests |
| `adapters/eyecite/` | Reference adapter for eyecite |
| `adapters/citare/` | Adapter for citare (Rust) |
| `bench/run.py` | Sends vectors to an adapter, scores the replies, prints a report; `--save` keeps the run |
| `bench/diff.py` | Compares two saved runs: citations gained, lost and changed per input |
| `bench/baseline.py` | Stores eyecite's runs in `baselines/eyecite/` by key, and restores them |
| `bench/report.py` | An engine's report: vector scores, statute metrics, corpus speed, diffs against eyecite and an earlier version |
| `bench/statutes.py` | Statute and court-rule metrics from saved runs: precision, recall and F1 per kind of law, field accuracy, agreement between engines |
| `baselines/` | citare's known failures, and the stored eyecite runs |
| `tests/` | Unit tests for the scorer, the diff and the corpus conversion (`mise run check`) |

## Usage

```bash
mise install
mise run bench:eyecite        # eyecite against its own vectors (should be 100%)
mise run bench:citare         # citare against the same vectors
mise run export:eyecite 2.7.8 # regenerate the vectors from an eyecite tag
mise run bench:divergences eyecite  # the divergence set; fails only outside its baseline
mise run bench:divergences citare
mise run bench:statutes eyecite     # the statute set, the same way
mise run bench:statutes citare
mise run report:statutes            # per-kind statute metrics for both engines, in reports/statutes/
mise run check                # lint and unit tests
mise run bench:curated eyecite      # the hand-curated set, the same way as the divergence set
mise run bench:curated citare
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

### Which citare gets benchmarked

`adapters/citare/Cargo.toml` names citare by its git URL on `main`, and the committed
`adapters/citare/Cargo.lock` pins the exact commit. That commit is what `bench:citare`
builds by default, and the adapter reports it in every run's `engine` field. To move it,
run `cargo update --manifest-path adapters/citare/Cargo.toml -p citare-core -p
citare-data-build`, check that `mise run bench:citare` still passes against
`baselines/citare.known-failures`, and commit the lock in its own PR. I don't put a `rev`
in `Cargo.toml`; the lock already pins the commit, and a second copy of it would only
drift.

`CITARE_PATH=../citare` builds a local checkout instead. `build:citare` patches every
citare crate with the checkout in a copy of the adapter under `target/`, so the
committed lock never changes, and it fails if cargo leaves any of those patches unused,
if the build compiled anything other than the checkout's `citare-core`, or if the
adapter reports a different version or commit. citare's own CI uses this path: it checks
out citation-bench at the commit in citare's `.github/citation-bench-ref` and runs
`bench:citare` with `CITARE_PATH` set to the citare commit under test, so the lock here
never decides what citare's CI scores.

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

### Stored eyecite runs

eyecite's answers to a fixed set of inputs only change when eyecite or the harness
changes, so its runs over the vectors and both corpora are committed in
`baselines/eyecite/` and reused while their key holds. A tier's key is a sha256 over
the eyecite version the adapter pins, the CI runner class the runs are timed on
(`RUNNER` in `bench/baseline.py`), and the bytes of the files that decide the run: the
eyecite adapter, `bench/run.py`, and either the vector set or the corpus manifest and
`tools/fetch_corpus.py`. `MANIFEST.json` lists each key's files and hashes beside
the run's headline numbers, so a refresh reads as a diff of that file in review; the
runs themselves are gzipped responses and timings, without the input text.

```bash
mise run baseline:check                        # fails if a stored run's key has changed
mise run baseline:eyecite                      # reruns eyecite on each stale tier and stores it
uv run bench/baseline.py restore corpus-1pct results/eyecite.json   # exit 3 on a key miss
```

CI's **Stored eyecite runs** job does the same as `baseline:eyecite` on a `homelab`
runner, the runner class citare's CI times itself on, and uploads the result as the
`eyecite-baseline` artifact to commit (`gh run download RUN_ID -n eyecite-baseline -D
DIR` wants an empty or new `DIR`). A weekly workflow opens an issue when PyPI has an
eyecite newer than the adapter's pin.

### Engine reports

`mise run report:citare --size 1` writes citare's report to `reports/citare/`: vector
scores per request kind, the known-failures ratchet, corpus speed, and the corpus diffs
against eyecite (from its stored run, or a live one on a key miss) and against an
earlier citare (`--previous DIR` with that run's `vectors.json` and
`corpus-<size>pct.json`), and the statute metrics from `report:statutes`. citare's CI
posts it on every PR and attaches it to every release.

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
