from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class ReqTraceGuiView:
    def __init__(
        self,
        *,
        methods: list[str],
        requirements_formats: list[str],
        evidence_formats: list[str],
        on_browse_requirements_file: Callable[[], None],
        on_browse_requirements_dir: Callable[[], None],
        on_browse_evidence: Callable[[], None],
        on_browse_evidence_dir: Callable[[], None],
        on_start_run: Callable[[], None],
        on_import_result: Callable[[], None],
        on_export_selected: Callable[[], None],
        on_run_selected: Callable[[], None],
        on_requirement_selected: Callable[[], None],
    ) -> None:
        self.root = tk.Tk()
        self.root.title("ReqTrace")
        self.root.geometry("1100x700")

        self.requirements_path_var = tk.StringVar()
        self.evidence_path_var = tk.StringVar()
        self.method_var = tk.StringVar(value=methods[0] if methods else "baseline")
        self.requirements_format_var = tk.StringVar(
            value=requirements_formats[0] if requirements_formats else "markdown"
        )
        self.evidence_format_var = tk.StringVar(
            value=evidence_formats[0] if evidence_formats else "testar"
        )

        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        config = ttk.LabelFrame(outer, text="Run configuration", padding=8)
        config.pack(fill=tk.X)

        ttk.Label(config, text="Requirements path").grid(row=0, column=0, sticky="w")
        ttk.Entry(config, textvariable=self.requirements_path_var, width=80).grid(
            row=0, column=1, sticky="ew", padx=6
        )
        browse_req = ttk.Frame(config)
        browse_req.grid(row=0, column=2)
        ttk.Button(
            browse_req,
            text="File",
            command=on_browse_requirements_file,
        ).pack(side=tk.LEFT)
        ttk.Button(
            browse_req,
            text="Dir",
            command=on_browse_requirements_dir,
        ).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(config, text="Evidence path").grid(row=1, column=0, sticky="w")
        ttk.Entry(config, textvariable=self.evidence_path_var, width=80).grid(
            row=1, column=1, sticky="ew", padx=6
        )
        browse_evidence = ttk.Frame(config)
        browse_evidence.grid(row=1, column=2)
        ttk.Button(browse_evidence, text="File", command=on_browse_evidence).pack(side=tk.LEFT)
        ttk.Button(browse_evidence, text="Dir", command=on_browse_evidence_dir).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        ttk.Label(config, text="Requirements format").grid(row=2, column=0, sticky="w")
        ttk.Combobox(
            config,
            textvariable=self.requirements_format_var,
            values=requirements_formats,
            state="readonly",
            width=20,
        ).grid(row=2, column=1, sticky="w", padx=6, pady=(4, 0))

        ttk.Label(config, text="Evidence format").grid(row=3, column=0, sticky="w")
        ttk.Combobox(
            config,
            textvariable=self.evidence_format_var,
            values=evidence_formats,
            state="readonly",
            width=20,
        ).grid(row=3, column=1, sticky="w", padx=6, pady=(4, 0))

        ttk.Label(config, text="Method").grid(row=4, column=0, sticky="w")
        ttk.Combobox(
            config,
            textvariable=self.method_var,
            values=methods,
            state="readonly",
            width=20,
        ).grid(row=4, column=1, sticky="w", padx=6, pady=(4, 0))

        action_bar = ttk.Frame(config)
        action_bar.grid(row=5, column=1, sticky="w", pady=(8, 0))
        ttk.Button(action_bar, text="Start run", command=on_start_run).pack(side=tk.LEFT)
        ttk.Button(action_bar, text="Import result", command=on_import_result).pack(
            side=tk.LEFT,
            padx=(8, 0),
        )
        ttk.Button(action_bar, text="Export selected", command=on_export_selected).pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

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
        self.runs_list.bind("<<ListboxSelect>>", lambda _event: on_run_selected())

        summary_frame = ttk.LabelFrame(right, text="Run summary", padding=8)
        summary_frame.pack(fill=tk.X)
        self.summary_text = tk.Text(summary_frame, height=10, wrap="word")
        self.summary_text.pack(fill=tk.X)

        req_frame = ttk.LabelFrame(right, text="Requirement results", padding=8)
        req_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
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
        self.requirement_table.pack(fill=tk.BOTH, expand=True)
        self.requirement_table.bind(
            "<<TreeviewSelect>>", lambda _event: on_requirement_selected()
        )

        detail_frame = ttk.LabelFrame(right, text="Requirement detail", padding=8)
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.detail_text = tk.Text(detail_frame, height=10, wrap="word")
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def run(self) -> None:
        self.root.mainloop()
