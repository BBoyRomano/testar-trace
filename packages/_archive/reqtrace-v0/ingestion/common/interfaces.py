from __future__ import annotations

from pathlib import Path
from typing import Protocol

from reqtrace.ingestion.common.models import NormalizedEvidenceBatch, NormalizedRequirementBatch
from reqtrace.ingestion.evidence.models import ParsedEvidenceSource
from reqtrace.ingestion.requirements.models import ParsedRequirementsSource


class RequirementsLoader(Protocol):
    def load(self, source: str | Path) -> ParsedRequirementsSource: ...


class EvidenceLoader(Protocol):
    def load(self, source: str | Path) -> ParsedEvidenceSource: ...


class RequirementsAdapter(Protocol):
    def ingest(self, parsed_source: ParsedRequirementsSource) -> NormalizedRequirementBatch: ...


class EvidenceAdapter(Protocol):
    def ingest(self, parsed_source: ParsedEvidenceSource) -> NormalizedEvidenceBatch: ...
