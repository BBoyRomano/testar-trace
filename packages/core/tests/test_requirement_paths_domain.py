from testar_trace.domain.requirement_paths import (
    PathMaterializationDiagnosticCode,
    PathMaterializationLimits,
    materialize_requirement_paths,
)
from testar_trace.domain.requirements import (
    Requirement,
    RequirementBranchResolution,
    RequirementElement,
    RequirementFlow,
    RequirementFlowBranch,
    RequirementFlowBranchKind,
    RequirementFlowEdge,
    RequirementFlowEdgeKind,
    RequirementFlowNode,
    RequirementPathOutcome,
    RequirementSet,
)


def test_materializes_main_alternative_terminal_and_rejoined_paths() -> None:
    requirements = _uc04_like_requirement_set()

    result = materialize_requirement_paths(requirements)

    assert result.is_exhaustive
    assert len(result.paths) == 7
    assert {path.outcome for path in result.paths} == {
        RequirementPathOutcome.SUCCESS,
        RequirementPathOutcome.FAILURE,
        RequirementPathOutcome.CANCELLED,
        RequirementPathOutcome.BLOCKED,
    }

    rejoined = next(
        path for path in result.paths if path.branch_ids == ("main", "alt-2a")
    )
    assert rejoined.element_ids == (
        "precondition",
        "trigger",
        "step-1",
        "step-2",
        "select-other-subject",
        "step-3",
        "step-4",
        "step-5",
        "success",
    )
    assert rejoined.resolution is RequirementBranchResolution.EXPLICIT
    assert next(
        path for path in result.paths if path.branch_ids == ("main",)
    ).title == ("Main path")
    assert rejoined.title == "Alternative path 2a"
    assert (
        next(
            path for path in result.paths if path.branch_ids == ("main", "alt-4a")
        ).title
        == "Exception path 4a"
    )


def test_path_ids_are_stable_across_materializations() -> None:
    requirements = _uc04_like_requirement_set()

    first = materialize_requirement_paths(requirements)
    second = materialize_requirement_paths(requirements)

    assert [path.id for path in first.paths] == [path.id for path in second.paths]


def test_reports_unterminated_path_instead_of_treating_it_as_complete() -> None:
    requirements = _single_branch_requirement_set(outcome=None)

    result = materialize_requirement_paths(requirements)

    assert result.paths == ()
    assert not result.is_exhaustive
    assert result.diagnostics[0].code is (
        PathMaterializationDiagnosticCode.UNTERMINATED_PATH
    )


def test_repeat_edges_are_explicitly_bounded() -> None:
    requirement_id = "req-repeat"
    flow_id = "flow-repeat"
    branch_id = "main"
    elements = tuple(
        RequirementElement(
            id=element_id,
            requirement_id=requirement_id,
            text=element_id,
        )
        for element_id in ("one", "two", "done")
    )
    nodes = (
        RequirementFlowNode(
            id="n1",
            requirement_id=requirement_id,
            flow_id=flow_id,
            branch_id=branch_id,
            element_id="one",
        ),
        RequirementFlowNode(
            id="n2",
            requirement_id=requirement_id,
            flow_id=flow_id,
            branch_id=branch_id,
            element_id="two",
        ),
        RequirementFlowNode(
            id="done",
            requirement_id=requirement_id,
            flow_id=flow_id,
            branch_id=branch_id,
            element_id="done",
            outcome=RequirementPathOutcome.SUCCESS,
        ),
    )
    flow = RequirementFlow(
        id=flow_id,
        requirement_id=requirement_id,
        title="Repeat flow",
        entry_node_id="n1",
        branches=(
            RequirementFlowBranch(
                id=branch_id,
                requirement_id=requirement_id,
                flow_id=flow_id,
                title="Main",
                kind=RequirementFlowBranchKind.MAIN,
                entry_node_id="n1",
            ),
        ),
        nodes=nodes,
        edges=(
            _edge(flow_id, requirement_id, "e1", "n1", "n2", order_index=0),
            _edge(flow_id, requirement_id, "exit", "n2", "done", order_index=0),
            _edge(
                flow_id,
                requirement_id,
                "repeat",
                "n2",
                "n1",
                kind=RequirementFlowEdgeKind.REPEAT,
                order_index=1,
            ),
        ),
    )
    requirements = RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Repeat"),),
        elements=elements,
        flows=(flow,),
    )

    result = materialize_requirement_paths(
        requirements,
        limits=PathMaterializationLimits(maximum_visits_per_node=2),
    )

    assert [path.element_ids for path in result.paths] == [
        ("one", "two", "done"),
        ("one", "two", "one", "two", "done"),
    ]
    assert result.bounded
    assert PathMaterializationDiagnosticCode.VISIT_LIMIT_REACHED in {
        diagnostic.code for diagnostic in result.diagnostics
    }


def _single_branch_requirement_set(
    *, outcome: RequirementPathOutcome | None
) -> RequirementSet:
    requirement_id = "req-1"
    flow_id = "flow-1"
    branch_id = "main"
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Requirement"),),
        elements=(
            RequirementElement(
                id="element-1",
                requirement_id=requirement_id,
                text="Element",
            ),
        ),
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Flow",
                entry_node_id="node-1",
                branches=(
                    RequirementFlowBranch(
                        id=branch_id,
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        title="Main",
                        kind=RequirementFlowBranchKind.MAIN,
                        entry_node_id="node-1",
                    ),
                ),
                nodes=(
                    RequirementFlowNode(
                        id="node-1",
                        requirement_id=requirement_id,
                        flow_id=flow_id,
                        branch_id=branch_id,
                        element_id="element-1",
                        outcome=outcome,
                    ),
                ),
            ),
        ),
    )


def _uc04_like_requirement_set() -> RequirementSet:
    requirement_id = "UC-04"
    flow_id = "UC-04:flow"
    element_ids = (
        "precondition",
        "trigger",
        "step-1",
        "step-2",
        "step-3",
        "step-4",
        "step-5",
        "success",
        "empty-table",
        "blocked",
        "select-other-subject",
        "cancel",
        "cancelled",
        "internal-error",
        "failure",
    )
    elements = tuple(
        RequirementElement(
            id=element_id,
            requirement_id=requirement_id,
            text=element_id,
            order_index=index,
        )
        for index, element_id in enumerate(element_ids)
    )
    branches = (
        _branch(flow_id, requirement_id, "main", "Main", "main:pre", 0),
        _branch(flow_id, requirement_id, "alt-1a", "1a empty table", "1a:empty", 1),
        _branch(flow_id, requirement_id, "alt-2a", "2a other subject", "2a:select", 2),
        _branch(flow_id, requirement_id, "alt-3a", "3a cancel", "3a:cancel", 3),
        _branch(
            flow_id,
            requirement_id,
            "alt-4a",
            "4a internal error",
            "4a:error",
            4,
            kind=RequirementFlowBranchKind.EXCEPTION,
        ),
    )
    nodes = (
        _node(flow_id, requirement_id, "main:pre", "main", "precondition"),
        _node(flow_id, requirement_id, "main:trigger", "main", "trigger"),
        _node(flow_id, requirement_id, "main:1", "main", "step-1"),
        _node(flow_id, requirement_id, "main:2", "main", "step-2"),
        _node(flow_id, requirement_id, "main:3", "main", "step-3"),
        _node(flow_id, requirement_id, "main:4", "main", "step-4"),
        _node(flow_id, requirement_id, "main:5", "main", "step-5"),
        _node(
            flow_id,
            requirement_id,
            "main:success",
            "main",
            "success",
            RequirementPathOutcome.SUCCESS,
        ),
        _node(flow_id, requirement_id, "1a:empty", "alt-1a", "empty-table"),
        _node(
            flow_id,
            requirement_id,
            "1a:blocked",
            "alt-1a",
            "blocked",
            RequirementPathOutcome.BLOCKED,
        ),
        _node(
            flow_id,
            requirement_id,
            "2a:select",
            "alt-2a",
            "select-other-subject",
        ),
        _node(flow_id, requirement_id, "3a:cancel", "alt-3a", "cancel"),
        _node(
            flow_id,
            requirement_id,
            "3a:cancelled",
            "alt-3a",
            "cancelled",
            RequirementPathOutcome.CANCELLED,
        ),
        _node(flow_id, requirement_id, "4a:error", "alt-4a", "internal-error"),
        _node(
            flow_id,
            requirement_id,
            "4a:failure",
            "alt-4a",
            "failure",
            RequirementPathOutcome.FAILURE,
        ),
    )
    edges = (
        _edge(flow_id, requirement_id, "m1", "main:pre", "main:trigger"),
        _edge(flow_id, requirement_id, "m2", "main:trigger", "main:1"),
        _edge(flow_id, requirement_id, "m3", "main:1", "main:2", order_index=0),
        _edge(
            flow_id,
            requirement_id,
            "b1a",
            "main:1",
            "1a:empty",
            kind=RequirementFlowEdgeKind.BRANCH,
            branch_id="alt-1a",
            order_index=1,
        ),
        _edge(flow_id, requirement_id, "m4", "main:2", "main:3", order_index=0),
        _edge(
            flow_id,
            requirement_id,
            "b2a",
            "main:2",
            "2a:select",
            kind=RequirementFlowEdgeKind.BRANCH,
            branch_id="alt-2a",
            order_index=1,
        ),
        _edge(flow_id, requirement_id, "m5", "main:3", "main:4", order_index=0),
        _edge(
            flow_id,
            requirement_id,
            "b3a",
            "main:3",
            "3a:cancel",
            kind=RequirementFlowEdgeKind.BRANCH,
            branch_id="alt-3a",
            order_index=1,
        ),
        _edge(flow_id, requirement_id, "m6", "main:4", "main:5", order_index=0),
        _edge(
            flow_id,
            requirement_id,
            "b4a",
            "main:4",
            "4a:error",
            kind=RequirementFlowEdgeKind.BRANCH,
            branch_id="alt-4a",
            order_index=1,
        ),
        _edge(flow_id, requirement_id, "m7", "main:5", "main:success"),
        _edge(flow_id, requirement_id, "1a:end", "1a:empty", "1a:blocked"),
        _edge(
            flow_id,
            requirement_id,
            "2a:rejoin",
            "2a:select",
            "main:3",
            kind=RequirementFlowEdgeKind.REJOIN,
            branch_id="alt-2a",
        ),
        _edge(flow_id, requirement_id, "3a:end", "3a:cancel", "3a:cancelled"),
        _edge(flow_id, requirement_id, "4a:end", "4a:error", "4a:failure"),
    )
    return RequirementSet(
        requirements=(Requirement(id=requirement_id, title="Cancel enrolment"),),
        elements=elements,
        flows=(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title="Cancel enrolment",
                entry_node_id="main:pre",
                branches=branches,
                nodes=nodes,
                edges=edges,
            ),
        ),
    )


def _branch(
    flow_id: str,
    requirement_id: str,
    branch_id: str,
    title: str,
    entry_node_id: str,
    order_index: int,
    *,
    kind: RequirementFlowBranchKind = RequirementFlowBranchKind.ALTERNATIVE,
) -> RequirementFlowBranch:
    if branch_id == "main":
        kind = RequirementFlowBranchKind.MAIN
    return RequirementFlowBranch(
        id=branch_id,
        requirement_id=requirement_id,
        flow_id=flow_id,
        title=title,
        kind=kind,
        entry_node_id=entry_node_id,
        order_index=order_index,
    )


def _node(
    flow_id: str,
    requirement_id: str,
    node_id: str,
    branch_id: str,
    element_id: str,
    outcome: RequirementPathOutcome | None = None,
) -> RequirementFlowNode:
    return RequirementFlowNode(
        id=node_id,
        requirement_id=requirement_id,
        flow_id=flow_id,
        branch_id=branch_id,
        element_id=element_id,
        outcome=outcome,
    )


def _edge(
    flow_id: str,
    requirement_id: str,
    edge_id: str,
    source_node_id: str,
    target_node_id: str,
    *,
    kind: RequirementFlowEdgeKind = RequirementFlowEdgeKind.NEXT,
    branch_id: str | None = None,
    order_index: int | None = None,
) -> RequirementFlowEdge:
    return RequirementFlowEdge(
        id=edge_id,
        requirement_id=requirement_id,
        flow_id=flow_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        kind=kind,
        branch_id=branch_id,
        order_index=order_index,
    )
