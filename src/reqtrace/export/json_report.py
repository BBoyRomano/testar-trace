from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reqtrace.domain.coverage import (
    CoverageReport,
    MatchEvidence,
    RequirementOccurrence,
    RequirementOccurrenceStep,
    RequirementResult,
    RequirementUnitResult,
)


def _match_evidence_to_dict(evidence: MatchEvidence) -> dict[str, Any]:
    return {
        "state_ids": list(evidence.state_ids),
        "transition_ids": list(evidence.transition_ids),
        "observations": list(evidence.observations),
        "explanation": evidence.explanation,
        "metadata": dict(evidence.metadata),
    }


def _requirement_unit_result_to_dict(result: RequirementUnitResult) -> dict[str, Any]:
    return {
        "requirement_id": result.requirement_id,
        "unit_id": result.unit_id,
        "status": result.status.value,
        "evidence": [_match_evidence_to_dict(item) for item in result.evidence],
        "metadata": dict(result.metadata),
    }


def _occurrence_step_to_dict(step: RequirementOccurrenceStep) -> dict[str, Any]:
    return {
        "unit_id": step.unit_id,
        "status": step.status.value,
        "evidence": [_match_evidence_to_dict(item) for item in step.evidence],
        "metadata": dict(step.metadata),
    }


def _occurrence_to_dict(occurrence: RequirementOccurrence) -> dict[str, Any]:
    return {
        "occurrence_id": occurrence.occurrence_id,
        "status": occurrence.status.value,
        "state_ids": list(occurrence.state_ids),
        "transition_ids": list(occurrence.transition_ids),
        "steps": [_occurrence_step_to_dict(item) for item in occurrence.steps],
        "metadata": dict(occurrence.metadata),
    }


def _requirement_result_to_dict(result: RequirementResult) -> dict[str, Any]:
    return {
        "requirement_id": result.requirement_id,
        "status": result.status.value,
        "unit_results": [
            _requirement_unit_result_to_dict(item) for item in result.unit_results
        ],
        "occurrences": [_occurrence_to_dict(item) for item in result.occurrences],
        "metadata": dict(result.metadata),
    }


def report_to_dict(report: CoverageReport) -> dict[str, Any]:
    return {
        "results": [_requirement_result_to_dict(item) for item in report.results],
        "summary": {
            "total_requirements": report.summary.total_requirements,
            "found": report.summary.found,
            "partially_found": report.summary.partially_found,
            "not_found": report.summary.not_found,
        },
        "metadata": dict(report.metadata),
    }


def write_json_report(report: CoverageReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report_to_dict(report), indent=2) + "\n",
        encoding="utf-8",
    )
