from __future__ import annotations

import sys
import types

from reqtrace.presentation.gui import app as gui_app


def test_launch_gui_returns_headless_exit_code_when_display_missing(monkeypatch, capsys) -> None:
    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)

    exit_code = gui_app.launch_gui()

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "no $DISPLAY environment variable" in captured.err


def test_launch_gui_prefers_explicit_logging_args_over_env(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def fake_configure_logging(
        level: str = "INFO",
        *,
        force: bool = True,
        log_file: str | None = None,
    ) -> int:
        captured["level"] = level
        captured["log_file"] = log_file
        return 20

    monkeypatch.setattr(gui_app, "configure_logging", fake_configure_logging)
    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("REQTRACE_LOG_LEVEL", "ERROR")
    monkeypatch.setenv("REQTRACE_LOG_FILE", "from-env.log")

    exit_code = gui_app.launch_gui(log_level="DEBUG", log_file="from-arg.log")

    assert exit_code == 2
    assert captured["level"] == "DEBUG"
    assert captured["log_file"] == "from-arg.log"


def test_print_gui_unavailable_message_writes_to_stderr(capsys) -> None:
    gui_app._print_gui_unavailable_message("GUI unavailable")

    captured = capsys.readouterr()
    assert captured.err == "GUI unavailable\n"


def test_launch_gui_reports_missing_tk_runtime_when_display_available(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setitem(sys.modules, "tkinter", None)

    exit_code = gui_app.launch_gui(log_level="INFO")

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "missing Tkinter runtime" in captured.err


def test_launch_gui_reports_tkinter_error_when_controller_raises_tcl_error(
    monkeypatch,
    capsys,
) -> None:
    class FakeTclError(Exception):
        pass

    fake_tk = types.ModuleType("tkinter")
    fake_tk.TclError = FakeTclError

    fake_controller_module = types.ModuleType("reqtrace.presentation.gui.controller")

    class FakeController:
        def run(self) -> None:
            raise FakeTclError("no display")

    fake_controller_module.ReqTraceGuiController = FakeController

    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)
    monkeypatch.setitem(sys.modules, "reqtrace.presentation.gui.controller", fake_controller_module)

    exit_code = gui_app.launch_gui(log_level="INFO")

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Tkinter error" in captured.err
