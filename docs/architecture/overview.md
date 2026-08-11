# Architecture Overview

TESTAR Trace compares canonical requirements with canonical state models generated
by TESTAR. External formats are converted before core analysis starts.

```text
requirement source(s) -> requirement adapters -> RequirementSet ---------+
                                                                        |
state-model source(s) -> state-model adapters -> StateModelCollection --+-> core analysis
                                                                        |
                                                    traceability method -+
```

## Package boundaries

`packages/core` owns immutable canonical models, requirement-path
materialization, traceability-method registration, built-in methods, progress,
and source-agnostic analysis. It has no file, network, browser, UI, or
external-format knowledge.

`packages/adapters` owns source access, format detection, parsing, and conversion
to core models. One requirements artifact can produce one or many requirements;
one state-model artifact produces exactly one state model. The loaders combine
one or many artifacts into the aggregate models consumed by core.

`apps` owns user interaction, runtime composition, elapsed time and timestamps,
worker messages, persistence, reports, and visualization. The web app runs the
same Python packages locally in a Pyodide Web Worker.

The dependency direction is strict:

```text
apps ------> adapters ------> core
  +-------------------------> core
```

Core never imports adapters or an application.

## Canonical requirements

A `RequirementSet` contains documents, requirements, requirement elements, and
authored flow graphs. A `RequirementFlow` owns named main, alternative, and
exception branches; occurrence nodes; and explicit next, branch, rejoin, and
repeat edges. Reusing an element in multiple nodes preserves the element's
semantic identity without collapsing distinct occurrences.

Core derives `RequirementPath` values by bounded deterministic graph traversal.
Each path contains every applicable element: shared constraints and
preconditions, the trigger, the main-flow prefix before divergence, branch
elements, any explicitly resumed main-flow suffix, later compatible branches,
and an explicit terminal outcome. Path identifiers are stable for the same edge
sequence. Traversal limits, unreachable graph content, and unterminated routes
are returned as diagnostics and are never silently treated as exhaustive.

Adapters interpret source-specific branch notation. Core validates references
and materializes deterministic paths; it does not parse Markdown, JSON, user
stories, or Gherkin.

Trace occurrences are scoped to exactly one requirement path and one state
model. Different paths may be supported by different models. Supporting
assessments can therefore be retained per model and also aggregated over a
`StateModelCollection` at path, branch, flow, requirement, and requirement-set
scope. A recorded execution sequence remains an explicit evidence basis and is
never conflated with a route inferred from the state-model graph.

## Canonical state models

A `StateModelCollection` contains one or more `StateModel` values. Each model
owns its states, widgets, actions, transitions, initial states, and optional
recorded `ExecutionSequence` values. Graph transitions and chronological
execution steps remain distinct concepts.

Every imported entity can retain a `SourceRef` with its original identifier,
container, source artifact, and location. Results can therefore refer back to
the original TESTAR entities without embedding visualization commands in core.

## App-facing results

A `TraceabilityResult` returns the path-materialization result used by the
analysis together with completeness assessments, trace links, and occurrences.

`CoverageAssessment` is the current reporting model for requirement-set,
requirement, flow, branch, and path scope. It keeps the primary completeness
conclusion separate from assessability and supporting coverage diagnostics, and
supports both per-model and collection-wide views.

A `TraceLink` assigns one score in the range `[0, 1]` to one canonical
state-model target for a requirement or requirement element. Methods can emit
continuous similarity scores or discrete values such as `0` and `1` without
changing the result shape. A lexical method uses independent, unordered links;
an application can filter or colour them with its own display threshold without
core prescribing presentation policy.

A `TraceOccurrence` identifies one ordered match of one requirement path within
one state model. Its ordered target references describe the connected route and
retain exact action, widget, state, and transition targets. Its link identifiers
connect direct evidence targets to their requirement elements and scores. This
lets an application distinguish an entire route, connector transitions, and the
direct evidence for one requirement element.

Applications resolve canonical target identifiers through the state model and
its source references. Core does not return colours, graph coordinates, or
other presentation instructions.

## Extension points

Registries are explicit instances, not process-global mutable state:

- `create_builtin_adapter_registry()` returns a new registry containing built-in
  requirement and state-model adapters;
- `create_builtin_method_registry()` returns a new registry containing built-in
  traceability methods;
- callers may add custom adapters or methods to their own registry, or pass a
  method callable directly to `analyze_traceability`.

Importing either package has no registration side effects. This makes native
applications, tests, and the browser worker independent and reproducible.

## Application responsibilities

Applications select sources, adapters, and methods; invoke analysis; bridge
progress and cancellation; measure runtime; serialize or persist results; and
render or highlight referenced state-model routes. Those responsibilities do
not move into core.
