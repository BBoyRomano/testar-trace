"""Strict graph-connected sequence traceability method."""

from __future__ import annotations

import math
import re
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import pairwise

from reqtrace.models.common import SourceRef
from reqtrace.models.evidence import (
    EvidenceSet,
    ExecutionAction,
    ExecutionElement,
    ExecutionState,
    ExecutionTransition,
)
from reqtrace.models.requirements import (
    RequirementArtifact,
    RequirementFragment,
    RequirementScenario,
    RequirementSet,
)
from reqtrace.models.traceability import (
    CoverageStatus,
    EvidenceRef,
    EvidenceRefKind,
    FragmentMatchKind,
    RequirementCoverage,
    RequirementFragmentAlignment,
    TraceabilityResult,
    TraceabilitySummary,
    TraceLink,
    TraceLinkStatus,
    TraceOccurrence,
    TraceOccurrenceStatus,
)
from reqtrace.progress import TraceContext

__all__ = ["trace_with_graph_sequence"]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "if",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "then",
        "to",
        "user",
        "when",
        "with",
    },
)

_GENERIC_TOKENS = frozenset(
    {
        "button",
        "click",
        "display",
        "enter",
        "form",
        "message",
        "page",
        "select",
        "success",
        "successful",
        "table",
        "value",
    },
)


@dataclass(frozen=True, slots=True)
class _EvidenceCandidate:
    id: str
    kind: EvidenceRefKind
    position: int
    text: str
    refs: tuple[EvidenceRef, ...]
    tokens: frozenset[str]
    transition: ExecutionTransition | None = None


@dataclass(frozen=True, slots=True)
class _RequirementVariant:
    id: str
    name: str
    branch_id: str | None
    fragments: tuple[RequirementFragment, ...]
    metadata: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _CandidateMatch:
    candidate: _EvidenceCandidate
    score: float


@dataclass(frozen=True, slots=True)
class _SequenceMatch:
    variant: _RequirementVariant
    matches: tuple[_CandidateMatch | None, ...]
    score: float
    evidence_path: tuple[_EvidenceCandidate, ...]


@dataclass(frozen=True, slots=True)
class _EvidenceIndex:
    candidates: tuple[_EvidenceCandidate, ...]
    transitions: tuple[_EvidenceCandidate, ...]
    outgoing: Mapping[str, tuple[_EvidenceCandidate, ...]]
    incoming: Mapping[str, tuple[_EvidenceCandidate, ...]]


def trace_with_graph_sequence(
    requirements: RequirementSet,
    evidence: EvidenceSet,
    context: TraceContext,
) -> TraceabilityResult:
    """Trace requirements using strict connected transition sequences.

    This method only moves from one matched transition to the next when the
    transitions are connected by state: ``current.Target == next.Source``.
    """
    return _trace(
        requirements=requirements,
        evidence=evidence,
        context=context,
        method="graph-sequence",
        title="Graph sequence traceability result",
        mode="graph-strict",
    )


def _trace(
    *,
    requirements: RequirementSet,
    evidence: EvidenceSet,
    context: TraceContext,
    method: str,
    title: str,
    mode: str,
) -> TraceabilityResult:
    context.raise_if_cancelled()
    context.report(
        "method-started",
        message=f"Starting {method} traceability method.",
        metadata={"method": method},
    )

    min_score = _float_option(context.options, "min_score", 0.12)
    max_gap = _int_option(context.options, "max_gap", 25)
    max_depth = _int_option(context.options, "max_depth", 8)
    max_sequences_per_variant = _int_option(
        context.options,
        "max_sequences_per_variant",
        10,
    )

    evidence_index = _build_evidence_index(evidence)
    candidates = evidence_index.candidates

    links: list[TraceLink] = []
    occurrences: list[TraceOccurrence] = []
    alignments: list[RequirementFragmentAlignment] = []
    coverage: list[RequirementCoverage] = []

    total_requirements = len(requirements.requirements)
    for requirement_index, requirement in enumerate(requirements.requirements, start=1):
        context.raise_if_cancelled()
        context.report(
            "method-progress",
            completed=requirement_index,
            total=total_requirements,
            metadata={"method": method, "requirement_id": requirement.id},
        )

        variants = _requirement_variants(
            requirements.fragments_for(requirement.id),
            requirements.scenarios_for(requirement.id),
        )
        requirement_sequences = _find_requirement_sequences(
            requirement=requirement,
            variants=variants,
            evidence_index=evidence_index,
            min_score=min_score,
            max_gap=max_gap,
            max_depth=max_depth,
            max_sequences_per_variant=max_sequences_per_variant,
            mode=mode,
        )

        requirement_occurrence_ids: list[str] = []
        for sequence_index, sequence in enumerate(requirement_sequences, start=1):
            occurrence_id = f"{requirement.id}:sequence:{sequence_index}"
            sequence_alignments = _build_alignments(
                requirement=requirement,
                sequence=sequence,
                occurrence_id=occurrence_id,
                sequence_index=sequence_index,
                method=method,
            )
            occurrence = _build_occurrence(
                requirement=requirement,
                sequence=sequence,
                occurrence_id=occurrence_id,
                sequence_index=sequence_index,
                alignment_ids=tuple(alignment.id for alignment in sequence_alignments),
                method=method,
            )
            link = _build_link(
                requirement=requirement,
                occurrence=occurrence,
                sequence=sequence,
                sequence_index=sequence_index,
                method=method,
            )

            alignments.extend(sequence_alignments)
            occurrences.append(occurrence)
            links.append(link)
            requirement_occurrence_ids.append(occurrence.id)

        coverage.append(
            _build_coverage(
                requirement=requirement,
                variants=variants,
                sequences=requirement_sequences,
                occurrences=tuple(
                    occurrence
                    for occurrence in occurrences
                    if occurrence.id in requirement_occurrence_ids
                ),
                method=method,
            ),
        )

    summary = _build_summary(
        total_requirements=total_requirements,
        coverage=tuple(coverage),
        total_links=len(links),
        method=method,
    )

    context.raise_if_cancelled()
    context.report(
        "method-finished",
        message=f"Finished {method} traceability method.",
        metadata={"method": method, "sequence_count": len(occurrences)},
    )

    return TraceabilityResult(
        id=method,
        title=title,
        summary=summary,
        requirement_source_ref=_requirement_source_ref(requirements),
        evidence_source_ref=evidence.source_ref,
        links=tuple(links),
        occurrences=tuple(occurrences),
        fragment_alignments=tuple(alignments),
        coverage=tuple(coverage),
        metadata={
            "method": method,
            "mode": mode,
            "evidence_set_id": evidence.id,
            "candidate_count": len(candidates),
            "transition_candidate_count": len(evidence_index.transitions),
            "sequence_count": len(occurrences),
            "min_score": min_score,
            "max_gap": max_gap,
            "max_depth": max_depth,
            "max_sequences_per_variant": max_sequences_per_variant,
        },
    )


def _build_evidence_index(evidence: EvidenceSet) -> _EvidenceIndex:
    candidates = _build_evidence_candidates(evidence)
    transitions = tuple(
        candidate for candidate in candidates if candidate.transition is not None
    )

    outgoing: dict[str, list[_EvidenceCandidate]] = {}
    incoming: dict[str, list[_EvidenceCandidate]] = {}
    for candidate in transitions:
        transition = candidate.transition
        if transition is None:
            continue
        outgoing.setdefault(transition.from_state_id, []).append(candidate)
        if transition.to_state_id is not None:
            incoming.setdefault(transition.to_state_id, []).append(candidate)

    return _EvidenceIndex(
        candidates=candidates,
        transitions=transitions,
        outgoing={
            state_id: tuple(sorted(items, key=lambda item: item.position))
            for state_id, items in outgoing.items()
        },
        incoming={
            state_id: tuple(sorted(items, key=lambda item: item.position))
            for state_id, items in incoming.items()
        },
    )


def _build_evidence_candidates(evidence: EvidenceSet) -> tuple[_EvidenceCandidate, ...]:
    state_by_id = {state.id: state for state in evidence.states}
    action_by_id = {action.id: action for action in evidence.actions}
    elements_by_state = _elements_by_state(evidence.elements)

    if evidence.transitions:
        transitions = sorted(
            evidence.transitions,
            key=lambda transition: (
                transition.order_index is None,
                transition.order_index or 0,
                transition.id,
            ),
        )
        return tuple(
            _transition_candidate(
                transition=transition,
                position=position,
                state_by_id=state_by_id,
                action_by_id=action_by_id,
                elements_by_state=elements_by_state,
            )
            for position, transition in enumerate(transitions)
        )

    candidates: list[_EvidenceCandidate] = []
    for artifact in evidence.artifacts:
        candidates.append(
            _candidate(
                candidate_id=artifact.id,
                kind=EvidenceRefKind.ARTIFACT,
                position=len(candidates),
                refs=(EvidenceRef(EvidenceRefKind.ARTIFACT, artifact.id),),
                text=_join_text(
                    artifact.id,
                    artifact.title,
                    artifact.text,
                    _metadata_text(artifact.metadata),
                ),
            ),
        )
    for state in evidence.states:
        candidates.append(
            _candidate(
                candidate_id=state.id,
                kind=EvidenceRefKind.STATE,
                position=len(candidates),
                refs=(EvidenceRef(EvidenceRefKind.STATE, state.id),),
                text=_state_text(state, elements_by_state.get(state.id, ())),
            ),
        )
    for element in evidence.elements:
        candidates.append(
            _candidate(
                candidate_id=element.id,
                kind=EvidenceRefKind.ELEMENT,
                position=len(candidates),
                refs=(EvidenceRef(EvidenceRefKind.ELEMENT, element.id),),
                text=_element_text(element),
            ),
        )
    for action in evidence.actions:
        candidates.append(
            _candidate(
                candidate_id=action.id,
                kind=EvidenceRefKind.ACTION,
                position=len(candidates),
                refs=(EvidenceRef(EvidenceRefKind.ACTION, action.id),),
                text=_action_text(action),
            ),
        )
    return tuple(candidates)


def _transition_candidate(
    *,
    transition: ExecutionTransition,
    position: int,
    state_by_id: Mapping[str, ExecutionState],
    action_by_id: Mapping[str, ExecutionAction],
    elements_by_state: Mapping[str, tuple[ExecutionElement, ...]],
) -> _EvidenceCandidate:
    action = action_by_id.get(transition.action_id)
    from_state = state_by_id.get(transition.from_state_id)
    to_state = (
        state_by_id.get(transition.to_state_id)
        if transition.to_state_id is not None
        else None
    )

    refs = [
        EvidenceRef(EvidenceRefKind.TRANSITION, transition.id),
        EvidenceRef(EvidenceRefKind.ACTION, transition.action_id),
        EvidenceRef(EvidenceRefKind.STATE, transition.from_state_id),
    ]
    if transition.to_state_id is not None:
        refs.append(EvidenceRef(EvidenceRefKind.STATE, transition.to_state_id))

    text = _join_text(
        transition.id,
        _action_text(action) if action is not None else transition.action_id,
        _state_text(from_state, elements_by_state.get(transition.from_state_id, ()))
        if from_state is not None
        else transition.from_state_id,
        _state_text(to_state, elements_by_state.get(transition.to_state_id or "", ()))
        if to_state is not None
        else transition.to_state_id,
        _metadata_text(transition.metadata),
    )
    return _candidate(
        candidate_id=transition.id,
        kind=EvidenceRefKind.TRANSITION,
        position=position,
        refs=_unique_refs(tuple(refs)),
        text=text,
        transition=transition,
    )


def _find_requirement_sequences(
    *,
    requirement: RequirementArtifact,
    variants: tuple[_RequirementVariant, ...],
    evidence_index: _EvidenceIndex,
    min_score: float,
    max_gap: int,
    max_depth: int,
    max_sequences_per_variant: int,
    mode: str,
) -> tuple[_SequenceMatch, ...]:
    sequences: list[_SequenceMatch] = []
    for variant in variants:
        sequences.extend(
            _find_variant_sequences(
                requirement=requirement,
                variant=variant,
                evidence_index=evidence_index,
                min_score=min_score,
                max_gap=max_gap,
                max_depth=max_depth,
                limit=max_sequences_per_variant,
                mode=mode,
            ),
        )
    return tuple(
        sorted(
            sequences,
            key=lambda sequence: (
                sequence.score,
                _matched_count(sequence.matches),
                sequence.variant.name == "main",
            ),
            reverse=True,
        ),
    )


def _find_variant_sequences(
    *,
    requirement: RequirementArtifact,
    variant: _RequirementVariant,
    evidence_index: _EvidenceIndex,
    min_score: float,
    max_gap: int,
    max_depth: int,
    limit: int,
    mode: str,
) -> tuple[_SequenceMatch, ...]:
    candidates = evidence_index.candidates
    if not variant.fragments or not candidates:
        return ()

    matches_by_fragment = tuple(
        _candidate_matches(requirement, fragment, candidates, min_score)
        for fragment in variant.fragments
    )
    anchors = [
        (fragment_index, candidate_match)
        for fragment_index, candidate_matches in enumerate(matches_by_fragment)
        for candidate_match in candidate_matches
    ]
    if not anchors:
        return ()

    deduped: dict[tuple[str, ...], _SequenceMatch] = {}
    for fragment_index, candidate_match in anchors:
        sequence = _expand_sequence(
            variant=variant,
            matches_by_fragment=matches_by_fragment,
            evidence_index=evidence_index,
            anchor_index=fragment_index,
            anchor_match=candidate_match,
            max_gap=max_gap,
            max_depth=max_depth,
            mode=mode,
        )
        signature = _sequence_signature(sequence)
        existing = deduped.get(signature)
        if existing is None or sequence.score > existing.score:
            deduped[signature] = sequence

    return tuple(
        sorted(
            deduped.values(),
            key=lambda sequence: (sequence.score, _matched_count(sequence.matches)),
            reverse=True,
        )[:limit],
    )


def _candidate_matches(
    requirement: RequirementArtifact,
    fragment: RequirementFragment,
    candidates: tuple[_EvidenceCandidate, ...],
    min_score: float,
) -> tuple[_CandidateMatch, ...]:
    fragment_tokens = _tokens_for_fragment(requirement, fragment)
    matches = [
        _CandidateMatch(candidate=candidate, score=score)
        for candidate in candidates
        if (score := _match_score(fragment_tokens, candidate.tokens)) >= min_score
    ]
    return tuple(
        sorted(
            matches,
            key=lambda candidate_match: (
                candidate_match.score,
                -candidate_match.candidate.position,
            ),
            reverse=True,
        ),
    )


def _expand_sequence(
    *,
    variant: _RequirementVariant,
    matches_by_fragment: tuple[tuple[_CandidateMatch, ...], ...],
    evidence_index: _EvidenceIndex,
    anchor_index: int,
    anchor_match: _CandidateMatch,
    max_gap: int,
    max_depth: int,
    mode: str,
) -> _SequenceMatch:
    if mode == "graph-strict":
        return _expand_graph_sequence(
            variant=variant,
            matches_by_fragment=matches_by_fragment,
            evidence_index=evidence_index,
            anchor_index=anchor_index,
            anchor_match=anchor_match,
            max_depth=1,
            include_unmatched=False,
        )
    if mode == "graph-window":
        return _expand_graph_sequence(
            variant=variant,
            matches_by_fragment=matches_by_fragment,
            evidence_index=evidence_index,
            anchor_index=anchor_index,
            anchor_match=anchor_match,
            max_depth=max_depth,
            include_unmatched=True,
        )
    return _expand_ordered_sequence(
        variant=variant,
        matches_by_fragment=matches_by_fragment,
        anchor_index=anchor_index,
        anchor_match=anchor_match,
        max_gap=max_gap,
    )


def _expand_ordered_sequence(
    *,
    variant: _RequirementVariant,
    matches_by_fragment: tuple[tuple[_CandidateMatch, ...], ...],
    anchor_index: int,
    anchor_match: _CandidateMatch,
    max_gap: int,
) -> _SequenceMatch:
    matches: list[_CandidateMatch | None] = [None] * len(variant.fragments)
    matches[anchor_index] = anchor_match

    current_position = anchor_match.candidate.position
    for fragment_index in range(anchor_index - 1, -1, -1):
        selected = _select_ordered_neighbor_match(
            matches_by_fragment[fragment_index],
            current_position=current_position,
            direction=-1,
            max_gap=max_gap,
        )
        matches[fragment_index] = selected
        if selected is not None:
            current_position = selected.candidate.position

    current_position = anchor_match.candidate.position
    for fragment_index in range(anchor_index + 1, len(variant.fragments)):
        selected = _select_ordered_neighbor_match(
            matches_by_fragment[fragment_index],
            current_position=current_position,
            direction=1,
            max_gap=max_gap,
        )
        matches[fragment_index] = selected
        if selected is not None:
            current_position = selected.candidate.position

    return _make_sequence(
        variant=variant,
        matches=tuple(matches),
        evidence_path=tuple(
            candidate_match.candidate
            for candidate_match in matches
            if candidate_match is not None
        ),
        path_penalty=1.0,
    )


def _expand_graph_sequence(
    *,
    variant: _RequirementVariant,
    matches_by_fragment: tuple[tuple[_CandidateMatch, ...], ...],
    evidence_index: _EvidenceIndex,
    anchor_index: int,
    anchor_match: _CandidateMatch,
    max_depth: int,
    include_unmatched: bool,
) -> _SequenceMatch:
    if anchor_match.candidate.transition is None:
        return _make_sequence(
            variant=variant,
            matches=_single_anchor_matches(
                fragment_count=len(variant.fragments),
                anchor_index=anchor_index,
                anchor_match=anchor_match,
            ),
            evidence_path=(anchor_match.candidate,),
            path_penalty=0.5,
        )

    matches: list[_CandidateMatch | None] = [None] * len(variant.fragments)
    matches[anchor_index] = anchor_match

    left_paths: list[_EvidenceCandidate] = []
    current = anchor_match.candidate
    total_gap = 0
    for fragment_index in range(anchor_index - 1, -1, -1):
        selected, bridge = _select_graph_neighbor_match(
            matches_by_fragment[fragment_index],
            evidence_index=evidence_index,
            current=current,
            direction=-1,
            max_depth=max_depth,
        )
        matches[fragment_index] = selected
        if selected is None:
            continue
        if include_unmatched:
            left_paths = list(bridge[:-1]) + left_paths
        current = selected.candidate
        total_gap += max(0, len(bridge) - 1)

    right_paths: list[_EvidenceCandidate] = []
    current = anchor_match.candidate
    for fragment_index in range(anchor_index + 1, len(variant.fragments)):
        selected, bridge = _select_graph_neighbor_match(
            matches_by_fragment[fragment_index],
            evidence_index=evidence_index,
            current=current,
            direction=1,
            max_depth=max_depth,
        )
        matches[fragment_index] = selected
        if selected is None:
            continue
        if include_unmatched:
            right_paths.extend(bridge[1:])
        current = selected.candidate
        total_gap += max(0, len(bridge) - 1)

    evidence_path = _dedupe_candidate_path(
        (
            *left_paths,
            *(
                candidate_match.candidate
                for candidate_match in matches
                if candidate_match is not None
            ),
            *right_paths,
        ),
    )
    if not evidence_path:
        evidence_path = (anchor_match.candidate,)

    path_penalty = 1.0 / (1.0 + 0.04 * total_gap)
    return _make_sequence(
        variant=variant,
        matches=tuple(matches),
        evidence_path=evidence_path,
        path_penalty=path_penalty,
    )


def _single_anchor_matches(
    *,
    fragment_count: int,
    anchor_index: int,
    anchor_match: _CandidateMatch,
) -> tuple[_CandidateMatch | None, ...]:
    matches: list[_CandidateMatch | None] = [None] * fragment_count
    matches[anchor_index] = anchor_match
    return tuple(matches)


def _select_graph_neighbor_match(
    matches: tuple[_CandidateMatch, ...],
    *,
    evidence_index: _EvidenceIndex,
    current: _EvidenceCandidate,
    direction: int,
    max_depth: int,
) -> tuple[_CandidateMatch | None, tuple[_EvidenceCandidate, ...]]:
    reachable = _reachable_candidates(
        evidence_index=evidence_index,
        current=current,
        direction=direction,
        max_depth=max_depth,
    )
    if not reachable:
        return None, ()

    reachable_by_id = {candidate.id: path for candidate, path in reachable}
    selectable = [
        candidate_match
        for candidate_match in matches
        if candidate_match.candidate.id in reachable_by_id
    ]
    if not selectable:
        return None, ()

    selected = max(
        selectable,
        key=lambda candidate_match: (
            candidate_match.score
            - 0.01 * (len(reachable_by_id[candidate_match.candidate.id]) - 1),
            -len(reachable_by_id[candidate_match.candidate.id]),
        ),
    )
    return selected, reachable_by_id[selected.candidate.id]


def _reachable_candidates(
    *,
    evidence_index: _EvidenceIndex,
    current: _EvidenceCandidate,
    direction: int,
    max_depth: int,
) -> tuple[tuple[_EvidenceCandidate, tuple[_EvidenceCandidate, ...]], ...]:
    transition = current.transition
    if transition is None:
        return ()

    start_state = transition.from_state_id if direction < 0 else transition.to_state_id
    if start_state is None:
        return ()

    queue: deque[tuple[str, tuple[_EvidenceCandidate, ...]]] = deque()
    queue.append((start_state, (current,)))
    seen: set[tuple[str, int]] = {(start_state, 0)}
    found: list[tuple[_EvidenceCandidate, tuple[_EvidenceCandidate, ...]]] = []

    while queue:
        state_id, path = queue.popleft()
        depth = len(path) - 1
        if depth >= max_depth:
            continue

        neighbors = (
            evidence_index.incoming.get(state_id, ())
            if direction < 0
            else evidence_index.outgoing.get(state_id, ())
        )
        for neighbor in neighbors:
            if neighbor.id == current.id:
                continue
            neighbor_transition = neighbor.transition
            if neighbor_transition is None:
                continue

            next_state = (
                neighbor_transition.from_state_id
                if direction < 0
                else neighbor_transition.to_state_id
            )
            if next_state is None:
                continue

            next_path = (neighbor, *path) if direction < 0 else (*path, neighbor)
            found.append((neighbor, next_path))

            state_key = (next_state, depth + 1)
            if state_key in seen:
                continue
            seen.add(state_key)
            queue.append((next_state, next_path))

    return tuple(found)


def _select_ordered_neighbor_match(
    matches: tuple[_CandidateMatch, ...],
    *,
    current_position: int,
    direction: int,
    max_gap: int,
) -> _CandidateMatch | None:
    selectable = [
        candidate_match
        for candidate_match in matches
        if _is_in_sequence_window(
            candidate_match.candidate.position,
            current_position=current_position,
            direction=direction,
            max_gap=max_gap,
        )
    ]
    if not selectable:
        return None
    return max(
        selectable,
        key=lambda candidate_match: (
            candidate_match.score
            - 0.002 * abs(candidate_match.candidate.position - current_position),
            -abs(candidate_match.candidate.position - current_position),
        ),
    )


def _is_in_sequence_window(
    position: int,
    *,
    current_position: int,
    direction: int,
    max_gap: int,
) -> bool:
    if direction < 0 and position > current_position:
        return False
    if direction > 0 and position < current_position:
        return False
    return abs(position - current_position) <= max_gap


def _make_sequence(
    *,
    variant: _RequirementVariant,
    matches: tuple[_CandidateMatch | None, ...],
    evidence_path: tuple[_EvidenceCandidate, ...],
    path_penalty: float,
) -> _SequenceMatch:
    return _SequenceMatch(
        variant=variant,
        matches=matches,
        score=_sequence_score(matches, len(variant.fragments), path_penalty),
        evidence_path=evidence_path,
    )


def _requirement_variants(
    fragments: tuple[RequirementFragment, ...],
    scenarios: tuple[RequirementScenario, ...],
) -> tuple[_RequirementVariant, ...]:
    scenario_variants = _scenario_variants(fragments, scenarios)
    if scenario_variants:
        return scenario_variants

    ordered = tuple(
        sorted(
            fragments,
            key=lambda fragment: (
                fragment.order_index is None,
                fragment.order_index or 0,
                fragment.id,
            ),
        ),
    )
    preconditions = tuple(
        fragment
        for fragment in ordered
        if fragment.branch_id is None and _fragment_kind_contains(fragment, "pre")
    )
    postconditions = tuple(
        fragment
        for fragment in ordered
        if fragment.branch_id is None and _fragment_kind_contains(fragment, "post")
    )
    main_flow = tuple(
        fragment
        for fragment in ordered
        if fragment not in preconditions
        and fragment not in postconditions
        and fragment.branch_id is None
        and not _is_alternative_fragment(fragment)
        and not _fragment_kind_contains(fragment, "constraint")
    )

    variants: list[_RequirementVariant] = []
    if preconditions or main_flow or postconditions:
        variants.append(
            _RequirementVariant(
                id="main",
                name="main",
                branch_id=None,
                fragments=preconditions + main_flow + postconditions,
                metadata={},
            ),
        )

    for branch_id, alternative_flow in _alternative_flows(ordered).items():
        variants.append(
            _RequirementVariant(
                id=branch_id,
                name="alternative",
                branch_id=branch_id,
                fragments=preconditions + alternative_flow + postconditions,
                metadata={},
            ),
        )

    if not variants and ordered:
        variants.append(
            _RequirementVariant(
                id="main",
                name="main",
                branch_id=None,
                fragments=ordered,
                metadata={},
            ),
        )

    return tuple(variants)


def _scenario_variants(
    fragments: tuple[RequirementFragment, ...],
    scenarios: tuple[RequirementScenario, ...],
) -> tuple[_RequirementVariant, ...]:
    fragment_by_id = {fragment.id: fragment for fragment in fragments}
    variants: list[_RequirementVariant] = []
    for scenario in sorted(
        scenarios,
        key=lambda item: (
            item.order_index is None,
            item.order_index or 0,
            item.id,
        ),
    ):
        scenario_fragments = tuple(
            fragment_by_id[fragment_id]
            for fragment_id in scenario.fragment_ids
            if fragment_id in fragment_by_id
        )
        if not scenario_fragments:
            continue
        branch_id = _scenario_branch_id(scenario)
        variants.append(
            _RequirementVariant(
                id=scenario.id,
                name=scenario.kind,
                branch_id=branch_id,
                fragments=scenario_fragments,
                metadata=scenario.metadata,
            ),
        )
    return tuple(variants)


def _scenario_branch_id(scenario: RequirementScenario) -> str | None:
    for key in ("branch_id", "branch_label"):
        value = scenario.metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _alternative_flows(
    fragments: tuple[RequirementFragment, ...],
) -> dict[str, tuple[RequirementFragment, ...]]:
    flows: dict[str, list[RequirementFragment]] = {}
    for fragment in fragments:
        if not _is_alternative_fragment(fragment):
            continue
        branch_id = fragment.branch_id or "alternative"
        flows.setdefault(branch_id, []).append(fragment)
    return {
        branch_id: tuple(flow)
        for branch_id, flow in sorted(flows.items(), key=lambda item: item[0])
    }


def _is_alternative_fragment(fragment: RequirementFragment) -> bool:
    return fragment.branch_id is not None or _fragment_kind_contains(
        fragment,
        "alternative",
        "alternate",
        "exception",
    )


def _fragment_kind_contains(
    fragment: RequirementFragment,
    *needles: str,
) -> bool:
    normalized = fragment.kind.strip().lower().replace("_", "-")
    return any(needle in normalized for needle in needles)


def _tokens_for_fragment(
    requirement: RequirementArtifact,
    fragment: RequirementFragment,
) -> frozenset[str]:
    return _tokenize(
        _join_text(
            fragment.text,
            requirement.title,
            requirement.summary,
            requirement.actor,
            requirement.scope,
        ),
    )


def _match_score(
    requirement_tokens: frozenset[str],
    evidence_tokens: frozenset[str],
) -> float:
    if not requirement_tokens or not evidence_tokens:
        return 0.0

    overlap = requirement_tokens & evidence_tokens
    if not overlap:
        return 0.0

    useful_overlap = overlap - _GENERIC_TOKENS
    generic_overlap = overlap & _GENERIC_TOKENS
    weighted_overlap = len(useful_overlap) + 0.35 * len(generic_overlap)

    denominator = math.sqrt(len(requirement_tokens) * len(evidence_tokens))
    return min(1.0, weighted_overlap / denominator)


def _build_alignments(
    *,
    requirement: RequirementArtifact,
    sequence: _SequenceMatch,
    occurrence_id: str,
    sequence_index: int,
    method: str,
) -> tuple[RequirementFragmentAlignment, ...]:
    alignments: list[RequirementFragmentAlignment] = []
    for fragment_index, (fragment, candidate_match) in enumerate(
        zip(sequence.variant.fragments, sequence.matches, strict=True),
        start=1,
    ):
        if candidate_match is None:
            continue
        alignments.append(
            RequirementFragmentAlignment(
                id=f"{occurrence_id}:alignment:{fragment_index}",
                requirement_id=requirement.id,
                fragment_id=fragment.id,
                occurrence_id=occurrence_id,
                evidence_refs=candidate_match.candidate.refs,
                match_kind=_match_kind(candidate_match.score),
                score=round(candidate_match.score, 4),
                rationale=(
                    "Requirement fragment text overlaps with evidence in a sequence."
                ),
                fragment_kind=fragment.kind,
                metadata={
                    "method": method,
                    "scenario_id": sequence.variant.id,
                    "variant": sequence.variant.name,
                    "branch_id": sequence.variant.branch_id,
                    "sequence_index": sequence_index,
                    "fragment_position": fragment_index,
                    "evidence_candidate_id": candidate_match.candidate.id,
                    "evidence_candidate_kind": candidate_match.candidate.kind.value,
                    "evidence_position": candidate_match.candidate.position,
                    "requirement_text": fragment.text,
                    "evidence_text": candidate_match.candidate.text,
                },
            ),
        )
    return tuple(alignments)


def _build_occurrence(
    *,
    requirement: RequirementArtifact,
    sequence: _SequenceMatch,
    occurrence_id: str,
    sequence_index: int,
    alignment_ids: tuple[str, ...],
    method: str,
) -> TraceOccurrence:
    matched = _matched_count(sequence.matches)
    total = len(sequence.matches)
    status = (
        TraceOccurrenceStatus.FULL
        if total > 0 and matched == total
        else TraceOccurrenceStatus.PARTIAL
    )
    evidence_path_refs = _evidence_path(sequence.evidence_path)
    return TraceOccurrence(
        id=occurrence_id,
        requirement_id=requirement.id,
        status=status,
        evidence_path=evidence_path_refs,
        alignment_ids=alignment_ids,
        score=round(sequence.score, 4),
        rationale=_occurrence_rationale(matched, total),
        metadata={
            "method": method,
            "scenario_id": sequence.variant.id,
            "variant": sequence.variant.name,
            "branch_id": sequence.variant.branch_id,
            "sequence_index": sequence_index,
            "matched_fragment_count": matched,
            "total_fragment_count": total,
            "candidate_ids": tuple(
                candidate_match.candidate.id
                for candidate_match in sequence.matches
                if candidate_match is not None
            ),
            "evidence_path_candidate_ids": tuple(
                candidate.id for candidate in sequence.evidence_path
            ),
            "signature": _sequence_signature(sequence),
        },
    )


def _build_link(
    *,
    requirement: RequirementArtifact,
    occurrence: TraceOccurrence,
    sequence: _SequenceMatch,
    sequence_index: int,
    method: str,
) -> TraceLink:
    evidence_ids = _unique_strings(
        evidence_ref.evidence_id for evidence_ref in occurrence.evidence_path
    )
    return TraceLink(
        id=f"{occurrence.id}:link",
        requirement_id=requirement.id,
        evidence_ids=evidence_ids,
        status=TraceLinkStatus.MATCHED
        if occurrence.status is TraceOccurrenceStatus.FULL
        else TraceLinkStatus.PARTIAL,
        score=occurrence.score,
        rationale=occurrence.rationale,
        metadata={
            "method": method,
            "scenario_id": sequence.variant.id,
            "occurrence_id": occurrence.id,
            "variant": sequence.variant.name,
            "branch_id": sequence.variant.branch_id,
            "sequence_index": sequence_index,
        },
    )


def _build_coverage(
    *,
    requirement: RequirementArtifact,
    variants: tuple[_RequirementVariant, ...],
    sequences: tuple[_SequenceMatch, ...],
    occurrences: tuple[TraceOccurrence, ...],
    method: str,
) -> RequirementCoverage:
    scenario_coverage = _build_scenario_coverage(
        variants=variants,
        occurrences=occurrences,
    )
    if not variants or not sequences or not occurrences:
        return RequirementCoverage(
            requirement_id=requirement.id,
            status=CoverageStatus.NOT_COVERED,
            coverage_ratio=0.0,
            rationale="No matching evidence sequence was found.",
            metadata={
                "method": method,
                "requirement_title": requirement.title,
                "sequence_count": 0,
                "scenario_coverage": scenario_coverage,
            },
        )

    best_occurrence = max(
        occurrences,
        key=lambda occurrence: occurrence.score or 0.0,
    )
    covered_scenarios = sum(
        item["status"] == CoverageStatus.COVERED.value for item in scenario_coverage
    )
    partial_scenarios = sum(
        item["status"] == CoverageStatus.PARTIALLY_COVERED.value
        for item in scenario_coverage
    )
    status = _requirement_coverage_status(
        total_scenarios=len(scenario_coverage),
        covered_scenarios=covered_scenarios,
        partial_scenarios=partial_scenarios,
    )
    coverage_ratio = (
        sum(_scenario_ratio(item) for item in scenario_coverage)
        / len(scenario_coverage)
        if scenario_coverage
        else 0.0
    )
    return RequirementCoverage(
        requirement_id=requirement.id,
        status=status,
        linked_evidence_ids=_unique_strings(
            evidence_ref.evidence_id for evidence_ref in best_occurrence.evidence_path
        ),
        coverage_ratio=round(coverage_ratio, 4),
        rationale=_coverage_rationale(
            covered_scenarios=covered_scenarios,
            partial_scenarios=partial_scenarios,
            total_scenarios=len(scenario_coverage),
        ),
        metadata={
            "method": method,
            "requirement_title": requirement.title,
            "sequence_count": len(sequences),
            "best_occurrence_id": best_occurrence.id,
            "scenario_coverage": scenario_coverage,
        },
    )


def _build_scenario_coverage(
    *,
    variants: tuple[_RequirementVariant, ...],
    occurrences: tuple[TraceOccurrence, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _scenario_coverage(variant=variant, occurrences=occurrences)
        for variant in variants
    )


def _scenario_coverage(
    *,
    variant: _RequirementVariant,
    occurrences: tuple[TraceOccurrence, ...],
) -> dict[str, object]:
    variant_occurrences = tuple(
        occurrence
        for occurrence in occurrences
        if occurrence.metadata.get("scenario_id") == variant.id
    )
    best_occurrence = max(
        variant_occurrences,
        key=lambda occurrence: occurrence.score or 0.0,
        default=None,
    )
    full = any(
        occurrence.status is TraceOccurrenceStatus.FULL
        for occurrence in variant_occurrences
    )
    status = (
        CoverageStatus.COVERED
        if full
        else CoverageStatus.PARTIALLY_COVERED
        if variant_occurrences
        else CoverageStatus.NOT_COVERED
    )
    best_metadata = best_occurrence.metadata if best_occurrence is not None else {}
    matched_fragment_count = best_metadata.get("matched_fragment_count", 0)
    total_fragment_count = len(variant.fragments)
    return {
        "scenario_id": variant.id,
        "kind": variant.name,
        "branch_id": variant.branch_id,
        "status": status.value,
        "coverage_ratio": _fragment_coverage_ratio(
            matched_fragment_count=matched_fragment_count,
            total_fragment_count=total_fragment_count,
        ),
        "best_score": round(best_occurrence.score or 0.0, 4)
        if best_occurrence is not None
        else None,
        "best_occurrence_id": best_occurrence.id
        if best_occurrence is not None
        else None,
        "matched_fragment_count": matched_fragment_count,
        "total_fragment_count": total_fragment_count,
        "sequence_count": len(variant_occurrences),
    }


def _requirement_coverage_status(
    *,
    total_scenarios: int,
    covered_scenarios: int,
    partial_scenarios: int,
) -> CoverageStatus:
    if total_scenarios > 0 and covered_scenarios == total_scenarios:
        return CoverageStatus.COVERED
    if covered_scenarios > 0 or partial_scenarios > 0:
        return CoverageStatus.PARTIALLY_COVERED
    return CoverageStatus.NOT_COVERED


def _coverage_rationale(
    *,
    covered_scenarios: int,
    partial_scenarios: int,
    total_scenarios: int,
) -> str:
    not_covered = total_scenarios - covered_scenarios - partial_scenarios
    return (
        f"{covered_scenarios}/{total_scenarios} scenarios fully covered; "
        f"{partial_scenarios} partially covered; {not_covered} not covered."
    )


def _scenario_ratio(item: Mapping[str, object]) -> float:
    value = item.get("coverage_ratio")
    return value if isinstance(value, (int, float)) else 0.0


def _fragment_coverage_ratio(
    *,
    matched_fragment_count: object,
    total_fragment_count: int,
) -> float:
    if total_fragment_count <= 0 or not isinstance(matched_fragment_count, int):
        return 0.0
    return round(matched_fragment_count / total_fragment_count, 4)


def _build_summary(
    *,
    total_requirements: int,
    coverage: tuple[RequirementCoverage, ...],
    total_links: int,
    method: str,
) -> TraceabilitySummary:
    covered = sum(
        requirement_coverage.status is CoverageStatus.COVERED
        for requirement_coverage in coverage
    )
    partial = sum(
        requirement_coverage.status is CoverageStatus.PARTIALLY_COVERED
        for requirement_coverage in coverage
    )
    uncovered = total_requirements - covered - partial
    requirements_coverage_ratio = _requirements_coverage_ratio(coverage)
    return TraceabilitySummary(
        total_requirements=total_requirements,
        covered_requirements=covered,
        partially_covered_requirements=partial,
        uncovered_requirements=uncovered,
        total_links=total_links,
        metadata={
            "method": method,
            "requirements_coverage_ratio": requirements_coverage_ratio,
        },
    )


def _requirements_coverage_ratio(
    coverage: tuple[RequirementCoverage, ...],
) -> float:
    if not coverage:
        return 0.0
    return round(
        sum(item.coverage_ratio or 0.0 for item in coverage) / len(coverage),
        4,
    )


def _candidate(
    *,
    candidate_id: str,
    kind: EvidenceRefKind,
    position: int,
    refs: tuple[EvidenceRef, ...],
    text: str,
    transition: ExecutionTransition | None = None,
) -> _EvidenceCandidate:
    return _EvidenceCandidate(
        id=candidate_id,
        kind=kind,
        position=position,
        text=text,
        refs=refs,
        tokens=_tokenize(text),
        transition=transition,
    )


def _match_kind(score: float) -> FragmentMatchKind:
    if score >= 0.85:
        return FragmentMatchKind.EXACT
    if score >= 0.45:
        return FragmentMatchKind.SEMANTIC
    return FragmentMatchKind.PARTIAL


def _occurrence_rationale(matched: int, total: int) -> str:
    if matched == total:
        return "All requirement fragments were found in an evidence sequence."
    return f"{matched} of {total} requirement fragments were found in evidence."


def _sequence_score(
    matches: tuple[_CandidateMatch | None, ...],
    total_fragments: int,
    path_penalty: float,
) -> float:
    if total_fragments == 0:
        return 0.0
    scores = [
        candidate_match.score
        for candidate_match in matches
        if candidate_match is not None
    ]
    if not scores:
        return 0.0
    completeness = len(scores) / total_fragments
    return min(1.0, (sum(scores) / len(scores)) * completeness * path_penalty)


def _matched_count(matches: tuple[_CandidateMatch | None, ...]) -> int:
    return sum(candidate_match is not None for candidate_match in matches)


def _sequence_signature(sequence: _SequenceMatch) -> tuple[str, ...]:
    return (
        sequence.variant.id,
        sequence.variant.name,
        sequence.variant.branch_id or "",
        *(candidate.id for candidate in sequence.evidence_path),
        "|",
        *(
            candidate_match.candidate.id if candidate_match is not None else ""
            for candidate_match in sequence.matches
        ),
    )


def _evidence_path(
    candidates: tuple[_EvidenceCandidate, ...],
) -> tuple[EvidenceRef, ...]:
    refs: list[EvidenceRef] = []
    for candidate in candidates:
        refs.extend(candidate.refs)
    return _unique_refs(tuple(refs))


def _dedupe_candidate_path(
    candidates: Iterable[_EvidenceCandidate],
) -> tuple[_EvidenceCandidate, ...]:
    seen: set[str] = set()
    unique: list[_EvidenceCandidate] = []
    for candidate in candidates:
        if candidate.id in seen:
            continue
        seen.add(candidate.id)
        unique.append(candidate)
    return tuple(sorted(unique, key=lambda item: item.position))


def _unique_refs(refs: tuple[EvidenceRef, ...]) -> tuple[EvidenceRef, ...]:
    seen: set[tuple[EvidenceRefKind, str]] = set()
    unique: list[EvidenceRef] = []
    for ref in refs:
        key = (ref.kind, ref.evidence_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(ref)
    return tuple(unique)


def _unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return tuple(unique)


def _elements_by_state(
    elements: tuple[ExecutionElement, ...],
) -> dict[str, tuple[ExecutionElement, ...]]:
    grouped: dict[str, list[ExecutionElement]] = {}
    for element in elements:
        grouped.setdefault(element.state_id, []).append(element)
    return {state_id: tuple(items) for state_id, items in grouped.items()}


def _state_text(
    state: ExecutionState,
    elements: tuple[ExecutionElement, ...],
) -> str:
    return _join_text(
        state.id,
        state.name,
        state.title,
        state.url,
        _metadata_text(state.metadata),
        *(_element_text(element) for element in elements),
    )


def _element_text(element: ExecutionElement) -> str:
    return _join_text(
        element.id,
        element.tag_name,
        element.role,
        element.text,
        element.title,
        element.href,
        element.css_selector,
        _metadata_text(element.metadata),
    )


def _action_text(action: ExecutionAction) -> str:
    return _join_text(
        action.id,
        action.description,
        _metadata_text(action.metadata),
    )


def _metadata_text(metadata: Mapping[str, object]) -> str:
    return _join_text(*_string_values(metadata.values()))


def _string_values(values: Iterable[object]) -> tuple[str, ...]:
    text: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            text.append(value)
        elif isinstance(value, (int, float, bool)):
            text.append(str(value))
        elif isinstance(value, Mapping):
            text.extend(_string_values(value.values()))
        elif isinstance(value, Iterable):
            text.extend(_string_values(value))
    return tuple(text)


def _join_text(*parts: object) -> str:
    return " ".join(str(part) for part in parts if part)


def _tokenize(text: str) -> frozenset[str]:
    raw_tokens = _TOKEN_PATTERN.findall(text.lower())
    tokens = {_stem(token) for token in raw_tokens if token not in _STOP_WORDS}
    tokens.update(_stem(f"{first}{second}") for first, second in pairwise(raw_tokens))
    return frozenset(token for token in tokens if token)


def _stem(token: str) -> str:
    for suffix in ("ingly", "edly", "ing", "ed", "es", "s"):
        if len(token) > len(suffix) + 2 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def _float_option(
    options: Mapping[str, object],
    key: str,
    default: float,
) -> float:
    value = options.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _int_option(
    options: Mapping[str, object],
    key: str,
    default: int,
) -> int:
    value = options.get(key)
    if isinstance(value, int):
        return value
    return default


def _requirement_source_ref(requirements: RequirementSet) -> SourceRef | None:
    if len(requirements.documents) == 1:
        return requirements.documents[0].source_ref
    return None
