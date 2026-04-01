from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable
from uuid import uuid4

from reqtrace.application.methods.candidate_match import (
    _WEAK_TOKENS,
    _build_candidates,
    _classify_intent,
    _expanded_tokens,
    _normalize_text,
    _tokens,
)
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.results import (
    EvidenceSnapshot,
    RequirementResultStatus,
    RequirementSnapshot,
    RequirementTraceabilityResult,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
    TraceabilitySummary,
)
from reqtrace.domain.evidence.models import Action, ApplicationState, Transition, UIElement
from reqtrace.domain.traceability.enums import (
    ConfidenceLabel,
    CoverageStatus,
    CoverageSubjectType,
    EvidenceTargetType,
    LinkType,
    TraceEvidenceKind,
)
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink


@dataclass(slots=True)
class _ScoredCandidate:
    candidate: object
    local_score: float
    selected_score: float
    matched_tokens: list[str]
    intent: str


@dataclass(slots=True)
class _Anchor:
    candidate: _ScoredCandidate
    sequence_key: int
    state_id: str | None
    transition_ids: tuple[str, ...]
    action_ids: tuple[str, ...]
    element_ids: tuple[str, ...]


@dataclass(slots=True)
class _PathAlignment:
    score: float
    anchors: dict[str, _Anchor]
    transition_ids: list[str]
    state_ids: list[str]


class FlowMatchMethod(TraceabilityMethod):
    """Path-aware flow matching over states, actions, elements, and transitions.

    Strategy:
    1. score local candidates for every requirement fragment
    2. convert each local candidate into one or more graph anchors
    3. align main-flow fragments on an ordered execution backbone that allows gaps
    4. evaluate alternative-flow fragments separately but with the same graph model
    5. report concrete states/transitions as supporting execution traces

    This stays within the current repository constraints:
    - observations are not required
    - branch semantics are inferred from fragment buckets, not full formal flow logic
    - intermediate evidence steps are allowed because alignment is order-preserving,
      not adjacency-preserving
    """

    name = "flow_match"
    method_name = "flow_match"

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        started_at = datetime.now(UTC)
        analysis_run_id = f"trace-run-{uuid4().hex}"

        requirements = list(
            _iter_selected_requirements(
                request.requirements,
                request.selected_requirement_ids,
            )
        )
        candidates = _build_candidates(request.evidence, request.selected_evidence_run_ids)
        graph = _EvidenceGraph.from_snapshot(request.evidence, request.selected_evidence_run_ids)

        requirement_results: list[RequirementTraceabilityResult] = []

        for requirement in requirements:
            fragments = list(request.requirements.fragments_for(requirement.id))
            preconditions, main_flow, alt_flow, postconditions = _partition_fragments(fragments)

            ranked_by_fragment = {
                fragment.id: _rank_candidates(fragment.text, candidates)
                for fragment in fragments
            }

            main_alignment = _align_fragment_sequence(main_flow, ranked_by_fragment, graph)
            alt_alignment = _align_fragment_sequence(alt_flow, ranked_by_fragment, graph)

            selected_by_fragment_id: dict[str, _Anchor] = {}
            selected_by_fragment_id.update(main_alignment.anchors)
            for fragment_id, anchor in alt_alignment.anchors.items():
                selected_by_fragment_id.setdefault(fragment_id, anchor)

            for bucket in (preconditions, postconditions):
                for fragment in bucket:
                    anchor = _best_anchor_for_fragment(fragment, ranked_by_fragment, graph)
                    if anchor is not None:
                        selected_by_fragment_id.setdefault(fragment.id, anchor)

            fragment_coverages: list[CoverageAssessment] = []
            trace_links: list[TraceLink] = []
            trace_evidence: list[TraceEvidence] = []
            warnings: list[str] = []
            selected_scores: list[float] = []

            for fragment in fragments:
                anchor = selected_by_fragment_id.get(fragment.id)
                if anchor is None or anchor.candidate.selected_score < 0.30:
                    fragment_coverages.append(
                        CoverageAssessment(
                            id=f"coverage-{uuid4().hex}",
                            analysis_run_id=analysis_run_id,
                            subject_type=CoverageSubjectType.REQUIREMENT_FRAGMENT,
                            subject_id=fragment.id,
                            coverage_status=CoverageStatus.UNCOVERED,
                            coverage_ratio=0.0,
                            confidence_ratio=None,
                            covered_fragment_count=None,
                            total_fragment_count=None,
                            supporting_run_count=0,
                            metadata={
                                "method": self.method_name,
                                "best_target_type": None,
                            },
                        )
                    )
                    warnings.append(f"No aligned execution support for fragment {fragment.id}")
                    continue

                selected_scores.append(anchor.candidate.selected_score)
                coverage_status, link_type, confidence_label = _coverage_for_score(
                    anchor.candidate.selected_score
                )
                if coverage_status == CoverageStatus.UNCERTAIN:
                    warnings.append(f"Uncertain aligned support for fragment {fragment.id}")

                link = TraceLink(
                    id=f"link-{uuid4().hex}",
                    analysis_run_id=analysis_run_id,
                    requirement_fragment_id=fragment.id,
                    evidence_target_type=EvidenceTargetType(anchor.candidate.candidate.target_type),
                    evidence_target_id=anchor.candidate.candidate.target_id,
                    link_type=link_type,
                    score=float(anchor.candidate.selected_score),
                    confidence_label=confidence_label,
                    metadata={
                        "method": self.method_name,
                        "intent": anchor.candidate.intent,
                        "sequence_key": anchor.sequence_key,
                        "anchor_transition_count": len(anchor.transition_ids),
                    },
                )
                trace_links.append(link)

                primary_transition_id = anchor.transition_ids[0] if anchor.transition_ids else None
                primary_element_id = anchor.element_ids[0] if anchor.element_ids else getattr(
                    anchor.candidate.candidate, "element_id", None
                )

                trace_evidence.append(
                    TraceEvidence(
                        id=f"evidence-{uuid4().hex}",
                        trace_link_id=link.id,
                        evidence_kind=TraceEvidenceKind.TEXT_MATCH,
                        text_excerpt=anchor.candidate.candidate.text[:240],
                        matched_tokens=anchor.candidate.matched_tokens,
                        run_id=graph.primary_run_id,
                        state_id=anchor.state_id,
                        transition_id=primary_transition_id,
                        element_id=primary_element_id,
                        details={
                            "method": self.method_name,
                            "candidate_type": anchor.candidate.candidate.target_type,
                            "widget_kind": getattr(anchor.candidate.candidate, "widget_kind", None),
                            "action_kind": getattr(anchor.candidate.candidate, "action_kind", None),
                            "transition_ids": list(anchor.transition_ids),
                            "state_ids": list(anchor.state_ids if hasattr(anchor, 'state_ids') else []),
                        },
                    )
                )

                fragment_coverages.append(
                    CoverageAssessment(
                        id=f"coverage-{uuid4().hex}",
                        analysis_run_id=analysis_run_id,
                        subject_type=CoverageSubjectType.REQUIREMENT_FRAGMENT,
                        subject_id=fragment.id,
                        coverage_status=coverage_status,
                        coverage_ratio=1.0 if coverage_status != CoverageStatus.UNCOVERED else 0.0,
                        confidence_ratio=float(anchor.candidate.selected_score),
                        covered_fragment_count=None,
                        total_fragment_count=None,
                        supporting_run_count=1 if graph.primary_run_id else 0,
                        metadata={
                            "method": self.method_name,
                            "best_target_type": anchor.candidate.candidate.target_type,
                            "sequence_key": anchor.sequence_key,
                        },
                    )
                )

            path_transition_ids = _merge_path_ids(main_alignment.transition_ids, alt_alignment.transition_ids)
            path_state_ids = _merge_path_ids(main_alignment.state_ids, alt_alignment.state_ids)

            if path_transition_ids or path_state_ids:
                trace_evidence.append(
                    TraceEvidence(
                        id=f"evidence-{uuid4().hex}",
                        trace_link_id=trace_links[0].id if trace_links else f"synthetic-link-{uuid4().hex}",
                        evidence_kind=TraceEvidenceKind.TRANSITION_PATH,
                        text_excerpt=_describe_path(path_state_ids, path_transition_ids),
                        matched_tokens=[],
                        run_id=graph.primary_run_id,
                        state_id=path_state_ids[0] if path_state_ids else None,
                        transition_id=path_transition_ids[0] if path_transition_ids else None,
                        element_id=None,
                        details={
                            "method": self.method_name,
                            "path_state_ids": path_state_ids,
                            "path_transition_ids": path_transition_ids,
                            "main_path_transition_ids": main_alignment.transition_ids,
                            "alt_path_transition_ids": alt_alignment.transition_ids,
                        },
                    )
                )

            artifact_coverage = _aggregate_requirement_coverage(
                analysis_run_id=analysis_run_id,
                requirement_id=requirement.id,
                main_flow_total=len(main_flow),
                main_flow_matched=sum(1 for fragment in main_flow if fragment.id in main_alignment.anchors),
                alt_flow_total=len(alt_flow),
                alt_flow_matched=sum(1 for fragment in alt_flow if fragment.id in alt_alignment.anchors),
                all_fragment_total=len(fragments),
                all_fragment_matched=sum(
                    1 for fragment in fragments if fragment.id in selected_by_fragment_id
                ),
                confidences=selected_scores,
                supporting_run_count=1 if graph.primary_run_id and selected_scores else 0,
            )

            requirement_results.append(
                RequirementTraceabilityResult(
                    requirement_id=requirement.id,
                    requirement_title=requirement.title,
                    status=RequirementResultStatus.DONE,
                    artifact_coverage=artifact_coverage,
                    fragment_coverages=fragment_coverages,
                    trace_links=trace_links,
                    trace_evidence=trace_evidence,
                    warnings=warnings,
                    error_message=None,
                    metadata={
                        "method": self.method_name,
                        "fragment_count": len(fragments),
                        "precondition_count": len(preconditions),
                        "main_flow_count": len(main_flow),
                        "alternate_flow_count": len(alt_flow),
                        "postcondition_count": len(postconditions),
                        "main_alignment_score": round(main_alignment.score, 4),
                        "alt_alignment_score": round(alt_alignment.score, 4),
                        "execution_classification": _classify_execution(
                            len(main_flow),
                            sum(1 for fragment in main_flow if fragment.id in main_alignment.anchors),
                            len(alt_flow),
                            sum(1 for fragment in alt_flow if fragment.id in alt_alignment.anchors),
                        ),
                        "path_state_ids": path_state_ids,
                        "path_transition_ids": path_transition_ids,
                    },
                )
            )

        ended_at = datetime.now(UTC)
        summary = _build_summary(requirement_results)
        run = TraceabilityRun(
            id=analysis_run_id,
            method_name=self.method_name,
            status="completed",
            started_at=started_at,
            ended_at=ended_at,
            total_requirement_count=len(requirements),
            processed_requirement_count=len(requirement_results),
            failed_requirement_count=0,
            metadata={
                "method": self.method_name,
                "evidence_run_count": len(graph.selected_run_ids) if graph.selected_run_ids else len(request.evidence.runs),
            },
        )
        return TraceabilityResult(
            run=run,
            requirement_results=requirement_results,
            summary=summary,
            warnings=[],
            metadata={"method": self.method_name},
        )


@dataclass(slots=True)
class _EvidenceGraph:
    states_by_id: dict[str, ApplicationState]
    actions_by_id: dict[str, Action]
    elements_by_id: dict[str, UIElement]
    transitions_by_id: dict[str, Transition]
    action_to_transition_ids: dict[str, list[str]]
    state_to_transition_ids: dict[str, list[str]]
    state_to_element_ids: dict[str, list[str]]
    transition_order: dict[str, int]
    selected_run_ids: set[str]
    primary_run_id: str | None

    @classmethod
    def from_snapshot(
        cls,
        snapshot: EvidenceSnapshot,
        selected_run_ids: Iterable[str] | None,
    ) -> _EvidenceGraph:
        chosen_run_ids = set(selected_run_ids or [])
        available_run_ids = {run.id for run in snapshot.runs}
        if not chosen_run_ids:
            chosen_run_ids = available_run_ids

        transitions = [
            transition
            for transition in snapshot.transitions
            if not transition.run_id or transition.run_id in chosen_run_ids
        ]
        transitions.sort(key=lambda item: (item.order_index is None, item.order_index or 0, item.id))

        action_to_transition_ids: dict[str, list[str]] = {}
        state_to_transition_ids: dict[str, list[str]] = {}
        transition_order: dict[str, int] = {}

        for position, transition in enumerate(transitions):
            transition_order[transition.id] = position
            action_to_transition_ids.setdefault(transition.action_id, []).append(transition.id)
            state_to_transition_ids.setdefault(transition.from_state_id, []).append(transition.id)
            if transition.to_state_id:
                state_to_transition_ids.setdefault(transition.to_state_id, []).append(transition.id)

        state_to_element_ids: dict[str, list[str]] = {}
        for element in snapshot.elements:
            state_to_element_ids.setdefault(element.state_id, []).append(element.id)

        primary_run_id = next(iter(chosen_run_ids), None) if chosen_run_ids else None
        return cls(
            states_by_id={state.id: state for state in snapshot.states},
            actions_by_id={action.id: action for action in snapshot.actions},
            elements_by_id={element.id: element for element in snapshot.elements},
            transitions_by_id={transition.id: transition for transition in transitions},
            action_to_transition_ids=action_to_transition_ids,
            state_to_transition_ids=state_to_transition_ids,
            state_to_element_ids=state_to_element_ids,
            transition_order=transition_order,
            selected_run_ids=chosen_run_ids,
            primary_run_id=primary_run_id,
        )


def _iter_selected_requirements(
    snapshot: RequirementSnapshot,
    selected_ids: Iterable[str] | None,
):
    if not selected_ids:
        yield from snapshot.iter_requirements()
        return
    selected = set(selected_ids)
    for requirement in snapshot.iter_requirements():
        if requirement.id in selected:
            yield requirement


def _partition_fragments(
    fragments: list[object],
) -> tuple[list[object], list[object], list[object], list[object]]:
    preconditions: list[object] = []
    main_flow: list[object] = []
    alternate_flow: list[object] = []
    postconditions: list[object] = []

    for fragment in fragments:
        kind_name = str(getattr(fragment, "kind", "")).lower()
        if "pre" in kind_name or "given" in kind_name:
            preconditions.append(fragment)
        elif "post" in kind_name or "then" in kind_name:
            postconditions.append(fragment)
        elif "alt" in kind_name or "alternative" in kind_name:
            alternate_flow.append(fragment)
        else:
            main_flow.append(fragment)

    preconditions.sort(key=lambda item: getattr(item, "order_index", 0) or 0)
    main_flow.sort(key=lambda item: getattr(item, "order_index", 0) or 0)
    alternate_flow.sort(key=lambda item: getattr(item, "order_index", 0) or 0)
    postconditions.sort(key=lambda item: getattr(item, "order_index", 0) or 0)
    return preconditions, main_flow, alternate_flow, postconditions


def _rank_candidates(fragment_text: str, candidates: list[object], limit: int = 7) -> list[_ScoredCandidate]:
    frag_tokens = _tokens(fragment_text)
    if not frag_tokens:
        return []

    frag_expanded = _expanded_tokens(frag_tokens)
    intent = _classify_intent(frag_tokens)
    phrase = _normalize_text(fragment_text)
    ranked: list[_ScoredCandidate] = []

    for candidate in candidates:
        token_overlap = frag_tokens & candidate.tokens
        expanded_overlap = frag_expanded & candidate.expanded_tokens

        informative_overlap = {t for t in expanded_overlap if t not in _WEAK_TOKENS}
        raw_informative = {t for t in token_overlap if t not in _WEAK_TOKENS}
        phrase_match = bool(phrase) and phrase in _normalize_text(candidate.text)

        if not informative_overlap and not raw_informative and not phrase_match:
            continue

        score = 0.0
        if informative_overlap:
            score += min(0.55, 0.18 * len(informative_overlap))
        if raw_informative:
            score += min(0.20, 0.10 * len(raw_informative))

        norm_candidate = _normalize_text(candidate.text)
        frag_terms = sorted(t for t in frag_expanded if t not in _WEAK_TOKENS)

        if phrase_match:
            score += 0.18
        else:
            for term in frag_terms:
                if term and term in norm_candidate:
                    score += 0.05

        if intent == "operation":
            if candidate.target_type == "action":
                score += 0.20
            if candidate.target_type == "transition":
                score += 0.12
            if getattr(candidate, "widget_kind", None) in {"button", "link"}:
                score += 0.12
        elif intent in {"display", "state"}:
            if candidate.target_type == "application_state":
                score += 0.18
            if candidate.target_type == "ui_element":
                score += 0.10
            if getattr(candidate, "widget_kind", None) == "content":
                score += 0.08
        elif intent == "click":
            if getattr(candidate, "action_kind", None) == "click":
                score += 0.18
        elif intent == "type":
            if getattr(candidate, "widget_kind", None) in {"input", "select"}:
                score += 0.18
            if getattr(candidate, "action_kind", None) == "type":
                score += 0.10

        lowered = norm_candidate
        if "university information system" in lowered:
            score -= 0.28
        if "not a real information system" in lowered:
            score -= 0.35
        if not raw_informative and len(informative_overlap) < 2 and not phrase_match:
            score -= 0.12

        score = max(0.0, min(score, 1.0))
        if score < 0.28:
            continue

        ranked.append(
            _ScoredCandidate(
                candidate=candidate,
                local_score=score,
                selected_score=score,
                matched_tokens=sorted(raw_informative or informative_overlap),
                intent=intent,
            )
        )

    ranked.sort(key=lambda item: item.local_score, reverse=True)
    return ranked[:limit]


def _best_anchor_for_fragment(
    fragment: object,
    ranked_by_fragment: dict[str, list[_ScoredCandidate]],
    graph: _EvidenceGraph,
) -> _Anchor | None:
    ranked = ranked_by_fragment.get(fragment.id, [])
    anchors = _anchors_from_ranked(ranked, graph)
    if not anchors:
        return None
    anchors.sort(key=lambda item: item.candidate.selected_score, reverse=True)
    return anchors[0]


def _align_fragment_sequence(
    fragments: list[object],
    ranked_by_fragment: dict[str, list[_ScoredCandidate]],
    graph: _EvidenceGraph,
) -> _PathAlignment:
    if not fragments:
        return _PathAlignment(score=0.0, anchors={}, transition_ids=[], state_ids=[])

    fragment_anchors: list[tuple[object, list[_Anchor]]] = []
    for fragment in fragments:
        anchors = _anchors_from_ranked(ranked_by_fragment.get(fragment.id, []), graph)
        fragment_anchors.append((fragment, anchors))

    states: dict[tuple[int, int], _PathAlignment] = {}
    best_overall = _PathAlignment(score=0.0, anchors={}, transition_ids=[], state_ids=[])

    for fragment_index, (fragment, anchors) in enumerate(fragment_anchors):
        if not anchors:
            continue

        next_states: dict[tuple[int, int], _PathAlignment] = {}
        for anchor_index, anchor in enumerate(anchors):
            base = _PathAlignment(
                score=anchor.candidate.selected_score,
                anchors={fragment.id: anchor},
                transition_ids=list(anchor.transition_ids),
                state_ids=[state_id for state_id in [anchor.state_id] if state_id],
            )
            best_state = base

            for (_, _), previous_alignment in states.items():
                previous_anchor = next(reversed(previous_alignment.anchors.values()))
                if anchor.sequence_key < previous_anchor.sequence_key:
                    continue

                bonus = _anchor_continuity_bonus(previous_anchor, anchor)
                candidate_alignment = _PathAlignment(
                    score=previous_alignment.score + anchor.candidate.selected_score + bonus,
                    anchors={**previous_alignment.anchors, fragment.id: anchor},
                    transition_ids=_merge_path_ids(
                        previous_alignment.transition_ids,
                        list(anchor.transition_ids),
                    ),
                    state_ids=_merge_path_ids(
                        previous_alignment.state_ids,
                        [state_id for state_id in [anchor.state_id] if state_id],
                    ),
                )
                if candidate_alignment.score > best_state.score:
                    best_state = candidate_alignment

            key = (fragment_index, anchor_index)
            next_states[key] = best_state
            if best_state.score > best_overall.score:
                best_overall = best_state

        states = next_states or states

    return best_overall


def _anchors_from_ranked(
    ranked: list[_ScoredCandidate],
    graph: _EvidenceGraph,
) -> list[_Anchor]:
    anchors: list[_Anchor] = []
    for scored in ranked:
        anchors.extend(_candidate_to_anchors(scored, graph))

    deduped: dict[tuple[int, str | None, tuple[str, ...]], _Anchor] = {}
    for anchor in anchors:
        key = (anchor.sequence_key, anchor.state_id, anchor.transition_ids)
        existing = deduped.get(key)
        if existing is None or anchor.candidate.selected_score > existing.candidate.selected_score:
            deduped[key] = anchor
    return sorted(
        deduped.values(),
        key=lambda item: (-item.candidate.selected_score, item.sequence_key),
    )[:10]


def _candidate_to_anchors(scored: _ScoredCandidate, graph: _EvidenceGraph) -> list[_Anchor]:
    candidate = scored.candidate
    target_type = getattr(candidate, "target_type", None)
    anchors: list[_Anchor] = []

    if target_type == EvidenceTargetType.TRANSITION.value:
        transition_id = candidate.target_id
        position = graph.transition_order.get(transition_id)
        transition = graph.transitions_by_id.get(transition_id)
        if position is not None and transition is not None:
            anchors.append(
                _Anchor(
                    candidate=scored,
                    sequence_key=position,
                    state_id=transition.to_state_id or transition.from_state_id,
                    transition_ids=(transition.id,),
                    action_ids=(transition.action_id,),
                    element_ids=tuple(),
                )
            )
        return anchors

    if target_type == EvidenceTargetType.ACTION.value:
        for transition_id in graph.action_to_transition_ids.get(candidate.target_id, []):
            transition = graph.transitions_by_id.get(transition_id)
            position = graph.transition_order.get(transition_id)
            if transition is None or position is None:
                continue
            anchors.append(
                _Anchor(
                    candidate=scored,
                    sequence_key=position,
                    state_id=transition.to_state_id or transition.from_state_id,
                    transition_ids=(transition.id,),
                    action_ids=(transition.action_id,),
                    element_ids=(candidate.element_id,) if candidate.element_id else tuple(),
                )
            )
        return anchors

    if target_type == EvidenceTargetType.APPLICATION_STATE.value:
        state_id = candidate.target_id
        transition_ids = graph.state_to_transition_ids.get(state_id, [])
        if transition_ids:
            for transition_id in transition_ids:
                position = graph.transition_order.get(transition_id)
                if position is None:
                    continue
                transition = graph.transitions_by_id[transition_id]
                anchors.append(
                    _Anchor(
                        candidate=scored,
                        sequence_key=position,
                        state_id=state_id,
                        transition_ids=(transition_id,),
                        action_ids=(transition.action_id,),
                        element_ids=tuple(graph.state_to_element_ids.get(state_id, [])[:3]),
                    )
                )
        else:
            anchors.append(
                _Anchor(
                    candidate=scored,
                    sequence_key=10_000_000,
                    state_id=state_id,
                    transition_ids=tuple(),
                    action_ids=tuple(),
                    element_ids=tuple(graph.state_to_element_ids.get(state_id, [])[:3]),
                )
            )
        return anchors

    if target_type == EvidenceTargetType.UI_ELEMENT.value:
        element_id = candidate.target_id
        element = graph.elements_by_id.get(element_id)
        if element is None:
            return anchors
        transition_ids = graph.state_to_transition_ids.get(element.state_id, [])
        if transition_ids:
            for transition_id in transition_ids:
                position = graph.transition_order.get(transition_id)
                if position is None:
                    continue
                transition = graph.transitions_by_id[transition_id]
                anchors.append(
                    _Anchor(
                        candidate=scored,
                        sequence_key=position,
                        state_id=element.state_id,
                        transition_ids=(transition_id,),
                        action_ids=(transition.action_id,),
                        element_ids=(element.id,),
                    )
                )
        else:
            anchors.append(
                _Anchor(
                    candidate=scored,
                    sequence_key=10_000_000,
                    state_id=element.state_id,
                    transition_ids=tuple(),
                    action_ids=tuple(),
                    element_ids=(element.id,),
                )
            )
    return anchors


def _anchor_continuity_bonus(previous: _Anchor, current: _Anchor) -> float:
    bonus = 0.0
    if previous.state_id and current.state_id and previous.state_id == current.state_id:
        bonus += 0.10
    if previous.transition_ids and current.transition_ids:
        previous_index = previous.sequence_key
        current_index = current.sequence_key
        gap = max(0, current_index - previous_index)
        if gap == 0:
            bonus += 0.08
        elif gap == 1:
            bonus += 0.20
        elif gap <= 3:
            bonus += 0.12
        elif gap <= 8:
            bonus += 0.06
    if set(previous.action_ids) & set(current.action_ids):
        bonus += 0.05
    if set(previous.element_ids) & set(current.element_ids):
        bonus += 0.04
    return bonus


def _coverage_for_score(score: float) -> tuple[CoverageStatus, LinkType, ConfidenceLabel]:
    if score >= 0.72:
        return CoverageStatus.COVERED, LinkType.COVERS, ConfidenceLabel.HIGH
    if score >= 0.48:
        return CoverageStatus.PARTIALLY_COVERED, LinkType.PARTIALLY_COVERS, ConfidenceLabel.MEDIUM
    return CoverageStatus.UNCERTAIN, LinkType.SUPPORTS, ConfidenceLabel.LOW


def _aggregate_requirement_coverage(
    *,
    analysis_run_id: str,
    requirement_id: str,
    main_flow_total: int,
    main_flow_matched: int,
    alt_flow_total: int,
    alt_flow_matched: int,
    all_fragment_total: int,
    all_fragment_matched: int,
    confidences: list[float],
    supporting_run_count: int,
) -> CoverageAssessment:
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    main_ratio = main_flow_matched / main_flow_total if main_flow_total else 0.0
    alt_ratio = alt_flow_matched / alt_flow_total if alt_flow_total else 0.0
    all_ratio = all_fragment_matched / all_fragment_total if all_fragment_total else 0.0

    if main_flow_total > 0 and main_ratio >= 1.0 and average_confidence >= 0.62:
        status = CoverageStatus.COVERED
        coverage_ratio = 1.0
        covered_fragment_count = main_flow_matched
    elif main_flow_total > 0 and main_ratio >= 0.6 and average_confidence >= 0.42:
        status = CoverageStatus.PARTIALLY_COVERED
        coverage_ratio = main_ratio
        covered_fragment_count = main_flow_matched
    elif alt_flow_total > 0 and alt_ratio > 0.0 and average_confidence >= 0.35:
        status = CoverageStatus.UNCERTAIN
        coverage_ratio = 0.0
        covered_fragment_count = 0
    elif all_ratio > 0.0 and average_confidence >= 0.30:
        status = CoverageStatus.UNCERTAIN
        coverage_ratio = 0.0
        covered_fragment_count = 0
    else:
        status = CoverageStatus.UNCOVERED
        coverage_ratio = 0.0
        covered_fragment_count = 0

    return CoverageAssessment(
        id=f"coverage-{uuid4().hex}",
        analysis_run_id=analysis_run_id,
        subject_type=CoverageSubjectType.REQUIREMENT,
        subject_id=requirement_id,
        coverage_status=status,
        coverage_ratio=coverage_ratio,
        confidence_ratio=average_confidence if confidences else 0.0,
        covered_fragment_count=covered_fragment_count,
        total_fragment_count=main_flow_total if main_flow_total else all_fragment_total,
        supporting_run_count=supporting_run_count,
        metadata={
            "method": "flow_match",
            "main_flow_ratio": round(main_ratio, 4),
            "alt_flow_ratio": round(alt_ratio, 4),
            "all_fragment_ratio": round(all_ratio, 4),
            "execution_classification": _classify_execution(
                main_flow_total,
                main_flow_matched,
                alt_flow_total,
                alt_flow_matched,
            ),
        },
    )


def _classify_execution(
    main_flow_total: int,
    main_flow_matched: int,
    alt_flow_total: int,
    alt_flow_matched: int,
) -> str:
    main_full = main_flow_total > 0 and main_flow_matched >= main_flow_total
    alt_any = alt_flow_total > 0 and alt_flow_matched > 0
    alt_full = alt_flow_total > 0 and alt_flow_matched >= alt_flow_total

    if main_full and alt_any:
        return "main_and_alt_covered"
    if main_full:
        return "main_path_covered"
    if alt_full:
        return "alt_path_covered"
    if main_flow_matched > 0 and alt_any:
        return "partial_main_and_alt"
    if main_flow_matched > 0:
        return "partial_main"
    if alt_any:
        return "partial_alt"
    return "not_executed"


def _merge_path_ids(left: list[str], right: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*left, *right]:
        if item and item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def _describe_path(state_ids: list[str], transition_ids: list[str]) -> str:
    if state_ids and transition_ids:
        return (
            f"Execution path touches {len(state_ids)} states and {len(transition_ids)} transitions: "
            f"states={', '.join(state_ids[:6])}; transitions={', '.join(transition_ids[:6])}"
        )
    if transition_ids:
        return f"Execution path uses transitions: {', '.join(transition_ids[:8])}"
    if state_ids:
        return f"Execution path uses states: {', '.join(state_ids[:8])}"
    return "No execution path available."


def _build_summary(results: list[RequirementTraceabilityResult]) -> TraceabilitySummary:
    requirement_count = len(results)
    analyzed_requirement_count = sum(
        1 for result in results if result.status == RequirementResultStatus.DONE
    )
    failed_requirement_count = sum(
        1 for result in results if result.status != RequirementResultStatus.DONE
    )
    covered_requirement_count = sum(
        1
        for result in results
        if result.artifact_coverage and result.artifact_coverage.coverage_status == CoverageStatus.COVERED
    )
    partially_covered_requirement_count = sum(
        1
        for result in results
        if result.artifact_coverage and result.artifact_coverage.coverage_status == CoverageStatus.PARTIALLY_COVERED
    )
    uncovered_requirement_count = sum(
        1
        for result in results
        if result.artifact_coverage and result.artifact_coverage.coverage_status == CoverageStatus.UNCOVERED
    )
    uncertain_requirement_count = sum(
        1
        for result in results
        if result.artifact_coverage and result.artifact_coverage.coverage_status == CoverageStatus.UNCERTAIN
    )
    requirement_fragment_count = sum(result.metadata.get("fragment_count", 0) for result in results)
    covered_fragment_count = sum(
        1
        for result in results
        for coverage in result.fragment_coverages
        if coverage.coverage_status == CoverageStatus.COVERED
    )
    trace_link_count = sum(len(result.trace_links) for result in results)
    trace_evidence_count = sum(len(result.trace_evidence) for result in results)
    warning_count = sum(len(result.warnings) for result in results)

    return TraceabilitySummary(
        requirement_count=requirement_count,
        analyzed_requirement_count=analyzed_requirement_count,
        failed_requirement_count=failed_requirement_count,
        covered_requirement_count=covered_requirement_count,
        partially_covered_requirement_count=partially_covered_requirement_count,
        uncovered_requirement_count=uncovered_requirement_count,
        uncertain_requirement_count=uncertain_requirement_count,
        requirement_fragment_count=requirement_fragment_count,
        covered_fragment_count=covered_fragment_count,
        trace_link_count=trace_link_count,
        trace_evidence_count=trace_evidence_count,
        warning_count=warning_count,
        metadata={},
    )
