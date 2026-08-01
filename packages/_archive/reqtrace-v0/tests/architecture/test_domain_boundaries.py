from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = PROJECT_ROOT / "src" / "reqtrace" / "domain"
REQTRACE_PREFIX: Final = "reqtrace."
FORBIDDEN_PREFIXES: Final = (
    "reqtrace.ingestion",
    "reqtrace.application",
    "reqtrace_api",
    "reqtrace_cli",
    "reqtrace_desktop",
)


def _resolve_from_module(
    *,
    current_module: str,
    module: str | None,
    level: int,
) -> str:
    if level == 0:
        return module or ""

    package_parts = current_module.split(".")[:-1]
    trim_count = max(level - 1, 0)
    if trim_count > len(package_parts):
        return ""
    base_parts = package_parts[: len(package_parts) - trim_count]
    if module:
        return ".".join([*base_parts, module])
    return ".".join(base_parts)


def _iter_imported_modules(*, node: ast.AST, current_module: str):
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name
        return

    if isinstance(node, ast.ImportFrom):
        resolved = _resolve_from_module(
            current_module=current_module,
            module=node.module,
            level=node.level,
        )
        if resolved:
            yield resolved
        if node.module is None and resolved:
            for alias in node.names:
                yield f"{resolved}.{alias.name}"


def test_domain_layer_has_no_reverse_or_interface_dependencies() -> None:
    violations: list[str] = []

    for path in DOMAIN_ROOT.rglob("*.py"):
        relative = path.relative_to(PROJECT_ROOT)
        current_module = ".".join(
            ("reqtrace", *path.relative_to(PROJECT_ROOT / "src").with_suffix("").parts)
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            for imported_module in _iter_imported_modules(
                node=node,
                current_module=current_module,
            ):
                if imported_module == current_module:
                    continue
                if imported_module.startswith(REQTRACE_PREFIX):
                    if imported_module.startswith("reqtrace.domain"):
                        continue
                if imported_module.startswith(FORBIDDEN_PREFIXES):
                    violations.append(
                        f"{relative}: domain must not import {imported_module}"
                    )

    assert not violations, "\n".join(violations)
