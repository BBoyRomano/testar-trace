# Tests

The automated test suite mirrors the main prototype layers:

- `tests/domain/` – domain-model invariants and boundary conditions
- `tests/ingestion/` – source loading, normalization, validation, and mapping
- `tests/application/` – orchestration and traceability-method behavior
- `tests/presentation/` – CLI, GUI, and presentation-runtime behavior

## Ground rules

- Keep tests generic and independent of a specific SUT.
- Prefer unit tests for pure behavior and contracts; reserve integration tests for parser/adapter/runtime boundaries.
- Avoid over-engineering test setup. Reuse fixtures only when duplication is real and repeated.
- Use real SUT bundles under `suts/` for manual evaluation and thesis experiments, not as the primary automated correctness contract.

## What we test

- Domain invariants and validation errors.
- Ingestion loader/adapter behavior for supported formats and malformed input.
- Application service contracts, method selection, cancellation, and result persistence.
- Presentation command/runtime behavior and output contracts.
- End-to-end integration of ingestion + mapping + execution for representative paths.

## What we intentionally avoid

- Asserting implementation details that do not affect behavior.
- Mirroring third-party library internals in our tests.
- UI pixel/layout assertions for current GUI views.
- Heavy autouse fixture chains that hide test setup.

## Structure and ordering

- Use regular test functions by default.
- Use classes only for lightweight grouping when it improves readability (no `__init__` and no `unittest.TestCase` inheritance).
- Keep tests in Arrange / Act / Assert order with descriptive names.
- Prefer deterministic assertions and bounded waits over unbounded sleeps.

## Fixtures and `conftest.py`

- Shared fixture factories live in `tests/conftest.py`.
- Application-unit snapshot fixtures live in `tests/application/unit/conftest.py`.
- Do not import from `conftest.py`; request fixtures by name.
- Keep fixtures explicit in function signatures; avoid broad autouse unless unavoidable.

## Decorators and markers

- `@pytest.mark.parametrize` for behavior matrices and alias/normalization checks.
- `@pytest.mark.integration` for integration tests touching I/O or multiple components.
- `@pytest.mark.skipif` only for real platform/runtime constraints.
- `@pytest.mark.xfail` only for known defects with a tracked reason; strict mode is enabled globally.

## Running the suite

Run the full suite from the repository root:

```bash
uv run pytest
```

Run only unit tests:

```bash
uv run pytest -m "not integration"
```

Run only integration tests:

```bash
uv run pytest -m integration
```

If your environment is not already using an editable install, install first:

```bash
python -m pip install uv
uv sync --group dev --locked
```
