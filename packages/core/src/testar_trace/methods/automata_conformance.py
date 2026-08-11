"""Exact finite-automata conformance for approved formal requirements."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

from testar_trace.domain.formal_requirements import (
    FormalConformancePolicy,
    FormalizationStatus,
    RequirementObservable,
    TraceStartMode,
)
from testar_trace.domain.requirement_paths import materialize_requirement_paths
from testar_trace.domain.requirements import RequirementPath, RequirementSet
from testar_trace.domain.state_models import (
    StateModel,
    StateModelCollection,
    Transition,
)
from testar_trace.domain.traceability import (
    TraceabilityResult,
    TraceEvidenceBasis,
    TraceLink,
    TraceOccurrence,
    TraceOccurrenceStatus,
    TraceTargetKind,
    TraceTargetRef,
)
from testar_trace.execution import TraceContext
from testar_trace.methods._formal_matching import (
    index_formal_model,
    transition_matches_observable,
)
from testar_trace.methods._path_assessments import (
    PathFinding,
    build_path_assessments,
    requirement_source_refs,
)

__all__ = ["trace_with_automata_conformance"]

_METHOD_ID = "automata-conformance"


@dataclass(frozen=True, slots=True)
class _MatchedTransition:
    element_index: int
    transition: Transition


@dataclass(frozen=True, slots=True)
class _SearchState:
    state_id: str
    position: int
    intervening: int
    route: tuple[Transition, ...]
    matches: tuple[_MatchedTransition, ...]


@dataclass(frozen=True, slots=True)
class _SearchResult:
    route: tuple[Transition, ...]
    matches: tuple[_MatchedTransition, ...]


def trace_with_automata_conformance(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    context: TraceContext,
) -> TraceabilityResult:
    """Check approved finite requirement paths against state-model automata."""
    context.raise_if_cancelled()
    materialization = materialize_requirement_paths(requirements)
    total = len(materialization.paths) * len(state_models.models)
    context.report(
        "automata-conformance.started",
        message="Formal conformance checking started",
        total=total,
        metadata={
            "total_requirements": len(requirements.requirements),
            "total_paths": len(materialization.paths),
        },
    )

    formalization = requirements.formalization
    approved = (
        formalization is not None
        and formalization.status is FormalizationStatus.APPROVED
    )
    observables = (
        {item.id: item for item in formalization.observables}
        if formalization is not None
        else {}
    )
    bindings = (
        {
            item.requirement_element_id: observables[item.observable_id]
            for item in formalization.bindings
        }
        if formalization is not None
        else {}
    )
    policy = formalization.policy if formalization is not None else None
    findings: list[PathFinding] = []
    occurrences: list[TraceOccurrence] = []
    links: list[TraceLink] = []
    completed = 0

    for model in state_models.models:
        for path in materialization.paths:
            context.raise_if_cancelled()
            path_observables = tuple(bindings.get(item) for item in path.element_ids)
            assessable = approved and all(item is not None for item in path_observables)
            if assessable and policy is not None:
                result = _search_product(
                    model,
                    tuple(
                        item
                        for item in path_observables
                        if isinstance(item, RequirementObservable)
                    ),
                    policy,
                )
                occurrence, occurrence_links = _build_occurrence(
                    path,
                    model,
                    result,
                )
                occurrences.append(occurrence)
                links.extend(occurrence_links)
                findings.append(
                    PathFinding(
                        path_id=path.id,
                        state_model_id=model.id,
                        assessable=True,
                        occurrence_id=occurrence.id,
                        covered_element_ids=occurrence.covered_element_ids,
                        missing_element_ids=occurrence.missing_element_ids,
                        rationale=occurrence.rationale or "",
                    )
                )
            else:
                findings.append(
                    PathFinding(
                        path_id=path.id,
                        state_model_id=model.id,
                        assessable=False,
                        missing_element_ids=_unique(path.element_ids),
                        rationale=_not_assessable_rationale(
                            formalization_exists=formalization is not None,
                            approved=approved,
                            missing_bindings=tuple(
                                element_id
                                for element_id, observable in zip(
                                    path.element_ids,
                                    path_observables,
                                    strict=True,
                                )
                                if observable is None
                            ),
                        ),
                    )
                )
            completed += 1
            context.report(
                "automata-conformance.path",
                message=f"Checked formal requirement path {path.id}",
                completed=completed,
                total=total,
                metadata={
                    "requirement_id": path.requirement_id,
                    "state_model_id": model.id,
                },
            )

    assessments = build_path_assessments(
        method_id=_METHOD_ID,
        evidence_label="formally bound state-model routes",
        requirements=requirements,
        state_models=state_models,
        materialization=materialization,
        findings=findings,
    )
    result = TraceabilityResult(
        id=_METHOD_ID,
        title="Formal conformance result",
        path_materialization=materialization,
        assessments=assessments,
        links=tuple(links),
        occurrences=tuple(occurrences),
        requirement_source_refs=requirement_source_refs(requirements),
        state_model_source_refs=state_models.source_refs,
        metadata={
            "method": _METHOD_ID,
            "analysis": "formal-path-conformance",
            "evidence_basis": TraceEvidenceBasis.FORMAL_MODEL_CHECK.value,
            "formalization_status": (
                formalization.status.value if formalization is not None else "missing"
            ),
            "formalization_schema_version": (
                formalization.schema_version if formalization is not None else None
            ),
            "path_materialization_exhaustive": materialization.is_exhaustive,
            "state_model_collection_id": state_models.id,
        },
    )
    context.report(
        "automata-conformance.completed",
        message="Formal conformance checking completed",
        completed=total,
        total=total,
    )
    return result


def _search_product(
    model: StateModel,
    observables: tuple[RequirementObservable, ...],
    policy: FormalConformancePolicy,
) -> _SearchResult:
    index = index_formal_model(model)
    outgoing: dict[str, tuple[Transition, ...]] = {}
    for state in model.states:
        outgoing[state.id] = tuple(
            sorted(
                (
                    transition
                    for transition in model.transitions
                    if transition.source_state_id == state.id
                ),
                key=lambda item: item.id,
            )
        )
    start_ids = (
        model.initial_state_ids
        if policy.start_mode is TraceStartMode.MODEL_INITIAL
        else tuple(state.id for state in model.states)
    )
    queue = deque(
        _SearchState(
            state_id=state_id,
            position=0,
            intervening=0,
            route=(),
            matches=(),
        )
        for state_id in start_ids
    )
    visited = {(item.state_id, item.position, item.intervening) for item in queue}
    best = _SearchResult(route=(), matches=())

    while queue:
        current = queue.popleft()
        if _search_key(current.route, current.matches) > _search_key(
            best.route, best.matches
        ):
            best = _SearchResult(route=current.route, matches=current.matches)
        for transition in outgoing.get(current.state_id, ()):
            target_id = transition.target_state_id
            matches_next = transition_matches_observable(
                transition,
                observables[current.position],
                index,
            )
            if matches_next:
                next_position = current.position + 1
                matched = _SearchState(
                    state_id=target_id or current.state_id,
                    position=next_position,
                    intervening=0,
                    route=(*current.route, transition),
                    matches=(
                        *current.matches,
                        _MatchedTransition(current.position, transition),
                    ),
                )
                if next_position == len(observables):
                    return _SearchResult(
                        route=matched.route,
                        matches=matched.matches,
                    )
                if target_id is not None:
                    _enqueue(queue, visited, matched)

            if (
                policy.allow_intervening_transitions
                and current.intervening < policy.maximum_intervening_transitions
                and target_id is not None
            ):
                _enqueue(
                    queue,
                    visited,
                    _SearchState(
                        state_id=target_id,
                        position=current.position,
                        intervening=current.intervening + 1,
                        route=(*current.route, transition),
                        matches=current.matches,
                    ),
                )
    return best


def _enqueue(
    queue: deque[_SearchState],
    visited: set[tuple[str, int, int]],
    state: _SearchState,
) -> None:
    key = (state.state_id, state.position, state.intervening)
    if key not in visited:
        visited.add(key)
        queue.append(state)


def _build_occurrence(
    path: RequirementPath,
    model: StateModel,
    result: _SearchResult,
) -> tuple[TraceOccurrence, tuple[TraceLink, ...]]:
    covered_positions = {item.element_index for item in result.matches}
    covered_ids = _unique(
        path.element_ids[index] for index in sorted(covered_positions)
    )
    missing_ids = _unique(
        element_id
        for index, element_id in enumerate(path.element_ids)
        if index not in covered_positions
    )
    occurrence_id = f"{_METHOD_ID}:occurrence:{path.id}:{model.id}"
    links = tuple(
        TraceLink(
            id=(
                f"{_METHOD_ID}:link:{path.id}:{match.element_index}:"
                f"{model.id}:{match.transition.id}"
            ),
            requirement_id=path.requirement_id,
            requirement_element_id=path.element_ids[match.element_index],
            state_model_id=model.id,
            target_ref=TraceTargetRef(
                kind=TraceTargetKind.TRANSITION,
                target_id=match.transition.id,
            ),
            score=1.0,
            occurrence_id=occurrence_id,
            rationale="The transition satisfies the approved formal observable.",
            metadata={
                "method": _METHOD_ID,
                "path_position": match.element_index,
                "match_kind": "approved-observable",
            },
        )
        for match in result.matches
    )
    full = len(covered_positions) == len(path.element_ids) and bool(path.element_ids)
    target_path = tuple(
        TraceTargetRef(
            kind=TraceTargetKind.TRANSITION,
            target_id=transition.id,
        )
        for transition in result.route
    ) or (TraceTargetRef(kind=TraceTargetKind.STATE_MODEL, target_id=model.id),)
    rationale = (
        f"All {len(path.element_ids)} formal events are accepted by the "
        "state-model product."
        if full
        else (
            f"The state-model product accepts {len(covered_positions)} of "
            f"{len(path.element_ids)} formal events before no continuation exists."
        )
    )
    occurrence = TraceOccurrence(
        id=occurrence_id,
        requirement_id=path.requirement_id,
        flow_id=path.flow_id,
        path_id=path.id,
        state_model_id=model.id,
        evidence_basis=TraceEvidenceBasis.FORMAL_MODEL_CHECK,
        status=TraceOccurrenceStatus.FULL if full else TraceOccurrenceStatus.PARTIAL,
        target_path=target_path,
        covered_element_ids=covered_ids,
        missing_element_ids=missing_ids,
        link_ids=tuple(link.id for link in links),
        score=len(covered_positions) / len(path.element_ids),
        rationale=rationale,
        metadata={
            "method": _METHOD_ID,
            "matched_position_count": len(covered_positions),
            "total_position_count": len(path.element_ids),
            "product_route_transition_count": len(result.route),
        },
    )
    return occurrence, links


def _not_assessable_rationale(
    *,
    formalization_exists: bool,
    approved: bool,
    missing_bindings: tuple[str, ...],
) -> str:
    if not formalization_exists:
        return "No formal requirements are attached to the requirement set."
    if not approved:
        return "The attached formal requirements have not been approved."
    return "Formal observable bindings are missing for: " + ", ".join(missing_bindings)


def _search_key(
    route: tuple[Transition, ...], matches: tuple[_MatchedTransition, ...]
) -> tuple[int, int]:
    return (len(matches), -len(route))


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
