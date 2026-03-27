# TbUIS

TbUIS is stored as a self-contained system-under-test bundle.

## Structure
- `app/`: packaged application binaries
- `requirements/canonical/`: authoritative requirements dataset
- `requirements/execution/`: current ReqTrace-ready requirement inputs
- `requirements/source/`: provenance and reference material
- `protocols/`: TESTAR protocols and settings
- `evidence/`: TESTAR run outputs and models
- `exports/`: ReqTrace-generated outputs for this SUT

## Requirements policy
- Canonical truth lives in `requirements/canonical/`
- Current markdown ingestion runs against `requirements/execution/`
- Provenance and diagrams stay in `requirements/source/`
