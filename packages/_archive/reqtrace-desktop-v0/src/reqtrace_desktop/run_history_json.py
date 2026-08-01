"""JSON-backed run history repository for the desktop adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from reqtrace.application.history.models import RunHistoryEntry
from reqtrace.application.results.models import TraceabilityResult
from reqtrace.errors import PersistenceError
from reqtrace.io import load_result, save_result

logger = logging.getLogger(__name__)


class JsonRunHistoryRepository:
    """File-based run history repository used by the desktop app."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)
        self._index_path = self._base_dir / "history.json"
        self._results_dir = self._base_dir / "results"

    def load_entries(self) -> list[RunHistoryEntry]:
        if not self._index_path.exists():
            return []
        try:
            payload = self._index_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error(
                "Failed to read desktop run history index.",
                exc_info=exc,
                extra={"index_path": str(self._index_path)},
            )
            raise PersistenceError(
                f"Could not read run history index from {self._index_path}"
            ) from exc

        try:
            index = RunHistoryIndex.model_validate_json(payload)
        except (ValidationError, ValueError) as exc:
            logger.error(
                "Invalid desktop run history index payload.",
                exc_info=exc,
                extra={"index_path": str(self._index_path)},
            )
            raise PersistenceError(
                f"Invalid run history index schema in {self._index_path}"
            ) from exc
        return index.entries

    def save_entries(self, entries: list[RunHistoryEntry]) -> None:
        try:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            index = RunHistoryIndex(entries=list(entries))
            payload = index.model_dump_json(indent=2)
            temp_path = self._index_path.with_suffix(self._index_path.suffix + ".tmp")
            temp_path.write_text(payload, encoding="utf-8")
            temp_path.replace(self._index_path)
        except OSError as exc:
            logger.error(
                "Failed to save desktop run history index.",
                exc_info=exc,
                extra={"index_path": str(self._index_path)},
            )
            raise PersistenceError(
                f"Could not save run history index to {self._index_path}"
            ) from exc

    def save_result(self, entry_id: str, result: TraceabilityResult) -> Path:
        result_path = self._results_dir / f"{entry_id}.json"
        save_result(result, result_path, format="json")
        return result_path

    def load_result(self, result_path: str | Path) -> TraceabilityResult:
        return load_result(result_path, format="json")

    def delete_result(self, result_path: str | Path) -> None:
        path = Path(result_path)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.error(
                "Failed to delete desktop run history result payload.",
                exc_info=exc,
                extra={"result_path": str(path)},
            )
            raise PersistenceError(
                f"Could not delete run history result payload at {path}"
            ) from exc


class RunHistoryIndex(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[RunHistoryEntry] = Field(default_factory=list)
