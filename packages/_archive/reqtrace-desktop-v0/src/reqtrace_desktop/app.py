from __future__ import annotations

import logging
import multiprocessing as mp
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger(__name__)
_SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
_DEFAULT_LOG_BACKUP_COUNT = 3


def _print_desktop_unavailable_message(message: str) -> None:
    print(message, file=sys.stderr)


def _configure_app_logging(
    *,
    level_name: str,
    log_file: str | Path | None,
) -> int:
    normalized = level_name.strip().upper()
    if normalized not in _SUPPORTED_LOG_LEVELS:
        raise ValueError(
            f"Unsupported log level: {level_name!r}. "
            f"Supported values: {', '.join(_SUPPORTED_LOG_LEVELS)}."
        )
    resolved_level = getattr(logging, normalized)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                filename=path,
                maxBytes=_DEFAULT_LOG_MAX_BYTES,
                backupCount=_DEFAULT_LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
        )
    logging.basicConfig(
        level=resolved_level,
        handlers=handlers,
        force=True,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return resolved_level


def launch_desktop(
    *, log_level: str | None = None, log_file: str | Path | None = None
) -> int:
    """Launch the desktop app.

    Returns a process exit code (0 = success, non-zero = could not start).
    This fails gracefully in headless environments (e.g., devcontainers).
    """
    resolved_log_level = log_level or os.environ.get("REQTRACE_LOG_LEVEL", "INFO")
    resolved_log_file: str | Path | None = log_file
    if resolved_log_file is None:
        resolved_log_file = os.environ.get("REQTRACE_LOG_FILE")
    if resolved_log_file is not None and not str(resolved_log_file).strip():
        resolved_log_file = None

    # Required on Windows for spawn-based child workers, especially in frozen builds.
    mp.freeze_support()
    try:
        _configure_app_logging(
            level_name=resolved_log_level,
            log_file=resolved_log_file,
        )
    except (OSError, ValueError) as exc:
        _print_desktop_unavailable_message(str(exc))
        return 2

    logger.debug(
        "Launching ReqTrace desktop app.",
        extra={
            "log_level": resolved_log_level.upper(),
            "log_file": str(resolved_log_file) if resolved_log_file else None,
        },
    )
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        _print_desktop_unavailable_message(
            "ReqTrace desktop app cannot start: no $DISPLAY environment variable was found.\n"
            "You're likely running in a headless environment (e.g., a devcontainer).\n\n"
            "Options:\n"
            "- Use the CLI:  reqtrace run ...\n"
            "- Run the desktop app on your host machine\n"
            "- Configure display forwarding (X11/XWayland) and set $DISPLAY\n"
        )
        return 2

    try:
        import tkinter as tk

        from reqtrace_desktop.controller import ReqTraceDesktopController
    except ImportError as exc:
        logger.error(
            "ReqTrace desktop app failed to import required desktop modules.",
            exc_info=exc,
        )
        _print_desktop_unavailable_message(
            "ReqTrace desktop app cannot start (missing Tkinter runtime).\n"
            f"Details: {exc}\n\n"
            "Install the Tk runtime for your platform, then try again."
        )
        return 2

    try:
        controller = ReqTraceDesktopController()
        controller.run()
        logger.info("ReqTrace desktop app exited normally.")
        return 0
    except tk.TclError as exc:
        logger.error(
            "ReqTrace desktop app failed to start due to Tkinter error.",
            exc_info=exc,
        )
        _print_desktop_unavailable_message(
            "ReqTrace desktop app cannot start (Tkinter error).\n"
            f"Details: {exc}\n\n"
            "This typically means the environment has no graphical display.\n"
            "Try running the desktop app on a machine with a desktop session or enable display forwarding."
        )
        return 2


def main() -> int:
    return launch_desktop()


if __name__ == "__main__":
    raise SystemExit(main())
