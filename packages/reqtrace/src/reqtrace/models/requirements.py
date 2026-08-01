"""Canonical requirement models."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from reqtrace.models.common import SourceRef, freeze_metadata

__all__ = [
    "RequirementArtifact",
    "RequirementDocument",
    "RequirementFragment",
    "RequirementScenario",
    "RequirementSet",
]


@dataclass(slots=True, frozen=True)
class RequirementDocument:
    """A source document containing one or more requirements."""

    id: str
    title: str
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("RequirementDocument.id must not be blank.")
        if not self.title.strip():
            raise ValueError("RequirementDocument.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class RequirementArtifact:
    """A canonical requirement ready for traceability analysis."""

    id: str
    title: str
    summary: str | None = None
    body: str | None = None
    actor: str | None = None
    scope: str | None = None
    level: str | None = None
    document_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("RequirementArtifact.id must not be blank.")
        if not self.title.strip():
            raise ValueError("RequirementArtifact.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class RequirementFragment:
    """An ordered requirement fragment such as a step or condition."""

    id: str
    requirement_id: str
    text: str
    kind: str = "fragment"
    order_index: int | None = None
    branch_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("RequirementFragment.id must not be blank.")
        if not self.requirement_id.strip():
            raise ValueError("RequirementFragment.requirement_id must not be blank.")
        if not self.text.strip():
            raise ValueError("RequirementFragment.text must not be blank.")
        if not self.kind.strip():
            raise ValueError("RequirementFragment.kind must not be blank.")
        if self.order_index is not None and self.order_index < 0:
            raise ValueError("RequirementFragment.order_index must be non-negative.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class RequirementScenario:
    """A traceable path through requirement fragments."""

    id: str
    requirement_id: str
    title: str
    kind: str
    fragment_ids: tuple[str, ...]
    order_index: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("RequirementScenario.id must not be blank.")
        if not self.requirement_id.strip():
            raise ValueError("RequirementScenario.requirement_id must not be blank.")
        if not self.title.strip():
            raise ValueError("RequirementScenario.title must not be blank.")
        if not self.kind.strip():
            raise ValueError("RequirementScenario.kind must not be blank.")
        if not self.fragment_ids:
            raise ValueError("RequirementScenario.fragment_ids must not be empty.")
        if any(not fragment_id.strip() for fragment_id in self.fragment_ids):
            raise ValueError(
                "RequirementScenario.fragment_ids must not contain blanks.",
            )
        if self.order_index is not None and self.order_index < 0:
            raise ValueError("RequirementScenario.order_index must be non-negative.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class RequirementSet:
    """A complete canonical requirements input for analysis."""

    documents: tuple[RequirementDocument, ...] = ()
    requirements: tuple[RequirementArtifact, ...] = ()
    fragments: tuple[RequirementFragment, ...] = ()
    scenarios: tuple[RequirementScenario, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))
        self._validate_references()

    def fragments_for(self, requirement_id: str) -> tuple[RequirementFragment, ...]:
        """Return fragments that belong to one requirement."""
        return tuple(
            fragment
            for fragment in self.fragments
            if fragment.requirement_id == requirement_id
        )

    def scenarios_for(self, requirement_id: str) -> tuple[RequirementScenario, ...]:
        """Return scenarios that belong to one requirement."""
        return tuple(
            scenario
            for scenario in self.scenarios
            if scenario.requirement_id == requirement_id
        )

    def _validate_references(self) -> None:
        requirement_ids = {requirement.id for requirement in self.requirements}
        fragment_ids: set[str] = set()
        scenario_ids: set[str] = set()

        for fragment in self.fragments:
            if fragment.id in fragment_ids:
                raise ValueError(f"Duplicate RequirementFragment.id: {fragment.id}")
            fragment_ids.add(fragment.id)

            if fragment.requirement_id not in requirement_ids:
                raise ValueError(
                    "RequirementFragment.requirement_id must reference a known "
                    f"requirement: {fragment.requirement_id}",
                )

        for scenario in self.scenarios:
            if scenario.id in scenario_ids:
                raise ValueError(f"Duplicate RequirementScenario.id: {scenario.id}")
            scenario_ids.add(scenario.id)

            if scenario.requirement_id not in requirement_ids:
                raise ValueError(
                    "RequirementScenario.requirement_id must reference a known "
                    f"requirement: {scenario.requirement_id}",
                )

            for fragment_id in scenario.fragment_ids:
                if fragment_id not in fragment_ids:
                    raise ValueError(
                        "RequirementScenario.fragment_ids must reference known "
                        f"fragments: {fragment_id}",
                    )
