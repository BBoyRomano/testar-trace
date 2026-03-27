# Systems under test (SUTs)

This folder stores per-SUT source material, executable inputs, protocols, evidence, and ReqTrace outputs.

## Layout
- `<sut>/requirements/canonical/`: authoritative, reviewable requirements dataset
- `<sut>/requirements/execution/`: current tool-ready requirement inputs
- `<sut>/requirements/source/`: provenance and reference material
- `<sut>/protocols/`: TESTAR protocol sources and settings
- `<sut>/evidence/`: raw and extracted TESTAR outputs
- `<sut>/app/`: packaged application binaries, when stored in the repo
- `<sut>/exports/`: ReqTrace-generated outputs for that SUT

Naming uses lowercase kebab-case for folders and descriptive filenames.
