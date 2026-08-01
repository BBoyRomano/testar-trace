from __future__ import annotations

import logging
import multiprocessing as mp
import os
import sys
from pathlib import Path

from reqtrace.logging_config import configure_logging

logger = logging.getLogger(__name__)


def _print_gui_unavailable_message(message: str) -> None:
    print(message, file=sys.stderr)


def launch_gui(*, log_level: str | None = None, log_file: str | Path | None = None) -> int:
    """Launch the GUI.

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
        configure_logging(resolved_log_level, log_file=resolved_log_file)
    except (OSError, ValueError) as exc:
        _print_gui_unavailable_message(str(exc))
        return 2

    logger.debug(
        "Launching ReqTrace GUI.",
        extra={
            "log_level": resolved_log_level.upper(),
            "log_file": str(resolved_log_file) if resolved_log_file else None,
        },
    )
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        _print_gui_unavailable_message(
            "ReqTrace GUI cannot start: no $DISPLAY environment variable was found.\n"
            "You're likely running in a headless environment (e.g., a devcontainer).\n\n"
            "Options:\n"
            "- Use the CLI:  reqtrace run ...\n"
            "- Run the GUI on your host machine\n"
            "- Configure GUI forwarding (X11/XWayland) and set $DISPLAY\n"
        )
        return 2

    try:
        import tkinter as tk

        from reqtrace.presentation.gui.controller import ReqTraceGuiController
    except ImportError as exc:
        logger.error("ReqTrace GUI failed to import required GUI modules.", exc_info=exc)
        _print_gui_unavailable_message(
            "ReqTrace GUI cannot start (missing Tkinter runtime).\n"
            f"Details: {exc}\n\n"
            "Install the Tk runtime for your platform, then try again."
        )
        return 2

    try:
        controller = ReqTraceGuiController()
        controller.run()
        logger.info("ReqTrace GUI exited normally.")
        return 0
    except tk.TclError as exc:
        logger.error("ReqTrace GUI failed to start due to Tkinter error.", exc_info=exc)
        _print_gui_unavailable_message(
            "ReqTrace GUI cannot start (Tkinter error).\n"
            f"Details: {exc}\n\n"
            "This typically means the environment has no graphical display.\n"
            "Try running the GUI on a machine with a desktop session or enable display forwarding."
        )
        return 2


def main() -> int:
    return launch_gui()


if __name__ == "__main__":
    raise SystemExit(main())
