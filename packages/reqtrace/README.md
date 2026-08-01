# reqtrace

Core models and traceability analysis for ReqTrace.

`reqtrace` is the core Python package for representing requirements, execution evidence, and traceability analysis results. It contains canonical data models, trace method registration, progress/cancellation primitives, and the main analysis entry point.

This package intentionally stays independent from files, Jira, Azure DevOps, TESTAR parsing, CLIs, APIs, and user interfaces. External inputs should be loaded by packages such as `reqtrace-adapters`.

## Installation

```bash
pip install reqtrace
```

For local development from the repository:

```bash
uv sync
```

## Basic usage

```python
from reqtrace import analyze_traceability
from reqtrace.models.evidence import EvidenceArtifact, EvidenceSet
from reqtrace.models.requirements import RequirementArtifact, RequirementSet

requirements = RequirementSet(
    requirements=(
        RequirementArtifact(
            id="req-1",
            title="Login",
        ),
    ),
)

evidence = EvidenceSet(
    id="evidence-1",
    title="Evidence",
    artifacts=(
        EvidenceArtifact(
            id="artifact-1",
            title="Login evidence",
        ),
    ),
)

result = analyze_traceability(requirements, evidence)

print(result.id)
print(result.summary.total_requirements)
print(result.summary.uncovered_requirements)
```

By default, `analyze_traceability()` uses the built-in `noop` method. The no-op method does not create trace links. It exists so applications can validate that the analysis pipeline, result models, progress reporting, and cancellation wiring work correctly.

Use `method="sequence"` to search ordered evidence for full and partial requirement sequences:

```python
result = analyze_traceability(
    requirements,
    evidence,
    method="sequence",
)
```

## Core concepts

| Concept | Meaning |
| --- | --- |
| `RequirementSet` | Normalized requirements to analyze. |
| `RequirementScenario` | One traceable path through requirement fragments. |
| `EvidenceSet` | Normalized execution or test evidence. |
| `TraceabilityResult` | Output of one traceability analysis run. |
| `TraceabilitySummary` | Typed coverage/link counts for a result. |
| Trace method | Callable traceability algorithm registered by name. |
| `TraceContext` | Runtime context for progress, cancellation, and options. |

The normal flow is:

```text
RequirementSet + EvidenceSet -> trace method -> TraceabilityResult
```

## Progress and cancellation

Applications can receive progress events by passing a callback:

```python
from reqtrace import analyze_traceability
from reqtrace.progress import ProgressEvent

events: list[ProgressEvent] = []

result = analyze_traceability(
    requirements,
    evidence,
    progress=events.append,
)
```

Applications can request cooperative cancellation with `CancellationToken`:

```python
from reqtrace import analyze_traceability
from reqtrace.progress import CancellationToken

cancellation = CancellationToken()

result = analyze_traceability(
    requirements,
    evidence,
    cancellation=cancellation,
)
```

Trace methods should periodically call `context.raise_if_cancelled()` at natural boundaries such as before major phases or inside long loops.

## Registering trace methods

Custom trace methods can be registered with `register_trace_method()`.

A trace method receives a `RequirementSet`, an `EvidenceSet`, and a `TraceContext`, and returns a `TraceabilityResult`.

```python
from reqtrace import analyze_traceability, register_trace_method
from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.models.traceability import TraceabilityResult, TraceabilitySummary
from reqtrace.progress import TraceContext


def trace_with_custom_method(
    requirements: RequirementSet,
    evidence: EvidenceSet,
    context: TraceContext,
) -> TraceabilityResult:
    context.raise_if_cancelled()
    context.report("custom-method", message="Running custom trace method")

    total_requirements = len(requirements.requirements)

    return TraceabilityResult(
        id="custom",
        title="Custom traceability result",
        summary=TraceabilitySummary(
            total_requirements=total_requirements,
            covered_requirements=0,
            partially_covered_requirements=0,
            uncovered_requirements=total_requirements,
            total_links=0,
        ),
    )


register_trace_method("custom", trace_with_custom_method)

result = analyze_traceability(requirements, evidence, method="custom")
```

Use `replace=True` only when intentionally overwriting an existing method.

## Built-in methods

| Method | Description |
| --- | --- |
| `noop` | Returns an empty traceability result for smoke checks and wiring validation. |
| `sequence` | Finds ordered full and partial requirement sequences in execution evidence. |

## Relationship to `reqtrace-adapters`

`reqtrace` expects normalized `RequirementSet` and `EvidenceSet` inputs. `reqtrace-adapters` is responsible for loading external input formats into those core models.

Typical application flow:

```text
external files / tools / APIs
        |
reqtrace-adapters
        |
RequirementSet + EvidenceSet
        |
reqtrace
        |
TraceabilityResult
```

## Development

Run tests:

```bash
uv run pytest packages/reqtrace/tests
```

Run linting and formatting according to the repository configuration:

```bash
uv run ruff check packages/reqtrace
uv run ruff format packages/reqtrace
```

Build the package:

```bash
uv build packages/reqtrace
```

## License

MIT License. See `LICENSE`.
