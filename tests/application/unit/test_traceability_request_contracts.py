from __future__ import annotations

from datetime import datetime

import pytest

from reqtrace.application.exceptions import InvalidTraceabilityRequestError
from reqtrace.application.results import (
    EvidenceSnapshot,
    RequirementSnapshot,
    TraceabilityRequest,
    TraceabilityRun,
)


def test_request_from_mapping_rejects_missing_keys() -> None:
    with pytest.raises(InvalidTraceabilityRequestError):
        RequirementSnapshot.from_mapping({"requirements": []})


def test_request_rejects_unknown_selected_requirement_ids(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    with pytest.raises(InvalidTraceabilityRequestError):
        TraceabilityRequest(
            requirements=build_requirements_snapshot(),
            evidence=build_evidence_snapshot(),
            selected_requirement_ids=["REQ-404"],
        )


def test_request_rejects_unknown_selected_evidence_run_ids(
    build_evidence_snapshot,
    build_requirements_snapshot,
) -> None:
    with pytest.raises(InvalidTraceabilityRequestError):
        TraceabilityRequest(
            requirements=build_requirements_snapshot(),
            evidence=build_evidence_snapshot(),
            selected_evidence_run_ids=["run-404"],
        )


def test_evidence_snapshot_rejects_duplicate_state_ids() -> None:
    with pytest.raises(InvalidTraceabilityRequestError, match="Duplicate state ids"):
        EvidenceSnapshot.from_mapping(
            {
                "states": [
                    {"id": "state-1"},
                    {"id": "state-1"},
                ],
                "elements": [],
                "actions": [],
                "transitions": [],
                "runs": [],
                "observations": [],
                "attachments": [],
            }
        )


def test_traceability_run_rejects_naive_timestamps() -> None:
    with pytest.raises(ValueError):
        TraceabilityRun(method_name="baseline", started_at=datetime(2026, 1, 1, 12, 0, 0))
