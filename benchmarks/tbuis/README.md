# TbUIS benchmark

This benchmark contains requirement variants, TESTAR protocols, and generated
state-model samples for the University Information System (TbUIS).

## Contents

- `requirements/`: a source-faithful reference plus use-case, user-story, and
  Gherkin variants consumed by requirement adapters;
- `protocols/`: focused TESTAR protocols for selected use cases;
- `evidence/`: TESTAR-generated `.json` state models and paired `.amp` files.

`evidence/manifest.json` records the byte size and SHA-256 checksum of every
retained evidence artifact so accidental changes are detectable.

Generated TESTAR Trace analysis results are intentionally excluded. Evaluation
results become versioned reference data only after independent review.

## Current provenance gaps

The original requirement URLs are recorded in
`requirements/source/source-manifest.md`, but retrieval dates and reuse terms
still need verification. The `uc-*.json` and `uc-*.amp` samples have stable
requirement-oriented names, but still need TESTAR version information,
protocol/settings links, generation dates, seeds where applicable, and
checksums.

Until those gaps are resolved, these models are useful integration samples but
must not be presented as a publication-ready evaluation dataset.

The credentials found in the retained TESTAR material are public TbUIS demo
values, not production secrets. This assumption must be reconfirmed when the
source and license audit is completed.
