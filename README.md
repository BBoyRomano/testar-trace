# Requirements Traceability for Scriptless Testing (ReqTrace)

ReqTrace is a Python-first traceability toolkit for linking requirement artifacts to scriptless GUI-testing evidence (with initial focus on TESTAR evidence exports).

## Package model

This repository is split into reusable Python packages and runnable interface apps:

- `reqtrace` (core library, distributed independently)
- `reqtrace-adapters` (file-format and external-source adapters)
- `reqtrace-cli` (CLI app)
- `reqtrace-api` (HTTP API app)
- `reqtrace-web` (Vite+ frontend app)

The core package contains canonical models, traceability methods, registries, and analysis orchestration. Input formats and external integrations live outside the core package.

## Current scope

- requirements adapter input formats: Markdown, JSON, and Gherkin feature files
- evidence adapters for TESTAR evidence exports
- traceability methods: `noop` and `sequence`
- JSON import/export of traceability results
- API-backed browser workflow for loading, analysis, and result inspection
- web dashboard under `apps/web/`

## Repository structure

- [`packages/reqtrace/`](packages/reqtrace/) - core Python library package
- [`packages/reqtrace-adapters/`](packages/reqtrace-adapters/) - adapter package for files, formats, and external sources
- [`apps/cli/`](apps/cli/) - CLI package (`reqtrace-cli`)
- [`apps/api/`](apps/api/) - API package (`reqtrace-api`)
- [`apps/web/`](apps/web/) - frontend app (`reqtrace-web`)
- [`packages/_archive/`](packages/_archive/) - archived legacy package code, kept temporarily
- [`docs/`](docs/) - architecture and planning docs

## Setup

### Python workspace setup

```bash
python -m pip install --upgrade pip
python -m pip install uv
uv sync --group dev --locked
```

### Interface install options

Install only what you need:

```bash
pip install reqtrace
pip install reqtrace-cli
pip install reqtrace-api
```

### Web setup

```bash
cd apps/web
vp install
```

## Quality checks

```bash
uv run ruff check .
uv run ty check
uv run pytest -q
```

Web checks:

```bash
cd apps/web
vp check
vp build
```

## Usage

Core package is import-first.

Preferred stable import path:

```python
from reqtrace import analyze_traceability
from reqtrace_adapters import load_evidence, load_requirements
```

Advanced/internal modules remain available but are not the primary compatibility surface.

CLI:

```bash
reqtrace --help
reqtrace methods
reqtrace analyze --help
```

API:

```bash
reqtrace-api
```

## Documentation map

- [`docs/README.md`](docs/README.md)
- [`docs/architecture/00-overview.md`](docs/architecture/00-overview.md)

## License

MIT. See [`LICENSE`](LICENSE).


