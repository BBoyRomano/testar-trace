from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from reqtrace.domain.coverage import (
    CoverageReport,
    CoverageSummary,
    MatchEvidence,
    OccurrenceStatus,
    RequirementOccurrence,
    RequirementOccurrenceStep,
    RequirementResult,
    RequirementStatus,
    RequirementUnitResult,
    RequirementUnitStatus,
)
from reqtrace.domain.requirements import RequirementCatalog, RequirementUnit
from reqtrace.domain.state_graph import Observation, StateGraph, Transition


_WORD_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "be",
    "by",
    "from",
    "that",
    "this",
    "will",
    "user",
    "appears",
    "appear",
    "selects",
    "select",
    "clicks",
    "click",
    "enters",
    "enter",
    "changes",
    "change",
    "located",
    "page",
    "field",
    "button",
    "option",
}


def normalize_text(value: str) -> list[str]:
    return _WORD_RE.findall(value.lower())


def unit_tokens(unit: RequirementUnit) -> tuple[str, ...]:
    tokens = normalize_text(unit.text)
    filtered = [token for token in tokens if token not in _STOPWORDS]
    return tuple(dict.fromkeys(filtered))


@dataclass(frozen=True)
class ObservationMatch:
    state_id: str
    observation: Observation


def find_observation_matches(
    state_graph: StateGraph,
    unit: RequirementUnit,
) -> tuple[ObservationMatch, ...]:
    tokens = unit_tokens(unit)
    if not tokens:
        return ()

    matches: list[ObservationMatch] = []

    for state in state_graph.states:
        for observation in state.observations:
            observation_tokens = set(normalize_text(observation.value))
            overlap = [token for token in tokens if token in observation_tokens]
            if overlap:
                matches.append(ObservationMatch(
                    state_id=state.id, observation=observation))

    return tuple(matches)


def transition_identifier(transition: Transition, index: int) -> str:
    action_id = transition.metadata.get("action_id")
    if isinstance(action_id, str) and action_id:
        return action_id
    return f"T{index}"


def classify_unit(
    unit: RequirementUnit,
    matches: tuple[ObservationMatch, ...],
    transition_ids: tuple[str, ...],
) -> RequirementUnitResult:
    tokens = unit_tokens(unit)

    unique_hits = {
        token
        for token in tokens
        for match in matches
        if token in set(normalize_text(match.observation.value))
    }

    if tokens and len(unique_hits) == len(tokens):
        status = RequirementUnitStatus.FOUND
    elif unique_hits:
        status = RequirementUnitStatus.PARTIALLY_FOUND
    else:
        status = RequirementUnitStatus.NOT_FOUND

    evidence = ()
    if matches:
        evidence = (
            MatchEvidence(
                state_ids=tuple(dict.fromkeys(
                    match.state_id for match in matches)),
                transition_ids=transition_ids,
                observations=tuple(
                    dict.fromkeys(match.observation.value for match in matches)
                ),
                explanation=(
                    f"Matched {len(matches)} observation(s) for requirement unit "
                    f"'{unit.id}' using path_occurrence_v1."
                ),
                metadata={},
            ),
        )

    return RequirementUnitResult(
        requirement_id="",
        unit_id=unit.id,
        status=status,
        evidence=evidence,
        metadata={},
    )


def transition_ids_for_states(
    transitions_by_state_pair: dict[tuple[str, str], list[str]],
    state_ids: tuple[str, ...],
) -> tuple[str, ...]:
    collected: list[str] = []

    for source_state_id in state_ids:
        for target_state_id in state_ids:
            if source_state_id == target_state_id:
                continue
            collected.extend(
                transitions_by_state_pair.get(
                    (source_state_id, target_state_id), [])
            )

    return tuple(dict.fromkeys(collected))


def build_transition_indexes(
    transitions: tuple[Transition, ...],
) -> tuple[dict[str, list[str]], dict[tuple[str, str], list[str]]]:
    transitions_by_state: dict[str, list[str]] = defaultdict(list)
    transitions_by_state_pair: dict[tuple[str,
                                          str], list[str]] = defaultdict(list)

    for index, transition in enumerate(transitions, start=1):
        transition_id = transition_identifier(transition, index)

        transitions_by_state[transition.source_id].append(transition_id)
        transitions_by_state[transition.target_id].append(transition_id)
        transitions_by_state_pair[(transition.source_id, transition.target_id)].append(
            transition_id
        )

    return dict(transitions_by_state), dict(transitions_by_state_pair)


def deduplicate_steps(
    steps: list[RequirementOccurrenceStep],
) -> tuple[RequirementOccurrenceStep, ...]:
    unique_steps: list[RequirementOccurrenceStep] = []
    seen_unit_ids: set[str] = set()

    for step in steps:
        if step.unit_id in seen_unit_ids:
            continue
        seen_unit_ids.add(step.unit_id)
        unique_steps.append(step)

    return tuple(unique_steps)


def connected_components_for_requirement(
    unit_results: tuple[RequirementUnitResult, ...],
    transitions_by_state: dict[str, list[str]],
) -> tuple[tuple[str, ...], ...]:
    relevant_states: set[str] = set()

    for unit_result in unit_results:
        for evidence in unit_result.evidence:
            relevant_states.update(evidence.state_ids)

    if not relevant_states:
        return ()

    adjacency: dict[str, set[str]] = {
        state_id: set() for state_id in relevant_states}

    for source_state_id in relevant_states:
        for other_state_id in relevant_states:
            if source_state_id == other_state_id:
                continue
            shared_transition = bool(
                set(transitions_by_state.get(source_state_id, []))
                & set(transitions_by_state.get(other_state_id, []))
            )
            if shared_transition:
                adjacency[source_state_id].add(other_state_id)

    visited: set[str] = set()
    components: list[tuple[str, ...]] = []

    for state_id in sorted(relevant_states):
        if state_id in visited:
            continue

        stack = [state_id]
        component: list[str] = []

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            stack.extend(sorted(adjacency[current] - visited))

        components.append(tuple(sorted(component)))

    return tuple(components)


def build_occurrences(
    requirement_id: str,
    unit_results: tuple[RequirementUnitResult, ...],
    transitions_by_state: dict[str, list[str]],
    transitions_by_state_pair: dict[tuple[str, str], list[str]],
) -> tuple[RequirementOccurrence, ...]:
    components = connected_components_for_requirement(
        unit_results, transitions_by_state)
    occurrences: list[RequirementOccurrence] = []

    for index, component_state_ids in enumerate(components, start=1):
        steps_for_component: list[RequirementOccurrenceStep] = []

        for unit_result in unit_results:
            if unit_result.status == RequirementUnitStatus.NOT_FOUND:
                continue

            matching_evidence = tuple(
                evidence
                for evidence in unit_result.evidence
                if set(evidence.state_ids) & set(component_state_ids)
            )
            if not matching_evidence:
                continue

            steps_for_component.append(
                RequirementOccurrenceStep(
                    unit_id=unit_result.unit_id,
                    status=unit_result.status,
                    evidence=matching_evidence,
                    metadata=unit_result.metadata,
                )
            )

        unique_steps = deduplicate_steps(steps_for_component)
        transition_ids = transition_ids_for_states(
            transitions_by_state_pair,
            component_state_ids,
        )

        if unique_steps and all(step.status == RequirementUnitStatus.FOUND for step in unique_steps):
            status = OccurrenceStatus.FOUND
        else:
            status = OccurrenceStatus.PARTIALLY_FOUND

        occurrences.append(
            RequirementOccurrence(
                occurrence_id=f"{requirement_id}#{index}",
                status=status,
                state_ids=component_state_ids,
                transition_ids=transition_ids,
                steps=unique_steps,
                metadata={},
            )
        )

    return tuple(occurrences)


def aggregate_requirement_status(
    unit_results: tuple[RequirementUnitResult, ...],
) -> RequirementStatus:
    if unit_results and all(unit.status == RequirementUnitStatus.FOUND for unit in unit_results):
        return RequirementStatus.FOUND

    if any(
        unit.status in {RequirementUnitStatus.FOUND,
                        RequirementUnitStatus.PARTIALLY_FOUND}
        for unit in unit_results
    ):
        return RequirementStatus.PARTIALLY_FOUND

    return RequirementStatus.NOT_FOUND


class PathOccurrenceV1Analyzer:
    name = "path_occurrence_v1"

    def analyze(
        self,
        state_graph: StateGraph,
        requirement_catalog: RequirementCatalog,
    ) -> CoverageReport:
        results: list[RequirementResult] = []
        transitions_by_state, transitions_by_state_pair = build_transition_indexes(
            state_graph.transitions
        )

        for requirement in requirement_catalog.requirements:
            unit_results: list[RequirementUnitResult] = []

            for unit in requirement.units:
                matches = find_observation_matches(state_graph, unit)
                matched_state_ids = tuple(dict.fromkeys(
                    match.state_id for match in matches))
                transition_ids = transition_ids_for_states(
                    transitions_by_state_pair,
                    matched_state_ids,
                )
                unit_result = classify_unit(unit, matches, transition_ids)
                unit_result = RequirementUnitResult(
                    requirement_id=requirement.id,
                    unit_id=unit_result.unit_id,
                    status=unit_result.status,
                    evidence=unit_result.evidence,
                    metadata=unit_result.metadata,
                )
                unit_results.append(unit_result)

            occurrences = build_occurrences(
                requirement.id,
                tuple(unit_results),
                transitions_by_state,
                transitions_by_state_pair,
            )
            requirement_status = aggregate_requirement_status(
                tuple(unit_results))

            results.append(
                RequirementResult(
                    requirement_id=requirement.id,
                    status=requirement_status,
                    unit_results=tuple(unit_results),
                    occurrences=occurrences,
                    metadata={},
                )
            )

        found = sum(1 for result in results if result.status ==
                    RequirementStatus.FOUND)
        partially_found = sum(
            1 for result in results if result.status == RequirementStatus.PARTIALLY_FOUND
        )
        not_found = sum(
            1 for result in results if result.status == RequirementStatus.NOT_FOUND
        )

        return CoverageReport(
            results=tuple(results),
            summary=CoverageSummary(
                total_requirements=len(results),
                found=found,
                partially_found=partially_found,
                not_found=not_found,
            ),
            metadata={
                "analyzer": self.name,
            },
        )
