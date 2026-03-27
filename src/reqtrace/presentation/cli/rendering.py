from __future__ import annotations

from rich.console import Console
from rich.table import Table

from reqtrace.application.results import TraceabilityResult


def render_result(console: Console, result: TraceabilityResult) -> None:
    summary_table = Table(title="Traceability Summary")
    summary_table.add_column("Metric")
    summary_table.add_column("Value", justify="right")
    summary_table.add_row("Run ID", result.run.id)
    summary_table.add_row("Method", result.run.method_name)
    summary_table.add_row("Status", str(result.run.status))
    summary_table.add_row("Requirements", str(result.summary.requirement_count))
    summary_table.add_row("Analyzed", str(result.summary.analyzed_requirement_count))
    summary_table.add_row("Failed", str(result.summary.failed_requirement_count))
    summary_table.add_row("Covered", str(result.summary.covered_requirement_count))
    summary_table.add_row("Partially covered", str(result.summary.partially_covered_requirement_count))
    summary_table.add_row("Uncovered", str(result.summary.uncovered_requirement_count))
    summary_table.add_row("Uncertain", str(result.summary.uncertain_requirement_count))
    summary_table.add_row("Requirement fragments", str(result.summary.requirement_fragment_count))
    summary_table.add_row("Covered fragments", str(result.summary.covered_fragment_count))
    summary_table.add_row("Trace links", str(result.summary.trace_link_count))
    summary_table.add_row("Trace evidence", str(result.summary.trace_evidence_count))
    console.print(summary_table)

    requirement_table = Table(title="Per-requirement Results")
    requirement_table.add_column("Requirement ID")
    requirement_table.add_column("Title")
    requirement_table.add_column("Status")
    requirement_table.add_column("Coverage")
    requirement_table.add_column("Confidence")
    requirement_table.add_column("Links", justify="right")
    requirement_table.add_column("Evidence", justify="right")

    for item in result.requirement_results:
        coverage = "n/a"
        confidence = "n/a"
        if item.artifact_coverage is not None:
            coverage = str(item.artifact_coverage.coverage_status)
            confidence = (
                f"{item.artifact_coverage.confidence_ratio:.2f}"
                if item.artifact_coverage.confidence_ratio is not None
                else "n/a"
            )
        requirement_table.add_row(
            item.requirement_id,
            item.requirement_title,
            str(item.status),
            coverage,
            confidence,
            str(len(item.trace_links)),
            str(len(item.trace_evidence)),
        )

    console.print(requirement_table)
