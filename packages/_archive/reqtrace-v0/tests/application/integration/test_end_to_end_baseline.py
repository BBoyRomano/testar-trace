from pathlib import Path

import pytest

from reqtrace.application.results import EvidenceSnapshot, RequirementSnapshot, TraceabilityRequest
from reqtrace.application.services.traceability_service import build_default_traceability_service
from reqtrace.ingestion.common.mapping import (
    map_evidence_batch_to_domain,
    map_requirements_batch_to_domain,
)
from reqtrace.ingestion.common.registry import build_default_registry

pytestmark = pytest.mark.integration


def test_end_to_end_baseline_runs_from_ingestion(
    tmp_path: Path,
    write_minimal_requirement_markdown,
    write_minimal_testar_model_file,
) -> None:
    requirements_path = tmp_path / "requirements.md"
    write_minimal_requirement_markdown(requirements_path)

    evidence_path = tmp_path / "testar.json"
    write_minimal_testar_model_file(evidence_path)

    registry = build_default_registry()
    requirements_batch = registry.ingest_requirements("markdown", requirements_path)
    evidence_batch = registry.ingest_evidence("testar", evidence_path)

    request = TraceabilityRequest(
        requirements=RequirementSnapshot.from_mapping(
            map_requirements_batch_to_domain(requirements_batch)
        ),
        evidence=EvidenceSnapshot.from_mapping(map_evidence_batch_to_domain(evidence_batch)),
    )

    result = build_default_traceability_service().execute(request)

    assert result.summary.requirement_count == 1
    assert result.summary.requirement_fragment_count == 3
    assert result.summary.trace_link_count == 0
