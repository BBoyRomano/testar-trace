"""Deterministic evaluation of completeness classifications."""

from collections import Counter
from dataclasses import dataclass

from testar_trace.domain.traceability import (
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    TraceabilityResult,
)

__all__ = [
    "CompletenessClassMetrics",
    "CompletenessEvaluation",
    "CompletenessReferenceLabel",
    "ConfusionMatrixRow",
    "evaluate_completeness",
]

_CLASSES = tuple(CompletenessStatus)


@dataclass(frozen=True, slots=True, kw_only=True)
class CompletenessReferenceLabel:
    """Independently curated expected completeness for one result scope."""

    scope_kind: AssessmentScopeKind
    scope_id: str
    completeness: CompletenessStatus

    def __post_init__(self) -> None:
        if not isinstance(self.scope_kind, AssessmentScopeKind):
            raise TypeError("scope_kind must be an AssessmentScopeKind")
        if not isinstance(self.completeness, CompletenessStatus):
            raise TypeError("completeness must be a CompletenessStatus")
        if not isinstance(self.scope_id, str):
            raise TypeError("scope_id must be a string")
        if self.scope_kind is AssessmentScopeKind.REQUIREMENT_SET:
            raise ValueError(
                "reference labels must identify an individual result scope"
            )
        if not self.scope_id or self.scope_id != self.scope_id.strip():
            raise ValueError(
                "scope_id must be non-empty without surrounding whitespace"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class CompletenessClassMetrics:
    """Precision, recall, and F1 for one completeness class."""

    completeness: CompletenessStatus
    support: int
    predicted: int
    true_positives: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ConfusionMatrixRow:
    """One expected-class row in the three-class confusion matrix."""

    expected: CompletenessStatus
    complete: int
    incomplete: int
    not_assessable: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CompletenessEvaluation:
    """Aggregate three-class evaluation for one traceability result."""

    total: int
    correct: int
    accuracy: float
    macro_f1: float
    assessability_rate: float
    class_metrics: tuple[CompletenessClassMetrics, ...]
    confusion_matrix: tuple[ConfusionMatrixRow, ...]


def evaluate_completeness(
    result: TraceabilityResult,
    labels: tuple[CompletenessReferenceLabel, ...],
) -> CompletenessEvaluation:
    """Compare collection-level assessments with independent reference labels."""
    if not isinstance(result, TraceabilityResult):
        raise TypeError("result must be a TraceabilityResult")
    if not isinstance(labels, tuple):
        raise TypeError("labels must be a tuple")
    if not all(isinstance(label, CompletenessReferenceLabel) for label in labels):
        raise TypeError("labels must contain CompletenessReferenceLabel values")
    if not labels:
        raise ValueError("labels must not be empty")

    label_keys = tuple((label.scope_kind, label.scope_id) for label in labels)
    if len(set(label_keys)) != len(label_keys):
        raise ValueError("reference labels must identify unique scopes")

    assessments = {
        (assessment.scope_kind, assessment.scope_id): assessment.completeness
        for assessment in result.assessments
        if assessment.view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
    }
    pairs: list[tuple[CompletenessStatus, CompletenessStatus]] = []
    for label in labels:
        key = (label.scope_kind, label.scope_id)
        actual = assessments.get(key)
        if actual is None:
            raise ValueError(
                f"result has no collection assessment for "
                f"{label.scope_kind.value} {label.scope_id!r}"
            )
        pairs.append((label.completeness, actual))

    correct = sum(expected is actual for expected, actual in pairs)
    class_metrics = tuple(
        _class_metrics(completeness, pairs) for completeness in _CLASSES
    )
    matrix = Counter(pairs)
    confusion_matrix = tuple(
        ConfusionMatrixRow(
            expected=expected,
            complete=matrix[(expected, CompletenessStatus.COMPLETE)],
            incomplete=matrix[(expected, CompletenessStatus.INCOMPLETE)],
            not_assessable=matrix[(expected, CompletenessStatus.NOT_ASSESSABLE)],
        )
        for expected in _CLASSES
    )
    total = len(pairs)
    assessable = sum(
        actual is not CompletenessStatus.NOT_ASSESSABLE for _, actual in pairs
    )
    return CompletenessEvaluation(
        total=total,
        correct=correct,
        accuracy=correct / total,
        macro_f1=sum(item.f1 for item in class_metrics) / len(class_metrics),
        assessability_rate=assessable / total,
        class_metrics=class_metrics,
        confusion_matrix=confusion_matrix,
    )


def _class_metrics(
    completeness: CompletenessStatus,
    pairs: list[tuple[CompletenessStatus, CompletenessStatus]],
) -> CompletenessClassMetrics:
    support = sum(expected is completeness for expected, _ in pairs)
    predicted = sum(actual is completeness for _, actual in pairs)
    true_positives = sum(
        expected is completeness and actual is completeness
        for expected, actual in pairs
    )
    precision = true_positives / predicted if predicted else 0.0
    recall = true_positives / support if support else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return CompletenessClassMetrics(
        completeness=completeness,
        support=support,
        predicted=predicted,
        true_positives=true_positives,
        precision=precision,
        recall=recall,
        f1=f1,
    )
