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
2. **Corpus comparison** (planned): run engines over real opinions, such as the Harvard CAP
   text that [stare.pub](https://stare.pub) serves, and report where they agree, how fast
   they run, and which spans differ. No hand-made answers needed.

## Layout

| Path | Contents |
|---|---|
| `docs/protocol.md` | The adapter protocol, and how citations are represented |
| `schema/` | JSON Schemas for vectors, requests, responses and citations |
| `vectors/` | Conformance vectors, one directory per source and version |
| `tools/export_eyecite.py` | Regenerates `vectors/eyecite-*` from an eyecite release's tests (`tools/_capture_<kind>.py`) |
| `adapters/eyecite/` | Reference adapter for eyecite |
| `adapters/citare/` | Adapter for citare (Rust) |
| `bench/run.py` | Sends vectors to an adapter, scores the replies, prints a report |

## Usage

```bash
mise install
mise run bench:eyecite        # eyecite against its own vectors (should be 100%)
mise run bench:citare         # citare against the same vectors
mise run export:eyecite 2.7.8 # regenerate the vectors from an eyecite tag
```

Any other engine:

```bash
uv run bench/run.py --adapter "./my-adapter" --vectors vectors/eyecite-2.7.8 --show 5
```

## Data provenance

The vectors in `vectors/eyecite-*` come from eyecite's test suite, © Free Law Project,
under the BSD 2-Clause License. See [NOTICE](NOTICE).
