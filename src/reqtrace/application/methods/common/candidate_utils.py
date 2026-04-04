"""Candidate-retrieval and lexical matching helpers shared by trace methods."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from reqtrace.application.request_models import EvidenceSnapshot, RequirementSnapshot
from reqtrace.domain.evidence.models import UIElement

WEAK_TOKENS = {
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
_OPERATION_TOKENS = {
    "restore",
    "restoration",
    "export",
    "import",
    "database",
    "backup",
    "db",
    "recover",
    "recovery",
}
_DISPLAY_TOKENS = {
    "display",
    "displays",
    "show",
    "shows",
    "present",
    "presents",
    "list",
    "lists",
    "information",
    "abilities",
}
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
class Candidate:
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


def iter_selected_requirements(
    snapshot: RequirementSnapshot, selected_ids: Iterable[str] | None
):
    if not selected_ids:
        yield from snapshot.iter_requirements()
        return
    selected = set(selected_ids)
    for requirement in snapshot.iter_requirements():
        if requirement.id in selected:
            yield requirement


def build_candidates(
    snapshot: EvidenceSnapshot, selected_run_ids: Iterable[str] | None
) -> list[Candidate]:
    snapshot = filter_evidence_by_selected_runs(snapshot, selected_run_ids)
    elements_by_state: dict[str, list[UIElement]] = {}
    for element in snapshot.elements:
        elements_by_state.setdefault(element.state_id, []).append(element)
    states_by_id = {state.id: state for state in snapshot.states}
    actions_by_id = {action.id: action for action in snapshot.actions}
    candidates: list[Candidate] = []

    for state in snapshot.states:
        related_elements = elements_by_state.get(state.id, [])
        content_texts = []
        for element in related_elements:
            element_primary_text = element_attribute(element, "text") or element_attribute(
                element, "title"
            )
            if element_primary_text:
                content_texts.append(element_primary_text)
        aggregate = " | ".join(
            dict.fromkeys(
                [part for part in [state.title, state.name, state.url, *content_texts[:8]] if part]
            )
        )
        if aggregate:
            candidates.append(
                Candidate(
                    "application_state",
                    state.id,
                    aggregate,
                    tokens(aggregate),
                    expanded_tokens(tokens(aggregate)),
                    state_id=state.id,
                    widget_kind="content",
                )
            )

    for element in snapshot.elements:
        parts = element_candidate_parts(element)
        if not parts:
            continue
        element_text = " | ".join(parts)
        tag_name = (element.tag_name or "").lower() if element.tag_name else None
        widget_kind = _TAG_KIND.get(tag_name) or (element.role.lower() if element.role else None)
        candidates.append(
            Candidate(
                "ui_element",
                element.id,
                f"{element_text} | {tag_name or 'element'}",
                tokens(element_text),
                expanded_tokens(tokens(element_text)),
                state_id=element.state_id,
                element_id=element.id,
                widget_kind=widget_kind,
            )
        )

    for action in snapshot.actions:
        action_parts = [
            action.description,
            action_attribute(action, "name"),
            action_attribute(action, "value"),
            action_attribute(action, "text"),
            action_attribute(action, "title"),
        ]
        text = " | ".join(part for part in action_parts if part)
        if not text:
            continue
        action_kind = (
            str(action.kind).lower().split(".")[-1]
            if getattr(action, "kind", None) is not None
            else None
        )
        target_element = next(
            (item for item in snapshot.elements if item.id == action.target_element_id), None
        )
        widget_kind = None
        if target_element is not None:
            widget_kind = _TAG_KIND.get((target_element.tag_name or "").lower()) or (
                target_element.role.lower() if target_element.role else None
            )
        candidates.append(
            Candidate(
                "action",
                action.id,
                text,
                tokens(text),
                expanded_tokens(tokens(text)),
                state_id=action.source_state_id,
                element_id=action.target_element_id,
                action_id=action.id,
                widget_kind=widget_kind,
                action_kind=action_kind,
            )
        )

    for transition in snapshot.transitions:
        parts = []
        from_state = states_by_id.get(transition.from_state_id)
        to_state = states_by_id.get(transition.to_state_id) if transition.to_state_id else None
        action = actions_by_id.get(transition.action_id)
        if from_state and from_state.title:
            parts.append(f"from {from_state.title}")
        if action and action.description:
            parts.append(action.description)
        if to_state and to_state.title:
            parts.append(f"to {to_state.title}")
        if not parts:
            continue
        text = " | ".join(parts)
        action_kind = (
            str(action.kind).lower().split(".")[-1]
            if action and getattr(action, "kind", None) is not None
            else None
        )
        candidates.append(
            Candidate(
                "transition",
                transition.id,
                text,
                tokens(text),
                expanded_tokens(tokens(text)),
                state_id=transition.to_state_id or transition.from_state_id,
                transition_id=transition.id,
                action_id=transition.action_id,
                action_kind=action_kind,
            )
        )

    return candidates


def filter_evidence_by_selected_runs(
    snapshot: EvidenceSnapshot, selected_run_ids: Iterable[str] | None
) -> EvidenceSnapshot:
    if not selected_run_ids:
        return snapshot
    selected = {value for value in selected_run_ids if value}
    if not selected:
        return snapshot

    runs = [run for run in snapshot.runs if run.id in selected]
    transitions = [
        transition for transition in snapshot.transitions if transition.run_id in selected
    ]
    action_ids = {transition.action_id for transition in transitions}
    state_ids = {
        state_id
        for transition in transitions
        for state_id in (transition.from_state_id, transition.to_state_id)
        if state_id
    }
    actions = [action for action in snapshot.actions if action.id in action_ids]
    state_ids.update(action.source_state_id for action in actions if action.source_state_id)
    element_ids = {action.target_element_id for action in actions if action.target_element_id}
    elements = [element for element in snapshot.elements if element.id in element_ids]
    state_ids.update(element.state_id for element in elements)
    states = [state for state in snapshot.states if state.id in state_ids]

    observations = [
        observation for observation in snapshot.observations if observation.run_id in selected
    ]
    observation_ids = {observation.id for observation in observations}
    attachments = [
        attachment
        for attachment in snapshot.attachments
        if attachment.run_id in selected
        or (attachment.observation_id and attachment.observation_id in observation_ids)
    ]
    artifacts = [
        artifact
        for artifact in snapshot.artifacts
        if artifact.run_id in selected or artifact.run_id is None
    ]

    return EvidenceSnapshot(
        artifacts=artifacts,
        states=states,
        elements=elements,
        actions=actions,
        transitions=transitions,
        runs=runs,
        observations=observations,
        attachments=attachments,
    )


def best_match(fragment_text: str, candidates: list[Candidate]) -> dict[str, Any] | None:
    frag_tokens = tokens(fragment_text)
    if not frag_tokens:
        return None
    frag_expanded = expanded_tokens(frag_tokens)
    intent = classify_intent(frag_tokens)
    phrase = normalize_text(fragment_text)
    best: dict[str, Any] | None = None

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
            score += min(0.55, 0.18 * len(informative_overlap))
        if raw_informative:
            score += min(0.20, 0.10 * len(raw_informative))

        normalized_candidate = normalize_text(candidate.text)
        frag_terms = sorted(token for token in frag_expanded if token not in WEAK_TOKENS)
        if phrase_match:
            score += 0.18
        else:
            for term in frag_terms:
                if term and term in normalized_candidate:
                    score += 0.05

        if intent == "operation":
            if candidate.target_type == "action":
                score += 0.18
            if candidate.target_type == "transition":
                score += 0.14
            if candidate.widget_kind in {"button", "link"}:
                score += 0.15
            if candidate.action_kind in {"navigate", "click"}:
                score += 0.10
        elif intent in {"display", "state"}:
            if candidate.target_type == "application_state":
                score += 0.16
            if candidate.widget_kind == "content":
                score += 0.10
            if candidate.target_type == "ui_element":
                score += 0.08
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

        lowered = normalized_candidate
        if (
            "use-cases" in lowered
            or "application use-cases" in lowered
            or "name of uc" in lowered
            or "context of use" in lowered
        ):
            score -= 0.35
        if "university information system" in lowered:
            score -= 0.18
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


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


def tokens(text: str | None) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9']+", normalize_text(text)) if token}


def expanded_tokens(token_values: set[str]) -> set[str]:
    expanded = set(token_values)
    for token in list(token_values):
        expanded.update(_EXPANSIONS.get(token, set()))
    return expanded


def classify_intent(token_values: set[str]) -> str:
    if {"click", "select", "choose", "press"} & token_values:
        return "click"
    if {"type", "enter", "fill", "input"} & token_values:
        return "type"
    if _OPERATION_TOKENS & token_values:
        return "operation"
    if _DISPLAY_TOKENS & token_values:
        return "display"
    if {"page", "screen", "state"} & token_values:
        return "state"
    return "generic"


def element_candidate_parts(element: UIElement) -> list[str]:
    parts = [
        element.text,
        element.title,
        element.href,
        element.css_selector,
        element.path,
        element.tag_name,
        element.role,
    ]
    return [part for part in parts if part]


def element_attribute(element: UIElement, key: str) -> str | None:
    value = element.attributes.get(key) if hasattr(element, "attributes") else None
    return value if isinstance(value, str) and value.strip() else None


def action_attribute(action: Any, key: str) -> str | None:
    value = action.attributes.get(key) if hasattr(action, "attributes") else None
    return value if isinstance(value, str) and value.strip() else None


__all__ = [
    "Candidate",
    "WEAK_TOKENS",
    "best_match",
    "build_candidates",
    "classify_intent",
    "filter_evidence_by_selected_runs",
    "expanded_tokens",
    "iter_selected_requirements",
    "normalize_text",
    "tokens",
]
