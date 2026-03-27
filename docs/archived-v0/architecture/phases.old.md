# Implementation phases

## Intent

This document defines the recommended implementation order for the project.

The goal is to stabilize the core analysis pipeline before expanding ingestion formats, exports, or user interfaces.

## Phase principles

- Build from the inside out: domain and analysis before interfaces.
- Stabilize canonical internal models before adding more external formats.
- Prefer one complete vertical slice over many partial features.
- Delay extensibility work until the first end-to-end flow is working.

## Phases

### 0. V1 contract

Define the first supported behavior of the system.

Clarify:
- result statuses
- what counts as evidence
- first supported TESTAR artifact
- first supported requirements artifact
- required report contents

### 1. Canonical models

Define the internal models used by the system.

This includes:
- state graph
- state observation
- requirement
- requirement unit
- requirement catalog
- match evidence
- coverage result

### 2. Fixtures and tests

Create small representative fixtures and expected results for validating the core behavior.

This phase should establish a minimal test harness for the first end-to-end flow.

### 3. CLI vertical slice

Build the smallest end-to-end flow through the CLI.

This phase should prove that the system can:
- accept inputs
- run analysis
- return a basic result

### 4. Ingestion v1

Implement the first ingestion path for both input families.

This includes:
- reading
- artifact identification
- validation
- translation into canonical internal models

### 5. Analysis v1

Implement the first matching and coverage analysis logic.

This phase should produce:
- requirement status
- supporting evidence
- summary metrics

### 6. Export v1

Stabilize the result shape and support at least one export format.

### 7. Progress and eventing

Add progress reporting needed for richer interfaces without coupling the analysis logic to presentation concerns.

### 8. Presentation expansion

Add the UI on top of the existing analysis pipeline and progress model.

### 9. Extensibility and hardening

Add more formats, versions, exporters, performance improvements, and other refinements.

## Out of scope for now

Do not prioritize these before the first end-to-end vertical slice works:
- plugin discovery
- advanced semantic matching
- multiple UI variants
- many input and output formats
- performance optimization beyond obvious issues
