from __future__ import annotations

from tests.application.unit._snapshots import build_evidence_snapshot, build_requirements_snapshot

from reqtrace.application.results import RequirementSnapshot, TraceabilityRequest
from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.domain.traceability.enums import CoverageStatus


def test_baseline_returns_uncovered_coverage_and_no_links() -> None:
    result = build_default_traceability_service().execute(
        TraceabilityRequest(
            requirements=build_requirements_snapshot(),
            evidence=build_evidence_snapshot(),
        )
    )

    assert result.run.method_name == "baseline"
    assert result.summary.requirement_count == 2
    assert result.summary.uncovered_requirement_count == 2
    assert result.summary.trace_link_count == 0
    assert result.summary.trace_evidence_count == 0
    assert len(result.requirement_results) == 2
    assert result.requirement_results[0].artifact_coverage is not None
    assert (
        result.requirement_results[0].artifact_coverage.coverage_status == CoverageStatus.UNCOVERED
    )
    assert result.requirement_results[0].trace_links == []
    assert result.requirement_results[0].trace_evidence == []


def test_baseline_only_processes_selected_requirements() -> None:
    result = build_default_traceability_service().execute(
        TraceabilityRequest(
            requirements=build_requirements_snapshot(),
            evidence=build_evidence_snapshot(),
            selected_requirement_ids=["REQ-2"],
        )
    )

    assert result.summary.requirement_count == 1
    assert [item.requirement_id for item in result.requirement_results] == ["REQ-2"]


def test_baseline_explicitly_ignores_selected_evidence_run_ids() -> None:
    result = build_default_traceability_service().execute(
        TraceabilityRequest(
            requirements=build_requirements_snapshot(),
            evidence=build_evidence_snapshot(),
            selected_evidence_run_ids=["run-1"],
        )
    )

    assert result.run.metadata["selected_evidence_run_count"] == 1
    assert result.run.metadata["selected_evidence_run_ids_ignored"] is True
    assert result.metadata["selected_evidence_run_ids_ignored"] is True
    assert result.requirement_results[0].metadata["selected_evidence_run_ids_ignored"] is True


def test_baseline_handles_zero_requirements() -> None:
    empty_requirements = RequirementSnapshot.from_mapping(
        {
            "requirements": [],
            "fragments": [],
            "flows": [],
            "flow_edges": [],
        }
    )
    result = build_default_traceability_service().execute(
        TraceabilityRequest(requirements=empty_requirements, evidence=build_evidence_snapshot())
    )

    assert result.summary.requirement_count == 0
    assert result.requirement_results == []
    assert result.run.total_requirement_count == 0
