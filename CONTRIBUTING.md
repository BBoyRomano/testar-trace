# Contributing

Thanks for contributing to ReqTrace.

This repository supports a thesis prototype, so changes should prioritize clarity, reproducibility, and stable boundaries.

## Setup

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Or use the provided devcontainer.

## Before opening a PR

Run quality checks locally:

```bash
ruff check .
pytest -q
```

Optional but recommended local hook check:

```bash
pre-commit run --all-files
```

If you touched runtime/data contracts, also run:

```bash
pytest --cov=reqtrace --cov-report=term-missing
```

## Scope and architecture rules

- keep layers separated (`ingestion`, `domain`, `application`, `infrastructure`, `presentation`)
- keep parsing logic in ingestion, not in application/presentation
- keep persistence/serialization adapters in infrastructure
- keep domain models source-agnostic
- avoid large refactors mixed with unrelated changes

## Tests

- add or update tests for every behavior change
- keep automated tests generic and SUT-agnostic by default
- use `tests/fixtures/` for reusable format fixtures
- use real `suts/` bundles for manual/evaluation workflows, not core automated correctness

See [`tests/README.md`](tests/README.md) for test strategy.

## Data and artifacts

- follow `suts/README.md` structure and retention policy
- avoid committing heavy binaries/raw output unless explicitly required
- prefer manifests/instructions for large external artifacts

## Documentation

Update docs when behavior or architecture changes:

- `README.md`
- `docs/README.md` (if doc structure/navigation changed)
- `docs/architecture/*`
- `docs/roadmap.md` (if status changed)

Keep README placement lean:

- use root/docs/tests/suts-level README files
- avoid adding deep nested README files unless a folder has independent lifecycle/rules
