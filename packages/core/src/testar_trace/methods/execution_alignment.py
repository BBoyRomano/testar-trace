"""Recorded-execution alignment for requirement completeness."""

from collections.abc import Iterable
from dataclasses import dataclass, field

from testar_trace.domain._validation import require_unit_interval
from testar_trace.domain.requirement_paths import (
    RequirementPath,
    materialize_requirement_paths,
)
from testar_trace.domain.requirements import RequirementElement, RequirementSet
from testar_trace.domain.state_models import (
    ExecutionSequence,
    ExecutionStep,
    StateModel,
    StateModelCollection,
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
    SemanticFacet,
    SemanticScore,
    TransitionSemanticCandidate,
    inverse_document_frequencies,
    score_element,
    transition_candidates,
)

__all__ = [
    "ExecutionAlignmentConfig",
    "ExecutionAlignmentMethod",
    "trace_with_execution_alignment",
]


_METHOD_ID = "execution-alignment"
_SCORER_ID = "weighted-token-f2-v1"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionAlignmentConfig:
    """Configuration for deterministic recorded-execution alignment."""

    similarity_threshold: float = 0.30
    maximum_candidates_per_element: int = 12

    def __post_init__(self) -> None:
        require_unit_interval(self.similarity_threshold, "similarity_threshold")
        if isinstance(self.maximum_candidates_per_element, bool) or not isinstance(
            self.maximum_candidates_per_element, int
        ):
            raise TypeError("maximum_candidates_per_element must be an integer")
        if self.maximum_candidates_per_element < 1:
            raise ValueError("maximum_candidates_per_element must be at least 1")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionAlignmentMethod:
    """Configured recorded-execution alignment method."""

    config: ExecutionAlignmentConfig = field(default_factory=ExecutionAlignmentConfig)

    def __post_init__(self) -> None:
        if not isinstance(self.config, ExecutionAlignmentConfig):
            raise TypeError("config must be an ExecutionAlignmentConfig")

    def __call__(
        self,
        requirements: RequirementSet,
        state_models: StateModelCollection,
        context: TraceContext,
    ) -> TraceabilityResult:
        return trace_with_execution_alignment(
            requirements,
            state_models,
            context,
            config=self.config,
        )


@dataclass(frozen=True, slots=True)
class _StepCandidate:
    step: ExecutionStep
    target_ref: TraceTargetRef
    facets: tuple[SemanticFacet, ...]


@dataclass(frozen=True, slots=True)
class _StepMatch:
    element_index: int
    element: RequirementElement
    candidate: _StepCandidate
    semantic: SemanticScore


@dataclass(frozen=True, slots=True)
class _ExecutionAlignment:
    sequence: ExecutionSequence
    matches: tuple[_StepMatch, ...]
    score_sum: float


def trace_with_execution_alignment(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    context: TraceContext,
    *,
    config: ExecutionAlignmentConfig | None = None,
) -> TraceabilityResult:
    """Align every materialized requirement path to recorded execution steps."""
    effective_config = ExecutionAlignmentConfig() if config is None else config
    if not isinstance(effective_config, ExecutionAlignmentConfig):
        raise TypeError("config must be an ExecutionAlignmentConfig")

    context.raise_if_cancelled()
    materialization = materialize_requirement_paths(requirements)
    total = len(materialization.paths) * len(state_models.models)
    context.report(
        "execution-alignment.started",
        message="Recorded-execution alignment started",
        total=total,
        metadata={
            "total_requirements": len(requirements.requirements),
            "total_paths": len(materialization.paths),
        },
    )
    elements = {element.id: element for element in requirements.elements}
    findings: list[PathFinding] = []
    occurrences: list[TraceOccurrence] = []
    links: list[TraceLink] = []
    completed = 0

    for model in state_models.models:
        semantic_transitions = transition_candidates(model)
        idf = inverse_document_frequencies(semantic_transitions)
        sequence_candidates = {
            sequence.id: _sequence_candidates(model, sequence, semantic_transitions)
            for sequence in model.sequences
        }
        for path in materialization.paths:
            context.raise_if_cancelled()
            if not model.sequences:
                findings.append(
                    PathFinding(
                        path_id=path.id,
                        state_model_id=model.id,
                        assessable=False,
                        rationale="The state model contains no recorded execution sequences.",
                    )
                )
            else:
                occurrence, occurrence_links = _align_path(
                    path,
                    model,
                    elements,
                    sequence_candidates,
                    idf,
                    effective_config,
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
                "execution-alignment.path",
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
        evidence_label="recorded execution sequences",
        requirements=requirements,
        state_models=state_models,
        materialization=materialization,
        findings=findings,
    )
    result = TraceabilityResult(
        id=_METHOD_ID,
        title="Recorded-execution alignment result",
        path_materialization=materialization,
        assessments=assessments,
        links=tuple(links),
        occurrences=tuple(occurrences),
        requirement_source_refs=requirement_source_refs(requirements),
        state_model_source_refs=state_models.source_refs,
        metadata={
            "method": _METHOD_ID,
            "analysis": "observed-path-completeness",
            "evidence_basis": TraceEvidenceBasis.EXECUTION_SEQUENCE.value,
            "scorer": _SCORER_ID,
            "similarity_threshold": effective_config.similarity_threshold,
            "maximum_candidates_per_element": (
                effective_config.maximum_candidates_per_element
            ),
            "path_materialization_exhaustive": materialization.is_exhaustive,
            "state_model_collection_id": state_models.id,
        },
    )
    context.report(
        "execution-alignment.completed",
        message="Recorded-execution alignment completed",
        completed=total,
        total=total,
    )
    return result


def _sequence_candidates(
    model: StateModel,
    sequence: ExecutionSequence,
    semantic_transitions: tuple[TransitionSemanticCandidate, ...],
) -> tuple[_StepCandidate, ...]:
    transition_facets = {
        candidate.transition.id: candidate.facets for candidate in semantic_transitions
    }
    transitions = {transition.id: transition for transition in model.transitions}
    candidates: list[_StepCandidate] = []
    for step in sequence.steps:
        facets: list[SemanticFacet] = []
        if step.transition_id is not None:
            facets.extend(transition_facets.get(step.transition_id, ()))
            target_ref = TraceTargetRef(
                kind=TraceTargetKind.TRANSITION,
                target_id=step.transition_id,
            )
        elif step.action_id is not None:
            for transition in transitions.values():
                if transition.action_id == step.action_id:
                    facets.extend(transition_facets.get(transition.id, ()))
            target_ref = TraceTargetRef(
                kind=TraceTargetKind.ACTION,
                target_id=step.action_id,
            )
        elif step.state_id is not None:
            for transition in transitions.values():
                if step.state_id in (
                    transition.source_state_id,
                    transition.target_state_id,
                ):
                    facets.extend(transition_facets.get(transition.id, ()))
            target_ref = TraceTargetRef(
                kind=TraceTargetKind.STATE,
                target_id=step.state_id,
            )
        else:
            target_ref = TraceTargetRef(
                kind=TraceTargetKind.EXECUTION_STEP,
                target_id=step.id,
            )
        candidates.append(
            _StepCandidate(
                step=step,
                target_ref=target_ref,
                facets=_unique_facets(facets),
            )
        )
    return tuple(candidates)


def _align_path(
    path: RequirementPath,
    model: StateModel,
    elements: dict[str, RequirementElement],
    candidates_by_sequence: dict[str, tuple[_StepCandidate, ...]],
    idf: dict[str, float],
    config: ExecutionAlignmentConfig,
) -> tuple[TraceOccurrence, tuple[TraceLink, ...]]:
    path_elements = tuple(elements[element_id] for element_id in path.element_ids)
    alignments = tuple(
        _align_sequence(
            sequence,
            path_elements,
            candidates_by_sequence[sequence.id],
            idf,
            config,
        )
        for sequence in model.sequences
    )
    alignment = max(alignments, key=_alignment_key)
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
    links = tuple(
        _trace_link(occurrence_id, path, model, alignment.sequence, match)
        for match in alignment.matches
    )
    target_path = tuple(match.candidate.target_ref for match in alignment.matches)
    if not target_path:
        target_path = (
            TraceTargetRef(
                kind=TraceTargetKind.EXECUTION_SEQUENCE,
                target_id=alignment.sequence.id,
            ),
        )
    coverage_ratio = (
        len(covered_positions) / len(path_elements) if path_elements else 0.0
    )
    mean_similarity = (
        alignment.score_sum / len(alignment.matches) if alignment.matches else 0.0
    )
    full = len(covered_positions) == len(path_elements) and bool(path_elements)
    rationale = (
        f"All {len(path_elements)} requirement elements align in order to recorded "
        f"execution {alignment.sequence.id}."
        if full
        else (
            f"{len(covered_positions)} of {len(path_elements)} requirement elements "
            f"align in order to recorded execution {alignment.sequence.id}."
        )
    )
    occurrence = TraceOccurrence(
        id=occurrence_id,
        requirement_id=path.requirement_id,
        flow_id=path.flow_id,
        path_id=path.id,
        state_model_id=model.id,
        evidence_basis=TraceEvidenceBasis.EXECUTION_SEQUENCE,
        execution_sequence_id=alignment.sequence.id,
        status=TraceOccurrenceStatus.FULL if full else TraceOccurrenceStatus.PARTIAL,
        target_path=target_path,
        covered_element_ids=covered_ids,
        missing_element_ids=missing_ids,
        link_ids=tuple(link.id for link in links),
        score=coverage_ratio * mean_similarity,
        rationale=rationale,
        metadata={
            "method": _METHOD_ID,
            "matched_position_count": len(covered_positions),
            "total_position_count": len(path_elements),
            "mean_similarity": mean_similarity,
        },
    )
    return occurrence, links


def _align_sequence(
    sequence: ExecutionSequence,
    elements: tuple[RequirementElement, ...],
    candidates: tuple[_StepCandidate, ...],
    idf: dict[str, float],
    config: ExecutionAlignmentConfig,
) -> _ExecutionAlignment:
    ranked_by_element: list[tuple[_StepMatch, ...]] = []
    for element_index, element in enumerate(elements):
        ranked: list[_StepMatch] = []
        for candidate in candidates:
            semantic = score_element(element, candidate.facets, idf)
            if semantic is None or semantic.score < config.similarity_threshold:
                continue
            ranked.append(
                _StepMatch(
                    element_index=element_index,
                    element=element,
                    candidate=candidate,
                    semantic=semantic,
                )
            )
        ranked.sort(
            key=lambda item: (-item.semantic.score, item.candidate.step.order_index)
        )
        ranked_by_element.append(tuple(ranked[: config.maximum_candidates_per_element]))

    all_alignments: list[_ExecutionAlignment] = []
    for element_matches in ranked_by_element:
        current: list[_ExecutionAlignment] = []
        for match in element_matches:
            best = _ExecutionAlignment(
                sequence=sequence,
                matches=(match,),
                score_sum=match.semantic.score,
            )
            for previous in all_alignments:
                if (
                    previous.matches[-1].candidate.step.order_index
                    > match.candidate.step.order_index
                ):
                    continue
                proposed = _ExecutionAlignment(
                    sequence=sequence,
                    matches=(*previous.matches, match),
                    score_sum=previous.score_sum + match.semantic.score,
                )
                if _alignment_key(proposed) > _alignment_key(best):
                    best = proposed
            current.append(best)
        all_alignments.extend(current)
    return max(
        all_alignments,
        key=_alignment_key,
        default=_ExecutionAlignment(sequence=sequence, matches=(), score_sum=0.0),
    )


def _trace_link(
    occurrence_id: str,
    path: RequirementPath,
    model: StateModel,
    sequence: ExecutionSequence,
    match: _StepMatch,
) -> TraceLink:
    return TraceLink(
        id=(
            f"{_METHOD_ID}:link:{path.id}:{match.element.id}:"
            f"{model.id}:{sequence.id}:{match.candidate.step.id}"
        ),
        requirement_id=path.requirement_id,
        requirement_element_id=match.element.id,
        state_model_id=model.id,
        target_ref=match.candidate.target_ref,
        score=match.semantic.score,
        occurrence_id=occurrence_id,
        rationale=(
            f"Weighted semantic alignment {match.semantic.score:.3f} against "
            f"recorded execution step {match.candidate.step.order_index}."
        ),
        metadata={
            "method": _METHOD_ID,
            "scorer": _SCORER_ID,
            "execution_sequence_id": sequence.id,
            "execution_step_id": match.candidate.step.id,
            "facet": match.semantic.facet,
            "matched_tokens": match.semantic.matched_tokens,
            "path_position": match.element_index,
        },
    )


def _alignment_key(alignment: _ExecutionAlignment) -> tuple[int, float, int]:
    last_order = (
        alignment.matches[-1].candidate.step.order_index if alignment.matches else -1
    )
    return (len(alignment.matches), round(alignment.score_sum, 12), -last_order)


def _unique_facets(values: Iterable[SemanticFacet]) -> tuple[SemanticFacet, ...]:
    return tuple(dict.fromkeys(values))


def _unique[T](values: Iterable[T]) -> tuple[T, ...]:
    return tuple(dict.fromkeys(values))
