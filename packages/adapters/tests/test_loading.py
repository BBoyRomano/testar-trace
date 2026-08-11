import json
from pathlib import Path

import pytest

from testar_trace.domain.requirements import Requirement, RequirementSet
from testar_trace_adapters import (
    Adapter,
    AdapterRegistry,
    SourceArtifact,
    load_requirements,
    load_state_models,
)


def test_one_file_can_contain_multiple_requirements(tmp_path: Path) -> None:
    path = tmp_path / "requirements.json"
    path.write_text(
        json.dumps(
            {
                "title": "Requirements",
                "use_cases": [
                    {"id": "UC-01", "title": "Login", "main_flow": ["Log in"]},
                    {"id": "UC-02", "title": "Logout", "main_flow": ["Log out"]},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = load_requirements(path)

    assert [item.id for item in result.requirements] == ["uc-01", "uc-02"]
    assert len(result.documents) == 1


def test_multiple_files_combine_into_one_requirement_set(tmp_path: Path) -> None:
    for requirement_id, action in (("UC-01", "Log in"), ("UC-02", "Log out")):
        (tmp_path / f"{requirement_id}.json").write_text(
            json.dumps(
                {
                    "id": requirement_id,
                    "title": action,
                    "main_flow": [action],
                }
            ),
            encoding="utf-8",
        )

    result = load_requirements(tmp_path, pattern="*.json")

    assert [item.id for item in result.requirements] == ["uc-01", "uc-02"]
    assert len(result.documents) == 2


def test_mixed_requirement_formats_are_detected_per_artifact() -> None:
    sources = (
        _use_case_artifact("login.json", "UC-01"),
        SourceArtifact(
            id="logout.feature",
            name="logout.feature",
            format="feature",
            data=(
                "Feature: Logout\n"
                "@uc-02\n"
                "Scenario: UC.02 Logout - main\n"
                "  When the user signs out\n"
                "  Then the session ends\n"
            ),
        ),
    )

    result = load_requirements(sources)

    assert [item.id for item in result.requirements] == ["uc-01", "uc-02"]
    assert len(result.documents) == 2


def test_duplicate_requirement_ids_are_not_silently_renamed() -> None:
    sources = (
        _use_case_artifact("one.json", "UC-01"),
        _use_case_artifact("two.json", "UC-01"),
    )

    with pytest.raises(ValueError, match=r"duplicate Requirement\.id"):
        load_requirements(sources)


def test_multiple_state_model_files_form_one_collection() -> None:
    sources = (
        _state_model_artifact("first.json"),
        _state_model_artifact("second.json"),
    )

    result = load_state_models(sources)

    assert [model.id for model in result.models] == ["first", "second"]
    assert [state.id for state in result.states] == [
        "first:state:s1",
        "second:state:s1",
    ]


def test_custom_requirement_adapter_can_be_selected_explicitly() -> None:
    def adapt(source: SourceArtifact) -> RequirementSet:
        return RequirementSet(
            requirements=(Requirement(id="custom", title=str(source.data)),),
        )

    registry = AdapterRegistry()
    registry.register_requirement(
        Adapter[RequirementSet](
            id="custom",
            name="Custom",
            formats=("txt",),
            adapt=adapt,
        )
    )
    source = SourceArtifact(
        id="custom.txt",
        name="custom.txt",
        data="Custom requirement",
        format="txt",
    )

    result = load_requirements(source, adapter="custom", registry=registry)

    assert result.requirements[0].title == "Custom requirement"


def _use_case_artifact(name: str, requirement_id: str) -> SourceArtifact:
    return SourceArtifact(
        id=name,
        name=name,
        format="json",
        data={
            "id": requirement_id,
            "title": "Login",
            "main_flow": ["Log in"],
        },
    )


def _state_model_artifact(name: str) -> SourceArtifact:
    return SourceArtifact(
        id=name,
        name=name,
        format="json",
        data={
            "ConcreteState": [{"AbstractID": "s1", "WidgetTree": []}],
            "ConcreteAction": [],
            "ConcreteTransitions": [],
        },
    )
