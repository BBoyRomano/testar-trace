from __future__ import annotations

from pathlib import Path


def test_package_includes_py_typed_marker() -> None:
    marker_path = Path("src/reqtrace/py.typed")
    assert marker_path.is_file()
