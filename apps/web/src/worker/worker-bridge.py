"""JSON boundary for TESTAR Trace running inside a Pyodide worker."""

import json
from typing import cast

from testar_trace import (
    RequirementSet,
    StateModelCollection,
    TraceContext,
    analyze_traceability,
    create_builtin_method_registry,
    to_plain_data,
)
from testar_trace_adapters import (
    SourceArtifact,
    create_builtin_adapter_registry,
    load_requirements,
    load_state_models,
)


def handle_request(operation: str, payload_json: str, progress_callback=None) -> str:
    """Execute one worker operation and return a JSON response envelope."""
    try:
        payload = json.loads(payload_json)
        if not isinstance(payload, dict):
            raise TypeError("Worker payload must be a JSON object.")
        response = {
            "ok": True,
            "value": to_plain_data(_dispatch(operation, payload, progress_callback)),
        }
    except Exception as error:  # noqa: BLE001
        response = {
            "ok": False,
            "error": {"name": type(error).__name__, "message": str(error)},
        }
    return json.dumps(response, ensure_ascii=False)


def _dispatch(
    operation: str,
    payload: dict[str, object],
    progress_callback,
) -> object:
    if operation == "catalog":
        return _catalog()
    if operation == "parse-requirements":
        return _parse_requirements(payload)
    if operation == "parse-state-models":
        return _parse_state_models(payload)
    if operation == "analyze":
        return _analyze(payload, progress_callback)
    raise ValueError(f"Unknown worker operation: {operation!r}.")


def _catalog() -> dict[str, object]:
    adapters = create_builtin_adapter_registry()
    methods = create_builtin_method_registry()
    return {
        "requirement_adapters": [
            {"id": item.id, "name": item.name, "formats": item.formats}
            for item in adapters.requirement_adapters()
        ],
        "state_model_adapters": [
            {"id": item.id, "name": item.name, "formats": item.formats}
            for item in adapters.state_model_adapters()
        ],
        "methods": [{"id": item.id, "name": item.name} for item in methods],
    }


def _parse_requirements(payload: dict[str, object]) -> RequirementSet:
    return load_requirements(
        _source_artifacts(payload, default_name="requirements.md"),
        adapter=_optional_string(payload, "adapter"),
    )


def _parse_state_models(payload: dict[str, object]) -> StateModelCollection:
    return load_state_models(
        _source_artifacts(payload, default_name="state-model.json"),
        adapter=_optional_string(payload, "adapter"),
        collection_id=_string(payload, "collection_id", default="state-models"),
        title=_string(payload, "title", default="State models"),
    )


def _analyze(payload: dict[str, object], progress_callback) -> object:
    methods = create_builtin_method_registry()
    method_id = _string(payload, "method", default="lexical")
    method = methods.get(method_id)
    if method is None:
        raise ValueError(f"Unknown trace method: {method_id!r}.")

    return analyze_traceability(
        _parse_requirements(_object(payload, "requirements")),
        _parse_state_models(_object(payload, "state_models")),
        method=method,
        context=TraceContext(progress=_progress_reporter(progress_callback)),
    )


def _progress_reporter(progress_callback):
    if progress_callback is None:
        return None

    def report(event) -> None:
        progress_callback(json.dumps(to_plain_data(event), ensure_ascii=False))

    return report


def _source_artifacts(
    payload: dict[str, object],
    *,
    default_name: str,
) -> tuple[SourceArtifact, ...]:
    values = payload.get("sources")
    if not isinstance(values, list) or not values:
        raise ValueError("'sources' must be a non-empty list.")

    artifacts: list[SourceArtifact] = []
    for index, value in enumerate(values):
        source = _source_payload(value)
        name = _string(source, "name", default=default_name)
        format_name = _string(
            source,
            "format",
            default=_format_from_name(name),
        ).removeprefix(".")
        artifacts.append(
            SourceArtifact(
                id=_string(source, "id", default=f"source-{index + 1}"),
                name=name,
                data=_string(source, "text", default=""),
                format=format_name,
                uri=_optional_string(source, "uri"),
            )
        )
    return tuple(artifacts)


def _source_payload(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("'sources' entries must be JSON objects.")
    return cast("dict[str, object]", value)


def _object(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise TypeError(f"{key!r} must be a JSON object.")
    return cast("dict[str, object]", value)


def _string(payload: dict[str, object], key: str, *, default: str) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise TypeError(f"{key!r} must be a string.")
    return value


def _optional_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise TypeError(f"{key!r} must be a string.")
    return value


def _format_from_name(name: str) -> str:
    parts = name.rsplit(".", maxsplit=1)
    if len(parts) != 2 or not parts[1]:
        raise ValueError(f"Source {name!r} has no file extension.")
    return parts[1]


handle_request  # noqa: B018
