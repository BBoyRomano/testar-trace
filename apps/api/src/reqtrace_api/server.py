"""Minimal HTTP API for ReqTrace applications."""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from reqtrace import analyze_traceability
from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import RequirementSet
from reqtrace.registry import available_trace_methods
from reqtrace.serialization import to_plain_data
from reqtrace_adapters import load_evidence, load_requirements
from reqtrace_adapters.load import validate_evidence, validate_requirements
from reqtrace_adapters.registry import available_parsers
from reqtrace_adapters.sources.base import SourceInput

__all__ = ["main", "run"]


class ReqTraceApiHandler(BaseHTTPRequestHandler):
    """Handle ReqTrace API requests."""

    server_version = "ReqTraceApi/0.1"

    def do_OPTIONS(self) -> None:
        self._send_empty(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:
        if self.path == "/api/v1/health":
            self._send_json({"status": "ok"})
            return
        if self.path == "/api/v1/methods":
            self._send_json({"methods": list(available_trace_methods())})
            return
        if self.path == "/api/v1/parsers":
            self._send_json(
                {
                    "parsers": [
                        {
                            "artifact": artifact,
                            "kind": kind,
                            "format": format_name,
                        }
                        for artifact, kind, format_name in available_parsers()
                    ],
                },
            )
            return
        self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint.")

    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            if self.path == "/api/v1/requirements/parse":
                self._send_json(to_plain_data(_parse_requirements(payload)))
                return
            if self.path == "/api/v1/evidence/parse":
                self._send_json(to_plain_data(_parse_evidence(payload)))
                return
            if self.path == "/api/v1/requirements/validate":
                _validate_requirements(payload)
                self._send_json({"valid": True})
                return
            if self.path == "/api/v1/evidence/validate":
                _validate_evidence(payload)
                self._send_json({"valid": True})
                return
            if self.path == "/api/v1/analyze":
                self._send_json(to_plain_data(_analyze(payload)))
                return
            self._send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint.")
        except ValueError as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))
        except Exception as error:  # noqa: BLE001
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        data = _decode_request_body(self.rfile.read(length))
        payload = json.loads(data or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"detail": message}, status=status)

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def _parse_requirements(payload: dict[str, object]) -> RequirementSet:
    kind = _string(payload, "kind", default="auto")
    format_name = _optional_string(payload, "format")
    return load_requirements(
        _PayloadSource(_source_inputs(payload, default_name="requirements.md")),
        kind=kind,
        format=format_name,
    )


def _validate_requirements(payload: dict[str, object]) -> None:
    kind = _string(payload, "kind", default="auto")
    format_name = _optional_string(payload, "format")
    validate_requirements(
        _PayloadSource(_source_inputs(payload, default_name="requirements.md")),
        kind=kind,
        format=format_name,
    )


def _decode_request_body(body: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Request body must be encoded as UTF-8 JSON.")


def _parse_evidence(payload: dict[str, object]) -> EvidenceSet:
    kind = _string(payload, "kind", default="auto")
    format_name = _optional_string(payload, "format")
    return load_evidence(
        _PayloadSource(_source_inputs(payload, default_name="evidence.json")),
        kind=kind,
        format=format_name,
    )


def _validate_evidence(payload: dict[str, object]) -> None:
    kind = _string(payload, "kind", default="auto")
    format_name = _optional_string(payload, "format")
    validate_evidence(
        _PayloadSource(_source_inputs(payload, default_name="evidence.json")),
        kind=kind,
        format=format_name,
    )


def _analyze(payload: dict[str, object]) -> object:
    requirements_payload = _object(payload, "requirements")
    evidence_payload = _object(payload, "evidence")
    requirements = _parse_requirements(requirements_payload)
    evidence = _parse_evidence(evidence_payload)
    return analyze_traceability(
        requirements,
        evidence,
        method=_string(payload, "method", default="sequence"),
    )


def _source_data(payload: dict[str, object], format_name: str) -> object:
    if "data" in payload:
        return payload["data"]
    text = _string(payload, "text", default="")
    if format_name == "json":
        parsed = json.loads(text or "{}")
        if not isinstance(parsed, dict):
            raise ValueError("JSON source text must decode to an object.")
        return parsed
    return text


class _PayloadSource:
    def __init__(self, inputs: tuple[SourceInput, ...]) -> None:
        self._inputs = inputs

    def load(self) -> tuple[SourceInput, ...]:
        return self._inputs


def _source_inputs(
    payload: dict[str, object],
    *,
    default_name: str,
) -> tuple[SourceInput, ...]:
    sources = payload.get("sources")
    if sources is None:
        return (_source_input(payload, default_name=default_name),)
    if not isinstance(sources, list):
        raise ValueError("'sources' must be a list.")
    if not sources:
        raise ValueError("'sources' must not be empty.")
    return tuple(
        _source_input(_source_payload(source), default_name=default_name)
        for source in sources
    )


def _source_input(payload: dict[str, object], *, default_name: str) -> SourceInput:
    format_name = _string(
        payload,
        "format",
        default=_format_from_name(default_name),
    ).removeprefix(".")
    return SourceInput(
        data=_source_data(payload, format_name),
        name=_string(payload, "name", default=default_name),
        format=format_name,
        uri=_optional_string(payload, "uri"),
    )


def _source_payload(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("'sources' entries must be JSON objects.")
    return value


def _format_from_name(name: str) -> str:
    parts = name.rsplit(".", maxsplit=1)
    return parts[1] if len(parts) == 2 else ""


def _object(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key!r} must be a JSON object.")
    return value


def _string(payload: dict[str, object], key: str, *, default: str) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key!r} must be a string.")
    return value


def _optional_string(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key!r} must be a string.")
    return value


def run(*, host: str, port: int) -> None:
    """Run the ReqTrace API server."""
    server = ThreadingHTTPServer((host, port), ReqTraceApiHandler)
    print(f"ReqTrace API listening on http://{host}:{port}")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    """Run the ReqTrace API command-line entry point."""
    parser = argparse.ArgumentParser(prog="reqtrace-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    run(host=args.host, port=args.port)
    return 0
