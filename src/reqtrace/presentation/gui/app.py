from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from reqtrace.application.results import TraceabilityResult
from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.presentation.runtime import RunInput, execute_run, export_result_json, import_result_json


@dataclass(slots=True)
class UiRunRecord:
    label: str
    status: str
    result: TraceabilityResult | None = None
    source_path: Path | None = None


class ReqTraceGui:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ReqTrace")
        self.root.geometry("1100x700")

        self._service = build_default_traceability_service()
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._runs: list[UiRunRecord] = []

        self.requirements_path_var = tk.StringVar()
        self.evidence_path_var = tk.StringVar()
        self.method_var = tk.StringVar(value="baseline")

        self._build_layout()
        self.root.after(150, self._poll_queue)

    def run(self) -> None:
        self.root.mainloop()

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        config = ttk.LabelFrame(outer, text="Run configuration", padding=8)
        config.pack(fill=tk.X)

        ttk.Label(config, text="Requirements file").grid(row=0, column=0, sticky="w")
        ttk.Entry(config, textvariable=self.requirements_path_var, width=80).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(config, text="Browse", command=self._browse_requirements).grid(row=0, column=2)

        ttk.Label(config, text="Evidence file").grid(row=1, column=0, sticky="w")
        ttk.Entry(config, textvariable=self.evidence_path_var, width=80).grid(row=1, column=1, sticky="ew", padx=6)
        ttk.Button(config, text="Browse", command=self._browse_evidence).grid(row=1, column=2)

        ttk.Label(config, text="Method").grid(row=2, column=0, sticky="w")
        methods = self._service.available_methods()
        ttk.Combobox(config, textvariable=self.method_var, values=methods, state="readonly", width=20).grid(
            row=2, column=1, sticky="w", padx=6, pady=(4, 0)
        )

        action_bar = ttk.Frame(config)
        action_bar.grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Button(action_bar, text="Start run", command=self._start_run).pack(side=tk.LEFT)
        ttk.Button(action_bar, text="Import result", command=self._import_result).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(action_bar, text="Export selected", command=self._export_selected).pack(side=tk.LEFT, padx=(8, 0))

        config.columnconfigure(1, weight=1)

        body = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text="Runs").pack(anchor="w")
        self.runs_list = tk.Listbox(left, exportselection=False)
        self.runs_list.pack(fill=tk.BOTH, expand=True)
        self.runs_list.bind("<<ListboxSelect>>", lambda _event: self._refresh_selected_run())

        summary_frame = ttk.LabelFrame(right, text="Run summary", padding=8)
        summary_frame.pack(fill=tk.X)
        self.summary_text = tk.Text(summary_frame, height=10, wrap="word")
        self.summary_text.pack(fill=tk.X)

        req_frame = ttk.LabelFrame(right, text="Requirement results", padding=8)
        req_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.requirement_table = ttk.Treeview(req_frame, columns=("status", "coverage", "links", "evidence"), show="tree headings")
        self.requirement_table.heading("#0", text="Requirement")
        self.requirement_table.heading("status", text="Status")
        self.requirement_table.heading("coverage", text="Coverage")
        self.requirement_table.heading("links", text="Links")
        self.requirement_table.heading("evidence", text="Evidence")
        self.requirement_table.pack(fill=tk.BOTH, expand=True)
        self.requirement_table.bind("<<TreeviewSelect>>", lambda _event: self._refresh_requirement_detail())

        detail_frame = ttk.LabelFrame(right, text="Requirement detail", padding=8)
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.detail_text = tk.Text(detail_frame, height=10, wrap="word")
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def _browse_requirements(self) -> None:
        selected = filedialog.askopenfilename(title="Select requirements file")
        if selected:
            self.requirements_path_var.set(selected)

    def _browse_evidence(self) -> None:
        selected = filedialog.askopenfilename(title="Select evidence file")
        if selected:
            self.evidence_path_var.set(selected)

    def _start_run(self) -> None:
        requirements_path = Path(self.requirements_path_var.get().strip())
        evidence_path = Path(self.evidence_path_var.get().strip())
        if not requirements_path.exists() or not evidence_path.exists():
            messagebox.showerror("ReqTrace", "Select both a requirements file and an evidence file.")
            return

        record = UiRunRecord(label=f"{self.method_var.get()} :: {requirements_path.name} :: running", status="running")
        self._runs.append(record)
        self.runs_list.insert(tk.END, record.label)
        run_index = len(self._runs) - 1

        def worker() -> None:
            try:
                result = execute_run(
                    RunInput(requirements_path=requirements_path, evidence_path=evidence_path, method_name=self.method_var.get()),
                    service=self._service,
                )
                self._queue.put(("run-complete", (run_index, result)))
            except Exception as exc:  # pragma: no cover
                self._queue.put(("run-failed", (run_index, str(exc))))

        threading.Thread(target=worker, daemon=True).start()

    def _import_result(self) -> None:
        selected = filedialog.askopenfilename(title="Import result JSON", filetypes=[("JSON files", "*.json"), ("All files", "*")])
        if not selected:
            return
        result_path = Path(selected)
        try:
            result = import_result_json(result_path)
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("ReqTrace", f"Could not import result:\n{exc}")
            return

        record = UiRunRecord(label=f"imported :: {result.run.method_name} :: {result_path.name}", status="imported", result=result, source_path=result_path)
        self._runs.append(record)
        self.runs_list.insert(tk.END, record.label)

    def _export_selected(self) -> None:
        record = self._selected_run_record()
        if record is None or record.result is None:
            messagebox.showinfo("ReqTrace", "Select a completed or imported run first.")
            return

        selected = filedialog.asksaveasfilename(title="Export result JSON", defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not selected:
            return
        export_result_json(record.result, Path(selected))
        messagebox.showinfo("ReqTrace", f"Saved result to {selected}")

    def _poll_queue(self) -> None:
        try:
            while True:
                event_name, payload = self._queue.get_nowait()
                if event_name == "run-complete":
                    index, result = payload  # type: ignore[misc]
                    record = self._runs[index]
                    record.status = "completed"
                    record.result = result
                    record.label = f"{result.run.method_name} :: {result.run.id} :: completed"
                    self.runs_list.delete(index)
                    self.runs_list.insert(index, record.label)
                elif event_name == "run-failed":
                    index, message = payload  # type: ignore[misc]
                    record = self._runs[index]
                    record.status = "failed"
                    record.label = f"failed :: {message}"
                    self.runs_list.delete(index)
                    self.runs_list.insert(index, record.label)
        except queue.Empty:
            pass
        finally:
            self.root.after(150, self._poll_queue)

    def _selected_run_record(self) -> UiRunRecord | None:
        selection = self.runs_list.curselection()
        if not selection:
            return None
        return self._runs[selection[0]]

    def _refresh_selected_run(self) -> None:
        record = self._selected_run_record()
        self.summary_text.delete("1.0", tk.END)
        for item in self.requirement_table.get_children():
            self.requirement_table.delete(item)
        self.detail_text.delete("1.0", tk.END)

        if record is None:
            return
        if record.result is None:
            self.summary_text.insert(tk.END, f"Status: {record.status}\nRun still in progress or failed.")
            return

        result = record.result
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
        self.summary_text.insert(tk.END, "\n".join(summary_lines))

        for item in result.requirement_results:
            coverage = str(item.artifact_coverage.coverage_status) if item.artifact_coverage else "n/a"
            self.requirement_table.insert(
                "",
                tk.END,
                iid=item.requirement_id,
                text=f"{item.requirement_id}: {item.requirement_title}",
                values=(str(item.status), coverage, len(item.trace_links), len(item.trace_evidence)),
            )

    def _refresh_requirement_detail(self) -> None:
        self.detail_text.delete("1.0", tk.END)
        record = self._selected_run_record()
        if record is None or record.result is None:
            return
        selection = self.requirement_table.selection()
        if not selection:
            return
        requirement_id = selection[0]
        for item in record.result.requirement_results:
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
            self.detail_text.insert(tk.END, "\n".join(lines))
            return


def _print_gui_unavailable_message(message: str) -> None:
    print(message, file=sys.stderr)


def launch_gui() -> int:
    """Launch the GUI.

    Returns a process exit code (0 = success, non-zero = could not start).
    This fails gracefully in headless environments (e.g., devcontainers).
    """
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        _print_gui_unavailable_message(
            "ReqTrace GUI cannot start: no $DISPLAY environment variable was found.\n"
            "You're likely running in a headless environment (e.g., a devcontainer).\n\n"
            "Options:\n"
            "- Use the CLI:  reqtrace run ...\n"
            "- Run the GUI on your host machine\n"
            "- Configure GUI forwarding (X11/XWayland) and set $DISPLAY\n"
        )
        return 2

    try:
        app = ReqTraceGui()
        app.run()
        return 0
    except tk.TclError as exc:
        _print_gui_unavailable_message(
            "ReqTrace GUI cannot start (Tkinter error).\n"
            f"Details: {exc}\n\n"
            "This typically means the environment has no graphical display.\n"
            "Try running the GUI on a machine with a desktop session or enable display forwarding."
        )
        return 2


def main() -> int:
    return launch_gui()


if __name__ == "__main__":
    raise SystemExit(main())
