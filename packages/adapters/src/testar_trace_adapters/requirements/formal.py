"""Adapter for the versioned TESTAR Trace formal-requirements format."""

import json
from collections.abc import Mapping
from typing import TypeGuard, cast

from testar_trace.domain.formal_requirements import (
    FormalConformancePolicy,
    FormalElementBinding,
    FormalizationStatus,
    FormalRequirementSet,
    ObservableField,
    ObservableOperator,
    ObservablePredicate,
    ObservableSelector,
    RequirementObservable,
    TraceStartMode,
)
from testar_trace.domain.requirements import (
    Requirement,
    RequirementBranchResolution,
    RequirementDocument,
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
from testar_trace_adapters.source import SourceArtifact

__all__ = ["is_formal_requirements", "parse_formal_requirements"]

_FORMAT_KIND = "testar-trace-formal-requirements"


def is_formal_requirements(source: SourceArtifact) -> bool:
    """Return whether an artifact uses the formal-requirements schema."""
    if source.format != "json":
        return False
    data = _json_mapping_or_none(source.data)
    return data is not None and data.get("kind") == _FORMAT_KIND


def parse_formal_requirements(source: SourceArtifact) -> RequirementSet:
    """Parse a complete formal-requirements artifact into canonical models."""
    data = _json_mapping(source.data, source.name)
    if data.get("kind") != _FORMAT_KIND:
        raise ValueError(f"{source.name} is not a formal-requirements artifact")
    if _integer(data, "schema_version") != 1:
        raise ValueError("formal requirements schema_version must be 1")

    document_id = f"{source.id}:document"
    requirement_values = _mapping_list(data, "requirements")
    requirements: list[Requirement] = []
    elements: list[RequirementElement] = []
    flows: list[RequirementFlow] = []
    for requirement_value in requirement_values:
        requirement_id = _string(requirement_value, "id")
        requirements.append(
            Requirement(
                id=requirement_id,
                title=_string(requirement_value, "title"),
                summary=_optional_string(requirement_value, "summary"),
                body=_optional_string(requirement_value, "body"),
                actor=_optional_string(requirement_value, "actor"),
                scope=_optional_string(requirement_value, "scope"),
                level=_optional_string(requirement_value, "level"),
                document_id=document_id,
                source_ref=source.source_ref(
                    native_id=requirement_id,
                    element_kind="requirement",
                ),
            )
        )
        elements.extend(_parse_elements(requirement_value, requirement_id, source))
        flows.extend(_parse_flows(requirement_value, requirement_id))

    formalization = _parse_formalization(_mapping(data, "formalization"), source)
    return RequirementSet(
        documents=(
            RequirementDocument(
                id=document_id,
                title=_optional_string(data, "title") or source.name,
                source_ref=source.source_ref(element_kind="requirement-document"),
            ),
        ),
        requirements=tuple(requirements),
        elements=tuple(elements),
        flows=tuple(flows),
        formalization=formalization,
        metadata={
            "source_artifact_ids": (source.id,),
            "formal_requirements_schema_version": 1,
        },
    )


def _parse_elements(
    value: Mapping[str, object],
    requirement_id: str,
    source: SourceArtifact,
) -> tuple[RequirementElement, ...]:
    result: list[RequirementElement] = []
    for element in _mapping_list(value, "elements"):
        element_id = _string(element, "id")
        result.append(
            RequirementElement(
                id=element_id,
                requirement_id=requirement_id,
                text=_string(element, "text"),
                kind=_optional_string(element, "kind") or "other",
                order_index=_optional_integer(element, "order_index"),
                source_ref=source.source_ref(
                    native_id=element_id,
                    element_kind="requirement-element",
                    container_id=requirement_id,
                ),
            )
        )
    return tuple(result)


def _parse_flows(
    value: Mapping[str, object], requirement_id: str
) -> tuple[RequirementFlow, ...]:
    result: list[RequirementFlow] = []
    for flow in _mapping_list(value, "flows"):
        flow_id = _string(flow, "id")
        branches = tuple(
            RequirementFlowBranch(
                id=_string(branch, "id"),
                requirement_id=requirement_id,
                flow_id=flow_id,
                title=_string(branch, "title"),
                kind=RequirementFlowBranchKind(_string(branch, "kind")),
                entry_node_id=_string(branch, "entry_node_id"),
                order_index=_optional_integer(branch, "order_index"),
                resolution=RequirementBranchResolution(
                    _optional_string(branch, "resolution") or "explicit"
                ),
            )
            for branch in _mapping_list(flow, "branches")
        )
        nodes = tuple(
            RequirementFlowNode(
                id=_string(node, "id"),
                requirement_id=requirement_id,
                flow_id=flow_id,
                branch_id=_string(node, "branch_id"),
                element_id=_string(node, "element_id"),
                outcome=(
                    RequirementPathOutcome(outcome)
                    if (outcome := _optional_string(node, "outcome")) is not None
                    else None
                ),
            )
            for node in _mapping_list(flow, "nodes")
        )
        edges = tuple(
            RequirementFlowEdge(
                id=_string(edge, "id"),
                requirement_id=requirement_id,
                flow_id=flow_id,
                source_node_id=_string(edge, "source_node_id"),
                target_node_id=_string(edge, "target_node_id"),
                kind=RequirementFlowEdgeKind(_string(edge, "kind")),
                branch_id=_optional_string(edge, "branch_id"),
                order_index=_optional_integer(edge, "order_index"),
            )
            for edge in _mapping_list(flow, "edges", required=False)
        )
        result.append(
            RequirementFlow(
                id=flow_id,
                requirement_id=requirement_id,
                title=_string(flow, "title"),
                entry_node_id=_string(flow, "entry_node_id"),
                branches=branches,
                nodes=nodes,
                edges=edges,
            )
        )
    return tuple(result)


def _parse_formalization(
    value: Mapping[str, object], source: SourceArtifact
) -> FormalRequirementSet:
    observables = tuple(
        RequirementObservable(
            id=_string(observable, "id"),
            requirement_id=_string(observable, "requirement_id"),
            label=_string(observable, "label"),
            selectors=tuple(
                ObservableSelector(
                    predicates=tuple(
                        ObservablePredicate(
                            field=ObservableField(_string(predicate, "field")),
                            operator=ObservableOperator(
                                _optional_string(predicate, "operator") or "equals"
                            ),
                            value=_string(predicate, "value"),
                            case_sensitive=_boolean(
                                predicate,
                                "case_sensitive",
                                default=False,
                            ),
                        )
                        for predicate in _mapping_list(selector, "predicates")
                    )
                )
                for selector in _mapping_list(observable, "selectors")
            ),
            source_ref=source.source_ref(
                native_id=_string(observable, "id"),
                element_kind="formal-observable",
            ),
        )
        for observable in _mapping_list(value, "observables", required=False)
    )
    bindings = tuple(
        FormalElementBinding(
            id=_optional_string(binding, "id")
            or f"binding:{_string(binding, 'requirement_element_id')}",
            requirement_element_id=_string(binding, "requirement_element_id"),
            observable_id=_string(binding, "observable_id"),
            source_ref=source.source_ref(
                native_id=_optional_string(binding, "id")
                or _string(binding, "requirement_element_id"),
                element_kind="formal-binding",
            ),
        )
        for binding in _mapping_list(value, "bindings", required=False)
    )
    policy_value = _mapping(value, "policy", required=False)
    allow_intervening = _boolean(
        policy_value,
        "allow_intervening_transitions",
        default=True,
    )
    policy = FormalConformancePolicy(
        start_mode=TraceStartMode(
            _optional_string(policy_value, "start_mode") or "any-state"
        ),
        allow_intervening_transitions=allow_intervening,
        maximum_intervening_transitions=_integer(
            policy_value, "maximum_intervening_transitions"
        )
        if "maximum_intervening_transitions" in policy_value
        else (12 if allow_intervening else 0),
    )
    return FormalRequirementSet(
        status=FormalizationStatus(_string(value, "status")),
        observables=observables,
        bindings=bindings,
        policy=policy,
        schema_version=1,
        source_ref=source.source_ref(element_kind="formal-requirements"),
    )


def _json_mapping(value: object, name: str) -> Mapping[str, object]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(f"{name} contains invalid JSON") from error
    if not _is_mapping(value):
        raise TypeError(f"{name} must contain a JSON object")
    return value


def _json_mapping_or_none(value: object) -> Mapping[str, object] | None:
    try:
        return _json_mapping(value, "source")
    except (TypeError, ValueError):
        return None


def _mapping(
    value: Mapping[str, object], key: str, *, required: bool = True
) -> Mapping[str, object]:
    item = value.get(key)
    if item is None and not required:
        return {}
    if not _is_mapping(item):
        raise TypeError(f"{key!r} must be an object")
    return item


def _mapping_list(
    value: Mapping[str, object], key: str, *, required: bool = True
) -> tuple[Mapping[str, object], ...]:
    item = value.get(key)
    if item is None and not required:
        return ()
    if not isinstance(item, list) or any(not _is_mapping(entry) for entry in item):
        raise TypeError(f"{key!r} must be a list of objects")
    if required and not item:
        raise ValueError(f"{key!r} must not be empty")
    return tuple(cast(Mapping[str, object], entry) for entry in item)


def _string(value: Mapping[str, object], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{key!r} must be a non-blank string")
    return item.strip()


def _optional_string(value: Mapping[str, object], key: str) -> str | None:
    item = value.get(key)
    if item is None:
        return None
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{key!r} must be a non-blank string or null")
    return item.strip()


def _integer(value: Mapping[str, object], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int):
        raise TypeError(f"{key!r} must be an integer")
    return item


def _optional_integer(value: Mapping[str, object], key: str) -> int | None:
    item = value.get(key)
    if item is None:
        return None
    if isinstance(item, bool) or not isinstance(item, int):
        raise TypeError(f"{key!r} must be an integer or null")
    return item


def _boolean(value: Mapping[str, object], key: str, *, default: bool) -> bool:
    item = value.get(key, default)
    if not isinstance(item, bool):
        raise TypeError(f"{key!r} must be a boolean")
    return item


def _is_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)
