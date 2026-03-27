# ReqTrace

ReqTrace is a thesis prototype for requirements traceability over scriptless GUI testing evidence.

It ingests requirements and TESTAR-exported GUI state models, maps them into a canonical domain model, executes a selected traceability method, and exposes the results through a CLI, a lightweight GUI, and JSON exports.

## Current supported inputs

- **Requirements:** markdown use-case files (`--requirements-format markdown`)
- **Evidence:** TESTAR exported model JSON (`--evidence-format testar`)
- **Method:** `baseline` is the currently implemented end-to-end method

The baseline method proves the full pipeline works on real data. It does **not** yet infer real trace links or coverage from evidence.

## Repository layout

- `src/` – ReqTrace source code
- `tests/` – automated tests and reusable test fixtures/builders
- `suts/` – system-under-test materials, protocols, evidence, and exports
- `docs/` – current architecture and project documentation
- `papers/` – thesis-related materials

Archived material lives under `docs/archived-v0/` and is retained for thesis history only.

## CLI

Install in editable mode:

```bash
python -m pip install -e .[dev]
```

List available methods:

```bash
reqtrace methods
```

Run ReqTrace on one requirements file and one TESTAR model:

```bash
reqtrace run \
  --requirements suts/tbuis/requirements/execution/uc-20-displays-information-about-system-s-abilities.md \
  --requirements-format markdown \
  --evidence suts/tbuis/evidence/runs/2026-03-22-webdriver-tbuis-public/model/model.json \
  --evidence-format testar \
  --method baseline
```

Write the result to a specific path:

```bash
reqtrace run \
  --requirements suts/tbuis/requirements/execution/uc-20-displays-information-about-system-s-abilities.md \
  --requirements-format markdown \
  --evidence suts/tbuis/evidence/runs/2026-03-22-webdriver-tbuis-public/model/model.json \
  --evidence-format testar \
  --method baseline \
  --output suts/tbuis/exports/uc-20-baseline-result.json
```

If `--output` is omitted, ReqTrace auto-generates a timestamped export path.

Render a previously exported result:

```bash
reqtrace show-result suts/tbuis/exports/tbuis-baseline-2026-03-27T01-46-58Z.json
```

Launch the lightweight desktop UI:

```bash
reqtrace ui
```

In headless environments such as devcontainers, the GUI may not be available. The CLI remains fully supported there.

## Documentation

Start with:

- `docs/architecture/00-overview.md`
- `docs/architecture/01-domain-model.md`
- `docs/architecture/02-ingestion.md`
- `docs/architecture/03-trace-analysis.md`
- `docs/architecture/04-presentation.md`

## Related project

ReqTrace uses TESTAR as the GUI testing tool.

- Source code: [github.com/TESTARtool](https://github.com/TESTARtool)
- Website: [testar.org](https://testar.org/)

## Citation

See [`CITATION.cff`](CITATION.cff).

## License

See [LICENSE](LICENSE).
