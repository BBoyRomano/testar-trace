"""Unit tests for shared application error-boundary mapping."""

import pytest

from reqtrace.application.error_boundary import raise_public_error
from reqtrace.application.exceptions import (
    InvalidTraceabilityRequestError,
    TraceabilityError,
)
from reqtrace.errors import ExecutionError, InputError
from reqtrace.ingestion.exceptions import RunInputValidationError


def test_raise_public_error_preserves_input_error() -> None:
    original = InputError("bad input")
    with pytest.raises(InputError, match="bad input"):
        raise_public_error(original)


def test_raise_public_error_preserves_execution_error() -> None:
    original = ExecutionError("bad execution")
    with pytest.raises(ExecutionError, match="bad execution"):
        raise_public_error(original)


def test_raise_public_error_maps_validation_errors_to_input_error() -> None:
    with pytest.raises(InputError, match="invalid"):
        raise_public_error(RunInputValidationError("invalid"))

    with pytest.raises(InputError, match="invalid"):
        raise_public_error(InvalidTraceabilityRequestError("invalid"))


def test_raise_public_error_maps_traceability_error_to_execution_error() -> None:
    with pytest.raises(ExecutionError, match="failed"):
        raise_public_error(TraceabilityError("failed"))


def test_raise_public_error_maps_unknown_error_to_execution_error() -> None:
    with pytest.raises(ExecutionError, match="boom"):
        raise_public_error(RuntimeError("boom"))

