"""No-op traceability method."""

from reqtrace.models.common import SourceRef
from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.models.traceability import (
    TraceabilityResult,
    TraceabilitySummary,
)
from reqtrace.progress import TraceContext

__all__ = ["trace_with_noop"]


def trace_with_noop(
    requirements: RequirementSet,
    evidence: EvidenceSet,
    context: TraceContext,
) -> TraceabilityResult:
    """Return an empty traceability result for wiring validation."""
    context.raise_if_cancelled()
    context.report(
        "method-started",
        message="Starting no-op traceability method.",
        metadata={"method": "noop"},
    )

    total_requirements = len(requirements.requirements)
    summary = TraceabilitySummary(
        total_requirements=total_requirements,
        covered_requirements=0,
        partially_covered_requirements=0,
        uncovered_requirements=total_requirements,
        total_links=0,
    )

    context.raise_if_cancelled()
    context.report(
        "method-finished",
        message="Finished no-op traceability method.",
        metadata={"method": "noop"},
    )

    return TraceabilityResult(
        id="noop",
        title="No-op traceability result",
        summary=summary,
        requirement_source_ref=_requirement_source_ref(requirements),
        evidence_source_ref=evidence.source_ref,
        links=(),
        occurrences=(),
        fragment_alignments=(),
        coverage=(),
        metadata={
            "method": "noop",
            "evidence_set_id": evidence.id,
        },
    )


def _requirement_source_ref(requirements: RequirementSet) -> SourceRef | None:
    if len(requirements.documents) == 1:
        return requirements.documents[0].source_ref
    return None
