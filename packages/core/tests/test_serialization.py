from enum import StrEnum
from typing import cast

import pytest

from testar_trace import TraceabilityResult, to_plain_data


class ExampleStatus(StrEnum):
    READY = "ready"


def test_to_plain_data_converts_canonical_result_and_summary(
    empty_trace_result: TraceabilityResult,
) -> None:
    value = cast("dict[str, object]", to_plain_data(empty_trace_result))

    assert isinstance(value, dict)
    assert value["id"] == "test-result"
    assert value["summary"] == {
        "total_requirements": 1,
        "covered_requirements": 0,
        "partially_covered_requirements": 0,
        "uncovered_requirements": 1,
        "complete_requirements": 0,
        "incomplete_requirements": 0,
        "not_assessable_requirements": 1,
        "total_paths": 0,
        "complete_paths": 0,
        "incomplete_paths": 0,
        "not_assessable_paths": 0,
        "total_links": 0,
        "total_occurrences": 0,
        "overall_coverage_ratio": None,
    }


def test_to_plain_data_converts_nested_enums_and_collections() -> None:
    assert to_plain_data({"statuses": (ExampleStatus.READY,)}) == {
        "statuses": ["ready"]
    }


def test_to_plain_data_rejects_unsupported_values() -> None:
    with pytest.raises(TypeError, match="Cannot serialize object"):
        to_plain_data(object())
