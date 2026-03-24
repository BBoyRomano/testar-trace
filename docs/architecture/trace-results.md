# Trace results

## Purpose

This document defines the intended result shape for traceability findings in ReqTrace.

A requirement result should be more informative than a single top-level status. ReqTrace should support:
- exact findings
- partial findings
- multiple occurrences
- step-level evidence
- drill-down to concrete model locations

## Why this is needed

A requirement may be:
- found exactly once
- found multiple times
- found only partially
- supported by local evidence that does not form a complete occurrence

A flat summary is not enough to represent that properly.

## Result levels

ReqTrace results should support four levels.

### 1. Requirement level

This is the top-level result for a requirement.

It answers:
- was the requirement found
- was it partially found
- was it not found

A requirement-level result should also summarize:
- unit results
- occurrences
- metadata

### 2. Occurrence level

This represents one concrete occurrence of the requirement in the model.

An occurrence should be able to capture:
- the states involved
- the transitions involved
- the matched requirement units or steps
- whether the occurrence is complete or partial
- which units are missing if partial

A requirement may have zero, one, or many occurrences.

### 3. Step or unit level

This represents the result for an individual requirement unit.

A unit result should be able to capture:
- whether it was found, partially found, or not found
- the evidence supporting that finding
- the exact states, transitions, and observations that support it

Depending on the input format, units may correspond to:
- preconditions
- triggers
- steps
- postconditions
- alternative-flow units

### 4. Evidence level

This is the most concrete support for a finding.

Evidence should be able to capture:
- matched state ids
- matched transition ids
- matched observations
- explanation of the match
- matching metadata

## Intended navigation model

The intended navigation model is:

- requirement
  - occurrence
    - step or unit
      - evidence

This should support drill-down from a requirement to the exact model fragments that justify the result.

## Result expectations

## Requirement level should support
- overall status
- requirement id
- unit results
- occurrences
- metadata

## Occurrence level should support
- occurrence status
- matched unit ids
- state ids
- transition ids
- missing unit ids if partial
- metadata

## Step or unit level should support
- unit id
- unit status
- evidence list
- metadata

## Evidence level should support
- matched states
- matched transitions
- matched observations
- explanation
- metadata

## Partial findings

Partial findings are essential and should be represented explicitly.

A requirement can be partially found when:
- some important units are found but others are missing
- evidence exists but does not form a complete occurrence
- steps are found but structural coherence is weak
- a branch or subflow is found but the full requirement is not

A partial result should preserve:
- what was found
- what is missing
- where the supporting evidence appears

## Multiple occurrences

The same requirement may appear multiple times in a model.

ReqTrace should allow:
- zero occurrences
- one occurrence
- many occurrences

Each occurrence should be reported separately if it represents a distinct coherent finding.

## Current domain direction

ReqTrace should keep the result model rich enough for occurrence-based and step-based analyzers.

This means the result model should be ready to support:
- requirement-level summaries
- occurrence-level drill-down
- step-level drill-down
- evidence-level explanations

Even if some analyzers are simpler, the shared result shape should not block richer analyzers later.

## Practical design choice

ReqTrace should prefer a stable result shape that richer analyzers can use directly.

This avoids redesigning the reporting model every time the analyzers become more sophisticated.

## Recommended interpretation

### Baseline analyzers
May produce:
- requirement status
- unit status
- lightweight evidence
- no occurrences or only minimal occurrences

### Richer analyzers
Should produce:
- requirement status
- explicit occurrences
- step-level mapping
- state and transition references
- partial-trace reporting
- missing-step reporting

## Main reporting goal

The main reporting goal is:

From a requirement, the user should be able to navigate to the exact states, transitions, and observations that support the finding, and see which parts of the requirement were found, partially found, or not found.
