"""Canonical formal semantics attached to authored requirements."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from testar_trace.domain._metadata import freeze_metadata
from testar_trace.domain._validation import (
    require_non_negative_int,
    require_text,
    unique_ids,
)
from testar_trace.domain.provenance import SourceRef

__all__ = [
    "FormalConformancePolicy",
    "FormalElementBinding",
    "FormalRequirementSet",
    "FormalizationStatus",
    "ObservableField",
    "ObservableOperator",
    "ObservablePredicate",
    "ObservableSelector",
    "RequirementObservable",
    "TraceStartMode",
]


class FormalizationStatus(StrEnum):
    """Review status of a formal requirements artifact."""

    DRAFT = "draft"
    APPROVED = "approved"


class TraceStartMode(StrEnum):
    """State-model locations from which a required trace may start."""

    ANY_STATE = "any-state"
    MODEL_INITIAL = "model-initial"


class ObservableOperator(StrEnum):
    """Deterministic comparison applied to an observable field."""

    EQUALS = "equals"
    CONTAINS = "contains"


class ObservableField(StrEnum):
    """Supported transition-context fields for approved observables."""

    TRANSITION_ID = "transition.id"
    ACTION_ID = "action.id"
    ACTION_DESCRIPTION = "action.description"
    ACTION_VALUE = "action.value"
    ACTION_TARGET_WIDGET_ID = "action.target-widget.id"
    ACTION_TARGET_TEXT = "action.target-widget.text"
    ACTION_TARGET_TITLE = "action.target-widget.title"
    ACTION_TARGET_ROLE = "action.target-widget.role"
    ACTION_TARGET_TAG = "action.target-widget.tag"
    ACTION_TARGET_HREF = "action.target-widget.href"
    SOURCE_STATE_ID = "source-state.id"
    SOURCE_STATE_NAME = "source-state.name"
    SOURCE_STATE_TITLE = "source-state.title"
    SOURCE_STATE_URL = "source-state.url"
    TARGET_STATE_ID = "target-state.id"
    TARGET_STATE_NAME = "target-state.name"
    TARGET_STATE_TITLE = "target-state.title"
    TARGET_STATE_URL = "target-state.url"
    SOURCE_WIDGET_TEXT = "source-widget.text"
    SOURCE_WIDGET_TITLE = "source-widget.title"
    SOURCE_WIDGET_ROLE = "source-widget.role"
    SOURCE_WIDGET_TAG = "source-widget.tag"
    SOURCE_WIDGET_HREF = "source-widget.href"
    TARGET_WIDGET_TEXT = "target-widget.text"
    TARGET_WIDGET_TITLE = "target-widget.title"
    TARGET_WIDGET_ROLE = "target-widget.role"
    TARGET_WIDGET_TAG = "target-widget.tag"
    TARGET_WIDGET_HREF = "target-widget.href"


@dataclass(frozen=True, slots=True, kw_only=True)
class ObservablePredicate:
    """One deterministic condition over a transition context."""

    field: ObservableField
    operator: ObservableOperator
    value: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.field, ObservableField):
            raise TypeError("field must be an ObservableField")
        if not isinstance(self.operator, ObservableOperator):
            raise TypeError("operator must be an ObservableOperator")
        require_text(self.value, "value")
        if not isinstance(self.case_sensitive, bool):
            raise TypeError("case_sensitive must be a bool")


@dataclass(frozen=True, slots=True, kw_only=True)
class ObservableSelector:
    """Conjunction of predicates defining one way to observe an event."""

    predicates: tuple[ObservablePredicate, ...]

    def __post_init__(self) -> None:
        if not self.predicates:
            raise ValueError("predicates must not be empty")
        if any(not isinstance(item, ObservablePredicate) for item in self.predicates):
            raise TypeError("predicates must contain ObservablePredicate values")


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementObservable:
    """Approved observable used to label formal requirement events."""

    id: str
    requirement_id: str
    label: str
    selectors: tuple[ObservableSelector, ...]
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.label, "label")
        if not self.selectors:
            raise ValueError("selectors must not be empty")
        if any(not isinstance(item, ObservableSelector) for item in self.selectors):
            raise TypeError("selectors must contain ObservableSelector values")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class FormalElementBinding:
    """Bind one canonical requirement element to one approved observable."""

    id: str
    requirement_element_id: str
    observable_id: str
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_element_id, "requirement_element_id")
        require_text(self.observable_id, "observable_id")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class FormalConformancePolicy:
    """Explicit execution semantics for formal path conformance."""

    start_mode: TraceStartMode = TraceStartMode.ANY_STATE
    allow_intervening_transitions: bool = True
    maximum_intervening_transitions: int = 12

    def __post_init__(self) -> None:
        if not isinstance(self.start_mode, TraceStartMode):
            raise TypeError("start_mode must be a TraceStartMode")
        if not isinstance(self.allow_intervening_transitions, bool):
            raise TypeError("allow_intervening_transitions must be a bool")
        require_non_negative_int(
            self.maximum_intervening_transitions,
            "maximum_intervening_transitions",
        )
        if (
            not self.allow_intervening_transitions
            and self.maximum_intervening_transitions
        ):
            raise ValueError(
                "maximum_intervening_transitions must be zero when intervening "
                "transitions are disabled"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class FormalRequirementSet:
    """Reviewed formal semantics augmenting one canonical requirement set."""

    status: FormalizationStatus
    observables: tuple[RequirementObservable, ...]
    bindings: tuple[FormalElementBinding, ...]
    policy: FormalConformancePolicy = field(default_factory=FormalConformancePolicy)
    schema_version: int = 1
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, FormalizationStatus):
            raise TypeError("status must be a FormalizationStatus")
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if not isinstance(self.policy, FormalConformancePolicy):
            raise TypeError("policy must be a FormalConformancePolicy")
        unique_ids(self.observables, "RequirementObservable")
        unique_ids(self.bindings, "FormalElementBinding")
        bound_element_ids = tuple(
            binding.requirement_element_id for binding in self.bindings
        )
        if len(set(bound_element_ids)) != len(bound_element_ids):
            raise ValueError("each requirement element may have at most one binding")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))
