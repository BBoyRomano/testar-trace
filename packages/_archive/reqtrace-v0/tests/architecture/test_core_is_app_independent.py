from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "src" / "reqtrace"
FORBIDDEN_TOP_LEVEL_IMPORTS = {
    "reqtrace_api",
    "reqtrace_cli",
    "reqtrace_desktop",
}


def _iter_imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.ImportFrom):
        if node.module:
            return [node.module]
        return []
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    return []


def test_core_package_does_not_depend_on_interface_apps() -> None:
    violations: list[str] = []
    for path in CORE_ROOT.rglob("*.py"):
        relative = path.relative_to(PROJECT_ROOT)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module in _iter_imported_modules(node):
                top_level = module.split(".")[0]
                if top_level in FORBIDDEN_TOP_LEVEL_IMPORTS:
                    violations.append(
                        f"{relative}: forbidden dependency on {top_level}"
                    )

    assert not violations, "\n".join(violations)
