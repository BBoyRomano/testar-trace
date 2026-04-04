# Architecture overview

## Purpose

This document is the entry point for the ReqTrace architecture set.

It explains:

- current system behavior
- architectural layers and responsibilities
- end-to-end data flow
- canonical terminology

## System summary

ReqTrace ingests requirements and scriptless-testing evidence, maps them into canonical models, executes a traceability method, and exposes results via CLI, GUI, and JSON import/export.

## End-to-end flow

```text
requirements/evidence inputs
-> ingestion loaders + normalization
-> domain mapping
-> application request snapshot
-> traceability method execution
-> result model
-> CLI/GUI rendering + JSON persistence
```

## Layers

### Ingestion (`src/reqtrace/ingestion/`)

Owns source-specific parsing, normalization, validation, and mapping into canonical application/domain snapshots.

### Domain (`src/reqtrace/domain/`)

Owns stable source-agnostic concepts for requirements, evidence, and traceability relationships.

### Application (`src/reqtrace/application/`)

Owns request/result contracts, method selection/execution, async run execution, and run-history use-cases.

### Infrastructure (`src/reqtrace/infrastructure/`)

Owns persistence/serialization adapters (for example JSON result serialization and JSON-backed run-history storage).

### Presentation (`src/reqtrace/presentation/`)

Owns CLI/GUI interaction, input collection, run orchestration wiring, and result rendering.

## Current implementation status

Current implementation is intentionally lightweight but complete for baseline thesis runs:

- ingestion supports markdown/json requirements and TESTAR evidence
- default selected method is baseline (`baseline`)
- `candidate_match`, `flow_match`, and `hybrid_match` are available for direct comparison
- run execution concurrency is handled by an application-level async executor
- GUI run history is persisted locally (`.reqtrace/gui-history`)

## Repository map

```text
docs/
  architecture/
    00-overview.md
    01-domain-model.md
    02-ingestion.md
    03-trace-analysis.md
    04-presentation.md
    05-infrastructure.md
    trace-methods/
      baseline.md
      candidate-match.md
      flow-match.md
      hybrid-match.md

src/
  reqtrace/
    domain/
    ingestion/
    application/
    infrastructure/
    presentation/
```

## Shared terminology

| Term | Meaning |
|---|---|
| Normalized record | Shared ingestion-side shape before domain mapping |
| Requirement artifact | Canonical requirement unit |
| Requirement fragment | Traceable fragment within a requirement |
| Requirement flow | Main/alternative structured flow |
| Evidence artifact | Canonical evidence unit |
| Trace link | Resolved requirement-to-evidence relation |
| Coverage assessment | Coverage and confidence outcome |
| Traceability method | Selected analysis approach for a run |
| Run | One traceability execution or imported result |
