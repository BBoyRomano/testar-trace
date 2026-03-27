# Trace analysis

## Purpose

This document defines the application layer responsible for traceability execution.

It describes how the system selects a method, executes a run, manages run lifecycle, emits progress, and returns application-level result models.

## Scope

This document covers:
- application runtime responsibilities
- trace-analysis boundaries
- application package structure
- method architecture
- run lifecycle
- runtime request, progress, and result models
- progress updates
- cancellation behavior
- method-document placement

Shared terminology is defined in `00-overview.md`. This document only adds local clarification where needed.

## Boundaries

Trace analysis belongs in the application layer.

- `ingestion/` prepares domain inputs from external sources.
- `domain/` defines canonical requirements, evidence, and traceability entities.
- `application/` executes methods and produces runtime progress and result models.
- `presentation/` displays those runs and controls execution.

Trace analysis should not be placed in:
- `ingestion/`
- `domain/`
- `presentation/`

## Package structure

A lean package structure is preferred.

```text
src/
  reqtrace/
    application/
      services/
        traceability_service.py
      methods/
        baseline.py
      results.py
      exceptions.py
      protocols.py
```

Additional modules may be introduced later when there is clear pressure, such as multiple real consumers, repeated logic, or genuinely separate concerns. The application layer should remain orchestration-focused rather than framework-like.

## Responsibilities

The application layer is responsible for:
- method selection
- run creation and execution
- live run lifecycle management
- progress emission
- cancellation handling
- requirement-level result assembly
- aggregate run result assembly
- shaping stable contracts for presentation and export

The application layer is not responsible for:
- parsing external requirement formats
- parsing external evidence formats
- defining source-specific ingestion adapters
- implementing GUI screens
- implementing CLI commands
- inventing traceability semantics that belong in a method definition

## Method architecture

The system must support multiple traceability methods over time.

A method is the top-level selectable approach exposed by the application. Each method is responsible for one complete execution against selected requirements and evidence.

A method implementation should:
- accept one stable request shape
- produce one stable result shape
- emit progress updates where supported
- cooperate with cancellation
- avoid depending on presentation concerns

A small protocol or equivalent contract is sufficient. A method does not require a plugin framework, stage engine, or dependency-injection container.

## Run lifecycle

Runs are first-class runtime objects.

A run may be:
- queued
- running
- completed
- failed
- cancelled
- imported

A live run should continue independently of which screen or command view is currently open. Presentation may navigate away from a run, inspect other runs, or open imported runs without altering the execution state of the original live run.

The application layer should support:
- starting a run
- querying a run while it is executing
- receiving incremental updates
- cancelling a running run
- listing active and completed runs
- loading imported result data for inspection

Pause and resume are not required in v1.

## Runtime models

The application layer returns application-level runtime models. These are not part of the core domain model.

Recommended runtime concepts:
- `TraceabilityRequest`
- `TraceabilityRun`
- `RequirementTraceabilityResult`
- `TraceabilitySummary`
- `TraceabilityResult`
- `RunProgressUpdate` or equivalent incremental progress model when live updates are supported

Recommended responsibilities:
- `TraceabilityRequest`: selected inputs, method, and runtime configuration
- `TraceabilityRun`: execution metadata, selected method, status, and timing
- `RequirementTraceabilityResult`: final per-requirement output including coverage, links, confidence, and warnings where applicable
- `TraceabilitySummary`: aggregate counts and run-level metrics
- `TraceabilityResult`: top-level completed or partial result bundle for one run
- `RunProgressUpdate`: incremental live progress state for one requirement or one run

These models should remain stable across methods so GUI, CLI, and export code can consume one consistent contract.

## Progress updates

The application layer should support incremental progress updates.

This allows the interface to show, per requirement:
- pending
- analyzing
- partially matched or low-confidence finding when supported by a method
- covered or partially covered when known
- done
- failed

The application layer should also support run-level progress such as:
- total requirements
- requirements started
- requirements completed
- requirements failed
- requirements cancelled or skipped where applicable
- elapsed time when available

Live updates should be granular enough to support both:
- CLI progress output
- GUI live tables and detail panels

The application layer does not need a complex event framework. A small, stable progress contract is enough.

## Cancellation and concurrency

The system should support multiple runs over time and should allow a running run to be cancelled.

Where the execution environment permits, the application layer may support multiple live runs concurrently. Presentation should treat each run as an independent object with its own progress and result state.

Cancellation should be cooperative:
- the application layer requests cancellation
- the executing method stops as soon as practical
- the run is finalized with a cancelled status and any valid partial result data retained if available

## Result shaping

The application layer owns the runtime-facing shape consumed by presentation and export.

That shape should support:
- run metadata
- selected method metadata
- requirement-level coverage and findings
- trace links and supporting evidence when a method produces them
- confidence or certainty indicators where available
- warnings and partial-result indicators
- summary metrics

The application layer should not format GUI widgets, terminal layout, Markdown, or HTML. Presentation is responsible for those projections.

## Method growth policy

The application layer should remain lean.

Introduce a new application-layer module only when at least one of these is true:
- logic is reused by two or more real methods or flows
- a file becomes crowded enough to harm readability
- a concern has a genuinely separate lifecycle, such as export-only projections or imported-run loading

Avoid introducing:
- stage frameworks
- event buses
- dependency-injection containers
- plugin discovery systems
- command-handler or mediator frameworks

unless they are clearly justified by real complexity.

## Method documentation placement

Each method should have its own document under:

```text
docs/
  architecture/
    trace-methods/
```

Those documents should define:
- method purpose
- method inputs
- processing behavior
- progress behavior
- result behavior
- limitations

The method document should not duplicate application-wide runtime rules defined here.

## References

- `02-ingestion.md` defines how requirements and evidence become domain inputs.
- `01-domain-model.md` defines the stable requirement, evidence, and traceability entities.
- `04-presentation.md` defines how runs, progress, and results are surfaced to users.
