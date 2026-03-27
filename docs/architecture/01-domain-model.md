# Domain model

## Purpose

This document defines the canonical domain concepts used across the system.

It covers the stable models for:
- requirements
- evidence
- traceability

## Scope

This document covers:
- domain responsibilities
- domain boundaries
- domain package structure
- requirements concepts
- evidence concepts
- traceability concepts

Shared terminology is defined in `00-overview.md`. This document only introduces terms that are local to the domain model.

## Boundaries

The domain layer is independent of source-specific ingestion details and independent of presentation concerns.

- `ingestion/` parses and normalizes external inputs, then maps them into domain models.
- `domain/` defines the stable canonical shapes used by the rest of the application.
- `application/trace_analysis/` executes analysis workflows over domain entities and returns runtime result models.
- `presentation/` displays application-layer results and progress.

The domain layer does not own:
- source-specific parsing logic
- pipeline orchestration
- runtime progress models
- GUI or CLI result shaping

## Package structure

```text
src/
  domain/
    requirements/
      models.py
    evidence/
      models.py
    traceability/
      models.py
    common/
      value_objects.py
      enums.py
```

This can later expand into multiple files per subdomain if needed, but the split should remain:
- `requirements/`
- `evidence/`
- `traceability/`
- `common/`

## Requirements concepts

Recommended core concepts:
- `RequirementArtifact`
- `RequirementFragment`
- `RequirementFlow`
- `RequirementFlowEdge`

### `RequirementArtifact`
Represents one requirement-level record, such as:
- user story
- use case
- formal requirement
- Gherkin scenario
- acceptance-criteria container

Recommended fields:
- `id`
- `external_id`
- `title`
- `text`
- `type`
- `source_type`
- `source_ref`
- `attributes`
- `fragments`
- `flows`

### `RequirementFragment`
Represents a smaller traceable unit inside a requirement artifact.

Examples:
- one acceptance criterion
- one step in a use case
- one line or block in a formal requirement
- one Gherkin step

Recommended fields:
- `id`
- `artifact_id`
- `text`
- `kind`
- `order_index`
- `attributes`

### `RequirementFlow`
Represents a structured flow within a requirement artifact.

Examples:
- preconditions
- main flow
- alternative flow
- postconditions

Recommended fields:
- `id`
- `artifact_id`
- `name`
- `kind`
- `nodes`
- `edges`

### `RequirementFlowEdge`
Represents one relationship between flow nodes or steps.

Recommended fields:
- `id`
- `flow_id`
- `source_fragment_id`
- `target_fragment_id`
- `kind`

## Evidence concepts

Recommended core concepts:
- `EvidenceItem`
- `EvidenceRun`
- `EvidenceState`
- `EvidenceTransition`
- `EvidenceObservation`

The exact shape can vary by tool family, but the domain should preserve canonical evidence concepts.

### `EvidenceItem`
A top-level evidence record.

Examples:
- one TESTAR run
- one generated report
- one execution summary
- one imported execution artifact

Recommended fields:
- `id`
- `external_id`
- `title`
- `type`
- `source_type`
- `source_ref`
- `attributes`

### `EvidenceRun`
Represents one execution run or session.

Recommended fields:
- `id`
- `evidence_item_id`
- `started_at`
- `finished_at`
- `status`
- `attributes`

### `EvidenceState`
Represents a system or UI state observed during execution.

Recommended fields:
- `id`
- `run_id`
- `title`
- `url`
- `widgets`
- `screenshot_ref`
- `attributes`

### `EvidenceTransition`
Represents one action or transition between states.

Recommended fields:
- `id`
- `run_id`
- `source_state_id`
- `target_state_id`
- `action`
- `attributes`

### `EvidenceObservation`
Represents additional supporting evidence not modeled as a state or transition.

Examples:
- log event
- assertion result
- warning
- screenshot metadata
- report excerpt reference

Recommended fields:
- `id`
- `run_id`
- `kind`
- `text`
- `attributes`

## Traceability concepts

Recommended core concepts:
- `TraceLink`
- `TraceEvidence`
- `CoverageAssessment`

### `TraceLink`
Represents a resolved relationship between a requirement target and evidence.

Requirement targets may be:
- whole requirement artifacts
- requirement fragments

Evidence targets may be:
- evidence items
- runs
- states
- transitions
- observations

Recommended fields:
- `id`
- `requirement_artifact_id`
- `requirement_fragment_id`
- `evidence_type`
- `evidence_id`
- `confidence_label`
- `confidence_score`
- `rationale`
- `attributes`

### `TraceEvidence`
Represents the supporting details associated with a trace decision.

Examples:
- matched state identifiers
- matched transitions
- supporting observations
- snippets or references used during analysis

Recommended fields:
- `id`
- `trace_link_id`
- `kind`
- `evidence_id`
- `text`
- `attributes`

### `CoverageAssessment`
Represents coverage status and supporting metrics for a requirement target.

Coverage targets may be:
- whole requirement artifacts
- requirement fragments

Recommended fields:
- `id`
- `requirement_artifact_id`
- `requirement_fragment_id`
- `status`
- `coverage_ratio`
- `confidence_label`
- `confidence_score`
- `supporting_link_ids`
- `attributes`

## Domain-local rules

- The domain layer defines canonical concepts, not source-native formats.
- Source-specific parsing and extraction stay outside the domain layer.
- Runtime workflow, progress, and run orchestration stay outside the domain layer.
- Domain concepts should be stable enough to support multiple ingestion paths and multiple analysis pipelines.
- Requirements, evidence, and traceability should remain separate subdomains even when implemented in a small number of files.

## References

- `02-ingestion.md` defines how external inputs are mapped into these domain concepts.
- `03-trace-analysis.md` defines the runtime models and workflow that operate on these domain concepts.
