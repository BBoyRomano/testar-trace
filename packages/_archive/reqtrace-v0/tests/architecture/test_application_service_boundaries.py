from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_ROOT = PROJECT_ROOT / "src" / "reqtrace" / "application"
ORCHESTRATION_MODULES = (
    APPLICATION_ROOT / "execution" / "async_executor.py",
    APPLICATION_ROOT / "execution" / "orchestrator.py",
    APPLICATION_ROOT / "history" / "service.py",
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


def test_application_orchestration_modules_do_not_depend_on_ingestion() -> None:
    violations: list[str] = []

    for path in ORCHESTRATION_MODULES:
        relative = path.relative_to(PROJECT_ROOT / "src")
        current_module = ".".join(relative.with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            for imported_module in _iter_imported_modules(
                node=node,
                current_module=current_module,
            ):
                if imported_module.startswith("reqtrace.ingestion"):
                    violations.append(
                        f"{relative}: service depends on ingestion ({imported_module})"
                    )

    assert not violations, "\n".join(violations)
