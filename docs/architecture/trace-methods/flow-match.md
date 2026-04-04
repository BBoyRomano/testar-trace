# Flow match method

## Purpose

`flow_match` is an ordered flow-oriented traceability method.

It attempts to align requirement flow fragments with plausible ordered evidence sequences.

## Current status

- implemented in code
- treated as experimental in current architecture
- available in default CLI/GUI service wiring for comparison runs

## Current behavior

The method currently:

- retrieves evidence candidates for fragments
- aligns main-flow fragments in order
- applies continuity heuristics between adjacent selected candidates
- evaluates preconditions, alternate fragments, and postconditions separately

## Current limits

The method does not yet provide exhaustive graph-theoretic proof for:

- complete branch reachability
- exhaustive alternate-flow realization
- globally optimal path selection under all noisy trace conditions
