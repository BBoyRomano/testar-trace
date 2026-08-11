"""Adapter for TESTAR state-model JSON exports."""

import json
from collections.abc import Mapping
from typing import TypeGuard

from testar_trace.domain.state_models import (
    Action,
    State,
    StateModel,
    StateModelLayer,
    Transition,
    Widget,
)
from testar_trace_adapters._identifiers import artifact_stem, scoped_id
from testar_trace_adapters.source import SourceArtifact

__all__ = ["is_testar_state_model", "parse_testar_state_model"]


def is_testar_state_model(source: SourceArtifact) -> bool:
    """Return whether an artifact resembles a TESTAR state-model export."""
    data = _json_object_or_none(source.data)
    return data is not None and (
        "ConcreteState" in data
        or "ConcreteTransitions" in data
        or "InitialStates" in data
    )


def parse_testar_state_model(source: SourceArtifact) -> StateModel:
    """Parse one TESTAR JSON artifact into exactly one canonical state model."""
    data = _json_object(source)
    model_id = artifact_stem(source.id)
    raw_states = _list(data.get("ConcreteState", []), "ConcreteState")
    raw_actions = _list(data.get("ConcreteAction", []), "ConcreteAction")
    raw_transitions = _list(
        data.get("ConcreteTransitions", []),
        "ConcreteTransitions",
    )

    states, widgets, state_ids = _states_and_widgets(
        raw_states,
        model_id=model_id,
        source=source,
    )
    actions, action_ids = _actions(
        raw_actions,
        model_id=model_id,
        source=source,
        widgets=widgets,
    )
    transitions = _transitions(
        raw_transitions,
        model_id=model_id,
        source=source,
        state_ids=state_ids,
        action_ids=action_ids,
    )

    return StateModel(
        id=model_id,
        title=_model_title(data, fallback=model_id),
        layer=StateModelLayer.MIXED,
        initial_state_ids=_initial_state_ids(
            data,
            model_id=model_id,
            state_ids=state_ids,
        ),
        states=states,
        widgets=widgets,
        actions=actions,
        transitions=transitions,
        source_ref=source.source_ref(
            native_id=model_id,
            element_kind="state-model",
        ),
        metadata={
            "source_format": "testar-json",
            "initial_page": _optional_text(data.get("InitialPage")),
            "initial_url": _optional_text(data.get("InitialUrl")),
        },
    )


def _states_and_widgets(
    values: list[object],
    *,
    model_id: str,
    source: SourceArtifact,
) -> tuple[tuple[State, ...], tuple[Widget, ...], dict[str, str]]:
    states: list[State] = []
    widgets: list[Widget] = []
    state_ids: dict[str, str] = {}

    for index, item in enumerate(values):
        location = f"ConcreteState[{index}]"
        value = _object(item, location)
        native_id = _required_text(
            value.get("AbstractID"),
            f"{location}.AbstractID",
        )
        state_id = scoped_id(model_id, "state", native_id)
        if native_id in state_ids:
            raise ValueError(f"duplicate TESTAR state id: {native_id!r}")
        state_ids[native_id] = state_id
        title = _optional_text(value.get("WebTitle"))
        states.append(
            State(
                id=state_id,
                state_model_id=model_id,
                name=title,
                title=title,
                url=_optional_text(value.get("WebHref")),
                source_ref=source.source_ref(
                    native_id=native_id,
                    element_kind="state",
                    container_id=model_id,
                    location=location,
                ),
                metadata={"testar_abstract_id": native_id},
            )
        )
        widgets.extend(
            _widget_tree(
                value.get("WidgetTree", []),
                model_id=model_id,
                state_id=state_id,
                state_native_id=native_id,
                source=source,
                location=f"{location}.WidgetTree",
            )
        )

    return tuple(states), tuple(widgets), state_ids


def _widget_tree(
    value: object,
    *,
    model_id: str,
    state_id: str,
    state_native_id: str,
    source: SourceArtifact,
    location: str,
) -> tuple[Widget, ...]:
    roots = _list(value, location)
    stack = [
        (item, f"{location}[{index}]")
        for index, item in reversed(tuple(enumerate(roots)))
    ]
    widgets: list[Widget] = []
    used_ids: set[str] = set()

    while stack:
        item, item_location = stack.pop()
        node = _object(item, item_location)
        children = _list(node.get("children", []), f"{item_location}.children")
        stack.extend(
            (child, f"{item_location}.children[{index}]")
            for index, child in reversed(tuple(enumerate(children)))
        )

        native_id = _first_text(
            node.get("ConcreteID"),
            node.get("AbstractID"),
            node.get("id"),
        )
        if native_id is None:
            continue
        widget_id = scoped_id(
            model_id,
            "widget",
            f"{state_native_id}:{native_id}",
        )
        if widget_id in used_ids:
            continue
        used_ids.add(widget_id)
        widgets.append(
            Widget(
                id=widget_id,
                state_model_id=model_id,
                state_id=state_id,
                tag_name=_optional_text(node.get("WebTagName")),
                role=_first_text(node.get("Role"), node.get("WebAriaRole")),
                text=_first_text(
                    node.get("WebTextContent"),
                    node.get("WebInnerText"),
                ),
                title=_first_text(node.get("WebTitle"), node.get("Title")),
                href=_optional_text(node.get("WebHref")),
                css_selector=_optional_text(node.get("WebCssSelector")),
                source_ref=source.source_ref(
                    native_id=native_id,
                    element_kind="widget",
                    container_id=state_id,
                    location=item_location,
                ),
                metadata=_selected_metadata(
                    node,
                    "WebName",
                    "WebType",
                    "WebValue",
                    "WebPlaceholder",
                ),
            )
        )

    return tuple(widgets)


def _actions(
    values: list[object],
    *,
    model_id: str,
    source: SourceArtifact,
    widgets: tuple[Widget, ...],
) -> tuple[tuple[Action, ...], dict[str, str]]:
    actions: list[Action] = []
    action_ids: dict[str, str] = {}

    for index, item in enumerate(values):
        location = f"ConcreteAction[{index}]"
        value = _object(item, location)
        native_ids = _text_values(
            value.get("actionId"),
            value.get("ActionId"),
            value.get("ConcreteID"),
            value.get("AbstractID"),
        )
        if not native_ids:
            raise ValueError(f"{location} must contain an action identifier")
        native_id = native_ids[0]
        action_id = scoped_id(model_id, "action", native_id)
        if action_id in {action.id for action in actions}:
            raise ValueError(f"duplicate TESTAR action id: {native_id!r}")
        for alias in native_ids:
            action_ids.setdefault(alias, action_id)

        actions.append(
            Action(
                id=action_id,
                state_model_id=model_id,
                description=_optional_text(value.get("Desc")),
                target_widget_id=_matching_widget_id(value, widgets),
                value=_first_text(
                    value.get("InputValue"),
                    value.get("Value"),
                    value.get("Text"),
                ),
                source_ref=source.source_ref(
                    native_id=native_id,
                    element_kind="action",
                    container_id=model_id,
                    location=location,
                ),
                metadata=_selected_metadata(
                    value,
                    "ActionRole",
                    "ActionType",
                    "WebTagName",
                ),
            )
        )

    return tuple(actions), action_ids


def _transitions(
    values: list[object],
    *,
    model_id: str,
    source: SourceArtifact,
    state_ids: Mapping[str, str],
    action_ids: Mapping[str, str],
) -> tuple[Transition, ...]:
    transitions: list[Transition] = []
    used_ids: set[str] = set()

    for index, item in enumerate(values):
        location = f"ConcreteTransitions[{index}]"
        value = _object(item, location)
        raw_action_id = _first_text(
            value.get("Action"),
            value.get("ActionId"),
            value.get("ActionWC"),
            value.get("ActionWA"),
        )
        if raw_action_id is None:
            raise ValueError(f"{location} must contain an action identifier")
        if raw_action_id not in action_ids:
            raise ValueError(f"{location} references unknown action {raw_action_id!r}")

        source_native_id = _required_text(
            value.get("Source"),
            f"{location}.Source",
        )
        if source_native_id not in state_ids:
            raise ValueError(
                f"{location} references unknown source state {source_native_id!r}"
            )
        target_native_id = _optional_text(value.get("Target"))
        if target_native_id is not None and target_native_id not in state_ids:
            raise ValueError(
                f"{location} references unknown target state {target_native_id!r}"
            )

        native_id = _first_text(value.get("id"), value.get("TransitionID"))
        native_id = native_id or str(index)
        transition_id = scoped_id(model_id, "transition", native_id)
        if transition_id in used_ids:
            transition_id = scoped_id(model_id, "transition", f"{native_id}:{index}")
        used_ids.add(transition_id)
        transitions.append(
            Transition(
                id=transition_id,
                state_model_id=model_id,
                source_state_id=state_ids[source_native_id],
                action_id=action_ids[raw_action_id],
                target_state_id=(
                    state_ids[target_native_id]
                    if target_native_id is not None
                    else None
                ),
                order_index=index,
                source_ref=source.source_ref(
                    native_id=native_id,
                    element_kind="transition",
                    container_id=model_id,
                    location=location,
                ),
            )
        )

    return tuple(transitions)


def _initial_state_ids(
    data: Mapping[str, object],
    *,
    model_id: str,
    state_ids: Mapping[str, str],
) -> tuple[str, ...]:
    values = _list(data.get("InitialStates", []), "InitialStates")
    result: list[str] = []
    for index, item in enumerate(values):
        native_id = _required_text(
            _object(item, f"InitialStates[{index}]").get("AbstractID"),
            f"InitialStates[{index}].AbstractID",
        )
        canonical_id = state_ids.get(native_id)
        if canonical_id is not None and canonical_id not in result:
            result.append(canonical_id)

    if not result:
        initial_id = _optional_text(data.get("InitialState"))
        if initial_id is not None and initial_id in state_ids:
            result.append(scoped_id(model_id, "state", initial_id))
    return tuple(result)


def _model_title(data: Mapping[str, object], *, fallback: str) -> str:
    title = _optional_text(data.get("InitialPage"))
    if title is not None:
        return title
    initial_states = data.get("InitialStates")
    if isinstance(initial_states, list):
        for item in initial_states:
            if _is_object(item):
                title = _optional_text(item.get("InitialPage"))
                if title is not None:
                    return title
    return fallback


def _matching_widget_id(
    action: Mapping[str, object],
    widgets: tuple[Widget, ...],
) -> str | None:
    native_id = _optional_text(action.get("ConcreteID"))
    selector = _optional_text(action.get("WebCssSelector"))
    matches = tuple(
        widget.id
        for widget in widgets
        if (
            native_id is not None
            and widget.source_ref is not None
            and widget.source_ref.native_id == native_id
        )
        or (selector is not None and widget.css_selector == selector)
    )
    return matches[0] if len(matches) == 1 else None


def _selected_metadata(
    value: Mapping[str, object],
    *keys: str,
) -> dict[str, object]:
    return {key: value[key] for key in keys if value.get(key) is not None}


def _json_object(source: SourceArtifact) -> dict[str, object]:
    value = source.data
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON in {source.name}: {error}") from error
    if not _is_object(value):
        raise TypeError(f"{source.name} JSON must contain an object")
    return value


def _json_object_or_none(value: object) -> dict[str, object] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if _is_object(value) else None


def _object(value: object, context: str) -> dict[str, object]:
    if not _is_object(value):
        raise TypeError(f"{context} must be an object with string keys")
    return value


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list")
    return list(value)


def _required_text(value: object, context: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ValueError(f"{context} must not be blank")
    return text


def _optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _first_text(*values: object) -> str | None:
    return next((text for value in values if (text := _optional_text(value))), None)


def _text_values(*values: object) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(text for value in values if (text := _optional_text(value)))
    )
