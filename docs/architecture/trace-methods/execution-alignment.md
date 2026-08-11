# Recorded-execution alignment

## Purpose

`execution-alignment` determines observed requirements completeness from
chronological execution sequences. It is stricter than graph alignment because
all elements of a requirement path must align in order within one recorded
execution sequence.

## Method

1. Materialize all complete requirement paths.
2. Build deterministic semantic facets for each recorded step from its linked
   transition, action or state.
3. Score requirement elements using the same weighted F2 semantic scorer as
   graph alignment.
4. Find the longest non-decreasing ordered alignment within each execution.
5. Select the strongest execution per requirement path.
6. Mark a requirement complete only when every exhaustively materialized path
   has a full occurrence in at least one model.

No path is stitched across executions or models. If a state model contains no
recorded sequences, the method returns `not-assessable` rather than treating
the unordered graph as an observed execution.

## Configuration

- `similarity_threshold` (default `0.30`): minimum semantic score.
- `maximum_candidates_per_element` (default `12`): bounds search per path
  element.

## Interpretation and limitations

- A full alignment establishes that corresponding steps were recorded in the
  required order. It does not prove the natural-language interpretation is
  correct.
- Missing recorded sequences are an evidence limitation, not evidence of
  incompleteness.
- Completeness for all alternatives requires recorded evidence for every
  materialized requirement path; one successful main flow is insufficient.
- Semantic thresholds require calibration on independently labeled data.

This is an alignment-based conformance check. Optimal alignments over process
models and event logs are commonly formulated as shortest-path problems over a
synchronous product; this implementation uses a bounded deterministic dynamic
program tailored to canonical TESTAR sequences.

## Research basis

- Massimiliano de Leoni, Fabrizio Maria Maggi and Wil van der Aalst, *Aligning
  Event Logs and Declarative Process Models for Conformance Checking* (2012),
  <https://doi.org/10.1007/978-3-642-32885-5_6>.
- Sebastiaan van Zelst et al., *Computing Alignments of Event Data and Process
  Models* (2018), <https://doi.org/10.1007/s12599-017-0501-x>.
