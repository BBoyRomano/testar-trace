import pytest
from reqtrace.methods.noop import trace_with_noop
from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementArtifact, RequirementSet
from reqtrace.progress import CancellationToken, ProgressEvent, TraceContext


def test_trace_with_noop_returns_empty_result(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    result = trace_with_noop(
        requirement_set,
        evidence_set,
        TraceContext(),
    )

    assert result.id == "noop"
    assert result.title == "No-op traceability result"
    assert result.links == ()
    assert result.occurrences == ()
    assert result.fragment_alignments == ()
    assert result.coverage == ()


def test_trace_with_noop_marks_all_requirements_uncovered(
    evidence_set: EvidenceSet,
) -> None:
    requirements = RequirementSet(
        requirements=(
            RequirementArtifact(id="req-1", title="Login"),
            RequirementArtifact(id="req-2", title="Logout"),
        ),
    )

    result = trace_with_noop(
        requirements,
        evidence_set,
        TraceContext(),
    )

    assert result.summary.total_requirements == 2
    assert result.summary.covered_requirements == 0
    assert result.summary.partially_covered_requirements == 0
    assert result.summary.uncovered_requirements == 2
    assert result.summary.total_links == 0


def test_trace_with_noop_reports_progress(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    events: list[ProgressEvent] = []
    context = TraceContext(progress=events.append)

    trace_with_noop(requirement_set, evidence_set, context)

    assert [event.phase for event in events] == [
        "method-started",
        "method-finished",
    ]


def test_trace_with_noop_raises_when_cancelled(
    requirement_set: RequirementSet,
    evidence_set: EvidenceSet,
) -> None:
    context = TraceContext(
        cancellation=CancellationToken(cancelled=True),
    )

    with pytest.raises(InterruptedError, match="cancelled"):
        trace_with_noop(requirement_set, evidence_set, context)
