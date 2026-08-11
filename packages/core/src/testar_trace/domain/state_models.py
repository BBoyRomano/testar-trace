"""Canonical TESTAR state models and recorded executions."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from testar_trace.domain._metadata import freeze_metadata
from testar_trace.domain._validation import (
    require_ids,
    require_known,
    require_non_negative_int,
    require_optional_text,
    require_text,
    unique_ids,
)
from testar_trace.domain.provenance import SourceRef

__all__ = [
    "Action",
    "ExecutionSequence",
    "ExecutionStep",
    "State",
    "StateModel",
    "StateModelCollection",
    "StateModelLayer",
    "Transition",
    "Widget",
]


class StateModelLayer(StrEnum):
    """Level of TESTAR information represented by a state model."""

    ABSTRACT = "abstract"
    CONCRETE = "concrete"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True, kw_only=True)
class State:
    """State in a canonical state model."""

    id: str
    state_model_id: str
    name: str | None = None
    title: str | None = None
    url: str | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.state_model_id, "state_model_id")
        require_optional_text(self.name, "name")
        require_optional_text(self.title, "title")
        require_optional_text(self.url, "url")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Widget:
    """Observable user-interface widget belonging to a state."""

    id: str
    state_model_id: str
    state_id: str
    tag_name: str | None = None
    role: str | None = None
    text: str | None = None
    title: str | None = None
    href: str | None = None
    css_selector: str | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.state_model_id, "state_model_id")
        require_text(self.state_id, "state_id")
        require_optional_text(self.tag_name, "tag_name")
        require_optional_text(self.role, "role")
        require_optional_text(self.text, "text")
        require_optional_text(self.title, "title")
        require_optional_text(self.href, "href")
        require_optional_text(self.css_selector, "css_selector")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Action:
    """Action available in or observed for a state model."""

    id: str
    state_model_id: str
    description: str | None = None
    target_widget_id: str | None = None
    value: str | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.state_model_id, "state_model_id")
        require_optional_text(self.description, "description")
        require_optional_text(
            self.target_widget_id,
            "target_widget_id",
        )
        require_optional_text(self.value, "value")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Transition:
    """Directed transition between states."""

    id: str
    state_model_id: str
    source_state_id: str
    action_id: str
    target_state_id: str | None = None
    order_index: int | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.state_model_id, "state_model_id")
        require_text(self.source_state_id, "source_state_id")
        require_text(self.action_id, "action_id")
        require_optional_text(
            self.target_state_id,
            "target_state_id",
        )
        require_non_negative_int(
            self.order_index,
            "order_index",
        )

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionStep:
    """Ordered step in a recorded TESTAR execution sequence."""

    id: str
    state_model_id: str
    sequence_id: str
    order_index: int
    state_id: str | None = None
    action_id: str | None = None
    transition_id: str | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.state_model_id, "state_model_id")
        require_text(self.sequence_id, "sequence_id")
        require_non_negative_int(
            self.order_index,
            "order_index",
        )
        require_optional_text(self.state_id, "state_id")
        require_optional_text(self.action_id, "action_id")
        require_optional_text(
            self.transition_id,
            "transition_id",
        )

        if not any(
            (
                self.state_id,
                self.action_id,
                self.transition_id,
            )
        ):
            raise ValueError(
                "an execution step must reference a state, action, or transition"
            )

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionSequence:
    """Chronological route recorded during a TESTAR execution."""

    id: str
    state_model_id: str
    title: str
    steps: tuple[ExecutionStep, ...]
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.state_model_id, "state_model_id")
        require_text(self.title, "title")

        if not self.steps:
            raise ValueError("steps must not be empty")

        unique_ids(self.steps, "ExecutionStep")

        expected_indexes = tuple(range(len(self.steps)))
        actual_indexes = tuple(step.order_index for step in self.steps)

        if actual_indexes != expected_indexes:
            raise ValueError(
                "steps must use consecutive order indexes starting at zero"
            )

        for step in self.steps:
            if step.state_model_id != self.state_model_id:
                raise ValueError("every step must belong to the sequence's state model")

            if step.sequence_id != self.id:
                raise ValueError("every step must reference its containing sequence")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateModel:
    """Canonical TESTAR state model and its recorded executions."""

    id: str
    title: str
    layer: StateModelLayer = StateModelLayer.MIXED
    initial_state_ids: tuple[str, ...] = ()
    states: tuple[State, ...] = ()
    widgets: tuple[Widget, ...] = ()
    actions: tuple[Action, ...] = ()
    transitions: tuple[Transition, ...] = ()
    sequences: tuple[ExecutionSequence, ...] = ()
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.title, "title")

        if not self.states:
            raise ValueError("states must not be empty")

        state_ids = unique_ids(self.states, "State")
        widget_ids = unique_ids(self.widgets, "Widget")
        action_ids = unique_ids(self.actions, "Action")
        unique_ids(
            self.transitions,
            "Transition",
        )
        unique_ids(self.sequences, "ExecutionSequence")

        require_ids(
            self.initial_state_ids,
            "initial_state_ids",
            allow_empty=True,
            unique=True,
        )
        require_known(
            self.initial_state_ids,
            state_ids,
            "initial_state_ids",
        )

        for item in (
            *self.states,
            *self.widgets,
            *self.actions,
            *self.transitions,
        ):
            if item.state_model_id != self.id:
                raise ValueError(
                    f"{type(item).__name__}.state_model_id "
                    "must match the containing model"
                )

        for widget in self.widgets:
            require_known(
                (widget.state_id,),
                state_ids,
                "Widget.state_id",
            )

        for action in self.actions:
            if action.target_widget_id is not None:
                require_known(
                    (action.target_widget_id,),
                    widget_ids,
                    "Action.target_widget_id",
                )

        transitions_by_id = {
            transition.id: transition for transition in self.transitions
        }

        for transition in self.transitions:
            require_known(
                (transition.source_state_id,),
                state_ids,
                "Transition.source_state_id",
            )
            require_known(
                (transition.action_id,),
                action_ids,
                "Transition.action_id",
            )

            if transition.target_state_id is not None:
                require_known(
                    (transition.target_state_id,),
                    state_ids,
                    "Transition.target_state_id",
                )

        all_steps = tuple(
            step for sequence in self.sequences for step in sequence.steps
        )
        unique_ids(all_steps, "ExecutionStep")

        for sequence in self.sequences:
            if sequence.state_model_id != self.id:
                raise ValueError(
                    "every execution sequence must belong to the containing model"
                )

            for step in sequence.steps:
                _validate_step_references(
                    step,
                    state_ids=state_ids,
                    action_ids=action_ids,
                    transitions_by_id=transitions_by_id,
                )

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateModelCollection:
    """Canonical input containing one or more state models."""

    id: str
    title: str
    models: tuple[StateModel, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.title, "title")

        if not self.models:
            raise ValueError("models must not be empty")

        unique_ids(self.models, "StateModel")

        for type_name, items in (
            ("State", self.states),
            ("Widget", self.widgets),
            ("Action", self.actions),
            ("Transition", self.transitions),
            ("ExecutionSequence", self.sequences),
            ("ExecutionStep", self.steps),
        ):
            unique_ids(items, type_name)

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )

    @property
    def states(self) -> tuple[State, ...]:
        """Return states from every model in collection order."""
        return tuple(item for model in self.models for item in model.states)

    @property
    def widgets(self) -> tuple[Widget, ...]:
        """Return widgets from every model in collection order."""
        return tuple(item for model in self.models for item in model.widgets)

    @property
    def actions(self) -> tuple[Action, ...]:
        """Return actions from every model in collection order."""
        return tuple(item for model in self.models for item in model.actions)

    @property
    def transitions(self) -> tuple[Transition, ...]:
        """Return transitions from every model in collection order."""
        return tuple(item for model in self.models for item in model.transitions)

    @property
    def sequences(self) -> tuple[ExecutionSequence, ...]:
        """Return execution sequences from every model."""
        return tuple(item for model in self.models for item in model.sequences)

    @property
    def steps(self) -> tuple[ExecutionStep, ...]:
        """Return execution steps from every model."""
        return tuple(step for sequence in self.sequences for step in sequence.steps)

    @property
    def source_refs(self) -> tuple[SourceRef, ...]:
        """Return source references from every sourced model."""
        return tuple(
            model.source_ref for model in self.models if model.source_ref is not None
        )

    @property
    def source_ref(self) -> SourceRef | None:
        """Return a source shared by every sourced model."""
        refs = self.source_refs

        if not refs:
            return None

        first = refs[0]
        return first if all(ref == first for ref in refs[1:]) else None


def _validate_step_references(
    step: ExecutionStep,
    *,
    state_ids: set[str],
    action_ids: set[str],
    transitions_by_id: Mapping[str, Transition],
) -> None:
    if step.state_id is not None:
        require_known(
            (step.state_id,),
            state_ids,
            "ExecutionStep.state_id",
        )

    if step.action_id is not None:
        require_known(
            (step.action_id,),
            action_ids,
            "ExecutionStep.action_id",
        )

    if step.transition_id is None:
        return

    require_known(
        (step.transition_id,),
        transitions_by_id,
        "ExecutionStep.transition_id",
    )

    transition = transitions_by_id[step.transition_id]

    if step.action_id is not None and step.action_id != transition.action_id:
        raise ValueError("ExecutionStep.action_id must match the referenced transition")
