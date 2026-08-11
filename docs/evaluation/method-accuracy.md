# Completeness-method accuracy

Accuracy is an empirical property of a method on a defined population. It
cannot be inferred from successful execution or from agreement between two
methods.

## Reference data

Create reference labels independently from method output. For each requirement,
requirement path and state-model collection, reviewers should record:

- the expected completeness class: `complete`, `incomplete`, or
  `not-assessable`;
- the expected evidence basis: graph-supported or recorded execution;
- the expected ordered transition or execution-step identifiers where a path is
  complete;
- a rationale and reviewer identity or review round;
- disagreements and their adjudicated resolution.

Use at least two reviewers for a publishable evaluation and report inter-rater
agreement before adjudication. Do not tune thresholds on the final test set.

## Data split

Separate benchmark cases by SUT or feature family, not by individual path, so
near-duplicate labels and GUI text do not leak between partitions.

1. **Development set:** inspect failures and tune normalization, thresholds and
   bounds.
2. **Validation set:** choose among candidate configurations.
3. **Held-out test set:** report final results once, without further tuning.

## Metrics

Report more than overall accuracy because an imbalanced benchmark can make a
method that predicts only `incomplete` appear strong.

- exact three-class accuracy;
- per-class precision, recall and F1;
- macro F1;
- confusion matrix;
- assessability rate;
- path-level exact match;
- route exact match or ordered-overlap score when reference routes exist;
- analysis time and peak memory.

Evaluate graph-supported and observed-execution claims separately. Treating
`not-assessable` as `incomplete` hides missing evidence and invalidates the
comparison.

Evaluate formal conformance separately from natural-language alignment. Review
the translation and observable bindings independently, and report both
formalization defects and checker defects. Otherwise a perfectly implemented
checker can appear inaccurate because its input specification was wrong.

The CLI can compute the classification metrics and confusion matrices from a
versioned reference-label file:

```text
uv run testar-trace compare \
  --requirements requirements.md \
  --state-models model.json \
  --labels completeness-labels.json \
  --method graph-alignment \
  --method execution-alignment
```

See [Completeness reference labels](../formats/completeness-reference-labels.md)
for the input schema. The command automates metric calculation; it does not
replace independent labeling, adjudication, data splitting, or error analysis.

## Claim threshold

A result of 100 percent on a finite held-out benchmark means only that no error
was observed in that benchmark. It is not a proof of perfect accuracy for new
natural-language requirements or state models. Formal conformance can provide
an exact result for its finite-path semantics, but does not establish that the
formalization faithfully captures the original natural-language intent.
Broader proof-level claims would additionally require validated temporal
properties, verified proposition mappings, an adequate state model, and a sound
exhaustive verification procedure.
