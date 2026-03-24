from pathlib import Path

from reqtrace.domain.requirements import RequirementKind, RequirementUnitKind
from reqtrace.ingest.requirements import load_requirement_catalog
from reqtrace.ingest.state_models import load_state_graph


FIXTURES_DIR = Path("tests/fixtures")


def test_load_state_graph() -> None:
    state_graph = load_state_graph(
        str(FIXTURES_DIR / "state_models" / "testar_v1_minimal.json")
    )

    assert len(state_graph.states) == 2
    assert len(state_graph.transitions) == 1


def test_load_requirement_catalog() -> None:
    requirement_catalog = load_requirement_catalog(
        str(FIXTURES_DIR / "canonical" / "case_001_found" / "requirements.json")
    )

    assert len(requirement_catalog.requirements) == 1

    requirement = requirement_catalog.requirements[0]
    assert requirement.id == "UC.01"
    assert requirement.kind == RequirementKind.USE_CASE
    assert requirement.title == "Application login"
    assert requirement.actor == "Unlogged user"

    unit_kinds = [unit.kind for unit in requirement.units]
    assert unit_kinds == [RequirementUnitKind.STEP]


def test_load_requirement_catalog_from_markdown() -> None:
    requirement_catalog = load_requirement_catalog(
        str(
            FIXTURES_DIR
            / "requirements_sources"
            / "use_cases_markdown"
            / "tbuis_use_cases.md"
        )
    )

    assert len(requirement_catalog.requirements) == 1
    assert requirement_catalog.requirements[0].id == "UC.01"


def test_load_requirement_catalog_from_csv() -> None:
    requirement_catalog = load_requirement_catalog(
        str(
            FIXTURES_DIR
            / "requirements_sources"
            / "user_stories_csv"
            / "tbuis_user_stories.csv"
        )
    )

    assert len(requirement_catalog.requirements) == 2
    assert requirement_catalog.requirements[0].kind == RequirementKind.USER_STORY


def test_load_requirement_catalog_from_feature() -> None:
    requirement_catalog = load_requirement_catalog(
        str(
            FIXTURES_DIR
            / "requirements_sources"
            / "gherkin_feature"
            / "requirements.feature"
        )
    )

    assert len(requirement_catalog.requirements) == 2
    assert requirement_catalog.requirements[0].kind == RequirementKind.FEATURE
