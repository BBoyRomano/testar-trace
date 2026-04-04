from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from reqtrace.application.history_models import RunHistoryEntry
from reqtrace.application.result_enums import RunStatus
from reqtrace.application.results import TraceabilityResult
from reqtrace.application.services import AsyncRunExecutor, RunHistoryService
from reqtrace.application.services.run_result_service import (
    export_result_json,
    import_result_json,
)
from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.infrastructure.persistence import JsonRunHistoryRepository
from reqtrace.presentation.exceptions import RunInputValidationError
from reqtrace.presentation.gui.views import ReqTraceGuiView
from reqtrace.presentation.runtime import (
    SUPPORTED_EVIDENCE_FORMATS,
    SUPPORTED_REQUIREMENTS_FORMATS,
    RunInput,
    build_request,
)

logger = logging.getLogger(__name__)


class ReqTraceGuiController:
    def __init__(self) -> None:
        self._service = build_default_traceability_service()
        self._executor = AsyncRunExecutor(self._service)
        self._history = RunHistoryService(
            JsonRunHistoryRepository(Path.cwd() / ".reqtrace" / "gui-history")
        )
        self._job_to_entry: dict[str, str] = {}
        self._entry_ids: list[str] = []
        self._entry_index_by_id: dict[str, int] = {}

        self.view = ReqTraceGuiView(
            methods=self._service.available_methods(),
            requirements_formats=list(SUPPORTED_REQUIREMENTS_FORMATS),
            evidence_formats=list(SUPPORTED_EVIDENCE_FORMATS),
            on_browse_requirements_file=self._browse_requirements_file,
            on_browse_requirements_dir=self._browse_requirements_dir,
            on_browse_evidence=self._browse_evidence,
            on_browse_evidence_dir=self._browse_evidence_dir,
            on_start_run=self._start_run,
            on_import_result=self._import_result,
            on_export_selected=self._export_selected,
            on_run_selected=self._refresh_selected_run,
            on_requirement_selected=self._refresh_requirement_detail,
        )
        self.view.root.protocol("WM_DELETE_WINDOW", self._on_close)

        for entry in self._history.list_entries():
            self._append_entry_to_view(entry)

        self.view.root.after(150, self._poll_executor)
        logger.info(
            "GUI controller initialized.",
            extra={"history_entry_count": len(self._entry_ids)},
        )

    def run(self) -> None:
        self.view.run()

    def _on_close(self) -> None:
        self._executor.shutdown()
        logger.info("GUI controller shutdown.")
        self.view.root.destroy()

    def _browse_requirements_file(self) -> None:
        selected = filedialog.askopenfilename(title="Select requirements file")
        if selected:
            self.view.requirements_path_var.set(selected)

    def _browse_requirements_dir(self) -> None:
        selected = filedialog.askdirectory(title="Select requirements directory")
        if selected:
            self.view.requirements_path_var.set(selected)

    def _browse_evidence(self) -> None:
        selected = filedialog.askopenfilename(title="Select evidence file")
        if selected:
            self.view.evidence_path_var.set(selected)

    def _browse_evidence_dir(self) -> None:
        selected = filedialog.askdirectory(title="Select evidence directory")
        if selected:
            self.view.evidence_path_var.set(selected)

    def _start_run(self) -> None:
        requirements_text = self.view.requirements_path_var.get().strip()
        evidence_text = self.view.evidence_path_var.get().strip()
        if not requirements_text or not evidence_text:
            logger.warning("GUI run start rejected due to missing input paths.")
            messagebox.showerror(
                "ReqTrace", "Select a requirements file or directory and an evidence file."
            )
            return

        run_input = RunInput(
            requirements_paths=[Path(requirements_text)],
            evidence_path=Path(evidence_text),
            requirements_format=self.view.requirements_format_var.get(),
            evidence_format=self.view.evidence_format_var.get(),
            method_name=self.view.method_var.get(),
        )

        try:
            request = build_request(run_input)
        except RunInputValidationError as exc:
            logger.warning("GUI run input validation failed.", extra={"error_message": str(exc)})
            messagebox.showerror("ReqTrace", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive boundary
            logger.error("GUI run request build failed.", exc_info=exc)
            messagebox.showerror("ReqTrace", f"Could not prepare run:\n{exc}")
            return

        entry = self._history.create_running_entry(
            method_name=self.view.method_var.get(),
            label=f"{self.view.method_var.get()} :: {Path(requirements_text).name} :: running",
        )
        self._append_entry_to_view(entry)

        job_id = self._executor.submit(request)
        self._job_to_entry[job_id] = entry.id
        logger.info(
            "GUI run submitted.",
            extra={"job_id": job_id, "entry_id": entry.id, "method_name": request.method_name},
        )

    def _import_result(self) -> None:
        selected = filedialog.askopenfilename(
            title="Import result JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*")],
        )
        if not selected:
            return
        result_path = Path(selected)
        try:
            result = import_result_json(result_path)
            entry = self._history.add_imported_result(result=result, source_path=result_path)
        except Exception as exc:  # pragma: no cover
            logger.error("GUI result import failed.", exc_info=exc)
            messagebox.showerror("ReqTrace", f"Could not import result:\n{exc}")
            return

        self._append_entry_to_view(entry)
        logger.info(
            "GUI result imported.",
            extra={"entry_id": entry.id, "run_id": result.run.id},
        )

    def _export_selected(self) -> None:
        entry = self._selected_history_entry()
        if entry is None:
            logger.debug("GUI export requested with no selected entry.")
            messagebox.showinfo("ReqTrace", "Select a completed or imported run first.")
            return

        result = self._history.get_result(entry.id)
        if result is None:
            logger.warning(
                "GUI export requested for entry with no result.",
                extra={"entry_id": entry.id},
            )
            messagebox.showinfo("ReqTrace", "Selected run has no result payload to export.")
            return

        selected = filedialog.asksaveasfilename(
            title="Export result JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not selected:
            return
        export_result_json(result, Path(selected))
        logger.info(
            "GUI result exported.",
            extra={"entry_id": entry.id, "run_id": result.run.id, "output_path": selected},
        )
        messagebox.showinfo("ReqTrace", f"Saved result to {selected}")

    def _poll_executor(self) -> None:
        try:
            for event in self._executor.drain_events():
                if event.status == RunStatus.RUNNING:
                    continue
                entry_id = self._job_to_entry.pop(event.job_id, None)
                if entry_id is None:
                    logger.warning(
                        "Received async event for unknown job.",
                        extra={"job_id": event.job_id, "status": str(event.status)},
                    )
                    continue
                if event.status == RunStatus.COMPLETED and event.result is not None:
                    entry = self._history.mark_completed(entry_id, event.result)
                    logger.info(
                        "GUI observed run completion.",
                        extra={"job_id": event.job_id, "entry_id": entry_id},
                    )
                else:
                    message = event.error_message or "Run failed."
                    entry = self._history.mark_failed(entry_id, message)
                    logger.error(
                        "GUI observed run failure.",
                        extra={
                            "job_id": event.job_id,
                            "entry_id": entry_id,
                            "error_message": message,
                        },
                    )
                self._update_entry_label(entry)
                self._refresh_selected_run()
        finally:
            self.view.root.after(150, self._poll_executor)

    def _append_entry_to_view(self, entry: RunHistoryEntry) -> None:
        index = len(self._entry_ids)
        self._entry_ids.append(entry.id)
        self._entry_index_by_id[entry.id] = index
        self.view.runs_list.insert(tk.END, entry.label)
        logger.debug("GUI history entry appended.", extra={"entry_id": entry.id, "index": index})

    def _update_entry_label(self, entry: RunHistoryEntry) -> None:
        index = self._entry_index_by_id.get(entry.id)
        if index is None:
            self._append_entry_to_view(entry)
            return
        self.view.runs_list.delete(index)
        self.view.runs_list.insert(index, entry.label)

    def _selected_history_entry(self) -> RunHistoryEntry | None:
        selection = self.view.runs_list.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self._entry_ids):
            return None
        return self._history.get_entry(self._entry_ids[index])

    def _selected_result(self) -> tuple[RunHistoryEntry | None, TraceabilityResult | None]:
        entry = self._selected_history_entry()
        if entry is None:
            return None, None
        try:
            return entry, self._history.get_result(entry.id)
        except Exception as exc:
            logger.error(
                "GUI failed to load selected run result.",
                exc_info=exc,
                extra={"entry_id": entry.id},
            )
            return entry, None

    def _refresh_selected_run(self) -> None:
        entry, result = self._selected_result()
        self.view.summary_text.delete("1.0", tk.END)
        for item in self.view.requirement_table.get_children():
            self.view.requirement_table.delete(item)
        self.view.detail_text.delete("1.0", tk.END)

        if entry is None:
            return
        if result is None:
            status_line = f"Status: {entry.status}"
            if entry.error_message:
                status_line = status_line + f"\nError: {entry.error_message}"
            self.view.summary_text.insert(tk.END, status_line)
            return

        summary_lines = [
            f"Run ID: {result.run.id}",
            f"Method: {result.run.method_name}",
            f"Status: {result.run.status}",
            f"Requirements: {result.summary.requirement_count}",
            f"Analyzed: {result.summary.analyzed_requirement_count}",
            f"Covered: {result.summary.covered_requirement_count}",
            f"Partially covered: {result.summary.partially_covered_requirement_count}",
            f"Uncovered: {result.summary.uncovered_requirement_count}",
            f"Trace links: {result.summary.trace_link_count}",
            f"Trace evidence: {result.summary.trace_evidence_count}",
        ]
        self.view.summary_text.insert(tk.END, "\n".join(summary_lines))

        for item in result.requirement_results:
            coverage = (
                str(item.artifact_coverage.coverage_status) if item.artifact_coverage else "n/a"
            )
            self.view.requirement_table.insert(
                "",
                tk.END,
                iid=item.requirement_id,
                text=f"{item.requirement_id}: {item.requirement_title}",
                values=(
                    str(item.status),
                    coverage,
                    len(item.trace_links),
                    len(item.trace_evidence),
                ),
            )

    def _refresh_requirement_detail(self) -> None:
        self.view.detail_text.delete("1.0", tk.END)
        _entry, result = self._selected_result()
        if result is None:
            return
        selection = self.view.requirement_table.selection()
        if not selection:
            return
        requirement_id = selection[0]
        for item in result.requirement_results:
            if item.requirement_id != requirement_id:
                continue
            lines = [
                f"Requirement ID: {item.requirement_id}",
                f"Title: {item.requirement_title}",
                f"Status: {item.status}",
                f"Trace links: {len(item.trace_links)}",
                f"Trace evidence: {len(item.trace_evidence)}",
                f"Warnings: {len(item.warnings)}",
            ]
            if item.artifact_coverage is not None:
                lines.extend(
                    [
                        f"Coverage: {item.artifact_coverage.coverage_status}",
                        f"Coverage ratio: {item.artifact_coverage.coverage_ratio}",
                        f"Confidence: {item.artifact_coverage.confidence_ratio}",
                    ]
                )
            if item.error_message:
                lines.append(f"Error: {item.error_message}")
            self.view.detail_text.insert(tk.END, "\n".join(lines))
            return
