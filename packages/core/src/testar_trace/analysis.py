"""Orchestration of traceability analysis."""

from testar_trace.domain.requirements import RequirementSet
from testar_trace.domain.state_models import StateModelCollection
from testar_trace.domain.traceability import TraceabilityResult
from testar_trace.execution import TraceContext
from testar_trace.methods._registry import TraceCallable

__all__ = ["analyze_traceability"]


def analyze_traceability(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    *,
    method: TraceCallable,
    context: TraceContext | None = None,
) -> TraceabilityResult:
    """Run a trace method against requirements and state models."""
    if not callable(method):
        raise TypeError("method must be callable")

    trace_context = TraceContext() if context is None else context

    trace_context.raise_if_cancelled()
    trace_context.report(
        "analysis.started",
        message="Traceability analysis started",
    )

    result = method(
        requirements,
        state_models,
        trace_context,
    )

    if not isinstance(result, TraceabilityResult):
        raise TypeError("trace method must return a TraceabilityResult")

    trace_context.raise_if_cancelled()
    trace_context.report(
        "analysis.completed",
        message="Traceability analysis completed",
    )

    return result
