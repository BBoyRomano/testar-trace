"""Typed adapter definitions and explicit registration."""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from testar_trace.domain.requirements import RequirementSet
from testar_trace.domain.state_models import StateModel
from testar_trace_adapters.source import SourceArtifact

__all__ = ["Adapter", "AdapterRegistry"]

_ADAPTER_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True, kw_only=True)
class Adapter[T]:
    """Named conversion from one source artifact to a canonical core value."""

    id: str
    name: str
    formats: tuple[str, ...]
    adapt: Callable[[SourceArtifact], T] = field(repr=False)
    detect: Callable[[SourceArtifact], bool] | None = field(
        default=None,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("id must be a string")
        if _ADAPTER_ID_PATTERN.fullmatch(self.id) is None:
            raise ValueError(
                "adapter id must contain lowercase letters or digits "
                "separated by single hyphens"
            )
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not self.name or self.name != self.name.strip():
            raise ValueError("name must be non-empty without surrounding whitespace")
        if not self.formats:
            raise ValueError("formats must not be empty")

        formats = tuple(_normalize_format(value) for value in self.formats)
        if len(set(formats)) != len(formats):
            raise ValueError("formats must be unique")
        object.__setattr__(self, "formats", formats)

        if not callable(self.adapt):
            raise TypeError("adapt must be callable")
        if self.detect is not None and not callable(self.detect):
            raise TypeError("detect must be callable or None")

    def __call__(self, source: SourceArtifact) -> T:
        """Adapt one source artifact."""
        return self.adapt(source)

    def supports(self, source: SourceArtifact) -> bool:
        """Return whether this adapter supports the artifact format and shape."""
        if source.format not in self.formats:
            return False
        return self.detect(source) if self.detect is not None else True


class AdapterRegistry:
    """Application-owned requirement and state-model adapter registry."""

    def __init__(self) -> None:
        self._requirement_adapters: dict[str, Adapter[RequirementSet]] = {}
        self._state_model_adapters: dict[str, Adapter[StateModel]] = {}

    def register_requirement(
        self,
        adapter: Adapter[RequirementSet],
        *,
        replace: bool = False,
    ) -> None:
        """Register an adapter producing a requirement set."""
        _register(self._requirement_adapters, adapter, replace=replace)

    def register_state_model(
        self,
        adapter: Adapter[StateModel],
        *,
        replace: bool = False,
    ) -> None:
        """Register an adapter producing one state model."""
        _register(self._state_model_adapters, adapter, replace=replace)

    def get_requirement(self, adapter_id: str) -> Adapter[RequirementSet] | None:
        """Return a registered requirement adapter."""
        _validate_adapter_id(adapter_id)
        return self._requirement_adapters.get(adapter_id)

    def get_state_model(self, adapter_id: str) -> Adapter[StateModel] | None:
        """Return a registered state-model adapter."""
        _validate_adapter_id(adapter_id)
        return self._state_model_adapters.get(adapter_id)

    def requirement_adapters(self) -> Iterator[Adapter[RequirementSet]]:
        """Iterate over requirement adapters in registration order."""
        return iter(self._requirement_adapters.values())

    def state_model_adapters(self) -> Iterator[Adapter[StateModel]]:
        """Iterate over state-model adapters in registration order."""
        return iter(self._state_model_adapters.values())


def _register[T](
    adapters: dict[str, Adapter[T]],
    adapter: Adapter[T],
    *,
    replace: bool,
) -> None:
    if not isinstance(adapter, Adapter):
        raise TypeError("adapter must be an Adapter")
    if not replace and adapter.id in adapters:
        raise ValueError(f"adapter {adapter.id!r} is already registered")
    adapters[adapter.id] = adapter


def _validate_adapter_id(adapter_id: str) -> None:
    if not isinstance(adapter_id, str):
        raise TypeError("adapter_id must be a string")
    if _ADAPTER_ID_PATTERN.fullmatch(adapter_id) is None:
        raise ValueError("adapter_id is not a valid adapter identifier")


def _normalize_format(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("adapter formats must be strings")
    normalized = value.strip().casefold().removeprefix(".")
    if not normalized:
        raise ValueError("adapter formats must not be blank")
    return normalized
