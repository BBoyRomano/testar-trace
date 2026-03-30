# Trace analysis

## Purpose

This document defines the application layer responsible for traceability execution.

It describes the current method-execution boundary, request/result contracts, and the rules for keeping the application layer thin.

## Boundaries

Trace analysis belongs in the application layer.

- `ingestion/` prepares canonical domain inputs.
- `domain/` defines stable requirements, evidence, and traceability entities.
- `application/` selects and executes traceability methods.
- `presentation/` collects user input and renders results.

## Current package structure

```text
src/
  reqtrace/
    application/
      services/
        traceability_service.py
      methods/
        baseline.py
        heuristic.py
      results.py
      exceptions.py
      protocols.py
```

This lean structure is deliberate and should remain the default until real complexity forces further extraction.

## Responsibilities

The application layer is responsible for:
- method selection
- request/result contracts
- execution orchestration
- requirement-level result assembly
- run-level summary assembly

The application layer is not responsible for:
- source parsing
- source-specific validation
- GUI threading
- CLI rendering
- domain-model definitions

## Method architecture

A method is the top-level selectable traceability approach exposed by the application.

Each method should:
- accept one stable `TraceabilityRequest`
- return one stable `TraceabilityResult`
- avoid depending on presentation concerns
- stay deterministic and explainable unless a method explicitly introduces another approach

A small protocol is enough. The application layer does not need a plugin framework, stage engine, or dependency injection container.

## Current runtime model

The current application layer executes methods synchronously through `TraceabilityService`.

That means:
- there is no application-level run queue yet
- there is no application-level cancellation contract yet
- there is no separate progress-update model yet
- GUI responsiveness is currently handled in the presentation layer with background threading

This is acceptable for the current prototype and should not be inflated just to match an earlier, richer architectural idea.

## Request and result models

The application layer currently exposes stable runtime-facing models such as:
- `TraceabilityRequest`
- `TraceabilityRun`
- `RequirementTraceabilityResult`
- `TraceabilitySummary`
- `TraceabilityResult`

These are application contracts, not core domain entities.

## Method growth policy

Introduce a new application-layer module only when one of these is true:
- logic is reused by two or more real methods or flows
- a file becomes crowded enough to harm readability
- a concern has a genuinely separate lifecycle

Avoid introducing:
- pipeline frameworks
- event buses
- DI containers
- plugin discovery
- mediator/handler frameworks

unless real complexity justifies them.
