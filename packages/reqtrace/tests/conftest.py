from collections.abc import Callable

import pytest
from reqtrace.models.evidence import EvidenceArtifact, EvidenceSet
from reqtrace.models.requirements import RequirementArtifact, RequirementSet
from reqtrace.models.traceability import TraceabilityResult, TraceabilitySummary
from reqtrace.progress import TraceContext


@pytest.fixture
def requirement_set() -> RequirementSet:
    return RequirementSet(
        requirements=(
            RequirementArtifact(
                id="req-1",
                title="Login",
            ),
        ),
    )


@pytest.fixture
def evidence_set() -> EvidenceSet:
    return EvidenceSet(
        id="evidence-1",
        title="Evidence",
        artifacts=(
            EvidenceArtifact(
                id="artifact-1",
                title="Login evidence",
            ),
        ),
    )


@pytest.fixture
def empty_trace_result() -> TraceabilityResult:
    return TraceabilityResult(
        id="test-result",
        title="Test result",
        summary=TraceabilitySummary(
            total_requirements=1,
            covered_requirements=0,
            partially_covered_requirements=0,
            uncovered_requirements=1,
            total_links=0,
        ),
    )


@pytest.fixture
def dummy_trace_method(
    empty_trace_result: TraceabilityResult,
) -> Callable[[RequirementSet, EvidenceSet, TraceContext], TraceabilityResult]:
    def trace_method(
        requirements: RequirementSet,
        evidence: EvidenceSet,
        context: TraceContext,
    ) -> TraceabilityResult:
        del requirements, evidence
        context.raise_if_cancelled()
        return empty_trace_result

    return trace_method
