import pytest
from reqtrace.progress import CancellationToken, ProgressEvent, TraceContext


def test_progress_event_copies_metadata() -> None:
    metadata = {"phase_index": 1}

    event = ProgressEvent(
        phase="matching",
        metadata=metadata,
    )
    metadata["phase_index"] = 2

    assert event.metadata["phase_index"] == 1


def test_progress_event_rejects_blank_phase() -> None:
    with pytest.raises(ValueError, match="phase must not be blank"):
        ProgressEvent(phase=" ")


def test_progress_event_rejects_negative_completed() -> None:
    with pytest.raises(ValueError, match="completed must be non-negative"):
        ProgressEvent(phase="matching", completed=-1)


def test_progress_event_rejects_negative_total() -> None:
    with pytest.raises(ValueError, match="total must be non-negative"):
        ProgressEvent(phase="matching", total=-1)


def test_progress_event_rejects_completed_greater_than_total() -> None:
    with pytest.raises(ValueError, match="completed must not be greater than total"):
        ProgressEvent(phase="matching", completed=2, total=1)


def test_cancellation_token_raises_after_cancel() -> None:
    token = CancellationToken()

    token.cancel()

    with pytest.raises(InterruptedError, match="cancelled"):
        token.raise_if_cancelled()


def test_trace_context_reports_progress() -> None:
    events: list[ProgressEvent] = []
    context = TraceContext(progress=events.append)

    context.report(
        "matching",
        message="Matching requirements",
        completed=1,
        total=2,
        metadata={"method": "test"},
    )

    assert len(events) == 1
    assert events[0].phase == "matching"
    assert events[0].message == "Matching requirements"
    assert events[0].completed == 1
    assert events[0].total == 2
    assert events[0].metadata["method"] == "test"


def test_trace_context_ignores_progress_without_reporter() -> None:
    context = TraceContext()

    context.report("matching", message="This should be ignored")


def test_trace_context_raises_when_cancelled() -> None:
    token = CancellationToken(cancelled=True)
    context = TraceContext(cancellation=token)

    with pytest.raises(InterruptedError, match="cancelled"):
        context.raise_if_cancelled()
