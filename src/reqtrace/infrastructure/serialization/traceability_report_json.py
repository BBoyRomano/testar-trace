from __future__ import annotations

import logging
from pathlib import Path

from pydantic import ValidationError

from reqtrace.application.results import TraceabilityResult
from reqtrace.infrastructure.exceptions import (
    ReportDeserializationError,
    ReportSerializationError,
)

logger = logging.getLogger(__name__)


def save_report(report: TraceabilityResult, output_path: str | Path) -> None:
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = report.model_dump_json(indent=2)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(path)
        logger.info(
            "Saved traceability report JSON.",
            extra={"run_id": report.run.id, "output_path": str(path)},
        )
    except OSError as exc:
        logger.error(
            "Failed to save traceability report JSON.",
            exc_info=exc,
            extra={"output_path": str(path)},
        )
        raise ReportSerializationError(f"Could not save report to {path}") from exc


def load_report(result_path: str | Path) -> TraceabilityResult:
    path = Path(result_path)
    try:
        payload = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error(
            "Failed to read traceability report JSON.",
            exc_info=exc,
            extra={"result_path": str(path)},
        )
        raise ReportDeserializationError(f"Could not read report from {path}") from exc

    try:
        report = TraceabilityResult.model_validate_json(payload)
        logger.info(
            "Loaded traceability report JSON.",
            extra={"run_id": report.run.id, "result_path": str(path)},
        )
        return report
    except ValidationError as exc:
        logger.error(
            "Invalid traceability report schema.",
            exc_info=exc,
            extra={"result_path": str(path)},
        )
        raise ReportDeserializationError(f"Invalid report schema in {path}") from exc
    except ValueError as exc:
        logger.error(
            "Invalid traceability report JSON payload.",
            exc_info=exc,
            extra={"result_path": str(path)},
        )
        raise ReportDeserializationError(f"Invalid report JSON in {path}") from exc
