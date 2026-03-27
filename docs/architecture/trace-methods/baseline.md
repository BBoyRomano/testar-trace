# Baseline traceability method

## Purpose

The baseline method is a complete runnable traceability method.

It exists to get the program running end to end before any real traceability logic is implemented.

It supports:
- method selection
- run creation
- requirement iteration
- valid result generation
- valid coverage generation
- progress integration
- reporting and presentation integration

It does not attempt to infer meaningful requirement-to-evidence links.

## Placement

Recommended implementation location:

```text
src/
  reqtrace/
    application/
      methods/
        baseline.py
```

Recommended implementation name:
- `BaselineMethod`

The method is selected by the application service like any other traceability method.

## Inputs

The baseline method accepts the standard application request inputs:
- requirements snapshot
- evidence snapshot
- optional selected requirement ids or scopes
- optional selected evidence scope
- optional runtime metadata

The baseline method may ignore some optional selection fields when they are not yet meaningful, but that behavior should be explicit and test-backed.

## Execution model

```text
start run
-> load selected requirements and evidence
-> iterate selected requirements
   -> mark requirement as analyzing if live progress is available
   -> inspect requirement artifact and fragments
   -> produce baseline result for the requirement
   -> mark requirement as done
-> finalize run
-> return result
```

## Processing behavior

For each selected requirement, the baseline method should:
1. read the requirement artifact
2. inspect its fragments if fragments exist
3. produce a valid requirement-level result
4. produce valid fragment-level coverage records where applicable
5. emit progress updates where live progress is supported

The baseline method may count evidence items or expose simple metadata for debugging, but it should not perform real matching.

## Progress behavior

If the application supports live progress updates, the baseline method should cooperate with that contract.

Per requirement, it should support statuses such as:
- `pending`
- `analyzing`
- `done`
- `failed`

The baseline method does not need to simulate traceability findings. It should simply provide stable, honest execution updates.

## Result behavior

The baseline method must return the same result shape expected from all other traceability methods.

### Trace links
Recommended behavior:
- return no resolved trace links

### Coverage
The method should still generate coverage results.

Recommended default values:
- requirement artifact coverage: `uncovered`
- requirement fragment coverage: `uncovered`
- `coverage_ratio = 0.0` where ratios are required
- `confidence_ratio = None`
- `covered_fragment_count = 0`
- `supporting_run_count = 0`

### Summary
The method should still return valid run-level summary values such as:
- requirement count
- analyzed requirement count
- uncovered requirement count
- requirement fragment count where available
- trace-link count = 0
- supporting-evidence count = 0 where available

## Error handling

Recommended behavior:
- mark the affected requirement as `failed` if requirement-level processing fails
- continue processing other requirements where possible
- finalize the run with an appropriate overall status
- return valid partial output if partial output is supported

## Reporting behavior

The baseline method must integrate with the normal reporting flow.

Its output should be usable by:
- GUI result views
- CLI summaries
- JSON and other export projections

The baseline method should also make it clear that no real traceability inference was performed.

## Intended use

The baseline method is intended for:
- initial end-to-end execution
- integration of ingestion, domain, application, and presentation
- validation of progress updates
- validation of result contracts
- validation of method selection
- early GUI and CLI development
- early export and reporting development

## Limitations

The baseline method:
- does not perform trace matching
- does not score evidence relevance
- does not resolve real trace links
- should not be interpreted as a meaningful coverage-analysis method

Its value is operational, not analytical.
