from __future__ import annotations

from datetime import datetime

import pytest

from reqtrace.application.history_models import RunHistoryEntry


def test_run_history_entry_rejects_naive_timestamps() -> None:
    with pytest.raises(ValueError):
        RunHistoryEntry(
            label="baseline :: run",
            created_at=datetime(2026, 1, 1, 12, 0, 0),
            updated_at=datetime(2026, 1, 1, 12, 0, 0),
        )
