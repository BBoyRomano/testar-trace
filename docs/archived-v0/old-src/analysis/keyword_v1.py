from __future__ import annotations

import re
from dataclasses import dataclass

from reqtrace.domain.coverage import (
    CoverageReport,
    CoverageSummary,
    MatchEvidence,
    RequirementResult,
    RequirementStatus,
    RequirementUnitResult,
    RequirementUnitStatus,
)
from reqtrace.domain.requirements import RequirementCatalog, RequirementUnit
from reqtrace.domain.state_graph import Observation, StateGraph


_WORD_RE = re.compile(r"[a-z0-9]+")


def normalize_text(value: str) -> list[str]:
    return _WORD_RE.findall(value.lower())


def keyword_tokens(unit: RequirementUnit) -> tuple[str, ...]:
    tokens = normalize_text(unit.text)
    stopwords = {
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
        "user",
        "appears",
        "selects",
        "clicks",
        "enters",
        "changes",
    }
    filtered = [token for token in tokens if token not in stopwords]
    return tuple(dict.fromkeys(filtered))


@dataclass(frozen=True)
class ObservationMatch:
    state_id: str
    observation: Observation


def find_observation_matches(
    state_graph: StateGraph,
    unit: RequirementUnit,
) -> tuple[ObservationMatch, ...]:
    tokens = keyword_tokens(unit)
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


def classify_unit(
    unit: RequirementUnit,
    matches: tuple[ObservationMatch, ...],
) -> RequirementUnitResult:
    tokens = keyword_tokens(unit)
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
                transition_ids=(),
                observations=tuple(
                    dict.fromkeys(match.observation.value for match in matches)
                ),
                explanation=f"Matched {len(matches)} observation(s) for requirement unit '{unit.id}'.",
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


class KeywordV1Analyzer:
    name = "keyword_v1"

    def analyze(
        self,
        state_graph: StateGraph,
        requirement_catalog: RequirementCatalog,
    ) -> CoverageReport:
        results: list[RequirementResult] = []

        for requirement in requirement_catalog.requirements:
            unit_results: list[RequirementUnitResult] = []

            for unit in requirement.units:
                matches = find_observation_matches(state_graph, unit)
                unit_result = classify_unit(unit, matches)
                unit_result = RequirementUnitResult(
                    requirement_id=requirement.id,
                    unit_id=unit_result.unit_id,
                    status=unit_result.status,
                    evidence=unit_result.evidence,
                    metadata=unit_result.metadata,
                )
                unit_results.append(unit_result)

            requirement_status = aggregate_requirement_status(
                tuple(unit_results))

            results.append(
                RequirementResult(
                    requirement_id=requirement.id,
                    status=requirement_status,
                    unit_results=tuple(unit_results),
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
