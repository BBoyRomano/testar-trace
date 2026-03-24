from __future__ import annotations

from collections.abc import Callable

from reqtrace.domain.requirements import RequirementCatalog
from reqtrace.ingest.requirements.canonical_json import (
    load_canonical_json_requirement_catalog,
)
from reqtrace.ingest.requirements.gherkin_feature import (
    load_gherkin_feature_requirement_catalog,
)
from reqtrace.ingest.requirements.use_cases_json import (
    load_use_cases_json_requirement_catalog,
)
from reqtrace.ingest.requirements.use_cases_markdown import (
    load_use_cases_markdown_requirement_catalog,
)
from reqtrace.ingest.requirements.user_stories_csv import (
    load_user_stories_csv_requirement_catalog,
)

RequirementImporter = Callable[[dict], RequirementCatalog]


def detect_requirement_importer(data: dict) -> RequirementImporter:
    format_name = data.get("format")

    if format_name == "tbuis_use_cases_v1":
        return load_use_cases_json_requirement_catalog

    if format_name == "tbuis_use_cases_markdown_v1":
        return load_use_cases_markdown_requirement_catalog

    if format_name == "user_stories_csv_v1":
        return load_user_stories_csv_requirement_catalog

    if format_name == "gherkin_feature_v1":
        return load_gherkin_feature_requirement_catalog

    return load_canonical_json_requirement_catalog
