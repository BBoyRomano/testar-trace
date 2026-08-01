"""TESTAR evidence adapters."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TypeGuard

from reqtrace.models.evidence import (
    EvidenceArtifact,
    EvidenceSet,
    ExecutionAction,
    ExecutionElement,
    ExecutionState,
    ExecutionTransition,
)

from reqtrace_adapters._utils import freeze_metadata, source_ref_from_source
from reqtrace_adapters.sources.base import SourceInput

__all__ = ["load_testar_state_model_json"]


@dataclass(slots=True, frozen=True)
class _TestarElement:
    """A UI element parsed from TESTAR output."""

    id: str
    state_id: str
    tag_name: str | None = None
    role: str | None = None
    text: str | None = None
    title: str | None = None
    href: str | None = None
    css_selector: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_TestarElement.id must not be blank.")
        if not self.state_id.strip():
            raise ValueError("_TestarElement.state_id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _TestarState:
    """An application state parsed from TESTAR output."""

    id: str
    name: str | None = None
    title: str | None = None
    url: str | None = None
    elements: tuple[_TestarElement, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_TestarState.id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _TestarAction:
    """An action parsed from TESTAR output."""

    id: str
    description: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_TestarAction.id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _TestarTransition:
    """A state transition parsed from TESTAR output."""

    id: str
    from_state_id: str
    action_id: str
    to_state_id: str | None = None
    order_index: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_TestarTransition.id must not be blank.")
        if not self.from_state_id.strip():
            raise ValueError("_TestarTransition.from_state_id must not be blank.")
        if not self.action_id.strip():
            raise ValueError("_TestarTransition.action_id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _TestarStateModel:
    """A parsed TESTAR state model before canonical mapping."""

    id: str
    title: str
    initial_url: str | None = None
    states: tuple[_TestarState, ...] = ()
    actions: tuple[_TestarAction, ...] = ()
    transitions: tuple[_TestarTransition, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_TestarStateModel.id must not be blank.")
        if not self.title.strip():
            raise ValueError("_TestarStateModel.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


def load_testar_state_model_json(source: SourceInput) -> EvidenceSet:
    """Load a TESTAR state model into canonical test evidence."""
    data = _require_object_dict(source.data, context=f"{source.name} JSON")
    model = _parse_testar_state_model(data, source=source)
    return _map_testar_state_model(model, source=source)


def _parse_testar_state_model(
    data: Mapping[str, object],
    *,
    source: SourceInput,
) -> _TestarStateModel:
    source_stem = _source_stem(source)
    raw_states = _require_list(data.get("ConcreteState", []), "ConcreteState")
    raw_actions = _require_list(data.get("ConcreteAction", []), "ConcreteAction")
    raw_transitions = _require_list(
        data.get("ConcreteTransitions", []),
        "ConcreteTransitions",
    )

    return _TestarStateModel(
        id=source_stem,
        title=_text_or_default(data.get("InitialPage"), source_stem),
        initial_url=_optional_text(data.get("InitialUrl")),
        states=tuple(
            _state_from_mapping(item, index=index)
            for index, item in enumerate(raw_states)
        ),
        actions=tuple(
            _action_from_mapping(item, index=index)
            for index, item in enumerate(raw_actions)
        ),
        transitions=tuple(
            _transition_from_mapping(item, index=index)
            for index, item in enumerate(raw_transitions)
        ),
        metadata={
            "initial_page": data.get("InitialPage"),
            "initial_url": data.get("InitialUrl"),
        },
    )


def _map_testar_state_model(
    model: _TestarStateModel,
    *,
    source: SourceInput,
) -> EvidenceSet:
    return EvidenceSet(
        id=model.id,
        title=model.title,
        artifacts=(
            EvidenceArtifact(
                id=f"{model.id}:artifact",
                title=model.title,
                text=model.initial_url or "",
            ),
        ),
        states=tuple(
            ExecutionState(
                id=state.id,
                name=state.name,
                title=state.title,
                url=state.url,
                metadata=state.metadata,
            )
            for state in model.states
        ),
        elements=tuple(
            ExecutionElement(
                id=element.id,
                state_id=element.state_id,
                tag_name=element.tag_name,
                role=element.role,
                text=element.text,
                title=element.title,
                href=element.href,
                css_selector=element.css_selector,
                metadata=element.metadata,
            )
            for state in model.states
            for element in state.elements
        ),
        actions=tuple(
            ExecutionAction(
                id=action.id,
                description=action.description,
                metadata=action.metadata,
            )
            for action in model.actions
        ),
        transitions=tuple(
            ExecutionTransition(
                id=transition.id,
                from_state_id=transition.from_state_id,
                action_id=transition.action_id,
                to_state_id=transition.to_state_id,
                order_index=transition.order_index,
                metadata=transition.metadata,
            )
            for transition in model.transitions
        ),
        source_ref=source_ref_from_source(source),
        metadata=model.metadata,
    )


def _state_from_mapping(item: object, *, index: int) -> _TestarState:
    state = _require_object_dict(item, context=f"ConcreteState[{index}]")
    state_id = _required_text(
        state.get("AbstractID"),
        context=f"ConcreteState[{index}].AbstractID",
    )
    title = _optional_text(state.get("WebTitle"))

    return _TestarState(
        id=state_id,
        name=title,
        title=title,
        url=_optional_text(state.get("WebHref")),
        elements=_elements_from_state(state, state_id=state_id),
    )


def _elements_from_state(
    state: Mapping[str, object],
    *,
    state_id: str,
) -> tuple[_TestarElement, ...]:
    raw_widget_tree = _require_list(state.get("WidgetTree", []), "WidgetTree")
    elements: list[_TestarElement] = []
    stack = list(reversed(raw_widget_tree))

    while stack:
        node = _require_object_dict(stack.pop(), context="WidgetTree node")
        children = _require_list(node.get("children", []), "WidgetTree children")
        stack.extend(reversed(children))

        element_key = (
            _optional_text(node.get("ConcreteID"))
            or _optional_text(node.get("AbstractID"))
            or _optional_text(node.get("id"))
        )
        if element_key is None:
            continue

        elements.append(
            _TestarElement(
                id=f"{state_id}:{element_key}",
                state_id=state_id,
                tag_name=_optional_text(node.get("WebTagName")),
                role=_optional_text(node.get("Role") or node.get("WebAriaRole")),
                text=_optional_text(
                    node.get("WebTextContent") or node.get("WebInnerText"),
                ),
                title=_optional_text(node.get("WebTitle") or node.get("Title")),
                href=_optional_text(node.get("WebHref")),
                css_selector=_optional_text(node.get("WebCssSelector")),
            ),
        )

    return tuple(elements)


def _action_from_mapping(item: object, *, index: int) -> _TestarAction:
    action = _require_object_dict(item, context=f"ConcreteAction[{index}]")
    return _TestarAction(
        id=_required_text(
            action.get("AbstractID"),
            context=f"ConcreteAction[{index}].AbstractID",
        ),
        description=_optional_text(action.get("Desc")),
    )


def _transition_from_mapping(item: object, *, index: int) -> _TestarTransition:
    transition = _require_object_dict(item, context=f"ConcreteTransitions[{index}]")
    return _TestarTransition(
        id=f"transition-{index}",
        from_state_id=_required_text(
            transition.get("Source"),
            context=f"ConcreteTransitions[{index}].Source",
        ),
        action_id=_required_text(
            transition.get("Action"),
            context=f"ConcreteTransitions[{index}].Action",
        ),
        to_state_id=_optional_text(transition.get("Target")),
        order_index=index,
    )


def _require_list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list.")
    return list(value)


def _require_object_dict(value: object, *, context: str) -> dict[str, object]:
    if not _is_object_dict(value):
        raise TypeError(f"{context} must be an object with string keys.")
    return value


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _required_text(value: object, *, context: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"{context} must not be blank.")
    return text


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _text_or_default(value: object, default: str) -> str:
    return _optional_text(value) or default


def _source_stem(source: SourceInput) -> str:
    return source.name.rsplit(".", maxsplit=1)[0] or source.name
