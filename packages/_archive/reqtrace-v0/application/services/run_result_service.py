"""Application-level use-cases for importing/exporting run results."""

from __future__ import annotations

import logging
from pathlib import Path

from reqtrace.application.results import TraceabilityResult
from reqtrace.infrastructure.serialization import load_report, save_report

logger = logging.getLogger(__name__)


def export_result_json(result: TraceabilityResult, output_path: str | Path) -> None:
    """Export a traceability run result to JSON."""
    logger.info(
        "Exporting result JSON.",
        extra={"run_id": result.run.id, "output_path": str(output_path)},
    )
    save_report(result, output_path)


def import_result_json(result_path: str | Path) -> TraceabilityResult:
    """Import a traceability run result from JSON."""
    logger.info("Importing result JSON.", extra={"result_path": str(result_path)})
    result = load_report(result_path)
    logger.info(
        "Imported result JSON.",
        extra={"run_id": result.run.id, "method_name": result.run.method_name},
    )
    return result
