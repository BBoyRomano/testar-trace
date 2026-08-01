from pathlib import Path

from reqtrace_cli._args import build_parser
from reqtrace_cli._rendering import (
    render_formats_text,
    render_report_text,
    render_requirements_text,
)
from reqtrace_cli._serialize import to_plain_data


def test_build_parser_accepts_methods_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["methods"])
    assert args.handler_name == "methods"


def test_build_parser_accepts_show_report_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["show-report", "report.json", "--summary-only"])
    assert args.handler_name == "show_report"
    assert args.summary_only is True


def test_build_parser_accepts_show_requirements_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "show-requirements",
            "--requirements",
            "requirements",
            "--requirements-kind",
            "use-case",
            "--requirement-id",
            "req-1",
        ],
    )
    assert args.handler_name == "show_requirements"
    assert args.requirements == "requirements"
    assert args.requirement_id == "req-1"


def test_build_parser_accepts_evidence_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["analyze", "--requirements", "req.md", "--evidence", "ev.json"]
    )
    assert args.handler_name == "analyze"
    assert args.evidence == "ev.json"
    assert args.method == "sequence"
    assert args.requirements_kind == "use-case"
    assert args.evidence_kind == "testar-state-model"


def test_build_parser_accepts_input_kind_options() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "analyze",
            "--requirements",
            "requirements",
            "--requirements-kind",
            "gherkin",
            "--requirements-format",
            "feature",
            "--requirements-pattern",
            "*.feature",
            "--requirements-recursive",
            "--evidence",
            "ev.json",
            "--evidence-kind",
            "testar-state-model",
            "--evidence-format",
            "json",
        ],
    )

    assert args.requirements_kind == "gherkin"
    assert args.requirements_format == "feature"
    assert args.requirements_pattern == "*.feature"
    assert args.requirements_recursive is True
    assert args.evidence_kind == "testar-state-model"
    assert args.evidence_format == "json"


def test_render_formats_lists_registered_parsers() -> None:
    text = render_formats_text()
    assert "ReqTrace Input Parsers" in text
    assert "requirements/use-case/md" in text
    assert "evidence/testar-state-model/json" in text


def test_render_report_text_renders_summary() -> None:
    report = {
        "id": "noop",
        "title": "No-op traceability result",
        "created_at": "2026-04-23T00:00:00+00:00",
        "metadata": {"method": "noop"},
        "summary": {
            "total_requirements": 2,
            "covered_requirements": 0,
            "partially_covered_requirements": 1,
            "uncovered_requirements": 1,
            "total_links": 3,
            "metadata": {"requirements_coverage_ratio": 0.25},
        },
        "coverage": [],
        "links": [],
    }
    text = render_report_text(report)
    assert "ReqTrace Report" in text
    assert "Requirements: 2" in text
    assert "Requirements coverage: 0.250" in text
    assert "Links: 3" in text


def test_render_report_text_does_not_limit_coverage() -> None:
    report = {
        "id": "sequence",
        "title": "Sequence traceability result",
        "created_at": "2026-04-27T00:00:00+00:00",
        "metadata": {"method": "sequence"},
        "summary": {
            "total_requirements": 2,
            "covered_requirements": 2,
            "partially_covered_requirements": 0,
            "uncovered_requirements": 0,
            "total_links": 0,
        },
        "coverage": [
            {
                "requirement_id": "req-1",
                "status": "covered",
                "coverage_ratio": 1.0,
            },
            {
                "requirement_id": "req-2",
                "status": "covered",
                "coverage_ratio": 1.0,
            },
        ],
        "links": [],
    }

    text = render_report_text(report, limit=1)

    assert "req-1: covered" in text
    assert "req-2: covered" in text


def test_render_report_text_can_focus_occurrences_and_alignments() -> None:
    report = {
        "id": "sequence",
        "title": "Sequence traceability result",
        "created_at": "2026-04-27T00:00:00+00:00",
        "metadata": {"method": "sequence"},
        "summary": {
            "total_requirements": 1,
            "covered_requirements": 0,
            "partially_covered_requirements": 1,
            "uncovered_requirements": 0,
            "total_links": 1,
        },
        "coverage": [
            {
                "requirement_id": "req-1",
                "status": "partially-covered",
                "coverage_ratio": 0.5,
                "rationale": (
                    "1/2 scenarios fully covered; 0 partially covered; 1 not covered."
                ),
                "metadata": {
                    "requirement_title": "Login",
                    "scenario_coverage": [
                        {
                            "scenario_id": "req-1:scenario:main",
                            "kind": "main",
                            "branch_id": None,
                            "status": "covered",
                            "coverage_ratio": 1.0,
                            "matched_fragment_count": 2,
                            "total_fragment_count": 2,
                        },
                        {
                            "scenario_id": "req-1:scenario:alt",
                            "kind": "alternative",
                            "branch_id": "alt-1",
                            "status": "not-covered",
                            "coverage_ratio": 0.0,
                            "matched_fragment_count": 0,
                            "total_fragment_count": 2,
                        },
                    ],
                },
            }
        ],
        "links": [
            {
                "requirement_id": "req-1",
                "evidence_ids": ["transition-1"],
                "score": 0.5,
            }
        ],
        "occurrences": [
            {
                "id": "occ-1",
                "requirement_id": "req-1",
                "status": "partial",
                "score": 0.5,
                "evidence_path": [
                    {"kind": "transition", "evidence_id": "transition-1"}
                ],
                "metadata": {
                    "variant": "main",
                    "matched_fragment_count": 1,
                    "total_fragment_count": 2,
                },
            }
        ],
        "fragment_alignments": [
            {
                "requirement_id": "req-1",
                "fragment_id": "fragment-1",
                "score": 0.5,
                "evidence_refs": [
                    {"kind": "transition", "evidence_id": "transition-1"}
                ],
            }
        ],
    }

    text = render_report_text(
        report,
        requirement_id="req-1",
        with_occurrences=True,
        with_alignments=True,
    )

    assert "Requirement filter: req-1" in text
    assert "req-1: Login: partially-covered (0.500)" in text
    assert "req-1:scenario:main (main): covered (1.000) 2/2 fragments" in text
    assert (
        "req-1:scenario:alt (alternative [alt-1]): not-covered (0.000) 0/2 fragments"
    ) in text
    assert "Occurrences" in text
    assert "Fragment Alignments" in text
    assert "fragment-1 -> transition:transition-1" in text


def test_render_requirements_text_groups_fragments() -> None:
    text = render_requirements_text(
        {
            "requirements": [
                {"id": "req-1", "title": "Login"},
                {"id": "req-2", "title": "Logout"},
            ],
            "fragments": [
                {
                    "id": "fragment-1",
                    "requirement_id": "req-1",
                    "kind": "main_step",
                    "order_index": 0,
                    "text": "Submit login form",
                }
            ],
            "scenarios": [
                {
                    "id": "req-1:scenario:main",
                    "requirement_id": "req-1",
                    "kind": "main",
                    "title": "Main flow",
                    "fragment_ids": ["fragment-1"],
                    "order_index": 0,
                    "metadata": {"source_kind": "main_flow"},
                }
            ],
        },
        requirement_id="req-1",
    )

    assert "Requirements: 1" in text
    assert "Scenarios: 1" in text
    assert "req-1: Login" in text
    assert "fragment-1" in text
    assert "req-1:scenario:main" in text
    assert "req-2" not in text


def test_to_plain_data_converts_path() -> None:
    assert to_plain_data(Path("report.json")) == "report.json"
