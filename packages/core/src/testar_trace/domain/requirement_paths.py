"""Deterministic, bounded materialization of complete requirement paths."""

import re
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from testar_trace.domain._validation import require_non_negative_int, require_text
from testar_trace.domain.requirements import (
    RequirementBranchResolution,
    RequirementFlow,
    RequirementFlowBranch,
    RequirementFlowBranchKind,
    RequirementFlowEdge,
    RequirementFlowEdgeKind,
    RequirementFlowNode,
    RequirementPath,
    RequirementSet,
)

__all__ = [
    "PathMaterializationDiagnostic",
    "PathMaterializationDiagnosticCode",
    "PathMaterializationLimits",
    "PathMaterializationResult",
    "materialize_requirement_paths",
]


class PathMaterializationDiagnosticCode(StrEnum):
    """Reason why a flow could not be materialized without qualification."""

    UNTERMINATED_PATH = "unterminated-path"
    UNMARKED_CYCLE = "unmarked-cycle"
    UNREACHABLE_BRANCH = "unreachable-branch"
    UNREACHABLE_NODE = "unreachable-node"
    PATH_LIMIT_REACHED = "path-limit-reached"
    NODE_LIMIT_REACHED = "node-limit-reached"
    VISIT_LIMIT_REACHED = "visit-limit-reached"


_BOUND_CODES = {
    PathMaterializationDiagnosticCode.PATH_LIMIT_REACHED,
    PathMaterializationDiagnosticCode.NODE_LIMIT_REACHED,
    PathMaterializationDiagnosticCode.VISIT_LIMIT_REACHED,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class PathMaterializationLimits:
    """Safety bounds for finite traversal of authored flow graphs."""

    maximum_paths_per_flow: int = 256
    maximum_nodes_per_path: int = 512
    maximum_visits_per_node: int = 1

    def __post_init__(self) -> None:
        for field_name in (
            "maximum_paths_per_flow",
            "maximum_nodes_per_path",
            "maximum_visits_per_node",
        ):
            value = getattr(self, field_name)
            require_non_negative_int(value, field_name)
            if value == 0:
                raise ValueError(f"{field_name} must be greater than zero")


@dataclass(frozen=True, slots=True, kw_only=True)
class PathMaterializationDiagnostic:
    """A structural or safety issue encountered while resolving a flow."""

    code: PathMaterializationDiagnosticCode
    flow_id: str
    message: str
    node_id: str | None = None
    edge_id: str | None = None

    def __post_init__(self) -> None:
        require_text(self.flow_id, "flow_id")
        require_text(self.message, "message")
        if self.node_id is not None:
            require_text(self.node_id, "node_id")
        if self.edge_id is not None:
            require_text(self.edge_id, "edge_id")
        if not isinstance(self.code, PathMaterializationDiagnosticCode):
            raise TypeError("code must be a PathMaterializationDiagnosticCode")


@dataclass(frozen=True, slots=True, kw_only=True)
class PathMaterializationResult:
    """Requirement paths together with explicit traversal qualifications."""

    paths: tuple[RequirementPath, ...]
    bounded: bool
    diagnostics: tuple[PathMaterializationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.bounded, bool):
            raise TypeError("bounded must be a bool")
        if self.bounded != any(
            diagnostic.code in _BOUND_CODES for diagnostic in self.diagnostics
        ):
            raise ValueError("bounded must reflect the materialization diagnostics")

    @property
    def is_exhaustive(self) -> bool:
        """Whether every graph route was resolved without qualifications."""
        return not self.bounded and not self.diagnostics


def materialize_requirement_paths(
    requirements: RequirementSet,
    *,
    limits: PathMaterializationLimits | None = None,
) -> PathMaterializationResult:
    """Resolve every complete path in requirement and flow order."""
    if not isinstance(requirements, RequirementSet):
        raise TypeError("requirements must be a RequirementSet")

    traversal_limits = PathMaterializationLimits() if limits is None else limits
    if not isinstance(traversal_limits, PathMaterializationLimits):
        raise TypeError("limits must be a PathMaterializationLimits")

    paths: list[RequirementPath] = []
    diagnostics: list[PathMaterializationDiagnostic] = []

    for flow in requirements.flows:
        flow_paths, flow_diagnostics = _materialize_flow(flow, traversal_limits)
        paths.extend(flow_paths)
        diagnostics.extend(flow_diagnostics)

    return PathMaterializationResult(
        paths=tuple(paths),
        bounded=any(item.code in _BOUND_CODES for item in diagnostics),
        diagnostics=tuple(diagnostics),
    )


def _materialize_flow(
    flow: RequirementFlow,
    limits: PathMaterializationLimits,
) -> tuple[list[RequirementPath], list[PathMaterializationDiagnostic]]:
    nodes_by_id = {node.id: node for node in flow.nodes}
    branches_by_id = {branch.id: branch for branch in flow.branches}
    outgoing: dict[str, list[RequirementFlowEdge]] = {
        node.id: [] for node in flow.nodes
    }
    for edge in flow.edges:
        outgoing[edge.source_node_id].append(edge)
    for edges in outgoing.values():
        edges.sort(key=_edge_order)

    paths: list[RequirementPath] = []
    diagnostics: list[PathMaterializationDiagnostic] = []
    diagnostic_keys: set[tuple[object, ...]] = set()
    visited_node_ids: set[str] = set()
    visited_branch_ids: set[str] = set()

    def diagnose(
        code: PathMaterializationDiagnosticCode,
        message: str,
        *,
        node_id: str | None = None,
        edge_id: str | None = None,
    ) -> None:
        key = (code, node_id, edge_id)
        if key in diagnostic_keys:
            return
        diagnostic_keys.add(key)
        diagnostics.append(
            PathMaterializationDiagnostic(
                code=code,
                flow_id=flow.id,
                message=message,
                node_id=node_id,
                edge_id=edge_id,
            )
        )

    def walk(
        node_ids: tuple[str, ...],
        edge_ids: tuple[str, ...],
        visit_counts: Counter[str],
        repeating: bool,
    ) -> None:
        node = nodes_by_id[node_ids[-1]]
        visited_node_ids.add(node.id)
        visited_branch_ids.add(node.branch_id)

        if node.outcome is not None:
            if len(paths) >= limits.maximum_paths_per_flow:
                diagnose(
                    PathMaterializationDiagnosticCode.PATH_LIMIT_REACHED,
                    f"flow exceeded {limits.maximum_paths_per_flow} complete paths",
                    node_id=node.id,
                )
                return
            paths.append(
                _make_path(
                    flow,
                    nodes_by_id,
                    branches_by_id,
                    node_ids,
                    edge_ids,
                    len(paths),
                )
            )
            return

        if len(node_ids) >= limits.maximum_nodes_per_path:
            diagnose(
                PathMaterializationDiagnosticCode.NODE_LIMIT_REACHED,
                f"path exceeded {limits.maximum_nodes_per_path} nodes",
                node_id=node.id,
            )
            return

        next_edges = outgoing[node.id]
        if not next_edges:
            diagnose(
                PathMaterializationDiagnosticCode.UNTERMINATED_PATH,
                "path ended at a node without an explicit outcome",
                node_id=node.id,
            )
            return

        for edge in next_edges:
            if len(paths) >= limits.maximum_paths_per_flow:
                diagnose(
                    PathMaterializationDiagnosticCode.PATH_LIMIT_REACHED,
                    f"flow exceeded {limits.maximum_paths_per_flow} complete paths",
                    edge_id=edge.id,
                )
                return

            target_id = edge.target_node_id
            target_visits = visit_counts[target_id]
            if target_visits:
                if edge.kind is not RequirementFlowEdgeKind.REPEAT and not repeating:
                    diagnose(
                        PathMaterializationDiagnosticCode.UNMARKED_CYCLE,
                        "a cycle must be entered through an explicit repeat edge",
                        edge_id=edge.id,
                    )
                    continue
                if target_visits >= limits.maximum_visits_per_node:
                    diagnose(
                        PathMaterializationDiagnosticCode.VISIT_LIMIT_REACHED,
                        f"node exceeded {limits.maximum_visits_per_node} visits",
                        node_id=target_id,
                        edge_id=edge.id,
                    )
                    continue

            next_counts = visit_counts.copy()
            next_counts[target_id] += 1
            walk(
                (*node_ids, target_id),
                (*edge_ids, edge.id),
                next_counts,
                repeating or edge.kind is RequirementFlowEdgeKind.REPEAT,
            )

    entry_id = flow.entry_node_id
    walk((entry_id,), (), Counter({entry_id: 1}), False)

    bounded = any(item.code in _BOUND_CODES for item in diagnostics)
    if not bounded:
        for branch in sorted(flow.branches, key=_branch_order):
            if branch.id not in visited_branch_ids:
                diagnose(
                    PathMaterializationDiagnosticCode.UNREACHABLE_BRANCH,
                    f"branch {branch.id!r} is unreachable from the flow entry",
                    node_id=branch.entry_node_id,
                )
        for node in flow.nodes:
            if node.id not in visited_node_ids:
                diagnose(
                    PathMaterializationDiagnosticCode.UNREACHABLE_NODE,
                    f"node {node.id!r} is unreachable from the flow entry",
                    node_id=node.id,
                )

    return paths, diagnostics


def _make_path(
    flow: RequirementFlow,
    nodes_by_id: dict[str, RequirementFlowNode],
    branches_by_id: dict[str, RequirementFlowBranch],
    node_ids: tuple[str, ...],
    edge_ids: tuple[str, ...],
    order_index: int,
) -> RequirementPath:
    nodes = tuple(nodes_by_id[node_id] for node_id in node_ids)
    branch_ids = tuple(dict.fromkeys(node.branch_id for node in nodes))
    branches = tuple(branches_by_id[branch_id] for branch_id in branch_ids)
    terminal = nodes[-1]
    assert terminal.outcome is not None

    signature = "\x1f".join(edge_ids) if edge_ids else f"node:{node_ids[0]}"
    digest = sha256(signature.encode("utf-8")).hexdigest()[:16]
    title = _path_title(branches)
    resolution = max(
        (branch.resolution for branch in branches),
        key=_resolution_rank,
    )

    return RequirementPath(
        id=f"{flow.id}:path:{digest}",
        requirement_id=flow.requirement_id,
        flow_id=flow.id,
        title=title,
        branch_ids=branch_ids,
        node_ids=node_ids,
        edge_ids=edge_ids,
        element_ids=tuple(node.element_id for node in nodes),
        outcome=terminal.outcome,
        order_index=order_index,
        resolution=resolution,
        metadata={"terminal_node_id": terminal.id},
    )


def _edge_order(edge: RequirementFlowEdge) -> tuple[bool, int, str]:
    return (edge.order_index is None, edge.order_index or 0, edge.id)


def _path_title(branches: tuple[RequirementFlowBranch, ...]) -> str:
    non_main = tuple(
        branch
        for branch in branches
        if branch.kind is not RequirementFlowBranchKind.MAIN
    )
    if not non_main:
        return "Main path"
    kind = (
        RequirementFlowBranchKind.EXCEPTION
        if any(
            branch.kind is RequirementFlowBranchKind.EXCEPTION for branch in non_main
        )
        else RequirementFlowBranchKind.ALTERNATIVE
    )
    labels = tuple(
        label
        for branch in non_main
        if (label := _path_branch_label(branch)) is not None
    )
    prefix = f"{kind.value.title()} path"
    if not labels:
        return prefix
    separator = (
        " "
        if all(
            re.fullmatch(r"\d+[a-z](?:-\d+)?", label, re.IGNORECASE) for label in labels
        )
        else ": "
    )
    return f"{prefix}{separator}{' + '.join(labels)}"


def _path_branch_label(branch: RequirementFlowBranch) -> str | None:
    source_label = branch.metadata.get("branch_label")
    if isinstance(source_label, str) and source_label.strip():
        return source_label.strip()
    label = re.sub(
        r"^(?:alternative|exception)(?:\s+flow|\s+scenario|\s+path)?\s*[:.-]?\s*",
        "",
        branch.title,
        flags=re.IGNORECASE,
    ).strip()
    leading_code = re.match(r"(?P<code>\d+[a-z](?:-\d+)?)\b", label, re.IGNORECASE)
    if leading_code is not None:
        return leading_code.group("code")
    return label or None


def _branch_order(branch: RequirementFlowBranch) -> tuple[bool, int, str]:
    return (
        branch.order_index is None,
        branch.order_index or 0,
        branch.id,
    )


def _resolution_rank(resolution: RequirementBranchResolution) -> int:
    return {
        RequirementBranchResolution.EXPLICIT: 0,
        RequirementBranchResolution.INFERRED: 1,
        RequirementBranchResolution.AMBIGUOUS: 2,
    }[resolution]
