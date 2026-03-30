# Requirements Traceability for Scriptless Testing (ReqTrace)

This repository contains the software prototype, documentation, evaluation assets, and thesis materials
for **Requirements Traceability for Scriptless Testing**.

The central software component is **ReqTrace**, a Python prototype for exploring requirements-to-evidence
traceability using executable requirements and TESTAR-generated evidence models.

## Repository structure

- [`src/reqtrace/`](src/reqtrace/) — the ReqTrace prototype
- [`tests/`](tests/) — automated tests
- [`docs/`](docs/) — project and architecture documentation
- [`suts/`](suts/) — systems under test and evaluation artifacts
- [`papers/`](papers/) — thesis and paper material

## Interfaces

ReqTrace currently provides two interfaces:

- **CLI** via `reqtrace`
- **UI** via `reqtrace ui`

## Setup

### Devcontainer

If you use the provided devcontainer, dependencies are installed automatically as part of the container
setup.

### Local installation

For a local Python environment:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

The quotes around `".[dev]"` avoid shell expansion issues in shells such as `zsh`.

## Current supported inputs

| Input kind | Currently supported format | Current execution input |
| --- | --- | --- |
| Requirements | Markdown | Requirement files. The CLI currently accepts one file, multiple files, or a directory of files. |
| Evidence | TESTAR model export JSON | One evidence model JSON file per run. |

## Usage

See the available commands and options:

```bash
reqtrace --help
reqtrace run --help
```

List the available traceability methods:

```bash
reqtrace methods
```

Run traceability for one requirement file:

```bash
reqtrace run \
  --requirements <path/to/requirement-file.md> \
  --requirements-format markdown \
  --evidence <path/to/model.json> \
  --evidence-format testar \
  --method heuristic
```

Run traceability for multiple requirement files:

```bash
reqtrace run \
  --requirements <path/to/requirement-a.md> \
  --requirements <path/to/requirement-b.md> \
  --requirements-format markdown \
  --evidence <path/to/model.json> \
  --evidence-format testar \
  --method heuristic
```

Run traceability for a directory of requirement files:

```bash
reqtrace run \
  --requirements <path/to/requirements-directory> \
  --requirements-format markdown \
  --evidence <path/to/model.json> \
  --evidence-format testar \
  --method heuristic
```

Show a saved result:

```bash
reqtrace show-result <path/to/result.json>
```

Launch the UI:

```bash
reqtrace ui
```

If `--output` is omitted, ReqTrace currently generates an output filename automatically. If `--output`
is provided, ReqTrace writes the result to that explicit path.

## Citation

If you use this repository or its artifacts, please cite the associated Master's thesis. See
[`CITATION.cff`](CITATION.cff) for citation details.

## License

MIT License — see [`LICENSE`](LICENSE).
