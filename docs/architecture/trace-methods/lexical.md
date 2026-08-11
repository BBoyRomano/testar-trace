# Lexical method

## Purpose

`lexical` is the first substantive traceability baseline. It independently
compares each canonical requirement element with textual state-model candidates
and retains every positive match at or above its retention threshold.

It produces unordered `TraceLink` values suitable for highlighting candidate
states, widgets, actions, and transitions. It deliberately produces no
`TraceOccurrence`, because lexical similarity alone does not establish an
ordered or connected requirement-path realization.

Each link refers to exactly one original state-model entity and carries its own
score. Context from related entities may contribute to that score—for example,
a transition candidate includes its action and endpoint text—but the resulting
link still targets only that transition. This keeps aggregation and highlighting
unambiguous for applications.

## Scoring

The initial scorer is deterministic token-frequency cosine similarity:

```text
score = dot(requirement tokens, candidate tokens)
        / (requirement norm * candidate norm)
```

Text is Unicode-normalized with NFKC, case-folded, and tokenized into Unicode
letter and number sequences. The initial version performs no stemming,
lemmatization, synonym expansion, or language-specific stop-word removal.

The scorer and its version are recorded as `token-frequency-cosine-v1`.

## Candidate space

Candidates use canonical fields only:

- state name, title, and URL;
- widget text, title, role, tag name, and link target;
- action description, value, and target-widget text;
- transition action/widget text and source/target state text.

Arbitrary adapter metadata is excluded from scoring.

## Configuration

`LexicalConfig` currently exposes:

- `retention_threshold`, default `0.0`.

Only positive scores are evidence, so zero-score candidates are omitted even at
the default threshold. The retention threshold controls result size and is not
a presentation setting. Applications remain free to apply a higher display
threshold or a colour scale without rerunning the analysis.

`LexicalMethod` is a configured callable that can be passed directly to
`analyze_traceability`. The built-in registry exposes the default configuration
under the stable method identifier `lexical`.

## Coverage and limitations

Coverage assessments report the proportion of unique requirement elements for
which at least one retained lexical candidate exists. Assessments are emitted
for requirement-set, requirement, flow, branch, and resolved-path scopes, both
per model and across the supplied model collection.

Completeness is always `not-assessable` for this method. Independent lexical
matches do not prove ordering, connectivity, divergence, rejoining,
termination, or one coherent execution route.
