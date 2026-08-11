"""Deterministic semantic profiles for path-alignment methods."""

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from testar_trace.domain.requirements import RequirementElement
from testar_trace.domain.state_models import (
    Action,
    State,
    StateModel,
    Transition,
    Widget,
)
from testar_trace.domain.traceability import TraceTargetKind, TraceTargetRef

_TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)
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
        "his",
        "her",
        "in",
        "into",
        "is",
        "it",
        "its",
        "located",
        "of",
        "on",
        "option",
        "other",
        "right",
        "side",
        "specific",
        "system",
        "the",
        "their",
        "then",
        "this",
        "to",
        "upper",
        "user",
        "will",
        "with",
    }
)
_SYNONYMS = {
    "activate": "activate",
    "choose": "activate",
    "click": "activate",
    "clicked": "activate",
    "clicking": "activate",
    "press": "activate",
    "pressed": "activate",
    "select": "activate",
    "selected": "activate",
    "display": "display",
    "displayed": "display",
    "appear": "display",
    "appeared": "display",
    "see": "display",
    "shown": "display",
    "visible": "display",
    "enter": "input",
    "entered": "input",
    "fill": "input",
    "filled": "input",
    "input": "input",
    "type": "input",
    "typed": "input",
    "logon": "login",
    "signin": "login",
    "signon": "login",
    "logoff": "logout",
    "signout": "logout",
}


@dataclass(frozen=True, slots=True)
class SemanticFacet:
    """One focused text view of a state-model transition or execution step."""

    label: str
    tokens: frozenset[str]
    target_ref: TraceTargetRef


@dataclass(frozen=True, slots=True)
class TransitionSemanticCandidate:
    """Semantic facets associated with one graph transition."""

    transition: Transition
    facets: tuple[SemanticFacet, ...]


@dataclass(frozen=True, slots=True)
class SemanticScore:
    """Score and explanation for one semantic candidate."""

    score: float
    facet: str
    matched_tokens: tuple[str, ...]
    target_ref: TraceTargetRef


def transition_candidates(
    model: StateModel,
) -> tuple[TransitionSemanticCandidate, ...]:
    """Build focused semantic candidates for every model transition."""
    states = {state.id: state for state in model.states}
    actions = {action.id: action for action in model.actions}
    widgets = {widget.id: widget for widget in model.widgets}
    widgets_by_state: dict[str, list[Widget]] = {state.id: [] for state in model.states}
    for widget in model.widgets:
        widgets_by_state[widget.state_id].append(widget)

    candidates: list[TransitionSemanticCandidate] = []
    for transition in model.transitions:
        action = actions[transition.action_id]
        target_widget = (
            widgets.get(action.target_widget_id)
            if action.target_widget_id is not None
            else None
        )
        source_state = states[transition.source_state_id]
        target_state = (
            states.get(transition.target_state_id)
            if transition.target_state_id is not None
            else None
        )
        facets = [
            _facet(
                "action",
                _action_text(action),
                kind=TraceTargetKind.ACTION,
                target_id=action.id,
            ),
            _facet(
                "source-state",
                _state_text(source_state),
                kind=TraceTargetKind.STATE,
                target_id=source_state.id,
            ),
        ]
        if target_widget is not None:
            facets.append(
                _facet(
                    "action-target",
                    _widget_text(target_widget),
                    kind=TraceTargetKind.WIDGET,
                    target_id=target_widget.id,
                )
            )
        if target_state is not None:
            facets.append(
                _facet(
                    "target-state",
                    _state_text(target_state),
                    kind=TraceTargetKind.STATE,
                    target_id=target_state.id,
                )
            )
        facets.extend(
            _facet(
                "source-widget",
                _widget_text(widget),
                kind=TraceTargetKind.WIDGET,
                target_id=widget.id,
            )
            for widget in widgets_by_state[source_state.id]
        )
        if target_state is not None:
            facets.extend(
                _facet(
                    "target-widget",
                    _widget_text(widget),
                    kind=TraceTargetKind.WIDGET,
                    target_id=widget.id,
                )
                for widget in widgets_by_state[target_state.id]
            )
        candidates.append(
            TransitionSemanticCandidate(
                transition=transition,
                facets=_unique_facets(facet for facet in facets if facet.tokens),
            )
        )
    return tuple(candidates)


def inverse_document_frequencies(
    candidates: Iterable[TransitionSemanticCandidate],
) -> dict[str, float]:
    """Calculate deterministic smoothed IDF weights over candidate facets."""
    documents = tuple(
        facet.tokens for candidate in candidates for facet in candidate.facets
    )
    if not documents:
        return {}
    frequencies = Counter(token for document in documents for token in document)
    total = len(documents)
    return {
        token: math.log((total + 1) / (frequency + 1)) + 1.0
        for token, frequency in frequencies.items()
    }


def score_element(
    element: RequirementElement,
    facets: Iterable[SemanticFacet],
    idf: dict[str, float],
) -> SemanticScore | None:
    """Return the strongest weighted token alignment for an element."""
    requirement_tokens = frozenset(normalized_tokens(element.text))
    if not requirement_tokens:
        return None

    best: SemanticScore | None = None
    for facet in facets:
        if not _facet_supports_element(element, facet):
            continue
        matched = requirement_tokens & facet.tokens
        if not matched:
            continue
        matched_weight = sum(idf.get(token, 1.0) for token in matched)
        requirement_weight = sum(idf.get(token, 1.0) for token in requirement_tokens)
        candidate_weight = sum(idf.get(token, 1.0) for token in facet.tokens)
        recall = matched_weight / requirement_weight
        precision = matched_weight / candidate_weight
        score = _f_beta(precision, recall, beta=2.0)
        proposed = SemanticScore(
            score=score,
            facet=facet.label,
            matched_tokens=tuple(sorted(matched)),
            target_ref=facet.target_ref,
        )
        if best is None or _semantic_score_key(proposed) > _semantic_score_key(best):
            best = proposed
    return best


def _facet_supports_element(
    element: RequirementElement,
    facet: SemanticFacet,
) -> bool:
    """Keep requirement semantics aligned with the role of graph evidence."""
    kind = element.kind.casefold().replace("-", "_")
    if kind in {"constraint", "precondition"}:
        return facet.label in {"source-state", "source-widget"}
    if kind in {"postcondition", "alternative_postcondition"}:
        return facet.label in {"target-state", "target-widget"}
    if kind == "trigger":
        return facet.label in {"action", "action-target"}
    if kind in {"main_step", "alternative_step", "exception_step"}:
        return facet.label in {
            "action",
            "action-target",
            "target-state",
            "target-widget",
        }
    return True


def normalized_tokens(text: str) -> tuple[str, ...]:
    """Normalize UI-oriented natural language into stable semantic tokens."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = normalized.replace("log in", "login").replace("sign in", "signin")
    normalized = normalized.replace("log out", "logout").replace("sign out", "signout")
    tokens: list[str] = []
    for raw in _TOKEN_PATTERN.findall(normalized):
        token = _normalize_token(raw)
        if token and token not in _STOP_WORDS:
            tokens.append(token)
    return tuple(dict.fromkeys(tokens))


def _normalize_token(token: str) -> str:
    synonym = _SYNONYMS.get(token)
    if synonym is not None:
        return synonym
    if len(token) > 5 and token.endswith("ies"):
        token = f"{token[:-3]}y"
    elif len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    return _SYNONYMS.get(token, token)


def _facet(
    label: str,
    text: str,
    *,
    kind: TraceTargetKind,
    target_id: str,
) -> SemanticFacet:
    return SemanticFacet(
        label=label,
        tokens=frozenset(normalized_tokens(text)),
        target_ref=TraceTargetRef(kind=kind, target_id=target_id),
    )


def _unique_facets(facets: Iterable[SemanticFacet]) -> tuple[SemanticFacet, ...]:
    result: list[SemanticFacet] = []
    seen: set[tuple[str, frozenset[str], TraceTargetKind, str]] = set()
    for facet in facets:
        key = (
            facet.label,
            facet.tokens,
            facet.target_ref.kind,
            facet.target_ref.target_id,
        )
        if key not in seen:
            seen.add(key)
            result.append(facet)
    return tuple(result)


def _f_beta(precision: float, recall: float, *, beta: float) -> float:
    if precision == 0.0 or recall == 0.0:
        return 0.0
    beta_squared = beta * beta
    return ((1.0 + beta_squared) * precision * recall) / (
        beta_squared * precision + recall
    )


def _semantic_score_key(value: SemanticScore) -> tuple[float, int, str, str, str]:
    return (
        value.score,
        len(value.matched_tokens),
        value.facet,
        value.target_ref.kind.value,
        value.target_ref.target_id,
    )


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
        widget.css_selector,
    )


def _action_text(action: Action) -> str:
    return _join_text(action.description, action.value)


def _join_text(*values: str | None) -> str:
    return " ".join(value.strip() for value in values if value and value.strip())
