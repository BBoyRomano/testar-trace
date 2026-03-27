# Analysis approaches

## Purpose

This document summarizes the main analysis approaches that ReqTrace can use to establish trace links between requirements and GUI state models.

ReqTrace does not fix a single final analysis approach at this stage. Multiple analyzers are supported so they can be evaluated and refined as the project develops.

## Current position

ReqTrace keeps analyzers as replaceable strategies.

This means:
- ingestion translates external artifacts into canonical internal models
- analyzers operate on canonical models
- different analyzers may use different trace-establishment logic
- analyzer comparison is part of the development and evaluation process

The project is not centered on plain keyword matching. The long-term direction is step-level traceability over the state model.

## Approach families

### 1. Lexical matching

Requirements are matched to states, transitions, and observations using textual overlap or simple lexical similarity.

Examples:
- keyword overlap
- token-based matching
- phrase overlap

Best use:
- baseline analysis
- candidate retrieval
- sanity checks

Main limitation:
- lexical overlap alone does not show that a requirement was actually exercised as a coherent behavior

### 2. Typed evidence mapping

Requirement units are matched differently depending on their role.

Examples:
- preconditions matched mainly to states
- triggers matched mainly to actions or transitions
- postconditions matched mainly to resulting states or messages

Best use:
- more structured evidence collection
- step-level explainability
- better precision than plain lexical matching

Main limitation:
- still does not by itself prove a coherent requirement occurrence or path

### 3. Occurrence mapping

Matched requirement-unit evidence is grouped into one or more concrete occurrences in the model.

Best use:
- showing where a requirement appears
- supporting multiple findings of the same requirement
- showing partial findings with grouped evidence

Main limitation:
- grouping alone can still be weak if it is not constrained by path structure

### 4. Path or sequence alignment

A requirement is treated as an ordered set of steps or units, and the analyzer searches for matching connected paths through the model.

Best use:
- requirement step traceability
- partial trace reporting
- stronger structural claims than local matching
- mapping requirement steps directly to states and transitions

Main limitation:
- requires stronger abstractions for step matching, ordering, and connectivity

### 5. Graph or pattern matching

Requirements are represented as structured graph or path fragments and matched against the state graph.

Best use:
- richer structural traceability
- explicit handling of order and branching

Main limitation:
- more complex to design and tune

### 6. Semantic-assisted matching

Semantic methods are used to improve retrieval or ranking.

Examples:
- semantic similarity
- embeddings
- LLM-assisted candidate ranking

Best use:
- synonym handling
- wording variation
- recall improvement

Main limitation:
- semantic similarity alone is not sufficient as trace evidence and should support explicit trace construction rather than replace it

## Recommended direction

The recommended direction is a layered strategy:

1. candidate retrieval
2. typed evidence mapping
3. occurrence or path construction

This supports gradual improvement while keeping analyzers comparable.

## Practical interpretation for ReqTrace

ReqTrace should eventually support:
- full requirement findings
- partial requirement findings
- multiple occurrences of the same requirement
- step-level evidence
- navigation from a requirement to the exact states, transitions, and observations that support the finding

## Current practical decision

For now:
- keep a simple lexical baseline
- keep a more structured evidence-oriented method
- move the main development direction toward occurrence and step-trace analysis
- delay final analyzer selection until the methods are clearer and better evaluated
