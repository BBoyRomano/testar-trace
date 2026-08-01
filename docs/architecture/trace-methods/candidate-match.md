# Candidate match method

## Purpose

`candidate_match` is a fragment-level evidence retrieval/scoring method.

It answers:

- which evidence candidates plausibly support each requirement fragment?
- how strong is that support?
- what requirement-level coverage follows from fragment-level matches?

## Current status

- implemented in code
- treated as experimental in current architecture
- available in default CLI/desktop service wiring for comparison runs

## Inputs

The method operates on the standard application request:

- requirements snapshot
- evidence snapshot
- selected requirement IDs (optional)
- selected evidence run IDs (optional)

## Evidence space

Current candidate space is built from canonical evidence objects:

- states
- UI elements
- actions
- transitions

## Output

The method produces:

- fragment-level coverage outcomes
- requirement-level coverage outcomes
- trace links and supporting trace evidence
- aggregate summary metrics

## Current limits

`candidate_match` does not fully guarantee:

- ordered end-to-end path realization for full use cases
- complete branch/alternate-flow realization proof
- strict precondition/postcondition context proof

