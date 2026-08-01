"""Canonical traceability result models."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from reqtrace.models.common import SourceRef, freeze_metadata

__all__ = [
    "CoverageStatus",
    "EvidenceRef",
    "EvidenceRefKind",
    "FragmentMatchKind",
    "RequirementCoverage",
    "RequirementFragmentAlignment",
    "TraceLink",
    "TraceLinkStatus",
    "TraceOccurrence",
    "TraceOccurrenceStatus",
    "TraceabilityResult",
    "TraceabilitySummary",
]


class TraceLinkStatus(StrEnum):
    """Status of an individual trace link."""

    MATCHED = "matched"
    PARTIAL = "partial"


class CoverageStatus(StrEnum):
    """Requirement-level coverage status."""

    COVERED = "covered"
    PARTIALLY_COVERED = "partially-covered"
    NOT_COVERED = "not-covered"


class EvidenceRefKind(StrEnum):
    """Kind of referenced evidence item."""

    ARTIFACT = "artifact"
    STATE = "state"
    ELEMENT = "element"
    ACTION = "action"
    TRANSITION = "transition"


class TraceOccurrenceStatus(StrEnum):
    """Coverage status for one concrete requirement occurrence."""

    FULL = "full"
    PARTIAL = "partial"


class FragmentMatchKind(StrEnum):
    """Match quality for one fragment-to-evidence alignment."""

    EXACT = "exact"
    SEMANTIC = "semantic"
    PARTIAL = "partial"


@dataclass(slots=True, frozen=True)
class EvidenceRef:
    """Typed reference to one evidence item."""

    kind: EvidenceRefKind
    evidence_id: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("EvidenceRef.evidence_id must not be blank.")


@dataclass(slots=True, frozen=True)
class TraceLink:
    """A traceability link between one requirement and evidence items."""

    id: str
    requirement_id: str
    evidence_ids: tuple[str, ...]
    status: TraceLinkStatus
    score: float | None = None
    rationale: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("TraceLink.id must not be blank.")
        if not self.requirement_id.strip():
            raise ValueError("TraceLink.requirement_id must not be blank.")
        if not self.evidence_ids:
            raise ValueError("TraceLink.evidence_ids must not be empty.")
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("TraceLink.score must be between 0 and 1.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class RequirementFragmentAlignment:
    """Alignment between one requirement fragment and evidence."""

    id: str
    requirement_id: str
    fragment_id: str
    occurrence_id: str
    evidence_refs: tuple[EvidenceRef, ...]
    match_kind: FragmentMatchKind
    score: float | None = None
    rationale: str | None = None
    fragment_kind: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("RequirementFragmentAlignment.id must not be blank.")
        if not self.requirement_id.strip():
            raise ValueError(
                "RequirementFragmentAlignment.requirement_id must not be blank."
            )
        if not self.fragment_id.strip():
            raise ValueError(
                "RequirementFragmentAlignment.fragment_id must not be blank."
            )
        if not self.occurrence_id.strip():
            raise ValueError(
                "RequirementFragmentAlignment.occurrence_id must not be blank."
            )
        if not self.evidence_refs:
            raise ValueError(
                "RequirementFragmentAlignment.evidence_refs must not be empty."
            )
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError(
                "RequirementFragmentAlignment.score must be between 0 and 1.",
            )
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class TraceOccurrence:
    """One concrete occurrence of requirement coverage in evidence."""

    id: str
    requirement_id: str
    status: TraceOccurrenceStatus
    evidence_path: tuple[EvidenceRef, ...]
    alignment_ids: tuple[str, ...] = ()
    score: float | None = None
    rationale: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("TraceOccurrence.id must not be blank.")
        if not self.requirement_id.strip():
            raise ValueError("TraceOccurrence.requirement_id must not be blank.")
        if not self.evidence_path:
            raise ValueError("TraceOccurrence.evidence_path must not be empty.")
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("TraceOccurrence.score must be between 0 and 1.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class RequirementCoverage:
    """Coverage summary for one requirement."""

    requirement_id: str
    status: CoverageStatus
    linked_evidence_ids: tuple[str, ...] = ()
    coverage_ratio: float | None = None
    rationale: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError("RequirementCoverage.requirement_id must not be blank.")
        if self.coverage_ratio is not None and not 0 <= self.coverage_ratio <= 1:
            raise ValueError(
                "RequirementCoverage.coverage_ratio must be between 0 and 1."
            )
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class TraceabilitySummary:
    """Aggregate summary for one traceability analysis result."""

    total_requirements: int
    covered_requirements: int
    partially_covered_requirements: int
    uncovered_requirements: int
    total_links: int
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("total_requirements", self.total_requirements),
            ("covered_requirements", self.covered_requirements),
            ("partially_covered_requirements", self.partially_covered_requirements),
            ("uncovered_requirements", self.uncovered_requirements),
            ("total_links", self.total_links),
        ):
            if value < 0:
                raise ValueError(f"TraceabilitySummary.{name} must be non-negative.")

        if (
            self.covered_requirements
            + self.partially_covered_requirements
            + self.uncovered_requirements
            != self.total_requirements
        ):
            raise ValueError(
                "covered + partially_covered + uncovered must equal "
                "total_requirements.",
            )

        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class TraceabilityResult:
    """Canonical traceability analysis result."""

    id: str
    title: str
    summary: TraceabilitySummary
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    requirement_source_ref: SourceRef | None = None
    evidence_source_ref: SourceRef | None = None
    links: tuple[TraceLink, ...] = ()
    occurrences: tuple[TraceOccurrence, ...] = ()
    fragment_alignments: tuple[RequirementFragmentAlignment, ...] = ()
    coverage: tuple[RequirementCoverage, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("TraceabilityResult.id must not be blank.")
        if not self.title.strip():
            raise ValueError("TraceabilityResult.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))
        self._validate_references()

    def _validate_references(self) -> None:
        occurrence_ids = {occurrence.id for occurrence in self.occurrences}
        alignment_ids: set[str] = set()

        for alignment in self.fragment_alignments:
            if alignment.id in alignment_ids:
                raise ValueError(
                    f"Duplicate RequirementFragmentAlignment.id: {alignment.id}",
                )
            alignment_ids.add(alignment.id)

            if alignment.occurrence_id not in occurrence_ids:
                raise ValueError(
                    "RequirementFragmentAlignment.occurrence_id must reference "
                    f"a known occurrence: {alignment.occurrence_id}",
                )
