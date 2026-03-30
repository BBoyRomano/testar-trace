
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable
from uuid import uuid4

from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.results import (
    EvidenceSnapshot,
    RequirementResultStatus,
    RequirementSnapshot,
    TraceabilityRequest,
    TraceabilityResult,
    TraceabilityRun,
    RequirementTraceabilityResult,
    TraceabilitySummary,
)
from reqtrace.domain.evidence.models import Action, ApplicationState, Transition, UIElement
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink
from reqtrace.domain.traceability.enums import CoverageStatus, CoverageSubjectType


_WEAK_TOKENS = {
    "a",
    "an",
    "and",
    "application",
    "about",
    "at",
    "by",
    "for",
    "from",
    "in",
    "information",
    "is",
    "of",
    "on",
    "page",
    "real",
    "system",
    "that",
    "the",
    "this",
    "to",
    "university",
    "user",
    "with",
}

_OPERATION_TOKENS = {"restore", "restoration", "export", "import", "database", "backup", "db", "recover", "recovery"}
_DISPLAY_TOKENS = {"display", "displays", "show", "shows", "present", "presents", "list", "lists", "information", "abilities"}

_EXPANSIONS = {
    "restoration": {"restore", "restoration", "recover", "recovery"},
    "restore": {"restore", "restoration", "recover", "recovery"},
    "recover": {"restore", "restoration", "recover", "recovery"},
    "recovery": {"restore", "restoration", "recover", "recovery"},
    "database": {"database", "db", "backup", "data"},
    "db": {"database", "db", "backup", "data"},
    "export": {"export", "download", "save"},
    "import": {"import", "upload", "load"},
    "login": {"login", "log", "sign", "signin", "signon"},
    "logout": {"logout", "log", "signout"},
}

_TAG_KIND = {
    "a": "link",
    "button": "button",
    "input": "input",
    "select": "select",
    "textarea": "input",
    "h1": "content",
    "h2": "content",
    "h3": "content",
    "div": "content",
    "p": "content",
    "span": "content",
}

@dataclass(slots=True)
class _Candidate:
    target_type: str
    target_id: str
    text: str
    tokens: set[str]
    expanded_tokens: set[str]
    state_id: str | None = None
    transition_id: str | None = None
    element_id: str | None = None
    action_id: str | None = None
    widget_kind: str | None = None
    action_kind: str | None = None


class HeuristicMethod(TraceabilityMethod):
    name = "heuristic"
    method_name = "heuristic"

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        started_at = datetime.now(UTC)
        analysis_run_id = f"trace-run-{uuid4().hex}"

        requirements = list(_iter_selected_requirements(request.requirements, request.selected_requirement_ids))
        candidates = _build_candidates(request.evidence, request.selected_evidence_run_ids)

        requirement_results: list[RequirementTraceabilityResult] = []

        for requirement in requirements:
            fragments = list(request.requirements.fragments_for(requirement.id))
            fragment_coverages: list[CoverageAssessment] = []
            trace_links: list[TraceLink] = []
            trace_evidence: list[TraceEvidence] = []
            warnings: list[str] = []
            matched_fragment_count = 0
            confidences: list[float] = []

            for fragment in fragments:
                match = _best_match(fragment.text, candidates)

                if match is None:
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
                            metadata={"method": self.method_name, "best_target_type": None},
                        )
                    )
                    continue

                matched_fragment_count += 1
                confidences.append(match["score"])

                if match["score"] >= 0.72:
                    coverage_status = CoverageStatus.COVERED
                    link_type = "covers"
                    confidence_label = "high"
                elif match["score"] >= 0.48:
                    coverage_status = CoverageStatus.PARTIALLY_COVERED
                    link_type = "partially_covers"
                    confidence_label = "medium"
                elif match["score"] >= 0.30:
                    coverage_status = CoverageStatus.UNCERTAIN
                    link_type = "supports"
                    confidence_label = "low"
                    warnings.append(f"Uncertain match for fragment {fragment.id}")
                else:
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
                            metadata={"method": self.method_name, "best_target_type": None},
                        )
                    )
                    continue

                link = TraceLink(
                    id=f"link-{uuid4().hex}",
                    analysis_run_id=analysis_run_id,
                    requirement_fragment_id=fragment.id,
                    evidence_target_type=match["candidate"].target_type,
                    evidence_target_id=match["candidate"].target_id,
                    link_type=link_type,
                    score=float(match["score"]),
                    confidence_label=confidence_label,
                    metadata={"method": self.method_name, "intent": match["intent"]},
                )
                trace_links.append(link)

                trace_evidence.append(
                    TraceEvidence(
                        id=f"evidence-{uuid4().hex}",
                        trace_link_id=link.id,
                        evidence_kind="text_match",
                        text_excerpt=match["candidate"].text[:240],
                        matched_tokens=sorted(match["matched_tokens"]),
                        run_id=None,
                        state_id=match["candidate"].state_id,
                        transition_id=match["candidate"].transition_id,
                        element_id=match["candidate"].element_id,
                        details={
                            "method": self.method_name,
                            "candidate_type": match["candidate"].target_type,
                            "widget_kind": match["candidate"].widget_kind,
                            "action_kind": match["candidate"].action_kind,
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
                        confidence_ratio=float(match["score"]),
                        covered_fragment_count=None,
                        total_fragment_count=None,
                        supporting_run_count=0,
                        metadata={
                            "method": self.method_name,
                            "best_target_type": match["candidate"].target_type,
                        },
                    )
                )

            artifact_coverage = _aggregate_requirement_coverage(
                analysis_run_id=analysis_run_id,
                requirement_id=requirement.id,
                total_fragment_count=len(fragments),
                matched_fragment_count=matched_fragment_count,
                confidences=confidences,
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
                    metadata={"method": self.method_name, "fragment_count": len(fragments)},
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
            processed_requirement_count=len(requirements),
            failed_requirement_count=0,
            metadata={"method": self.method_name, "evidence_run_count": len(request.evidence.runs)},
        )
        return TraceabilityResult(
            run=run,
            requirement_results=requirement_results,
            summary=summary,
            warnings=[],
            metadata={"method": self.method_name},
        )


def _iter_selected_requirements(snapshot: RequirementSnapshot, selected_ids: Iterable[str] | None):
    if not selected_ids:
        yield from snapshot.iter_requirements()
        return
    selected = set(selected_ids)
    for requirement in snapshot.iter_requirements():
        if requirement.id in selected:
            yield requirement


def _build_candidates(snapshot: EvidenceSnapshot, selected_run_ids: Iterable[str] | None) -> list[_Candidate]:
    # Current evidence objects are not run-scoped strongly enough for deep filtering; keep all and let later
    # refinements add stricter run-level filtering if needed.
    selected_run_ids = set(selected_run_ids or [])

    elements_by_state: dict[str, list[UIElement]] = {}
    for element in snapshot.elements:
        elements_by_state.setdefault(element.state_id, []).append(element)

    states_by_id = {state.id: state for state in snapshot.states}
    actions_by_id = {action.id: action for action in snapshot.actions}

    candidates: list[_Candidate] = []

    for state in snapshot.states:
        related_elements = elements_by_state.get(state.id, [])
        content_texts = []
        for element in related_elements:
            if element.text:
                content_texts.append(element.text)
            elif element.title:
                content_texts.append(element.title)
        aggregate = " | ".join(dict.fromkeys([part for part in [state.title, state.url, *content_texts[:8]] if part]))
        if aggregate:
            candidates.append(
                _Candidate(
                    target_type="application_state",
                    target_id=state.id,
                    text=aggregate,
                    tokens=_tokens(aggregate),
                    expanded_tokens=_expanded_tokens(_tokens(aggregate)),
                    state_id=state.id,
                    widget_kind="content",
                )
            )

    for element in snapshot.elements:
        attr_name = element.attributes.get("name") if element.attributes else None
        attr_value = element.attributes.get("value") if element.attributes else None
        element_text = " | ".join(
            part
            for part in [
                element.text,
                element.title,
                element.href,
                element.tag_name,
                element.role,
                element.css_selector,
                element.path,
                attr_name,
                attr_value,
            ]
            if part
        )
        if not element_text:
            continue
        tag_name = (element.tag_name or "").lower() if element.tag_name else None
        widget_kind = _TAG_KIND.get(tag_name) or (element.role.lower() if element.role else None)
        candidates.append(
            _Candidate(
                target_type="ui_element",
                target_id=element.id,
                text=f"{element_text} | {tag_name or 'element'}",
                tokens=_tokens(element_text),
                expanded_tokens=_expanded_tokens(_tokens(element_text)),
                state_id=element.state_id,
                element_id=element.id,
                widget_kind=widget_kind,
            )
        )

    for action in snapshot.actions:
        text = " | ".join(part for part in [action.description] if part)
        if not text:
            continue
        action_kind = str(action.kind).lower().split(".")[-1] if getattr(action, "kind", None) is not None else None
        target_element = next((e for e in snapshot.elements if e.id == action.target_element_id), None)
        widget_kind = None
        if target_element is not None:
            widget_kind = _TAG_KIND.get((target_element.tag_name or "").lower()) or (
                target_element.role.lower() if target_element.role else None
            )
        candidates.append(
            _Candidate(
                target_type="action",
                target_id=action.id,
                text=text,
                tokens=_tokens(text),
                expanded_tokens=_expanded_tokens(_tokens(text)),
                state_id=action.source_state_id,
                element_id=action.target_element_id,
                action_id=action.id,
                widget_kind=widget_kind,
                action_kind=action_kind,
            )
        )

    for transition in snapshot.transitions:
        parts: list[str] = []
        from_state = states_by_id.get(transition.from_state_id)
        to_state = states_by_id.get(transition.to_state_id) if transition.to_state_id else None
        action = actions_by_id.get(transition.action_id)
        if from_state and from_state.title:
            parts.append(f"from {from_state.title}")
        if action and action.description:
            parts.append(action.description)
        if to_state and to_state.title:
            parts.append(f"to {to_state.title}")
        if parts:
            text = " | ".join(parts)
            action_kind = str(action.kind).lower().split(".")[-1] if action and getattr(action, "kind", None) is not None else None
            candidates.append(
                _Candidate(
                    target_type="transition",
                    target_id=transition.id,
                    text=text,
                    tokens=_tokens(text),
                    expanded_tokens=_expanded_tokens(_tokens(text)),
                    state_id=transition.to_state_id or transition.from_state_id,
                    transition_id=transition.id,
                    action_id=transition.action_id,
                    action_kind=action_kind,
                )
            )

    return candidates


def _best_match(fragment_text: str, candidates: list[_Candidate]):
    frag_tokens = _tokens(fragment_text)
    if not frag_tokens:
        return None
    frag_expanded = _expanded_tokens(frag_tokens)
    intent = _classify_intent(frag_tokens)
    phrase = _normalize_text(fragment_text)

    best = None
    for candidate in candidates:
        token_overlap = frag_tokens & candidate.tokens
        expanded_overlap = frag_expanded & candidate.expanded_tokens

        informative_overlap = {t for t in expanded_overlap if t not in _WEAK_TOKENS}
        raw_informative = {t for t in token_overlap if t not in _WEAK_TOKENS}

        phrase_match = phrase and (phrase in _normalize_text(candidate.text))
        if not informative_overlap and not raw_informative and not phrase_match:
            continue

        score = 0.0

        # Stronger weighting for informative lexical evidence.
        if informative_overlap:
            score += min(0.55, 0.18 * len(informative_overlap))
        if raw_informative:
            score += min(0.20, 0.10 * len(raw_informative))

        # Light fuzzy/substring support.
        norm_candidate = _normalize_text(candidate.text)
        frag_terms = sorted(t for t in frag_expanded if t not in _WEAK_TOKENS)
        if phrase_match:
            score += 0.18
        else:
            for term in frag_terms:
                if term and term in norm_candidate:
                    score += 0.05
            score = min(score, 1.0)

        # Intent-aware candidate preferences.
        if intent == "operation":
            if candidate.target_type == "action":
                score += 0.18
            if candidate.target_type == "transition":
                score += 0.12
            if candidate.widget_kind in {"button", "link"}:
                score += 0.15
            if candidate.action_kind in {"navigate", "click"}:
                score += 0.10
        elif intent in {"display", "state"}:
            if candidate.target_type == "application_state":
                score += 0.18
            if candidate.widget_kind == "content":
                score += 0.12
            if candidate.target_type == "ui_element":
                score += 0.06
        elif intent == "click":
            if candidate.action_kind == "click":
                score += 0.18
            if candidate.widget_kind in {"button", "link"}:
                score += 0.12
        elif intent == "type":
            if candidate.widget_kind in {"input", "select"}:
                score += 0.18
            if candidate.action_kind == "type":
                score += 0.12

        # Penalise generic site boilerplate.
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

        if best is None or score > best["score"]:
            best = {
                "candidate": candidate,
                "score": score,
                "matched_tokens": sorted(raw_informative or informative_overlap),
                "intent": intent,
            }

    return best


def _aggregate_requirement_coverage(
    *,
    analysis_run_id: str,
    requirement_id: str,
    total_fragment_count: int,
    matched_fragment_count: int,
    confidences: list[float],
) -> CoverageAssessment:
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    matched_ratio = matched_fragment_count / total_fragment_count if total_fragment_count else 0.0

    if matched_ratio >= 0.8 and average_confidence >= 0.72:
        status = CoverageStatus.COVERED
        coverage_ratio = matched_ratio
        covered_fragment_count = matched_fragment_count
    elif matched_ratio >= 0.35 and average_confidence >= 0.48:
        status = CoverageStatus.PARTIALLY_COVERED
        coverage_ratio = matched_ratio
        covered_fragment_count = matched_fragment_count
    elif matched_fragment_count > 0 and average_confidence >= 0.30:
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
        total_fragment_count=total_fragment_count,
        supporting_run_count=0,
        metadata={"method": "heuristic"},
    )


def _build_summary(results: list[RequirementTraceabilityResult]) -> TraceabilitySummary:
    requirement_count = len(results)
    analyzed_requirement_count = sum(1 for result in results if result.status == RequirementResultStatus.DONE)
    failed_requirement_count = sum(1 for result in results if result.status != RequirementResultStatus.DONE)
    covered_requirement_count = sum(1 for result in results if result.artifact_coverage.coverage_status == CoverageStatus.COVERED)
    partially_covered_requirement_count = sum(
        1 for result in results if result.artifact_coverage.coverage_status == CoverageStatus.PARTIALLY_COVERED
    )
    uncovered_requirement_count = sum(
        1 for result in results if result.artifact_coverage.coverage_status == CoverageStatus.UNCOVERED
    )
    uncertain_requirement_count = sum(
        1 for result in results if result.artifact_coverage.coverage_status == CoverageStatus.UNCERTAIN
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


def _normalize_text(text: str | None) -> str:
    return " ".join(_tokens(text or ""))


def _tokens(text: str) -> set[str]:
    raw = re.findall(r"[A-Za-z0-9]+", text.lower())
    tokens: set[str] = set()
    for token in raw:
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("tion") and len(token) > 5:
            # keep noun stem alongside the original form
            tokens.add(token[:-4])
        elif token.endswith("ing") and len(token) > 5:
            tokens.add(token[:-3])
        elif token.endswith("ed") and len(token) > 4:
            tokens.add(token[:-2])
        elif token.endswith("s") and len(token) > 3:
            tokens.add(token[:-1])
        tokens.add(token)
    return tokens


def _expanded_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        expanded.update(_EXPANSIONS.get(token, set()))
    return expanded


def _classify_intent(tokens: set[str]) -> str:
    if tokens & {"click", "press", "select", "choose"}:
        return "click"
    if tokens & {"enter", "type", "fill", "input"}:
        return "type"
    if tokens & {"open", "go", "goto", "redirect", "navigate"}:
        return "navigate"
    if tokens & _OPERATION_TOKENS:
        return "operation"
    if tokens & _DISPLAY_TOKENS:
        return "display"
    if tokens & {"screen", "page", "state", "view"}:
        return "state"
    return "generic"
