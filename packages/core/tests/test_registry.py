import pytest

from testar_trace import create_builtin_method_registry
from testar_trace.methods._registry import TraceMethod, TraceMethodRegistry


def test_register_and_get_trace_method(dummy_trace_method) -> None:
    method = TraceMethod(
        id="registry-test-basic",
        name="Registry test",
        trace=dummy_trace_method,
    )
    registry = TraceMethodRegistry()

    registry.register(method)

    assert registry.get(method.id) is method


def test_method_registry_rejects_duplicate(dummy_trace_method) -> None:
    method = TraceMethod(
        id="registry-test-duplicate",
        name="Registry test",
        trace=dummy_trace_method,
    )
    registry = TraceMethodRegistry((method,))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(method)


def test_method_registry_can_explicitly_replace(dummy_trace_method) -> None:
    original = TraceMethod(
        id="registry-test-replace",
        name="Original",
        trace=dummy_trace_method,
    )
    replacement = TraceMethod(
        id="registry-test-replace",
        name="Replacement",
        trace=dummy_trace_method,
    )
    registry = TraceMethodRegistry((original,))

    registry.register(replacement, replace=True)

    assert registry.get(original.id) is replacement


def test_builtin_method_registries_are_isolated(dummy_trace_method) -> None:
    first = create_builtin_method_registry()
    second = create_builtin_method_registry()
    first.register(TraceMethod(id="custom", name="Custom", trace=dummy_trace_method))

    assert first.get("custom") is not None
    assert second.get("custom") is None
    graph = second.get("graph-alignment")
    execution = second.get("execution-alignment")
    formal = second.get("automata-conformance")
    assert graph is not None
    assert execution is not None
    assert formal is not None
    assert graph.name == "Graph alignment"
    assert execution.name == "Execution alignment"
    assert formal.name == "Formal check"
    assert second.get("sequence") is None
