# Hybrid match method

## Purpose

`hybrid_match` combines ordered-flow alignment and lexical candidate retrieval.

It is intended as the current primary experimental method for thesis evaluation runs.

## Current status

- implemented in code
- treated as experimental (still under calibration)
- available in default CLI/GUI service wiring for direct comparison against other methods

## Current behavior

The method currently:

- runs flow-oriented matching as the primary path
- enriches/falls back with candidate-level lexical matching where useful
- aggregates links/evidence into requirement-level coverage and confidence outcomes
- reports representative execution instances for matched flows

## Current limits

The method does not yet guarantee:

- exhaustive graph-theoretic proof of all alternate branches
- final confidence calibration for all noisy state-model patterns
- full explainability UX parity with planned interactive graph views
