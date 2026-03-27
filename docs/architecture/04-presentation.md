# Presentation

## Purpose

This document defines the presentation layer.

It describes how the system exposes run setup, live execution, results, imported results, and export behavior through GUI and CLI interfaces.

## Scope

This document covers:
- presentation responsibilities
- GUI responsibilities
- CLI responsibilities
- run setup and control
- live run views
- result views
- import and export behavior
- presentation-local rules

Shared terminology is defined in `00-overview.md`.

## Boundaries

Presentation belongs in `presentation/`.

Presentation is responsible for:
- collecting user input for a run
- selecting requirement and evidence inputs
- selecting a traceability method
- starting a run
- listing and opening runs
- showing live progress
- showing requirement and evidence details
- showing run-level and requirement-level results
- importing saved results
- exporting visible results

Presentation is not responsible for:
- source parsing
- ingestion validation
- traceability matching or scoring
- link resolution
- coverage calculation

## Interface structure

The presentation layer includes two interfaces:
- `presentation/gui/`
- `presentation/cli/`

Both interfaces should operate on the same application-layer contracts and result shapes.

## Run setup

A user should be able to create a run by selecting:
- requirements source
- requirement source format when needed
- evidence source
- evidence source format when needed
- traceability method
- optional requirement or evidence scope filters
- optional output or export destination

Method-specific options may be added later, but the common setup flow should remain method-agnostic.

## Runs and lifecycle

Runs are first-class presentation objects.

Each run should show:
- run id or run name
- source kind: live or imported
- selected method
- status
- progress
- timestamps if available

Imported runs should be:
- viewable
- filterable alongside live runs where useful
- exportable
- clearly distinguished from live runs

Recommended run statuses:
- queued
- running
- completed
- failed
- cancelled
- imported

A run must continue independently of whether its detail view is currently open. Users should be able to navigate away from a live run, inspect another run, start an additional run, or open imported results without stopping the original live run.

## GUI

### Workspace
Main features:
- start new analysis run
- open saved result
- view recent live and imported runs
- quick links to requirement and evidence views

### Analysis setup
Main features:
- requirements source selection
- evidence source selection
- method dropdown
- optional scope selection
- run button

Optional later:
- advanced settings
- method-specific configuration

### Runs view
Main features:
- active runs
- completed runs
- imported runs
- per-run status
- per-run progress
- selected method
- open run detail
- cancel running run
- start additional runs while others are active

### Live run detail
Main features:
- overall progress bar
- method name
- run status
- current activity if available
- cancel action
- link back to run list or workspace without affecting execution

Per-requirement live fields should include:
- requirement id
- title
- status
- coverage status when known
- confidence or certainty when available
- finding count or linked result count when available
- warning or partial-result indicator when applicable

Incremental updates should be visible while a run is executing. If a method discovers one finding and later discovers additional findings, the visible requirement state should update accordingly.

### Results overview
Main features:
- summary metrics
- filters by status, confidence, and method
- requirement results table
- run metadata
- export actions

Recommended summary metrics include:
- requirement count
- analyzed requirement count
- covered, partially covered, and uncovered requirement counts
- requirement fragment count and covered fragment count where available
- trace-link count
- supporting-evidence count where available
- confidence-related metrics when supported by the selected method
- warning count
- elapsed duration when available

### Requirement result detail
Main features:
- requirement structure
- fragment-by-fragment coverage
- matched evidence
- linked states, transitions, actions, or observations
- supporting runs
- confidence
- explanations or rationale where available
- uncovered fragments
- partial findings or low-confidence findings when present

### Requirements view
Main features:
- requirements table or tree
- search and filtering
- requirement detail panel

Requirement detail should show:
- requirement id
- title
- type
- source
- fragments
- flow structure
- preconditions
- main flow
- alternative flows
- postconditions

### Evidence view
Main features:
- evidence list or summary view
- search and filtering
- state, transition, and run detail views

Evidence detail should show:
- state id
- title or URL
- UI elements
- transitions
- actions
- run membership
- optional screenshots, logs, or report references

### Export and import
Main features:
- export JSON
- export Markdown or HTML later
- export CSV later
- choose scope
- choose detail level
- import previously saved results for inspection

Imported results should preserve enough run metadata and requirement-level results to support inspection without requiring the original live execution context.

## GUI capabilities

The GUI should support:
- selecting a method for a new run
- starting multiple runs
- viewing multiple runs at once
- opening a run and seeing live progress
- navigating away from a run while it continues
- cancelling a running run
- opening an imported result for inspection
- viewing run summaries and requirement details
- exporting results

The GUI does not need pause or resume support in v1.

## CLI

Recommended commands:
- `analyze`
- `list-methods`
- `list-runs`
- `show-run`
- `open-results`
- `export-results`

Recommended options:
- requirements source
- requirement source format
- evidence source
- evidence source format
- selected method
- output format
- output path
- requirement filter or scope
- verbosity

CLI behavior should align with the same run and result concepts used by the GUI.

CLI output should support:
- progress updates while a run is executing
- final summary output
- optional detailed requirement output
- imported-result inspection
- export commands over the same shared result data

The CLI does not need to reproduce every GUI interaction, but it should expose the same underlying capabilities where practical.

## Presentation-local rules

- Presentation consumes application-layer contracts rather than implementing business logic.
- GUI and CLI should expose the same run model and the same core result concepts.
- Imported runs should be handled as presentation-visible results, not as new analysis executions.
- Export should be driven from shared application-layer result models.
- Presentation should surface uncertainty honestly, including low-confidence findings, partial results, and cancelled or failed runs where applicable.

## References

- `03-trace-analysis.md` defines the runtime models and live progress behavior consumed by presentation.
- `01-domain-model.md` defines the canonical requirement and evidence concepts surfaced in result views.
