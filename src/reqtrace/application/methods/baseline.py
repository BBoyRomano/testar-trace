"""Baseline traceability method.

The baseline method intentionally performs no matching. It exists to exercise the
pipeline and produce deterministic uncovered outputs under the canonical report
contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from reqtrace.application.result_metrics import build_input_summary, build_traceability_summary
from reqtrace.application.results import (
    CoverageSummary,
    CoverageVerdict,
    FlowStatus,
    FragmentTraceResult,
    RequirementResultStatus,
    RequirementTraceabilityResult,
    RunStatus,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
)
from reqtrace.domain.traceability.enums import CoverageStatus, CoverageSubjectType
from reqtrace.domain.traceability.models import CoverageAssessment


class BaselineMethod:
    name = "baseline"

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        selected_requirements = request.requirements.iter_requirements(
            request.selected_requirement_ids
        )
        run = TraceabilityRun(
            method_name=self.name,
            status=RunStatus.RUNNING,
            total_requirement_count=len(selected_requirements),
            metadata={
                "selected_evidence_run_count": len(request.selected_evidence_run_ids),
                "selected_evidence_run_ids_ignored": bool(request.selected_evidence_run_ids),
            },
        )

        results: list[RequirementTraceabilityResult] = []
        for requirement in selected_requirements:
            fragments = request.requirements.fragments_for(requirement.id)
            fragment_results = [
                FragmentTraceResult(
                    fragment_id=fragment.id,
                    fragment_kind=str(fragment.kind),
                    fragment_text=fragment.text,
                    status=FlowStatus.NOT_COVERED,
                    score=0.0,
                )
                for fragment in fragments
            ]
            artifact_coverage = CoverageAssessment(
                id=f"coverage-{uuid4().hex}",
                analysis_run_id=run.id,
                subject_type=CoverageSubjectType.REQUIREMENT,
                subject_id=requirement.id,
                coverage_status=CoverageStatus.UNCOVERED,
                coverage_ratio=0.0,
                confidence_ratio=0.0,
                covered_fragment_count=0,
                total_fragment_count=len(fragments),
                supporting_run_count=0,
                metadata={
                    "method": self.name,
                    "selected_evidence_run_ids_ignored": bool(request.selected_evidence_run_ids),
                },
            )
            fragment_coverages = [
                CoverageAssessment(
                    id=f"coverage-{uuid4().hex}",
                    analysis_run_id=run.id,
                    subject_type=CoverageSubjectType.REQUIREMENT_FRAGMENT,
                    subject_id=fragment.id,
                    coverage_status=CoverageStatus.UNCOVERED,
                    coverage_ratio=0.0,
                    confidence_ratio=0.0,
                    supporting_run_count=0,
                    metadata={"method": self.name},
                )
                for fragment in fragments
            ]
            results.append(
                RequirementTraceabilityResult(
                    requirement_id=requirement.id,
                    requirement_title=requirement.title,
                    requirement_external_id=requirement.external_id,
                    status=RequirementResultStatus.DONE,
                    coverage=CoverageSummary(
                        status=CoverageVerdict.NONE,
                        main_flow_status=FlowStatus.NOT_COVERED,
                        alt_flow_status=FlowStatus.NONE_DEFINED,
                        confidence=0.0,
                    ),
                    fragment_results=fragment_results,
                    warnings=[],
                    artifact_coverage=artifact_coverage,
                    fragment_coverages=fragment_coverages,
                    metadata={
                        "method": self.name,
                        "selected_evidence_run_ids_ignored": bool(
                            request.selected_evidence_run_ids
                        ),
                    },
                )
            )

        finished_run = run.model_copy(
            update={
                "status": RunStatus.COMPLETED,
                "processed_requirement_count": len(results),
                "failed_requirement_count": 0,
                "ended_at": datetime.now(timezone.utc),
            }
        )
        summary = build_traceability_summary(
            results,
            input_summary=build_input_summary(request.requirements, request.evidence),
        )
        return TraceabilityResult(
            run=finished_run,
            requirement_results=results,
            summary=summary,
            metadata={
                "method": self.name,
                "selected_evidence_run_ids_ignored": bool(request.selected_evidence_run_ids),
            },
        )
