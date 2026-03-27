from __future__ import annotations

from reqtrace.presentation.gui import app as gui_app


def test_launch_gui_returns_headless_exit_code_when_display_missing(monkeypatch, capsys) -> None:
    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)

    exit_code = gui_app.launch_gui()

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "no $DISPLAY environment variable" in captured.err


def test_print_gui_unavailable_message_writes_to_stderr(capsys) -> None:
    gui_app._print_gui_unavailable_message("GUI unavailable")

    captured = capsys.readouterr()
    assert captured.err == "GUI unavailable\n"
