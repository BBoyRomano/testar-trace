# ReqTrace roadmap

This roadmap maps thesis goals to implementation phases.

## Phase 0: core baseline pipeline (completed)

- markdown/json requirements ingestion
- TESTAR evidence ingestion
- baseline method execution path
- CLI and local GUI execution
- JSON import/export for results

## Phase 1: ingestion extensibility (in progress)

- keep format-keyed ingestion registry as stable extension boundary
- add additional requirement notations incrementally
- keep TESTAR primary while preserving a path for future evidence adapters

## Phase 2: method quality and semantics (planned)

- improve precondition/postcondition evidence checks
- improve alternate-flow branch quality and uncertainty calibration
- strengthen multi-instance reporting for repeated requirement realizations

## Phase 3: run management UX (partially completed)

Completed now:

- application-level async run executor
- concurrent run handling
- persisted GUI run history

Planned next:

- richer in-flight per-requirement progress visibility
- cancellation controls

## Phase 4: explainability and interaction (planned)

- synchronized requirement-step and graph-step highlighting
- instance-level drill-down views for main/alternate traces
- richer trace chain visualization with intermediate-step context

## Phase 5: reporting and sharing (in progress)

Completed now:

- JSON import/export baseline contract

Planned next:

- richer thesis-facing summary views and report templates
- expanded global metric reporting for evaluation communication
