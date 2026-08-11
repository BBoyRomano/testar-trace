# Formal automata conformance

## Purpose

`automata-conformance` determines model-checked completeness for requirements
whose observable semantics have been explicitly authored and approved. It
answers this bounded question:

> Does every finite requirement path have an accepted, connected route through at
> least one supplied state model under the declared conformance policy?

The web interface presents this method as **Formal check**. The shorter label is
presentation copy; the stable method identifier remains
`automata-conformance`.

## Method

1. Materialize every complete requirement path, including alternatives.
2. Replace each requirement element with its approved observable binding.
3. Treat the required observable sequence as a finite automaton.
4. Search the product of that automaton and each state-model labelled transition
   system with deterministic breadth-first traversal.
5. Accept a model occurrence only when every observable is matched in order on
   one connected route. Optional intervening transitions are controlled and
   bounded by the authored policy.
6. Mark a requirement complete only when materialization is exhaustive and all
   its requirement paths have a full accepted occurrence.

Selectors are exact, deterministic predicates over action, transition, state,
and widget fields. Predicates within one selector are combined with AND;
alternative selectors for one observable are combined with OR. Comparison is
case-insensitive by default and supports only `equals` and `contains`.

## Assessability

The method reports `not-assessable` when:

- no formalization is attached;
- its status is `draft`; or
- any element in a materialized path lacks an observable binding.

These conditions are not evidence that the requirement is incomplete. They
mean the exact checker lacks an approved proposition mapping.

## Guarantees and limitations

The search is deterministic and exact for the declared finite-path semantics.
It does not use similarity thresholds, an LLM, or probabilistic classification.
That supports a stronger conclusion than natural-language alignment, but not an
unconditional claim of 100% real-world accuracy. The result still depends on:

- faithful formalization of the original requirement;
- correct and complete observable bindings;
- a state model that adequately represents the SUT;
- the chosen start and intervening-transition policy; and
- exhaustive finite path materialization.

General temporal properties such as liveness, unbounded recurrence, timing, or
data constraints are outside this first method. They should be added only with
a deliberately versioned property language and checker semantics rather than
being inferred silently from prose.
