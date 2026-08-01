"""Built-in trace method registrations."""

from reqtrace.methods import (
    graph_sequence,
    graph_window_sequence,
    noop,
    sequence,
    sequence_v2,
)
from reqtrace.registry import register_trace_method

__all__ = ["register_builtin_trace_methods"]


def register_builtin_trace_methods() -> None:
    """Register trace methods shipped with ReqTrace."""
    register_trace_method(
        "noop",
        noop.trace_with_noop,
        replace=True,
    )
    register_trace_method(
        "sequence",
        sequence.trace_with_sequence,
        replace=True,
    )
    register_trace_method(
        "sequence-v2",
        sequence_v2.trace_with_sequence,
        replace=True,
    )
    register_trace_method(
        "graph-sequence",
        graph_sequence.trace_with_graph_sequence,
        replace=True,
    )
    register_trace_method(
        "graph-window-sequence",
        graph_window_sequence.trace_with_graph_window_sequence,
        replace=True,
    )
