from __future__ import annotations

from reqtrace.domain.requirements import RequirementCatalog
from reqtrace.ingest.common import load_json_file
from reqtrace.ingest.requirements.registry import detect_requirement_importer

__all__ = ["load_requirement_catalog"]


def load_requirement_catalog(path: str) -> RequirementCatalog:
    data = load_json_file(path)
    importer = detect_requirement_importer(data)
    return importer(data)
