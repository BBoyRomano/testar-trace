from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from reqtrace.application.methods.common.candidate_utils import (
    best_match,
    build_candidates,
    filter_evidence_by_selected_runs,
    iter_selected_requirements,
)
from reqtrace.application.methods.common.progress import (
    emit_requirement_progress,
    raise_if_canceled,
)
from reqtrace.application.progress import CancellationCallback, ProgressCallback
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.result_metrics import build_input_summary, build_traceability_summary
from reqtrace.application.results import (
    CoverageSummary,
    CoverageVerdict,
    ExecutionInstance,
    ExecutionTrace,
    FlowStatus,
    FragmentTraceResult,
    RequirementResultStatus,
    RequirementTraceabilityResult,
    RunStatus,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
    TraceKind,
    TracePathItem,
)
from reqtrace.domain.traceability.enums import CoverageStatus, CoverageSubjectType
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink


class CandidateMatchMethod(TraceabilityMethod):
    name = "candidate_match"
    method_name = "candidate_match"

    def run(
        self,
        request: TraceabilityRequest,
        *,
        progress_callback: ProgressCallback | None = None,
        is_canceled: CancellationCallback | None = None,
    ) -> TraceabilityResult:
        started_at = datetime.now(UTC)
        analysis_run_id = f"trace-run-{uuid4().hex}"
        requirements = list(
            iter_selected_requirements(request.requirements, request.selected_requirement_ids)
        )
        total_requirements = len(requirements)
        evidence = filter_evidence_by_selected_runs(
            request.evidence, request.selected_evidence_run_ids
        )
        candidates = build_candidates(evidence, request.selected_evidence_run_ids)

        results: list[RequirementTraceabilityResult] = []
        processed_requirements = 0
        for requirement in requirements:
            raise_if_canceled(is_canceled=is_canceled)
            emit_requirement_progress(
                progress_callback=progress_callback,
                requirement_id=requirement.id,
                requirement_title=requirement.title,
                state="processing",
                processed_requirement_count=processed_requirements,
                total_requirement_count=total_requirements,
                phase=self.method_name,
            )
            fragments = list(request.requirements.fragments_for(requirement.id))
            fragment_results: list[FragmentTraceResult] = []
            fragment_coverages: list[CoverageAssessment] = []
            trace_links: list[TraceLink] = []
            trace_evidence: list[TraceEvidence] = []
            warnings: list[str] = []
            scores: list[float] = []
            instances: list[ExecutionInstance] = []

            for fragment in fragments:
                raise_if_canceled(is_canceled=is_canceled)
                match = best_match(fragment.text, candidates)
                flow_status = FlowStatus.NOT_COVERED
                if match is not None:
                    score = float(match["score"])
                    scores.append(score)
                    if score >= 0.72:
                        flow_status = FlowStatus.COVERED
                    elif score >= 0.30:
                        flow_status = FlowStatus.PARTIAL
                    if score >= 0.30:
                        link = TraceLink(
                            id=f"link-{uuid4().hex}",
                            analysis_run_id=analysis_run_id,
                            requirement_fragment_id=fragment.id,
                            evidence_target_type=match["candidate"].target_type,
                            evidence_target_id=match["candidate"].target_id,
                            link_type="covers" if flow_status == FlowStatus.COVERED else "supports",
                            score=score,
                            confidence_label="high" if score >= 0.72 else "medium",
                            metadata={"method": self.method_name, "intent": match["intent"]},
                        )
                        trace_links.append(link)
                        trace_evidence.append(
                            TraceEvidence(
                                id=f"evidence-{uuid4().hex}",
                                trace_link_id=link.id,
                                evidence_kind="text_match",
                                text_excerpt=match["candidate"].text[:240],
                                matched_tokens=sorted(match["matched_tokens"]),
                                state_id=match["candidate"].state_id,
                                transition_id=match["candidate"].transition_id,
                                element_id=match["candidate"].element_id,
                                details={"candidate_type": match["candidate"].target_type},
                            )
                        )
                        if flow_status == FlowStatus.COVERED:
                            item_kind = (
                                "transition" if match["candidate"].transition_id else "state"
                            )
                            path_item = TracePathItem(
                                kind=item_kind,
                                item_id=match["candidate"].transition_id
                                or match["candidate"].state_id
                                or match["candidate"].target_id,
                                state_id=match["candidate"].state_id,
                                transition_id=match["candidate"].transition_id,
                                action_id=match["candidate"].action_id,
                                label=match["candidate"].text[:120],
                                matched_fragment_ids=[fragment.id],
                                match_role="matched",
                            )
                            trace = ExecutionTrace(
                                trace_kind=TraceKind.CANDIDATE,
                                score=score,
                                path=[path_item],
                                matched_fragment_ids=[fragment.id],
                            )
                            instances.append(
                                ExecutionInstance(
                                    flow_id=requirement.id,
                                    flow_kind=TraceKind.CANDIDATE,
                                    covered_fragment_ids=[fragment.id],
                                    representative_trace=trace,
                                )
                            )
                fragment_results.append(
                    FragmentTraceResult(
                        fragment_id=fragment.id,
                        fragment_kind=str(fragment.kind),
                        fragment_text=fragment.text,
                        status=flow_status,
                        score=float(match["score"]) if match else 0.0,
                        matched_state_ids=[match["candidate"].state_id]
                        if match and match["candidate"].state_id
                        else [],
                        matched_transition_ids=[match["candidate"].transition_id]
                        if match and match["candidate"].transition_id
                        else [],
                        matched_action_ids=[match["candidate"].action_id]
                        if match and match["candidate"].action_id
                        else [],
                        matched_element_ids=[match["candidate"].element_id]
                        if match and match["candidate"].element_id
                        else [],
                    )
                )
                fragment_coverages.append(
                    CoverageAssessment(
                        id=f"coverage-{uuid4().hex}",
                        analysis_run_id=analysis_run_id,
                        subject_type=CoverageSubjectType.REQUIREMENT_FRAGMENT,
                        subject_id=fragment.id,
                        coverage_status=(
                            CoverageStatus.COVERED
                            if flow_status == FlowStatus.COVERED
                            else CoverageStatus.PARTIALLY_COVERED
                            if flow_status == FlowStatus.PARTIAL
                            else CoverageStatus.UNCOVERED
                        ),
                        coverage_ratio=1.0
                        if flow_status == FlowStatus.COVERED
                        else 0.5
                        if flow_status == FlowStatus.PARTIAL
                        else 0.0,
                        confidence_ratio=float(match["score"]) if match else 0.0,
                        supporting_run_count=0,
                        metadata={"method": self.method_name},
                    )
                )

            avg_score = sum(scores) / len(scores) if scores else 0.0
            matched_count = sum(
                1 for item in fragment_results if item.status != FlowStatus.NOT_COVERED
            )
            ratio = matched_count / len(fragment_results) if fragment_results else 0.0
            if ratio >= 0.8 and avg_score >= 0.72:
                verdict = CoverageVerdict.FULL
                cov_status = CoverageStatus.COVERED
            elif matched_count > 0:
                verdict = CoverageVerdict.PARTIAL if avg_score >= 0.3 else CoverageVerdict.UNCERTAIN
                cov_status = (
                    CoverageStatus.PARTIALLY_COVERED
                    if avg_score >= 0.48
                    else CoverageStatus.UNCERTAIN
                )
            else:
                verdict = CoverageVerdict.NONE
                cov_status = CoverageStatus.UNCOVERED
            artifact_coverage = CoverageAssessment(
                id=f"coverage-{uuid4().hex}",
                analysis_run_id=analysis_run_id,
                subject_type=CoverageSubjectType.REQUIREMENT,
                subject_id=requirement.id,
                coverage_status=cov_status,
                coverage_ratio=ratio if cov_status != CoverageStatus.UNCOVERED else 0.0,
                confidence_ratio=avg_score,
                covered_fragment_count=matched_count
                if cov_status != CoverageStatus.UNCERTAIN
                else 0,
                total_fragment_count=len(fragment_results),
                supporting_run_count=0,
                metadata={"method": self.method_name},
            )
            results.append(
                RequirementTraceabilityResult(
                    requirement_id=requirement.id,
                    requirement_title=requirement.title,
                    requirement_external_id=requirement.external_id,
                    status=RequirementResultStatus.DONE,
                    coverage=CoverageSummary(
                        status=verdict,
                        main_flow_status=FlowStatus.COVERED
                        if verdict == CoverageVerdict.FULL
                        else FlowStatus.PARTIAL
                        if matched_count
                        else FlowStatus.NOT_COVERED,
                        confidence=avg_score,
                        main_flow_ratio=ratio,
                    ),
                    fragment_results=fragment_results,
                    execution_instances=instances,
                    warnings=warnings,
                    artifact_coverage=artifact_coverage,
                    fragment_coverages=fragment_coverages,
                    trace_links=trace_links,
                    trace_evidence=trace_evidence,
                    metadata={"method": self.method_name},
                )
            )
            processed_requirements += 1
            emit_requirement_progress(
                progress_callback=progress_callback,
                requirement_id=requirement.id,
                requirement_title=requirement.title,
                state="completed",
                processed_requirement_count=processed_requirements,
                total_requirement_count=total_requirements,
                phase=self.method_name,
            )

        ended_at = datetime.now(UTC)
        summary = build_traceability_summary(
            results, input_summary=build_input_summary(request.requirements, request.evidence)
        )
        run = TraceabilityRun(
            id=analysis_run_id,
            method_name=self.method_name,
            status=RunStatus.COMPLETED,
            started_at=started_at,
            ended_at=ended_at,
            total_requirement_count=len(requirements),
            processed_requirement_count=len(results),
            failed_requirement_count=0,
            metadata={"method": self.method_name},
        )
        return TraceabilityResult(
            run=run,
            requirement_results=results,
            summary=summary,
            metadata={
                "method": self.method_name,
                "selected_evidence_run_count": len(request.selected_evidence_run_ids),
            },
        )
