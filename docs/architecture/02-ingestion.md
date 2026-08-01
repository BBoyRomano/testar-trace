# Ingestion

## Purpose

The ingestion layer reads external requirement/evidence sources and converts them into canonical snapshots.

It is the boundary between source-specific formats and source-agnostic traceability logic.

## Current supported formats

- requirements input formats: `markdown`, `json`
- evidence: `testar`

Requirements input can be one file, multiple files, or a directory.

## Boundaries

Ingestion owns:

- source access (file/directory loading)
- source-specific parsing
- normalization into ingestion-side models
- ingestion-side validation
- mapping into canonical snapshots

Ingestion does not own:

- method selection/scoring
- interface orchestration
- result rendering/persistence

## Package structure

```text
src/reqtrace/ingestion/
  exceptions.py
  input_resolution.py
  mapping.py
  normalization.py
  ports.py
  provenance.py
  records.py
  registry.py
  validation.py
  requirements/
    adapter.py
    models.py
    markdown_loader.py
    json_loader.py
  evidence/
    adapter.py
    models.py
    testar_loader.py
```

## Ingestion flow

```text
source path(s)
-> loader/parser
-> normalized ingestion batch
-> validation
-> canonical mapping
-> application request snapshot
```

## Extension model

ReqTrace uses a format-keyed ingestion registry.

To add a new source type:

1. implement loader/parser
2. normalize into ingestion models
3. map to canonical entities
4. register under a stable format key

This keeps format growth incremental and method-agnostic.

## Design rules

- Keep parsing logic inside ingestion.
- Preserve provenance and flow/step structure where available.
- Keep adapters small, explicit, and deterministic.
