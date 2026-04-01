# Candidate match method

## Purpose

`candidate_match` is a fragment-level evidence retrieval and scoring method.

It is intended to answer:

- what evidence candidates plausibly support each requirement fragment?
- how strong is that support?
- what requirement-level coverage/confidence follows from those fragment-level matches?

It is **not** intended to prove that all requirement steps are realized as one coherent trace.

## Inputs

The method operates on the standard application request:

- requirements snapshot
- evidence snapshot
- selected requirement IDs (optional)
- selected evidence run IDs (optional)

## Evidence space

The method currently builds candidates from canonical evidence objects:

- application states
- UI elements
- actions
- transitions

## Fragment coverage

The method includes all fragment kinds:

- preconditions
- main steps
- alternate steps
- postconditions

It scores them independently and aggregates them at requirement level.

## Output

The method produces:

- fragment-level coverage assessments
- requirement-level coverage assessments
- trace links
- supporting trace evidence
- aggregate summary metrics

## Boundary of the method

`candidate_match` stops at candidate retrieval and scoring.

It does not yet perform:

- ordered step/path realization
- transition chain validation across the whole use case
- main vs alternate flow path reporting
- explicit precondition/postcondition context reasoning
