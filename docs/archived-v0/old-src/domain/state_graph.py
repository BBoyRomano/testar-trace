from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class ObservationKind(str, Enum):
    TEXT = "text"
    TITLE = "title"
    URL = "url"
    ACTION_LABEL = "action_label"
    FIELD_LABEL = "field_label"
    STATUS_MESSAGE = "status_message"
    LINK_TEXT = "link_text"
    OTHER = "other"


@dataclass(frozen=True)
class Observation:
    kind: ObservationKind
    value: str
    locator: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class State:
    id: str
    title: str | None = None
    url: str | None = None
    observations: tuple[Observation, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Transition:
    source_id: str
    target_id: str
    action: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class StateGraph:
    states: tuple[State, ...]
    transitions: tuple[Transition, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)
