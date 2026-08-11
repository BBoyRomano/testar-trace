import ast
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("source_root", "forbidden_roots"),
    [
        (
            REPOSITORY_ROOT / "packages/core/src",
            {"testar_trace_adapters", "testar_trace_cli"},
        ),
        (
            REPOSITORY_ROOT / "packages/adapters/src",
            {"testar_trace_cli"},
        ),
    ],
)
def test_package_dependency_direction(
    source_root: Path,
    forbidden_roots: set[str],
) -> None:
    violations: list[str] = []
    for source_path in sorted(source_root.rglob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=source_path)
        for node in ast.walk(tree):
            imported = _imported_roots(node)
            forbidden = sorted(imported & forbidden_roots)
            if forbidden:
                relative = source_path.relative_to(REPOSITORY_ROOT)
                line = getattr(node, "lineno", 0)
                violations.append(f"{relative}:{line}: {', '.join(forbidden)}")

    assert violations == []


def _imported_roots(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Import):
        return {alias.name.partition(".")[0] for alias in node.names}
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return {node.module.partition(".")[0]}
    return set()
