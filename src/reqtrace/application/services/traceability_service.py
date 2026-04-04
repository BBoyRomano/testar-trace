"""Traceability service: orchestrates method selection and execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from reqtrace.application.exceptions import (
    TraceabilityMethodExecutionError,
    UnknownTraceabilityMethodError,
)
from reqtrace.application.methods.baseline import BaselineMethod
from reqtrace.application.methods.candidate_match import CandidateMatchMethod
from reqtrace.application.methods.flow_match import FlowMatchMethod
from reqtrace.application.methods.hybrid_match import HybridMatchMethod
from reqtrace.application.protocols import TraceabilityMethod
from reqtrace.application.results import TraceabilityRequest, TraceabilityResult

logger = logging.getLogger(__name__)


@dataclass
class TraceabilityService:
    methods: dict[str, TraceabilityMethod] = field(default_factory=dict)

    def register_method(self, method: TraceabilityMethod) -> None:
        self.methods[method.name] = method
        logger.debug("Registered traceability method.", extra={"method_name": method.name})

    def available_methods(self) -> list[str]:
        return sorted(self.methods)

    def execute(self, request: TraceabilityRequest) -> TraceabilityResult:
        try:
            method = self.methods[request.method_name]
        except KeyError as exc:
            logger.warning(
                "Unknown traceability method requested.",
                extra={"method_name": request.method_name},
            )
            raise UnknownTraceabilityMethodError(
                f"Unknown traceability method: {request.method_name}"
            ) from exc

        logger.info(
            "Running traceability method.",
            extra={"method_name": method.name},
        )
        started = time.perf_counter()
        try:
            result = method.run(request)
            elapsed = time.perf_counter() - started
            logger.info(
                "Traceability method completed in %.2fs.",
                elapsed,
                extra={
                    "method_name": method.name,
                    "run_id": result.run.id,
                    "status": str(result.run.status),
                },
            )
            return result
        except Exception as exc:  # pragma: no cover - defensive boundary
            logger.exception("Traceability method '%s' failed.", method.name)
            raise TraceabilityMethodExecutionError(
                f"Traceability method '{method.name}' failed."
            ) from exc


def build_default_traceability_service(
    *, include_experimental_methods: bool = True
) -> TraceabilityService:
    service = TraceabilityService()
    service.register_method(BaselineMethod())
    if include_experimental_methods:
        service.register_method(CandidateMatchMethod())
        service.register_method(FlowMatchMethod())
        service.register_method(HybridMatchMethod())
    return service
