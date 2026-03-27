from __future__ import annotations

from reqtrace.domain.state_graph import (
    Observation,
    ObservationKind,
    State,
    StateGraph,
    Transition,
)


def load_canonical_json_state_graph(data: dict) -> StateGraph:
    states = tuple(
        State(
            id=item["id"],
            title=item.get("title"),
            url=item.get("url"),
            observations=tuple(
                Observation(
                    kind=ObservationKind(obs["kind"]),
                    value=obs["value"],
                    locator=obs.get("locator"),
                    metadata=obs.get("metadata", {}),
                )
                for obs in item.get("observations", [])
            ),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("states", [])
    )

    transitions = tuple(
        Transition(
            source_id=item["source_id"],
            target_id=item["target_id"],
            action=item.get("action"),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("transitions", [])
    )

    return StateGraph(
        states=states,
        transitions=transitions,
        metadata=data.get("metadata", {}),
    )
