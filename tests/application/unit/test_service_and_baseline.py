from __future__ import annotations

from datetime import datetime
from typing import NoReturn

import pytest

from reqtrace.application.exceptions import (
    InvalidTraceabilityRequestError,
    TraceabilityMethodExecutionError,
    UnknownTraceabilityMethodError,
)
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.results import (
    EvidenceSnapshot,
    RequirementSnapshot,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
    TraceabilitySummary,
)
from reqtrace.application.services.traceability_service import (
    TraceabilityService,
    build_default_traceability_service,
)
from reqtrace.domain.evidence.enums import ExecutionRunStatus
from reqtrace.domain.evidence.models import ExecutionRun
from reqtrace.domain.requirements.enums import RequirementFragmentKind, RequirementKind
from reqtrace.domain.requirements.models import RequirementArtifact, RequirementFragment
from reqtrace.domain.traceability.enums import CoverageStatus


def _build_requirements_snapshot() -> RequirementSnapshot:
    return RequirementSnapshot.from_mapping(
        {
            "requirements": [
                RequirementArtifact(id="REQ-1", kind=RequirementKind.USE_CASE, title="Login"),
                RequirementArtifact(id="REQ-2", kind=RequirementKind.USE_CASE, title="Logout"),
            ],
            "fragments": [
                RequirementFragment(
                    id="REQ-1-frag-1",
                    requirement_id="REQ-1",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The user enters credentials",
                    order_index=0,
                ),
                RequirementFragment(
                    id="REQ-2-frag-1",
                    requirement_id="REQ-2",
                    kind=RequirementFragmentKind.MAIN_STEP,
                    text="The user logs out",
                    order_index=0,
                ),
            ],
            "flows": [],
            "flow_edges": [],
        }
    )


def _build_evidence_snapshot() -> EvidenceSnapshot:
    return EvidenceSnapshot.from_mapping(
        {
            "states": [],
            "elements": [],
            "actions": [],
            "transitions": [],
            "runs": [
                ExecutionRun(id="run-1", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
                ExecutionRun(id="run-2", tool_name="TESTAR", status=ExecutionRunStatus.COMPLETED),
            ],
            "observations": [],
            "attachments": [],
        }
    )


def test_service_exposes_baseline_method() -> None:
    service = build_default_traceability_service()
    assert service.available_methods() == ["baseline"]


def test_service_raises_on_unknown_method() -> None:
    request = TraceabilityRequest(
        method_name="unknown",
        requirements=_build_requirements_snapshot(),
        evidence=_build_evidence_snapshot(),
    )

    with pytest.raises(UnknownTraceabilityMethodError):
        build_default_traceability_service().execute(request)


def test_service_wraps_method_failure() -> None:
    class FailingMethod:
        name = "failing"

        def run(self, request: TraceabilityRequest) -> NoReturn:
            raise RuntimeError("boom")

    service = TraceabilityService(methods={"failing": FailingMethod()})
    request = TraceabilityRequest(
        method_name="failing",
        requirements=_build_requirements_snapshot(),
        evidence=_build_evidence_snapshot(),
    )

    with pytest.raises(TraceabilityMethodExecutionError):
        service.execute(request)


def test_request_from_mapping_rejects_missing_keys() -> None:
    with pytest.raises(InvalidTraceabilityRequestError):
        RequirementSnapshot.from_mapping({"requirements": []})


def test_request_rejects_unknown_selected_requirement_ids() -> None:
    with pytest.raises(InvalidTraceabilityRequestError):
        TraceabilityRequest(
            requirements=_build_requirements_snapshot(),
            evidence=_build_evidence_snapshot(),
            selected_requirement_ids=["REQ-404"],
        )


def test_request_rejects_unknown_selected_evidence_run_ids() -> None:
    with pytest.raises(InvalidTraceabilityRequestError):
        TraceabilityRequest(
            requirements=_build_requirements_snapshot(),
            evidence=_build_evidence_snapshot(),
            selected_evidence_run_ids=["run-404"],
        )


def test_traceability_run_rejects_naive_timestamps() -> None:
    with pytest.raises(ValueError):
        TraceabilityRun(method_name="baseline", started_at=datetime(2026, 1, 1, 12, 0, 0))


def test_baseline_returns_uncovered_coverage_and_no_links() -> None:
    result = build_default_traceability_service().execute(
        TraceabilityRequest(
            requirements=_build_requirements_snapshot(),
            evidence=_build_evidence_snapshot(),
        )
    )

    assert result.run.method_name == "baseline"
    assert result.summary.requirement_count == 2
    assert result.summary.uncovered_requirement_count == 2
    assert result.summary.trace_link_count == 0
    assert result.summary.trace_evidence_count == 0
    assert len(result.requirement_results) == 2
    assert result.requirement_results[0].artifact_coverage is not None
    assert result.requirement_results[0].artifact_coverage.coverage_status == CoverageStatus.UNCOVERED
    assert result.requirement_results[0].trace_links == []
    assert result.requirement_results[0].trace_evidence == []


def test_baseline_only_processes_selected_requirements() -> None:
    result = build_default_traceability_service().execute(
        TraceabilityRequest(
            requirements=_build_requirements_snapshot(),
            evidence=_build_evidence_snapshot(),
            selected_requirement_ids=["REQ-2"],
        )
    )

    assert result.summary.requirement_count == 1
    assert [item.requirement_id for item in result.requirement_results] == ["REQ-2"]


def test_baseline_explicitly_ignores_selected_evidence_run_ids() -> None:
    result = build_default_traceability_service().execute(
        TraceabilityRequest(
            requirements=_build_requirements_snapshot(),
            evidence=_build_evidence_snapshot(),
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
        TraceabilityRequest(requirements=empty_requirements, evidence=_build_evidence_snapshot())
    )

    assert result.summary.requirement_count == 0
    assert result.requirement_results == []
    assert result.run.total_requirement_count == 0
