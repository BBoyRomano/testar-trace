from __future__ import annotations

from collections.abc import Callable
from typing import Any

from reqtrace.domain.state_graph import StateGraph
from reqtrace.ingest.state_models.canonical_json import load_canonical_json_state_graph
from reqtrace.ingest.state_models.testar_json_v1 import load_testar_json_v1_state_graph


StateModelImporter = Callable[[dict[str, Any]], StateGraph]


def is_canonical_json_state_graph(data: dict[str, Any]) -> bool:
    return "states" in data and "transitions" in data


def is_testar_json_v1_state_graph(data: dict[str, Any]) -> bool:
    return "ConcreteState" in data and "ConcreteTransitions" in data


STATE_MODEL_IMPORTERS: tuple[tuple[Callable[[dict[str, Any]], bool], StateModelImporter], ...] = (
    (is_canonical_json_state_graph, load_canonical_json_state_graph),
    (is_testar_json_v1_state_graph, load_testar_json_v1_state_graph),
)


def detect_state_model_importer(data: dict[str, Any]) -> StateModelImporter:
    for can_load, importer in STATE_MODEL_IMPORTERS:
        if can_load(data):
            return importer

    raise ValueError("Unsupported state model format.")
