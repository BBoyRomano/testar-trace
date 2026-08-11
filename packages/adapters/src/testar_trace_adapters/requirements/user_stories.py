"""User-story JSON adapter."""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TypeGuard

from testar_trace.domain.requirements import (
    Requirement,
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
from testar_trace_adapters._identifiers import identifier
from testar_trace_adapters.source import SourceArtifact

__all__ = ["is_user_story_source", "parse_user_stories"]


@dataclass(slots=True, frozen=True)
class _AcceptanceCriterion:
    id: str
    title: str
    kind: str
    statements: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class _UserStory:
    id: str
    title: str
    role: str | None = None
    goal: str | None = None
    benefit: str | None = None
    rules: tuple[tuple[str, str], ...] = ()
    criteria: tuple[_AcceptanceCriterion, ...] = ()
    location: str = "story"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.title.strip():
            raise ValueError("User-story id and title must not be blank.")
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def summary(self) -> str | None:
        parts = []
        if self.role:
            parts.append(f"As a {self.role}")
        if self.goal:
            parts.append(f"I want {self.goal}")
        if self.benefit:
            parts.append(f"so that {self.benefit}")
        return ", ".join(parts) or None


def is_user_story_source(source: SourceArtifact) -> bool:
    """Return whether an artifact resembles user-story JSON."""
    if source.format != "json":
        return False
    data = _json_mapping_or_none(source.data)
    return data is not None and (
        "user_stories" in data
        or "stories" in data
        or any(key in data for key in ("as_a", "role", "i_want", "goal"))
    )


def parse_user_stories(source: SourceArtifact) -> RequirementSet:
    """Parse one or more user stories from JSON."""
    data = _json_mapping(source)
    raw_stories = data.get("user_stories", data.get("stories"))
    if raw_stories is None:
        story_values = (data,)
        document_title = _story_title(data, source)
    else:
        story_values = tuple(_require_list(raw_stories, "user_stories"))
        document_title = _optional_text(data.get("title")) or _source_stem(source)

    stories = tuple(
        _parse_story(
            _require_mapping(value, context=f"user_stories[{index}]"),
            source=source,
            location=f"user_stories[{index}]",
        )
        for index, value in enumerate(story_values)
    )
    return _map_stories(document_title, stories, source=source)


def _parse_story(
    data: Mapping[str, object],
    *,
    source: SourceArtifact,
    location: str,
) -> _UserStory:
    title = _story_title(data, source)
    return _UserStory(
        id=_story_id(data, fallback_title=title),
        title=title,
        role=_first_text(data, "role", "Role", "AsA", "as_a"),
        goal=_first_text(data, "goal", "Goal", "IWant", "i_want"),
        benefit=_first_text(data, "benefit", "Benefit", "SoThat", "so_that"),
        rules=_parse_rules(data.get("rules", []), context=f"{location}.rules"),
        criteria=_parse_criteria(
            data.get("acceptance_criteria", []),
            context=f"{location}.acceptance_criteria",
        ),
        location=location,
        metadata=_story_metadata(data),
    )


def _map_stories(
    document_title: str,
    stories: tuple[_UserStory, ...],
    *,
    source: SourceArtifact,
) -> RequirementSet:
    document_id = f"{identifier(source.id)}:document"
    requirements: list[Requirement] = []
    elements: list[RequirementElement] = []
    flows: list[RequirementFlow] = []

    for story in stories:
        requirements.append(
            Requirement(
                id=story.id,
                title=story.title,
                summary=story.summary,
                actor=story.role,
                scope=_metadata_text(story.metadata, "scope"),
                level=_metadata_text(story.metadata, "level"),
                document_id=document_id,
                source_ref=source.source_ref(
                    native_id=story.id,
                    element_kind="requirement",
                    container_id=document_id,
                    location=story.location,
                ),
                metadata=story.metadata,
            ),
        )
        story_elements, flow = _map_story_content(story, source=source)
        elements.extend(story_elements)
        flows.append(flow)

    return RequirementSet(
        documents=(
            RequirementDocument(
                id=document_id,
                title=document_title,
                source_ref=source.source_ref(),
            ),
        ),
        requirements=tuple(requirements),
        elements=tuple(elements),
        flows=tuple(flows),
    )


def _map_story_content(
    story: _UserStory,
    *,
    source: SourceArtifact,
) -> tuple[tuple[RequirementElement, ...], RequirementFlow]:
    elements: list[RequirementElement] = []

    def add(text: str, kind: str, *, branch_id: str | None = None) -> str:
        element_id = f"{story.id}:element:{len(elements) + 1}"
        metadata = {"branch_id": branch_id} if branch_id is not None else {}
        elements.append(
            RequirementElement(
                id=element_id,
                requirement_id=story.id,
                text=text,
                kind=kind,
                order_index=len(elements),
                source_ref=source.source_ref(
                    native_id=element_id,
                    element_kind="requirement-element",
                    container_id=story.id,
                    location=f"{story.location}.element[{len(elements)}]",
                ),
                metadata=metadata,
            ),
        )
        return element_id

    common_ids: list[str] = []
    if story.role:
        common_ids.append(add(f"As a {story.role}", "role"))
    if story.goal:
        common_ids.append(add(story.goal, "goal"))
    if story.benefit:
        common_ids.append(add(story.benefit, "benefit"))
    for kind, text in story.rules:
        if text not in {"---", "N/A"}:
            common_ids.append(add(text, kind))

    main_ids: list[str] = []
    alternative_criteria: list[_AcceptanceCriterion] = []
    for criterion in story.criteria:
        if criterion.kind == "alternative":
            alternative_criteria.append(criterion)
            continue
        target = (
            common_ids if criterion.kind in {"precondition", "trigger"} else main_ids
        )
        kind = "main_step" if criterion.kind == "main" else criterion.kind
        target.extend(add(statement, kind) for statement in criterion.statements)

    if not common_ids and not main_ids:
        main_ids.append(add(story.title, "summary"))

    alternative_values: list[tuple[str, int, tuple[str, ...]]] = []
    for criterion in alternative_criteria:
        for label, statements in _alternative_branches(criterion):
            branch_id = f"alt-{identifier(label)}"
            origin = _branch_origin(label)
            branch_element_ids = tuple(
                add(text, kind, branch_id=branch_id) for kind, text in statements
            )
            alternative_values.append((branch_id, origin, branch_element_ids))

    flow = _story_flow(
        story,
        main_element_ids=(*common_ids, *main_ids),
        main_step_ids=tuple(main_ids),
        alternatives=tuple(alternative_values),
    )
    return tuple(elements), flow


def _story_flow(
    story: _UserStory,
    *,
    main_element_ids: tuple[str, ...],
    main_step_ids: tuple[str, ...],
    alternatives: tuple[tuple[str, int, tuple[str, ...]], ...],
) -> RequirementFlow:
    flow_id = f"{story.id}:flow"
    main_branch_id = f"{flow_id}:branch:main"
    nodes: list[RequirementFlowNode] = []
    edges: list[RequirementFlowEdge] = []
    branches: list[RequirementFlowBranch] = []
    main_nodes_by_element: dict[str, str] = {}

    for index, element_id in enumerate(main_element_ids):
        node_id = f"{flow_id}:node:main:{index + 1}"
        main_nodes_by_element[element_id] = node_id
        nodes.append(
            RequirementFlowNode(
                id=node_id,
                requirement_id=story.id,
                flow_id=flow_id,
                branch_id=main_branch_id,
                element_id=element_id,
                outcome=(
                    RequirementPathOutcome.SUCCESS
                    if index == len(main_element_ids) - 1
                    else None
                ),
            )
        )
        if index:
            edges.append(
                RequirementFlowEdge(
                    id=f"{flow_id}:edge:main:{index}",
                    requirement_id=story.id,
                    flow_id=flow_id,
                    source_node_id=nodes[index - 1].id,
                    target_node_id=node_id,
                    kind=RequirementFlowEdgeKind.NEXT,
                    order_index=len(edges),
                )
            )

    branches.append(
        RequirementFlowBranch(
            id=main_branch_id,
            requirement_id=story.id,
            flow_id=flow_id,
            title="Main flow",
            kind=RequirementFlowBranchKind.MAIN,
            entry_node_id=nodes[0].id,
            order_index=0,
        )
    )

    for branch_index, (short_id, origin, element_ids) in enumerate(
        alternatives,
        start=1,
    ):
        if not element_ids:
            continue
        branch_id = f"{flow_id}:branch:{short_id}"
        branch_node_ids: list[str] = []
        for element_index, element_id in enumerate(element_ids):
            node_id = f"{flow_id}:node:{short_id}:{element_index + 1}"
            branch_node_ids.append(node_id)
            nodes.append(
                RequirementFlowNode(
                    id=node_id,
                    requirement_id=story.id,
                    flow_id=flow_id,
                    branch_id=branch_id,
                    element_id=element_id,
                    outcome=(
                        RequirementPathOutcome.OTHER
                        if element_index == len(element_ids) - 1
                        else None
                    ),
                )
            )
            if element_index:
                edges.append(
                    RequirementFlowEdge(
                        id=f"{flow_id}:edge:{short_id}:{element_index}",
                        requirement_id=story.id,
                        flow_id=flow_id,
                        source_node_id=branch_node_ids[element_index - 1],
                        target_node_id=node_id,
                        kind=RequirementFlowEdgeKind.NEXT,
                        order_index=len(edges),
                    )
                )

        source_element_id = (
            main_step_ids[origin - 1]
            if 0 < origin <= len(main_step_ids)
            else main_element_ids[0]
        )
        branches.append(
            RequirementFlowBranch(
                id=branch_id,
                requirement_id=story.id,
                flow_id=flow_id,
                title=f"Alternative flow {short_id.removeprefix('alt-')}",
                kind=RequirementFlowBranchKind.ALTERNATIVE,
                entry_node_id=branch_node_ids[0],
                order_index=branch_index,
                metadata={"branch_origin_step": origin},
            )
        )
        edges.append(
            RequirementFlowEdge(
                id=f"{flow_id}:edge:branch:{short_id}",
                requirement_id=story.id,
                flow_id=flow_id,
                source_node_id=main_nodes_by_element[source_element_id],
                target_node_id=branch_node_ids[0],
                kind=RequirementFlowEdgeKind.BRANCH,
                branch_id=branch_id,
                order_index=len(edges),
            )
        )

    return RequirementFlow(
        id=flow_id,
        requirement_id=story.id,
        title=story.title,
        entry_node_id=nodes[0].id,
        branches=tuple(branches),
        nodes=tuple(nodes),
        edges=tuple(edges),
        metadata={"source_kind": "user-story"},
    )


def _alternative_branches(
    criterion: _AcceptanceCriterion,
) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
    branches: list[tuple[str, tuple[tuple[str, str], ...]]] = []
    label = criterion.id
    statements: list[tuple[str, str]] = []
    postconditions = False

    def finish() -> None:
        if statements:
            branches.append((label, tuple(statements)))

    for statement in criterion.statements:
        heading = re.match(r"^\*\*(\d+[A-Za-z])\.\s*(.+?)\*\*$", statement)
        if heading is not None:
            finish()
            label = heading.group(1).lower()
            statements = [("alternative_step", heading.group(2).strip())]
            postconditions = False
            continue
        if statement.lower().rstrip(":") == "postconditions":
            postconditions = True
            continue
        statements.append(
            (
                "alternative_postcondition" if postconditions else "alternative_step",
                statement,
            ),
        )
    finish()
    return tuple(branches)


def _branch_origin(label: str) -> int:
    match = re.match(r"(\d+)", label)
    return int(match.group(1)) if match is not None else 0


def _parse_rules(value: object, *, context: str) -> tuple[tuple[str, str], ...]:
    rules: list[tuple[str, str]] = []
    for index, item in enumerate(_require_list(value, context)):
        rule = _require_mapping(item, context=f"{context}[{index}]")
        text = _optional_text(rule.get("text"))
        if text is not None:
            rules.append((_optional_text(rule.get("kind")) or "rule", text))
    return tuple(rules)


def _parse_criteria(
    value: object,
    *,
    context: str,
) -> tuple[_AcceptanceCriterion, ...]:
    criteria: list[_AcceptanceCriterion] = []
    for index, item in enumerate(_require_list(value, context)):
        criterion = _require_mapping(item, context=f"{context}[{index}]")
        statements = tuple(
            text
            for raw in _require_list(
                criterion.get("statements", []),
                f"{context}[{index}].statements",
            )
            if (text := _optional_text(raw)) is not None
        )
        criteria.append(
            _AcceptanceCriterion(
                id=_optional_text(criterion.get("id")) or f"criterion-{index + 1}",
                title=_optional_text(criterion.get("title"))
                or f"Criterion {index + 1}",
                kind=(_optional_text(criterion.get("type")) or "criterion").lower(),
                statements=statements,
            ),
        )
    return tuple(criteria)


def _story_title(data: Mapping[str, object], source: SourceArtifact) -> str:
    return _first_text(
        data, "title", "name", "Name", "summary", "Summary"
    ) or _source_stem(source)


def _story_id(data: Mapping[str, object], *, fallback_title: str) -> str:
    value = _first_text(
        data, "id", "ID", "Id", "key", "Key", "identifier", "Identifier"
    )
    return identifier(value or fallback_title, fallback="user-story")


def _first_text(data: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = _optional_text(data.get(key))
        if value is not None:
            return value
    return None


def _metadata_text(metadata: Mapping[str, object], key: str) -> str | None:
    return _optional_text(metadata.get(key))


def _optional_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _story_metadata(data: Mapping[str, object]) -> dict[str, object]:
    parsed = {
        "acceptance_criteria",
        "as_a",
        "benefit",
        "Benefit",
        "goal",
        "Goal",
        "id",
        "ID",
        "Id",
        "IWant",
        "i_want",
        "key",
        "Key",
        "name",
        "Name",
        "role",
        "Role",
        "rules",
        "SoThat",
        "so_that",
        "summary",
        "Summary",
        "title",
    }
    return {key: value for key, value in data.items() if key not in parsed}


def _require_list(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{context} must be a list.")
    return list(value)


def _require_mapping(value: object, *, context: str) -> dict[str, object]:
    if not _is_object_dict(value):
        raise TypeError(f"{context} must be an object with string keys.")
    return value


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _json_mapping(source: SourceArtifact) -> dict[str, object]:
    value = source.data
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON in {source.name}: {error}") from error
    return _require_mapping(value, context=f"{source.name} JSON")


def _json_mapping_or_none(value: object) -> dict[str, object] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if _is_object_dict(value) else None


def _freeze_metadata(
    value: Mapping[str, object],
) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


def _source_stem(source: SourceArtifact) -> str:
    return source.name.rsplit(".", maxsplit=1)[0] or source.name
