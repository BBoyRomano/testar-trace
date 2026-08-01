"""Application service for persisted run history."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from reqtrace.application.exceptions import RunHistoryEntryNotFoundError
from reqtrace.application.history_models import RunHistoryEntry
from reqtrace.application.result_enums import RunStatus
from reqtrace.application.results import TraceabilityResult

logger = logging.getLogger(__name__)


class RunHistoryRepository(Protocol):
    def load_entries(self) -> list[RunHistoryEntry]: ...

    def save_entries(self, entries: list[RunHistoryEntry]) -> None: ...

    def save_result(self, entry_id: str, result: TraceabilityResult) -> Path: ...

    def load_result(self, result_path: str | Path) -> TraceabilityResult: ...

    def delete_result(self, result_path: str | Path) -> None: ...


class RunHistoryService:
    def __init__(self, repository: RunHistoryRepository) -> None:
        self._repository = repository
        self._entries: list[RunHistoryEntry] = list(repository.load_entries())
        self._result_cache: dict[str, TraceabilityResult] = {}
        logger.info(
            "Run history service initialized.",
            extra={"entry_count": len(self._entries)},
        )

    def list_entries(self) -> list[RunHistoryEntry]:
        return list(self._entries)

    def get_entry(self, entry_id: str) -> RunHistoryEntry:
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        logger.warning("Run history entry not found.", extra={"entry_id": entry_id})
        raise RunHistoryEntryNotFoundError(f"Unknown run history entry id: {entry_id}")

    def get_result(self, entry_id: str) -> TraceabilityResult | None:
        cached = self._result_cache.get(entry_id)
        if cached is not None:
            logger.debug("Run history result cache hit.", extra={"entry_id": entry_id})
            return cached
        entry = self.get_entry(entry_id)
        if entry.result_path is None:
            logger.debug("Run history entry has no result path.", extra={"entry_id": entry_id})
            return None
        result = self._repository.load_result(entry.result_path)
        self._result_cache[entry_id] = result
        logger.info(
            "Run history result loaded.",
            extra={"entry_id": entry_id, "result_path": entry.result_path},
        )
        return result

    def create_running_entry(self, *, method_name: str, label: str) -> RunHistoryEntry:
        now = datetime.now(timezone.utc)
        entry = RunHistoryEntry(
            label=label,
            status=RunStatus.RUNNING,
            method_name=method_name,
            created_at=now,
            updated_at=now,
        )
        self._entries.append(entry)
        self._save_entries()
        logger.info(
            "Created running history entry.",
            extra={"entry_id": entry.id, "method_name": method_name},
        )
        return entry

    def mark_completed(self, entry_id: str, result: TraceabilityResult) -> RunHistoryEntry:
        entry = self.get_entry(entry_id)
        result_path = self._repository.save_result(entry.id, result)
        updated = entry.model_copy(
            update={
                "status": RunStatus.COMPLETED,
                "run_id": result.run.id,
                "method_name": result.run.method_name,
                "result_path": str(result_path),
                "error_message": None,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._replace_entry(updated)
        self._result_cache[entry_id] = result
        self._save_entries()
        logger.info(
            "Marked history entry completed.",
            extra={
                "entry_id": entry_id,
                "run_id": result.run.id,
                "method_name": result.run.method_name,
            },
        )
        return updated

    def mark_failed(self, entry_id: str, message: str) -> RunHistoryEntry:
        entry = self.get_entry(entry_id)
        updated = entry.model_copy(
            update={
                "status": RunStatus.FAILED,
                "error_message": message,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._replace_entry(updated)
        self._save_entries()
        logger.error(
            "Marked history entry failed.",
            extra={"entry_id": entry_id, "error_message": message},
        )
        return updated

    def add_imported_result(
        self, *, result: TraceabilityResult, source_path: str | Path
    ) -> RunHistoryEntry:
        now = datetime.now(timezone.utc)
        label = f"imported :: {result.run.method_name} :: {Path(source_path).name}"
        entry = RunHistoryEntry(
            label=label,
            status=RunStatus.COMPLETED,
            method_name=result.run.method_name,
            run_id=result.run.id,
            source_path=str(source_path),
            created_at=now,
            updated_at=now,
        )
        result_path = self._repository.save_result(entry.id, result)
        entry = entry.model_copy(update={"result_path": str(result_path)})
        self._entries.append(entry)
        self._result_cache[entry.id] = result
        self._save_entries()
        logger.info(
            "Added imported result to history.",
            extra={
                "entry_id": entry.id,
                "run_id": result.run.id,
                "source_path": str(source_path),
            },
        )
        return entry

    def delete_entry(self, entry_id: str) -> None:
        entry = self.get_entry(entry_id)
        if entry.result_path:
            self._repository.delete_result(entry.result_path)
        self._entries = [entry for entry in self._entries if entry.id != entry_id]
        self._result_cache.pop(entry_id, None)
        self._save_entries()
        logger.info("Deleted run history entry.", extra={"entry_id": entry_id})

    def _replace_entry(self, updated: RunHistoryEntry) -> None:
        for index, entry in enumerate(self._entries):
            if entry.id == updated.id:
                self._entries[index] = updated
                return
        raise RunHistoryEntryNotFoundError(f"Unknown run history entry id: {updated.id}")

    def _save_entries(self) -> None:
        self._repository.save_entries(self._entries)
        logger.debug(
            "Persisted run history entries.",
            extra={"entry_count": len(self._entries)},
        )
