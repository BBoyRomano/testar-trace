# Architecture

## Purpose

This project analyzes whether requirements appear to have been exercised in a TESTAR-generated application state model and reports evidence-based coverage results.

## Core idea

External artifacts should be treated as unstable. Internal analysis models should be treated as stable.

TESTAR exports, requirements documents, and report formats may change over time. The analysis should therefore operate on canonical internal models rather than directly on external file structures.

## System parts

### Ingestion

Reads external artifacts, identifies their kind and version, validates their structure, and translates them into canonical internal models.

Input families:
- state model artifacts
- requirements artifacts

### Domain

Defines the canonical internal models used by analysis.

Core concepts:
- state graph
- state observation
- requirement catalog
- requirement
- requirement unit
- match evidence
- coverage result

### Application

Orchestrates the analysis flow between ingestion, analysis, presentation, and export.

### Analysis

Matches requirements against the state graph and produces explainable coverage results.

Outputs include:
- requirement status
- supporting evidence
- summary metrics

### Presentation

Presents results through user-facing interfaces.

Planned interfaces:
- CLI first
- UI later

### Export

Writes coverage results to external output formats.

## Dependency direction

Dependencies should point inward toward the domain and analysis core.

Preferred direction:
- presentation depends on application
- export depends on application
- application depends on ingestion, analysis, and domain
- ingestion depends on domain
- analysis depends on domain
- domain depends on nothing outside the domain

## Architectural principles

- Keep analysis independent from external file formats and schemas.
- Translate external artifacts into canonical internal models before matching.
- Prefer explainable evidence over opaque scoring.
- Share one analysis pipeline across CLI and UI.
- Add extensibility through clear boundaries, not premature abstraction.

## Open areas

The following are expected to evolve:
- exact TESTAR import details
- exact requirements import details
- matching and scoring strategy
- export formats
- UI structure
