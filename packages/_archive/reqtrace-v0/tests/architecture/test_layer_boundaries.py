from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "reqtrace"
LAYER_NAMES = {"domain", "ingestion", "application"}
FORBIDDEN_IMPORTS_BY_LAYER = {
    "domain": {"ingestion", "application"},
    "ingestion": {"application"},
    "application": set(),
}
REQTRACE_PREFIX: Final = "reqtrace."


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


def _iter_imported_layers(*, node: ast.AST, current_module: str):
    for module in _iter_imported_modules(node=node, current_module=current_module):
        if not module.startswith(REQTRACE_PREFIX):
            continue
        parts = module.split(".")
        if len(parts) > 1:
            yield parts[1]


def test_layer_dependencies_follow_architecture_boundaries() -> None:
    violations: list[str] = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        relative = path.relative_to(PACKAGE_ROOT)
        source_layer = relative.parts[0] if relative.parts else ""
        if source_layer not in LAYER_NAMES:
            continue
        current_module = ".".join(("reqtrace", *relative.with_suffix("").parts))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden_targets = FORBIDDEN_IMPORTS_BY_LAYER[source_layer]
        for node in ast.walk(tree):
            for target_layer in _iter_imported_layers(
                node=node,
                current_module=current_module,
            ):
                if target_layer not in LAYER_NAMES:
                    continue
                if target_layer in forbidden_targets:
                    violations.append(
                        f"{relative}: {source_layer} must not import {target_layer}"
                    )

    assert not violations, "\n".join(violations)
