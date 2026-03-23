from pathlib import Path

from reqtrace.ingest.common import load_json_file
from reqtrace.ingest.requirements import load_requirement_catalog
from reqtrace.ingest.requirements.canonical_json import (
    load_canonical_json_requirement_catalog,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "canonical"


def test_load_canonical_json_requirement_catalog_directly() -> None:
    data = load_json_file(
        FIXTURES_DIR / "case_001_found" / "requirements.json")
    catalog = load_canonical_json_requirement_catalog(data)

    assert len(catalog.requirements) == 1
    assert catalog.requirements[0].id == "UC.01"
    assert catalog.requirements[0].title == "Application login"


def test_load_requirement_catalog_via_selector() -> None:
    catalog = load_requirement_catalog(
        str(FIXTURES_DIR / "case_001_found" / "requirements.json"))

    assert len(catalog.requirements) == 1
    assert len(catalog.requirements[0].units) == 2
