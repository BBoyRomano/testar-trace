# Tests

The test suite mirrors the main repository layers:

- `tests/domain/` – domain-model invariants and boundary conditions
- `tests/ingestion/` – source loading, normalization, validation, and mapping
- `tests/application/` – runtime orchestration and baseline method behavior
- `tests/presentation/` – CLI, GUI, and presentation-runtime behavior

Use small helper/builders only where they reduce repetition without hiding the supported input formats.
Use realistic file fixtures for integration-style tests.

Run the full suite from the repository root:

```bash
pytest
```

For local development, install the package in editable mode before running the suite if your environment does not already do so:

```bash
python -m pip install -e .[dev]
```
