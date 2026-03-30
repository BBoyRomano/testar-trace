# Tests

The automated test suite mirrors the main prototype layers:

- `tests/domain/` – domain-model invariants and boundary conditions
- `tests/ingestion/` – source loading, normalization, validation, and mapping
- `tests/application/` – orchestration and traceability-method behavior
- `tests/presentation/` – CLI, GUI, and presentation-runtime behavior

## Test design rules

- Keep automated tests **generic** and independent of a specific SUT.
- Use small helper/builders only where they reduce repetition without hiding the supported input formats.
- Use realistic file fixtures for ingestion and file-based integration tests.
- Use real SUT bundles under `suts/` for manual evaluation and thesis experiments, not as the primary automated correctness contract.

## Running the suite

Run the full suite from the repository root:

```bash
pytest
```

If your environment is not already using an editable install, install first:

```bash
python -m pip install -e .[dev]
```
