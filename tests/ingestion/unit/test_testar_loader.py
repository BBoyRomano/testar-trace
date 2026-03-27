import pytest

from reqtrace.ingestion.common.exceptions import SourceValidationError
from reqtrace.ingestion.evidence.testar.loader import TestarLoader
from tests._builders import minimal_testar_model_payload


def _sample_payload() -> dict:
    return {
        "InitialUrl": "https://example.test/",
        "InitialPage": "Example page",
        "ConcreteState": [
            {
                "AbstractID": "state-a",
                "WebTitle": "Home",
                "WebHref": "https://example.test/home",
                "WidgetTree": [
                    {
                        "id": "n1",
                        "AbstractID": "action-open-settings",
                        "ConcreteID": "element-1",
                        "WebTagName": "a",
                        "WebHref": "/settings",
                        "WebTextContent": "Settings",
                        "WebCssSelector": "#settings-link",
                        "children": [],
                    }
                ],
            },
            {
                "AbstractID": "state-b",
                "WebTitle": "Settings",
                "WebHref": "https://example.test/settings",
                "WidgetTree": [],
            },
        ],
        "ConcreteAction": [
            {
                "AbstractID": "action-open-settings",
                "WebHref": "/settings",
                "WebTagName": "a",
                "Desc": "Left Click at 'a_settings'",
                "WebCssSelector": "#settings-link",
            }
        ],
        "ConcreteTransitions": [
            {
                "Source": "state-a",
                "Target": "state-b",
                "Action": "action-open-settings",
            }
        ],
    }


def test_testar_loader_parses_payload() -> None:
    loader = TestarLoader()
    parsed = loader.load_payload(payload=_sample_payload())

    assert parsed.run.tool_name == "TESTAR"
    assert parsed.run.attributes["initial_url"] == "https://example.test/"
    assert len(parsed.states) == 2
    assert len(parsed.elements) == 1
    assert parsed.elements[0].id == "state-a:element-1"
    assert len(parsed.actions) == 1
    assert parsed.actions[0].source_state_id == "state-a"
    assert parsed.actions[0].target_element_id == "state-a:element-1"
    assert parsed.actions[0].kind.value == "navigate"
    assert len(parsed.transitions) == 1
    assert parsed.transitions[0].run_id == parsed.run.id


def test_testar_loader_rejects_missing_states() -> None:
    loader = TestarLoader()
    payload = minimal_testar_model_payload()
    del payload["ConcreteState"]

    with pytest.raises(SourceValidationError, match="ConcreteState"):
        loader.load_payload(payload=payload)


def test_testar_loader_rejects_invalid_widget_tree_container() -> None:
    loader = TestarLoader()
    payload = minimal_testar_model_payload(widget_tree={})

    with pytest.raises(SourceValidationError, match="WidgetTree"):
        loader.load_payload(payload=payload)
