"""Trace-method definitions and registration."""

import re
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field

from testar_trace.domain.requirements import RequirementSet
from testar_trace.domain.state_models import StateModelCollection
from testar_trace.domain.traceability import TraceabilityResult
from testar_trace.execution import TraceContext

type TraceCallable = Callable[
    [RequirementSet, StateModelCollection, TraceContext],
    TraceabilityResult,
]

_METHOD_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceMethod:
    """A named trace method available for selection and execution."""

    id: str
    name: str
    trace: TraceCallable = field(repr=False)

    def __post_init__(self) -> None:
        _validate_method_id(self.id)

        if not isinstance(self.name, str):
            raise TypeError("name must be a string")

        if not self.name:
            raise ValueError("name must not be empty")

        if self.name != self.name.strip():
            raise ValueError("name must not start or end with whitespace")

        if not callable(self.trace):
            raise TypeError("trace must be callable")

    def __call__(
        self,
        requirements: RequirementSet,
        state_models: StateModelCollection,
        context: TraceContext,
    ) -> TraceabilityResult:
        """Execute the trace method."""
        return self.trace(requirements, state_models, context)


class TraceMethodRegistry:
    """Mutable registry of trace methods keyed by stable identifiers."""

    def __init__(
        self,
        methods: Iterable[TraceMethod] = (),
    ) -> None:
        self._methods: dict[str, TraceMethod] = {}

        for method in methods:
            self.register(method)

    def __len__(self) -> int:
        return len(self._methods)

    def __iter__(self) -> Iterator[TraceMethod]:
        return iter(self._methods.values())

    def register(
        self,
        method: TraceMethod,
        *,
        replace: bool = False,
    ) -> None:
        """Register a trace method."""
        if not isinstance(method, TraceMethod):
            raise TypeError("method must be a TraceMethod")

        if not replace and method.id in self._methods:
            raise ValueError(f"trace method {method.id!r} is already registered")

        self._methods[method.id] = method

    def get(self, method_id: str) -> TraceMethod | None:
        """Return the registered method, or `None` when it is absent."""
        _validate_method_id(method_id)
        return self._methods.get(method_id)


def _validate_method_id(method_id: str) -> None:
    if not isinstance(method_id, str):
        raise TypeError("method_id must be a string")

    if _METHOD_ID_PATTERN.fullmatch(method_id) is None:
        raise ValueError(
            "method_id must contain lowercase letters or digits "
            "separated by single hyphens"
        )
