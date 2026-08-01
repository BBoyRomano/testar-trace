import pytest
from reqtrace_adapters.requirements.gherkin import load_gherkin_feature
from reqtrace_adapters.requirements.use_cases import (
    load_use_case_json,
    load_use_case_markdown,
)
from reqtrace_adapters.requirements.user_stories import load_user_story_json
from reqtrace_adapters.sources.base import SourceInput


def test_load_use_case_markdown() -> None:
    source = SourceInput(
        data=(
            "# Login\n"
            "ID: UC-1\n"
            "Actor: user\n\n"
            "## Preconditions\n"
            "- Login page is open\n\n"
            "## Main flow\n"
            "1. User enters credentials\n"
            "2. System logs in\n\n"
            "## Alternative flow\n"
            "1. User enters invalid credentials\n"
            "2. Postcondition: Error message is shown\n\n"
            "## Postconditions\n"
            "- Dashboard is shown\n"
        ),
        name="login.md",
        format="md",
        uri="login.md",
    )

    result = load_use_case_markdown(source)

    assert result.documents[0].title == "Login"
    assert result.requirements[0].id == "uc-1"
    assert result.requirements[0].title == "Login"
    assert result.requirements[0].actor == "user"
    assert [fragment.kind for fragment in result.fragments] == [
        "precondition",
        "main_step",
        "main_step",
        "alternative_step",
        "alternative_postcondition",
        "postcondition",
    ]
    assert [fragment.text for fragment in result.fragments] == [
        "Login page is open",
        "User enters credentials",
        "System logs in",
        "User enters invalid credentials",
        "Error message is shown",
        "Dashboard is shown",
    ]
    assert result.fragments[3].branch_id == "alt-1"
    assert result.fragments[4].branch_id == "alt-1"
    assert [scenario.kind for scenario in result.scenarios] == [
        "main",
        "alternative",
    ]
    assert result.scenarios[0].fragment_ids == (
        "uc-1:fragment:1",
        "uc-1:fragment:2",
        "uc-1:fragment:3",
        "uc-1:fragment:6",
    )
    assert result.scenarios[1].metadata["branch_id"] == "alt-1"


def test_load_use_case_json_with_multiple_cases() -> None:
    source = SourceInput(
        data={
            "title": "Use cases",
            "use_cases": [
                {
                    "id": "UC-1",
                    "title": "Login",
                    "BasicFlow": ["User enters credentials", "System logs in"],
                },
                {
                    "id": "UC-2",
                    "title": "Logout",
                    "BasicFlow": ["User logs out"],
                },
            ],
        },
        name="use-cases.json",
        format="json",
        uri="use-cases.json",
    )

    result = load_use_case_json(source)

    assert result.documents[0].title == "Use cases"
    assert [requirement.id for requirement in result.requirements] == ["uc-1", "uc-2"]
    assert [requirement.title for requirement in result.requirements] == [
        "Login",
        "Logout",
    ]
    assert len(result.fragments) == 3
    assert len(result.scenarios) == 2


def test_use_case_alternative_scenario_expands_referenced_postconditions() -> None:
    source = SourceInput(
        data={
            "id": "UC-15",
            "title": "Evaluate exam",
            "preconditions": ["Teacher is logged in"],
            "trigger": "Teacher starts evaluation",
            "main_success_scenario": [
                "Teacher selects subject",
                "Teacher selects student",
                "Teacher saves evaluation",
            ],
            "postconditions": [
                "Result is saved",
                "Teacher remains on page",
                "Message appears",
                "Student disappears",
                "Evaluation defaults to A",
            ],
            "alternative_flows": [
                {
                    "id": "UC.15.alt.3a",
                    "title": "3a. Last student on exam date",
                    "postconditions": [
                        "Conditions 1-2 and 4-5 of the main postcondition list "
                        "are now enforced",
                        "No student is registered on this exam date",
                    ],
                }
            ],
        },
        name="use-cases.json",
        format="json",
        uri="use-cases.json",
    )

    result = load_use_case_json(source)

    scenario = result.scenarios[1]
    scenario_fragments = _scenario_fragments(result.fragments, scenario.fragment_ids)
    assert scenario.metadata["branches_from_main_step"] == 3
    assert scenario.metadata["branches_from"] == "uc-15:fragment:5"
    assert scenario.metadata["referenced_postcondition_indices"] == (1, 2, 4, 5)
    assert [fragment.text for fragment in scenario_fragments] == [
        "Teacher is logged in",
        "Teacher starts evaluation",
        "Teacher selects subject",
        "Teacher selects student",
        "Teacher saves evaluation",
        "Last student on exam date",
        "Conditions 1-2 and 4-5 of the main postcondition list are now enforced",
        "No student is registered on this exam date",
        "Result is saved",
        "Teacher remains on page",
        "Student disappears",
        "Evaluation defaults to A",
    ]


def test_use_case_alternative_scenario_can_resume_main_flow() -> None:
    source = SourceInput(
        data={
            "id": "UC-12",
            "title": "Cancel exam date",
            "preconditions": ["Teacher is logged in"],
            "trigger": "Teacher starts cancellation",
            "main_success_scenario": [
                "Teacher selects the exam date",
                "Teacher confirms the cancellation",
                "System cancels the exam date",
            ],
            "postconditions": ["The exam date is cancelled"],
            "alternative_flows": [
                {
                    "id": "UC.12.alt.1d",
                    "title": "1d. Teacher uses search",
                    "steps": ["Teacher filters the list of exam dates"],
                    "postconditions": [
                        "The main success scenario continues from the step 2 onwards",
                    ],
                }
            ],
        },
        name="use-cases.json",
        format="json",
        uri="use-cases.json",
    )

    result = load_use_case_json(source)

    scenario = result.scenarios[1]
    scenario_fragments = _scenario_fragments(result.fragments, scenario.fragment_ids)
    assert scenario.metadata["branches_from_main_step"] == 1
    assert scenario.metadata["branches_from"] == "uc-12:fragment:3"
    assert scenario.metadata["continues_from_main_step"] == 2
    assert [fragment.text for fragment in scenario_fragments] == [
        "Teacher is logged in",
        "Teacher starts cancellation",
        "Teacher selects the exam date",
        "Teacher uses search",
        "Teacher filters the list of exam dates",
        "The main success scenario continues from the step 2 onwards",
        "Teacher confirms the cancellation",
        "System cancels the exam date",
        "The exam date is cancelled",
    ]


def _scenario_fragments(fragments, fragment_ids):
    fragments_by_id = {fragment.id: fragment for fragment in fragments}
    return [fragments_by_id[fragment_id] for fragment_id in fragment_ids]


def test_load_user_story_json() -> None:
    source = SourceInput(
        data={
            "id": "US-1",
            "title": "Login",
            "role": "user",
            "goal": "log in",
            "benefit": "access my account",
            "priority": "high",
        },
        name="story.json",
        format="json",
        uri="story.json",
    )

    result = load_user_story_json(source)

    story = result.requirements[0]
    assert story.id == "us-1"
    assert story.title == "Login"
    assert story.summary == "As a user, I want log in, so that access my account"
    assert story.metadata["priority"] == "high"
    assert [fragment.kind for fragment in result.fragments] == [
        "role",
        "goal",
        "benefit",
    ]
    assert result.scenarios[0].kind == "user-story"


def test_load_gherkin_feature() -> None:
    source = SourceInput(
        data=(
            "Feature: Login\n\n"
            "  Given a user is on the login page\n"
            "  When the user submits valid credentials\n"
            "  Then the user is logged in\n"
        ),
        name="login.feature",
        format="feature",
        uri="login.feature",
    )

    result = load_gherkin_feature(source)

    assert result.documents[0].title == "Login"
    assert result.requirements[0].id == "login"
    assert [fragment.kind for fragment in result.fragments] == [
        "given",
        "when",
        "then",
    ]
    assert result.scenarios[0].kind == "gherkin-scenario"


def test_invalid_markdown_use_case_without_title_raises() -> None:
    source = SourceInput(
        data="## Main flow\n- User logs in\n",
        name="missing-title.md",
        format="md",
        uri="missing-title.md",
    )

    with pytest.raises(ValueError, match="top-level title"):
        load_use_case_markdown(source)


def test_invalid_gherkin_without_feature_header_raises() -> None:
    source = SourceInput(
        data="Given a user is on the login page\n",
        name="missing-feature.feature",
        format="feature",
        uri="missing-feature.feature",
    )

    with pytest.raises(ValueError, match="Feature header"):
        load_gherkin_feature(source)
