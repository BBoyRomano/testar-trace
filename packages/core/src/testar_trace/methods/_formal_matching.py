"""Deterministic evaluation of approved observables over state-model transitions."""

from dataclasses import dataclass

from testar_trace.domain.formal_requirements import (
    ObservableField,
    ObservableOperator,
    ObservablePredicate,
    ObservableSelector,
    RequirementObservable,
)
from testar_trace.domain.state_models import (
    Action,
    State,
    StateModel,
    Transition,
    Widget,
)


@dataclass(frozen=True, slots=True)
class FormalModelIndex:
    """Indexed state-model entities used by observable evaluation."""

    states: dict[str, State]
    actions: dict[str, Action]
    widgets: dict[str, Widget]
    widgets_by_state: dict[str, tuple[Widget, ...]]


def index_formal_model(model: StateModel) -> FormalModelIndex:
    """Build one immutable-by-convention lookup index for a state model."""
    widgets_by_state: dict[str, list[Widget]] = {}
    for widget in model.widgets:
        widgets_by_state.setdefault(widget.state_id, []).append(widget)
    return FormalModelIndex(
        states={state.id: state for state in model.states},
        actions={action.id: action for action in model.actions},
        widgets={widget.id: widget for widget in model.widgets},
        widgets_by_state={
            state_id: tuple(sorted(values, key=lambda item: item.id))
            for state_id, values in widgets_by_state.items()
        },
    )


def transition_matches_observable(
    transition: Transition,
    observable: RequirementObservable,
    index: FormalModelIndex,
) -> bool:
    """Return whether one transition satisfies any approved selector."""
    return any(
        _selector_matches(transition, selector, index)
        for selector in observable.selectors
    )


def _selector_matches(
    transition: Transition,
    selector: ObservableSelector,
    index: FormalModelIndex,
) -> bool:
    return all(
        _predicate_matches(transition, predicate, index)
        for predicate in selector.predicates
    )


def _predicate_matches(
    transition: Transition,
    predicate: ObservablePredicate,
    index: FormalModelIndex,
) -> bool:
    expected = _normalize(predicate.value, predicate.case_sensitive)
    return any(
        _compare(
            _normalize(value, predicate.case_sensitive),
            expected,
            predicate.operator,
        )
        for value in _field_values(transition, predicate.field, index)
    )


def _compare(actual: str, expected: str, operator: ObservableOperator) -> bool:
    if operator is ObservableOperator.EQUALS:
        return actual == expected
    return expected in actual


def _normalize(value: str, case_sensitive: bool) -> str:
    normalized = " ".join(value.split())
    return normalized if case_sensitive else normalized.casefold()


def _field_values(
    transition: Transition,
    field: ObservableField,
    index: FormalModelIndex,
) -> tuple[str, ...]:
    action = index.actions[transition.action_id]
    source = index.states[transition.source_state_id]
    target = (
        index.states.get(transition.target_state_id)
        if transition.target_state_id is not None
        else None
    )
    action_widget = (
        index.widgets.get(action.target_widget_id)
        if action.target_widget_id is not None
        else None
    )
    direct = {
        ObservableField.TRANSITION_ID: transition.id,
        ObservableField.ACTION_ID: action.id,
        ObservableField.ACTION_DESCRIPTION: action.description,
        ObservableField.ACTION_VALUE: action.value,
        ObservableField.ACTION_TARGET_WIDGET_ID: (
            action_widget.id if action_widget is not None else None
        ),
        ObservableField.ACTION_TARGET_TEXT: (
            action_widget.text if action_widget is not None else None
        ),
        ObservableField.ACTION_TARGET_TITLE: (
            action_widget.title if action_widget is not None else None
        ),
        ObservableField.ACTION_TARGET_ROLE: (
            action_widget.role if action_widget is not None else None
        ),
        ObservableField.ACTION_TARGET_TAG: (
            action_widget.tag_name if action_widget is not None else None
        ),
        ObservableField.ACTION_TARGET_HREF: (
            action_widget.href if action_widget is not None else None
        ),
        ObservableField.SOURCE_STATE_ID: source.id,
        ObservableField.SOURCE_STATE_NAME: source.name,
        ObservableField.SOURCE_STATE_TITLE: source.title,
        ObservableField.SOURCE_STATE_URL: source.url,
        ObservableField.TARGET_STATE_ID: target.id if target is not None else None,
        ObservableField.TARGET_STATE_NAME: target.name if target is not None else None,
        ObservableField.TARGET_STATE_TITLE: (
            target.title if target is not None else None
        ),
        ObservableField.TARGET_STATE_URL: target.url if target is not None else None,
    }
    if field in direct:
        value = direct[field]
        return (value,) if value is not None else ()

    source_widgets = index.widgets_by_state.get(source.id, ())
    target_widgets = index.widgets_by_state.get(target.id, ()) if target else ()
    collection, attribute = {
        ObservableField.SOURCE_WIDGET_TEXT: (source_widgets, "text"),
        ObservableField.SOURCE_WIDGET_TITLE: (source_widgets, "title"),
        ObservableField.SOURCE_WIDGET_ROLE: (source_widgets, "role"),
        ObservableField.SOURCE_WIDGET_TAG: (source_widgets, "tag_name"),
        ObservableField.SOURCE_WIDGET_HREF: (source_widgets, "href"),
        ObservableField.TARGET_WIDGET_TEXT: (target_widgets, "text"),
        ObservableField.TARGET_WIDGET_TITLE: (target_widgets, "title"),
        ObservableField.TARGET_WIDGET_ROLE: (target_widgets, "role"),
        ObservableField.TARGET_WIDGET_TAG: (target_widgets, "tag_name"),
        ObservableField.TARGET_WIDGET_HREF: (target_widgets, "href"),
    }[field]
    return tuple(
        value
        for widget in collection
        if (value := getattr(widget, attribute)) is not None
    )
