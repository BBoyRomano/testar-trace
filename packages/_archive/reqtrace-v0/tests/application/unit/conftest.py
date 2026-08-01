from __future__ import annotations

from collections.abc import Callable

import pytest

from reqtrace.application.results import EvidenceSnapshot, RequirementSnapshot
from reqtrace.domain.evidence.enums import ExecutionRunStatus
from reqtrace.domain.evidence.models import ExecutionRun
from reqtrace.domain.requirements.enums import RequirementFragmentKind, RequirementKind
from reqtrace.domain.requirements.models import RequirementArtifact, RequirementFragment


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


@pytest.fixture
def build_requirements_snapshot() -> Callable[[], RequirementSnapshot]:
    return _build_requirements_snapshot


@pytest.fixture
def build_evidence_snapshot() -> Callable[[], EvidenceSnapshot]:
    return _build_evidence_snapshot
