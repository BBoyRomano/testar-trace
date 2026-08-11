# TESTAR Trace Documentation

This directory contains current cross-cutting documentation for TESTAR Trace.
Product usage belongs in the application and package READMEs; benchmark-specific
provenance belongs with the benchmark.

## Structure

```text
docs/
  architecture/    Current system design and traceability methods
  evaluation/      Evaluation methodology and metrics
  formats/         Versioned external and benchmark formats
  operations.md    Repository governance and production deployment
  terminology.md   Canonical project and domain terminology
```

The authoritative system overview is
[`architecture/overview.md`](architecture/overview.md). Architecture history is
available through Git and is not duplicated in the active documentation tree.

Use the most specific documentation location:

- project purpose and setup: [`README.md`](../README.md);
- package behavior: the package's `README.md`;
- application behavior: the application's `README.md`;
- benchmark policy and provenance: [`benchmarks/`](../benchmarks/);
- contributor workflow: [`CONTRIBUTING.md`](../CONTRIBUTING.md);
- architecture, terminology, formats, evaluation, and operations: this directory.

Documentation must describe current behavior. Removed designs and methods
should be deleted rather than retained as an in-tree archive.
