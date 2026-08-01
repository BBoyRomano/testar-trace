from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "reqtrace"
REQTRACE_PREFIX: Final = "reqtrace."
PUBLIC_MODULE_IMPORT_PREFIXES = {
    "__init__.py": (
        "reqtrace.analysis",
        "reqtrace.io",
        "reqtrace.contracts",
        "reqtrace.errors",
    ),
    "analysis.py": (
        "reqtrace._api_types",
        "reqtrace.application.execution.runner",
        "reqtrace.contracts",
        "reqtrace.errors",
    ),
    "io.py": (
        "reqtrace._paths",
        "reqtrace.contracts",
        "reqtrace.errors",
    ),
    "contracts.py": (
        "reqtrace._paths",
        "reqtrace._api_types",
        "reqtrace.application.progress",
        "reqtrace.application.results",
    ),
    "errors.py": (),
    "formats.py": (
        "reqtrace._paths",
        "reqtrace._api_types",
        "reqtrace.errors",
        "reqtrace.ingestion.exceptions",
        "reqtrace.ingestion.input_resolution",
    ),
}


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


def test_root_public_modules_only_import_allowed_internal_dependencies() -> None:
    violations: list[str] = []

    for filename, allowed_prefixes in PUBLIC_MODULE_IMPORT_PREFIXES.items():
        path = PACKAGE_ROOT / filename
        current_module = ".".join(
            ("reqtrace", *path.relative_to(PACKAGE_ROOT).with_suffix("").parts)
        )
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            for imported_module in _iter_imported_modules(
                node=node,
                current_module=current_module,
            ):
                if not imported_module.startswith(REQTRACE_PREFIX):
                    continue
                if imported_module == current_module:
                    continue
                if any(
                    imported_module.startswith(prefix)
                    for prefix in allowed_prefixes
                ):
                    continue
                violations.append(
                    f"{filename}: disallowed internal dependency {imported_module}"
                )

    assert not violations, "\n".join(violations)

