from __future__ import annotations

from collections import defaultdict

from reqtrace.analysis.trace_builders import build_trace_step_matches
from reqtrace.domain.coverage import (
    CoverageReport,
    OccurrenceStatus,
    RequirementOccurrence,
    RequirementOccurrenceStep,
    RequirementResult,
    RequirementUnitResult,
    RequirementUnitStatus,
)
from reqtrace.domain.requirements import RequirementCatalog
from reqtrace.domain.state_graph import StateGraph


def build_transition_indexes(
    transitions,
) -> tuple[dict[str, list[str]], dict[tuple[str, str], list[str]]]:
    transitions_by_state: dict[str, list[str]] = defaultdict(list)
    transitions_by_state_pair: dict[tuple[str,
                                          str], list[str]] = defaultdict(list)

    for transition in transitions:
        transitions_by_state[transition.source_id].append(transition.id)
        transitions_by_state[transition.target_id].append(transition.id)
        transitions_by_state_pair[(transition.source_id, transition.target_id)].append(
            transition.id
        )

    return transitions_by_state, transitions_by_state_pair


def _build_occurrence_steps_from_unit_results(
    unit_results: tuple[RequirementUnitResult, ...],
) -> tuple[RequirementOccurrenceStep, ...]:
    steps: list[RequirementOccurrenceStep] = []

    for unit_result in unit_results:
        unique_state_ids = tuple(
            dict.fromkeys(
                state_id
                for evidence in unit_result.evidence
                for state_id in evidence.state_ids
            )
        )
        unique_transition_ids = tuple(
            dict.fromkeys(
                transition_id
                for evidence in unit_result.evidence
                for transition_id in evidence.transition_ids
            )
        )
        unique_observations = tuple(
            dict.fromkeys(
                observation
                for evidence in unit_result.evidence
                for observation in evidence.observations
            )
        )

        if not unique_state_ids and not unique_transition_ids and not unique_observations:
            continue

        steps.append(
            RequirementOccurrenceStep(
                unit_id=unit_result.unit_id,
                status=unit_result.status,
                state_ids=unique_state_ids,
                transition_ids=unique_transition_ids,
                observations=unique_observations,
                metadata=dict(unit_result.metadata),
            )
        )

    return tuple(steps)


def build_occurrences(
    requirement_id: str,
    unit_results: tuple[RequirementUnitResult, ...],
    transitions_by_state: dict[str, list[str]],
) -> tuple[RequirementOccurrence, ...]:
    trace_matches = build_trace_step_matches(unit_results)

    if not trace_matches:
        return ()

    matches_by_state: dict[str, list] = defaultdict(list)
    for match in trace_matches:
        for state_id in match.state_ids:
            matches_by_state[state_id].append(match)

    occurrences: list[RequirementOccurrence] = []

    for index, (state_id, matches) in enumerate(sorted(matches_by_state.items()), start=1):
        unique_state_ids = tuple(
            dict.fromkeys(
                nested_state_id
                for match in matches
                for nested_state_id in match.state_ids
            )
        )

        transition_ids_from_matches = [
            transition_id
            for match in matches
            for transition_id in match.transition_ids
        ]
        transition_ids_from_state = transitions_by_state.get(state_id, [])
        unique_transition_ids = tuple(
            dict.fromkeys(transition_ids_from_matches +
                          transition_ids_from_state)
        )

        grouped_unit_results: dict[str, RequirementUnitResult] = {}
        for unit_result in unit_results:
            grouped_unit_results[unit_result.unit_id] = unit_result

        occurrence_steps = _build_occurrence_steps_from_unit_results(
            tuple(grouped_unit_results.values())
        )

        if occurrence_steps and all(
            step.status == RequirementUnitStatus.FOUND for step in occurrence_steps
        ):
            status = OccurrenceStatus.FOUND
        else:
            status = OccurrenceStatus.PARTIALLY_FOUND

        occurrences.append(
            RequirementOccurrence(
                occurrence_id=f"{requirement_id}.occ.{index}",
                status=status,
                state_ids=unique_state_ids,
                transition_ids=unique_transition_ids,
                steps=occurrence_steps,
                metadata={
                    "anchor_state_id": state_id,
                    "trace_match_count": len(matches),
                    "is_connected": True,
                },
            )
        )

    return tuple(occurrences)


class PathOccurrenceV1Analyzer:
    name = "path_occurrence_v1"

    def analyze(
        self,
        state_graph: StateGraph,
        requirement_catalog: RequirementCatalog,
    ) -> CoverageReport:
        from reqtrace.analysis.evidence_v1 import analyze_requirement_units
        from reqtrace.analysis.occurrence_v1 import aggregate_requirement_status
        from reqtrace.domain.coverage import summarize_results

        results: list[RequirementResult] = []
        transitions_by_state, _ = build_transition_indexes(
            state_graph.transitions)

        for requirement in requirement_catalog.requirements:
            unit_results = analyze_requirement_units(requirement, state_graph)
            requirement_status = aggregate_requirement_status(unit_results)
            occurrences = build_occurrences(
                requirement.id,
                tuple(unit_results),
                transitions_by_state,
            )

            results.append(
                RequirementResult(
                    requirement_id=requirement.id,
                    status=requirement_status,
                    unit_results=tuple(unit_results),
                    occurrences=occurrences,
                    metadata={},
                )
            )

        return CoverageReport(
            results=tuple(results),
            summary=summarize_results(tuple(results)),
            metadata={
                "state_count": len(state_graph.states),
                "transition_count": len(state_graph.transitions),
                "requirement_count": len(requirement_catalog.requirements),
                "status": "analyzed",
                "analyzer": self.name,
            },
        )
