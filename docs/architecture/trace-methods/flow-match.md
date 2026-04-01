# Flow match method

## Purpose

`flow_match` is an ordered flow-oriented traceability method.

It is intended to answer:

- can the requirement's evidence anchors be aligned into a plausible ordered flow?
- how complete is that aligned flow?
- how coherent is the resulting sequence of states, actions, and transitions?

## Current behavior

The method currently:

- retrieves candidate evidence for all fragments
- aligns main-flow fragments in order
- applies simple continuity bonuses between adjacent chosen candidates
- evaluates preconditions, alternate steps, and postconditions separately

## Current limit

The method does not yet perform:

- exhaustive path search
- complete alternate-branch realization
- explicit graph-theoretic proof of flow reachability
