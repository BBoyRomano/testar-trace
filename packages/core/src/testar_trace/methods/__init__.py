"""Trace-method implementations for TESTAR Trace."""

from testar_trace.methods.automata_conformance import trace_with_automata_conformance
from testar_trace.methods.execution_alignment import (
    ExecutionAlignmentConfig,
    ExecutionAlignmentMethod,
    trace_with_execution_alignment,
)
from testar_trace.methods.graph_alignment import (
    GraphAlignmentConfig,
    GraphAlignmentMethod,
    trace_with_graph_alignment,
)
from testar_trace.methods.lexical import (
    LexicalConfig,
    LexicalMethod,
    trace_with_lexical,
)
from testar_trace.methods.noop import trace_with_noop

__all__ = [
    "ExecutionAlignmentConfig",
    "ExecutionAlignmentMethod",
    "GraphAlignmentConfig",
    "GraphAlignmentMethod",
    "LexicalConfig",
    "LexicalMethod",
    "trace_with_automata_conformance",
    "trace_with_execution_alignment",
    "trace_with_graph_alignment",
    "trace_with_lexical",
    "trace_with_noop",
]
