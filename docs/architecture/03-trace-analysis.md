# Trace analysis

The application layer currently exposes two traceability methods:

- `baseline`
- `candidate_match`

## Baseline

`baseline` is a control method. It executes the full application pipeline and returns valid result
objects without attempting real traceability inference.

## Candidate match

`candidate_match` is the first real traceability method.

Its purpose is to:

1. take requirement fragments from the application request
2. build searchable evidence candidates from canonical evidence objects
3. score fragment-to-candidate matches
4. keep the best-supported fragment matches
5. aggregate fragment results to requirement-level coverage and confidence

### What it includes

`candidate_match` includes all fragment kinds as candidate-matching inputs, including:

- preconditions
- main steps
- alternate steps
- postconditions

### What it does not prove

`candidate_match` does **not** prove that the requirement is realized as a coherent ordered execution
path through the state model.

In particular, it does not yet prove:

- that all main steps are realized in order
- that alternate flows are realized as complete alternate paths
- that preconditions hold at the correct entry context
- that postconditions hold at the correct resulting context

Those concerns belong to a later flow/path-aware method.

## Planned next method

The next major method should be a flow/path-oriented method, for example `flow_match`, which uses
the structured requirement flow and the state-model transitions to reason about ordered realization.
