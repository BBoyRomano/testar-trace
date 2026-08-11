# Graph path alignment

## Purpose

`graph-alignment` determines model-supported requirements completeness. It is
the default practical completeness method for TESTAR exports that contain a
state graph but no chronological execution sequences.

The method answers this bounded question:

> Does every requirement path have a semantically corresponding, ordered and
> connected route in at least one supplied state model?

It does not claim that the route was observed in one TESTAR execution.

## Method

1. Materialize all complete requirement paths, including explicit alternatives.
2. Build focused semantic facets for every transition: its action, action target,
   source and target states, and individual source and target widgets.
3. Normalize UI-oriented language deterministically and score requirement
   elements with smoothed inverse-document-frequency weights and an F2 score.
   Evidence roles are constrained by requirement semantics: conditions use
   source-state evidence, triggers use actions, postconditions use target-state
   evidence, and flow steps may use either an action or its observable result.
4. Retain the strongest candidates above the configured threshold.
5. Preserve the exact semantic evidence target for each match: action, widget,
   source or target state. The transition remains part of the connected route.
6. Use dynamic programming to find the longest ordered alignment whose matched
   transitions are connected by graph traversal. One atomic transition may
   support its source condition, action and target condition, but one action is
   not reused as multiple independent executable steps. A trigger may share its
   action with the immediately following flow step because use-case formats
   commonly repeat that triggering action as main step 1.
7. Assess each path independently. A collection may use different models for
   different paths, but one path is never stitched across models.
8. Mark a requirement complete only when path materialization is exhaustive and
   every requirement path has one full coherent occurrence.

The implementation is deterministic. Candidate ordering, graph traversal, tie
breaking and emitted identifiers are stable.

## Configuration

- `similarity_threshold` (default `0.30`): minimum semantic score.
- `maximum_candidates_per_element` (default `12`): bounds candidate search.
- `maximum_intervening_transitions` (default `12`): bounds graph connectors
  between matched transitions.

These values are initial operating defaults, not empirically calibrated claims.
Tune them only against a separate labeled development set, then report accuracy
on a held-out test set.

## Interpretation and limitations

- `complete` means model-supported completeness, not observed test execution.
- `incomplete` means at least one assessable requirement path lacks a full coherent
  alignment.
- `not-assessable` is returned when requirement paths cannot be materialized
  exhaustively or no state-model input can assess them.
- Semantic matching can produce false positives or false negatives. Natural
  language and GUI labels are not formal specifications.
- Requirement-element kinds must be normalized by an adapter for role-aware
  matching. Unknown kinds retain the general semantic fallback.
- Intervening transitions are permitted because state models often contain
  implementation navigation that is absent from requirements.

The graph constraint follows the general labelled-transition-system view used
in model-based conformance testing. The semantic correspondence layer is a
project-specific deterministic heuristic and must be validated empirically.

## Research basis

- Jan Tretmans, *Conformance Testing with Labelled Transition Systems:
  Implementation Relations and Test Generation* (1996),
  <https://doi.org/10.1016/S0169-7552(96)00017-7>.
- Sebastiaan van Zelst et al., *Computing Alignments of Event Data and Process
  Models* (2018), <https://doi.org/10.1007/s12599-017-0501-x>.
