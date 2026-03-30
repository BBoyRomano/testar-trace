"""Shared presentation runtime helpers.

These helpers bridge file-based user input to the application layer while
keeping the CLI and GUI thin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timezone
from pathlib import Path
from typing import Any

from reqtrace.application.results import EvidenceSnapshot, RequirementSnapshot, TraceabilityRequest, TraceabilityResult
from reqtrace.application.services.traceability_service import TraceabilityService, build_default_traceability_service
from reqtrace.ingestion.common.mapping import map_evidence_batch_to_domain, map_requirements_batch_to_domain
from reqtrace.ingestion.common.registry import IngestionRegistry, build_default_registry


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


def resolve_requirement_paths(run_input: RunInput) -> list[Path]:
    raw_paths: list[Path] = []
    if run_input.requirements_paths:
        raw_paths.extend(run_input.requirements_paths)
    elif run_input.requirements_path is not None:
        raw_paths.append(run_input.requirements_path)

    if not raw_paths:
        raise ValueError("At least one requirements path must be provided.")

    resolved: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_dir():
            resolved.extend(sorted(p for p in path.glob('*.md') if p.is_file()))
        else:
            resolved.append(path)

    if not resolved:
        raise ValueError("No requirement markdown files were found.")
    return resolved


def build_request(run_input: RunInput, *, registry: IngestionRegistry | None = None) -> TraceabilityRequest:
    registry = registry or build_default_registry()

    requirement_paths = resolve_requirement_paths(run_input)

    combined_requirements_mapping = {
        "requirements": [],
        "fragments": [],
        "flows": [],
        "flow_edges": [],
    }
    for requirement_path in requirement_paths:
        batch = registry.ingest_requirements(run_input.requirements_format, requirement_path)
        mapping = map_requirements_batch_to_domain(batch)
        for key in combined_requirements_mapping:
            combined_requirements_mapping[key].extend(mapping[key])

    evidence_batch = registry.ingest_evidence(run_input.evidence_format, run_input.evidence_path)

    requirements = RequirementSnapshot.from_mapping(combined_requirements_mapping)
    evidence = EvidenceSnapshot.from_mapping(map_evidence_batch_to_domain(evidence_batch))

    metadata = {
        "requirements_format": run_input.requirements_format,
        "requirements_paths": [str(path) for path in requirement_paths],
        "evidence_format": run_input.evidence_format,
        "evidence_path": str(run_input.evidence_path),
        **run_input.metadata,
    }

    return TraceabilityRequest(
        method_name=run_input.method_name,
        requirements=requirements,
        evidence=evidence,
        selected_requirement_ids=list(run_input.selected_requirement_ids),
        selected_evidence_run_ids=list(run_input.selected_evidence_run_ids),
        options=dict(run_input.options),
        metadata=metadata,
    )


def execute_run(
    run_input: RunInput,
    *,
    registry: IngestionRegistry | None = None,
    service: TraceabilityService | None = None,
) -> TraceabilityResult:
    request = build_request(run_input, registry=registry)
    service = service or build_default_traceability_service()
    return service.execute(request)


def export_result_json(result: TraceabilityResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def import_result_json(result_path: Path) -> TraceabilityResult:
    return TraceabilityResult.model_validate_json(result_path.read_text(encoding="utf-8"))


def infer_sut_name(*paths: Path) -> str:
    """Infer SUT name from a path like suts/<sut>/... ."""
    for path in paths:
        parts = list(path.parts)
        if "suts" in parts:
            idx = parts.index("suts")
            if idx + 1 < len(parts):
                return parts[idx + 1]
    return "run"


def default_export_path(run_input: RunInput, result: TraceabilityResult) -> Path:
    """Compute a stable default export path for a run.

    Pattern: <sut>-<method>-<timestamp>.json
    Directory: suts/<sut>/exports if the inputs live under suts/, else ./exports
    """
    requirement_paths = resolve_requirement_paths(run_input)
    sut = infer_sut_name(*requirement_paths, run_input.evidence_path)
    ts = result.run.started_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    filename = f"{sut}-{run_input.method_name}-{ts}.json"
    if sut != "run":
        return Path("suts") / sut / "exports" / filename
    return Path("exports") / filename
