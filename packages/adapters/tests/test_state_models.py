from pathlib import Path

import pytest

from testar_trace_adapters import SourceArtifact
from testar_trace_adapters.state_models import parse_testar_state_model


def test_parse_testar_state_model_uses_model_qualified_ids() -> None:
    source = SourceArtifact(
        id="login.json",
        name="login.json",
        format="json",
        uri="login.json",
        data={
            "InitialStates": [{"AbstractID": "s1", "InitialPage": "Login"}],
            "ConcreteState": [
                {
                    "AbstractID": "s1",
                    "WebTitle": "Login",
                    "WidgetTree": [
                        {
                            "ConcreteID": "username",
                            "WebTagName": "input",
                            "WebTextContent": "Username",
                            "children": [],
                        }
                    ],
                }
            ],
            "ConcreteAction": [{"AbstractID": "a1", "Desc": "Click login"}],
            "ConcreteTransitions": [{"Source": "s1", "Action": "a1", "Target": "s1"}],
        },
    )

    result = parse_testar_state_model(source)

    assert result.id == "login"
    assert result.initial_state_ids == ("login:state:s1",)
    assert result.states[0].id == "login:state:s1"
    assert result.widgets[0].id == "login:widget:s1:username"
    assert result.actions[0].id == "login:action:a1"
    assert result.transitions[0].source_state_id == "login:state:s1"
    assert result.transitions[0].action_id == "login:action:a1"
    assert result.states[0].source_ref is not None
    assert result.states[0].source_ref.native_id == "s1"


def test_testar_adapter_does_not_copy_large_html_into_metadata() -> None:
    source = SourceArtifact(
        id="model.json",
        name="model.json",
        format="json",
        data={
            "ConcreteState": [
                {
                    "AbstractID": "s1",
                    "WebOuterHTML": "<html>very large</html>",
                    "WidgetTree": [],
                }
            ],
            "ConcreteAction": [],
            "ConcreteTransitions": [],
        },
    )

    result = parse_testar_state_model(source)

    assert "WebOuterHTML" not in result.states[0].metadata


def test_parse_complete_tbuis_model_three() -> None:
    repository = Path(__file__).parents[3]
    path = repository / "benchmarks/tbuis/evidence/uc-04.json"
    source = SourceArtifact(
        id=path.name,
        name=path.name,
        format="json",
        data=path.read_text(encoding="utf-8"),
        uri=str(path),
    )

    result = parse_testar_state_model(source)

    assert len(result.states) == 47
    assert len(result.actions) == 39
    assert len(result.transitions) == 39


def test_invalid_testar_shape_raises() -> None:
    source = SourceArtifact(
        id="invalid.json",
        name="invalid.json",
        format="json",
        data={"ConcreteState": "not-a-list"},
    )

    with pytest.raises(TypeError, match="ConcreteState must be a list"):
        parse_testar_state_model(source)
