"""Canonical requirement models and authored behaviour-flow graphs."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from testar_trace.domain._metadata import freeze_metadata
from testar_trace.domain._validation import (
    require_ids,
    require_known,
    require_non_negative_int,
    require_optional_text,
    require_text,
    unique_ids,
)
from testar_trace.domain.formal_requirements import FormalRequirementSet
from testar_trace.domain.provenance import SourceRef

__all__ = [
    "Requirement",
    "RequirementBranchResolution",
    "RequirementDocument",
    "RequirementElement",
    "RequirementFlow",
    "RequirementFlowBranch",
    "RequirementFlowBranchKind",
    "RequirementFlowEdge",
    "RequirementFlowEdgeKind",
    "RequirementFlowNode",
    "RequirementPath",
    "RequirementPathOutcome",
    "RequirementSet",
]


class RequirementFlowBranchKind(StrEnum):
    """Authored role of a branch in a requirement flow."""

    MAIN = "main"
    ALTERNATIVE = "alternative"
    EXCEPTION = "exception"


class RequirementBranchResolution(StrEnum):
    """Certainty with which a branch was attached to the canonical graph."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    AMBIGUOUS = "ambiguous"


class RequirementFlowEdgeKind(StrEnum):
    """Structural role of an edge in a requirement flow."""

    NEXT = "next"
    BRANCH = "branch"
    REJOIN = "rejoin"
    REPEAT = "repeat"


class RequirementPathOutcome(StrEnum):
    """Outcome reached at the terminal node of a requirement path."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    OTHER = "other"


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementDocument:
    """Source document containing one or more requirements."""

    id: str
    title: str
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.title, "title")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class Requirement:
    """Canonical software requirement."""

    id: str
    title: str
    summary: str | None = None
    body: str | None = None
    actor: str | None = None
    scope: str | None = None
    level: str | None = None
    document_id: str | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.title, "title")
        require_optional_text(self.summary, "summary")
        require_optional_text(self.body, "body")
        require_optional_text(self.actor, "actor")
        require_optional_text(self.scope, "scope")
        require_optional_text(self.level, "level")
        require_optional_text(self.document_id, "document_id")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementElement:
    """Semantic and independently traceable part of a requirement."""

    id: str
    requirement_id: str
    text: str
    kind: str = "other"
    order_index: int | None = None
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.text, "text")
        require_text(self.kind, "kind")
        require_non_negative_int(self.order_index, "order_index")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementFlowBranch:
    """Named authored branch within a requirement-flow graph."""

    id: str
    requirement_id: str
    flow_id: str
    title: str
    kind: RequirementFlowBranchKind
    entry_node_id: str
    order_index: int | None = None
    resolution: RequirementBranchResolution = RequirementBranchResolution.EXPLICIT
    source_ref: SourceRef | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.flow_id, "flow_id")
        require_text(self.title, "title")
        require_text(self.entry_node_id, "entry_node_id")
        require_non_negative_int(self.order_index, "order_index")
        _require_enum(self.kind, RequirementFlowBranchKind, "kind")
        _require_enum(self.resolution, RequirementBranchResolution, "resolution")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementFlowNode:
    """One occurrence of a requirement element in a flow graph."""

    id: str
    requirement_id: str
    flow_id: str
    branch_id: str
    element_id: str
    outcome: RequirementPathOutcome | None = None

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.flow_id, "flow_id")
        require_text(self.branch_id, "branch_id")
        require_text(self.element_id, "element_id")
        if self.outcome is not None:
            _require_enum(self.outcome, RequirementPathOutcome, "outcome")


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementFlowEdge:
    """Directed relationship between two requirement-flow nodes."""

    id: str
    requirement_id: str
    flow_id: str
    source_node_id: str
    target_node_id: str
    kind: RequirementFlowEdgeKind
    branch_id: str | None = None
    order_index: int | None = None

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.flow_id, "flow_id")
        require_text(self.source_node_id, "source_node_id")
        require_text(self.target_node_id, "target_node_id")
        require_optional_text(self.branch_id, "branch_id")
        require_non_negative_int(self.order_index, "order_index")
        _require_enum(self.kind, RequirementFlowEdgeKind, "kind")


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementPath:
    """Complete independently assessable route derived from a flow graph."""

    id: str
    requirement_id: str
    flow_id: str
    title: str
    branch_ids: tuple[str, ...]
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    element_ids: tuple[str, ...]
    outcome: RequirementPathOutcome
    order_index: int
    resolution: RequirementBranchResolution
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.flow_id, "flow_id")
        require_text(self.title, "title")
        require_ids(self.branch_ids, "branch_ids", unique=True)
        require_ids(self.node_ids, "node_ids")
        require_ids(self.edge_ids, "edge_ids", allow_empty=True)
        require_ids(self.element_ids, "element_ids")
        require_non_negative_int(self.order_index, "order_index")
        _require_enum(self.outcome, RequirementPathOutcome, "outcome")
        _require_enum(self.resolution, RequirementBranchResolution, "resolution")

        if len(self.element_ids) != len(self.node_ids):
            raise ValueError(
                "element_ids and node_ids must contain the same number of items"
            )
        if len(self.edge_ids) != len(self.node_ids) - 1:
            raise ValueError("edge_ids must connect each consecutive pair of nodes")

        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementFlow:
    """Canonical authored branching graph for one requirement."""

    id: str
    requirement_id: str
    title: str
    entry_node_id: str
    branches: tuple[RequirementFlowBranch, ...]
    nodes: tuple[RequirementFlowNode, ...]
    edges: tuple[RequirementFlowEdge, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_text(self.id, "id")
        require_text(self.requirement_id, "requirement_id")
        require_text(self.title, "title")
        require_text(self.entry_node_id, "entry_node_id")

        if not self.branches:
            raise ValueError("branches must not be empty")
        if not self.nodes:
            raise ValueError("nodes must not be empty")

        branch_ids = unique_ids(self.branches, "RequirementFlowBranch")
        node_ids = unique_ids(self.nodes, "RequirementFlowNode")
        unique_ids(self.edges, "RequirementFlowEdge")
        require_known((self.entry_node_id,), node_ids, "entry_node_id")

        main_branches = tuple(
            branch
            for branch in self.branches
            if branch.kind is RequirementFlowBranchKind.MAIN
        )
        if len(main_branches) != 1:
            raise ValueError("a flow must contain exactly one main branch")
        if main_branches[0].entry_node_id != self.entry_node_id:
            raise ValueError("the main branch must start at the flow entry node")

        nodes_by_id = {node.id: node for node in self.nodes}

        for branch in self.branches:
            _require_flow_owner(branch, self.id, self.requirement_id)
            require_known(
                (branch.entry_node_id,), node_ids, "RequirementFlowBranch.entry_node_id"
            )
            if nodes_by_id[branch.entry_node_id].branch_id != branch.id:
                raise ValueError("a branch entry node must belong to that branch")

        for node in self.nodes:
            _require_flow_owner(node, self.id, self.requirement_id)
            require_known(
                (node.branch_id,), branch_ids, "RequirementFlowNode.branch_id"
            )

        outgoing_node_ids: set[str] = set()
        for edge in self.edges:
            _require_flow_owner(edge, self.id, self.requirement_id)
            require_known(
                (edge.source_node_id,), node_ids, "RequirementFlowEdge.source_node_id"
            )
            require_known(
                (edge.target_node_id,), node_ids, "RequirementFlowEdge.target_node_id"
            )
            if edge.branch_id is not None:
                require_known(
                    (edge.branch_id,), branch_ids, "RequirementFlowEdge.branch_id"
                )
            _validate_edge_branch_semantics(edge, nodes_by_id)
            outgoing_node_ids.add(edge.source_node_id)

        for node in self.nodes:
            if node.outcome is not None and node.id in outgoing_node_ids:
                raise ValueError(
                    "a terminal node with an outcome must not have outgoing edges"
                )

        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(frozen=True, slots=True, kw_only=True)
class RequirementSet:
    """Complete canonical requirement input for analysis."""

    requirements: tuple[Requirement, ...]
    documents: tuple[RequirementDocument, ...] = ()
    elements: tuple[RequirementElement, ...] = ()
    flows: tuple[RequirementFlow, ...] = ()
    formalization: FormalRequirementSet | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.requirements:
            raise ValueError("requirements must not be empty")

        document_ids = unique_ids(self.documents, "RequirementDocument")
        requirement_ids = unique_ids(self.requirements, "Requirement")
        unique_ids(self.elements, "RequirementElement")
        unique_ids(self.flows, "RequirementFlow")

        element_ids_by_requirement = {
            requirement_id: set() for requirement_id in requirement_ids
        }

        for requirement in self.requirements:
            if requirement.document_id is not None:
                require_known(
                    (requirement.document_id,),
                    document_ids,
                    "Requirement.document_id",
                )

        for element in self.elements:
            require_known(
                (element.requirement_id,),
                requirement_ids,
                "RequirementElement.requirement_id",
            )
            element_ids_by_requirement[element.requirement_id].add(element.id)

        for flow in self.flows:
            require_known(
                (flow.requirement_id,),
                requirement_ids,
                "RequirementFlow.requirement_id",
            )
            local_element_ids = element_ids_by_requirement[flow.requirement_id]
            for node in flow.nodes:
                require_known(
                    (node.element_id,),
                    local_element_ids,
                    "RequirementFlowNode.element_id",
                )

        if self.formalization is not None:
            if not isinstance(self.formalization, FormalRequirementSet):
                raise TypeError("formalization must be a FormalRequirementSet or None")
            observable_ids = unique_ids(
                self.formalization.observables,
                "RequirementObservable",
            )
            elements_by_id = {element.id: element for element in self.elements}
            observables_by_id = {
                observable.id: observable
                for observable in self.formalization.observables
            }
            for observable in self.formalization.observables:
                require_known(
                    (observable.requirement_id,),
                    requirement_ids,
                    "RequirementObservable.requirement_id",
                )
            for binding in self.formalization.bindings:
                require_known(
                    (binding.requirement_element_id,),
                    elements_by_id,
                    "FormalElementBinding.requirement_element_id",
                )
                require_known(
                    (binding.observable_id,),
                    observable_ids,
                    "FormalElementBinding.observable_id",
                )
                element = elements_by_id[binding.requirement_element_id]
                observable = observables_by_id[binding.observable_id]
                if element.requirement_id != observable.requirement_id:
                    raise ValueError(
                        "a formal binding and observable must belong to the same "
                        "requirement"
                    )

        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def elements_for(self, requirement_id: str) -> tuple[RequirementElement, ...]:
        """Return elements belonging to a requirement."""
        return tuple(
            element
            for element in self.elements
            if element.requirement_id == requirement_id
        )

    def flows_for(self, requirement_id: str) -> tuple[RequirementFlow, ...]:
        """Return flows belonging to a requirement."""
        return tuple(
            flow for flow in self.flows if flow.requirement_id == requirement_id
        )


def _require_enum(value: object, enum_type: type[StrEnum], field_name: str) -> None:
    if not isinstance(value, enum_type):
        raise TypeError(f"{field_name} must be a {enum_type.__name__}")


def _require_flow_owner(
    item: RequirementFlowBranch | RequirementFlowNode | RequirementFlowEdge,
    flow_id: str,
    requirement_id: str,
) -> None:
    if item.flow_id != flow_id:
        raise ValueError(f"{type(item).__name__}.flow_id must match its flow")
    if item.requirement_id != requirement_id:
        raise ValueError(
            f"{type(item).__name__}.requirement_id must match its flow's requirement"
        )


def _validate_edge_branch_semantics(
    edge: RequirementFlowEdge,
    nodes_by_id: Mapping[str, RequirementFlowNode],
) -> None:
    source_branch_id = nodes_by_id[edge.source_node_id].branch_id
    target_branch_id = nodes_by_id[edge.target_node_id].branch_id

    if edge.kind in (RequirementFlowEdgeKind.NEXT, RequirementFlowEdgeKind.REPEAT):
        if source_branch_id != target_branch_id:
            raise ValueError("next and repeat edges must remain within one branch")
        if edge.branch_id is not None:
            raise ValueError("next and repeat edges must not declare branch_id")
        return

    if source_branch_id == target_branch_id:
        raise ValueError("branch and rejoin edges must cross branch boundaries")

    expected_branch_id = (
        target_branch_id
        if edge.kind is RequirementFlowEdgeKind.BRANCH
        else source_branch_id
    )
    if edge.branch_id != expected_branch_id:
        relation = "target" if edge.kind is RequirementFlowEdgeKind.BRANCH else "source"
        raise ValueError(
            f"{edge.kind.value} edge branch_id must identify its {relation} branch"
        )
