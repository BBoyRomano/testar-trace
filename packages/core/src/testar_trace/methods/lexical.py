"""Deterministic lexical traceability baseline."""

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from math import sqrt

from testar_trace.domain._validation import require_unit_interval
from testar_trace.domain.provenance import SourceRef
from testar_trace.domain.requirement_paths import materialize_requirement_paths
from testar_trace.domain.requirements import (
    RequirementElement,
    RequirementPath,
    RequirementSet,
)
from testar_trace.domain.state_models import (
    Action,
    State,
    StateModel,
    StateModelCollection,
    Widget,
)
from testar_trace.domain.traceability import (
    AssessabilityStatus,
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageAssessment,
    CoverageStatus,
    TraceabilityResult,
    TraceLink,
    TraceTargetKind,
    TraceTargetRef,
)
from testar_trace.execution import TraceContext

__all__ = [
    "LexicalConfig",
    "LexicalMethod",
    "trace_with_lexical",
]

_METHOD_ID = "lexical"
_SCORER_ID = "token-frequency-cosine-v1"
_TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)
_TARGET_KIND_ORDER = {
    TraceTargetKind.TRANSITION: 0,
    TraceTargetKind.ACTION: 1,
    TraceTargetKind.WIDGET: 2,
    TraceTargetKind.STATE: 3,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class LexicalConfig:
    """Configuration for deterministic lexical candidate matching."""

    retention_threshold: float = 0.0

    def __post_init__(self) -> None:
        require_unit_interval(self.retention_threshold, "retention_threshold")


@dataclass(frozen=True, slots=True, kw_only=True)
class LexicalMethod:
    """Configured callable lexical trace method."""

    config: LexicalConfig = field(default_factory=LexicalConfig)

    def __post_init__(self) -> None:
        if not isinstance(self.config, LexicalConfig):
            raise TypeError("config must be a LexicalConfig")

    def __call__(
        self,
        requirements: RequirementSet,
        state_models: StateModelCollection,
        context: TraceContext,
    ) -> TraceabilityResult:
        """Run lexical tracing with the configured options."""
        return trace_with_lexical(
            requirements,
            state_models,
            context,
            config=self.config,
        )


@dataclass(frozen=True, slots=True)
class _LexicalCandidate:
    state_model_id: str
    primary_kind: TraceTargetKind
    primary_id: str
    target_ref: TraceTargetRef
    tokens: Counter[str]


def trace_with_lexical(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    context: TraceContext,
    *,
    config: LexicalConfig | None = None,
) -> TraceabilityResult:
    """Match requirement elements to canonical state-model text."""
    effective_config = LexicalConfig() if config is None else config
    if not isinstance(effective_config, LexicalConfig):
        raise TypeError("config must be a LexicalConfig")

    context.raise_if_cancelled()
    path_materialization = materialize_requirement_paths(requirements)
    progress_metadata = {
        "total_requirements": len(requirements.requirements),
        "total_paths": len(path_materialization.paths),
    }
    context.report(
        "lexical.started",
        message="Lexical trace method started",
        total=len(requirements.elements),
        metadata=progress_metadata,
    )
    candidates_by_model = {
        model.id: _state_model_candidates(model) for model in state_models.models
    }
    links: list[TraceLink] = []
    matched_element_ids_by_model = {model.id: set() for model in state_models.models}

    for completed, element in enumerate(requirements.elements, start=1):
        context.raise_if_cancelled()
        requirement_tokens = _token_counts(element.text)

        for model in state_models.models:
            ranked = _rank_candidates(
                requirement_tokens,
                candidates_by_model[model.id],
                effective_config,
            )
            if ranked:
                matched_element_ids_by_model[model.id].add(element.id)
            links.extend(
                _links_for_ranked_candidates(
                    element,
                    ranked,
                )
            )

        context.report(
            "lexical.matching",
            message=f"Matched requirement element {element.id}",
            completed=completed,
            total=len(requirements.elements),
            metadata={**progress_metadata, "requirement_id": element.requirement_id},
        )

    context.report(
        "lexical.assessing",
        message="Building coverage assessments",
        metadata=progress_metadata,
    )
    assessments = _build_assessments(
        requirements,
        state_models,
        path_materialization.paths,
        candidates_by_model,
        matched_element_ids_by_model,
    )
    result = TraceabilityResult(
        id=_METHOD_ID,
        title="Lexical traceability result",
        path_materialization=path_materialization,
        assessments=assessments,
        links=tuple(links),
        requirement_source_refs=_requirement_source_refs(requirements),
        state_model_source_refs=state_models.source_refs,
        metadata={
            "method": _METHOD_ID,
            "scorer": _SCORER_ID,
            "retention_threshold": effective_config.retention_threshold,
            "matching_scope": "requirement-elements",
            "ordered_route_matching": False,
            "state_model_collection_id": state_models.id,
        },
    )

    context.raise_if_cancelled()
    context.report(
        "lexical.completed",
        message="Lexical trace method completed",
        completed=len(requirements.elements),
        total=len(requirements.elements),
        metadata=progress_metadata,
    )
    return result


def _state_model_candidates(model: StateModel) -> tuple[_LexicalCandidate, ...]:
    states_by_id = {state.id: state for state in model.states}
    widgets_by_id = {widget.id: widget for widget in model.widgets}
    actions_by_id = {action.id: action for action in model.actions}
    candidates: list[_LexicalCandidate] = []

    for state in model.states:
        _append_candidate(
            candidates,
            model.id,
            TraceTargetKind.STATE,
            state.id,
            TraceTargetRef(kind=TraceTargetKind.STATE, target_id=state.id),
            _state_text(state),
        )

    for widget in model.widgets:
        _append_candidate(
            candidates,
            model.id,
            TraceTargetKind.WIDGET,
            widget.id,
            TraceTargetRef(kind=TraceTargetKind.WIDGET, target_id=widget.id),
            _widget_text(widget),
        )

    for action in model.actions:
        widget = (
            widgets_by_id.get(action.target_widget_id)
            if action.target_widget_id is not None
            else None
        )
        _append_candidate(
            candidates,
            model.id,
            TraceTargetKind.ACTION,
            action.id,
            TraceTargetRef(kind=TraceTargetKind.ACTION, target_id=action.id),
            _join_text(_action_text(action), _widget_text(widget)),
        )

    for transition in model.transitions:
        action = actions_by_id[transition.action_id]
        widget = (
            widgets_by_id.get(action.target_widget_id)
            if action.target_widget_id is not None
            else None
        )
        source_state = states_by_id[transition.source_state_id]
        target_state = (
            states_by_id.get(transition.target_state_id)
            if transition.target_state_id is not None
            else None
        )
        _append_candidate(
            candidates,
            model.id,
            TraceTargetKind.TRANSITION,
            transition.id,
            TraceTargetRef(
                kind=TraceTargetKind.TRANSITION,
                target_id=transition.id,
            ),
            _join_text(
                _action_text(action),
                _widget_text(widget),
                _state_text(source_state),
                _state_text(target_state),
            ),
        )

    return tuple(candidates)


def _append_candidate(
    candidates: list[_LexicalCandidate],
    state_model_id: str,
    primary_kind: TraceTargetKind,
    primary_id: str,
    target_ref: TraceTargetRef,
    text: str,
) -> None:
    tokens = _token_counts(text)
    if not tokens:
        return
    candidates.append(
        _LexicalCandidate(
            state_model_id=state_model_id,
            primary_kind=primary_kind,
            primary_id=primary_id,
            target_ref=target_ref,
            tokens=tokens,
        )
    )


def _rank_candidates(
    requirement_tokens: Counter[str],
    candidates: tuple[_LexicalCandidate, ...],
    config: LexicalConfig,
) -> tuple[tuple[_LexicalCandidate, float, tuple[str, ...]], ...]:
    if not requirement_tokens:
        return ()

    ranked: list[tuple[_LexicalCandidate, float, tuple[str, ...]]] = []
    for candidate in candidates:
        score = _cosine_similarity(requirement_tokens, candidate.tokens)
        if score <= 0.0 or score < config.retention_threshold:
            continue
        matched_tokens = tuple(
            sorted(requirement_tokens.keys() & candidate.tokens.keys())
        )
        ranked.append((candidate, score, matched_tokens))

    ranked.sort(
        key=lambda item: (
            -item[1],
            _TARGET_KIND_ORDER[item[0].primary_kind],
            item[0].primary_id,
        )
    )
    return tuple(ranked)


def _links_for_ranked_candidates(
    element: RequirementElement,
    ranked: tuple[tuple[_LexicalCandidate, float, tuple[str, ...]], ...],
) -> tuple[TraceLink, ...]:
    links: list[TraceLink] = []
    for rank, (candidate, score, matched_tokens) in enumerate(ranked, start=1):
        matched_text = ", ".join(matched_tokens)
        links.append(
            TraceLink(
                id=(
                    f"{_METHOD_ID}:link:{element.id}:{candidate.state_model_id}:"
                    f"{candidate.primary_kind.value}:{candidate.primary_id}"
                ),
                requirement_id=element.requirement_id,
                requirement_element_id=element.id,
                state_model_id=candidate.state_model_id,
                target_ref=candidate.target_ref,
                score=score,
                rationale=(
                    f"Token cosine similarity {score:.3f}; "
                    f"matched tokens: {matched_text}."
                ),
                metadata={
                    "scorer": _SCORER_ID,
                    "rank": rank,
                    "matched_tokens": matched_tokens,
                    "primary_target_kind": candidate.primary_kind.value,
                    "primary_target_id": candidate.primary_id,
                },
            )
        )
    return tuple(links)


def _build_assessments(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    paths: tuple[RequirementPath, ...],
    candidates_by_model: dict[str, tuple[_LexicalCandidate, ...]],
    matched_element_ids_by_model: dict[str, set[str]],
) -> tuple[CoverageAssessment, ...]:
    scopes: list[
        tuple[AssessmentScopeKind, str, str, tuple[str, ...], tuple[str, ...]]
    ] = []
    requirement_ids = tuple(requirement.id for requirement in requirements.requirements)
    all_element_ids = tuple(element.id for element in requirements.elements)
    scopes.append(
        (
            AssessmentScopeKind.REQUIREMENT_SET,
            "requirements",
            "requirement-set",
            requirement_ids,
            all_element_ids,
        )
    )

    for requirement in requirements.requirements:
        requirement_element_ids = tuple(
            element.id for element in requirements.elements_for(requirement.id)
        )
        scopes.append(
            (
                AssessmentScopeKind.REQUIREMENT,
                requirement.id,
                requirement.id,
                (requirement.id,),
                requirement_element_ids,
            )
        )
        for flow in requirements.flows_for(requirement.id):
            flow_element_ids = _unique(node.element_id for node in flow.nodes)
            scopes.append(
                (
                    AssessmentScopeKind.FLOW,
                    flow.id,
                    flow.id,
                    (requirement.id,),
                    flow_element_ids,
                )
            )
            for branch in flow.branches:
                branch_element_ids = _unique(
                    node.element_id
                    for node in flow.nodes
                    if node.branch_id == branch.id
                )
                scopes.append(
                    (
                        AssessmentScopeKind.BRANCH,
                        branch.id,
                        f"{flow.id}:{branch.id}",
                        (requirement.id,),
                        branch_element_ids,
                    )
                )

    for path in paths:
        scopes.append(
            (
                AssessmentScopeKind.PATH,
                path.id,
                path.id,
                (path.requirement_id,),
                _unique(path.element_ids),
            )
        )

    all_model_ids = tuple(model.id for model in state_models.models)
    collection_matches: set[str] = set()
    for matched_element_ids in matched_element_ids_by_model.values():
        collection_matches.update(matched_element_ids)
    assessments: list[CoverageAssessment] = []

    for (
        scope_kind,
        scope_id,
        assessment_key,
        scope_requirement_ids,
        element_ids,
    ) in scopes:
        assessments.append(
            _assessment(
                assessment_id=(
                    f"{_METHOD_ID}:assessment:{scope_kind.value}:"
                    f"{assessment_key}:collection:{state_models.id}"
                ),
                scope_kind=scope_kind,
                scope_id=scope_id,
                requirement_ids=scope_requirement_ids,
                view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
                state_models=state_models,
                state_model_ids=all_model_ids,
                element_ids=element_ids,
                matched_element_ids=collection_matches,
                has_candidates=any(candidates_by_model.values()),
            )
        )
        for model in state_models.models:
            assessments.append(
                _assessment(
                    assessment_id=(
                        f"{_METHOD_ID}:assessment:{scope_kind.value}:"
                        f"{assessment_key}:model:{model.id}"
                    ),
                    scope_kind=scope_kind,
                    scope_id=scope_id,
                    requirement_ids=scope_requirement_ids,
                    view_kind=AssessmentViewKind.STATE_MODEL,
                    state_models=state_models,
                    state_model_ids=(model.id,),
                    element_ids=element_ids,
                    matched_element_ids=matched_element_ids_by_model[model.id],
                    has_candidates=bool(candidates_by_model[model.id]),
                )
            )

    return tuple(assessments)


def _assessment(
    *,
    assessment_id: str,
    scope_kind: AssessmentScopeKind,
    scope_id: str,
    requirement_ids: tuple[str, ...],
    view_kind: AssessmentViewKind,
    state_models: StateModelCollection,
    state_model_ids: tuple[str, ...],
    element_ids: tuple[str, ...],
    matched_element_ids: set[str],
    has_candidates: bool,
) -> CoverageAssessment:
    if not element_ids:
        return CoverageAssessment(
            id=assessment_id,
            scope_kind=scope_kind,
            scope_id=scope_id,
            requirement_ids=requirement_ids,
            view_kind=view_kind,
            state_model_collection_id=state_models.id,
            state_model_ids=state_model_ids,
            status=CoverageStatus.NOT_COVERED,
            assessability=AssessabilityStatus.NONE,
            completeness=CompletenessStatus.NOT_ASSESSABLE,
            rationale="The scope contains no traceable requirement elements.",
        )
    if not has_candidates:
        return CoverageAssessment(
            id=assessment_id,
            scope_kind=scope_kind,
            scope_id=scope_id,
            requirement_ids=requirement_ids,
            view_kind=view_kind,
            state_model_collection_id=state_models.id,
            state_model_ids=state_model_ids,
            status=CoverageStatus.NOT_COVERED,
            assessability=AssessabilityStatus.NONE,
            completeness=CompletenessStatus.NOT_ASSESSABLE,
            rationale="The state-model view contains no canonical text candidates.",
        )

    covered = tuple(
        element_id for element_id in element_ids if element_id in matched_element_ids
    )
    missing = tuple(
        element_id
        for element_id in element_ids
        if element_id not in matched_element_ids
    )
    coverage_ratio = len(covered) / len(element_ids)
    status = (
        CoverageStatus.COVERED
        if coverage_ratio == 1.0
        else CoverageStatus.PARTIALLY_COVERED
        if coverage_ratio > 0.0
        else CoverageStatus.NOT_COVERED
    )
    return CoverageAssessment(
        id=assessment_id,
        scope_kind=scope_kind,
        scope_id=scope_id,
        requirement_ids=requirement_ids,
        view_kind=view_kind,
        state_model_collection_id=state_models.id,
        state_model_ids=state_model_ids,
        status=status,
        assessability=AssessabilityStatus.FULL,
        completeness=CompletenessStatus.NOT_ASSESSABLE,
        covered_element_ids=covered,
        missing_element_ids=missing,
        coverage_ratio=coverage_ratio,
        rationale=(
            f"Lexical candidates were retained for {len(covered)} of "
            f"{len(element_ids)} requirement elements. Ordered path "
            "completeness is not established by this method."
        ),
    )


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot_product = sum(count * right[token] for token, count in left.items())
    left_norm = sqrt(sum(count * count for count in left.values()))
    right_norm = sqrt(sum(count * count for count in right.values()))
    score = min(1.0, max(0.0, dot_product / (left_norm * right_norm)))
    return 1.0 if score >= 1.0 - 1e-12 else score


def _token_counts(text: str) -> Counter[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return Counter(_TOKEN_PATTERN.findall(normalized))


def _state_text(state: State | None) -> str:
    if state is None:
        return ""
    return _join_text(state.name, state.title, state.url)


def _widget_text(widget: Widget | None) -> str:
    if widget is None:
        return ""
    return _join_text(
        widget.text,
        widget.title,
        widget.role,
        widget.tag_name,
        widget.href,
    )


def _action_text(action: Action) -> str:
    return _join_text(action.description, action.value)


def _join_text(*values: str | None) -> str:
    return " ".join(value.strip() for value in values if value and value.strip())


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _requirement_source_refs(
    requirements: RequirementSet,
) -> tuple[SourceRef, ...]:
    refs: list[SourceRef] = []
    for document in requirements.documents:
        if document.source_ref is not None and document.source_ref not in refs:
            refs.append(document.source_ref)
    for requirement in requirements.requirements:
        if requirement.source_ref is not None and requirement.source_ref not in refs:
            refs.append(requirement.source_ref)
    return tuple(refs)
