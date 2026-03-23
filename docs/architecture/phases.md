# Implementation phases

## Purpose

This document defines the implementation phases for ReqTrace.

Each phase should leave the repository in a stable and usable state.

## Phase 0 — Project foundation

Establish the initial project structure, naming, and architecture direction.

Outputs:

- repository structure
- architecture document
- phase plan
- v1 scope

## Phase 1 — Canonical domain model

Define the canonical internal models used by ReqTrace.

Outputs:

- state graph model
- requirements model
- coverage model

## Phase 2 — Core application flow

Define the main application use case for analyzing coverage.

Outputs:

- analyze coverage use case
- initial request and report flow

## Phase 3 — Basic ingestion

Support canonical input files for state models and requirements.

Outputs:

- canonical state model importer
- canonical requirements importer
- ingestion tests

## Phase 4 — Baseline analysis

Implement the first working analyzer and baseline coverage behavior.

Outputs:

- baseline analyzer
- analysis tests
- baseline report generation

## Phase 5 — Export and CLI

Expose results through JSON export and a CLI entry point.

Outputs:

- JSON exporter
- CLI command
- CLI tests

## Phase 6 — Basic UI

Add a simple terminal UI using the same application flow.

Outputs:

- terminal UI
- shared application integration

## Phase 7 — Real TESTAR ingestion

Support TESTAR JSON imports through a dedicated importer.

Outputs:

- TESTAR state model importer
- importer detection
- TESTAR ingestion tests

## Phase 8 — Real requirements input

Support real requirements input using the structured ReqTrace requirements format.

Outputs:

- TbUIS requirements input
- real input loading tests

## Phase 9 — Extensibility and real-model integration

Stabilize extension points and connect the prototype to real SUT assets and real TESTAR output.

Outputs:

- importer registries
- analyzer registries
- preserved baseline analyzer
- additional analyzer support
- SUT asset structure
- real-model analysis runs
- stable JSON report export
- repository cleanup and tooling baseline

## Phase 10 — Evaluation and refinement

Evaluate analyzer behavior on real models and improve coverage quality.

Outputs:

- analyzer comparisons on real models
- matching improvements
- evidence refinements
- clearer false positive and false negative handling
- thesis-ready evaluation outputs

## Phase 11 — Thesis completion assets

Prepare the repository for final thesis delivery.

Outputs:

- final evaluation artifacts
- final figures and tables
- final thesis materials
- final presentation materials if needed
