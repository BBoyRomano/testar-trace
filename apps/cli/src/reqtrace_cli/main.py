"""Main entry point for the ReqTrace CLI."""

import json
import logging
from pathlib import Path
from typing import Any, TypeGuard

from reqtrace import analyze_traceability
from reqtrace.registry import available_trace_methods
from reqtrace_adapters import load_evidence, load_requirements

from ._args import build_parser
from ._logging import configure_logging
from ._rendering import (
    render_formats_text,
    render_report_text,
    render_requirements_text,
)
from ._serialize import dumps_json, load_json_file, to_plain_data, write_json

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    handler_name = args.handler_name
    if handler_name == "methods":
        return _handle_methods()
    if handler_name == "formats":
        return _handle_formats()
    if handler_name == "show_requirements":
        return _handle_show_requirements(args)
    if handler_name == "analyze":
        return _handle_analyze(args)
    if handler_name == "show_report":
        return _handle_show_report(args)

    parser.error(f"Unknown command handler: {handler_name}")
    return 2


def _handle_methods() -> int:
    """List available methods."""
    for name in available_trace_methods():
        print(name)
    return 0


def _handle_formats() -> int:
    """Show supported input format information."""
    print(render_formats_text())
    return 0


def _handle_show_requirements(args: Any) -> int:
    """Load and render requirements from CLI arguments."""
    requirements = load_requirements(
        Path(args.requirements),
        kind=args.requirements_kind,
        format=args.requirements_format,
        pattern=args.requirements_pattern,
        recursive=args.requirements_recursive,
    )
    data = to_plain_data(requirements)
    if args.json:
        print(dumps_json(_filter_requirements(data, args.requirement_id)))
        return 0

    print(render_requirements_text(data, requirement_id=args.requirement_id))
    return 0


def _handle_analyze(args: Any) -> int:
    """Run analysis from CLI arguments."""
    requirements_path = Path(args.requirements)
    evidence_path = Path(args.evidence)

    requirements = load_requirements(
        requirements_path,
        kind=args.requirements_kind,
        format=args.requirements_format,
        pattern=args.requirements_pattern,
        recursive=args.requirements_recursive,
    )
    evidence = load_evidence(
        evidence_path,
        kind=args.evidence_kind,
        format=args.evidence_format,
    )

    logger.info(
        "Running traceability analysis.",
        extra={
            "requirements": str(requirements_path),
            "evidence": str(evidence_path),
            "method": args.method,
        },
    )
    analysis_result = analyze_traceability(
        requirements,
        evidence,
        method=args.method,
    )
    report = to_plain_data(analysis_result)

    if args.output:
        write_json(Path(args.output), report)
        logger.info(
            "Wrote traceability report JSON.", extra={"output": str(args.output)}
        )

    _print_report(
        report,
        json_output=args.json,
        summary_only=args.summary_only,
        requirement_id=args.requirement_id,
        limit=None if args.all else args.limit,
        with_details=args.details or args.all,
        with_occurrences=args.with_occurrences,
        with_alignments=args.with_alignments,
    )
    return 0


def _handle_show_report(args: Any) -> int:
    """Render a previously saved traceability report file."""
    report_path = Path(args.report)
    report = load_json_file(report_path)
    _print_report(
        report,
        json_output=args.json,
        summary_only=args.summary_only,
        requirement_id=args.requirement_id,
        limit=None if args.all else args.limit,
        with_details=args.details or args.all,
        with_occurrences=args.with_occurrences,
        with_alignments=args.with_alignments,
    )
    return 0


def _print_report(
    report: Any,
    *,
    json_output: bool,
    summary_only: bool,
    requirement_id: str | None,
    limit: int | None,
    with_details: bool,
    with_occurrences: bool,
    with_alignments: bool,
) -> None:
    """Print one traceability report object in the requested output mode."""
    if json_output:
        if requirement_id and isinstance(report, dict):
            print(dumps_json(_filter_report(report, requirement_id)))
            return
        if (
            summary_only
            and isinstance(report, dict)
            and isinstance(report.get("summary"), dict)
        ):
            print(dumps_json(report["summary"]))
            return
        print(dumps_json(report))
        return

    if isinstance(report, dict):
        print(
            render_report_text(
                report,
                summary_only=summary_only,
                requirement_id=requirement_id,
                limit=limit,
                with_links=with_details,
                with_occurrences=with_details or with_occurrences,
                with_alignments=with_details or with_alignments,
            )
        )
        return

    print(json.dumps(to_plain_data(report), ensure_ascii=False, indent=2))


def _filter_requirements(data: Any, requirement_id: str | None) -> Any:
    if not requirement_id or not isinstance(data, dict):
        return data

    requirements = data.get("requirements")
    fragments = data.get("fragments")
    scenarios = data.get("scenarios")
    if isinstance(requirements, list):
        data = dict(data)
        data["requirements"] = [
            requirement
            for requirement in requirements
            if _is_object_dict(requirement) and requirement.get("id") == requirement_id
        ]
    if isinstance(fragments, list):
        data = dict(data)
        data["fragments"] = [
            fragment
            for fragment in fragments
            if _is_object_dict(fragment)
            and fragment.get("requirement_id") == requirement_id
        ]
    if isinstance(scenarios, list):
        data = dict(data)
        data["scenarios"] = [
            scenario
            for scenario in scenarios
            if _is_object_dict(scenario)
            and scenario.get("requirement_id") == requirement_id
        ]
    return data


def _filter_report(report: dict[str, object], requirement_id: str) -> dict[str, object]:
    filtered = dict(report)
    for key in ("coverage", "links", "occurrences", "fragment_alignments"):
        value = filtered.get(key)
        if not isinstance(value, list):
            continue
        filtered[key] = [
            item
            for item in value
            if _is_object_dict(item) and item.get("requirement_id") == requirement_id
        ]
    return filtered


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)
