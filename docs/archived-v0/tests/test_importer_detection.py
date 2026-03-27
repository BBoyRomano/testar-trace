import json
from pathlib import Path

from reqtrace.ingest.requirements.canonical_json import (
    load_canonical_json_requirement_catalog,
)
from reqtrace.ingest.requirements.common import load_requirement_source
from reqtrace.ingest.requirements.gherkin_feature import (
    load_gherkin_feature_requirement_catalog,
)
from reqtrace.ingest.requirements.registry import detect_requirement_importer
from reqtrace.ingest.requirements.use_cases_json import (
    load_use_cases_json_requirement_catalog,
)
from reqtrace.ingest.requirements.use_cases_markdown import (
    load_use_cases_markdown_requirement_catalog,
)
from reqtrace.ingest.requirements.user_stories_csv import (
    load_user_stories_csv_requirement_catalog,
)
from reqtrace.ingest.state_models.registry import detect_state_model_importer
from reqtrace.ingest.state_models.testar_json_v1 import load_testar_json_v1_state_graph


FIXTURES_DIR = Path("tests/fixtures")


def test_detect_requirement_importer_defaults_to_canonical_json() -> None:
    importer = detect_requirement_importer(
        {
            "requirements": [],
        }
    )

    assert importer is load_canonical_json_requirement_catalog


def test_detect_requirement_importer_for_tbuis_use_cases_json() -> None:
    importer = detect_requirement_importer(
        {
            "format": "tbuis_use_cases_v1",
            "use_cases": [],
        }
    )

    assert importer is load_use_cases_json_requirement_catalog


def test_detect_requirement_importer_for_tbuis_use_cases_markdown() -> None:
    importer = detect_requirement_importer(
        {
            "format": "tbuis_use_cases_markdown_v1",
            "content": "",
        }
    )

    assert importer is load_use_cases_markdown_requirement_catalog


def test_detect_requirement_importer_for_user_stories_csv() -> None:
    importer = detect_requirement_importer(
        {
            "format": "user_stories_csv_v1",
            "content": "",
        }
    )

    assert importer is load_user_stories_csv_requirement_catalog


def test_detect_requirement_importer_for_gherkin_feature() -> None:
    importer = detect_requirement_importer(
        {
            "format": "gherkin_feature_v1",
            "content": "",
        }
    )

    assert importer is load_gherkin_feature_requirement_catalog


def test_load_requirement_source_for_markdown() -> None:
    source = load_requirement_source(
        str(
            FIXTURES_DIR
            / "requirements_sources"
            / "use_cases_markdown"
            / "tbuis_use_cases.md"
        )
    )

    assert source["format"] == "tbuis_use_cases_markdown_v1"
    assert "content" in source


def test_load_requirement_source_for_csv() -> None:
    source = load_requirement_source(
        str(
            FIXTURES_DIR
            / "requirements_sources"
            / "user_stories_csv"
            / "tbuis_user_stories.csv"
        )
    )

    assert source["format"] == "user_stories_csv_v1"
    assert "content" in source


def test_load_requirement_source_for_feature() -> None:
    source = load_requirement_source(
        str(
            FIXTURES_DIR
            / "requirements_sources"
            / "gherkin_feature"
            / "requirements.feature"
        )
    )

    assert source["format"] == "gherkin_feature_v1"
    assert "content" in source


def test_detect_state_model_importer_for_testar_json_v1() -> None:
    data = json.loads(
        (FIXTURES_DIR / "state_models" / "testar_v1_minimal.json").read_text(
            encoding="utf-8"
        )
    )

    importer = detect_state_model_importer(data)

    assert importer is load_testar_json_v1_state_graph
