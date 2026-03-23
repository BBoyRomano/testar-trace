# ReqTrace

Repository accompanying the Master's thesis **Requirements Traceability for Scriptless GUI Testing**.

ReqTrace is a thesis prototype for analyzing whether requirements appear to have been exercised in TESTAR-generated GUI state models and for reporting evidence-based coverage results.

## Repository layout

- `src/` contains the ReqTrace prototype
- `tests/` contains automated tests and test fixtures
- `suts/` contains system-under-test assets, requirements, protocols, and run outputs
- `docs/` contains project documentation
- `papers/` contains proposal, thesis, bibliography, and figures

## Run

```bash
reqtrace analyze tests/fixtures/canonical/case_001_found/state.json tests/fixtures/canonical/case_001_found/requirements.json
```

## Select analyzer

```bash
reqtrace analyze tests/fixtures/state_models/testar_v1_minimal.json tests/fixtures/canonical/case_001_found/requirements.json --analyzer keyword_v1
```

```bash
reqtrace analyze suts/tbuis/testing/testar/runs/2026-03-22-webdriver-tbuis-public/model.json suts/tbuis/requirements/use-cases.json --analyzer evidence_v1
```

## Export JSON

```bash
reqtrace analyze tests/fixtures/canonical/case_001_found/state.json tests/fixtures/canonical/case_001_found/requirements.json -o report.json
```

## Run UI

```bash
reqtrace ui tests/fixtures/canonical/case_001_found/state.json tests/fixtures/canonical/case_001_found/requirements.json
```

## Related project

This study uses TESTAR for scriptless GUI testing.

- Source code: [github.com/TESTARtool](https://github.com/TESTARtool)
- Website: [testar.org](https://testar.org/)

## Citation

See [`CITATION.cff`](CITATION.cff).

## License

See [LICENSE](LICENSE).
