"""Reference-label loading and method-comparison orchestration."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import TypeGuard

from testar_trace import (
    CompletenessEvaluation,
    CompletenessReferenceLabel,
    TraceContext,
    TraceMethod,
    analyze_traceability,
    evaluate_completeness,
)
from testar_trace.domain import AssessmentScopeKind, CompletenessStatus, RequirementSet
from testar_trace.domain.state_models import StateModelCollection

from ._serialize import load_json_file


@dataclass(frozen=True, slots=True, kw_only=True)
class MethodComparison:
    """One method's measured result against the same reference labels."""

    method_id: str
    method_name: str
    duration_seconds: float
    evaluation: CompletenessEvaluation


def load_reference_labels(path: Path) -> tuple[CompletenessReferenceLabel, ...]:
    """Load and validate the versioned completeness-reference JSON format."""
    data = load_json_file(path)
    if not _is_object_dict(data):
        raise ValueError("reference-label file must contain a JSON object")
    unexpected_top_level = sorted(set(data) - {"schema_version", "labels"})
    if unexpected_top_level:
        raise ValueError(
            "reference-label file contains unsupported fields: "
            + ", ".join(unexpected_top_level)
        )
    if data.get("schema_version") != 1:
        raise ValueError("reference-label schema_version must be 1")
    items = data.get("labels")
    if not isinstance(items, list) or not items:
        raise ValueError("reference-label file must contain a non-empty labels array")

    labels: list[CompletenessReferenceLabel] = []
    for index, item in enumerate(items):
        if not _is_object_dict(item):
            raise ValueError(f"labels[{index}] must be a JSON object")
        unexpected_fields = sorted(
            set(item) - {"scope_kind", "scope_id", "completeness"}
        )
        if unexpected_fields:
            raise ValueError(
                f"labels[{index}] contains unsupported fields: "
                + ", ".join(unexpected_fields)
            )
        try:
            scope_kind = AssessmentScopeKind(str(item.get("scope_kind")))
            completeness = CompletenessStatus(str(item.get("completeness")))
        except ValueError as error:
            raise ValueError(
                f"labels[{index}] contains an unsupported class"
            ) from error
        scope_id = item.get("scope_id")
        if not isinstance(scope_id, str):
            raise TypeError(f"labels[{index}].scope_id must be a string")
        labels.append(
            CompletenessReferenceLabel(
                scope_kind=scope_kind,
                scope_id=scope_id,
                completeness=completeness,
            )
        )
    keys = [(label.scope_kind, label.scope_id) for label in labels]
    if len(set(keys)) != len(keys):
        raise ValueError("reference labels must identify unique scopes")
    return tuple(labels)


def compare_method(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    method: TraceMethod,
    labels: tuple[CompletenessReferenceLabel, ...],
    *,
    context: TraceContext,
) -> MethodComparison:
    """Run and evaluate one method with elapsed wall-clock time."""
    started = perf_counter()
    result = analyze_traceability(
        requirements, state_models, method=method, context=context
    )
    duration = perf_counter() - started
    return MethodComparison(
        method_id=method.id,
        method_name=method.name,
        duration_seconds=duration,
        evaluation=evaluate_completeness(result, labels),
    )


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)
