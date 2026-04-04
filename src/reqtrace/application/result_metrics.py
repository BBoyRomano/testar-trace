"""Pure helpers for building application-level report summaries."""

from __future__ import annotations

from reqtrace.application.results import (
    CoverageVerdict,
    EvidenceSnapshot,
    FlowStatus,
    GlobalCoverageSummary,
    InputSummary,
    RequirementResultStatus,
    RequirementSnapshot,
    RequirementTraceabilityResult,
    TraceabilitySummary,
)
from reqtrace.domain.traceability.enums import CoverageStatus


def build_input_summary(
    requirements: RequirementSnapshot, evidence: EvidenceSnapshot
) -> InputSummary:
    return InputSummary(
        requirement_count=len(requirements.requirements),
        fragment_count=len(requirements.fragments),
        flow_count=len(requirements.flows),
        state_count=len(evidence.states),
        element_count=len(evidence.elements),
        action_count=len(evidence.actions),
        transition_count=len(evidence.transitions),
        run_count=len(evidence.runs),
    )


def build_global_coverage(results: list[RequirementTraceabilityResult]) -> GlobalCoverageSummary:
    total = len(results)
    fully = sum(1 for item in results if item.coverage.status == CoverageVerdict.FULL)
    main_only = sum(1 for item in results if item.coverage.status == CoverageVerdict.MAIN_ONLY)
    alt_only = sum(1 for item in results if item.coverage.status == CoverageVerdict.ALT_ONLY)
    partial = sum(1 for item in results if item.coverage.status == CoverageVerdict.PARTIAL)
    none = sum(1 for item in results if item.coverage.status == CoverageVerdict.NONE)
    uncertain = sum(1 for item in results if item.coverage.status == CoverageVerdict.UNCERTAIN)
    any_trace = sum(1 for item in results if item.execution_instances)
    main_trace = sum(
        1 for item in results if item.main_flow_result and item.main_flow_result.instance_ids
    )
    alt_trace = sum(
        1 for item in results if any(flow.instance_ids for flow in item.alternative_flow_results)
    )
    overall_ratio = ((fully + main_only + alt_only) + 0.5 * partial) / total if total else 0.0
    main_ratio = sum(item.coverage.main_flow_ratio for item in results) / total if total else 0.0
    alt_ratio = sum(item.coverage.alt_flow_ratio for item in results) / total if total else 0.0
    average_conf = sum(item.coverage.confidence for item in results) / total if total else 0.0
    return GlobalCoverageSummary(
        total_requirements=total,
        fully_covered=fully,
        main_only=main_only,
        alt_only=alt_only,
        partial=partial,
        none=none,
        uncertain=uncertain,
        requirements_with_any_trace=any_trace,
        requirements_with_main_trace=main_trace,
        requirements_with_alt_trace=alt_trace,
        overall_coverage_ratio=overall_ratio,
        main_flow_coverage_ratio=main_ratio,
        alt_flow_coverage_ratio=alt_ratio,
        average_confidence=average_conf,
    )


def build_traceability_summary(
    results: list[RequirementTraceabilityResult],
    *,
    input_summary: InputSummary,
) -> TraceabilitySummary:
    requirement_count = len(results)
    analyzed_requirement_count = sum(
        1 for item in results if item.status == RequirementResultStatus.DONE
    )
    failed_requirement_count = requirement_count - analyzed_requirement_count
    covered_requirement_count = sum(
        1
        for item in results
        if item.artifact_coverage is not None
        and item.artifact_coverage.coverage_status == CoverageStatus.COVERED
    )
    partially_covered_requirement_count = sum(
        1
        for item in results
        if item.artifact_coverage is not None
        and item.artifact_coverage.coverage_status == CoverageStatus.PARTIALLY_COVERED
    )
    uncovered_requirement_count = sum(
        1
        for item in results
        if item.artifact_coverage is not None
        and item.artifact_coverage.coverage_status == CoverageStatus.UNCOVERED
    )
    uncertain_requirement_count = sum(
        1
        for item in results
        if item.artifact_coverage is not None
        and item.artifact_coverage.coverage_status == CoverageStatus.UNCERTAIN
    )
    requirement_fragment_count = sum(len(item.fragment_results) for item in results)
    covered_fragment_count = sum(
        1
        for item in results
        for fragment in item.fragment_results
        if fragment.status == FlowStatus.COVERED
    )
    trace_link_count = sum(len(item.trace_links) for item in results)
    trace_evidence_count = sum(len(item.trace_evidence) for item in results)
    warning_count = sum(len(item.warnings) for item in results)
    return TraceabilitySummary(
        requirement_count=requirement_count,
        analyzed_requirement_count=analyzed_requirement_count,
        failed_requirement_count=failed_requirement_count,
        covered_requirement_count=covered_requirement_count,
        partially_covered_requirement_count=partially_covered_requirement_count,
        uncovered_requirement_count=uncovered_requirement_count,
        uncertain_requirement_count=uncertain_requirement_count,
        requirement_fragment_count=requirement_fragment_count,
        covered_fragment_count=covered_fragment_count,
        trace_link_count=trace_link_count,
        trace_evidence_count=trace_evidence_count,
        warning_count=warning_count,
        input_summary=input_summary,
        global_coverage=build_global_coverage(results),
    )
