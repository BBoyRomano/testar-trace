from __future__ import annotations

from reqtrace.analysis.trace_models import TraceStepMatch
from reqtrace.domain.coverage import MatchEvidence, RequirementUnitResult


def build_trace_step_matches(
    unit_results: tuple[RequirementUnitResult, ...],
) -> tuple[TraceStepMatch, ...]:
    matches: list[TraceStepMatch] = []

    for unit_result in unit_results:
        matches.extend(
            _build_trace_step_matches_for_unit_result(unit_result)
        )

    return tuple(matches)


def _build_trace_step_matches_for_unit_result(
    unit_result: RequirementUnitResult,
) -> tuple[TraceStepMatch, ...]:
    sequence = _extract_sequence(unit_result.unit_id)

    return tuple(
        _build_trace_step_match(
            requirement_id=unit_result.requirement_id,
            unit_id=unit_result.unit_id,
            unit_kind=unit_result.metadata.get("unit_kind", "unknown"),
            sequence=sequence,
            status=unit_result.status.value,
            evidence=evidence,
        )
        for evidence in unit_result.evidence
    )


def _build_trace_step_match(
    requirement_id: str,
    unit_id: str,
    unit_kind: str,
    sequence: int | None,
    status: str,
    evidence: MatchEvidence,
) -> TraceStepMatch:
    from reqtrace.domain.coverage import RequirementUnitStatus

    return TraceStepMatch(
        requirement_id=requirement_id,
        unit_id=unit_id,
        unit_kind=unit_kind,
        sequence=sequence,
        state_ids=evidence.state_ids,
        transition_ids=evidence.transition_ids,
        matched_observations=evidence.observations,
        status=RequirementUnitStatus(status),
        explanation=evidence.explanation,
        metadata=dict(evidence.metadata),
    )


def _extract_sequence(unit_id: str) -> int | None:
    last_part = unit_id.rsplit(".", maxsplit=1)[-1]
    if last_part.isdigit():
        return int(last_part)
    return None
