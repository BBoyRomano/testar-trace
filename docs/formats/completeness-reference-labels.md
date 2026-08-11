# Completeness reference labels JSON

The TESTAR Trace CLI `compare` command consumes independently curated expected
completeness labels. These labels are benchmark inputs, not output copied from a
traceability method.

## Format

```json
{
  "schema_version": 1,
  "labels": [
    {
      "scope_kind": "requirement",
      "scope_id": "UC-01",
      "completeness": "complete"
    },
    {
      "scope_kind": "path",
      "scope_id": "UC-01:flow:path:alternative-1",
      "completeness": "incomplete"
    }
  ]
}
```

Each `scope_kind` and `scope_id` pair must be unique and must resolve to a
collection-level assessment produced by every compared method.
Unknown top-level or label fields are rejected so misspelled labels cannot be
silently accepted.

Supported completeness classes are:

- `complete`;
- `incomplete`;
- `not-assessable`.

Supported individual scope kinds are `requirement`, `flow`, `branch`, and
`path`. Requirement and path labels are recommended for the standard evaluation
protocol.

## Review provenance

The versioned interchange format deliberately contains only adjudicated labels.
Store reviewer identities, review rounds, disagreements, source evidence, and
adjudication records in adjacent benchmark documentation or a separately
controlled review artifact. Do not tune methods against the held-out label file.

See [Completeness-method accuracy](../evaluation/method-accuracy.md) for required
evaluation safeguards and interpretation limits.
