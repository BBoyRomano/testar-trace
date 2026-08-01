from __future__ import annotations

from pathlib import Path

import pytest

from reqtrace.application.exceptions import RunHistoryEntryNotFoundError
from reqtrace.application.history_models import RunHistoryEntry
from reqtrace.application.result_enums import RunStatus
from reqtrace.application.results import TraceabilityResult
from reqtrace.application.services.run_history_service import RunHistoryService


class InMemoryRunHistoryRepository:
    def __init__(self) -> None:
        self.entries: list[RunHistoryEntry] = []
        self.results: dict[str, TraceabilityResult] = {}

    def load_entries(self) -> list[RunHistoryEntry]:
        return list(self.entries)

    def save_entries(self, entries: list[RunHistoryEntry]) -> None:
        self.entries = list(entries)

    def save_result(self, entry_id: str, result: TraceabilityResult) -> Path:
        self.results[entry_id] = result
        return Path(f"/virtual/{entry_id}.json")

    def load_result(self, result_path: str | Path) -> TraceabilityResult:
        entry_id = Path(result_path).stem
        return self.results[entry_id]

    def delete_result(self, result_path: str | Path) -> None:
        entry_id = Path(result_path).stem
        self.results.pop(entry_id, None)


def test_run_history_tracks_running_completed_and_result_lookup(
    tmp_path: Path,
    build_traceability_result,
) -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    entry = service.create_running_entry(method_name="baseline", label="baseline :: run")
    assert entry.status == RunStatus.RUNNING

    result = build_traceability_result(tmp_path)
    completed = service.mark_completed(entry.id, result)

    assert completed.status == RunStatus.COMPLETED
    assert completed.run_id == result.run.id
    assert service.get_result(entry.id) is not None


def test_run_history_get_result_returns_none_without_result_path() -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    entry = service.create_running_entry(method_name="baseline", label="baseline :: run")
    assert service.get_result(entry.id) is None


def test_run_history_loads_existing_entries_from_repository() -> None:
    repository = InMemoryRunHistoryRepository()
    repository.entries = [RunHistoryEntry(label="preloaded")]
    service = RunHistoryService(repository)
    entries = service.list_entries()
    assert len(entries) == 1
    assert entries[0].label == "preloaded"


def test_run_history_tracks_failed_entry() -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    entry = service.create_running_entry(method_name="baseline", label="baseline :: run")
    failed = service.mark_failed(entry.id, "boom")

    assert failed.status == RunStatus.FAILED
    assert failed.error_message == "boom"


def test_run_history_add_imported_result(tmp_path: Path, build_traceability_result) -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    result = build_traceability_result(tmp_path)
    imported = service.add_imported_result(result=result, source_path="/tmp/result.json")

    assert imported.status == RunStatus.COMPLETED
    assert imported.source_path == "/tmp/result.json"
    assert service.get_result(imported.id) is not None


def test_run_history_raises_for_unknown_entry() -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    with pytest.raises(RunHistoryEntryNotFoundError):
        service.get_entry("missing")


def test_run_history_mark_completed_raises_for_unknown_entry(
    tmp_path: Path,
    build_traceability_result,
) -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    result = build_traceability_result(tmp_path)
    with pytest.raises(RunHistoryEntryNotFoundError):
        service.mark_completed("missing", result)


def test_run_history_delete_entry_removes_history_and_cached_result(
    tmp_path: Path,
    build_traceability_result,
) -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    entry = service.create_running_entry(method_name="baseline", label="baseline :: run")
    result = build_traceability_result(tmp_path)
    service.mark_completed(entry.id, result)
    assert service.get_result(entry.id) is not None

    service.delete_entry(entry.id)

    with pytest.raises(RunHistoryEntryNotFoundError):
        service.get_entry(entry.id)


def test_run_history_preserves_user_label_on_completion_and_failure(
    tmp_path: Path,
    build_traceability_result,
) -> None:
    service = RunHistoryService(InMemoryRunHistoryRepository())
    entry = service.create_running_entry(method_name="baseline", label="My analysis label")
    result = build_traceability_result(tmp_path)

    completed = service.mark_completed(entry.id, result)
    assert completed.label == "My analysis label"

    failed_entry = service.create_running_entry(method_name="baseline", label="Failure label")
    failed = service.mark_failed(failed_entry.id, "boom")
    assert failed.label == "Failure label"
