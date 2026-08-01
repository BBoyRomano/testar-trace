import pytest
from reqtrace_adapters.evidence.testar import load_testar_state_model_json
from reqtrace_adapters.sources.base import SourceInput


def test_load_testar_state_model_json() -> None:
    source = SourceInput(
        data={
            "InitialPage": "Login",
            "InitialUrl": "https://example.test/login",
            "ConcreteState": [
                {
                    "AbstractID": "s1",
                    "WebTitle": "Login",
                    "WebHref": "https://example.test/login",
                    "WidgetTree": [
                        {
                            "ConcreteID": "username",
                            "WebTagName": "input",
                            "WebTextContent": "Username",
                            "children": [],
                        },
                    ],
                },
            ],
            "ConcreteAction": [
                {
                    "AbstractID": "a1",
                    "Desc": "Click login",
                },
            ],
            "ConcreteTransitions": [
                {
                    "Source": "s1",
                    "Action": "a1",
                    "Target": "s1",
                },
            ],
        },
        name="model.json",
        format="json",
        uri="model.json",
    )

    result = load_testar_state_model_json(source)

    assert result.id == "model"
    assert result.title == "Login"
    assert result.source_ref is not None
    assert len(result.artifacts) == 1
    assert len(result.states) == 1
    assert len(result.elements) == 1
    assert len(result.actions) == 1
    assert len(result.transitions) == 1

    assert result.states[0].id == "s1"
    assert result.elements[0].id == "s1:username"
    assert result.actions[0].id == "a1"
    assert result.transitions[0].from_state_id == "s1"
    assert result.transitions[0].action_id == "a1"
    assert result.transitions[0].to_state_id == "s1"


def test_invalid_testar_state_model_shape_raises() -> None:
    source = SourceInput(
        data={
            "ConcreteState": "not-a-list",
            "ConcreteAction": [],
            "ConcreteTransitions": [],
        },
        name="invalid.json",
        format="json",
        uri="invalid.json",
    )

    with pytest.raises(TypeError, match="ConcreteState must be a list"):
        load_testar_state_model_json(source)
