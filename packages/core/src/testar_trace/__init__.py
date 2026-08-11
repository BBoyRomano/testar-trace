"""Core models and traceability analysis for TESTAR Trace."""

import logging

from testar_trace.analysis import analyze_traceability
from testar_trace.domain import (
    FormalRequirementSet,
    RequirementSet,
    StateModel,
    StateModelCollection,
    TraceabilityResult,
)
from testar_trace.evaluation import (
    CompletenessClassMetrics,
    CompletenessEvaluation,
    CompletenessReferenceLabel,
    ConfusionMatrixRow,
    evaluate_completeness,
)
from testar_trace.execution import (
    CancellationToken,
    ProgressCallback,
    ProgressEvent,
    TraceCancelledError,
    TraceContext,
)
from testar_trace.methods._builtins import (
    create_builtin_method_registry,
)
from testar_trace.methods._registry import (
    TraceCallable,
    TraceMethod,
    TraceMethodRegistry,
)
from testar_trace.serialization import to_plain_data

__all__ = [
    "CancellationToken",
    "CompletenessClassMetrics",
    "CompletenessEvaluation",
    "CompletenessReferenceLabel",
    "ConfusionMatrixRow",
    "FormalRequirementSet",
    "ProgressCallback",
    "ProgressEvent",
    "RequirementSet",
    "StateModel",
    "StateModelCollection",
    "TraceCallable",
    "TraceCancelledError",
    "TraceContext",
    "TraceMethod",
    "TraceMethodRegistry",
    "TraceabilityResult",
    "analyze_traceability",
    "create_builtin_method_registry",
    "evaluate_completeness",
    "to_plain_data",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
