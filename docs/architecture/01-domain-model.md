# Domain model

## Purpose

This document defines canonical entities used across ingestion, analysis methods, and presentation.

The domain layer is source-agnostic and UI-agnostic.

## Boundaries

- `ingestion/` parses external formats and maps to domain concepts.
- `domain/` defines stable concepts for requirements, evidence, and traceability.
- `application/` executes methods over canonical snapshots and returns result models.
- `presentation/` displays and exports application-layer results.

Domain does not own parser logic, method orchestration, persistence, or UI behavior.

## Package structure

```text
src/reqtrace/domain/
  common/
  requirements/
  evidence/
  traceability/
```

## Core entities

### Common

- `SourceRef`
- `ImportBatchRef`
- `Provenance`

### Requirements

- `RequirementArtifact`
- `RequirementFragment`
- `RequirementFlow`
- `RequirementFlowEdge`

Requirement fragments support preconditions, main steps, alternative steps, and postconditions.

### Evidence

- `ExecutionRun`
- `ApplicationState`
- `UIElement`
- `Action`
- `Transition`
- `Observation`
- `Attachment`

Current ingestion focuses on TESTAR exports; domain concepts remain generic for future tool adapters.

### Traceability

- `TraceLink`
- `TraceEvidence`
- `CoverageAssessment`

These capture requirement-to-evidence links and coverage outcomes.

## Design rules

- Keep domain entities stable and explicit.
- Keep source-specific parsing and heuristics outside domain.
- Preserve flow and step structure for path-aware analysis.
