"""Core models and traceability analysis for ReqTrace."""

import logging

from reqtrace._builtins import register_builtin_trace_methods
from reqtrace.analysis import analyze_traceability
from reqtrace.progress import CancellationToken, ProgressEvent, TraceContext
from reqtrace.registry import register_trace_method

__all__ = [
    "CancellationToken",
    "ProgressEvent",
    "TraceContext",
    "analyze_traceability",
    "register_trace_method",
]

register_builtin_trace_methods()

logging.getLogger(__name__).addHandler(logging.NullHandler())
