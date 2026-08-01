from __future__ import annotations

import logging
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from threading import Event
from time import monotonic
from tkinter import filedialog, messagebox

from reqtrace._api_types import parse_trace_method_name
from reqtrace.application.execution.async_executor import AsyncRunExecutor
from reqtrace.application.history.models import RunHistoryEntry
from reqtrace.application.history.service import RunHistoryService
from reqtrace.application.progress import RequirementProgress
from reqtrace.application.results.enums import RunStatus
from reqtrace.application.results.models import TraceabilityResult
from reqtrace.application.execution.orchestrator import (
    build_default_orchestrator,
)
from reqtrace import (
    TraceRequest,
    load_result,
    save_result,
)
from reqtrace.errors import InputError
from reqtrace.formats import detect_evidence, detect_requirements
from reqtrace_desktop.run_history_json import JsonRunHistoryRepository
from reqtrace_desktop.run_preparation import (
    PREPARATION_CANCELED_MESSAGE,
    PreparationEvent,
    prepare_and_submit_run,
)
from reqtrace_desktop.status_formatting import (
    duration_display,
    final_requirement_row_tag,
    live_requirement_row_tag,
    live_requirement_status_display,
    requirement_status_display,
    run_row_tag,
    status_display,
    timestamp_display,
)
from reqtrace_desktop.state_store import DesktopStateStore
from reqtrace_desktop.view import ReqTraceDesktopView

logger = logging.getLogger(__name__)


class ReqTraceDesktopController:
    _SPINNER_FRAMES = ("|", "/", "-", "\\")
    _RUNNING_REFRESH_INTERVAL_SECONDS = 0.35
    _UNSET_FORMAT_LABEL = "not detected"

    def __init__(self) -> None:
        self._service = build_default_orchestrator()
        self._executor = AsyncRunExecutor(self._service, execution_backend="process")
        self._prepare_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="reqtrace-prepare",
        )
        self._state_root = Path.cwd() / ".reqtrace"
        self._state_store = DesktopStateStore(self._state_root)
        self._ui_state = self._load_ui_state()
        self._history = RunHistoryService(
            JsonRunHistoryRepository(self._state_root / "desktop-history")
        )
        self._prepare_events: Queue[PreparationEvent] = Queue()
        self._prepare_futures: dict[str, Future[None]] = {}
        self._prepare_cancel_flags: dict[str, Event] = {}
        self._preparing_entries: set[str] = set()
        self._job_to_entry: dict[str, str] = {}
        self._entry_to_job: dict[str, str] = {}
        self._pending_requirements: dict[str, list[tuple[str, str]]] = {}
        self._live_requirement_statuses: dict[str, dict[str, str]] = {}
        self._live_progress_meta: dict[str, dict[str, object]] = {}
        self._cancel_requested_entries: set[str] = set()
        self._refresh_requested_entries: set[str] = set()
        self._last_running_refresh_at = 0.0
        self._spinner_index = 0
        self._closing = False

        self.view = ReqTraceDesktopView(
            methods=self._service.available_methods(),
            on_requirements_path_changed=self._on_requirements_path_changed,
            on_evidence_path_changed=self._on_evidence_path_changed,
            on_browse_requirements_file=self._browse_requirements_file,
            on_browse_requirements_dir=self._browse_requirements_dir,
            on_browse_evidence_file=self._browse_evidence_file,
            on_browse_evidence_dir=self._browse_evidence_dir,
            on_start_run=self._start_run,
            on_cancel_selected=self._cancel_selected,
            on_delete_selected=self._delete_selected,
            on_import_result=self._import_result,
            on_export_selected=self._export_selected,
            on_run_selected=self._refresh_selected_run,
            on_requirement_selected=self._refresh_requirement_detail,
        )
        self.view.root.protocol("WM_DELETE_WINDOW", self._on_close)

        for entry in self._history.list_entries():
            self._upsert_entry_row(entry)
        self._restore_ui_state()
        self._refresh_detected_formats()

        self.view.root.after(150, self._poll_executor)
        self.view.root.after(180, self._animate_running_state)
        logger.info(
            "Desktop controller initialized.",
            extra={"history_entry_count": len(self._history.list_entries())},
        )

    def run(self) -> None:
        self.view.run()

    def _show_view_panel(self, method_name: str) -> None:
        method = getattr(self.view, method_name, None)
        if callable(method):
            method()

    def _on_close(self) -> None:
        self._closing = True
        self._save_ui_state()
        for cancel_flag in self._prepare_cancel_flags.values():
            cancel_flag.set()
        self._prepare_executor.shutdown(wait=False, cancel_futures=True)
        self._executor.shutdown(wait=False)
        logger.info("Desktop controller shutdown.")
        self.view.root.destroy()

    def _on_requirements_path_changed(self) -> None:
        self._refresh_requirements_format_detected()

    def _on_evidence_path_changed(self) -> None:
        self._refresh_evidence_format_detected()

    def _refresh_detected_formats(self) -> None:
        self._refresh_requirements_format_detected()
        self._refresh_evidence_format_detected()

    def _refresh_requirements_format_detected(self) -> None:
        detected = self._infer_requirements_format_label(
            self.view.requirements_path_var.get()
        )
        self.view.requirements_format_detected_var.set(detected)

    def _refresh_evidence_format_detected(self) -> None:
        detected = self._infer_evidence_format_label(
            self.view.evidence_path_var.get()
        )
        self.view.evidence_format_detected_var.set(detected)

    def _infer_requirements_format_label(self, path_text: str) -> str:
        normalized = path_text.strip()
        if not normalized:
            return self._UNSET_FORMAT_LABEL
        path = Path(normalized)
        if not path.exists():
            return "unknown (path not found)"
        try:
            detected = detect_requirements([path])
        except InputError as exc:
            return f"unknown ({self._truncate_text(str(exc), 110)})"
        return f"{detected} (auto)"

    def _infer_evidence_format_label(self, path_text: str) -> str:
        normalized = path_text.strip()
        if not normalized:
            return self._UNSET_FORMAT_LABEL
        path = Path(normalized)
        if not path.exists():
            return "unknown (path not found)"
        try:
            detected = detect_evidence(path)
        except InputError as exc:
            return f"unknown ({self._truncate_text(str(exc), 110)})"
        return f"{detected} (auto)"

    @staticmethod
    def _truncate_text(value: str, limit: int) -> str:
        normalized = value.strip()
        if len(normalized) <= limit:
            return normalized
        if limit <= 3:
            return normalized[:limit]
        return f"{normalized[: limit - 3]}..."

    def _restore_ui_state(self) -> None:
        requirements_path = str(self._ui_state.get("requirements_path", "")).strip()
        evidence_path = str(self._ui_state.get("evidence_path", "")).strip()
        if requirements_path:
            self.view.requirements_path_var.set(requirements_path)
        if evidence_path:
            self.view.evidence_path_var.set(evidence_path)

    def _load_ui_state(self) -> dict[str, str]:
        return self._state_store.load()

    def _save_ui_state(self) -> None:
        requirements_path = self.view.requirements_path_var.get().strip()
        evidence_path = self.view.evidence_path_var.get().strip()
        payload = {
            "requirements_path": requirements_path,
            "evidence_path": evidence_path,
            "last_requirements_dir": self._derive_last_dir(
                preferred_path=requirements_path,
                fallback_key="last_requirements_dir",
            ),
            "last_evidence_dir": self._derive_last_dir(
                preferred_path=evidence_path,
                fallback_key="last_evidence_dir",
            ),
        }
        self._ui_state = payload
        self._state_store.save(payload)

    def _derive_last_dir(self, *, preferred_path: str, fallback_key: str) -> str:
        fallback_value = str(self._ui_state.get(fallback_key, ""))
        return self._state_store.derive_last_dir(
            preferred_path=preferred_path,
            fallback=fallback_value,
        )

    def _dialog_initialdir(self, *, current_value: str, fallback_key: str) -> str:
        fallback_value = str(self._ui_state.get(fallback_key, ""))
        return self._state_store.dialog_initial_dir(
            current_value=current_value,
            fallback=fallback_value,
        )

    def _browse_requirements_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select requirements file",
            initialdir=self._dialog_initialdir(
                current_value=self.view.requirements_path_var.get(),
                fallback_key="last_requirements_dir",
            ),
            filetypes=[
                ("Requirements files", "*.md *.json"),
                ("Markdown files", "*.md"),
                ("JSON files", "*.json"),
                ("All files", "*"),
            ],
        )
        if selected:
            self.view.requirements_path_var.set(selected)
            self._ui_state["last_requirements_dir"] = str(Path(selected).parent)
            self._save_ui_state()

    def _browse_requirements_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Select requirements directory",
            initialdir=self._dialog_initialdir(
                current_value=self.view.requirements_path_var.get(),
                fallback_key="last_requirements_dir",
            ),
        )
        if selected:
            self.view.requirements_path_var.set(selected)
            self._ui_state["last_requirements_dir"] = selected
            self._save_ui_state()

    def _browse_evidence_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select TESTAR Evidence file",
            initialdir=self._dialog_initialdir(
                current_value=self.view.evidence_path_var.get(),
                fallback_key="last_evidence_dir",
            ),
            filetypes=[
                ("TESTAR model", "model.json"),
                ("JSON files", "*.json"),
                ("All files", "*"),
            ],
        )
        if selected:
            self.view.evidence_path_var.set(selected)
            self._ui_state["last_evidence_dir"] = str(Path(selected).parent)
            self._save_ui_state()

    def _browse_evidence_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Select TESTAR Evidence directory",
            initialdir=self._dialog_initialdir(
                current_value=self.view.evidence_path_var.get(),
                fallback_key="last_evidence_dir",
            ),
        )
        if selected:
            self.view.evidence_path_var.set(selected)
            self._ui_state["last_evidence_dir"] = selected
            self._save_ui_state()

    def _start_run(self) -> None:
        requirements_text = self.view.requirements_path_var.get().strip()
        evidence_text = self.view.evidence_path_var.get().strip()
        if not requirements_text or not evidence_text:
            logger.warning("Desktop run start rejected due to missing input paths.")
            messagebox.showerror(
                "ReqTrace",
                "Select a requirements source and a Evidence source before starting.",
            )
            return

        requirements_path = Path(requirements_text)
        try:
            resolved_requirements_format = detect_requirements([requirements_path])
            resolved_evidence_format = detect_evidence(Path(evidence_text))
        except InputError as exc:
            logger.warning(
                "Desktop format inference failed.",
                extra={"error_message": str(exc)},
            )
            messagebox.showerror("ReqTrace", str(exc))
            return

        try:
            method_name = parse_trace_method_name(self.view.method_var.get())
            trace_request = TraceRequest(
                requirements_paths=[requirements_path],
                evidence_path=Path(evidence_text),
                requirements_format=resolved_requirements_format,
                evidence_format=resolved_evidence_format,
                method_name=method_name,
            )
        except ValueError as exc:
            logger.warning(
                "Desktop method selection validation failed.",
                extra={"error_message": str(exc)},
            )
            messagebox.showerror("ReqTrace", str(exc))
            return

        self._save_ui_state()

        entry = self._history.create_running_entry(
            method_name=self.view.method_var.get(),
            label=self._build_analysis_label(
                requirements_path=Path(requirements_text),
                evidence_path=Path(evidence_text),
                explicit_name=self.view.analysis_name_var.get().strip(),
            ),
        )
        self._pending_requirements[entry.id] = []
        self._live_requirement_statuses[entry.id] = {}
        self._live_progress_meta[entry.id] = {
            "processed": 0,
            "total": 0,
            "phase": "preparing",
            "message": "Loading requirements and Evidence.",
        }
        self._preparing_entries.add(entry.id)
        self._prepare_cancel_flags[entry.id] = Event()
        self._upsert_entry_row(entry)
        self._select_entry(entry.id)
        self._refresh_selected_run()
        self._show_view_panel("show_overview")

        future = self._prepare_executor.submit(
            prepare_and_submit_run,
            entry.id,
            trace_request,
            self._prepare_cancel_flags[entry.id],
            executor=self._executor,
            events_queue=self._prepare_events,
        )
        self._prepare_futures[entry.id] = future
        logger.info(
            "Desktop run preparation submitted.",
            extra={"entry_id": entry.id, "method_name": trace_request.method_name},
        )

    def _drain_preparation_events(self) -> None:
        selected = self._selected_history_entry()
        selected_entry_id = selected.id if selected is not None else None
        while True:
            try:
                event = self._prepare_events.get_nowait()
            except Empty:
                break

            if event.kind == "prepared":
                requirements = list(event.requirements or [])
                self._pending_requirements[event.entry_id] = requirements
                self._live_requirement_statuses[event.entry_id] = {
                    requirement_id: "waiting" for requirement_id, _title in requirements
                }
                self._live_progress_meta[event.entry_id] = {
                    "processed": 0,
                    "total": len(requirements),
                    "phase": event.phase or "analyzing",
                    "message": "Prepared. Waiting for execution.",
                }
                self._refresh_requested_entries.add(event.entry_id)
                continue

            if event.kind == "submitted":
                if event.job_id is None:
                    continue
                self._preparing_entries.discard(event.entry_id)
                self._prepare_cancel_flags.pop(event.entry_id, None)
                self._prepare_futures.pop(event.entry_id, None)
                self._entry_to_job[event.entry_id] = event.job_id
                self._job_to_entry[event.job_id] = event.entry_id
                logger.info(
                    "Desktop run submitted.",
                    extra={"entry_id": event.entry_id, "job_id": event.job_id},
                )
                if event.entry_id in self._cancel_requested_entries:
                    self._executor.cancel(event.job_id)
                self._refresh_requested_entries.add(event.entry_id)
                continue

            if event.kind == "failed":
                self._preparing_entries.discard(event.entry_id)
                self._prepare_cancel_flags.pop(event.entry_id, None)
                self._prepare_futures.pop(event.entry_id, None)
                self._entry_to_job.pop(event.entry_id, None)
                self._pending_requirements.pop(event.entry_id, None)
                self._live_requirement_statuses.pop(event.entry_id, None)
                self._live_progress_meta.pop(event.entry_id, None)
                self._cancel_requested_entries.discard(event.entry_id)
                self._refresh_requested_entries.discard(event.entry_id)
                message = event.message or "Could not prepare run."
                entry = self._history.mark_failed(event.entry_id, message)
                self._upsert_entry_row(entry)
                self._refresh_requested_entries.add(event.entry_id)

        if (
            selected_entry_id is not None
            and selected_entry_id in self._refresh_requested_entries
        ):
            self._refresh_requested_entries.discard(selected_entry_id)
            self._refresh_selected_run()

    def _cancel_selected(self) -> None:
        entry = self._selected_history_entry()
        if entry is None:
            messagebox.showinfo("ReqTrace", "Select a running analysis to cancel.")
            return
        if entry.status != RunStatus.RUNNING:
            messagebox.showinfo("ReqTrace", "Selected analysis is not running.")
            return

        job_id = self._entry_to_job.get(entry.id)
        if job_id is None:
            if entry.id in self._preparing_entries:
                self._cancel_requested_entries.add(entry.id)
                future = self._prepare_futures.get(entry.id)
                if future is not None and future.cancel():
                    self._prepare_events.put(
                        PreparationEvent(
                            entry_id=entry.id,
                            kind="failed",
                            message=PREPARATION_CANCELED_MESSAGE,
                        )
                    )
                else:
                    cancel_flag = self._prepare_cancel_flags.get(entry.id)
                    if cancel_flag is not None:
                        cancel_flag.set()
                self._refresh_selected_run()
                return
            messagebox.showinfo(
                "ReqTrace", "No active worker was found for the selected analysis."
            )
            return

        canceled = self._executor.cancel(job_id)
        if canceled:
            self._cancel_requested_entries.add(entry.id)
            logger.info(
                "Desktop cancellation requested.",
                extra={"job_id": job_id, "entry_id": entry.id},
            )
            self._refresh_selected_run()
            return

        messagebox.showinfo(
            "ReqTrace",
            "Could not cancel the selected analysis.\nIt may have already finished.",
        )

    def _delete_selected(self) -> None:
        entry = self._selected_history_entry()
        if entry is None:
            messagebox.showinfo("ReqTrace", "Select an analysis to delete.")
            return
        if entry.status == RunStatus.RUNNING:
            messagebox.showinfo(
                "ReqTrace", "Cancel the running analysis before deleting it."
            )
            return

        confirmed = messagebox.askyesno(
            "ReqTrace",
            "Delete selected analysis from history?\n"
            "Stored result data for that run will no longer be shown in the dashboard.",
        )
        if not confirmed:
            return

        self._history.delete_entry(entry.id)
        self._job_to_entry = {
            job_id: item
            for job_id, item in self._job_to_entry.items()
            if item != entry.id
        }
        self._entry_to_job.pop(entry.id, None)
        self._pending_requirements.pop(entry.id, None)
        self._live_requirement_statuses.pop(entry.id, None)
        self._live_progress_meta.pop(entry.id, None)
        self._cancel_requested_entries.discard(entry.id)
        self._refresh_requested_entries.discard(entry.id)
        self._preparing_entries.discard(entry.id)
        self._prepare_futures.pop(entry.id, None)
        self._prepare_cancel_flags.pop(entry.id, None)
        if self.view.runs_table.exists(entry.id):
            self.view.runs_table.delete(entry.id)
        self._refresh_selected_run()

    def _import_result(self) -> None:
        selected = filedialog.askopenfilename(
            title="Import result JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*")],
        )
        if not selected:
            return
        result_path = Path(selected)
        try:
            result = load_result(result_path)
            entry = self._history.add_imported_result(
                result=result, source_path=result_path
            )
        except Exception as exc:  # pragma: no cover
            logger.error("Desktop result import failed.", exc_info=exc)
            messagebox.showerror("ReqTrace", f"Could not import result:\n{exc}")
            return

        self._upsert_entry_row(entry)
        self._select_entry(entry.id)
        logger.info(
            "Desktop result imported.",
            extra={"entry_id": entry.id, "run_id": result.run.id},
        )
        self._refresh_selected_run()

    def _export_selected(self) -> None:
        entry = self._selected_history_entry()
        if entry is None:
            logger.debug("Desktop export requested with no selected entry.")
            messagebox.showinfo(
                "ReqTrace", "Select a completed or imported analysis first."
            )
            return

        result = self._history.get_result(entry.id)
        if result is None:
            logger.warning(
                "Desktop export requested for entry with no result.",
                extra={"entry_id": entry.id},
            )
            messagebox.showinfo(
                "ReqTrace", "Selected analysis has no result payload to export."
            )
            return

        selected = filedialog.asksaveasfilename(
            title="Export result JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not selected:
            return
        save_result(result, Path(selected))
        logger.info(
            "Desktop result exported.",
            extra={
                "entry_id": entry.id,
                "run_id": result.run.id,
                "output_path": selected,
            },
        )
        messagebox.showinfo("ReqTrace", f"Saved result to {selected}")

    def _poll_executor(self) -> None:
        try:
            self._drain_preparation_events()
            for event in self._executor.drain_events():
                if event.status == RunStatus.RUNNING:
                    if event.progress is not None:
                        entry_id = self._job_to_entry.get(event.job_id)
                        if entry_id is not None:
                            self._apply_progress_update(entry_id, event.progress)
                    continue
                entry_id = self._job_to_entry.pop(event.job_id, None)
                if entry_id is None:
                    logger.warning(
                        "Received async event for unknown job.",
                        extra={"job_id": event.job_id, "status": str(event.status)},
                    )
                    continue
                self._entry_to_job.pop(entry_id, None)
                self._pending_requirements.pop(entry_id, None)
                self._live_requirement_statuses.pop(entry_id, None)
                self._live_progress_meta.pop(entry_id, None)
                self._cancel_requested_entries.discard(entry_id)
                self._refresh_requested_entries.discard(entry_id)
                self._preparing_entries.discard(entry_id)
                self._prepare_futures.pop(entry_id, None)
                self._prepare_cancel_flags.pop(entry_id, None)

                if event.status == RunStatus.COMPLETED and event.result is not None:
                    entry = self._history.mark_completed(entry_id, event.result)
                    logger.info(
                        "Desktop observed run completion.",
                        extra={"job_id": event.job_id, "entry_id": entry_id},
                    )
                else:
                    message = event.error_message or "Analysis failed."
                    entry = self._history.mark_failed(entry_id, message)
                    logger.error(
                        "Desktop observed run failure.",
                        extra={
                            "job_id": event.job_id,
                            "entry_id": entry_id,
                            "error_message": message,
                        },
                    )
                self._upsert_entry_row(entry)
                self._refresh_selected_run()
        finally:
            if not self._closing:
                self.view.root.after(150, self._poll_executor)

    def _upsert_entry_row(self, entry: RunHistoryEntry) -> None:
        values = (
            entry.label,
            self._status_display(entry),
            entry.method_name,
            self._timestamp_display(entry.updated_at),
        )
        tags = (self._run_row_tag(entry),)
        if self.view.runs_table.exists(entry.id):
            self.view.runs_table.item(entry.id, values=values, tags=tags)
            return
        self.view.runs_table.insert("", tk.END, iid=entry.id, values=values, tags=tags)
        logger.debug("Desktop history entry upserted.", extra={"entry_id": entry.id})

    def _select_entry(self, entry_id: str) -> None:
        if not self.view.runs_table.exists(entry_id):
            return
        self.view.runs_table.selection_set(entry_id)
        self.view.runs_table.focus(entry_id)

    def _selected_history_entry(self) -> RunHistoryEntry | None:
        selection = self.view.runs_table.selection()
        if not selection:
            return None
        entry_id = selection[0]
        try:
            return self._history.get_entry(entry_id)
        except Exception as exc:  # pragma: no cover - defensive boundary
            logger.error("Failed to load selected history entry.", exc_info=exc)
            return None

    def _selected_result(
        self,
    ) -> tuple[RunHistoryEntry | None, TraceabilityResult | None]:
        entry = self._selected_history_entry()
        if entry is None:
            return None, None
        try:
            return entry, self._history.get_result(entry.id)
        except Exception as exc:
            logger.error(
                "Desktop failed to load selected run result.",
                exc_info=exc,
                extra={"entry_id": entry.id},
            )
            return entry, None

    def _refresh_selected_run(self) -> None:
        entry, result = self._selected_result()
        self._show_view_panel("show_overview")
        self._set_insight_rows([])
        for item in self.view.requirement_table.get_children():
            self.view.requirement_table.delete(item)
        self.view.detail_text.delete("1.0", tk.END)
        self.view.clear_metrics()

        if entry is None:
            return

        if result is None:
            self.view.metric_method_var.set(entry.method_name)
            self.view.metric_status_var.set(self._status_display(entry))
            if entry.status == RunStatus.RUNNING:
                self._render_running_placeholders(entry)
            else:
                self._render_non_result_placeholders(entry)
            return

        self.view.metric_run_id_var.set(result.run.id)
        self.view.metric_method_var.set(result.run.method_name)
        self.view.metric_status_var.set(str(result.run.status))
        self.view.metric_duration_var.set(self._duration_display(result))
        self.view.metric_requirements_var.set(str(result.summary.requirement_count))
        self.view.metric_coverage_var.set(
            f"{100.0 * result.summary.global_coverage.overall_coverage_ratio:.1f}%"
        )
        self.view.metric_links_var.set(str(result.summary.trace_link_count))
        self.view.metric_confidence_var.set(
            f"{100.0 * result.summary.global_coverage.average_confidence:.1f}%"
        )
        self.view.metric_progress_var.set(100.0)
        self.view.metric_progress_text_var.set("100%")
        self.view.insight_summary_var.set("Completed")

        coverage = result.summary.global_coverage
        self._set_insight_rows(
            [
                ("Coverage: full", str(coverage.fully_covered)),
                ("Coverage: main-only", str(coverage.main_only)),
                ("Coverage: alt-only", str(coverage.alt_only)),
                ("Coverage: partial", str(coverage.partial)),
                ("Coverage: uncovered", str(coverage.none)),
                ("Coverage: uncertain", str(coverage.uncertain)),
                (
                    "Traceability",
                    (
                        f"{coverage.requirements_with_any_trace}/{coverage.total_requirements} "
                        f"(main {coverage.requirements_with_main_trace}, "
                        f"alt {coverage.requirements_with_alt_trace})"
                    ),
                ),
                ("Trace items", str(result.summary.trace_evidence_count)),
            ]
        )

        for item in result.requirement_results:
            coverage = str(item.coverage.status)
            self.view.requirement_table.insert(
                "",
                tk.END,
                iid=item.requirement_id,
                text=f"{item.requirement_id}: {item.requirement_title}",
                values=(
                    self._requirement_status_display(item.status.value),
                    coverage,
                    len(item.trace_links),
                    len(item.trace_evidence),
                ),
                tags=(self._final_requirement_row_tag(item.status.value),),
            )

    def _refresh_requirement_detail(self) -> None:
        self.view.detail_text.delete("1.0", tk.END)
        _entry, result = self._selected_result()
        if result is None:
            return
        selection = self.view.requirement_table.selection()
        if not selection:
            return
        self._show_view_panel("show_detail")
        requirement_id = selection[0]
        for item in result.requirement_results:
            if item.requirement_id != requirement_id:
                continue
            lines = [
                f"Requirement ID: {item.requirement_id}",
                f"Title: {item.requirement_title}",
                f"Status: {item.status}",
                f"Coverage: {item.coverage.status}",
                f"Main flow: {item.coverage.main_flow_status}",
                f"Alternative flow: {item.coverage.alt_flow_status}",
                f"Confidence: {item.coverage.confidence:.3f}",
                f"Trace links: {len(item.trace_links)}",
                f"Trace items: {len(item.trace_evidence)}",
                f"Warnings: {len(item.warnings)}",
            ]
            if item.error_message:
                lines.append(f"Error: {item.error_message}")
            self.view.detail_text.insert(tk.END, "\n".join(lines))
            return

    def _apply_progress_update(
        self, entry_id: str, progress: RequirementProgress
    ) -> None:
        statuses = self._live_requirement_statuses.setdefault(entry_id, {})
        statuses[progress.requirement_id] = progress.state

        pending_requirements = self._pending_requirements.setdefault(entry_id, [])
        if progress.requirement_id not in {item[0] for item in pending_requirements}:
            pending_requirements.append(
                (progress.requirement_id, progress.requirement_title)
            )

        self._live_progress_meta[entry_id] = {
            "processed": progress.processed_requirement_count,
            "total": progress.total_requirement_count,
            "phase": progress.phase,
            "message": progress.message,
        }
        self._refresh_requested_entries.add(entry_id)

    def _render_running_placeholders(self, entry: RunHistoryEntry) -> None:
        spinner = self._spinner_frame()
        pending_requirements = self._pending_requirements.get(entry.id, [])
        progress_meta = self._live_progress_meta.get(entry.id, {})
        processed_count = self._coerce_int(progress_meta.get("processed"), default=0)
        total_count = self._coerce_int(
            progress_meta.get("total"),
            default=len(pending_requirements),
        )
        current_phase = str(progress_meta.get("phase") or entry.method_name)
        current_message = progress_meta.get("message")
        elapsed_seconds = (
            datetime.now(tz=entry.created_at.tzinfo) - entry.created_at
        ).total_seconds()

        self.view.metric_run_id_var.set(f"{spinner} pending")
        self.view.metric_duration_var.set(f"{elapsed_seconds:.1f}s")
        if total_count:
            self.view.metric_requirements_var.set(f"{processed_count}/{total_count}")
        else:
            self.view.metric_requirements_var.set(f"{spinner} scanning")
        progress_percentage = (
            (processed_count / total_count * 100.0) if total_count else 0.0
        )
        self.view.metric_progress_var.set(progress_percentage)
        if total_count:
            self.view.metric_progress_text_var.set(f"{progress_percentage:.0f}%")
        else:
            self.view.metric_progress_text_var.set(f"{spinner} scanning")
        self.view.metric_coverage_var.set(f"{spinner} processing")
        self.view.metric_links_var.set(f"{spinner}")
        self.view.metric_confidence_var.set(f"{spinner} processing")
        self.view.insight_summary_var.set(
            f"{self._status_display(entry, animated=True)} | {current_phase}"
        )

        rows = [
            ("Analysis", entry.label),
            ("Phase", current_phase),
            ("Progress", f"{processed_count}/{total_count}"),
            ("Status", "Metrics and trace links appear when the run finishes."),
        ]
        if entry.id in self._cancel_requested_entries:
            rows.append(("Cancellation", "Requested. Finishing current step."))
        if isinstance(current_message, str) and current_message:
            rows.append(("Message", current_message))
        self._set_insight_rows(rows)

        if total_count == 0:
            return

        live_statuses = self._live_requirement_statuses.get(entry.id, {})
        for requirement_id, requirement_title in pending_requirements:
            status = self._live_requirement_status_display(
                live_statuses.get(requirement_id, "waiting")
            )
            self.view.requirement_table.insert(
                "",
                tk.END,
                iid=requirement_id,
                text=f"{requirement_id}: {requirement_title}",
                values=(status, "-", 0, 0),
                tags=(
                    self._live_requirement_row_tag(
                        live_statuses.get(requirement_id, "waiting")
                    ),
                ),
            )

    def _render_non_result_placeholders(self, entry: RunHistoryEntry) -> None:
        self.view.metric_run_id_var.set(entry.run_id or "n/a")
        self.view.metric_duration_var.set("n/a")
        self.view.metric_requirements_var.set("n/a")
        self.view.metric_progress_var.set(0.0)
        self.view.metric_progress_text_var.set("0%")
        self.view.metric_coverage_var.set("n/a")
        self.view.metric_links_var.set("n/a")
        self.view.metric_confidence_var.set("n/a")
        self.view.insight_summary_var.set(self._status_display(entry))

        rows = [
            ("Status", self._status_display(entry)),
            ("Analysis", entry.label),
            ("Result", "Result payload is not available for this history item."),
        ]
        if entry.error_message:
            rows.append(("Error", entry.error_message))
        self._set_insight_rows(rows)

    def _set_insight_rows(self, rows: list[tuple[str, str]]) -> None:
        for item in self.view.insights_table.get_children():
            self.view.insights_table.delete(item)
        for index, (label, value) in enumerate(rows):
            self.view.insights_table.insert(
                "",
                tk.END,
                iid=f"insight-{index}",
                text=label,
                values=(value,),
            )

    def _animate_running_state(self) -> None:
        if self._closing:
            return
        self._spinner_index = (self._spinner_index + 1) % len(self._SPINNER_FRAMES)
        for entry in self._history.list_entries():
            if entry.status != RunStatus.RUNNING:
                continue
            if not self.view.runs_table.exists(entry.id):
                continue
            self.view.runs_table.item(
                entry.id,
                values=(
                    entry.label,
                    self._status_display(entry, animated=True),
                    entry.method_name,
                    self._timestamp_display(entry.updated_at),
                ),
                tags=(self._run_row_tag(entry),),
            )

        selected = self._selected_history_entry()
        if selected is not None and selected.status == RunStatus.RUNNING:
            now = monotonic()
            needs_refresh = selected.id in self._refresh_requested_entries
            if (
                needs_refresh
                or now - self._last_running_refresh_at
                >= self._RUNNING_REFRESH_INTERVAL_SECONDS
            ):
                self._refresh_requested_entries.discard(selected.id)
                self._last_running_refresh_at = now
                self._refresh_selected_run()

        if not self._closing:
            self.view.root.after(180, self._animate_running_state)

    def _build_analysis_label(
        self,
        *,
        requirements_path: Path,
        evidence_path: Path,
        explicit_name: str | None = None,
    ) -> str:
        if explicit_name:
            return explicit_name
        requirements_name = requirements_path.name
        evidence_name = evidence_path.name
        return f"{requirements_name} <- {evidence_name}"

    def _status_display(self, entry: RunHistoryEntry, *, animated: bool = False) -> str:
        return status_display(
            entry,
            animated=animated,
            spinner_frame=self._spinner_frame(),
            is_cancel_requested=entry.id in self._cancel_requested_entries,
            is_preparing=entry.id in self._preparing_entries,
        )

    def _requirement_status_display(self, status_value: str) -> str:
        return requirement_status_display(status_value)

    def _live_requirement_status_display(self, status_value: str) -> str:
        return live_requirement_status_display(
            status_value,
            spinner_frame=self._spinner_frame(),
        )

    def _timestamp_display(self, value: datetime) -> str:
        return timestamp_display(value)

    def _duration_display(self, result: TraceabilityResult) -> str:
        return duration_display(result)

    def _spinner_frame(self) -> str:
        return self._SPINNER_FRAMES[self._spinner_index]

    def _run_row_tag(self, entry: RunHistoryEntry) -> str:
        return run_row_tag(entry)

    def _live_requirement_row_tag(self, status_value: str) -> str:
        return live_requirement_row_tag(status_value)

    def _final_requirement_row_tag(self, status_value: str) -> str:
        return final_requirement_row_tag(status_value)

    @staticmethod
    def _coerce_int(value: object, *, default: int) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default



