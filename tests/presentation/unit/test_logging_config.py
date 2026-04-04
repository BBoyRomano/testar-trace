from __future__ import annotations

import logging
from pathlib import Path

import pytest

from reqtrace.logging_config import configure_logging, parse_log_level


def test_parse_log_level_rejects_unknown_level() -> None:
    with pytest.raises(ValueError):
        parse_log_level("verbose")


def test_configure_logging_accepts_case_insensitive_level() -> None:
    resolved = configure_logging("debug")
    assert resolved == logging.DEBUG


def test_configure_logging_writes_to_rotating_log_file(tmp_path: Path) -> None:
    log_path = tmp_path / "reqtrace.log"
    configure_logging("info", log_file=log_path)
    logging.getLogger("reqtrace.test").info("hello from test")
    for handler in logging.getLogger().handlers:
        handler.flush()
    assert log_path.exists()
    assert "hello from test" in log_path.read_text(encoding="utf-8")
