# Architecture

## Purpose

ReqTrace analyzes whether requirements appear to have been exercised in a TESTAR-generated application state model and reports evidence-based coverage results.

## Core idea

External inputs are unstable.

TESTAR exports, requirements sources, and report formats may change over time. ReqTrace should translate external inputs into canonical internal models before analysis.

## Structure

ReqTrace is organized around five parts:

- `ingest/` reads external artifacts and translates them into canonical internal models
- `domain/` defines the canonical models used by the application
- `analysis/` evaluates requirements against the state graph
- `export/` writes coverage results to external formats
- `presentation/` exposes the application through CLI and UI entry points

## Dependency direction

Dependencies point inward.

Preferred direction:

- `presentation` depends on `application` and `domain`
- `export` depends on `domain`
- `application` depends on `analysis`, `domain`, `export`, and `ingest`
- `analysis` depends on `domain`
- `ingest` depends on `domain`
- `domain` depends on nothing else in the project

## Analysis model

Analysis is strategy-based.

Different analyzers may evaluate the same canonical models in different ways. Analyzer differences are analysis concerns, not ingestion or domain concerns.

## Architectural principles

- Translate external artifacts before analysis
- Keep canonical models independent from source formats
- Keep analysis strategies replaceable
- Prefer explicit evidence over opaque scoring
- Share one application flow across CLI and UI
- Add extension points only where change is expected

## Current extension points

Current extension points are:

- state model importers
- requirements importers
- analyzers
- exporters

## Current focus

The current focus is improving real-model analysis quality while preserving a stable and extensible project structure.
