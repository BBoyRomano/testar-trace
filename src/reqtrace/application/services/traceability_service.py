"""Traceability service: orchestrates method selection and execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from reqtrace.application.exceptions import (
    TraceabilityMethodExecutionError,
    UnknownTraceabilityMethodError,
)
from reqtrace.application.methods.baseline import BaselineMethod
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.results import TraceabilityRequest, TraceabilityResult

logger = logging.getLogger(__name__)


@dataclass
class TraceabilityService:
    methods: dict[str, TraceabilityMethod] = field(default_factory=dict)

    def register_method(self, method: TraceabilityMethod) -> None:
        self.methods[method.name] = method

    def available_methods(self) -> list[str]:
        return sorted(self.methods)

    def execute(self, request: TraceabilityRequest) -> TraceabilityResult:
        try:
            method = self.methods[request.method_name]
        except KeyError as exc:
            raise UnknownTraceabilityMethodError(
                f"Unknown traceability method: {request.method_name}"
            ) from exc

        logger.info("Running traceability method '%s'.", method.name)
        try:
            return method.run(request)
        except Exception as exc:  # pragma: no cover - defensive boundary
            logger.exception("Traceability method '%s' failed.", method.name)
            raise TraceabilityMethodExecutionError(
                f"Traceability method '{method.name}' failed."
            ) from exc


def build_default_traceability_service() -> TraceabilityService:
    service = TraceabilityService()
    service.register_method(BaselineMethod())
    return service
