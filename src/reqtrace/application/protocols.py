"""Protocols for application-layer traceability methods."""

from __future__ import annotations

from typing import Protocol

from reqtrace.application.results import TraceabilityRequest, TraceabilityResult


class TraceabilityMethod(Protocol):
    """A traceability method transforms inputs into traceability outputs."""

    name: str

    def run(self, request: TraceabilityRequest) -> TraceabilityResult:
        ...
