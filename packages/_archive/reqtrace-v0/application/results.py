"""Compatibility exports for application request and result models.

The model definitions are split across:
- `request_models.py`
- `result_enums.py`
- `result_models.py`

This module is retained as a stable import surface.
"""

from __future__ import annotations

from reqtrace.application.request_models import (
    EvidenceSnapshot,
    RequirementSnapshot,
    TraceabilityRequest,
)
from reqtrace.application.result_enums import (
    CoverageVerdict,
    FlowStatus,
    MatchRole,
    RequirementResultStatus,
    RunStatus,
    StrEnum,
    TraceKind,
    TracePathItemKind,
)
from reqtrace.application.result_models import (
    CoverageSummary,
    ExecutionInstance,
    ExecutionTrace,
    FlowCoverageResult,
    FragmentTraceResult,
    GlobalCoverageSummary,
    InputSummary,
    RequirementTraceabilityResult,
    TraceabilityResult,
    TraceabilityRun,
    TraceabilitySummary,
    TracePathItem,
)

__all__ = [
    "CoverageSummary",
    "CoverageVerdict",
    "EvidenceSnapshot",
    "ExecutionInstance",
    "ExecutionTrace",
    "FlowCoverageResult",
    "FlowStatus",
    "FragmentTraceResult",
    "GlobalCoverageSummary",
    "InputSummary",
    "MatchRole",
    "RequirementResultStatus",
    "RequirementSnapshot",
    "RequirementTraceabilityResult",
    "RunStatus",
    "StrEnum",
    "TraceKind",
    "TracePathItem",
    "TracePathItemKind",
    "TraceabilityRequest",
    "TraceabilityResult",
    "TraceabilityRun",
    "TraceabilitySummary",
]
