from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class ReqTraceGuiView:
    def __init__(
        self,
        *,
        methods: list[str],
        on_requirements_path_changed: Callable[[], None],
        on_evidence_path_changed: Callable[[], None],
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
        self.root.geometry("1280x820")
        self.root.minsize(1120, 720)
        self._configure_styles()

        self.icon_image = self._create_logo_image(32)
        self.logo_image = self._create_logo_image(40)
        self.root.iconphoto(True, self.icon_image)

        self.requirements_path_var = tk.StringVar()
        self.evidence_path_var = tk.StringVar()
        self.analysis_name_var = tk.StringVar()
        self.method_var = tk.StringVar(value=methods[0] if methods else "baseline")
        self.requirements_format_detected_var = tk.StringVar(value="not detected")
        self.evidence_format_detected_var = tk.StringVar(value="not detected")
        self.insight_summary_var = tk.StringVar(value="Select or start an analysis.")

        self.metric_run_id_var = tk.StringVar(value="n/a")
        self.metric_method_var = tk.StringVar(value="n/a")
        self.metric_status_var = tk.StringVar(value="n/a")
        self.metric_duration_var = tk.StringVar(value="n/a")
        self.metric_requirements_var = tk.StringVar(value="0")
        self.metric_coverage_var = tk.StringVar(value="0.0%")
        self.metric_links_var = tk.StringVar(value="0")
        self.metric_confidence_var = tk.StringVar(value="0.0%")
        self.metric_progress_var = tk.DoubleVar(value=0.0)
        self.metric_progress_text_var = tk.StringVar(value="0%")

        self.requirements_path_var.trace_add("write", lambda *_args: on_requirements_path_changed())
        self.evidence_path_var.trace_add("write", lambda *_args: on_evidence_path_changed())

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
            text="Traceability workspace for requirements and evidence",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        config = ttk.LabelFrame(outer, text="Run Setup", padding=12)
        config.pack(fill=tk.X)

        self._build_source_row(
            parent=config,
            row=0,
            label="Requirements source",
            path_var=self.requirements_path_var,
            detected_var=self.requirements_format_detected_var,
            on_browse_file=on_browse_requirements_file,
            on_browse_dir=on_browse_requirements_dir,
        )
        self._build_source_row(
            parent=config,
            row=2,
            label="Evidence source",
            path_var=self.evidence_path_var,
            detected_var=self.evidence_format_detected_var,
            on_browse_file=on_browse_evidence_file,
            on_browse_dir=on_browse_evidence_dir,
        )

        method_row = ttk.Frame(config)
        method_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        ttk.Label(method_row, text="Method").pack(side=tk.LEFT)
        ttk.Combobox(
            method_row,
            textvariable=self.method_var,
            values=methods,
            state="readonly",
            width=20,
        ).pack(side=tk.LEFT, padx=(8, 16))

        ttk.Label(method_row, text="Analysis name").pack(side=tk.LEFT)
        ttk.Entry(method_row, textvariable=self.analysis_name_var).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(8, 0),
        )
        ttk.Button(method_row, text="Start Analysis", style="Accent.TButton", command=on_start_run).pack(
            side=tk.RIGHT
        )

        config.columnconfigure(1, weight=1)

        body = tk.PanedWindow(
            outer,
            orient=tk.HORIZONTAL,
            bd=0,
            sashwidth=7,
            relief=tk.FLAT,
            opaqueresize=False,
        )
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        right = ttk.Frame(body)
        body.add(left, minsize=340)
        body.add(right, minsize=720)

        history_header = ttk.Frame(left)
        history_header.pack(fill=tk.X)
        ttk.Label(history_header, text="Analysis History", style="Section.TLabel").pack(side=tk.LEFT)
        history_actions = ttk.Frame(history_header)
        history_actions.pack(side=tk.RIGHT)
        ttk.Button(history_actions, text="Import", command=on_import_result).pack(side=tk.LEFT)
        ttk.Button(history_actions, text="Export", command=on_export_selected).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(history_actions, text="Cancel", command=on_cancel_selected).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(history_actions, text="Delete", command=on_delete_selected).pack(side=tk.LEFT, padx=(6, 0))

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
        self.runs_table.column("analysis", width=250, anchor="w")
        self.runs_table.column("status", width=130, anchor="w")
        self.runs_table.column("method", width=140, anchor="w")
        self.runs_table.column("updated", width=180, anchor="w")
        self.runs_table.tag_configure("run_running", foreground="#0b62d6")
        self.runs_table.tag_configure("run_completed", foreground="#176b38")
        self.runs_table.tag_configure("run_warning", foreground="#995e00")
        self.runs_table.tag_configure("run_failed", foreground="#a81f2b")
        self.runs_table.tag_configure("run_canceled", foreground="#5d6778")
        self.runs_table.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.runs_table.bind("<<TreeviewSelect>>", lambda _event: on_run_selected())

        self.workspace_notebook = ttk.Notebook(right)
        self.workspace_notebook.pack(fill=tk.BOTH, expand=True)

        overview_tab = ttk.Frame(self.workspace_notebook, padding=8)
        requirements_tab = ttk.Frame(self.workspace_notebook, padding=8)
        detail_tab = ttk.Frame(self.workspace_notebook, padding=8)
        about_tab = ttk.Frame(self.workspace_notebook, padding=8)

        self.workspace_notebook.add(overview_tab, text="Overview")
        self.workspace_notebook.add(requirements_tab, text="Requirements")
        self.workspace_notebook.add(detail_tab, text="Detail")
        self.workspace_notebook.add(about_tab, text="About")

        self.overview_tab = overview_tab
        self.requirements_tab = requirements_tab
        self.detail_tab = detail_tab
        self.about_tab = about_tab

        metrics = ttk.LabelFrame(overview_tab, text="Analysis Insights", padding=10)
        metrics.pack(fill=tk.BOTH, expand=True)
        self._metric_cell(metrics, "Run ID", self.metric_run_id_var, 0, 0)
        self._metric_cell(metrics, "Method", self.metric_method_var, 0, 1)
        self._metric_cell(metrics, "Status", self.metric_status_var, 0, 2)
        self._metric_cell(metrics, "Duration", self.metric_duration_var, 0, 3)
        self._metric_cell(metrics, "Requirements", self.metric_requirements_var, 1, 0)
        self._metric_cell(metrics, "Overall Coverage", self.metric_coverage_var, 1, 1)
        self._metric_cell(metrics, "Trace Links", self.metric_links_var, 1, 2)
        self._metric_cell(metrics, "Avg Confidence", self.metric_confidence_var, 1, 3)

        self.progress_bar = ttk.Progressbar(metrics, variable=self.metric_progress_var, maximum=100.0)
        self.progress_bar.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        progress_meta = ttk.Frame(metrics)
        progress_meta.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        ttk.Label(progress_meta, textvariable=self.insight_summary_var, style="Hint.TLabel").pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
        )
        ttk.Label(progress_meta, textvariable=self.metric_progress_text_var, style="MetricValue.TLabel").pack(
            side=tk.RIGHT
        )

        self.insights_table = ttk.Treeview(
            metrics,
            columns=("value",),
            show="tree headings",
            height=8,
        )
        self.insights_table.heading("#0", text="Insight")
        self.insights_table.heading("value", text="Value")
        self.insights_table.column("#0", width=220, anchor="w")
        self.insights_table.column("value", width=680, anchor="w")
        self.insights_table.grid(row=4, column=0, columnspan=4, sticky="nsew", pady=(8, 0))

        for column in range(4):
            metrics.columnconfigure(column, weight=1)
        metrics.rowconfigure(4, weight=1)

        req_frame = ttk.LabelFrame(requirements_tab, text="Requirement Status", padding=8)
        req_frame.pack(fill=tk.BOTH, expand=True)
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
        self.requirement_table.column("#0", width=520)
        self.requirement_table.column("status", width=120, anchor="w")
        self.requirement_table.column("coverage", width=130, anchor="w")
        self.requirement_table.column("links", width=80, anchor="e")
        self.requirement_table.column("evidence", width=90, anchor="e")
        self.requirement_table.tag_configure("req_waiting", foreground="#4b5563")
        self.requirement_table.tag_configure("req_processing", foreground="#0b62d6")
        self.requirement_table.tag_configure("req_completed", foreground="#176b38")
        self.requirement_table.tag_configure("req_failed", foreground="#a81f2b")
        self.requirement_table.pack(fill=tk.BOTH, expand=True)
        self.requirement_table.bind("<<TreeviewSelect>>", lambda _event: on_requirement_selected())

        detail_frame = ttk.LabelFrame(detail_tab, text="Requirement Detail", padding=8)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        self.detail_text = tk.Text(detail_frame, height=10, wrap="word", font=("Consolas", 10))
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        about_card = ttk.LabelFrame(about_tab, text="Identity", padding=12)
        about_card.pack(fill=tk.BOTH, expand=True)

        about_header = ttk.Frame(about_card)
        about_header.pack(fill=tk.X)
        ttk.Label(about_header, image=self.logo_image).pack(side=tk.LEFT)
        ttk.Label(about_header, text="ReqTrace mark", style="Section.TLabel").pack(side=tk.LEFT, padx=(10, 0))

        about_message = (
            "The logo represents traceability as a directed relation:\n"
            "- Left stack: requirements source (structured intent).\n"
            "- Right nodes: observed evidence states/actions.\n"
            "- Connecting lines: discovered trace links between both sides.\n\n"
            "This screen exists so design intent stays explicit and reusable for future visual updates."
        )
        ttk.Label(about_card, text=about_message, style="Body.TLabel", justify=tk.LEFT).pack(
            anchor="w",
            pady=(10, 0),
        )

    def run(self) -> None:
        self.root.mainloop()

    def show_overview(self) -> None:
        self.workspace_notebook.select(self.overview_tab)

    def show_requirements(self) -> None:
        self.workspace_notebook.select(self.requirements_tab)

    def show_detail(self) -> None:
        self.workspace_notebook.select(self.detail_tab)

    def show_about(self) -> None:
        self.workspace_notebook.select(self.about_tab)

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
        self.metric_progress_text_var.set("0%")
        self.insight_summary_var.set("Select or start an analysis.")

    def _build_source_row(
        self,
        *,
        parent: ttk.LabelFrame,
        row: int,
        label: str,
        path_var: tk.StringVar,
        detected_var: tk.StringVar,
        on_browse_file: Callable[[], None],
        on_browse_dir: Callable[[], None],
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=path_var).grid(row=row, column=1, sticky="ew", padx=8)

        action_container = ttk.Frame(parent)
        action_container.grid(row=row, column=2, sticky="w")

        browse_menu_button = ttk.Menubutton(action_container, text="Browse...")
        browse_menu = tk.Menu(browse_menu_button, tearoff=False)
        browse_menu.add_command(label="File...", command=on_browse_file)
        browse_menu.add_command(label="Folder...", command=on_browse_dir)
        browse_menu_button["menu"] = browse_menu
        browse_menu_button.pack(side=tk.LEFT)

        ttk.Label(parent, text="Detected format").grid(row=row + 1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(parent, textvariable=detected_var, style="Hint.TLabel").grid(
            row=row + 1,
            column=1,
            sticky="w",
            padx=8,
            pady=(6, 0),
        )

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Title.TLabel", font=("Segoe UI Semibold", 20), foreground="#0f172a")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#475569")
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 11), foreground="#0f172a")
        style.configure("Body.TLabel", font=("Segoe UI", 10), foreground="#1f2937")
        style.configure("MetricTitle.TLabel", font=("Segoe UI", 9), foreground="#475569")
        style.configure("MetricValue.TLabel", font=("Segoe UI Semibold", 11), foreground="#0f172a")
        style.configure("Hint.TLabel", font=("Segoe UI", 9), foreground="#475569")
        style.configure("Accent.TButton", font=("Segoe UI Semibold", 10), padding=(14, 6))

    def _metric_cell(
        self,
        parent: ttk.LabelFrame,
        title: str,
        value_var: tk.StringVar,
        row: int,
        column: int,
    ) -> None:
        cell = ttk.Frame(parent, padding=(4, 2))
        cell.grid(row=row, column=column, sticky="ew")
        ttk.Label(cell, text=title, style="MetricTitle.TLabel").pack(anchor="w")
        ttk.Label(cell, textvariable=value_var, style="MetricValue.TLabel").pack(anchor="w")

    def _create_logo_image(self, size: int) -> tk.PhotoImage:
        image = tk.PhotoImage(width=size, height=size)
        image.put("#eef4ff", to=(0, 0, size, size))

        left_x0 = int(size * 0.12)
        left_x1 = int(size * 0.40)
        image.put("#0f766e", to=(left_x0, int(size * 0.18), left_x1, int(size * 0.84)))
        image.put("#ffffff", to=(left_x0 + 2, int(size * 0.26), left_x1 - 2, int(size * 0.30)))
        image.put("#ffffff", to=(left_x0 + 2, int(size * 0.39), left_x1 - 2, int(size * 0.43)))
        image.put("#ffffff", to=(left_x0 + 2, int(size * 0.52), left_x1 - 6, int(size * 0.56)))

        node_size = max(4, int(size * 0.16))
        node1 = (int(size * 0.64), int(size * 0.18))
        node2 = (int(size * 0.72), int(size * 0.44))
        node3 = (int(size * 0.60), int(size * 0.68))
        for x, y in (node1, node2, node3):
            image.put("#1d4ed8", to=(x, y, x + node_size, y + node_size))

        image.put("#64748b", to=(left_x1, int(size * 0.30), node1[0], int(size * 0.33)))
        image.put("#64748b", to=(left_x1, int(size * 0.47), node2[0], int(size * 0.50)))
        image.put("#64748b", to=(left_x1, int(size * 0.66), node3[0], int(size * 0.69)))

        return image
