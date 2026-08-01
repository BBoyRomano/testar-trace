import pytest
from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.models.traceability import TraceabilityResult
from reqtrace.progress import TraceContext
from reqtrace.registry import (
    available_trace_methods,
    get_trace_method,
    register_trace_method,
)


def test_register_and_get_trace_method(dummy_trace_method) -> None:
    register_trace_method(
        "registry-test-basic",
        dummy_trace_method,
    )

    method = get_trace_method("registry-test-basic")

    assert method is dummy_trace_method


def test_register_trace_method_normalizes_name(dummy_trace_method) -> None:
    register_trace_method(
        "Registry_Test_Normalized",
        dummy_trace_method,
    )

    method = get_trace_method("registry-test-normalized")

    assert method is dummy_trace_method


def test_register_trace_method_rejects_duplicate(dummy_trace_method) -> None:
    register_trace_method(
        "registry-test-duplicate",
        dummy_trace_method,
    )

    with pytest.raises(ValueError, match="already registered"):
        register_trace_method(
            "registry-test-duplicate",
            dummy_trace_method,
        )


def test_register_trace_method_replace_overwrites(
    dummy_trace_method,
    empty_trace_result: TraceabilityResult,
) -> None:
    def replacement_method(
        requirements: RequirementSet,
        evidence: EvidenceSet,
        context: TraceContext,
    ) -> TraceabilityResult:
        del requirements, evidence, context
        return empty_trace_result

    register_trace_method(
        "registry-test-replace",
        dummy_trace_method,
    )
    register_trace_method(
        "registry-test-replace",
        replacement_method,
        replace=True,
    )

    method = get_trace_method("registry-test-replace")

    assert method is replacement_method


def test_available_trace_methods_returns_registered_names(dummy_trace_method) -> None:
    register_trace_method(
        "registry-test-available",
        dummy_trace_method,
    )

    assert "registry-test-available" in available_trace_methods()
