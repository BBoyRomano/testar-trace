# Architecture overview

## Purpose

This document is the entry point for the architecture documentation set.

It explains:
- what the system does
- how the architecture is split into layers
- how data moves through the system
- which terms are used consistently across the repository
- which rules apply across all layers
- where to find subsystem-specific details

## Scope

These architecture documents are intended to:
- establish a shared structure for the repository
- guide contributors toward consistent implementations
- define ownership boundaries between layers
- provide a shared vocabulary for design, implementation, and review

They do not replace method-specific documentation. Method-specific behavior belongs under `docs/architecture/trace-methods/`.

## System summary

The system ingests requirements and evidence, maps them into a canonical domain model, executes a selected traceability method, and exposes live or imported run data through GUI and CLI interfaces.

At a high level:

```text
requirements sources + evidence sources
-> ingestion
-> domain model
-> application runtime
-> presentation
```

## End-to-end flow

```text
source
-> source loader
-> parsed source model
-> normalized record batch
-> ingestion-side validation
-> domain mapping
-> canonical domain model
-> selected application method
-> run/result models
-> GUI / CLI / exports
```

A complete run may be:
- started from user-selected requirement and evidence inputs
- observed while it is executing
- cancelled while it is running
- exported after completion
- imported later for inspection

## Architecture layers

### Ingestion
`ingestion/` reads external files, exports, and connectors; parses source-specific formats; normalizes extracted content; validates ingestion-side records; and maps them into the domain model.

### Domain model
`domain/` defines the stable canonical concepts used across the system for requirements, evidence, and traceability.

### Application runtime
`application/` executes selected traceability methods, manages run lifecycle, coordinates live execution, and returns application-level request, progress, and result models.

### Presentation
`presentation/` exposes analysis setup, run control, progress, results, imported runs, and exports through GUI and CLI interfaces.

## Repository structure

Documentation structure:

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
```

Recommended source layout:

```text
src/
  reqtrace/
    ingestion/
    domain/
      requirements/
      evidence/
      traceability/
      common/
    application/
    presentation/
      cli/
      gui/
```

## Shared terminology

Use these terms consistently across architecture docs, code, and review discussions.

| Term | Meaning |
|---|---|
| **Artifact type** | The logical shape of the content being modeled |
| **Source type** | Where the content comes from |
| **Container format** | How the content is stored or exchanged |
| **Exchange format** | A transport format between tools rather than a writing notation |
| **Normalized record** | The shared ingestion-side shape produced before domain mapping |
| **Requirement artifact** | A canonical requirement record in the domain model |
| **Requirement fragment** | A smaller traceable unit within a requirement artifact |
| **Requirement flow** | A structured sequence such as a main flow or alternative flow |
| **Evidence item** | A canonical evidence record in the domain model |
| **Trace link** | A resolved relationship between a requirement target and evidence |
| **Coverage assessment** | Coverage status and supporting metrics for a requirement target |
| **Method** | The selected traceability approach used for a run |
| **Run** | One live or imported execution or result shown to the user |
| **Live run** | A run executed by the application |
| **Imported run** | A previously saved result opened for inspection |
| **Run lifecycle** | The set of transitions a run may undergo, such as queued, running, completed, failed, cancelled, or imported |

Subsystem docs may define additional local terms when needed, but shared terms should keep the meanings established here.

## Cross-cutting architectural rules

- Ingestion owns source access, parsing, extraction, normalization, ingestion-side validation, and mapping into the domain model.
- The domain model does not own source-specific parsing logic.
- The domain model defines stable canonical entities, not runtime workflow objects.
- Runtime execution models belong in `application/`, not in `domain/`.
- Methods are the top-level selectable traceability approaches exposed by the application.
- The application layer owns run lifecycle, method selection, execution, cancellation, and result shaping for presentation.
- Presentation consumes application-layer contracts and must not implement parsing, matching, scoring, or coverage logic.
- Method-specific documentation belongs under `docs/architecture/trace-methods/`.
- Shared terminology should remain consistent across all architecture docs and implementation discussions.

## Reading order

Read the documents in this order:
1. `00-overview.md`
2. `01-domain-model.md`
3. `02-ingestion.md`
4. `03-trace-analysis.md`
5. `04-presentation.md`
6. `trace-methods/baseline.md`

## Document map

- `01-domain-model.md` defines canonical requirements, evidence, and traceability concepts.
- `02-ingestion.md` defines ingestion responsibilities, source handling, normalization, and domain mapping.
- `03-trace-analysis.md` defines application-layer methods, run lifecycle, progress, and result models.
- `04-presentation.md` defines GUI and CLI responsibilities, setup flows, run views, progress views, detail views, and exports.
- `trace-methods/baseline.md` defines the bootstrap method used to run the program end to end before real traceability analysis exists.
