from collections.abc import Callable

import pytest

from testar_trace import (
    CancellationToken,
    ProgressEvent,
    TraceCancelledError,
    TraceContext,
)


def test_progress_event_copies_metadata() -> None:
    metadata = {"phase_index": 1}

    event = ProgressEvent(phase="matching", metadata=metadata)
    metadata["phase_index"] = 2

    assert event.metadata["phase_index"] == 1


@pytest.mark.parametrize(
    ("factory", "expected_error"),
    [
        (lambda: ProgressEvent(phase=""), "phase must not be empty"),
        (
            lambda: ProgressEvent(phase=" matching"),
            "must not start or end with whitespace",
        ),
        (
            lambda: ProgressEvent(phase="matching", completed=-1),
            "completed must be non-negative",
        ),
        (
            lambda: ProgressEvent(phase="matching", total=-1),
            "total must be non-negative",
        ),
    ],
)
def test_progress_event_rejects_invalid_values(
    factory: Callable[[], ProgressEvent],
    expected_error: str,
) -> None:
    with pytest.raises(ValueError, match=expected_error):
        factory()


def test_progress_event_rejects_completed_greater_than_total() -> None:
    with pytest.raises(ValueError, match="completed must not be greater than total"):
        ProgressEvent(phase="matching", completed=2, total=1)


def test_cancellation_token_raises_after_cancel() -> None:
    token = CancellationToken()
    token.cancel()

    with pytest.raises(TraceCancelledError, match="cancelled"):
        token.raise_if_cancelled()


def test_trace_context_reports_structured_progress() -> None:
    events: list[ProgressEvent] = []
    context = TraceContext(progress=events.append)

    context.report(
        "matching",
        message="Matching requirements",
        completed=1,
        total=2,
        metadata={"method": "test"},
    )

    assert events == [
        ProgressEvent(
            phase="matching",
            message="Matching requirements",
            completed=1,
            total=2,
            metadata={"method": "test"},
        )
    ]


def test_trace_context_without_reporter_is_a_noop() -> None:
    TraceContext().report("matching", message="This is intentionally ignored")
