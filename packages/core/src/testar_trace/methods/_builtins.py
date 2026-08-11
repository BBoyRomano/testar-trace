"""Built-in trace-method definitions."""

from testar_trace.methods._registry import (
    TraceMethod,
    TraceMethodRegistry,
)
from testar_trace.methods.automata_conformance import trace_with_automata_conformance
from testar_trace.methods.execution_alignment import ExecutionAlignmentMethod
from testar_trace.methods.graph_alignment import GraphAlignmentMethod
from testar_trace.methods.lexical import LexicalMethod
from testar_trace.methods.noop import trace_with_noop

_BUILTIN_TRACE_METHODS: tuple[TraceMethod, ...] = (
    TraceMethod(
        id="noop",
        name="No-op (diagnostic test)",
        trace=trace_with_noop,
    ),
    TraceMethod(
        id="lexical",
        name="Lexical",
        trace=LexicalMethod(),
    ),
    TraceMethod(
        id="graph-alignment",
        name="Graph alignment",
        trace=GraphAlignmentMethod(),
    ),
    TraceMethod(
        id="execution-alignment",
        name="Execution alignment",
        trace=ExecutionAlignmentMethod(),
    ),
    TraceMethod(
        id="automata-conformance",
        name="Formal check",
        trace=trace_with_automata_conformance,
    ),
)


def create_builtin_method_registry() -> TraceMethodRegistry:
    """Create a registry containing the built-in trace methods."""
    return TraceMethodRegistry(_BUILTIN_TRACE_METHODS)
