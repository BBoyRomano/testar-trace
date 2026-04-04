from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import Iterable
from uuid import uuid4

from reqtrace.application.methods.common.candidate_utils import (
    WEAK_TOKENS,
    Candidate,
    best_match,
    build_candidates,
    classify_intent,
    expanded_tokens,
    filter_evidence_by_selected_runs,
    iter_selected_requirements,
    normalize_text,
    tokens,
)
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.result_metrics import build_input_summary, build_traceability_summary
from reqtrace.application.results import (
    CoverageSummary,
    CoverageVerdict,
    ExecutionInstance,
    ExecutionTrace,
    FlowCoverageResult,
    FlowStatus,
    FragmentTraceResult,
    MatchRole,
    RequirementResultStatus,
    RequirementTraceabilityResult,
    RunStatus,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
    TraceKind,
    TracePathItem,
    TracePathItemKind,
)
from reqtrace.domain.traceability.enums import CoverageStatus, CoverageSubjectType
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink


@dataclass(frozen=True, slots=True)
class _Anchor:
    fragment_id: str
    candidate: Candidate
    score: float
    matched_tokens: tuple[str, ...]
    positions: tuple[int, ...]
    intent: str


@dataclass(frozen=True, slots=True)
class _Placement:
    fragment_id: str
    candidate: Candidate
    position: int
    score: float
    matched_tokens: tuple[str, ...]
    intent: str


@dataclass(frozen=True, slots=True)
class _AlignedSolution:
    placements: tuple[_Placement, ...]
    score: float
    window: tuple[int, int]


@dataclass(frozen=True, slots=True)
class _CandidateExecution:
    flow_id: str
    flow_kind: TraceKind
    covered_fragment_ids: tuple[str, ...]
    representative_trace: ExecutionTrace
    quality: float
    core_positions: tuple[int, ...]
    display_range: tuple[int, int]


class FlowMatchMethod(TraceabilityMethod):
    name = "flow_match"
    method_name = "flow_match"

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        started_at = datetime.now(UTC)
        analysis_run_id = f"trace-run-{uuid4().hex}"
        requirements = list(
            iter_selected_requirements(request.requirements, request.selected_requirement_ids)
        )
        evidence = filter_evidence_by_selected_runs(
            request.evidence, request.selected_evidence_run_ids
        )

        states_by_id = {state.id: state for state in evidence.states}
        actions_by_id = {action.id: action for action in evidence.actions}
        transitions = sorted(
            evidence.transitions,
            key=lambda item: item.order_index if item.order_index is not None else 10**9,
        )
        transitions_by_order = {index: transition for index, transition in enumerate(transitions)}
        transition_index_by_id = {
            transition.id: index for index, transition in enumerate(transitions)
        }
        transition_indexes_by_state: dict[str, list[int]] = defaultdict(list)
        transition_indexes_by_action: dict[str, list[int]] = defaultdict(list)
        for index, transition in enumerate(transitions):
            transition_indexes_by_state[transition.from_state_id].append(index)
            if transition.to_state_id:
                transition_indexes_by_state[transition.to_state_id].append(index)
            transition_indexes_by_action[transition.action_id].append(index)

        candidates = build_candidates(evidence, request.selected_evidence_run_ids)
        results: list[RequirementTraceabilityResult] = []

        for requirement in requirements:
            fragments = list(request.requirements.fragments_for(requirement.id))
            preconditions, main_fragments, alt_groups, postconditions = _partition_fragments(
                fragments
            )

            main_sequence = [*preconditions, *main_fragments, *postconditions]
            main_instances = _find_flow_instances(
                flow_id=f"{requirement.id}:main",
                flow_kind=TraceKind.MAIN,
                display_fragments=main_sequence,
                coverage_fragments=main_fragments if main_fragments else main_sequence,
                candidates=candidates,
                transition_indexes_by_state=transition_indexes_by_state,
                transition_indexes_by_action=transition_indexes_by_action,
                transition_index_by_id=transition_index_by_id,
                states_by_id=states_by_id,
                actions_by_id=actions_by_id,
                transitions_by_order=transitions_by_order,
            )

            alt_instances: list[ExecutionInstance] = []
            alt_results: list[FlowCoverageResult] = []
            for branch_id, branch_fragments in alt_groups.items():
                alt_sequence = [*preconditions, *branch_fragments, *postconditions]
                instances = _find_flow_instances(
                    flow_id=branch_id,
                    flow_kind=TraceKind.ALTERNATIVE,
                    display_fragments=alt_sequence,
                    coverage_fragments=branch_fragments,
                    candidates=candidates,
                    transition_indexes_by_state=transition_indexes_by_state,
                    transition_indexes_by_action=transition_indexes_by_action,
                    transition_index_by_id=transition_index_by_id,
                    states_by_id=states_by_id,
                    actions_by_id=actions_by_id,
                    transitions_by_order=transitions_by_order,
                )
                alt_instances.extend(instances)
                alt_results.append(
                    _flow_result_from_instances(
                        branch_id,
                        TraceKind.ALTERNATIVE,
                        "Alternative flow",
                        branch_fragments,
                        instances,
                    )
                )

            instance_by_fragment: dict[str, list[ExecutionInstance]] = defaultdict(list)
            for instance in [*main_instances, *alt_instances]:
                for fragment_id in instance.covered_fragment_ids:
                    instance_by_fragment[fragment_id].append(instance)

            fragment_results: list[FragmentTraceResult] = []
            fragment_coverages: list[CoverageAssessment] = []
            trace_links: list[TraceLink] = []
            trace_evidence: list[TraceEvidence] = []
            all_local_scores: list[float] = []

            for fragment in fragments:
                match = best_match(fragment.text, candidates)
                local_score = float(match["score"]) if match else 0.0
                all_local_scores.append(local_score)
                instances = instance_by_fragment.get(fragment.id, [])
                status = (
                    FlowStatus.COVERED
                    if instances
                    else FlowStatus.PARTIAL
                    if local_score >= 0.30
                    else FlowStatus.NOT_COVERED
                )
                matched_state_ids = sorted(
                    {
                        state_id
                        for instance in instances
                        for state_id in _state_ids_from_instance(instance)
                    }
                )
                matched_transition_ids = sorted(
                    {
                        transition_id
                        for instance in instances
                        for transition_id in _transition_ids_from_instance(instance)
                    }
                )
                matched_action_ids = sorted(
                    {
                        action_id
                        for instance in instances
                        for action_id in _action_ids_from_instance(instance)
                    }
                )
                matched_element_ids = sorted(
                    {
                        element_id
                        for instance in instances
                        for element_id in _element_ids_from_instance(instance)
                    }
                )
                fragment_results.append(
                    FragmentTraceResult(
                        fragment_id=fragment.id,
                        fragment_kind=str(fragment.kind),
                        fragment_text=fragment.text,
                        status=status,
                        score=max(
                            [
                                local_score,
                                *[instance.representative_trace.score for instance in instances],
                            ],
                            default=0.0,
                        ),
                        matched_state_ids=matched_state_ids,
                        matched_transition_ids=matched_transition_ids,
                        matched_action_ids=matched_action_ids,
                        matched_element_ids=matched_element_ids,
                        metadata={
                            "branch_id": getattr(fragment, "branch_id", None),
                            "instance_ids": [instance.instance_id for instance in instances],
                            "step_mappings": [
                                mapping
                                for instance in instances
                                for mapping in instance.metadata.get("step_mappings", [])
                                if mapping.get("fragment_id") == fragment.id
                            ],
                        },
                    )
                )

                coverage_status = (
                    CoverageStatus.COVERED
                    if status == FlowStatus.COVERED
                    else CoverageStatus.PARTIALLY_COVERED
                    if status == FlowStatus.PARTIAL
                    else CoverageStatus.UNCOVERED
                )
                fragment_coverages.append(
                    CoverageAssessment(
                        id=f"coverage-{uuid4().hex}",
                        analysis_run_id=analysis_run_id,
                        subject_type=CoverageSubjectType.REQUIREMENT_FRAGMENT,
                        subject_id=fragment.id,
                        coverage_status=coverage_status,
                        coverage_ratio=1.0
                        if status == FlowStatus.COVERED
                        else 0.5
                        if status == FlowStatus.PARTIAL
                        else 0.0,
                        confidence_ratio=max(
                            [
                                local_score,
                                *[instance.representative_trace.score for instance in instances],
                            ],
                            default=0.0,
                        ),
                        supporting_run_count=0,
                        metadata={"method": self.method_name},
                    )
                )

                if match and local_score >= 0.30:
                    link = TraceLink(
                        id=f"link-{uuid4().hex}",
                        analysis_run_id=analysis_run_id,
                        requirement_fragment_id=fragment.id,
                        evidence_target_type=match["candidate"].target_type,
                        evidence_target_id=match["candidate"].target_id,
                        link_type="covers" if status == FlowStatus.COVERED else "supports",
                        score=local_score,
                        confidence_label="high"
                        if local_score >= 0.72
                        else "medium"
                        if local_score >= 0.48
                        else "low",
                        metadata={"method": self.method_name},
                    )
                    trace_links.append(link)
                    trace_evidence.append(
                        TraceEvidence(
                            id=f"evidence-{uuid4().hex}",
                            trace_link_id=link.id,
                            evidence_kind="transition_path" if instances else "text_match",
                            text_excerpt=match["candidate"].text[:240],
                            matched_tokens=match["matched_tokens"],
                            state_id=match["candidate"].state_id,
                            transition_id=match["candidate"].transition_id,
                            element_id=match["candidate"].element_id,
                            details={
                                "instance_ids": [instance.instance_id for instance in instances]
                            },
                        )
                    )

            main_result = (
                _flow_result_from_instances(
                    f"{requirement.id}:main",
                    TraceKind.MAIN,
                    "Main flow",
                    main_fragments if main_fragments else main_sequence,
                    main_instances,
                )
                if main_sequence
                else None
            )
            coverage = _coverage_from_flow_results(main_result, alt_results)
            if coverage.status == CoverageVerdict.NONE and any(
                item.status == FlowStatus.PARTIAL for item in fragment_results
            ):
                coverage.status = CoverageVerdict.PARTIAL
                if main_result and main_result.status == FlowStatus.NOT_COVERED:
                    coverage.main_flow_status = FlowStatus.PARTIAL
                    coverage.main_flow_ratio = max(
                        coverage.main_flow_ratio,
                        _partial_ratio(main_fragments or main_sequence, fragment_results),
                    )
                    coverage.confidence = max(
                        coverage.confidence,
                        sum(all_local_scores) / len(all_local_scores) if all_local_scores else 0.0,
                    )

            artifact_coverage = CoverageAssessment(
                id=f"coverage-{uuid4().hex}",
                analysis_run_id=analysis_run_id,
                subject_type=CoverageSubjectType.REQUIREMENT,
                subject_id=requirement.id,
                coverage_status=_artifact_status_from_verdict(coverage.status),
                coverage_ratio=max(coverage.main_flow_ratio, coverage.alt_flow_ratio),
                confidence_ratio=coverage.confidence,
                covered_fragment_count=sum(
                    1 for item in fragment_results if item.status == FlowStatus.COVERED
                ),
                total_fragment_count=len(fragment_results),
                supporting_run_count=0,
                metadata={"method": self.method_name, "alt_flow_ratio": coverage.alt_flow_ratio},
            )

            results.append(
                RequirementTraceabilityResult(
                    requirement_id=requirement.id,
                    requirement_title=requirement.title,
                    requirement_external_id=requirement.external_id,
                    status=RequirementResultStatus.DONE,
                    coverage=coverage,
                    main_flow_result=main_result,
                    alternative_flow_results=alt_results,
                    fragment_results=fragment_results,
                    execution_instances=[*main_instances, *alt_instances],
                    warnings=[],
                    artifact_coverage=artifact_coverage,
                    fragment_coverages=fragment_coverages,
                    trace_links=trace_links,
                    trace_evidence=trace_evidence,
                    metadata={
                        "method": self.method_name,
                        "precondition_count": len(preconditions),
                        "main_flow_count": len(main_fragments),
                        "postcondition_count": len(postconditions),
                        "average_local_score": sum(all_local_scores) / len(all_local_scores)
                        if all_local_scores
                        else 0.0,
                    },
                )
            )

        ended_at = datetime.now(UTC)
        summary = build_traceability_summary(
            results, input_summary=build_input_summary(request.requirements, request.evidence)
        )
        run = TraceabilityRun(
            id=analysis_run_id,
            method_name=self.method_name,
            status=RunStatus.COMPLETED,
            started_at=started_at,
            ended_at=ended_at,
            total_requirement_count=len(requirements),
            processed_requirement_count=len(results),
            failed_requirement_count=0,
            metadata={"method": self.method_name},
        )
        return TraceabilityResult(
            run=run,
            requirement_results=results,
            summary=summary,
            metadata={
                "method": self.method_name,
                "selected_evidence_run_count": len(request.selected_evidence_run_ids),
            },
        )


def _partition_fragments(fragments: list[object]):
    preconditions: list[object] = []
    main_flow: list[object] = []
    alt_groups: dict[str, list[object]] = defaultdict(list)
    postconditions: list[object] = []
    for fragment in fragments:
        kind_name = str(getattr(fragment, "kind", "")).lower()
        branch_id = getattr(fragment, "branch_id", None) or "alt-1"
        if "pre" in kind_name:
            preconditions.append(fragment)
        elif "post" in kind_name:
            postconditions.append(fragment)
        elif "alt" in kind_name or "alternative" in kind_name:
            alt_groups[branch_id].append(fragment)
        else:
            main_flow.append(fragment)
    return preconditions, main_flow, dict(alt_groups), postconditions


def _find_flow_instances(
    *,
    flow_id: str,
    flow_kind: TraceKind,
    display_fragments: list[object],
    coverage_fragments: list[object],
    candidates: list[Candidate],
    transition_indexes_by_state,
    transition_indexes_by_action,
    transition_index_by_id,
    states_by_id,
    actions_by_id,
    transitions_by_order,
) -> list[ExecutionInstance]:
    if not display_fragments:
        return []

    placements_per_fragment: list[list[_Placement]] = []
    for fragment in display_fragments:
        anchors = _anchors_for_fragment(
            fragment,
            candidates,
            transition_indexes_by_state=transition_indexes_by_state,
            transition_indexes_by_action=transition_indexes_by_action,
            transition_index_by_id=transition_index_by_id,
        )
        placements = _placements_for_fragment(anchors)
        if not placements:
            return []
        placements_per_fragment.append(placements)

    solutions = _enumerate_aligned_solutions(placements_per_fragment)
    if not solutions:
        return []

    coverage_fragment_ids = {fragment.id for fragment in coverage_fragments}
    proposals = [
        _solution_to_candidate_execution(
            solution,
            flow_id=flow_id,
            flow_kind=flow_kind,
            coverage_fragment_ids=coverage_fragment_ids,
            states_by_id=states_by_id,
            actions_by_id=actions_by_id,
            transitions_by_order=transitions_by_order,
        )
        for solution in solutions
    ]
    proposals = [proposal for proposal in proposals if proposal is not None]
    return _select_representative_instances(proposals)


def _anchors_for_fragment(
    fragment: object,
    candidates: list[Candidate],
    *,
    transition_indexes_by_state,
    transition_indexes_by_action,
    transition_index_by_id,
) -> list[_Anchor]:
    fragment_id = getattr(fragment, "id")
    fragment_text = getattr(fragment, "text", "")
    frag_tokens = tokens(fragment_text)
    frag_expanded = expanded_tokens(frag_tokens)
    phrase = normalize_text(fragment_text)
    intent = classify_intent(frag_tokens)
    kind_name = str(getattr(fragment, "kind", "")).lower()

    ranked: list[_Anchor] = []
    for candidate in candidates:
        token_overlap = frag_tokens & candidate.tokens
        expanded_overlap = frag_expanded & candidate.expanded_tokens
        informative_overlap = {token for token in expanded_overlap if token not in WEAK_TOKENS}
        raw_informative = {token for token in token_overlap if token not in WEAK_TOKENS}
        phrase_match = bool(phrase) and phrase in normalize_text(candidate.text)
        if not informative_overlap and not raw_informative and not phrase_match:
            continue

        score = 0.0
        if informative_overlap:
            score += min(0.44, 0.16 * len(informative_overlap))
        if raw_informative:
            score += min(0.18, 0.08 * len(raw_informative))
        if phrase_match:
            score += 0.12
        score += _target_type_bonus(intent=intent, kind_name=kind_name, candidate=candidate)
        score -= _documentation_penalty(candidate)
        score = max(0.0, min(score, 1.0))
        if score < 0.32:
            continue

        positions = _positions_for_candidate(
            candidate,
            transition_indexes_by_state=transition_indexes_by_state,
            transition_indexes_by_action=transition_indexes_by_action,
            transition_index_by_id=transition_index_by_id,
        )
        if not positions:
            continue
        ranked.append(
            _Anchor(
                fragment_id=fragment_id,
                candidate=candidate,
                score=score,
                matched_tokens=tuple(sorted(raw_informative or informative_overlap)),
                positions=tuple(sorted(set(positions))),
                intent=intent,
            )
        )

    ranked.sort(key=lambda item: (item.score, -len(item.positions)), reverse=True)
    return ranked[:12]


def _target_type_bonus(*, intent: str, kind_name: str, candidate: Candidate) -> float:
    bonus = 0.0
    target_type = candidate.target_type
    action_kind = (candidate.action_kind or "").lower()
    widget_kind = (candidate.widget_kind or "").lower()
    is_pre_or_post = "pre" in kind_name or "post" in kind_name

    if intent in {"click", "operation"}:
        if target_type == "transition":
            bonus += 0.20
        if target_type == "action":
            bonus += 0.18
        if action_kind in {"click", "navigate", "submit", "select"}:
            bonus += 0.10
        if widget_kind in {"button", "link"}:
            bonus += 0.08
    elif intent == "type":
        if target_type == "action":
            bonus += 0.20
        if target_type == "transition":
            bonus += 0.08
        if widget_kind in {"input", "select"}:
            bonus += 0.14
        if action_kind == "type":
            bonus += 0.12
    elif intent in {"display", "state"} or is_pre_or_post:
        if target_type == "application_state":
            bonus += 0.20
        if target_type == "transition":
            bonus += 0.10
        if target_type == "ui_element":
            bonus += 0.10
        if widget_kind == "content":
            bonus += 0.06
    else:
        if target_type == "transition":
            bonus += 0.12
        if target_type == "action":
            bonus += 0.10
        if target_type == "application_state":
            bonus += 0.08
        if target_type == "ui_element":
            bonus += 0.06
    return bonus


def _documentation_penalty(candidate: Candidate) -> float:
    lowered = normalize_text(candidate.text)
    penalty = 0.0
    if "use-cases" in lowered:
        penalty += 0.34
    if "application use-cases" in lowered:
        penalty += 0.30
    if "name of uc" in lowered or "context of use" in lowered:
        penalty += 0.26
    if "actor:" in lowered and "uc." in lowered:
        penalty += 0.22
    if candidate.target_type == "application_state" and lowered.count("uc.") >= 1:
        penalty += 0.18
    return penalty


def _positions_for_candidate(
    candidate: Candidate,
    *,
    transition_indexes_by_state,
    transition_indexes_by_action,
    transition_index_by_id,
) -> list[int]:
    if candidate.transition_id and candidate.transition_id in transition_index_by_id:
        return [transition_index_by_id[candidate.transition_id]]
    if candidate.action_id:
        action_positions = transition_indexes_by_action.get(candidate.action_id, [])
        if action_positions:
            return list(action_positions)
    if candidate.state_id:
        return list(transition_indexes_by_state.get(candidate.state_id, []))
    return []


def _placements_for_fragment(anchors: list[_Anchor]) -> list[_Placement]:
    placements: list[_Placement] = []
    seen: set[tuple[str, int]] = set()
    for anchor in anchors:
        for position in anchor.positions[:6]:
            key = (anchor.candidate.target_id, position)
            if key in seen:
                continue
            seen.add(key)
            placements.append(
                _Placement(
                    fragment_id=anchor.fragment_id,
                    candidate=anchor.candidate,
                    position=position,
                    score=anchor.score,
                    matched_tokens=anchor.matched_tokens,
                    intent=anchor.intent,
                )
            )
    placements.sort(key=lambda item: (item.position, -item.score, item.candidate.target_type))
    return placements[:32]


def _enumerate_aligned_solutions(
    placements_per_fragment: list[list[_Placement]],
) -> list[_AlignedSolution]:
    if not placements_per_fragment:
        return []

    windows: set[tuple[int, int]] = set()
    first_fragment = placements_per_fragment[0]
    unique_first_positions = sorted({placement.position for placement in first_fragment})
    for start_pos in unique_first_positions:
        end_pos = _minimal_end_for_start(start_pos, placements_per_fragment)
        if end_pos is not None:
            windows.add((start_pos, end_pos))

    solutions: list[_AlignedSolution] = []
    for start_pos, end_pos in sorted(
        windows, key=lambda item: (item[1] - item[0], item[0], item[1])
    ):
        best = _best_solution_in_window(start_pos, end_pos, placements_per_fragment)
        if best is not None:
            solutions.append(best)

    solutions.sort(key=lambda item: (_range_length(item.window), -item.score, item.window[0]))
    best_by_window: dict[tuple[int, int], _AlignedSolution] = {}
    for solution in solutions:
        current = best_by_window.get(solution.window)
        if current is None or solution.score > current.score:
            best_by_window[solution.window] = solution
    return list(best_by_window.values())[:120]


def _minimal_end_for_start(
    start_pos: int, placements_per_fragment: list[list[_Placement]]
) -> int | None:
    current = start_pos
    for idx, placements in enumerate(placements_per_fragment):
        valid_positions = [
            placement.position for placement in placements if placement.position >= current
        ]
        if idx == 0:
            valid_positions = [position for position in valid_positions if position == start_pos]
        if not valid_positions:
            return None
        current = min(valid_positions)
    return current


def _best_solution_in_window(
    start_pos: int, end_pos: int, placements_per_fragment: list[list[_Placement]]
) -> _AlignedSolution | None:
    filtered: list[list[_Placement]] = []
    for idx, placements in enumerate(placements_per_fragment):
        items = [
            placement for placement in placements if start_pos <= placement.position <= end_pos
        ]
        if idx == 0:
            items = [placement for placement in items if placement.position == start_pos]
        if not items:
            return None
        filtered.append(items)

    @lru_cache(maxsize=None)
    def best_from(
        fragment_index: int, last_pos: int, used_first_key: str | None = None
    ) -> tuple[float, tuple[_Placement, ...]] | None:
        placements = filtered[fragment_index]
        best_local: tuple[float, tuple[_Placement, ...]] | None = None
        for placement in placements:
            if placement.position < last_pos:
                continue
            score = placement.score
            if placement.position == last_pos and fragment_index > 0:
                score -= 0.02
            if fragment_index == len(filtered) - 1:
                candidate_result = (score, (placement,))
            else:
                tail = best_from(fragment_index + 1, placement.position)
                if tail is None:
                    continue
                candidate_result = (score + tail[0], (placement, *tail[1]))
            if best_local is None or _solution_rank(candidate_result) > _solution_rank(best_local):
                best_local = candidate_result
        return best_local

    best = best_from(0, start_pos)
    if best is None:
        return None
    return _AlignedSolution(
        placements=best[1], score=best[0] / max(len(best[1]), 1), window=(start_pos, end_pos)
    )


def _solution_rank(result: tuple[float, tuple[_Placement, ...]]) -> tuple[float, float]:
    score, placements = result
    compactness = 1.0 / max((placements[-1].position - placements[0].position + 1), 1)
    return score, compactness


def _solution_to_candidate_execution(
    solution: _AlignedSolution,
    *,
    flow_id: str,
    flow_kind: TraceKind,
    coverage_fragment_ids: set[str],
    states_by_id,
    actions_by_id,
    transitions_by_order,
) -> _CandidateExecution | None:
    covered_fragment_ids = tuple(
        sorted(
            {
                placement.fragment_id
                for placement in solution.placements
                if placement.fragment_id in coverage_fragment_ids
            }
        )
    )
    if covered_fragment_ids != tuple(sorted(coverage_fragment_ids)):
        return None
    trace = _build_display_trace(
        trace_kind=flow_kind,
        placements=solution.placements,
        states_by_id=states_by_id,
        actions_by_id=actions_by_id,
        transitions_by_order=transitions_by_order,
        window=solution.window,
    )
    quality = _execution_quality(solution, trace)
    if quality < 0.40:
        return None
    return _CandidateExecution(
        flow_id=flow_id,
        flow_kind=flow_kind,
        covered_fragment_ids=covered_fragment_ids,
        representative_trace=trace,
        quality=quality,
        core_positions=tuple(placement.position for placement in solution.placements),
        display_range=solution.window,
    )


def _execution_quality(solution: _AlignedSolution, trace: ExecutionTrace) -> float:
    matched_items = sum(1 for item in trace.path if item.match_role == MatchRole.MATCHED)
    total_items = len(trace.path)
    compactness = len(solution.placements) / max(_range_length(solution.window), 1)
    mapped_ratio = len(solution.placements) / max(total_items, 1)
    return min(
        1.0, 0.55 * solution.score + 0.25 * compactness + 0.20 * mapped_ratio + 0.02 * matched_items
    )


def _select_representative_instances(
    proposals: list[_CandidateExecution],
) -> list[ExecutionInstance]:
    ordered = sorted(
        proposals,
        key=lambda proposal: (
            _range_length(proposal.display_range),
            -proposal.quality,
            proposal.display_range[0],
        ),
    )
    groups: list[dict[str, object]] = []
    for proposal in ordered:
        group = next(
            (item for item in groups if _same_execution_instance(proposal, item["proposal"])), None
        )
        if group is None:
            groups.append({"proposal": proposal, "omitted": []})
            continue
        current: _CandidateExecution = group["proposal"]
        if _prefer_candidate(proposal, current):
            group["omitted"].append(current.representative_trace.trace_id)
            group["proposal"] = proposal
        else:
            group["omitted"].append(proposal.representative_trace.trace_id)

    instances: list[ExecutionInstance] = []
    for index, group in enumerate(groups[:20], start=1):
        proposal = group["proposal"]
        omitted_trace_ids: list[str] = group["omitted"]
        step_mappings = proposal.representative_trace.metadata.get("step_mappings", [])
        instances.append(
            ExecutionInstance(
                flow_id=proposal.flow_id,
                flow_kind=proposal.flow_kind,
                covered_fragment_ids=list(proposal.covered_fragment_ids),
                representative_trace=proposal.representative_trace,
                overlapping_trace_count=1 + len(omitted_trace_ids),
                omitted_trace_ids=omitted_trace_ids,
                metadata={
                    "instance_index": index,
                    "matched_core_transition_ids": [
                        item.transition_id
                        for item in proposal.representative_trace.path
                        if item.kind == TracePathItemKind.TRANSITION
                        and item.match_role == MatchRole.MATCHED
                    ],
                    "matched_core_state_ids": [
                        item.state_id
                        for item in proposal.representative_trace.path
                        if item.kind == TracePathItemKind.STATE
                        and item.match_role == MatchRole.MATCHED
                        and item.state_id
                    ],
                    "display_range": proposal.display_range,
                    "quality": proposal.quality,
                    "step_mappings": step_mappings,
                },
            )
        )
    return instances


def _same_execution_instance(left: _CandidateExecution, right: _CandidateExecution) -> bool:
    if left.flow_id != right.flow_id:
        return False
    core_overlap = _jaccard(left.core_positions, right.core_positions)
    range_overlap = _range_overlap(left.display_range, right.display_range)
    return core_overlap >= 0.60 or range_overlap >= 0.90


def _prefer_candidate(candidate: _CandidateExecution, current: _CandidateExecution) -> bool:
    candidate_len = _range_length(candidate.display_range)
    current_len = _range_length(current.display_range)
    if candidate_len < current_len and candidate.quality >= current.quality * 0.92:
        return True
    if candidate_len == current_len and candidate.quality > current.quality:
        return True
    return False


def _build_display_trace(
    *,
    trace_kind: TraceKind,
    placements: tuple[_Placement, ...],
    states_by_id,
    actions_by_id,
    transitions_by_order,
    window: tuple[int, int],
) -> ExecutionTrace:
    start, end = window
    matched_fragment_ids_by_state: dict[str, list[str]] = defaultdict(list)
    matched_fragment_ids_by_transition: dict[str, list[str]] = defaultdict(list)
    matched_element_ids_by_fragment: dict[str, set[str]] = defaultdict(set)
    step_mappings: list[dict[str, object]] = []

    for placement in placements:
        fragment_id = placement.fragment_id
        candidate = placement.candidate
        position = placement.position
        transition = transitions_by_order[position]
        mapping = {
            "fragment_id": fragment_id,
            "position": position,
            "candidate_type": candidate.target_type,
            "candidate_id": candidate.target_id,
            "state_id": candidate.state_id,
            "transition_id": candidate.transition_id,
            "action_id": candidate.action_id,
            "element_id": candidate.element_id,
            "matched_tokens": list(placement.matched_tokens),
            "score": placement.score,
        }
        step_mappings.append(mapping)
        matched_fragment_ids_by_transition[transition.id].append(fragment_id)
        matched_fragment_ids_by_state[transition.from_state_id].append(fragment_id)
        if transition.to_state_id:
            matched_fragment_ids_by_state[transition.to_state_id].append(fragment_id)
        if candidate.state_id:
            matched_fragment_ids_by_state[candidate.state_id].append(fragment_id)
        if candidate.element_id:
            matched_element_ids_by_fragment[fragment_id].add(candidate.element_id)

    path: list[TracePathItem] = []
    for index in range(start, end + 1):
        transition = transitions_by_order[index]
        from_state = states_by_id.get(transition.from_state_id)
        to_state = states_by_id.get(transition.to_state_id) if transition.to_state_id else None
        if from_state is not None and (not path or path[-1].state_id != from_state.id):
            path.append(
                TracePathItem(
                    kind=TracePathItemKind.STATE,
                    item_id=from_state.id,
                    state_id=from_state.id,
                    label=from_state.title or from_state.name or from_state.id,
                    matched_fragment_ids=sorted(
                        set(matched_fragment_ids_by_state.get(from_state.id, []))
                    ),
                    match_role=MatchRole.MATCHED
                    if matched_fragment_ids_by_state.get(from_state.id)
                    else MatchRole.INTERMEDIATE,
                )
            )
        action = actions_by_id.get(transition.action_id)
        action_label = action.description if action and action.description else transition.id
        path.append(
            TracePathItem(
                kind=TracePathItemKind.TRANSITION,
                item_id=transition.id,
                transition_id=transition.id,
                state_id=transition.to_state_id or transition.from_state_id,
                action_id=transition.action_id,
                label=action_label,
                matched_fragment_ids=sorted(
                    set(matched_fragment_ids_by_transition.get(transition.id, []))
                ),
                match_role=MatchRole.MATCHED
                if matched_fragment_ids_by_transition.get(transition.id)
                else MatchRole.INTERMEDIATE,
                metadata={
                    "from_state_id": transition.from_state_id,
                    "to_state_id": transition.to_state_id,
                },
            )
        )
        if to_state is not None:
            path.append(
                TracePathItem(
                    kind=TracePathItemKind.STATE,
                    item_id=to_state.id,
                    state_id=to_state.id,
                    label=to_state.title or to_state.name or to_state.id,
                    matched_fragment_ids=sorted(
                        set(matched_fragment_ids_by_state.get(to_state.id, []))
                    ),
                    match_role=MatchRole.MATCHED
                    if matched_fragment_ids_by_state.get(to_state.id)
                    else MatchRole.INTERMEDIATE,
                )
            )

    matched_fragment_ids = sorted(
        {fragment_id for item in path for fragment_id in item.matched_fragment_ids}
    )
    match_ratio = sum(1 for item in path if item.match_role == MatchRole.MATCHED) / max(
        len(path), 1
    )
    return ExecutionTrace(
        trace_kind=trace_kind,
        score=min(1.0, max(0.0, 0.35 + 0.65 * match_ratio)),
        path=path,
        matched_fragment_ids=matched_fragment_ids,
        metadata={
            "range": (start, end),
            "matched_element_ids_by_fragment": {
                fragment_id: sorted(element_ids)
                for fragment_id, element_ids in matched_element_ids_by_fragment.items()
            },
            "step_mappings": step_mappings,
        },
    )


def _flow_result_from_instances(
    flow_id: str,
    flow_kind: TraceKind,
    name: str,
    fragments: list[object],
    instances: list[ExecutionInstance],
) -> FlowCoverageResult:
    fragment_ids = [getattr(fragment, "id") for fragment in fragments]
    covered_fragment_ids = sorted(
        {fragment_id for instance in instances for fragment_id in instance.covered_fragment_ids}
    )
    ratio = len(covered_fragment_ids) / len(fragment_ids) if fragment_ids else 0.0
    if not fragments:
        status = FlowStatus.NONE_DEFINED
    elif instances and ratio >= 1.0:
        status = FlowStatus.COVERED
    elif covered_fragment_ids:
        status = FlowStatus.PARTIAL
    else:
        status = FlowStatus.NOT_COVERED
    confidence = max((instance.representative_trace.score for instance in instances), default=0.0)
    return FlowCoverageResult(
        flow_id=flow_id,
        flow_kind=flow_kind,
        name=name,
        status=status,
        ratio=ratio,
        confidence=confidence,
        fragment_ids=fragment_ids,
        covered_fragment_ids=covered_fragment_ids,
        instance_ids=[instance.instance_id for instance in instances],
    )


def _coverage_from_flow_results(
    main_result: FlowCoverageResult | None, alt_results: list[FlowCoverageResult]
) -> CoverageSummary:
    main_ratio = main_result.ratio if main_result else 0.0
    alt_defined = [item for item in alt_results if item.status != FlowStatus.NONE_DEFINED]
    alt_ratio = sum(item.ratio for item in alt_defined) / len(alt_defined) if alt_defined else 0.0
    if not alt_results:
        alt_status = FlowStatus.NONE_DEFINED
    elif alt_defined and all(item.status == FlowStatus.COVERED for item in alt_defined):
        alt_status = FlowStatus.COVERED
    elif any(item.covered_fragment_ids for item in alt_results):
        alt_status = FlowStatus.PARTIAL
    else:
        alt_status = FlowStatus.NOT_COVERED
    confidence_values = [
        item.confidence for item in [main_result, *alt_results] if item is not None
    ]
    confidence = max(confidence_values, default=0.0)
    if (
        main_result
        and main_result.status == FlowStatus.COVERED
        and (not alt_defined or all(item.status == FlowStatus.COVERED for item in alt_defined))
    ):
        verdict = CoverageVerdict.FULL
    elif main_result and main_result.status == FlowStatus.COVERED:
        verdict = CoverageVerdict.MAIN_ONLY
    elif any(item.status == FlowStatus.COVERED for item in alt_results):
        verdict = CoverageVerdict.ALT_ONLY
    elif (main_result and main_result.covered_fragment_ids) or any(
        item.covered_fragment_ids for item in alt_results
    ):
        verdict = CoverageVerdict.PARTIAL
    else:
        verdict = CoverageVerdict.NONE
    return CoverageSummary(
        status=verdict,
        main_flow_status=main_result.status if main_result else FlowStatus.NOT_COVERED,
        alt_flow_status=alt_status,
        main_flow_ratio=main_ratio,
        alt_flow_ratio=alt_ratio,
        confidence=confidence,
    )


def _partial_ratio(fragments: list[object], fragment_results: list[FragmentTraceResult]) -> float:
    if not fragments:
        return 0.0
    fragment_ids = {fragment.id for fragment in fragments}
    covered = sum(
        1
        for result in fragment_results
        if result.fragment_id in fragment_ids and result.status != FlowStatus.NOT_COVERED
    )
    return covered / len(fragment_ids)


def _artifact_status_from_verdict(verdict: CoverageVerdict) -> CoverageStatus:
    if verdict == CoverageVerdict.FULL:
        return CoverageStatus.COVERED
    if verdict in {CoverageVerdict.MAIN_ONLY, CoverageVerdict.ALT_ONLY, CoverageVerdict.PARTIAL}:
        return CoverageStatus.PARTIALLY_COVERED
    if verdict == CoverageVerdict.UNCERTAIN:
        return CoverageStatus.UNCERTAIN
    return CoverageStatus.UNCOVERED


def _jaccard(left: Iterable[int], right: Iterable[int]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    if not union:
        return 0.0
    return len(left_set & right_set) / len(union)


def _range_overlap(a: tuple[int, int], b: tuple[int, int]) -> float:
    left = max(a[0], b[0])
    right = min(a[1], b[1])
    if left > right:
        return 0.0
    overlap = right - left + 1
    shortest = min(_range_length(a), _range_length(b))
    return overlap / shortest if shortest > 0 else 0.0


def _range_length(rng: tuple[int, int]) -> int:
    return rng[1] - rng[0] + 1


def _state_ids_from_instance(instance: ExecutionInstance | None) -> list[str]:
    if instance is None:
        return []
    return [item.state_id for item in instance.representative_trace.path if item.state_id]


def _transition_ids_from_instance(instance: ExecutionInstance | None) -> list[str]:
    if instance is None:
        return []
    return [item.transition_id for item in instance.representative_trace.path if item.transition_id]


def _action_ids_from_instance(instance: ExecutionInstance | None) -> list[str]:
    if instance is None:
        return []
    return [item.action_id for item in instance.representative_trace.path if item.action_id]


def _element_ids_from_instance(instance: ExecutionInstance | None) -> list[str]:
    if instance is None:
        return []
    element_ids: list[str] = []
    by_fragment = instance.representative_trace.metadata.get("matched_element_ids_by_fragment", {})
    for values in by_fragment.values():
        element_ids.extend(values)
    return element_ids
