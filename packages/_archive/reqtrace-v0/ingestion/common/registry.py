from __future__ import annotations

from dataclasses import dataclass, field

from reqtrace.ingestion.common.exceptions import UnsupportedSourceError
from reqtrace.ingestion.common.interfaces import (
    EvidenceAdapter,
    EvidenceLoader,
    RequirementsAdapter,
    RequirementsLoader,
)
from reqtrace.ingestion.common.models import NormalizedEvidenceBatch, NormalizedRequirementBatch
from reqtrace.ingestion.evidence.adapter import DefaultEvidenceNormalizer
from reqtrace.ingestion.evidence.testar.loader import TestarLoader
from reqtrace.ingestion.requirements.adapter import (
    DefaultRequirementsNormalizer,
)
from reqtrace.ingestion.requirements.json.loader import JsonRequirementsLoader
from reqtrace.ingestion.requirements.markdown.loader import MarkdownRequirementsLoader


@dataclass
class IngestionRegistry:
    requirement_loaders: dict[str, RequirementsLoader] = field(default_factory=dict)
    evidence_loaders: dict[str, EvidenceLoader] = field(default_factory=dict)
    requirement_adapter: RequirementsAdapter | None = None
    evidence_adapter: EvidenceAdapter | None = None

    def register_requirement_loader(self, source_key: str, loader: RequirementsLoader) -> None:
        self.requirement_loaders[source_key] = loader

    def register_evidence_loader(self, source_key: str, loader: EvidenceLoader) -> None:
        self.evidence_loaders[source_key] = loader

    def get_requirement_loader(self, source_key: str) -> RequirementsLoader:
        try:
            return self.requirement_loaders[source_key]
        except KeyError as exc:
            raise UnsupportedSourceError(f"Unsupported requirements source: {source_key}") from exc

    def get_evidence_loader(self, source_key: str) -> EvidenceLoader:
        try:
            return self.evidence_loaders[source_key]
        except KeyError as exc:
            raise UnsupportedSourceError(f"Unsupported evidence source: {source_key}") from exc

    def ingest_requirements(self, source_key: str, source) -> NormalizedRequirementBatch:
        if self.requirement_adapter is None:
            raise UnsupportedSourceError("No requirements adapter is registered.")
        loader = self.get_requirement_loader(source_key)
        parsed = loader.load(source)
        return self.requirement_adapter.ingest(parsed)

    def ingest_evidence(self, source_key: str, source) -> NormalizedEvidenceBatch:
        if self.evidence_adapter is None:
            raise UnsupportedSourceError("No evidence adapter is registered.")
        loader = self.get_evidence_loader(source_key)
        parsed = loader.load(source)
        return self.evidence_adapter.ingest(parsed)


def build_default_registry() -> IngestionRegistry:
    registry = IngestionRegistry(
        requirement_adapter=DefaultRequirementsNormalizer(),
        evidence_adapter=DefaultEvidenceNormalizer(),
    )
    registry.register_requirement_loader("markdown", MarkdownRequirementsLoader())
    registry.register_requirement_loader("json", JsonRequirementsLoader())
    registry.register_evidence_loader("testar", TestarLoader())
    return registry
