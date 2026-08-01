# Trace analysis

## Purpose

This document describes traceability methods in the application layer and their current status.

## Method status

- `baseline`: control method for pipeline sanity checks
- `candidate_match`: lexical retrieval comparator
- `flow_match`: ordered flow/path alignment method
- `hybrid_match`: ensemble method (flow-first with candidate fallback/enrichment)

Default service wiring now exposes all methods for direct CLI/desktop comparison.

## Method summary

### baseline

Control method.

- exercises the full pipeline end-to-end
- produces valid result contracts
- does not perform substantive matching

### candidate_match (experimental)

Fragment-level candidate retrieval and scoring.

- scores fragments against evidence candidates
- aggregates to requirement-level coverage
- useful for early retrieval-quality experiments

Limitations:

- does not strongly guarantee ordered full-flow realization
- not sufficient by itself to prove coherent end-to-end requirement execution

### flow_match (experimental)

Flow-aware matching across transitions and requirement-flow structure.

- attempts ordered alignment for flow fragments
- reports representative execution instances
- separates main/alternate flow outcomes

Limitations:

- still evolving for robust branch/path proof and confidence calibration

### hybrid_match

Flow-first ensemble that merges strengths of:

- `flow_match` for ordered execution evidence
- `candidate_match` for lexical fallback and evidence enrichment

## Canonical naming

Use traceability method as the standard term in docs and UI.

## Detailed method specs

- `trace-methods/baseline.md`
- `trace-methods/candidate-match.md`
- `trace-methods/flow-match.md`
- `trace-methods/hybrid-match.md`

