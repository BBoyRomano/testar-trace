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
from reqtrace.domain.requirements import RequirementCatalog, RequirementUnit, RequirementUnitKind
from reqtrace.domain.state_graph import Observation, ObservationKind, StateGraph


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


def allowed_kinds_for_unit(unit: RequirementUnit) -> set[ObservationKind]:
    if unit.kind == RequirementUnitKind.PRECONDITION:
        return {ObservationKind.TITLE, ObservationKind.TEXT, ObservationKind.LINK_TEXT, ObservationKind.URL}
    if unit.kind == RequirementUnitKind.TRIGGER:
        return {ObservationKind.ACTION_LABEL, ObservationKind.LINK_TEXT, ObservationKind.TEXT}
    if unit.kind == RequirementUnitKind.POSTCONDITION:
        return {ObservationKind.TITLE, ObservationKind.TEXT, ObservationKind.LINK_TEXT}
    return {
        ObservationKind.TITLE,
        ObservationKind.TEXT,
        ObservationKind.LINK_TEXT,
        ObservationKind.ACTION_LABEL,
    }


def find_observation_matches(
    state_graph: StateGraph,
    unit: RequirementUnit,
) -> tuple[ObservationMatch, ...]:
    tokens = unit_tokens(unit)
    if not tokens:
        return ()

    allowed_kinds = allowed_kinds_for_unit(unit)
    matches: list[ObservationMatch] = []

    for state in state_graph.states:
        for observation in state.observations:
            if observation.kind not in allowed_kinds:
                continue

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
                transition_ids=(),
                observations=tuple(dict.fromkeys(
                    match.observation.value for match in matches)),
                explanation=f"Matched {len(matches)} observation(s) for requirement unit '{unit.id}' using evidence_v1.",
                metadata={
                    "unit_kind": unit.kind.value,
                    "observation_kinds": tuple(
                        dict.fromkeys(
                            match.observation.kind.value for match in matches)
                    ),
                },
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


class EvidenceV1Analyzer:
    name = "evidence_v1"

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
            1 for result in results if result.status == RequirementStatus.PARTIALLY_FOUND)
        not_found = sum(1 for result in results if result.status ==
                        RequirementStatus.NOT_FOUND)

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
