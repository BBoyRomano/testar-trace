import pytest
from reqtrace.analysis import analyze_traceability
from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.models.traceability import TraceabilityResult
from reqtrace.progress import CancellationToken, ProgressEvent, TraceContext
from reqtrace.registry import register_trace_method


def test_analyze_traceability_runs_noop_method(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    result = analyze_traceability(requirement_set, evidence_set)

    assert result.id == "noop"
    assert result.summary.total_requirements == 1
    assert result.summary.uncovered_requirements == 1
    assert result.links == ()


def test_analyze_traceability_reports_started_and_completed(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    events: list[ProgressEvent] = []

    analyze_traceability(
        requirement_set,
        evidence_set,
        progress=events.append,
    )

    phases = [event.phase for event in events]

    assert "started" in phases
    assert "completed" in phases


def test_analyze_traceability_adds_elapsed_seconds(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    result = analyze_traceability(requirement_set, evidence_set)

    elapsed_seconds = result.metadata["elapsed_seconds"]

    assert isinstance(elapsed_seconds, float)
    assert elapsed_seconds >= 0


def test_analyze_traceability_rejects_unknown_method(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    with pytest.raises(ValueError, match="Unknown trace method"):
        analyze_traceability(
            requirement_set,
            evidence_set,
            method="missing-method",
        )


def test_analyze_traceability_raises_when_cancelled_before_start(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    cancellation = CancellationToken(cancelled=True)

    with pytest.raises(InterruptedError, match="cancelled"):
        analyze_traceability(
            requirement_set,
            evidence_set,
            cancellation=cancellation,
        )


def test_analyze_traceability_runs_registered_custom_method(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
    empty_trace_result: TraceabilityResult,
) -> None:
    def trace_method(
        requirements: RequirementSet,
        evidence: EvidenceSet,
        context: TraceContext,
    ) -> TraceabilityResult:
        del requirements, evidence
        context.report("custom-method")
        return empty_trace_result

    register_trace_method(
        "analysis-test-custom",
        trace_method,
    )

    events: list[ProgressEvent] = []
    result = analyze_traceability(
        requirement_set,
        evidence_set,
        method="analysis-test-custom",
        progress=events.append,
    )

    assert result.id == "test-result"
    assert "custom-method" in [event.phase for event in events]
