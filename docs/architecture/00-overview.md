# Architecture overview

## Purpose

This document is the entry point for the architecture documentation set.

It explains:
- what the system does now
- how the architecture is split into layers
- how data moves through the system
- which terms are used consistently across the repository
- where to find subsystem-specific details

## System summary

ReqTrace ingests requirements and GUI-testing evidence, maps them into a canonical domain model, executes a selected traceability method, and exposes results through CLI, GUI, and JSON exports.

At a high level:

```text
requirements sources + evidence sources
-> ingestion
-> domain model
-> application methods
-> presentation
```

## End-to-end flow

```text
source files
-> source loader
-> parsed source model
-> normalized record batch
-> ingestion validation
-> domain mapping
-> canonical domain model
-> selected traceability method
-> result models
-> CLI / GUI / exports
```

## Architecture layers

### Ingestion
`ingestion/` reads external sources, parses source-specific formats, normalizes extracted content, validates ingestion-side records, and maps them into the domain model.

### Domain model
`domain/` defines the stable canonical concepts used across the system for requirements, evidence, and traceability.

### Application
`application/` selects and executes traceability methods and returns stable request/result models.

### Presentation
`presentation/` exposes analysis setup, run execution, results, imports, and exports through GUI and CLI interfaces.

## Current implementation note

The current implementation is intentionally lean:
- ingestion is source-aware but domain-mapped
- application executes methods synchronously through a thin service
- GUI uses presentation-owned background threading for responsiveness
- there is no full application-level live run manager yet

Where future-oriented features are discussed elsewhere in the docs, they should be read as potential extensions rather than already implemented behavior.

## Repository structure

```text
docs/
  architecture/
    00-overview.md
    01-domain-model.md
    02-ingestion.md
    03-trace-analysis.md
    04-presentation.md
    trace-methods/
      baseline.md
      heuristic.md

src/
  reqtrace/
    ingestion/
    domain/
    application/
    presentation/
```

## Shared terminology

| Term | Meaning |
|---|---|
| **Normalized record** | A shared ingestion-side shape produced before domain mapping |
| **Requirement artifact** | A canonical requirement record in the domain model |
| **Requirement fragment** | A smaller traceable unit within a requirement artifact |
| **Requirement flow** | A structured sequence such as a main flow or alternative flow |
| **Evidence item** | A canonical evidence record in the domain model |
| **Trace link** | A resolved relationship between a requirement target and evidence |
| **Coverage assessment** | Coverage status and supporting metrics for a requirement target |
| **Method** | The selected traceability approach used for a run |
| **Run** | One completed or imported execution/result shown to the user |

## Cross-cutting rules

- Ingestion owns source access, parsing, normalization, and mapping into the domain model.
- The domain model does not own source-specific parsing logic.
- The application layer owns method selection and result shaping, not parsing or UI.
- Presentation consumes application-layer contracts and must not implement traceability scoring.
- Method-specific documentation belongs under `docs/architecture/trace-methods/`.
