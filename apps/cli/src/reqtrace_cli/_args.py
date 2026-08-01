"""Argument parsing for the ReqTrace CLI."""

import argparse
from importlib.metadata import PackageNotFoundError, version


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="reqtrace",
        description="ReqTrace command-line interface.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=_cli_version(),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    methods_parser = subparsers.add_parser(
        "methods",
        help="List available traceability methods.",
        description="List available traceability methods.",
    )
    methods_parser.set_defaults(handler_name="methods")

    formats_parser = subparsers.add_parser(
        "formats",
        help="Show registered input parsers.",
        description="Show registered input parsers.",
    )
    formats_parser.set_defaults(handler_name="formats")

    requirements_parser = subparsers.add_parser(
        "show-requirements",
        help="Load and render requirements.",
        description="Load and render requirements.",
    )
    requirements_parser.add_argument(
        "--requirements",
        required=True,
        help="Path to a requirements file or directory.",
    )
    requirements_parser.add_argument(
        "--requirements-kind",
        default="use-case",
        help="Requirement kind. Default: use-case.",
    )
    requirements_parser.add_argument(
        "--requirements-format",
        help=argparse.SUPPRESS,
    )
    requirements_parser.add_argument(
        "--requirements-pattern",
        default="*",
        help="File pattern when requirements is a directory.",
    )
    requirements_parser.add_argument(
        "--requirements-recursive",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    requirements_parser.add_argument(
        "--requirement-id",
        help="Show one requirement by ID.",
    )
    requirements_parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON to stdout instead of human-readable text.",
    )
    requirements_parser.set_defaults(handler_name="show_requirements")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run traceability analysis.",
        description="Run traceability analysis.",
    )
    analyze_parser.add_argument(
        "--requirements",
        required=True,
        help="Path to a requirements file or directory.",
    )
    analyze_parser.add_argument(
        "--evidence",
        required=True,
        help="Path to an evidence file.",
    )
    analyze_parser.add_argument(
        "--method",
        default="sequence",
        help="Traceability method. Default: sequence.",
    )
    analyze_parser.add_argument(
        "--requirements-kind",
        default="use-case",
        help="Requirement kind. Default: use-case.",
    )
    analyze_parser.add_argument(
        "--requirements-format",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--requirements-pattern",
        default="*",
        help="File pattern when requirements is a directory.",
    )
    analyze_parser.add_argument(
        "--requirements-recursive",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--evidence-kind",
        default="testar-state-model",
        help="Evidence kind. Default: testar-state-model.",
    )
    analyze_parser.add_argument(
        "--evidence-format",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--output",
        help="Write the traceability report JSON to this path.",
    )
    analyze_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only a summary view.",
    )
    analyze_parser.add_argument(
        "--requirement-id",
        help="Focus human-readable output on one requirement ID.",
    )
    analyze_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--details",
        action="store_true",
        help="Show links, occurrences, and fragment alignments.",
    )
    analyze_parser.add_argument(
        "--with-occurrences",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--with-alignments",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--all",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON to stdout instead of a human-readable summary.",
    )
    analyze_parser.set_defaults(handler_name="analyze")

    show_report_parser = subparsers.add_parser(
        "show-report",
        help="Render a previously exported traceability report JSON file.",
        description="Render a previously exported traceability report JSON file.",
    )
    show_report_parser.add_argument(
        "report",
        help="Path to an exported traceability report JSON file.",
    )
    show_report_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only a summary view.",
    )
    show_report_parser.add_argument(
        "--requirement-id",
        help="Focus output on one requirement ID.",
    )
    show_report_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help=argparse.SUPPRESS,
    )
    show_report_parser.add_argument(
        "--details",
        action="store_true",
        help="Show links, occurrences, and fragment alignments.",
    )
    show_report_parser.add_argument(
        "--with-occurrences",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    show_report_parser.add_argument(
        "--with-alignments",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    show_report_parser.add_argument(
        "--all",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    show_report_parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON to stdout instead of a human-readable summary.",
    )
    show_report_parser.set_defaults(handler_name="show_report")

    return parser


def _cli_version() -> str:
    try:
        package_version = version("reqtrace-cli")
    except PackageNotFoundError:
        package_version = "0.0.0"
    return f"reqtrace-cli {package_version}"
