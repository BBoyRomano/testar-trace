from __future__ import annotations

from typing import Any

from reqtrace.domain.state_graph import (
    Observation,
    ObservationKind,
    State,
    StateGraph,
    Transition,
)


def _walk_widget_tree(node: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = [node]
    for child in node.get("children", []) or []:
        nodes.extend(_walk_widget_tree(child))
    return nodes


def _map_observation_kind(node: dict[str, Any]) -> ObservationKind:
    tag = (node.get("WebTagName") or "").lower()

    if node.get("WebTextContent"):
        if tag == "a":
            return ObservationKind.LINK_TEXT
        if tag in {"input", "button"}:
            return ObservationKind.ACTION_LABEL
        return ObservationKind.TEXT

    if node.get("WebHref"):
        return ObservationKind.URL

    return ObservationKind.OTHER


def _extract_observations_from_state(concrete_state: dict[str, Any]) -> tuple[Observation, ...]:
    observations: list[Observation] = []

    title = concrete_state.get("WebTitle")
    if title:
        observations.append(
            Observation(
                kind=ObservationKind.TITLE,
                value=title,
                locator=None,
                metadata={},
            )
        )

    href = concrete_state.get("WebHref")
    if href:
        observations.append(
            Observation(
                kind=ObservationKind.URL,
                value=href,
                locator=None,
                metadata={},
            )
        )

    for root in concrete_state.get("WidgetTree", []) or []:
        for node in _walk_widget_tree(root):
            text = node.get("WebTextContent")
            href = node.get("WebHref")
            locator = node.get("WebCssSelector")

            if text:
                observations.append(
                    Observation(
                        kind=_map_observation_kind(node),
                        value=text,
                        locator=locator,
                        metadata={
                            "tag": node.get("WebTagName"),
                            "abstract_id": node.get("AbstractID"),
                            "concrete_id": node.get("ConcreteID"),
                        },
                    )
                )
            elif href and node.get("WebTagName", "").lower() == "a":
                observations.append(
                    Observation(
                        kind=ObservationKind.URL,
                        value=href,
                        locator=locator,
                        metadata={
                            "tag": node.get("WebTagName"),
                            "abstract_id": node.get("AbstractID"),
                            "concrete_id": node.get("ConcreteID"),
                        },
                    )
                )

    return tuple(observations)


def _build_action_lookup(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for action in data.get("ConcreteAction", []) or []:
        abstract_id = action.get("AbstractID")
        if abstract_id:
            lookup[abstract_id] = action
    return lookup


def load_testar_json_v1_state_graph(data: dict[str, Any]) -> StateGraph:
    action_lookup = _build_action_lookup(data)

    states = tuple(
        State(
            id=state["AbstractID"],
            title=state.get("WebTitle"),
            url=state.get("WebHref"),
            observations=_extract_observations_from_state(state),
            metadata={},
        )
        for state in data.get("ConcreteState", []) or []
    )

    transitions: list[Transition] = []
    for transition in data.get("ConcreteTransitions", []) or []:
        action_id = transition.get("Action")
        action = action_lookup.get(action_id, {})
        action_desc = action.get("Desc") or action_id

        transitions.append(
            Transition(
                source_id=transition["Source"],
                target_id=transition["Target"],
                action=action_desc,
                metadata={"action_id": action_id},
            )
        )

    return StateGraph(
        states=states,
        transitions=tuple(transitions),
        metadata={
            "source": "testar",
            "version": "json_v1",
            "initial_url": data.get("InitialUrl"),
            "initial_page": data.get("InitialPage"),
        },
    )
