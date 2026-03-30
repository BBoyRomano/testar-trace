# Heuristic traceability method

## Purpose

The heuristic method is the first real deterministic traceability method in the prototype.

It matches requirement fragments against canonical evidence using lexical, structural, and UI/action cues.

## Inputs

The method consumes the standard application request:
- requirement snapshots
- evidence snapshots
- optional requirement selection
- optional evidence-run selection

It does not parse source files directly.

## Current behavior

The method currently:
- builds evidence candidates from states, elements, actions, and transitions
- normalizes requirement-fragment text into matching terms
- scores candidates using lexical overlap and simple structural cues
- applies conservative thresholds to classify fragments as:
  - covered
  - partially covered
  - uncertain
  - uncovered
- aggregates fragment results into requirement-level coverage and trace links

## Design goals

The method is intentionally:
- deterministic
- explainable
- lightweight
- compatible with the current TESTAR evidence model

## Current limitations

The method does not yet perform:
- full multi-step path reconstruction
- true application-level run progress updates
- semantic embedding or LLM-based reasoning

It should be treated as heuristic v1: useful for evaluation and refinement, not a final traceability algorithm.
