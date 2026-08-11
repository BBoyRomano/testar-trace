"""Optional external-format adapters for TESTAR Trace."""

import logging

from testar_trace_adapters._builtins import create_builtin_adapter_registry
from testar_trace_adapters.loading import load_requirements, load_state_models
from testar_trace_adapters.registry import Adapter, AdapterRegistry
from testar_trace_adapters.source import (
    Source,
    SourceArtifact,
    SourceValue,
    read_source_artifacts,
)

__all__ = [
    "Adapter",
    "AdapterRegistry",
    "Source",
    "SourceArtifact",
    "SourceValue",
    "create_builtin_adapter_registry",
    "load_requirements",
    "load_state_models",
    "read_source_artifacts",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
