# Benchmark policy

A benchmark is a curated collection of artifacts associated with one system
under test (SUT). Benchmarks support reproducible demonstrations, regression
tests, and independently reviewed method evaluation.

## Allowed versioned artifacts

- requirements in supported external formats;
- TESTAR protocols and settings needed to reproduce state models;
- reasonably sized TESTAR-generated state models used as stable inputs;
- manually curated completeness labels and expected trace links;
- small generated results that were reviewed and explicitly promoted to
  reference data.

Routine application exports and historical experiment output are not benchmark
inputs and must not be committed.

## Required benchmark documentation

Every benchmark directory must identify:

- the SUT and original artifact sources;
- retrieval or generation dates;
- applicable licenses or permissions;
- the TESTAR version, protocol, settings, and random seed when known;
- which files are inputs, derived variants, and reviewed reference data;
- checksums or a versioned external-dataset reference for large artifacts;
- known provenance, privacy, or reproducibility gaps.

## Large artifacts

Do not add large generated outputs to Git history. Publish large reproducible
artifacts as versioned dataset or release assets and retain a small manifest
containing their location, size, checksum, and generation instructions.

## Tests

Unit tests should use focused fixtures. Complete benchmark artifacts are
appropriate for integration, regression, performance, and evaluation tests.
