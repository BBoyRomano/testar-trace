from collections.abc import Mapping
from typing import cast

import pytest

from testar_trace.domain import (
    Action,
    Requirement,
    RequirementElement,
    RequirementSet,
    SourceRef,
    SourceType,
    State,
    StateModel,
    Transition,
    Widget,
)
from testar_trace.domain._metadata import freeze_metadata


def test_metadata_is_recursively_frozen() -> None:
    frozen = freeze_metadata({"nested": {"items": ["one", {"value": 2}]}})

    nested = frozen["nested"]
    assert isinstance(nested, Mapping)
    assert cast("Mapping[str, object]", nested)["items"] == ("one", {"value": 2})


def test_metadata_rejects_non_json_values() -> None:
    with pytest.raises(TypeError, match="JSON-compatible"):
        freeze_metadata({"unsupported": object()})


def test_source_reference_rejects_blank_locator_fields() -> None:
    with pytest.raises(ValueError, match="native_id must not be blank"):
        SourceRef(
            source_type=SourceType.FILE,
            source_name="model.json",
            native_id=" ",
        )


def test_requirement_set_rejects_elements_owned_by_an_unknown_requirement() -> None:
    with pytest.raises(ValueError, match=r"RequirementElement\.requirement_id"):
        RequirementSet(
            requirements=(Requirement(id="req-1", title="Login"),),
            elements=(
                RequirementElement(
                    id="element-1",
                    requirement_id="missing",
                    text="The user logs in",
                ),
            ),
        )


def test_state_model_rejects_widgets_owned_by_an_unknown_state() -> None:
    with pytest.raises(ValueError, match=r"Widget\.state_id"):
        StateModel(
            id="model-1",
            title="Login",
            states=(State(id="state-1", state_model_id="model-1"),),
            widgets=(
                Widget(
                    id="widget-1",
                    state_model_id="model-1",
                    state_id="missing",
                ),
            ),
        )


def test_state_model_rejects_transitions_with_an_unknown_action() -> None:
    with pytest.raises(ValueError, match=r"Transition\.action_id"):
        StateModel(
            id="model-1",
            title="Login",
            states=(State(id="state-1", state_model_id="model-1"),),
            transitions=(
                Transition(
                    id="transition-1",
                    state_model_id="model-1",
                    source_state_id="state-1",
                    action_id="missing",
                ),
            ),
        )


def test_state_model_accepts_consistent_transition_references() -> None:
    model = StateModel(
        id="model-1",
        title="Login",
        states=(State(id="state-1", state_model_id="model-1"),),
        actions=(Action(id="action-1", state_model_id="model-1"),),
        transitions=(
            Transition(
                id="transition-1",
                state_model_id="model-1",
                source_state_id="state-1",
                action_id="action-1",
            ),
        ),
    )

    assert model.transitions[0].action_id == "action-1"
