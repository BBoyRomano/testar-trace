# Analyzers

## Purpose

This document defines the analyzer set used by ReqTrace.

Its purpose is to keep the analyzer family small, distinct, and methodologically clear.

ReqTrace should not accumulate analyzers that differ only accidentally or experimentally. Each analyzer should represent a recognizable method with a clear role.

## Design principles

### 1. Each analyzer should have a distinct purpose

An analyzer should exist because it represents a meaningful analysis method, not just because it was easy to prototype.

### 2. Names should describe methods

Analyzer names should communicate what the method does.

### 3. The analyzer set should stay small

It is better to keep a few analyzers with clearly different purposes than many overlapping variants.

### 4. The main direction is step traceability

The long-term goal is not simple keyword overlap.

The main direction is to trace requirement units, especially steps, to concrete states and transitions in the GUI state model, and to report exactly where they were found.

## Current analyzer roles

## 1. Lexical baseline

### Current name
`keyword_v1`

### Intended role
Baseline only

### Purpose
Provide the simplest requirement-analysis baseline using lexical overlap.

### Strengths
- simple
- fast
- easy to understand
- useful as a baseline for comparison

### Weaknesses
- weak semantics
- sensitive to wording
- not path-aware
- not a strong traceability method

### Recommended future name
`lexical_baseline_v1`

## 2. Evidence matching

### Current name
`evidence_v1`

### Intended role
Intermediate method

### Purpose
Match requirement units to evidence in a more structured way than the lexical baseline.

This method should focus on:
- unit-level evidence collection
- better explanations
- more structured matching by requirement-unit role

### Strengths
- more explainable than the lexical baseline
- better foundation for richer methods

### Weaknesses
- still not enough on its own for strong traceability claims
- may still be mostly local and text-driven

### Recommended future name
`evidence_matching_v1`

## 3. Occurrence mapping

### Current name
`occurrence_v1`

### Intended role
Intermediate method

### Purpose
Group matched requirement evidence into concrete occurrences in the model.

This method should answer:
- where does this requirement appear?
- how many times does it appear?
- which requirement units appear in each occurrence?

### Strengths
- supports requirement-to-model navigation
- more useful than isolated evidence matches

### Weaknesses
- can still be weak if occurrences are not constrained by path structure
- may not respect step order strongly enough

### Recommended future name
`occurrence_mapping_v1`

## 4. Path-based step tracing

### Current names related to this idea
- `path_occurrence_v1`
- `ordered_path_v1`

### Intended role
Main method direction

### Purpose
Trace requirement steps to coherent, connected evidence in the state model.

This method should:
- match requirement steps to state and transition evidence
- preserve ordering where relevant
- group evidence into connected traces
- report partial traces and missing steps
- show exactly where a requirement is present in the model

### Strengths
- closest to real requirements traceability
- structurally stronger than local matching
- aligns with the main goal of the project

### Weaknesses
- more complex than the baseline methods
- requires clearer rules for matching, connectivity, ordering, and branch handling

### Recommended future name
`step_trace_v1`

## Recommended analyzer set

The preferred analyzer set is:

- `keyword_v1` as the lexical baseline
- `evidence_v1` as the evidence-oriented intermediate method
- `occurrence_v1` as the occurrence-oriented intermediate method
- a future consolidated main method: `step_trace_v1`

## Recommended cleanup direction

### Keep
- `keyword_v1`
- `evidence_v1`
- `occurrence_v1`

### Redesign and merge
- `path_occurrence_v1`
- `ordered_path_v1`

These should likely converge into one clearer analyzer:
- `step_trace_v1`

## Why `step_trace_v1` is the best main name

`step_trace_v1` clearly communicates:
- the main unit is the requirement step
- the goal is traceability
- the method builds traces through the state model

It is clearer and more defensible than names based on incidental implementation detail.

## Method distinctions to preserve

### Lexical baseline
How much local lexical overlap exists?

### Evidence matching
What evidence exists for each requirement unit?

### Occurrence mapping
Where does this requirement appear in the model?

### Step trace
Can the requirement steps be traced through a coherent path in the model?

## Current recommendation

For now:
- keep `keyword_v1` as the baseline
- keep `evidence_v1` as the structured refinement
- keep `occurrence_v1` while its role is still useful and distinct
- stop treating `path_occurrence_v1` and `ordered_path_v1` as final long-term names
- move the main method direction toward a cleaner `step_trace_v1`

## Next implementation direction

The next major analyzer step should be to design and implement `step_trace_v1` as the main thesis-direction method, rather than continuing to accumulate path-related variants with overlapping responsibilities.
