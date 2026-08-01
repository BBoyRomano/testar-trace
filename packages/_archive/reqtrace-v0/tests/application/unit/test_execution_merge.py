from __future__ import annotations

from dataclasses import dataclass

from reqtrace.application.methods.common.execution_merge import (
    prefer_candidate,
    range_length,
    range_overlap,
    same_execution_instance,
)


@dataclass(frozen=True)
class _ExecutionCandidate:
    flow_id: str
    core_positions: tuple[int, ...]
    display_range: tuple[int, int]
    quality: float


def test_range_length_is_inclusive() -> None:
    assert range_length((3, 3)) == 1
    assert range_length((2, 6)) == 5


def test_range_overlap_uses_shortest_window_ratio() -> None:
    assert range_overlap((0, 4), (2, 3)) == 1.0
    assert range_overlap((0, 2), (3, 5)) == 0.0


def test_same_execution_instance_uses_flow_and_overlap_thresholds() -> None:
    left = _ExecutionCandidate(
        flow_id="main",
        core_positions=(1, 2, 3),
        display_range=(0, 5),
        quality=0.7,
    )
    right = _ExecutionCandidate(
        flow_id="main",
        core_positions=(1, 2, 4),
        display_range=(1, 5),
        quality=0.8,
    )
    wrong_flow = _ExecutionCandidate(
        flow_id="alt",
        core_positions=(1, 2, 3),
        display_range=(0, 5),
        quality=0.9,
    )

    assert same_execution_instance(left, right)
    assert not same_execution_instance(left, wrong_flow)


def test_prefer_candidate_favors_compact_or_higher_quality_trace() -> None:
    current = _ExecutionCandidate(
        flow_id="main",
        core_positions=(1, 2),
        display_range=(0, 10),
        quality=0.90,
    )
    compact = _ExecutionCandidate(
        flow_id="main",
        core_positions=(1, 2),
        display_range=(0, 7),
        quality=0.84,
    )
    equal_len_better_quality = _ExecutionCandidate(
        flow_id="main",
        core_positions=(1, 2),
        display_range=(0, 10),
        quality=0.91,
    )
    weaker = _ExecutionCandidate(
        flow_id="main",
        core_positions=(1, 2),
        display_range=(0, 10),
        quality=0.89,
    )

    assert prefer_candidate(compact, current)
    assert prefer_candidate(equal_len_better_quality, current)
    assert not prefer_candidate(weaker, current)
