from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.requirements.enums import RequirementKind
from reqtrace.ingestion.common.mapping import map_requirements_batch_to_domain
from reqtrace.ingestion.common.models import NormalizedRequirementBatch, NormalizedRequirementRecord


def test_requirement_batch_maps_to_domain_models() -> None:
    batch = NormalizedRequirementBatch(
        requirements=[
            NormalizedRequirementRecord(
                id="req-1",
                kind=RequirementKind.USE_CASE,
                title="Sample requirement",
                source_type=SourceType.FILE,
                source_name="sample",
            )
        ]
    )

    mapped = map_requirements_batch_to_domain(batch)

    assert len(mapped["requirements"]) == 1
    assert mapped["requirements"][0].title == "Sample requirement"
