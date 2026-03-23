from __future__ import annotations

from collections.abc import Callable
from typing import Any

from reqtrace.domain.requirements import RequirementCatalog
from reqtrace.ingest.requirements.canonical_json import (
    load_canonical_json_requirement_catalog,
)


RequirementImporter = Callable[[dict[str, Any]], RequirementCatalog]


def is_canonical_json_requirement_catalog(data: dict[str, Any]) -> bool:
    return "requirements" in data


REQUIREMENT_IMPORTERS: tuple[tuple[Callable[[dict[str, Any]], bool], RequirementImporter], ...] = (
    (is_canonical_json_requirement_catalog,
     load_canonical_json_requirement_catalog),
)


def detect_requirement_importer(data: dict[str, Any]) -> RequirementImporter:
    for can_load, importer in REQUIREMENT_IMPORTERS:
        if can_load(data):
            return importer

    raise ValueError("Unsupported requirements format.")
