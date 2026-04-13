from __future__ import annotations

import importlib
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from reqtrace.application.history_models import RunHistoryEntry
from reqtrace.application.progress import RequirementProgress
from reqtrace.application.result_enums import RunStatus


@pytest.fixture
def controller_cls(monkeypatch):
    fake_tk = types.ModuleType("tkinter")
    fake_tk.END = "end"
    fake_tk.filedialog = types.ModuleType("tkinter.filedialog")
    fake_tk.messagebox = types.ModuleType("tkinter.messagebox")

    fake_views = types.ModuleType("reqtrace.presentation.gui.views")

    class DummyView:
        pass

    fake_views.ReqTraceGuiView = DummyView

    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)
    monkeypatch.setitem(sys.modules, "tkinter.filedialog", fake_tk.filedialog)
    monkeypatch.setitem(sys.modules, "tkinter.messagebox", fake_tk.messagebox)
    monkeypatch.setitem(sys.modules, "reqtrace.presentation.gui.views", fake_views)
    monkeypatch.delitem(sys.modules, "reqtrace.presentation.gui.controller", raising=False)

    module = importlib.import_module("reqtrace.presentation.gui.controller")
    return module.ReqTraceGuiController


def _controller_stub(controller_cls):
    controller = controller_cls.__new__(controller_cls)
    controller._spinner_index = 0
    controller._cancel_requested_entries = set()
    controller._preparing_entries = set()
    controller._pending_requirements = {}
    controller._live_requirement_statuses = {}
    controller._live_progress_meta = {}
    controller._refresh_requested_entries = set()
    return controller


def test_build_analysis_label_prefers_explicit_name(controller_cls) -> None:
    controller = _controller_stub(controller_cls)

    label = controller._build_analysis_label(
        requirements_path=Path("requirements.md"),
        evidence_path=Path("model.json"),
        explicit_name="Manual run label",
    )

    assert label == "Manual run label"


def test_build_analysis_label_falls_back_to_paths(controller_cls) -> None:
    controller = _controller_stub(controller_cls)

    label = controller._build_analysis_label(
        requirements_path=Path("/tmp/data/requirements.md"),
        evidence_path=Path("/tmp/output/model.json"),
    )

    assert label == "requirements.md <- model.json"


@pytest.mark.parametrize(
    ("status", "error_message", "expected_display"),
    [
        (RunStatus.COMPLETED, None, "[OK] completed"),
        (RunStatus.COMPLETED_WITH_ERRORS, None, "[!] completed-with-errors"),
        (RunStatus.PENDING, None, "[ ] pending"),
        (RunStatus.FAILED, "Canceled by user.", "[X] canceled"),
        (RunStatus.FAILED, "Boom", "[X] failed"),
    ],
)
def test_status_display_for_non_running_states(
    controller_cls,
    status: RunStatus,
    error_message: str | None,
    expected_display: str,
) -> None:
    controller = _controller_stub(controller_cls)
    entry = RunHistoryEntry(label="analysis", status=status, error_message=error_message)

    assert controller._status_display(entry) == expected_display


def test_status_display_for_running_state_variants(controller_cls) -> None:
    controller = _controller_stub(controller_cls)
    entry = RunHistoryEntry(label="analysis", status=RunStatus.RUNNING)

    assert controller._status_display(entry) == "[~] running"
    assert controller._status_display(entry, animated=True) == "[|] analyzing"

    controller._preparing_entries.add(entry.id)
    assert controller._status_display(entry) == "[~] preparing"
    assert controller._status_display(entry, animated=True) == "[|] preparing"

    controller._cancel_requested_entries.add(entry.id)
    assert controller._status_display(entry) == "[|] canceling"


def test_run_row_tag_maps_status_and_canceled_failure(controller_cls) -> None:
    controller = _controller_stub(controller_cls)

    assert controller._run_row_tag(RunHistoryEntry(label="a", status=RunStatus.RUNNING)) == "run_running"
    assert controller._run_row_tag(RunHistoryEntry(label="a", status=RunStatus.COMPLETED)) == "run_completed"
    assert (
        controller._run_row_tag(
            RunHistoryEntry(label="a", status=RunStatus.COMPLETED_WITH_ERRORS)
        )
        == "run_warning"
    )
    assert (
        controller._run_row_tag(
            RunHistoryEntry(label="a", status=RunStatus.FAILED, error_message="Canceled by user.")
        )
        == "run_canceled"
    )
    assert controller._run_row_tag(RunHistoryEntry(label="a", status=RunStatus.FAILED)) == "run_failed"


def test_requirement_status_display_helpers(controller_cls) -> None:
    controller = _controller_stub(controller_cls)

    assert controller._requirement_status_display("done") == "[OK] done"
    assert controller._requirement_status_display("failed") == "[X] failed"
    assert controller._live_requirement_status_display("waiting") == "[ ] waiting"
    assert controller._live_requirement_status_display("processing") == "[|] analyzing"
    assert controller._live_requirement_status_display("completed") == "[OK] done"
    assert controller._live_requirement_status_display("failed") == "[X] failed"


@pytest.mark.parametrize(
    ("status_value", "expected_tag"),
    [
        ("waiting", "req_waiting"),
        ("processing", "req_processing"),
        ("completed", "req_completed"),
        ("failed", "req_failed"),
    ],
)
def test_live_requirement_row_tag(controller_cls, status_value: str, expected_tag: str) -> None:
    controller = _controller_stub(controller_cls)
    assert controller._live_requirement_row_tag(status_value) == expected_tag


@pytest.mark.parametrize(
    ("status_value", "expected_tag"),
    [("done", "req_completed"), ("failed", "req_failed")],
)
def test_final_requirement_row_tag(controller_cls, status_value: str, expected_tag: str) -> None:
    controller = _controller_stub(controller_cls)
    assert controller._final_requirement_row_tag(status_value) == expected_tag


def test_timestamp_display_converts_to_utc(controller_cls) -> None:
    controller = _controller_stub(controller_cls)
    plus_two = timezone(timedelta(hours=2))
    local = datetime(2026, 1, 1, 12, 0, tzinfo=plus_two)

    assert controller._timestamp_display(local) == "2026-01-01 10:00:00"


def test_duration_display_formats_elapsed_seconds(
    controller_cls,
    build_traceability_result,
    tmp_path,
) -> None:
    controller = _controller_stub(controller_cls)
    result = build_traceability_result(tmp_path)

    assert controller._duration_display(result).endswith("s")


def test_duration_display_returns_na_for_open_run(
    controller_cls,
    build_traceability_result,
    tmp_path,
) -> None:
    controller = _controller_stub(controller_cls)
    result = build_traceability_result(tmp_path)
    no_end_run = result.run.model_copy(update={"ended_at": None})
    open_result = result.model_copy(update={"run": no_end_run})

    assert controller._duration_display(open_result) == "n/a"


def test_apply_progress_update_tracks_live_status_and_meta(controller_cls) -> None:
    controller = _controller_stub(controller_cls)
    entry_id = "entry-1"
    progress = RequirementProgress(
        requirement_id="REQ-1",
        requirement_title="Login",
        state="processing",
        processed_requirement_count=0,
        total_requirement_count=2,
        phase="baseline",
        message="Loading",
    )

    controller._apply_progress_update(entry_id, progress)

    assert controller._live_requirement_statuses[entry_id]["REQ-1"] == "processing"
    assert controller._pending_requirements[entry_id] == [("REQ-1", "Login")]
    assert controller._live_progress_meta[entry_id]["processed"] == 0
    assert controller._live_progress_meta[entry_id]["total"] == 2
    assert controller._live_progress_meta[entry_id]["phase"] == "baseline"
    assert controller._live_progress_meta[entry_id]["message"] == "Loading"
    assert entry_id in controller._refresh_requested_entries


def test_apply_progress_update_does_not_duplicate_pending_requirement(controller_cls) -> None:
    controller = _controller_stub(controller_cls)
    entry_id = "entry-1"
    first = RequirementProgress(
        requirement_id="REQ-1",
        requirement_title="Login",
        state="processing",
        processed_requirement_count=0,
        total_requirement_count=1,
        phase="baseline",
    )
    second = RequirementProgress(
        requirement_id="REQ-1",
        requirement_title="Login",
        state="completed",
        processed_requirement_count=1,
        total_requirement_count=1,
        phase="baseline",
    )

    controller._apply_progress_update(entry_id, first)
    controller._apply_progress_update(entry_id, second)

    assert controller._pending_requirements[entry_id] == [("REQ-1", "Login")]
    assert controller._live_requirement_statuses[entry_id]["REQ-1"] == "completed"
