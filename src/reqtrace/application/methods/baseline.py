"""Baseline traceability method.

This method performs no real traceability inference. It exists to:
- exercise the end-to-end ingestion -> analysis -> result pipeline
- produce deterministic "uncovered" coverage outputs
- provide a reference point for future methods

Baseline behavior notes:
- selected_requirement_ids are honored
- selected_evidence_run_ids are validated by the request model but ignored by
  this method for now
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from reqtrace.application.results import (
    RequirementResultStatus,
    RequirementTraceabilityResult,
    RunStatus,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
    TraceabilitySummary,
)
from reqtrace.domain.traceability.enums import CoverageStatus, CoverageSubjectType
from reqtrace.domain.traceability.models import CoverageAssessment


class BaselineMethod:
    name = "baseline"

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        selected_requirements = request.requirements.iter_requirements(request.selected_requirement_ids)
        selected_evidence_run_ids_ignored = bool(request.selected_evidence_run_ids)

        run = TraceabilityRun(
            method_name=self.name,
            status=RunStatus.RUNNING,
            total_requirement_count=len(selected_requirements),
            metadata={
                "baseline": True,
                "selected_evidence_run_count": len(request.selected_evidence_run_ids),
                "total_evidence_run_count": len(request.evidence.runs),
                "selected_evidence_run_ids_ignored": selected_evidence_run_ids_ignored,
            },
        )

        requirement_results: list[RequirementTraceabilityResult] = []
        failed = 0

        for requirement in selected_requirements:
            fragments = request.requirements.fragments_for(requirement.id)
            try:
                requirement_results.append(
                    self._build_uncovered_result(
                        analysis_run_id=run.id,
                        requirement_id=requirement.id,
                        requirement_title=requirement.title,
                        fragment_ids=[fragment.id for fragment in fragments],
                        evidence_run_count=len(request.evidence.runs),
                        selected_evidence_run_ids_ignored=selected_evidence_run_ids_ignored,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive
                failed += 1
                requirement_results.append(
                    RequirementTraceabilityResult(
                        requirement_id=requirement.id,
                        requirement_title=requirement.title,
                        status=RequirementResultStatus.FAILED,
                        artifact_coverage=None,
                        fragment_coverages=[],
                        trace_links=[],
                        trace_evidence=[],
                        warnings=[],
                        error_message=str(exc),
                        metadata={
                            "baseline": True,
                            "fragment_count": len(fragments),
                            "selected_evidence_run_ids_ignored": selected_evidence_run_ids_ignored,
                        },
                    )
                )

        finalized_run = run.model_copy(
            update={
                "status": RunStatus.COMPLETED_WITH_ERRORS if failed else RunStatus.COMPLETED,
                "processed_requirement_count": len(selected_requirements),
                "failed_requirement_count": failed,
                "ended_at": datetime.now(timezone.utc),
            }
        )

        summary = self._summarize(requirement_results)
        return TraceabilityResult(
            run=finalized_run,
            requirement_results=requirement_results,
            summary=summary,
            metadata={
                "baseline": True,
                "method_name": self.name,
                "selected_evidence_run_ids_ignored": selected_evidence_run_ids_ignored,
            },
        )

    def _build_uncovered_result(
        self,
        *,
        analysis_run_id: str,
        requirement_id: str,
        requirement_title: str,
        fragment_ids: list[str],
        evidence_run_count: int,
        selected_evidence_run_ids_ignored: bool,
    ) -> RequirementTraceabilityResult:
        artifact_coverage = CoverageAssessment(
            id=f"coverage-{uuid4().hex}",
            analysis_run_id=analysis_run_id,
            subject_type=CoverageSubjectType.REQUIREMENT,
            subject_id=requirement_id,
            coverage_status=CoverageStatus.UNCOVERED,
            coverage_ratio=0.0,
            confidence_ratio=None,
            covered_fragment_count=0,
            total_fragment_count=len(fragment_ids),
            supporting_run_count=0,
            metadata={"baseline": True},
        )

        fragment_coverages = [
            CoverageAssessment(
                id=f"coverage-{uuid4().hex}",
                analysis_run_id=analysis_run_id,
                subject_type=CoverageSubjectType.REQUIREMENT_FRAGMENT,
                subject_id=fragment_id,
                coverage_status=CoverageStatus.UNCOVERED,
                coverage_ratio=0.0,
                confidence_ratio=None,
                covered_fragment_count=None,
                total_fragment_count=None,
                supporting_run_count=0,
                metadata={"baseline": True},
            )
            for fragment_id in fragment_ids
        ]

        return RequirementTraceabilityResult(
            requirement_id=requirement_id,
            requirement_title=requirement_title,
            status=RequirementResultStatus.DONE,
            artifact_coverage=artifact_coverage,
            fragment_coverages=fragment_coverages,
            trace_links=[],
            trace_evidence=[],
            warnings=[],
            metadata={
                "baseline": True,
                "fragment_count": len(fragment_ids),
                "available_evidence_run_count": evidence_run_count,
                "selected_evidence_run_ids_ignored": selected_evidence_run_ids_ignored,
            },
        )

    def _summarize(self, results: list[RequirementTraceabilityResult]) -> TraceabilitySummary:
        covered_requirements = 0
        partially_covered_requirements = 0
        uncovered_requirements = 0
        uncertain_requirements = 0
        requirement_fragment_count = 0
        covered_fragment_count = 0
        trace_link_count = 0
        trace_evidence_count = 0
        warning_count = 0
        failed = 0

        for result in results:
            if result.status == RequirementResultStatus.FAILED:
                failed += 1

            if result.artifact_coverage is not None:
                status = result.artifact_coverage.coverage_status
                if status == CoverageStatus.COVERED:
                    covered_requirements += 1
                elif status == CoverageStatus.PARTIALLY_COVERED:
                    partially_covered_requirements += 1
                elif status == CoverageStatus.UNCOVERED:
                    uncovered_requirements += 1
                elif status == CoverageStatus.UNCERTAIN:
                    uncertain_requirements += 1

            requirement_fragment_count += len(result.fragment_coverages)
            covered_fragment_count += sum(
                1 for frag in result.fragment_coverages if frag.coverage_status == CoverageStatus.COVERED
            )
            trace_link_count += len(result.trace_links)
            trace_evidence_count += len(result.trace_evidence)
            warning_count += len(result.warnings)

        return TraceabilitySummary(
            requirement_count=len(results),
            analyzed_requirement_count=len(results) - failed,
            failed_requirement_count=failed,
            covered_requirement_count=covered_requirements,
            partially_covered_requirement_count=partially_covered_requirements,
            uncovered_requirement_count=uncovered_requirements,
            uncertain_requirement_count=uncertain_requirements,
            requirement_fragment_count=requirement_fragment_count,
            covered_fragment_count=covered_fragment_count,
            trace_link_count=trace_link_count,
            trace_evidence_count=trace_evidence_count,
            warning_count=warning_count,
        )
