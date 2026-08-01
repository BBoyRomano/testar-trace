"""Adapters for loading external inputs into ReqTrace models."""

import logging

from reqtrace_adapters._builtins import register_builtin_parsers
from reqtrace_adapters.load import (
    load_evidence,
    load_requirements,
    validate_evidence,
    validate_requirements,
)
from reqtrace_adapters.registry import available_parsers, register_parser

__all__ = [
    "available_parsers",
    "load_evidence",
    "load_requirements",
    "register_parser",
    "validate_evidence",
    "validate_requirements",
]

register_builtin_parsers()

logging.getLogger(__name__).addHandler(logging.NullHandler())
