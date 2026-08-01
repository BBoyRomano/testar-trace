import json

import pytest

from reqtrace_api.server import _parse_evidence, _parse_requirements


def test_parse_requirements_uses_canonical_adapter() -> None:
    requirements = _parse_requirements(
        {
            "name": "requirements.md",
            "kind": "use-case",
            "format": "md",
            "text": (
                "## UC.1 - Login\n\n"
                "**Preconditions**\n"
                "1. Login page is open\n\n"
                "**Main Success Scenario**\n"
                "1. User submits login form\n\n"
                "**Postconditions**\n"
                "1. Dashboard is shown\n"
            ),
        },
    )

    assert requirements.requirements[0].id == "uc-1"
    assert requirements.scenarios[0].fragment_ids == (
        "uc-1:fragment:1",
        "uc-1:fragment:2",
        "uc-1:fragment:3",
    )


def test_parse_requirements_accepts_json_text() -> None:
    requirements = _parse_requirements(
        {
            "name": "requirements.json",
            "kind": "use-case",
            "format": "json",
            "text": json.dumps(
                {
                    "id": "UC-1",
                    "title": "Login",
                    "main_success_scenario": ["User submits login form"],
                },
            ),
        },
    )

    assert requirements.requirements[0].title == "Login"


def test_parse_requirements_can_select_parser_automatically() -> None:
    requirements = _parse_requirements(
        {
            "name": "requirements.md",
            "format": "md",
            "text": (
                "## UC.1 - Login\n\n"
                "**Main Success Scenario**\n"
                "1. User submits login form\n"
            ),
        },
    )

    assert requirements.requirements[0].id == "uc-1"


def test_parse_requirements_accepts_multiple_sources() -> None:
    requirements = _parse_requirements(
        {
            "kind": "use-case",
            "sources": [
                {
                    "name": "login.md",
                    "format": "md",
                    "text": (
                        "## UC.1 - Login\n\n"
                        "**Main Success Scenario**\n"
                        "1. User submits login form\n"
                    ),
                },
                {
                    "name": "logout.md",
                    "format": "md",
                    "text": (
                        "## UC.2 - Logout\n\n"
                        "**Main Success Scenario**\n"
                        "1. User signs out\n"
                    ),
                },
            ],
        },
    )

    assert [requirement.id for requirement in requirements.requirements] == [
        "uc-1",
        "uc-2",
    ]


def test_parse_evidence_uses_canonical_testar_adapter() -> None:
    evidence = _parse_evidence(
        {
            "name": "model.json",
            "kind": "testar-state-model",
            "format": "json",
            "text": json.dumps(
                {
                    "InitialPage": "App",
                    "ConcreteState": [
                        {
                            "AbstractID": "state-1",
                            "WidgetTree": [{"ConcreteID": "widget-1"}],
                        },
                        {"AbstractID": "state-2"},
                    ],
                    "ConcreteAction": [{"AbstractID": "action-1", "Desc": "Click"}],
                    "ConcreteTransitions": [
                        {
                            "Source": "state-1",
                            "Target": "state-2",
                            "Action": "action-1",
                        },
                    ],
                },
            ),
        },
    )

    assert len(evidence.states) == 2
    assert len(evidence.actions) == 1
    assert len(evidence.transitions) == 1
    assert len(evidence.elements) == 1


def test_parse_evidence_rejects_empty_state_model() -> None:
    with pytest.raises(ValueError, match="No evidence items found"):
        _parse_evidence(
            {
                "name": "model.json",
                "format": "json",
                "text": "{}",
            },
        )
