"""Traceability analysis entry points."""

from collections.abc import Mapping
from dataclasses import replace
from time import perf_counter

from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.models.traceability import TraceabilityResult
from reqtrace.progress import CancellationToken, ProgressReporter, TraceContext
from reqtrace.registry import available_trace_methods, get_trace_method

__all__ = ["analyze_traceability"]


def analyze_traceability(
    requirements: RequirementSet,
    evidence: EvidenceSet,
    *,
    method: str = "noop",
    options: Mapping[str, object] | None = None,
    progress: ProgressReporter | None = None,
    cancellation: CancellationToken | None = None,
) -> TraceabilityResult:
    """Run one traceability method against requirements and evidence."""
    trace_method = get_trace_method(method)

    if trace_method is None:
        available = ", ".join(available_trace_methods())
        raise ValueError(
            f"Unknown trace method: {method}. "
            f"Available methods: {available or 'none'}.",
        )

    context = TraceContext(
        progress=progress,
        cancellation=cancellation,
        options=options or {},
    )

    context.raise_if_cancelled()
    context.report("started", message=f"Running trace method: {method}")

    started = perf_counter()
    result = trace_method(requirements, evidence, context)
    elapsed = perf_counter() - started

    context.raise_if_cancelled()
    context.report("completed", message=f"Completed trace method: {method}")

    return _with_elapsed_seconds(result, elapsed)


def _with_elapsed_seconds(
    result: TraceabilityResult,
    elapsed_seconds: float,
) -> TraceabilityResult:
    metadata = dict(result.metadata)
    metadata.setdefault("elapsed_seconds", elapsed_seconds)

    return replace(result, metadata=metadata)
