# Domain model

## Purpose

This document defines canonical entities used across ingestion, analysis methods, and interface adapters.

The domain layer is source-agnostic and UI-agnostic.
It is intentionally a validated canonical schema with lightweight invariants, not a behavior-heavy domain service layer.

## Modeling style

The domain is intentionally **thin** and **canonical**:

- Domain modules define stable concepts, enums, and invariants.
- Domain models are schema-first records with validation boundaries.
- Method orchestration, runtime policies, and persistence workflows live outside the domain.

This keeps the domain easy to evolve across ingestion formats and interface adapters.

## Boundaries

- `ingestion/` parses external formats and maps to domain concepts.
- `domain/` defines stable concepts for requirements, evidence, and traceability.
- `application/` executes methods over canonical snapshots and returns result models.
- `apps/*` interface adapters display and export application-layer results.

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

## Common package guardrails

`domain/common` is reserved for primitives that are truly cross-domain and stable.

- Allowed: base model contracts, shared enum utilities, provenance/source references.
- Not allowed: convenience helpers that only serve one subdomain.
- If a type is only used in one bounded context, keep it in that subdomain package.

## Evolution triggers

Apply structural changes only when the model pressure is real:

- Split `domain/traceability` further when one module starts mixing multiple concerns heavily.
- Revisit generic evidence fields when a second non-TESTAR evidence source cannot map cleanly.
- Extract notation-specific requirement payloads if `RequirementArtifact` grows into a catch-all.

Until those triggers appear, prefer consistency and stability over extra abstraction.

