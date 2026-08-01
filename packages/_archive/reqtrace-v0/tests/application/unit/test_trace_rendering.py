from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reqtrace.application.methods.common.trace_rendering import build_display_trace
from reqtrace.application.results import MatchRole, TraceKind, TracePathItemKind
from reqtrace.domain.evidence.enums import ActionKind
from reqtrace.domain.evidence.models import Action, ApplicationState, Transition
from reqtrace.domain.traceability.enums import EvidenceTargetType


@dataclass(frozen=True)
class _CandidateStub:
    target_type: EvidenceTargetType
    target_id: str
    state_id: str | None
    transition_id: str | None
    action_id: str | None
    element_id: str | None


@dataclass(frozen=True)
class _PlacementStub:
    fragment_id: str
    candidate: _CandidateStub
    position: int
    matched_tokens: tuple[str, ...]
    score: float


def test_build_display_trace_builds_path_and_metadata() -> None:
    states_by_id = {
        "s1": ApplicationState(id="s1", title="State 1"),
        "s2": ApplicationState(id="s2", title="State 2"),
    }
    actions_by_id = {
        "a1": Action(id="a1", kind=ActionKind.CLICK, description="Click login"),
    }
    transitions_by_order = {
        0: Transition(id="t1", from_state_id="s1", to_state_id="s2", action_id="a1"),
    }
    placements = (
        _PlacementStub(
            fragment_id="REQ-1:F-1",
            candidate=_CandidateStub(
                target_type=EvidenceTargetType.TRANSITION,
                target_id="t1",
                state_id="s1",
                transition_id="t1",
                action_id="a1",
                element_id="e1",
            ),
            position=0,
            matched_tokens=("login",),
            score=0.88,
        ),
    )

    def enrich_mapping(placement: _PlacementStub, mapping: dict[str, Any]) -> None:
        mapping["extra"] = f"fragment:{placement.fragment_id}"

    trace = build_display_trace(
        trace_kind=TraceKind.MAIN,
        placements=placements,
        states_by_id=states_by_id,
        actions_by_id=actions_by_id,
        transitions_by_order=transitions_by_order,
        window=(0, 0),
        enrich_mapping=enrich_mapping,
    )

    assert trace.path[0].kind == TracePathItemKind.STATE
    assert trace.path[1].kind == TracePathItemKind.TRANSITION
    assert trace.path[1].match_role == MatchRole.MATCHED
    assert trace.matched_fragment_ids == ["REQ-1:F-1"]
    step_mappings = trace.metadata["step_mappings"]
    assert isinstance(step_mappings, list)
    assert step_mappings[0]["extra"] == "fragment:REQ-1:F-1"

