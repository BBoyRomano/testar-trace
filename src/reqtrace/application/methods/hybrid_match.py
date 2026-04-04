from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from reqtrace.application.methods.candidate_match import CandidateMatchMethod
from reqtrace.application.methods.flow_match import FlowMatchMethod
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.result_metrics import build_input_summary, build_traceability_summary
from reqtrace.application.results import (
    CoverageVerdict,
    RequirementTraceabilityResult,
    RunStatus,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
)

_VERDICT_RANK = {
    CoverageVerdict.FULL: 5,
    CoverageVerdict.MAIN_ONLY: 4,
    CoverageVerdict.ALT_ONLY: 4,
    CoverageVerdict.PARTIAL: 3,
    CoverageVerdict.UNCERTAIN: 2,
    CoverageVerdict.NONE: 1,
}


class HybridMatchMethod(TraceabilityMethod):
    """Hybrid method combining flow-level alignment and candidate retrieval.

    Policy:
    - Prefer flow evidence when it yields execution instances (stronger ordered proof).
    - Otherwise prefer the stronger requirement-level verdict/confidence between
      flow and candidate outputs.
    """

    name = "hybrid_match"
    method_name = "hybrid_match"

    def __init__(self) -> None:
        self._flow = FlowMatchMethod()
        self._candidate = CandidateMatchMethod()

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        started_at = datetime.now(UTC)
        analysis_run_id = f"trace-run-{uuid4().hex}"

        flow_result = self._flow.run(request)
        candidate_result = self._candidate.run(request)

        candidate_by_id = {
            item.requirement_id: item for item in candidate_result.requirement_results
        }
        merged_results: list[RequirementTraceabilityResult] = []
        for flow_item in flow_result.requirement_results:
            candidate_item = candidate_by_id.get(flow_item.requirement_id)
            if candidate_item is None:
                merged_results.append(_retag_item(flow_item, analysis_run_id))
                continue
            merged_results.append(
                _retag_item(_choose_better_result(flow_item, candidate_item), analysis_run_id)
            )

        summary = build_traceability_summary(
            merged_results,
            input_summary=build_input_summary(request.requirements, request.evidence),
        )
        run = TraceabilityRun(
            id=analysis_run_id,
            method_name=self.method_name,
            status=RunStatus.COMPLETED,
            started_at=started_at,
            ended_at=datetime.now(UTC),
            total_requirement_count=len(merged_results),
            processed_requirement_count=len(merged_results),
            failed_requirement_count=0,
            metadata={
                "method": self.method_name,
                "source_methods": ["flow_match", "candidate_match"],
            },
        )
        return TraceabilityResult(
            run=run,
            requirement_results=merged_results,
            summary=summary,
            metadata={
                "method": self.method_name,
                "source_methods": ["flow_match", "candidate_match"],
            },
        )


def _choose_better_result(
    flow_item: RequirementTraceabilityResult,
    candidate_item: RequirementTraceabilityResult,
) -> RequirementTraceabilityResult:
    if flow_item.execution_instances:
        return _merge_links_and_evidence(flow_item, candidate_item)

    flow_rank = _VERDICT_RANK[flow_item.coverage.status]
    candidate_rank = _VERDICT_RANK[candidate_item.coverage.status]
    if flow_rank > candidate_rank:
        return _merge_links_and_evidence(flow_item, candidate_item)
    if candidate_rank > flow_rank:
        return _merge_links_and_evidence(candidate_item, flow_item)

    if flow_item.coverage.confidence >= candidate_item.coverage.confidence:
        return _merge_links_and_evidence(flow_item, candidate_item)
    return _merge_links_and_evidence(candidate_item, flow_item)


def _merge_links_and_evidence(
    preferred: RequirementTraceabilityResult,
    secondary: RequirementTraceabilityResult,
) -> RequirementTraceabilityResult:
    preferred_links = list(preferred.trace_links)
    preferred_link_ids = {item.id for item in preferred_links}
    merged_links = preferred_links + [
        item for item in secondary.trace_links if item.id not in preferred_link_ids
    ]

    preferred_evidence = list(preferred.trace_evidence)
    preferred_evidence_ids = {item.id for item in preferred_evidence}
    merged_evidence = preferred_evidence + [
        item for item in secondary.trace_evidence if item.id not in preferred_evidence_ids
    ]

    warnings = list(dict.fromkeys([*preferred.warnings, *secondary.warnings]))
    metadata = {
        **secondary.metadata,
        **preferred.metadata,
        "selected_by": "hybrid_match",
    }

    return preferred.model_copy(
        update={
            "trace_links": merged_links,
            "trace_evidence": merged_evidence,
            "warnings": warnings,
            "metadata": metadata,
        }
    )


def _retag_item(
    item: RequirementTraceabilityResult,
    analysis_run_id: str,
) -> RequirementTraceabilityResult:
    artifact_coverage = item.artifact_coverage
    if artifact_coverage is not None:
        artifact_coverage = artifact_coverage.model_copy(
            update={"analysis_run_id": analysis_run_id}
        )

    fragment_coverages = [
        coverage.model_copy(update={"analysis_run_id": analysis_run_id})
        for coverage in item.fragment_coverages
    ]
    trace_links = [
        link.model_copy(update={"analysis_run_id": analysis_run_id}) for link in item.trace_links
    ]

    return item.model_copy(
        update={
            "artifact_coverage": artifact_coverage,
            "fragment_coverages": fragment_coverages,
            "trace_links": trace_links,
            "metadata": {**item.metadata, "method": "hybrid_match"},
        }
    )
