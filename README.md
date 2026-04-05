# Requirements Traceability for Scriptless Testing (ReqTrace)

ReqTrace is a Python thesis prototype for establishing requirements traceability between requirement artifacts and scriptless GUI-testing evidence, with an initial focus on TESTAR state-model exports.

This repository contains source code, tests, architecture docs, SUT bundles, and thesis materials.

## Current implemented scope

ReqTrace currently supports:

- requirements ingestion from `markdown` and `json`
- requirements input as one file, many files, or directory input
- evidence ingestion for `testar` (state-model JSON and run-bundle style inputs)
- baseline traceability execution (`baseline`) as the default production method
- CLI and local GUI execution
- JSON import/export of traceability results
- persisted GUI run history at `.reqtrace/gui-history/`
- asynchronous multi-run execution via application-level run executor

## Method status

- `baseline`: enabled by default in CLI/GUI and used as the stable control path
- `candidate_match`: lexical retrieval comparator (step-level evidence matching)
- `flow_match`: ordered flow alignment method (path-aware matching)
- `hybrid_match`: primary ensemble candidate (combines `flow_match` + `candidate_match`)

## Repository structure

- [`src/reqtrace/`](src/reqtrace/) — source code
- [`tests/`](tests/) — automated tests
- [`docs/`](docs/) — architecture and planning docs (see [`docs/README.md`](docs/README.md))
- [`packaging/`](packaging/) — executable/distribution build assets
- [`suts/`](suts/) — per-SUT reproducibility bundles
- [`papers/`](papers/) — thesis/proposal materials (Overleaf Git sync)
- [`docs/archived-v0/`](docs/archived-v0/) — archived legacy material (non-authoritative)

## Setup

### Devcontainer

Use the provided devcontainer (`Python 3.14`) for a ready-to-run environment.

### Local setup

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Quality checks

```bash
ruff check .
pytest -q
```

Optional local hook runner:

```bash
pre-commit run --all-files
```

Optional coverage report:

```bash
pytest --cov=reqtrace --cov-report=term-missing
```

## CLI usage

Show help:

```bash
reqtrace --help
reqtrace run --help
```

List enabled methods in the default CLI wiring:

```bash
reqtrace methods
```

Run with one requirements file:

```bash
reqtrace run \
  --requirements <path/to/requirements.md> \
  --requirements-format markdown \
  --evidence <path/to/testar-model.json> \
  --evidence-format testar \
  --method baseline
```

Run with multiple requirement paths:

```bash
reqtrace run \
  --requirements <path/to/req-a.md> \
  --requirements <path/to/req-b.md> \
  --requirements-format markdown \
  --evidence <path/to/testar-model.json> \
  --evidence-format testar \
  --method baseline
```

Run with a directory of JSON requirements:

```bash
reqtrace run \
  --requirements <path/to/requirements-json-dir> \
  --requirements-format json \
  --evidence <path/to/testar-model.json> \
  --evidence-format testar \
  --method baseline
```

Render a saved result:

```bash
reqtrace show-result <path/to/result.json>
```

Launch GUI:

```bash
reqtrace ui
```

Enable debug logging and persist logs to a rotating file:

```bash
reqtrace -vv --log-file .reqtrace/logs/reqtrace.log run \
  --requirements <path/to/requirements.md> \
  --evidence <path/to/testar-model.json>
```

Normal logging levels:

- default: warnings/errors only
- `-v`: run-level progress (`INFO`)
- `-vv`: deep troubleshooting (`DEBUG`)
- `--log-level <LEVEL>`: explicit override

Notes:

- If `--output` is omitted, results are rendered only.
- If `--output` is set, the result JSON is also written to disk.
- `--log-file` is optional. Without it, logs are written to the terminal stream only.

GUI logging can be configured via environment variables:

```bash
REQTRACE_LOG_LEVEL=DEBUG REQTRACE_LOG_FILE=.reqtrace/logs/gui.log reqtrace ui
```

## Executable distribution (Windows)

For users who should run ReqTrace without cloning this repository, build standalone
executables with PyInstaller.

Local build commands (Windows):

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev,packaging]"
pyinstaller packaging/pyinstaller/reqtrace-cli.spec
pyinstaller packaging/pyinstaller/reqtrace-gui.spec
```

Outputs:

- `dist/reqtrace/reqtrace.exe`
- `dist/reqtrace-gui/reqtrace-gui.exe`

You can also run the manual GitHub Actions workflow
`Build Executables` to generate downloadable Windows artifacts.

## SUT data strategy

Data is organized per system-under-test under `suts/<sut-name>/`.

Each bundle can contain:

- requirements datasets (`canonical`, `execution`, `source`, `variants`)
- TESTAR protocols and evidence bundles
- curated evaluation outputs
- optional local export area for ad-hoc runs

See [`suts/README.md`](suts/README.md) for the authoritative structure policy.

## Documentation map

- Documentation index: [`docs/README.md`](docs/README.md)
- Roadmap: [`docs/roadmap.md`](docs/roadmap.md)
- Test strategy: [`tests/README.md`](tests/README.md)
- Contribution guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)

## README policy

To avoid documentation bloat, README files are intentionally limited to these levels:

- root `README.md`: setup, usage, and repository entry point
- `docs/README.md`: design/planning map
- `tests/README.md`: test strategy
- `suts/README.md` + `suts/<sut>/README.md`: SUT data policy and per-SUT specifics

## Reproducibility notes

- Automated tests are intentionally SUT-agnostic.
- Real evaluation bundles and pinned experiment outputs live under `suts/`.
- Overleaf-synced thesis/proposal material lives under `papers/`.

## Citation

If you use this repository or its artifacts, cite the associated thesis.
See [`CITATION.cff`](CITATION.cff).

## License

MIT License — see [`LICENSE`](LICENSE).
