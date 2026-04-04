# Systems Under Test (SUTs)

This folder is organized as reproducible per-SUT bundles.

Each SUT lives under `suts/<sut-name>/` to keep requirements, TESTAR evidence, protocols, and evaluation outputs together.

## Final structure policy

Use this structure for each SUT:

- `requirements/canonical/`: authoritative requirements dataset used for reporting
- `requirements/execution/`: current tool-ready ReqTrace inputs
- `requirements/source/`: provenance references and diagrams
- `requirements/variants/`: additional notations/file types under development
- `protocols/`: TESTAR protocol sources and settings for reruns
- `evidence/runs/<run-id>/`: evidence bundles with run metadata and model artifacts
- `evaluation/pinned-results/`: curated ReqTrace result JSON files referenced in thesis/evaluation
- `exports/`: local, user-generated run exports (not part of curated dataset)
- `app/`: optional artifact manifest and retrieval instructions (avoid committing large binaries)

## Retention rules

- Keep canonical requirements, execution inputs, protocol sources, and model JSON in Git.
- Keep only curated/pinned result exports in Git.
- Treat `exports/` as local working output chosen by the user.
- Avoid committing bulky raw TESTAR output trees unless explicitly needed.
- Prefer source manifests and retrieval instructions over committing large app binaries.

## README policy

- Keep one README at `suts/` and one at each `suts/<sut>/`.
- Prefer documenting subfolder rules in the SUT root README.
- Add deeper README files only when a subfolder has independent lifecycle or external handoff needs.
