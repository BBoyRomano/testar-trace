from __future__ import annotations

from datetime import timedelta

from rich.console import Console
from rich.table import Table

from reqtrace.application.results import TraceabilityResult


def _format_duration(duration: timedelta) -> str:
    total_seconds = duration.total_seconds()
    if total_seconds < 0:
        return "n/a"
    if total_seconds < 60:
        return f"{total_seconds:.2f}s"
    whole_seconds = int(total_seconds)
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes}m {seconds:02d}s"


def _format_run_duration(result: TraceabilityResult) -> str:
    started_at = result.run.started_at
    ended_at = result.run.ended_at
    if started_at is None:
        return "n/a"
    if ended_at is None:
        return "running"
    return _format_duration(ended_at - started_at)


def _truncate_title(value: str, *, max_length: int = 64) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def _labelize(value: str) -> str:
    return value.replace("_", " ").title()


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_result(console: Console, result: TraceabilityResult) -> None:
    summary_table = Table(title="Traceability Summary")
    summary_table.add_column("Metric")
    summary_table.add_column("Value", justify="right")
    summary_table.add_row("Run ID", result.run.id)
    summary_table.add_row("Method", _labelize(result.run.method_name))
    summary_table.add_row("Status", _labelize(str(result.run.status)))
    summary_table.add_row("Duration", _format_run_duration(result))
    summary_table.add_row("Total Requirements (#)", str(result.summary.requirement_count))
    summary_table.add_row(
        "Analyzed Requirements (#)",
        str(result.summary.analyzed_requirement_count),
    )
    summary_table.add_row("Failed Requirements (#)", str(result.summary.failed_requirement_count))
    summary_table.add_row(
        "Fully Covered (#)",
        str(result.summary.global_coverage.fully_covered),
    )
    summary_table.add_row(
        "Main-Flow Only (#)",
        str(result.summary.global_coverage.main_only),
    )
    summary_table.add_row(
        "Alt-Flow Only (#)",
        str(result.summary.global_coverage.alt_only),
    )
    summary_table.add_row("Partially Covered (#)", str(result.summary.global_coverage.partial))
    summary_table.add_row("Uncovered (#)", str(result.summary.global_coverage.none))
    summary_table.add_row("Uncertain (#)", str(result.summary.global_coverage.uncertain))
    summary_table.add_row(
        "Requirements With Any Trace (#)",
        str(result.summary.global_coverage.requirements_with_any_trace),
    )
    summary_table.add_row(
        "Reqs With Main-Flow Trace (#)",
        str(result.summary.global_coverage.requirements_with_main_trace),
    )
    summary_table.add_row(
        "Reqs With Alt-Flow Trace (#)",
        str(result.summary.global_coverage.requirements_with_alt_trace),
    )
    summary_table.add_row("Trace Links (#)", str(result.summary.trace_link_count))
    if result.summary.trace_evidence_count != result.summary.trace_link_count:
        summary_table.add_row(
            "Supporting Evidence Items (#)",
            str(result.summary.trace_evidence_count),
        )
    summary_table.add_row(
        "Overall Coverage (%)",
        _format_percent(result.summary.global_coverage.overall_coverage_ratio),
    )
    summary_table.add_row(
        "Main-Flow Coverage (%)",
        _format_percent(result.summary.global_coverage.main_flow_coverage_ratio),
    )
    summary_table.add_row(
        "Alt-Flow Coverage (%)",
        _format_percent(result.summary.global_coverage.alt_flow_coverage_ratio),
    )
    summary_table.add_row(
        "Average Confidence (%)",
        _format_percent(result.summary.global_coverage.average_confidence),
    )
    console.print(summary_table)

    requirement_table = Table(title="Per-requirement Results")
    requirement_table.add_column("Requirement ID", no_wrap=True)
    requirement_table.add_column("External ID", no_wrap=True)
    requirement_table.add_column("Title")
    requirement_table.add_column("Coverage")
    requirement_table.add_column("Main Flow")
    requirement_table.add_column("Alt Flow")
    requirement_table.add_column("Confidence (%)", justify="right")
    requirement_table.add_column("Matched Instances (#)", justify="right")
    requirement_table.add_column("Links (#)", justify="right")
    requirement_table.add_column("Evidence (#)", justify="right")

    for item in result.requirement_results:
        requirement_table.add_row(
            item.requirement_id,
            item.requirement_external_id or "-",
            _truncate_title(item.requirement_title),
            _labelize(str(item.coverage.status)),
            _labelize(str(item.coverage.main_flow_status)),
            _labelize(str(item.coverage.alt_flow_status)),
            _format_percent(item.coverage.confidence),
            str(len(item.execution_instances)),
            str(len(item.trace_links)),
            str(len(item.trace_evidence)),
        )
    console.print(requirement_table)
