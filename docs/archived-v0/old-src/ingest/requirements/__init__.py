from __future__ import annotations

from reqtrace.domain.requirements import RequirementCatalog
from reqtrace.ingest.requirements.common import load_requirement_source
from reqtrace.ingest.requirements.registry import detect_requirement_importer


def load_requirement_catalog(path: str) -> RequirementCatalog:
    source = load_requirement_source(path)
    importer = detect_requirement_importer(source)
    return importer(source)
