# TESTAR Trace Adapters

`testar-trace-adapters` is the optional external-input package for TESTAR
Trace. It reads supported artifacts and converts them into the canonical domain
models from `testar-trace`.

Applications may omit this package and construct `RequirementSet`, `StateModel`,
and `StateModelCollection` values directly with their own loading logic.

## Built-in adapters

The package currently provides:

- JSON and Markdown use cases;
- JSON user stories;
- Gherkin feature files;
- TESTAR Trace formal-requirements JSON;
- TESTAR state-model JSON exports.

Use-case sources are mapped through private, format-specific models before the
authored main, alternative, and rejoining flows are converted into the core
requirement graph. Each Gherkin scenario is retained as one complete flow. Core,
not the adapters, materializes complete requirement paths.

Markdown use cases retain their authored block in `Requirement.body`. Explicit
section values, including `N/A`, remain available in requirement metadata; an
absent section is therefore distinguishable from an authored not-applicable
value.

The formal-requirements format is a complete canonical authoring input rather
than an alternative domain model. Its adapter constructs the same
`RequirementSet` as the natural-language adapters and attaches reviewed
observables and element bindings for exact conformance checking. See the
[format reference](../../docs/formats/formal-requirements.md).

## Loading

One requirements artifact may contain one or many requirements. Loading one or
many such artifacts always returns one `RequirementSet`:

```python
from testar_trace_adapters import load_requirements

requirements = load_requirements(
    "requirements",
    pattern="*.json",
    adapter="use-case",
)
```

Each state-model artifact must contain exactly one model. Loading one or many
artifacts returns one `StateModelCollection`:

```python
from testar_trace_adapters import load_state_models

state_models = load_state_models(
    "evidence",
    pattern="*.json",
    adapter="testar",
)
```

Canonical state-model entity identifiers are qualified by model identifier so
they remain globally unique in a collection. Original TESTAR identifiers remain
available through `SourceRef.native_id`.

## In-memory and custom sources

Browser, API, and already-decoded inputs can be supplied as `SourceArtifact`
values. A custom synchronous source can implement the structural `Source`
protocol and return one or more artifacts from `read()`.

```python
from testar_trace_adapters import SourceArtifact, load_requirements

requirements = load_requirements(
    SourceArtifact(
        id="jira-project",
        name="jira-project.json",
        data=jira_issue_data,
        format="jira",
    ),
    adapter="jira",
    registry=registry,
)
```

Network authentication and asynchronous fetching remain the caller's
responsibility. The registered adapter converts the fetched source data into a
core model.

## Custom adapters

Registries are explicit instances and have no import-time side effects:

```python
from testar_trace.domain.requirements import RequirementSet
from testar_trace_adapters import Adapter, create_builtin_adapter_registry

registry = create_builtin_adapter_registry()
registry.register_requirement(
    Adapter[RequirementSet](
        id="jira",
        name="Jira requirements",
        formats=("jira",),
        adapt=parse_jira_requirements,
    )
)
```

Requirement adapters return a `RequirementSet`. State-model adapters return
exactly one `StateModel`; the loader constructs the final collection.

## Gherkin scope

The built-in Gherkin adapter supports features, tags, backgrounds, scenarios,
scenario outlines/templates, examples, and Given/When/Then/And/But steps.
Unsupported constructs such as Rule blocks, doc strings, and step data tables
are rejected explicitly rather than silently ignored.

## Status

TESTAR Trace is under active development. The public Python API is not yet
stable.
