from __future__ import annotations

from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Static

from reqtrace.application.analyze_coverage import (
    AnalyzeCoverageRequest,
    AnalyzeCoverageUseCase,
)


@dataclass(frozen=True)
class UiInput:
    state_path: str
    requirements_path: str


class ReqTraceApp(App[None]):
    TITLE = "ReqTrace"
    SUB_TITLE = "Requirements traceability"

    def __init__(self, ui_input: UiInput) -> None:
        super().__init__()
        self.ui_input = ui_input

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Loading analysis...", id="summary")
        yield DataTable(id="results")
        yield Footer()

    def on_mount(self) -> None:
        summary = self.query_one("#summary", Static)
        table = self.query_one("#results", DataTable)

        table.add_columns("Requirement", "Status",
                          "Matched Units", "Total Units")

        use_case = AnalyzeCoverageUseCase()
        report = use_case.execute(
            AnalyzeCoverageRequest(
                state_path=self.ui_input.state_path,
                requirements_path=self.ui_input.requirements_path,
            )
        )

        summary.update(
            "\n".join(
                [
                    f"Requirements: {report.summary.total_requirements}",
                    f"Found: {report.summary.found}",
                    f"Partially found: {report.summary.partially_found}",
                    f"Not found: {report.summary.not_found}",
                ]
            )
        )

        for result in report.results:
            matched_units = sum(
                1
                for unit_result in result.unit_results
                if unit_result.status.value in {"found", "partially_found"}
            )
            total_units = len(result.unit_results)

            table.add_row(
                result.requirement_id,
                result.status.value,
                str(matched_units),
                str(total_units),
            )
