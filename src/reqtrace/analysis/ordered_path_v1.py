from __future__ import annotations

import re
from collections import defaultdict, deque
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


def build_transition_indexes(
    transitions: tuple[Transition, ...],
) -> tuple[
    dict[str, list[str]],
    dict[tuple[str, str], list[str]],
    dict[str, set[str]],
]:
    transitions_by_state: dict[str, list[str]] = defaultdict(list)
    transitions_by_state_pair: dict[tuple[str,
                                          str], list[str]] = defaultdict(list)
    outgoing_neighbors: dict[str, set[str]] = defaultdict(set)

    for index, transition in enumerate(transitions, start=1):
        transition_id = transition_identifier(transition, index)

        transitions_by_state[transition.source_id].append(transition_id)
        transitions_by_state[transition.target_id].append(transition_id)
        transitions_by_state_pair[(transition.source_id, transition.target_id)].append(
            transition_id
        )
        outgoing_neighbors[transition.source_id].add(transition.target_id)

    return dict(transitions_by_state), dict(transitions_by_state_pair), dict(outgoing_neighbors)


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


def shortest_path_length(
    start_state_id: str,
    end_state_id: str,
    outgoing_neighbors: dict[str, set[str]],
) -> int | None:
    if start_state_id == end_state_id:
        return 0

    visited = {start_state_id}
    queue: deque[tuple[str, int]] = deque([(start_state_id, 0)])

    while queue:
        current, distance = queue.popleft()

        for neighbor in sorted(outgoing_neighbors.get(current, set())):
            if neighbor == end_state_id:
                return distance + 1
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append((neighbor, distance + 1))

    return None


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
                    f"'{unit.id}' using ordered_path_v1."
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


def choose_ordered_state_sequence(
    unit_results: tuple[RequirementUnitResult, ...],
    outgoing_neighbors: dict[str, set[str]],
) -> tuple[tuple[str, RequirementOccurrenceStep], ...]:
    chosen: list[tuple[str, RequirementOccurrenceStep]] = []
    previous_state_id: str | None = None

    for unit_result in unit_results:
        if unit_result.status == RequirementUnitStatus.NOT_FOUND or not unit_result.evidence:
            continue

        candidate_state_ids = unit_result.evidence[0].state_ids
        if not candidate_state_ids:
            continue

        best_state_id = None
        best_distance = None

        for candidate_state_id in candidate_state_ids:
            if previous_state_id is None:
                best_state_id = candidate_state_id
                break

            distance = shortest_path_length(
                previous_state_id,
                candidate_state_id,
                outgoing_neighbors,
            )
            if distance is None:
                continue
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_state_id = candidate_state_id

        if best_state_id is None:
            best_state_id = candidate_state_ids[0]

        matching_evidence = tuple(
            evidence
            for evidence in unit_result.evidence
            if best_state_id in evidence.state_ids
        ) or unit_result.evidence

        step = RequirementOccurrenceStep(
            unit_id=unit_result.unit_id,
            status=unit_result.status,
            evidence=matching_evidence,
            metadata=unit_result.metadata,
        )
        chosen.append((best_state_id, step))
        previous_state_id = best_state_id

    return tuple(chosen)


def build_ordered_occurrences(
    requirement_id: str,
    unit_results: tuple[RequirementUnitResult, ...],
    transitions_by_state_pair: dict[tuple[str, str], list[str]],
    outgoing_neighbors: dict[str, set[str]],
) -> tuple[RequirementOccurrence, ...]:
    ordered_sequence = choose_ordered_state_sequence(
        unit_results, outgoing_neighbors)
    if not ordered_sequence:
        return ()

    state_ids = tuple(state_id for state_id, _ in ordered_sequence)
    steps = tuple(step for _, step in ordered_sequence)

    ordered_transition_ids: list[str] = []
    for index in range(len(state_ids) - 1):
        source_state_id = state_ids[index]
        target_state_id = state_ids[index + 1]
        ordered_transition_ids.extend(
            transitions_by_state_pair.get(
                (source_state_id, target_state_id), [])
        )

    unique_transition_ids = tuple(dict.fromkeys(ordered_transition_ids))

    if steps and all(step.status == RequirementUnitStatus.FOUND for step in steps):
        status = OccurrenceStatus.FOUND
    else:
        status = OccurrenceStatus.PARTIALLY_FOUND

    return (
        RequirementOccurrence(
            occurrence_id=f"{requirement_id}#1",
            status=status,
            state_ids=state_ids,
            transition_ids=unique_transition_ids,
            steps=steps,
            metadata={},
        ),
    )


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


class OrderedPathV1Analyzer:
    name = "ordered_path_v1"

    def analyze(
        self,
        state_graph: StateGraph,
        requirement_catalog: RequirementCatalog,
    ) -> CoverageReport:
        results: list[RequirementResult] = []
        _, transitions_by_state_pair, outgoing_neighbors = build_transition_indexes(
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

            occurrences = build_ordered_occurrences(
                requirement.id,
                tuple(unit_results),
                transitions_by_state_pair,
                outgoing_neighbors,
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
