"""Canonical traceability relationships and analysis results."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from testar_trace.domain._metadata import freeze_metadata
from testar_trace.domain._validation import (
    require_ids,
    require_optional_text,
    require_text,
    require_unit_interval,
    unique_ids,
)
from testar_trace.domain.provenance import SourceRef
from testar_trace.domain.requirement_paths import PathMaterializationResult

__all__ = [
    "AssessabilityStatus",
    "AssessmentScopeKind",
    "AssessmentViewKind",
    "CompletenessStatus",
    "CoverageAssessment",
    "CoverageStatus",
    "TraceEvidenceBasis",
    "TraceLink",
    "TraceOccurrence",
    "TraceOccurrenceStatus",
    "TraceTargetKind",
    "TraceTargetRef",
    "TraceabilityResult",
    "TraceabilitySummary",
]


class CoverageStatus(StrEnum):
    """Coverage status assigned to a requirement."""

    COVERED = "covered"
    PARTIALLY_COVERED = "partially-covered"
    NOT_COVERED = "not-covered"


class AssessabilityStatus(StrEnum):
    """Extent to which available inputs permit a coverage assessment."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"
    UNKNOWN = "unknown"


class CompletenessStatus(StrEnum):
    """Completeness conclusion for an assessed requirement scope."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    NOT_ASSESSABLE = "not-assessable"


class AssessmentScopeKind(StrEnum):
    """Canonical requirement scope at which coverage is aggregated."""

    PATH = "path"
    BRANCH = "branch"
    FLOW = "flow"
    REQUIREMENT = "requirement"
    REQUIREMENT_SET = "requirement-set"


class AssessmentViewKind(StrEnum):
    """State-model view over which findings are aggregated."""

    STATE_MODEL = "state-model"
    STATE_MODEL_COLLECTION = "state-model-collection"


class TraceTargetKind(StrEnum):
    """Kind of state-model element referenced by traceability data."""

    STATE_MODEL = "state-model"
    STATE = "state"
    WIDGET = "widget"
    ACTION = "action"
    TRANSITION = "transition"
    EXECUTION_SEQUENCE = "execution-sequence"
    EXECUTION_STEP = "execution-step"


class TraceOccurrenceStatus(StrEnum):
    """Coverage status of one concrete trace occurrence."""

    FULL = "full"
    PARTIAL = "partial"


class TraceEvidenceBasis(StrEnum):
    """Kind of coherent state-model route supporting an occurrence."""

    STATE_MODEL_GRAPH = "state-model-graph"
    EXECUTION_SEQUENCE = "execution-sequence"
    FORMAL_MODEL_CHECK = "formal-model-check"


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceTargetRef:
    """Typed reference to a state-model trace target."""

    kind: TraceTargetKind
    target_id: str

    def __post_init__(self) -> None:
        require_text(self.target_id, "target_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceLink:
    """One scored requirement match to one state-model target."""

    id: str
    requirement_id: str
    state_model_id: str
    target_ref: TraceTargetRef
    score: float
    requirement_element_id: str | None = None
    occurrence_id: str | None = None
    rationale: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.state_model_id, "state_model_id")
        require_optional_text(self.requirement_element_id, "requirement_element_id")
        require_optional_text(self.occurrence_id, "occurrence_id")
        if not isinstance(self.target_ref, TraceTargetRef):
            raise TypeError("target_ref must be a TraceTargetRef")
        require_unit_interval(self.score, "score")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceOccurrence:
    """Concrete occurrence of requirement coverage in a state model."""

    id: str
    requirement_id: str
    flow_id: str
    path_id: str
    state_model_id: str
    evidence_basis: TraceEvidenceBasis
    status: TraceOccurrenceStatus
    target_path: tuple[TraceTargetRef, ...]
    execution_sequence_id: str | None = None
    covered_element_ids: tuple[str, ...] = ()
    missing_element_ids: tuple[str, ...] = ()
    link_ids: tuple[str, ...] = ()
    score: float | None = None
    rationale: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.flow_id, "flow_id")
        require_text(self.path_id, "path_id")
        require_text(self.state_model_id, "state_model_id")
        require_optional_text(self.execution_sequence_id, "execution_sequence_id")

        if not isinstance(self.evidence_basis, TraceEvidenceBasis):
            raise TypeError("evidence_basis must be a TraceEvidenceBasis")
        if not isinstance(self.status, TraceOccurrenceStatus):
            raise TypeError("status must be a TraceOccurrenceStatus")
        if (
            self.evidence_basis is TraceEvidenceBasis.EXECUTION_SEQUENCE
            and self.execution_sequence_id is None
        ):
            raise ValueError(
                "execution_sequence_id is required for execution-sequence evidence"
            )

        if not self.target_path:
            raise ValueError("target_path must not be empty")

        require_ids(
            self.covered_element_ids,
            "covered_element_ids",
            allow_empty=True,
            unique=True,
        )
        require_ids(
            self.missing_element_ids,
            "missing_element_ids",
            allow_empty=True,
            unique=True,
        )
        require_ids(
            self.link_ids,
            "link_ids",
            allow_empty=True,
            unique=True,
        )
        require_unit_interval(self.score, "score")

        overlapping = set(self.covered_element_ids) & set(self.missing_element_ids)
        if overlapping:
            raise ValueError("covered and missing elements must be disjoint")
        if self.status is TraceOccurrenceStatus.FULL and self.missing_element_ids:
            raise ValueError("a full occurrence must not have missing elements")

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CoverageAssessment:
    """Coverage and completeness at one requirement scope and model view."""

    id: str
    scope_kind: AssessmentScopeKind
    scope_id: str
    requirement_ids: tuple[str, ...]
    view_kind: AssessmentViewKind
    state_model_collection_id: str
    state_model_ids: tuple[str, ...]
    status: CoverageStatus
    assessability: AssessabilityStatus
    completeness: CompletenessStatus
    occurrence_ids: tuple[str, ...] = ()
    covered_element_ids: tuple[str, ...] = ()
    missing_element_ids: tuple[str, ...] = ()
    coverage_ratio: float | None = None
    rationale: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.scope_id, "scope_id")
        require_ids(self.requirement_ids, "requirement_ids", unique=True)
        require_text(self.state_model_collection_id, "state_model_collection_id")
        require_ids(self.state_model_ids, "state_model_ids", unique=True)
        require_ids(
            self.occurrence_ids,
            "occurrence_ids",
            allow_empty=True,
            unique=True,
        )
        require_ids(
            self.covered_element_ids,
            "covered_element_ids",
            allow_empty=True,
            unique=True,
        )
        require_ids(
            self.missing_element_ids,
            "missing_element_ids",
            allow_empty=True,
            unique=True,
        )
        require_unit_interval(self.coverage_ratio, "coverage_ratio")

        for value, enum_type, field_name in (
            (self.scope_kind, AssessmentScopeKind, "scope_kind"),
            (self.view_kind, AssessmentViewKind, "view_kind"),
            (self.status, CoverageStatus, "status"),
            (self.assessability, AssessabilityStatus, "assessability"),
            (self.completeness, CompletenessStatus, "completeness"),
        ):
            if not isinstance(value, enum_type):
                raise TypeError(f"{field_name} must be a {enum_type.__name__}")

        if (
            self.scope_kind is not AssessmentScopeKind.REQUIREMENT_SET
            and len(self.requirement_ids) != 1
        ):
            raise ValueError(
                "path, branch, flow, and requirement assessments must refer "
                "to exactly one requirement"
            )
        if (
            self.view_kind is AssessmentViewKind.STATE_MODEL
            and len(self.state_model_ids) != 1
        ):
            raise ValueError("a state-model assessment must refer to exactly one model")

        overlapping = set(self.covered_element_ids) & set(self.missing_element_ids)
        if overlapping:
            raise ValueError("covered and missing elements must be disjoint")

        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceabilitySummary:
    """Aggregate counts derived from a traceability result."""

    total_requirements: int
    covered_requirements: int
    partially_covered_requirements: int
    uncovered_requirements: int
    complete_requirements: int
    incomplete_requirements: int
    not_assessable_requirements: int
    total_paths: int
    complete_paths: int
    incomplete_paths: int
    not_assessable_paths: int
    total_links: int
    total_occurrences: int
    overall_coverage_ratio: float | None


@dataclass(frozen=True, slots=True, kw_only=True)
class TraceabilityResult:
    """Canonical result of one traceability analysis."""

    id: str
    title: str
    path_materialization: PathMaterializationResult
    assessments: tuple[CoverageAssessment, ...]
    links: tuple[TraceLink, ...] = ()
    occurrences: tuple[TraceOccurrence, ...] = ()
    requirement_source_refs: tuple[SourceRef, ...] = ()
    state_model_source_refs: tuple[SourceRef, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.title, "title")
        if not isinstance(self.path_materialization, PathMaterializationResult):
            raise TypeError("path_materialization must be a PathMaterializationResult")

        link_ids = unique_ids(self.links, "TraceLink")
        links_by_id = {link.id: link for link in self.links}
        unique_ids(self.assessments, "CoverageAssessment")
        occurrence_ids = unique_ids(
            self.occurrences,
            "TraceOccurrence",
        )
        occurrences_by_id = {
            occurrence.id: occurrence for occurrence in self.occurrences
        }
        requirement_ids = {
            requirement_id
            for assessment in self.assessments
            for requirement_id in assessment.requirement_ids
        }
        paths_by_id = {path.id: path for path in self.path_materialization.paths}
        collection_ids = {
            assessment.state_model_collection_id for assessment in self.assessments
        }
        state_model_ids = {
            state_model_id
            for assessment in self.assessments
            for state_model_id in assessment.state_model_ids
        }
        if len(collection_ids) > 1:
            raise ValueError("all assessments must use one state-model collection")

        for occurrence in self.occurrences:
            if occurrence.requirement_id not in requirement_ids:
                raise ValueError(
                    "TraceOccurrence.requirement_id must reference "
                    "an assessed requirement"
                )
            if occurrence.state_model_id not in state_model_ids:
                raise ValueError(
                    "TraceOccurrence.state_model_id must reference an assessed "
                    "state model"
                )
            if occurrence.path_id not in paths_by_id:
                raise ValueError(
                    "TraceOccurrence.path_id must reference a materialized path"
                )
            path = paths_by_id[occurrence.path_id]
            if occurrence.requirement_id != path.requirement_id:
                raise ValueError(
                    "an occurrence and its path must reference the same requirement"
                )
            if occurrence.flow_id != path.flow_id:
                raise ValueError(
                    "an occurrence and its path must reference the same flow"
                )
            occurrence_element_ids = set(occurrence.covered_element_ids) | set(
                occurrence.missing_element_ids
            )
            if not occurrence_element_ids <= set(path.element_ids):
                raise ValueError(
                    "an occurrence may reference only elements on its path"
                )

            for link_id in occurrence.link_ids:
                if link_id not in link_ids:
                    raise ValueError(
                        "TraceOccurrence.link_ids must reference "
                        f"a known link: {link_id}"
                    )

                link = links_by_id[link_id]

                if link.occurrence_id != occurrence.id:
                    raise ValueError("an occurrence may reference only its own links")
                if link.requirement_id != occurrence.requirement_id:
                    raise ValueError(
                        "an occurrence and its links must reference "
                        "the same requirement"
                    )
                if link.state_model_id != occurrence.state_model_id:
                    raise ValueError(
                        "an occurrence and its links must reference the same state model"
                    )

        for assessment in self.assessments:
            if assessment.scope_kind is AssessmentScopeKind.PATH:
                if assessment.scope_id not in paths_by_id:
                    raise ValueError(
                        "a path assessment must reference a materialized path"
                    )
                path = paths_by_id[assessment.scope_id]
                if assessment.requirement_ids != (path.requirement_id,):
                    raise ValueError(
                        "a path assessment must reference its path's requirement"
                    )
                assessed_element_ids = set(assessment.covered_element_ids) | set(
                    assessment.missing_element_ids
                )
                if not assessed_element_ids <= set(path.element_ids):
                    raise ValueError(
                        "a path assessment may reference only elements on its path"
                    )

            for occurrence_id in assessment.occurrence_ids:
                if occurrence_id not in occurrence_ids:
                    raise ValueError(
                        "CoverageAssessment.occurrence_ids must reference a known "
                        "occurrence"
                    )
                occurrence = occurrences_by_id[occurrence_id]
                if occurrence.requirement_id not in assessment.requirement_ids:
                    raise ValueError(
                        "an assessment may reference occurrences only for its "
                        "requirements"
                    )
                if occurrence.state_model_id not in assessment.state_model_ids:
                    raise ValueError(
                        "an assessment may reference occurrences only from its "
                        "state-model view"
                    )
                if (
                    assessment.scope_kind is AssessmentScopeKind.PATH
                    and occurrence.path_id != assessment.scope_id
                ):
                    raise ValueError(
                        "a path assessment may reference occurrences only for its path"
                    )
                if (
                    assessment.scope_kind is AssessmentScopeKind.FLOW
                    and occurrence.flow_id != assessment.scope_id
                ):
                    raise ValueError(
                        "a flow assessment may reference occurrences only for its flow"
                    )
                if assessment.scope_kind is AssessmentScopeKind.BRANCH:
                    path = paths_by_id[occurrence.path_id]
                    if assessment.scope_id not in path.branch_ids:
                        raise ValueError(
                            "a branch assessment may reference occurrences only "
                            "for paths containing its branch"
                        )

        for link in self.links:
            if link.requirement_id not in requirement_ids:
                raise ValueError(
                    "TraceLink.requirement_id must reference an assessed requirement"
                )
            if link.state_model_id not in state_model_ids:
                raise ValueError(
                    "TraceLink.state_model_id must reference an assessed state model"
                )
            if link.occurrence_id is None:
                continue
            if link.occurrence_id not in occurrence_ids:
                raise ValueError(
                    "TraceLink.occurrence_id must reference a known occurrence"
                )
            occurrence = occurrences_by_id[link.occurrence_id]
            if link.id not in occurrence.link_ids:
                raise ValueError(
                    "an occurrence-linked link must be referenced by that occurrence"
                )
            if link.requirement_id != occurrence.requirement_id:
                raise ValueError(
                    "an occurrence-linked link must reference the same requirement"
                )
            if link.state_model_id != occurrence.state_model_id:
                raise ValueError(
                    "an occurrence-linked link must reference the same state model"
                )
            path = paths_by_id[occurrence.path_id]
            if (
                link.requirement_element_id is not None
                and link.requirement_element_id not in path.element_ids
            ):
                raise ValueError(
                    "an occurrence-linked link may reference only elements on its path"
                )
            if link.target_ref not in occurrence.target_path:
                raise ValueError(
                    "an occurrence-linked link must target an entity on its path"
                )

        object.__setattr__(
            self,
            "metadata",
            freeze_metadata(self.metadata),
        )

    @property
    def summary(self) -> TraceabilitySummary:
        """Return aggregate counts derived from the result."""
        requirement_assessments = tuple(
            assessment
            for assessment in self.assessments
            if assessment.scope_kind is AssessmentScopeKind.REQUIREMENT
            and assessment.view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
        )
        path_assessments = tuple(
            assessment
            for assessment in self.assessments
            if assessment.scope_kind is AssessmentScopeKind.PATH
            and assessment.view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
        )
        requirement_statuses = Counter(
            assessment.status for assessment in requirement_assessments
        )
        requirement_completeness = Counter(
            assessment.completeness for assessment in requirement_assessments
        )
        path_completeness = Counter(
            assessment.completeness for assessment in path_assessments
        )
        set_assessments = tuple(
            assessment
            for assessment in self.assessments
            if assessment.scope_kind is AssessmentScopeKind.REQUIREMENT_SET
            and assessment.view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
        )
        if len(set_assessments) > 1:
            raise ValueError(
                "a result must contain at most one collection-wide "
                "requirement-set assessment"
            )

        return TraceabilitySummary(
            total_requirements=len(requirement_assessments),
            covered_requirements=requirement_statuses[CoverageStatus.COVERED],
            partially_covered_requirements=requirement_statuses[
                CoverageStatus.PARTIALLY_COVERED
            ],
            uncovered_requirements=requirement_statuses[CoverageStatus.NOT_COVERED],
            complete_requirements=requirement_completeness[CompletenessStatus.COMPLETE],
            incomplete_requirements=requirement_completeness[
                CompletenessStatus.INCOMPLETE
            ],
            not_assessable_requirements=requirement_completeness[
                CompletenessStatus.NOT_ASSESSABLE
            ],
            total_paths=len(path_assessments),
            complete_paths=path_completeness[CompletenessStatus.COMPLETE],
            incomplete_paths=path_completeness[CompletenessStatus.INCOMPLETE],
            not_assessable_paths=path_completeness[CompletenessStatus.NOT_ASSESSABLE],
            total_links=len(self.links),
            total_occurrences=len(self.occurrences),
            overall_coverage_ratio=(
                set_assessments[0].coverage_ratio if set_assessments else None
            ),
        )
