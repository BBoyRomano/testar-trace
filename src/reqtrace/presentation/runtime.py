"""Shared presentation runtime helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from reqtrace.application.results import (
    EvidenceSnapshot,
    RequirementSnapshot,
    TraceabilityRequest,
    TraceabilityResult,
)
from reqtrace.application.services.run_result_service import (
    export_result_json as export_result_json_use_case,
)
from reqtrace.application.services.run_result_service import (
    import_result_json as import_result_json_use_case,
)
from reqtrace.application.services.traceability_service import (
    TraceabilityService,
    build_default_traceability_service,
)
from reqtrace.ingestion.common.mapping import (
    map_evidence_batch_to_domain,
    map_requirements_batch_to_domain,
)
from reqtrace.ingestion.common.registry import IngestionRegistry, build_default_registry
from reqtrace.presentation.exceptions import RunInputValidationError

logger = logging.getLogger(__name__)

SUPPORTED_REQUIREMENTS_FORMATS = ("markdown", "json")
SUPPORTED_EVIDENCE_FORMATS = ("testar",)
_REQUIREMENTS_FORMAT_ALIASES = {
    "md": "markdown",
    "markdown": "markdown",
    "json": "json",
}
_EVIDENCE_FORMAT_ALIASES = {
    "testar": "testar",
}

REQUIREMENT_FILE_PATTERNS = {
    "markdown": "*.md",
    "json": "*.json",
}


@dataclass(slots=True)
class RunInput:
    requirements_path: Path | None = None
    evidence_path: Path | None = None
    requirements_paths: list[Path] = field(default_factory=list)
    requirements_format: str = "markdown"
    evidence_format: str = "testar"
    method_name: str = "baseline"
    selected_requirement_ids: list[str] = field(default_factory=list)
    selected_evidence_run_ids: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_requirements_format(value: str) -> str:
    canonical = _REQUIREMENTS_FORMAT_ALIASES.get(value.strip().lower())
    if canonical is None:
        raise RunInputValidationError(
            f"Unsupported requirements format: {value!r}. "
            f"Supported values: {', '.join(SUPPORTED_REQUIREMENTS_FORMATS)}."
        )
    return canonical


def normalize_evidence_format(value: str) -> str:
    canonical = _EVIDENCE_FORMAT_ALIASES.get(value.strip().lower())
    if canonical is None:
        raise RunInputValidationError(
            f"Unsupported evidence format: {value!r}. "
            f"Supported values: {', '.join(SUPPORTED_EVIDENCE_FORMATS)}."
        )
    return canonical


def resolve_requirement_paths(run_input: RunInput) -> list[Path]:
    logger.debug(
        "Resolving requirement paths.",
        extra={"requirements_format": run_input.requirements_format},
    )
    requirements_format = normalize_requirements_format(run_input.requirements_format)
    raw_paths: list[Path] = []
    if run_input.requirements_paths:
        raw_paths.extend(run_input.requirements_paths)
    elif run_input.requirements_path is not None:
        raw_paths.append(run_input.requirements_path)
    if not raw_paths:
        raise RunInputValidationError("At least one requirements path must be provided.")
    resolved: list[Path] = []
    pattern = REQUIREMENT_FILE_PATTERNS.get(requirements_format)
    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.exists():
            raise RunInputValidationError(f"Requirements path does not exist: {path}")
        if path.is_dir():
            if pattern is None:
                raise RunInputValidationError(
                    f"Unsupported requirements format for directory input: {requirements_format}"
                )
            resolved.extend(sorted(p for p in path.glob(pattern) if p.is_file()))
        else:
            resolved.append(path)
    # Preserve order while deduplicating.
    resolved = list(dict.fromkeys(resolved))
    if not resolved:
        if pattern is None:
            raise RunInputValidationError("No requirement files were found.")
        raise RunInputValidationError(
            f"No requirement files matching pattern {pattern!r} were found."
        )
    logger.debug(
        "Resolved requirement paths.",
        extra={"resolved_requirement_path_count": len(resolved)},
    )
    return resolved


def build_request(
    run_input: RunInput, *, registry: IngestionRegistry | None = None
) -> TraceabilityRequest:
    logger.info(
        "Building traceability request.",
        extra={
            "method_name": run_input.method_name,
            "requirements_format": run_input.requirements_format,
            "evidence_format": run_input.evidence_format,
        },
    )
    registry = registry or build_default_registry()
    requirements_format = normalize_requirements_format(run_input.requirements_format)
    evidence_format = normalize_evidence_format(run_input.evidence_format)
    if run_input.evidence_path is None:
        raise RunInputValidationError("An evidence path must be provided.")
    evidence_path = Path(run_input.evidence_path)
    if not evidence_path.exists():
        raise RunInputValidationError(f"Evidence path does not exist: {evidence_path}")

    requirement_paths = resolve_requirement_paths(run_input)
    logger.info("Ingesting requirements sources (%d file(s)).", len(requirement_paths))
    combined_requirements_mapping = {
        "documents": [],
        "requirements": [],
        "fragments": [],
        "flows": [],
        "flow_edges": [],
    }
    for requirement_path in requirement_paths:
        logger.debug(
            "Ingesting requirements path.",
            extra={"requirements_path": str(requirement_path)},
        )
        batch = registry.ingest_requirements(requirements_format, requirement_path)
        mapping = map_requirements_batch_to_domain(batch)
        for key in combined_requirements_mapping:
            combined_requirements_mapping[key].extend(mapping[key])
    logger.info(
        "Requirements ingestion completed: files=%d requirements=%d fragments=%d flows=%d.",
        len(requirement_paths),
        len(combined_requirements_mapping["requirements"]),
        len(combined_requirements_mapping["fragments"]),
        len(combined_requirements_mapping["flows"]),
    )
    evidence_batch = registry.ingest_evidence(evidence_format, evidence_path)
    requirements = RequirementSnapshot.from_mapping(combined_requirements_mapping)
    evidence = EvidenceSnapshot.from_mapping(map_evidence_batch_to_domain(evidence_batch))
    logger.info(
        "Evidence ingestion completed: runs=%d states=%d transitions=%d actions=%d.",
        len(evidence.runs),
        len(evidence.states),
        len(evidence.transitions),
        len(evidence.actions),
    )
    metadata = {
        "requirements_format": requirements_format,
        "requirements_paths": [str(path) for path in requirement_paths],
        "evidence_format": evidence_format,
        "evidence_path": str(evidence_path),
        **run_input.metadata,
    }
    request = TraceabilityRequest(
        method_name=run_input.method_name,
        requirements=requirements,
        evidence=evidence,
        selected_requirement_ids=list(run_input.selected_requirement_ids),
        selected_evidence_run_ids=list(run_input.selected_evidence_run_ids),
        options=dict(run_input.options),
        metadata=metadata,
    )
    logger.info(
        "Traceability request built.",
        extra={
            "requirement_count": len(request.requirements.requirements),
            "run_count": len(request.evidence.runs),
        },
    )
    return request


def execute_run(
    run_input: RunInput,
    *,
    registry: IngestionRegistry | None = None,
    service: TraceabilityService | None = None,
) -> TraceabilityResult:
    logger.info("Executing traceability run.", extra={"method_name": run_input.method_name})
    request = build_request(run_input, registry=registry)
    service = service or build_default_traceability_service()
    result = service.execute(request)
    logger.info(
        "Traceability run completed.",
        extra={
            "run_id": result.run.id,
            "method_name": result.run.method_name,
            "status": str(result.run.status),
            "requirement_count": result.summary.requirement_count,
        },
    )
    return result


def export_result_json(result: TraceabilityResult, output_path: Path) -> None:
    logger.info(
        "Exporting traceability result.",
        extra={"run_id": result.run.id, "output_path": str(output_path)},
    )
    export_result_json_use_case(result, output_path)


def import_result_json(result_path: Path) -> TraceabilityResult:
    logger.info("Importing traceability result.", extra={"result_path": str(result_path)})
    result = import_result_json_use_case(result_path)
    logger.info(
        "Imported traceability result.",
        extra={"run_id": result.run.id, "method_name": result.run.method_name},
    )
    return result
