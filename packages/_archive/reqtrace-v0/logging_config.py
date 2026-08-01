"""Central logging configuration for ReqTrace."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 3
_RESERVED_LOG_RECORD_KEYS = frozenset(
    logging.LogRecord(
        name="reqtrace",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
)


def _format_extra_value(value: object) -> str:
    text = str(value)
    if len(text) > 160:
        text = text[:157] + "..."
    if any(char.isspace() for char in text):
        return repr(text)
    return text


class _ContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        extras: list[str] = []
        for key, value in sorted(record.__dict__.items()):
            if key in _RESERVED_LOG_RECORD_KEYS or key in {"message", "asctime"}:
                continue
            if key.startswith("_"):
                continue
            extras.append(f"{key}={_format_extra_value(value)}")
        if extras:
            return f"{formatted} | {' '.join(extras)}"
        return formatted


def parse_log_level(level: str) -> int:
    normalized = level.strip().upper()
    if normalized not in SUPPORTED_LOG_LEVELS:
        raise ValueError(
            f"Unsupported log level: {level!r}. "
            f"Supported values: {', '.join(SUPPORTED_LOG_LEVELS)}."
        )
    return getattr(logging, normalized)


def configure_logging(
    level: str = "INFO",
    *,
    force: bool = True,
    log_file: str | Path | None = None,
    max_bytes: int = DEFAULT_LOG_MAX_BYTES,
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
) -> int:
    """Configure process logging and return the resolved numeric level."""

    resolved_level = parse_log_level(level)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                filename=path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
        )
    formatter = _ContextFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(
        level=resolved_level,
        handlers=handlers,
        force=force,
    )
    return resolved_level
