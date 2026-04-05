from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class ReqTraceGuiView:
    def __init__(
        self,
        *,
        methods: list[str],
        on_browse_requirements_file: Callable[[], None],
        on_browse_requirements_dir: Callable[[], None],
        on_browse_evidence_file: Callable[[], None],
        on_browse_evidence_dir: Callable[[], None],
        on_start_run: Callable[[], None],
        on_cancel_selected: Callable[[], None],
        on_delete_selected: Callable[[], None],
        on_import_result: Callable[[], None],
        on_export_selected: Callable[[], None],
        on_run_selected: Callable[[], None],
        on_requirement_selected: Callable[[], None],
    ) -> None:
        self.root = tk.Tk()
        self.root.title("ReqTrace")
        self.root.geometry("1220x760")
        self._configure_styles()

        self.logo_image = self._create_logo_image()
        self.root.iconphoto(True, self.logo_image)

        self.requirements_path_var = tk.StringVar()
        self.evidence_path_var = tk.StringVar()
        self.analysis_name_var = tk.StringVar()
        self.method_var = tk.StringVar(value=methods[0] if methods else "baseline")
        self.requirements_format_var = tk.StringVar(value="auto")

        self.metric_run_id_var = tk.StringVar(value="n/a")
        self.metric_method_var = tk.StringVar(value="n/a")
        self.metric_status_var = tk.StringVar(value="n/a")
        self.metric_duration_var = tk.StringVar(value="n/a")
        self.metric_requirements_var = tk.StringVar(value="0")
        self.metric_coverage_var = tk.StringVar(value="0.0%")
        self.metric_links_var = tk.StringVar(value="0")
        self.metric_confidence_var = tk.StringVar(value="0.0%")
        self.metric_progress_var = tk.DoubleVar(value=0.0)

        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(outer)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, image=self.logo_image).pack(side=tk.LEFT)
        header_text = ttk.Frame(header)
        header_text.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(header_text, text="ReqTrace", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header_text,
            text="Requirements-to-evidence analysis dashboard",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        config = ttk.LabelFrame(outer, text="New Analysis", padding=10)
        config.pack(fill=tk.X)

        ttk.Label(config, text="Requirements source").grid(row=0, column=0, sticky="w")
        ttk.Entry(config, textvariable=self.requirements_path_var).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        req_actions = ttk.Frame(config)
        req_actions.grid(row=0, column=2, sticky="w")
        ttk.Button(req_actions, text="Select file", command=on_browse_requirements_file).pack(
            side=tk.LEFT
        )
        ttk.Button(req_actions, text="Select folder", command=on_browse_requirements_dir).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        ttk.Label(config, text="Evidence source").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(config, textvariable=self.evidence_path_var).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(6, 0)
        )
        evidence_actions = ttk.Frame(config)
        evidence_actions.grid(row=1, column=2, sticky="w", pady=(6, 0))
        ttk.Button(evidence_actions, text="Select file", command=on_browse_evidence_file).pack(
            side=tk.LEFT
        )
        ttk.Button(evidence_actions, text="Select folder", command=on_browse_evidence_dir).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        ttk.Label(config, text="Requirements format").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(
            config,
            textvariable=self.requirements_format_var,
            values=["auto", "markdown", "json"],
            state="readonly",
            width=14,
        ).grid(row=2, column=1, sticky="w", padx=8, pady=(6, 0))

        ttk.Label(config, text="Evidence format").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Label(config, text="testar (auto)").grid(
            row=3,
            column=1,
            sticky="w",
            padx=8,
            pady=(6, 0),
        )

        ttk.Label(config, text="Method").grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(
            config,
            textvariable=self.method_var,
            values=methods,
            state="readonly",
            width=20,
        ).grid(row=4, column=1, sticky="w", padx=8, pady=(6, 0))

        ttk.Label(config, text="Analysis name (optional)").grid(
            row=5, column=0, sticky="w", pady=(6, 0)
        )
        ttk.Entry(config, textvariable=self.analysis_name_var).grid(
            row=5, column=1, sticky="ew", padx=8, pady=(6, 0)
        )

        action_bar = ttk.Frame(config)
        action_bar.grid(row=6, column=1, sticky="w", pady=(10, 0))
        ttk.Button(action_bar, text="Start Analysis", command=on_start_run).pack(side=tk.LEFT)

        config.columnconfigure(1, weight=1)

        body = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body)
        body.add(left, weight=2)
        body.add(right, weight=5)

        ttk.Label(left, text="Analysis History", style="Section.TLabel").pack(anchor="w")
        self.runs_table = ttk.Treeview(
            left,
            columns=("analysis", "status", "method", "updated"),
            show="headings",
            height=20,
        )
        self.runs_table.heading("analysis", text="Analysis")
        self.runs_table.heading("status", text="Status")
        self.runs_table.heading("method", text="Method")
        self.runs_table.heading("updated", text="Updated (UTC)")
        self.runs_table.column("analysis", width=240, anchor="w")
        self.runs_table.column("status", width=140, anchor="w")
        self.runs_table.column("method", width=160, anchor="w")
        self.runs_table.column("updated", width=180, anchor="w")
        self.runs_table.tag_configure("run_running", foreground="#1d4ed8")
        self.runs_table.tag_configure("run_completed", foreground="#166534")
        self.runs_table.tag_configure("run_warning", foreground="#a16207")
        self.runs_table.tag_configure("run_failed", foreground="#b91c1c")
        self.runs_table.tag_configure("run_canceled", foreground="#6b7280")
        self.runs_table.pack(fill=tk.BOTH, expand=True)
        self.runs_table.bind("<<TreeviewSelect>>", lambda _event: on_run_selected())

        history_actions = ttk.Frame(left)
        history_actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(history_actions, text="Cancel", command=on_cancel_selected).pack(side=tk.LEFT)
        ttk.Button(history_actions, text="Delete", command=on_delete_selected).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(history_actions, text="Export", command=on_export_selected).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Button(history_actions, text="Import", command=on_import_result).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        metrics = ttk.LabelFrame(right, text="Analysis Insights", padding=10)
        metrics.pack(fill=tk.X)
        self._metric_cell(metrics, "Run ID", self.metric_run_id_var, 0, 0)
        self._metric_cell(metrics, "Method", self.metric_method_var, 0, 1)
        self._metric_cell(metrics, "Status", self.metric_status_var, 0, 2)
        self._metric_cell(metrics, "Duration", self.metric_duration_var, 0, 3)
        self._metric_cell(metrics, "Requirements", self.metric_requirements_var, 1, 0)
        self._metric_cell(metrics, "Overall Coverage", self.metric_coverage_var, 1, 1)
        self._metric_cell(metrics, "Trace Links", self.metric_links_var, 1, 2)
        self._metric_cell(metrics, "Avg Confidence", self.metric_confidence_var, 1, 3)
        self.progress_bar = ttk.Progressbar(
            metrics,
            variable=self.metric_progress_var,
            maximum=100.0,
        )
        self.progress_bar.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        for column in range(4):
            metrics.columnconfigure(column, weight=1)

        self.insights_text = tk.Text(metrics, height=6, wrap="word")
        self.insights_text.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        req_frame = ttk.LabelFrame(right, text="Requirement Status", padding=8)
        req_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.requirement_table = ttk.Treeview(
            req_frame,
            columns=("status", "coverage", "links", "evidence"),
            show="tree headings",
        )
        self.requirement_table.heading("#0", text="Requirement")
        self.requirement_table.heading("status", text="Status")
        self.requirement_table.heading("coverage", text="Coverage")
        self.requirement_table.heading("links", text="Links")
        self.requirement_table.heading("evidence", text="Evidence")
        self.requirement_table.column("#0", width=440)
        self.requirement_table.column("status", width=120, anchor="w")
        self.requirement_table.column("coverage", width=120, anchor="w")
        self.requirement_table.column("links", width=80, anchor="e")
        self.requirement_table.column("evidence", width=90, anchor="e")
        self.requirement_table.tag_configure("req_waiting", foreground="#4b5563")
        self.requirement_table.tag_configure("req_processing", foreground="#1d4ed8")
        self.requirement_table.tag_configure("req_completed", foreground="#166534")
        self.requirement_table.tag_configure("req_failed", foreground="#b91c1c")
        self.requirement_table.pack(fill=tk.BOTH, expand=True)
        self.requirement_table.bind("<<TreeviewSelect>>", lambda _event: on_requirement_selected())

        detail_frame = ttk.LabelFrame(right, text="Requirement Detail", padding=8)
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.detail_text = tk.Text(detail_frame, height=10, wrap="word")
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def run(self) -> None:
        self.root.mainloop()

    def clear_metrics(self) -> None:
        self.metric_run_id_var.set("n/a")
        self.metric_method_var.set("n/a")
        self.metric_status_var.set("n/a")
        self.metric_duration_var.set("n/a")
        self.metric_requirements_var.set("0")
        self.metric_coverage_var.set("0.0%")
        self.metric_links_var.set("0")
        self.metric_confidence_var.set("0.0%")
        self.metric_progress_var.set(0.0)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("TkDefaultFont", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#4d5a66")
        style.configure("Section.TLabel", font=("TkDefaultFont", 11, "bold"))
        style.configure("MetricTitle.TLabel", foreground="#4d5a66")
        style.configure("MetricValue.TLabel", font=("TkDefaultFont", 11, "bold"))

    def _metric_cell(
        self, parent: ttk.LabelFrame, title: str, value_var: tk.StringVar, row: int, column: int
    ) -> None:
        cell = ttk.Frame(parent, padding=(4, 2))
        cell.grid(row=row, column=column, sticky="ew")
        ttk.Label(cell, text=title, style="MetricTitle.TLabel").pack(anchor="w")
        ttk.Label(cell, textvariable=value_var, style="MetricValue.TLabel").pack(anchor="w")

    def _create_logo_image(self) -> tk.PhotoImage:
        image = tk.PhotoImage(width=32, height=32)
        image.put("#1f6feb", to=(0, 0, 32, 32))
        image.put("#0d3a77", to=(2, 2, 30, 30))
        image.put("#ffffff", to=(8, 6, 24, 9))
        image.put("#ffffff", to=(8, 6, 11, 26))
        image.put("#ffffff", to=(8, 14, 21, 17))
        image.put("#ffffff", to=(18, 14, 24, 26))
        image.put("#ffffff", to=(8, 23, 24, 26))
        return image
