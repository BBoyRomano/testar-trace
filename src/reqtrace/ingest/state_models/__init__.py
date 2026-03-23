from __future__ import annotations

from reqtrace.domain.state_graph import StateGraph
from reqtrace.ingest.common import load_json_file
from reqtrace.ingest.state_models.registry import detect_state_model_importer

__all__ = ["load_state_graph"]


def load_state_graph(path: str) -> StateGraph:
    data = load_json_file(path)
    importer = detect_state_model_importer(data)
    return importer(data)
