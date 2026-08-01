"""Canonical evidence models."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from reqtrace.models.common import SourceRef, freeze_metadata

__all__ = [
    "EvidenceArtifact",
    "EvidenceSet",
    "ExecutionAction",
    "ExecutionElement",
    "ExecutionState",
    "ExecutionTransition",
]


@dataclass(slots=True, frozen=True)
class EvidenceArtifact:
    """A top-level evidence artifact, such as a scenario or imported item."""

    id: str
    title: str
    text: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("EvidenceArtifact.id must not be blank.")
        if not self.title.strip():
            raise ValueError("EvidenceArtifact.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class ExecutionState:
    """One observed application state."""

    id: str
    name: str | None = None
    title: str | None = None
    url: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("ExecutionState.id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class ExecutionElement:
    """One observed UI element inside an application state."""

    id: str
    state_id: str
    tag_name: str | None = None
    role: str | None = None
    text: str | None = None
    title: str | None = None
    href: str | None = None
    css_selector: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("ExecutionElement.id must not be blank.")
        if not self.state_id.strip():
            raise ValueError("ExecutionElement.state_id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class ExecutionAction:
    """One observed user or system action."""

    id: str
    description: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("ExecutionAction.id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class ExecutionTransition:
    """One observed transition between two states."""

    id: str
    from_state_id: str
    action_id: str
    to_state_id: str | None = None
    order_index: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("ExecutionTransition.id must not be blank.")
        if not self.from_state_id.strip():
            raise ValueError("ExecutionTransition.from_state_id must not be blank.")
        if not self.action_id.strip():
            raise ValueError("ExecutionTransition.action_id must not be blank.")
        if self.order_index is not None and self.order_index < 0:
            raise ValueError("ExecutionTransition.order_index must be non-negative.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class EvidenceSet:
    """A normalized collection of execution evidence."""

    id: str
    title: str
    artifacts: tuple[EvidenceArtifact, ...] = ()
    states: tuple[ExecutionState, ...] = ()
    elements: tuple[ExecutionElement, ...] = ()
    actions: tuple[ExecutionAction, ...] = ()
    transitions: tuple[ExecutionTransition, ...] = ()
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("EvidenceSet.id must not be blank.")
        if not self.title.strip():
            raise ValueError("EvidenceSet.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))
        self._validate_references()

    def _validate_references(self) -> None:
        state_ids = {state.id for state in self.states}
        action_ids = {action.id for action in self.actions}

        for element in self.elements:
            if element.state_id not in state_ids:
                raise ValueError(
                    "ExecutionElement.state_id must reference a known state: "
                    f"{element.state_id}",
                )

        for transition in self.transitions:
            if transition.from_state_id not in state_ids:
                raise ValueError(
                    "ExecutionTransition.from_state_id must reference a known state: "
                    f"{transition.from_state_id}",
                )
            if (
                transition.to_state_id is not None
                and transition.to_state_id not in state_ids
            ):
                raise ValueError(
                    "ExecutionTransition.to_state_id must reference a known state: "
                    f"{transition.to_state_id}",
                )
            if transition.action_id not in action_ids:
                raise ValueError(
                    "ExecutionTransition.action_id must reference a known action: "
                    f"{transition.action_id}",
                )
