"""Graph-constrained semantic alignment for requirement completeness."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field

from testar_trace.domain._validation import require_unit_interval
from testar_trace.domain.requirement_paths import (
    RequirementPath,
    materialize_requirement_paths,
)
from testar_trace.domain.requirements import RequirementElement, RequirementSet
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
from testar_trace.methods._path_assessments import (
    PathFinding,
    build_path_assessments,
    requirement_source_refs,
)
from testar_trace.methods._semantic_matching import (
    SemanticScore,
    TransitionSemanticCandidate,
    inverse_document_frequencies,
    score_element,
    transition_candidates,
)

__all__ = [
    "GraphAlignmentConfig",
    "GraphAlignmentMethod",
    "trace_with_graph_alignment",
]


_METHOD_ID = "graph-alignment"
_SCORER_ID = "weighted-token-f2-v2"


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphAlignmentConfig:
    """Configuration for deterministic graph-constrained alignment."""

    similarity_threshold: float = 0.30
    maximum_candidates_per_element: int = 12
    maximum_intervening_transitions: int = 12

    def __post_init__(self) -> None:
        require_unit_interval(self.similarity_threshold, "similarity_threshold")
        for name, value, minimum in (
            ("maximum_candidates_per_element", self.maximum_candidates_per_element, 1),
            (
                "maximum_intervening_transitions",
                self.maximum_intervening_transitions,
                0,
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
            if value < minimum:
                raise ValueError(f"{name} must be at least {minimum}")


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphAlignmentMethod:
    """Configured graph-alignment traceability method."""

    config: GraphAlignmentConfig = field(default_factory=GraphAlignmentConfig)

    def __post_init__(self) -> None:
        if not isinstance(self.config, GraphAlignmentConfig):
            raise TypeError("config must be a GraphAlignmentConfig")

    def __call__(
        self,
        requirements: RequirementSet,
        state_models: StateModelCollection,
        context: TraceContext,
    ) -> TraceabilityResult:
        return trace_with_graph_alignment(
            requirements,
            state_models,
            context,
            config=self.config,
        )


@dataclass(frozen=True, slots=True)
class _CandidateMatch:
    element_index: int
    element: RequirementElement
    candidate: TransitionSemanticCandidate
    semantic: SemanticScore


@dataclass(frozen=True, slots=True)
class _Alignment:
    matches: tuple[_CandidateMatch, ...]
    connectors: tuple[tuple[Transition, ...], ...]
    score_sum: float

    @property
    def gap_count(self) -> int:
        return sum(len(value) for value in self.connectors)


def trace_with_graph_alignment(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    context: TraceContext,
    *,
    config: GraphAlignmentConfig | None = None,
) -> TraceabilityResult:
    """Align every materialized requirement path to a connected graph route."""
    effective_config = GraphAlignmentConfig() if config is None else config
    if not isinstance(effective_config, GraphAlignmentConfig):
        raise TypeError("config must be a GraphAlignmentConfig")

    context.raise_if_cancelled()
    materialization = materialize_requirement_paths(requirements)
    total = len(materialization.paths) * len(state_models.models)
    context.report(
        "graph-alignment.started",
        message="Graph path alignment started",
        total=total,
        metadata={
            "total_requirements": len(requirements.requirements),
            "total_paths": len(materialization.paths),
        },
    )
    elements = {element.id: element for element in requirements.elements}
    occurrences: list[TraceOccurrence] = []
    links: list[TraceLink] = []
    findings: list[PathFinding] = []
    completed = 0

    for model in state_models.models:
        candidates = transition_candidates(model)
        idf = inverse_document_frequencies(candidates)
        connector_cache: dict[tuple[str, str], tuple[Transition, ...] | None] = {}
        for path in materialization.paths:
            context.raise_if_cancelled()
            occurrence, occurrence_links = _align_path(
                path,
                model,
                elements,
                candidates,
                idf,
                effective_config,
                connector_cache,
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
            completed += 1
            context.report(
                "graph-alignment.path",
                message=f"Aligned requirement path {path.id}",
                completed=completed,
                total=total,
                metadata={
                    "requirement_id": path.requirement_id,
                    "state_model_id": model.id,
                },
            )

    assessments = build_path_assessments(
        method_id=_METHOD_ID,
        evidence_label="connected state-model routes",
        requirements=requirements,
        state_models=state_models,
        materialization=materialization,
        findings=findings,
    )
    result = TraceabilityResult(
        id=_METHOD_ID,
        title="Graph path alignment result",
        path_materialization=materialization,
        assessments=assessments,
        links=tuple(links),
        occurrences=tuple(occurrences),
        requirement_source_refs=requirement_source_refs(requirements),
        state_model_source_refs=state_models.source_refs,
        metadata={
            "method": _METHOD_ID,
            "analysis": "ordered-path-completeness",
            "evidence_basis": TraceEvidenceBasis.STATE_MODEL_GRAPH.value,
            "scorer": _SCORER_ID,
            "similarity_threshold": effective_config.similarity_threshold,
            "maximum_candidates_per_element": (
                effective_config.maximum_candidates_per_element
            ),
            "maximum_intervening_transitions": (
                effective_config.maximum_intervening_transitions
            ),
            "path_materialization_exhaustive": materialization.is_exhaustive,
            "state_model_collection_id": state_models.id,
        },
    )
    context.report(
        "graph-alignment.completed",
        message="Graph path alignment completed",
        completed=total,
        total=total,
    )
    return result


def _align_path(
    path: RequirementPath,
    model: StateModel,
    elements: dict[str, RequirementElement],
    candidates: tuple[TransitionSemanticCandidate, ...],
    idf: dict[str, float],
    config: GraphAlignmentConfig,
    connector_cache: dict[tuple[str, str], tuple[Transition, ...] | None],
) -> tuple[TraceOccurrence, tuple[TraceLink, ...]]:
    path_elements = tuple(elements[element_id] for element_id in path.element_ids)
    matches_by_element = tuple(
        _rank_candidates(index, element, candidates, idf, config)
        for index, element in enumerate(path_elements)
    )
    alignment = _best_graph_alignment(
        model,
        matches_by_element,
        config.maximum_intervening_transitions,
        connector_cache,
    )
    covered_positions = {match.element_index for match in alignment.matches}
    covered_ids = _unique(
        path_elements[index].id for index in sorted(covered_positions)
    )
    missing_ids = _unique(
        element.id
        for index, element in enumerate(path_elements)
        if index not in covered_positions
    )
    occurrence_id = f"{_METHOD_ID}:occurrence:{path.id}:{model.id}"
    target_path = _alignment_target_path(alignment)
    if not target_path:
        target_path = (
            TraceTargetRef(kind=TraceTargetKind.STATE_MODEL, target_id=model.id),
        )
    coverage_ratio = (
        len(covered_positions) / len(path_elements) if path_elements else 0.0
    )
    mean_similarity = (
        alignment.score_sum / len(alignment.matches) if alignment.matches else 0.0
    )
    occurrence_score = coverage_ratio * mean_similarity
    full = len(covered_positions) == len(path_elements) and bool(path_elements)
    links = tuple(
        _trace_link(occurrence_id, path, model, match) for match in alignment.matches
    )
    rationale = (
        f"All {len(path_elements)} requirement elements align to one connected "
        "state-model route."
        if full
        else (
            f"{len(covered_positions)} of {len(path_elements)} requirement elements "
            "align in order on one connected state-model route."
        )
    )
    occurrence = TraceOccurrence(
        id=occurrence_id,
        requirement_id=path.requirement_id,
        flow_id=path.flow_id,
        path_id=path.id,
        state_model_id=model.id,
        evidence_basis=TraceEvidenceBasis.STATE_MODEL_GRAPH,
        status=TraceOccurrenceStatus.FULL if full else TraceOccurrenceStatus.PARTIAL,
        target_path=target_path,
        covered_element_ids=covered_ids,
        missing_element_ids=missing_ids,
        link_ids=tuple(link.id for link in links),
        score=occurrence_score,
        rationale=rationale,
        metadata={
            "method": _METHOD_ID,
            "matched_position_count": len(covered_positions),
            "total_position_count": len(path_elements),
            "connector_transition_count": alignment.gap_count,
            "mean_similarity": mean_similarity,
        },
    )
    return occurrence, links


def _rank_candidates(
    element_index: int,
    element: RequirementElement,
    candidates: tuple[TransitionSemanticCandidate, ...],
    idf: dict[str, float],
    config: GraphAlignmentConfig,
) -> tuple[_CandidateMatch, ...]:
    ranked: list[_CandidateMatch] = []
    for candidate in candidates:
        semantic = score_element(element, candidate.facets, idf)
        if semantic is None or semantic.score < config.similarity_threshold:
            continue
        ranked.append(
            _CandidateMatch(
                element_index=element_index,
                element=element,
                candidate=candidate,
                semantic=semantic,
            )
        )
    ranked.sort(
        key=lambda match: (
            -match.semantic.score,
            match.candidate.transition.id,
            match.semantic.facet,
        )
    )
    return tuple(ranked[: config.maximum_candidates_per_element])


def _best_graph_alignment(
    model: StateModel,
    matches_by_element: tuple[tuple[_CandidateMatch, ...], ...],
    maximum_gap: int,
    connector_cache: dict[tuple[str, str], tuple[Transition, ...] | None],
) -> _Alignment:
    best_by_candidate: dict[tuple[int, str], _Alignment] = {}
    all_alignments: list[_Alignment] = []
    for element_matches in matches_by_element:
        for match in element_matches:
            best = _Alignment(
                matches=(match,), connectors=(), score_sum=match.semantic.score
            )
            for previous in all_alignments:
                previous_match = previous.matches[-1]
                if (
                    previous_match.candidate.transition.id
                    == match.candidate.transition.id
                    and not _can_share_transition(previous_match, match)
                ):
                    continue
                connector = _connector(
                    model,
                    previous_match.candidate.transition,
                    match.candidate.transition,
                    maximum_gap,
                    connector_cache,
                )
                if connector is None:
                    continue
                proposed = _Alignment(
                    matches=(*previous.matches, match),
                    connectors=(*previous.connectors, connector),
                    score_sum=previous.score_sum + match.semantic.score,
                )
                if _alignment_key(proposed) > _alignment_key(best):
                    best = proposed
            best_by_candidate[(match.element_index, match.candidate.transition.id)] = (
                best
            )
        all_alignments.extend(
            best_by_candidate[(match.element_index, match.candidate.transition.id)]
            for match in element_matches
        )
    return max(all_alignments, key=_alignment_key, default=_Alignment((), (), 0.0))


def _can_share_transition(previous: _CandidateMatch, current: _CandidateMatch) -> bool:
    """Allow one atomic transition to support its distinct semantic roles.

    A source condition, the performed action, and an observed target condition may
    legitimately refer to the same transition. Two independent executable steps
    may not both consume the same action. A trigger and its immediately following
    authored step are the one intentional co-reference because use-case formats
    commonly repeat the triggering action as main step 1.
    """
    action_facets = {"action", "action-target"}
    if (
        previous.semantic.facet not in action_facets
        or current.semantic.facet not in action_facets
    ):
        return True
    return previous.element.kind == "trigger" and current.element.kind in {
        "main_step",
        "alternative_step",
        "exception_step",
    }


def _connector(
    model: StateModel,
    previous: Transition,
    current: Transition,
    maximum_gap: int,
    cache: dict[tuple[str, str], tuple[Transition, ...] | None],
) -> tuple[Transition, ...] | None:
    key = (previous.id, current.id)
    if key in cache:
        return cache[key]
    if previous.id == current.id:
        cache[key] = ()
        return ()
    if previous.target_state_id is None:
        cache[key] = None
        return None
    if previous.target_state_id == current.source_state_id:
        cache[key] = ()
        return ()

    outgoing: dict[str, list[Transition]] = {}
    for transition in model.transitions:
        outgoing.setdefault(transition.source_state_id, []).append(transition)
    for values in outgoing.values():
        values.sort(key=lambda transition: transition.id)

    queue: deque[tuple[str, tuple[Transition, ...]]] = deque(
        [(previous.target_state_id, ())]
    )
    visited = {previous.target_state_id}
    while queue:
        state_id, path = queue.popleft()
        if len(path) >= maximum_gap:
            continue
        for transition in outgoing.get(state_id, ()):
            if transition.id == current.id:
                continue
            next_path = (*path, transition)
            if transition.target_state_id == current.source_state_id:
                cache[key] = next_path
                return next_path
            if (
                transition.target_state_id is not None
                and transition.target_state_id not in visited
            ):
                visited.add(transition.target_state_id)
                queue.append((transition.target_state_id, next_path))
    cache[key] = None
    return None


def _alignment_target_path(alignment: _Alignment) -> tuple[TraceTargetRef, ...]:
    targets: list[TraceTargetRef] = []
    last_transition_id: str | None = None
    for index, match in enumerate(alignment.matches):
        if index > 0:
            for transition in alignment.connectors[index - 1]:
                targets.append(
                    TraceTargetRef(
                        kind=TraceTargetKind.TRANSITION,
                        target_id=transition.id,
                    )
                )
                last_transition_id = transition.id
        transition_ref = TraceTargetRef(
            kind=TraceTargetKind.TRANSITION,
            target_id=match.candidate.transition.id,
        )
        if transition_ref.target_id != last_transition_id:
            targets.append(transition_ref)
            last_transition_id = transition_ref.target_id
        if match.semantic.target_ref != transition_ref:
            targets.append(match.semantic.target_ref)
    return _deduplicate_consecutive(targets)


def _trace_link(
    occurrence_id: str,
    path: RequirementPath,
    model: StateModel,
    match: _CandidateMatch,
) -> TraceLink:
    transition = match.candidate.transition
    return TraceLink(
        id=(
            f"{_METHOD_ID}:link:{path.id}:{match.element.id}:{model.id}:{transition.id}"
        ),
        requirement_id=path.requirement_id,
        requirement_element_id=match.element.id,
        state_model_id=model.id,
        target_ref=match.semantic.target_ref,
        score=match.semantic.score,
        occurrence_id=occurrence_id,
        rationale=(
            f"Weighted semantic alignment {match.semantic.score:.3f} against "
            f"the transition's {match.semantic.facet} facet, represented by "
            f"{match.semantic.target_ref.kind.value} "
            f"{match.semantic.target_ref.target_id}."
        ),
        metadata={
            "method": _METHOD_ID,
            "scorer": _SCORER_ID,
            "facet": match.semantic.facet,
            "matched_tokens": match.semantic.matched_tokens,
            "path_position": match.element_index,
            "route_transition_id": transition.id,
        },
    )


def _alignment_key(alignment: _Alignment) -> tuple[int, float, int]:
    return (
        len(alignment.matches),
        round(alignment.score_sum, 12),
        -alignment.gap_count,
    )


def _deduplicate_consecutive(
    values: list[TraceTargetRef],
) -> tuple[TraceTargetRef, ...]:
    result: list[TraceTargetRef] = []
    for value in values:
        if not result or result[-1] != value:
            result.append(value)
    return tuple(result)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
