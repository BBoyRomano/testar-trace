from __future__ import annotations

from pathlib import Path

import pytest

from reqtrace.application.history_models import RunHistoryEntry
from reqtrace.infrastructure.exceptions import RunHistoryPersistenceError
from reqtrace.infrastructure.persistence.run_history_json import JsonRunHistoryRepository


def test_json_run_history_repository_roundtrip_entries(tmp_path: Path) -> None:
    repository = JsonRunHistoryRepository(tmp_path / ".reqtrace")
    entry = RunHistoryEntry(label="baseline :: run")

    repository.save_entries([entry])
    loaded = repository.load_entries()

    assert len(loaded) == 1
    assert loaded[0].id == entry.id
    assert loaded[0].label == entry.label


def test_json_run_history_repository_roundtrip_result(tmp_path: Path, build_traceability_result) -> None:
    repository = JsonRunHistoryRepository(tmp_path / ".reqtrace")
    result = build_traceability_result(tmp_path)

    saved_path = repository.save_result("entry-1", result)
    loaded = repository.load_result(saved_path)

    assert loaded.run.id == result.run.id
    assert loaded.summary.requirement_count == result.summary.requirement_count


def test_json_run_history_repository_delete_result_is_idempotent(
    tmp_path: Path,
    build_traceability_result,
) -> None:
    repository = JsonRunHistoryRepository(tmp_path / ".reqtrace")
    result = build_traceability_result(tmp_path)

    saved_path = repository.save_result("entry-1", result)
    assert saved_path.exists()

    repository.delete_result(saved_path)
    assert not saved_path.exists()

    # Repeated delete should be a no-op.
    repository.delete_result(saved_path)


def test_json_run_history_repository_raises_for_invalid_index_schema(tmp_path: Path) -> None:
    repository = JsonRunHistoryRepository(tmp_path / ".reqtrace")
    history_path = tmp_path / ".reqtrace" / "history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text('{"entries": [{"label": ""}]}', encoding="utf-8")

    with pytest.raises(RunHistoryPersistenceError):
        repository.load_entries()


def test_json_run_history_repository_raises_when_index_path_is_directory(tmp_path: Path) -> None:
    repository = JsonRunHistoryRepository(tmp_path / ".reqtrace")
    history_path = tmp_path / ".reqtrace" / "history.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.mkdir()

    with pytest.raises(RunHistoryPersistenceError):
        repository.load_entries()


def test_json_run_history_repository_raises_when_base_dir_is_file(tmp_path: Path) -> None:
    blocking_file = tmp_path / ".reqtrace"
    blocking_file.write_text("x", encoding="utf-8")
    repository = JsonRunHistoryRepository(blocking_file)
    entry = RunHistoryEntry(label="baseline :: run")

    with pytest.raises(RunHistoryPersistenceError):
        repository.save_entries([entry])
