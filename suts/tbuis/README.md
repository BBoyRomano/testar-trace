# TbUIS

TbUIS is maintained as a reproducible SUT bundle with a curated in-repo footprint.

## Structure

- `requirements/canonical/`: authoritative requirement source-of-truth
- `requirements/execution/`: current markdown inputs used by ReqTrace runs
- `requirements/source/`: provenance links and diagrams
- `requirements/variants/`: additional notations and formats under development
- `protocols/`: TESTAR protocols/settings per variant
- `evidence/runs/`: run bundles with metadata and model artifacts
- `evaluation/pinned-results/`: curated result exports used in thesis/evaluation
- `exports/`: local ad-hoc exports (not curated, not committed by policy)
- `app/`: artifact sourcing manifest (hosted app is primary execution target)

## Retention decisions

- Kept: requirement datasets, protocol sources, evidence model artifacts (`model.json`, `model.amp`), pinned result exports.
- Trimmed: full raw TESTAR `output/` tree from in-repo run bundle.
- Trimmed: committed WAR binary; app is hosted and referenced via manifest.
- Trimmed: duplicate PNG diagrams where SVG exists.

## Requirements policy

- Canonical truth: `requirements/canonical/tbuis-use-cases.json`
- Human-readable canonical rendering: `requirements/canonical/tbuis-use-cases.md`
- Execution inputs: `requirements/execution/uc-*.md`
- Alternative notations/formats: `requirements/variants/`

## Evidence bundle contract

Each folder under `evidence/runs/<run-id>/` contains:

- `metadata.json`: provenance and retained-artifact manifest
- `model/model.json`: primary TESTAR model consumed by ReqTrace
- optional `model/model.amp`: additional retained model artifact
- optional `output/`: raw TESTAR outputs (typically omitted in Git for size)

## Protocol variants

`protocols/` stores three maintained variants:

- `public/`
- `student/`
- `teacher/`

Each variant keeps the protocol source file and `test.settings`.

## Evaluation and exports

- `evaluation/pinned-results/` holds curated thesis-referenced result JSON files.
- `exports/` is for local user-selected exports and should not be treated as curated evidence.
