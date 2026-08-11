from pathlib import Path

import pytest

from testar_trace.domain.requirement_paths import materialize_requirement_paths
from testar_trace.domain.requirements import (
    RequirementFlowBranchKind,
    RequirementFlowEdgeKind,
)
from testar_trace_adapters import SourceArtifact, load_requirements
from testar_trace_adapters.requirements import (
    parse_gherkin_feature,
    parse_use_case_json,
    parse_use_case_markdown,
    parse_user_stories,
)


def test_use_case_json_maps_alternative_and_rejoin_to_flow_graph() -> None:
    source = SourceArtifact(
        id="cancel.json",
        name="cancel.json",
        format="json",
        data={
            "id": "UC-04",
            "title": "Cancel registration",
            "preconditions": ["Student is logged in"],
            "trigger": "Student starts cancellation",
            "main_success_scenario": [
                "Student chooses a subject",
                "Student confirms cancellation",
                "System removes enrollment",
            ],
            "postconditions": ["Enrollment is removed"],
            "alternative_flows": [
                {
                    "id": "UC.04.alt.1a",
                    "title": "1a. Student filters subjects",
                    "steps": ["Student filters the subject list"],
                    "postconditions": [
                        "The main success scenario continues from the 2nd step onwards"
                    ],
                }
            ],
        },
    )

    result = parse_use_case_json(source)
    flow = result.flows[0]
    paths = materialize_requirement_paths(result)

    assert [branch.kind for branch in flow.branches] == [
        RequirementFlowBranchKind.MAIN,
        RequirementFlowBranchKind.ALTERNATIVE,
    ]
    assert {edge.kind for edge in flow.edges} >= {
        RequirementFlowEdgeKind.BRANCH,
        RequirementFlowEdgeKind.REJOIN,
    }
    assert len(paths.paths) == 2
    assert paths.diagnostics == ()


def test_use_case_markdown_uses_private_source_model_before_mapping() -> None:
    source = SourceArtifact(
        id="login.md",
        name="login.md",
        format="md",
        data=(
            "## UC-01 — Login\n\n"
            "**Primary Actor**\n"
            "User\n\n"
            "**Preconditions**\n"
            "- Login page is open\n\n"
            "**Main Success Scenario**\n"
            "1. User submits credentials\n\n"
            "**Postconditions**\n"
            "- Dashboard appears\n\n"
            "**Technology and Data Variations List**\n"
            "N/A\n"
        ),
    )

    result = parse_use_case_markdown(source)

    assert result.requirements[0].id == "uc-01"
    assert result.requirements[0].actor == "User"
    assert result.requirements[0].metadata["technology_and_data_variations"] == ("N/A",)
    assert result.requirements[0].body is not None
    assert "**Technology and Data Variations List**\nN/A" in result.requirements[0].body
    assert [item.kind for item in result.elements] == [
        "precondition",
        "main_step",
        "postcondition",
    ]
    assert len(materialize_requirement_paths(result).paths) == 1


def test_gherkin_groups_scenarios_but_keeps_each_as_a_complete_flow() -> None:
    source = SourceArtifact(
        id="login.feature",
        name="login.feature",
        format="feature",
        data=(
            "Feature: Login\n"
            "Background:\n"
            "  Given the login page is open\n"
            "@uc-01\n"
            "Scenario: UC.01 Login - main\n"
            "  When valid credentials are submitted\n"
            "  Then the dashboard appears\n"
            "@uc-01 @alternative\n"
            "Scenario: UC.01 Login - alternative invalid password\n"
            "  When an invalid password is submitted\n"
            "  Then an error appears\n"
        ),
    )

    result = parse_gherkin_feature(source)
    paths = materialize_requirement_paths(result)

    assert [item.id for item in result.requirements] == ["uc-01"]
    assert len(result.flows) == 2
    assert [flow.metadata["scenario_kind"] for flow in result.flows] == [
        "main",
        "alternative",
    ]
    assert len(paths.paths) == 2


def test_gherkin_scenario_outline_expands_examples() -> None:
    source = SourceArtifact(
        id="login.feature",
        name="login.feature",
        format="feature",
        data=(
            "Feature: Login\n"
            "@uc-01\n"
            "Scenario Outline: Invalid login\n"
            "  When <password> is submitted\n"
            "  Then an error appears\n"
            "Examples:\n"
            "  | password |\n"
            "  | empty |\n"
            "  | wrong |\n"
        ),
    )

    result = parse_gherkin_feature(source)

    assert len(result.flows) == 2
    assert {element.text for element in result.elements} >= {
        "empty is submitted",
        "wrong is submitted",
    }


def test_user_story_json_maps_acceptance_criteria_to_graph() -> None:
    source = SourceArtifact(
        id="stories.json",
        name="stories.json",
        format="json",
        data={
            "title": "Stories",
            "user_stories": [
                {
                    "id": "US-01",
                    "title": "Login",
                    "as_a": "user",
                    "i_want": "log in",
                    "acceptance_criteria": [
                        {
                            "id": "main",
                            "title": "Main",
                            "type": "main",
                            "statements": ["Submit credentials", "See dashboard"],
                        },
                        {
                            "id": "alternative",
                            "title": "Alternative",
                            "type": "alternative",
                            "statements": [
                                "**1a. Password is invalid**",
                                "An error appears",
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = parse_user_stories(source)

    assert result.requirements[0].summary == "As a user, I want log in"
    assert [branch.kind for branch in result.flows[0].branches] == [
        RequirementFlowBranchKind.MAIN,
        RequirementFlowBranchKind.ALTERNATIVE,
    ]
    assert len(materialize_requirement_paths(result).paths) == 2


def test_tbuis_benchmarks_load_into_revamped_core_models() -> None:
    repository = Path(__file__).parents[3]
    use_cases = load_requirements(
        repository / "benchmarks/tbuis/requirements/use-cases.json",
        adapter="use-case",
    )
    gherkin = load_requirements(
        repository / "benchmarks/tbuis/requirements/gherkin.feature",
        adapter="gherkin",
    )

    assert len(use_cases.requirements) == 22
    assert len(gherkin.requirements) == 22
    assert len(gherkin.flows) == 71
    assert materialize_requirement_paths(use_cases).diagnostics == ()


def test_unsupported_gherkin_rule_is_rejected_explicitly() -> None:
    source = SourceArtifact(
        id="rule.feature",
        name="rule.feature",
        format="feature",
        data="Feature: Login\nRule: Authentication\nScenario: Login\nGiven a user\n",
    )

    with pytest.raises(ValueError, match="Rule blocks are not supported"):
        parse_gherkin_feature(source)
