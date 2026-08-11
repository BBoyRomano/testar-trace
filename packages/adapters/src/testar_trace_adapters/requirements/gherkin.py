"""Gherkin feature adapter."""

import re
from dataclasses import dataclass

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

__all__ = ["is_gherkin_feature", "parse_gherkin_feature"]


@dataclass(frozen=True, slots=True, kw_only=True)
class _GherkinStep:
    keyword: str
    source_keyword: str
    text: str
    line: int


@dataclass(frozen=True, slots=True, kw_only=True)
class _GherkinScenario:
    title: str
    tags: tuple[str, ...]
    steps: tuple[_GherkinStep, ...]
    line: int
    examples: tuple[tuple[tuple[str, str], ...], ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class _GherkinFeature:
    id: str
    title: str
    tags: tuple[str, ...]
    background: tuple[_GherkinStep, ...]
    scenarios: tuple[_GherkinScenario, ...]


def is_gherkin_feature(source: SourceArtifact) -> bool:
    """Return whether an artifact contains a Gherkin Feature header."""
    return isinstance(source.data, str) and bool(
        re.search(
            r"^\s*Feature\s*:",
            source.data,
            flags=re.IGNORECASE | re.MULTILINE,
        )
    )


def parse_gherkin_feature(source: SourceArtifact) -> RequirementSet:
    """Parse one Gherkin feature into canonical requirements and flows."""
    if not isinstance(source.data, str):
        raise TypeError(f"{source.name} Gherkin input must be text")
    return _map_feature(_parse_feature(source.data, source=source), source=source)


def _parse_feature(text: str, *, source: SourceArtifact) -> _GherkinFeature:
    title: str | None = None
    feature_tags: tuple[str, ...] = ()
    background: list[_GherkinStep] = []
    feature_steps: list[_GherkinStep] = []
    scenarios: list[_GherkinScenario] = []
    pending_tags: tuple[str, ...] = ()
    current_title: str | None = None
    current_tags: tuple[str, ...] = ()
    current_line = 0
    current_steps: list[_GherkinStep] = []
    example_header: tuple[str, ...] = ()
    examples: list[tuple[tuple[str, str], ...]] = []
    section = "feature"
    inherited_keyword: str | None = None

    def finish_scenario() -> None:
        nonlocal current_title, current_steps, examples, example_header
        if current_title is None:
            return
        scenarios.append(
            _GherkinScenario(
                title=current_title,
                tags=current_tags,
                steps=tuple(current_steps),
                line=current_line,
                examples=tuple(examples),
            )
        )
        current_title = None
        current_steps = []
        examples = []
        example_header = ()

    lines = text.splitlines()
    in_doc_string = False
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if line.startswith(('"""', "```")):
            in_doc_string = not in_doc_string
            raise ValueError(
                f"Gherkin doc strings are not supported: {source.name}:{line_number}"
            )
        if in_doc_string or not line or line.startswith("#"):
            continue
        lowered = line.casefold()
        if lowered.startswith("rule:"):
            raise ValueError(
                f"Gherkin Rule blocks are not supported: {source.name}:{line_number}"
            )
        if line.startswith("@"):
            pending_tags = tuple(part.removeprefix("@") for part in line.split())
            continue
        if lowered.startswith("feature:"):
            if title is not None:
                raise ValueError(f"multiple Feature headers in {source.name}")
            title = line.partition(":")[2].strip()
            feature_tags = pending_tags
            pending_tags = ()
            continue
        if lowered.startswith("background:"):
            finish_scenario()
            section = "background"
            inherited_keyword = None
            continue
        if lowered.startswith(("scenario:", "scenario outline:", "scenario template:")):
            finish_scenario()
            current_title = line.partition(":")[2].strip()
            current_tags = (*feature_tags, *pending_tags)
            pending_tags = ()
            current_line = line_number
            section = "scenario"
            inherited_keyword = None
            continue
        if lowered.startswith("examples:"):
            if current_title is None:
                raise ValueError(
                    f"Examples must belong to a scenario: {source.name}:{line_number}"
                )
            section = "examples"
            continue
        if line.startswith("|"):
            if section != "examples":
                raise ValueError(
                    f"Gherkin step tables are not supported: {source.name}:{line_number}"
                )
            cells = _table_cells(line)
            if not example_header:
                example_header = cells
            elif len(cells) != len(example_header):
                raise ValueError(
                    f"Examples row has the wrong number of cells: "
                    f"{source.name}:{line_number}"
                )
            else:
                examples.append(tuple(zip(example_header, cells, strict=True)))
            continue

        parsed = _parse_step(line, line=line_number, inherited=inherited_keyword)
        if parsed is None:
            continue
        inherited_keyword = parsed.keyword
        if section == "background":
            background.append(parsed)
        elif current_title is not None:
            current_steps.append(parsed)
        else:
            feature_steps.append(parsed)

    finish_scenario()
    if title is None or not title:
        raise ValueError(f"Feature file must contain a Feature header: {source.name}")
    if not scenarios and feature_steps:
        scenarios.append(
            _GherkinScenario(
                title=title,
                tags=feature_tags,
                steps=tuple(feature_steps),
                line=1,
            )
        )
    if not scenarios:
        raise ValueError(f"Feature file must contain a scenario: {source.name}")
    return _GherkinFeature(
        id=identifier(title, fallback="gherkin-feature"),
        title=title,
        tags=feature_tags,
        background=tuple(background),
        scenarios=tuple(scenarios),
    )


def _parse_step(
    value: str,
    *,
    line: int,
    inherited: str | None,
) -> _GherkinStep | None:
    match = re.match(r"^(Given|When|Then|And|But|\*)\s+(.+)$", value, re.IGNORECASE)
    if match is None:
        return None
    source_keyword = match.group(1).casefold()
    keyword = inherited if source_keyword in {"and", "but", "*"} else source_keyword
    return _GherkinStep(
        keyword=keyword or "step",
        source_keyword=source_keyword,
        text=match.group(2).strip(),
        line=line,
    )


def _map_feature(
    feature: _GherkinFeature,
    *,
    source: SourceArtifact,
) -> RequirementSet:
    document_id = f"{identifier(source.id)}:document"
    grouped: dict[str, list[_GherkinScenario]] = {}
    titles: dict[str, str] = {}
    for scenario in feature.scenarios:
        requirement_id = _scenario_requirement_id(scenario, feature=feature)
        grouped.setdefault(requirement_id, []).append(scenario)
        titles.setdefault(requirement_id, _requirement_title(scenario.title))

    requirements: list[Requirement] = []
    elements: list[RequirementElement] = []
    flows: list[RequirementFlow] = []
    for requirement_id, scenarios in grouped.items():
        requirements.append(
            Requirement(
                id=requirement_id,
                title=titles[requirement_id],
                document_id=document_id,
                source_ref=source.source_ref(
                    native_id=requirement_id,
                    element_kind="requirement",
                    container_id=document_id,
                ),
                metadata={"source_kind": "gherkin"},
            )
        )
        requirement_elements, requirement_flows = _map_scenarios(
            requirement_id,
            scenarios,
            background=feature.background,
            source=source,
        )
        elements.extend(requirement_elements)
        flows.extend(requirement_flows)

    return RequirementSet(
        documents=(
            RequirementDocument(
                id=document_id,
                title=feature.title,
                source_ref=source.source_ref(),
                metadata={"tags": feature.tags},
            ),
        ),
        requirements=tuple(requirements),
        elements=tuple(elements),
        flows=tuple(flows),
    )


def _map_scenarios(
    requirement_id: str,
    scenarios: list[_GherkinScenario],
    *,
    background: tuple[_GherkinStep, ...],
    source: SourceArtifact,
) -> tuple[tuple[RequirementElement, ...], tuple[RequirementFlow, ...]]:
    elements: list[RequirementElement] = []
    element_ids: dict[tuple[str, str, int], str] = {}
    flows: list[RequirementFlow] = []
    used_flow_ids: set[str] = set()

    for scenario_index, scenario in enumerate(scenarios, start=1):
        rows = scenario.examples or ((),)
        for example_index, row in enumerate(rows, start=1):
            values = dict(row)
            occurrences: dict[tuple[str, str], int] = {}
            scenario_element_ids: list[str] = []
            for step in (*background, *scenario.steps):
                text = _substitute_examples(step.text, values)
                kind = _step_kind(step.keyword, text)
                occurrence_key = (kind, text)
                occurrence = occurrences.get(occurrence_key, 0)
                occurrences[occurrence_key] = occurrence + 1
                signature = (kind, text, occurrence)
                element_id = element_ids.get(signature)
                if element_id is None:
                    element_id = f"{requirement_id}:element:{len(elements) + 1}"
                    element_ids[signature] = element_id
                    elements.append(
                        RequirementElement(
                            id=element_id,
                            requirement_id=requirement_id,
                            text=text,
                            kind=kind,
                            order_index=len(elements),
                            source_ref=source.source_ref(
                                native_id=element_id,
                                element_kind="requirement-element",
                                container_id=requirement_id,
                                location=f"line:{step.line}",
                            ),
                            metadata={"gherkin_keyword": step.source_keyword},
                        )
                    )
                scenario_element_ids.append(element_id)

            if not scenario_element_ids:
                continue
            suffix = identifier(scenario.title, fallback=str(scenario_index))
            if scenario.examples:
                suffix = f"{suffix}-example-{example_index}"
            flow_id = f"{requirement_id}:flow:{suffix}"
            if flow_id in used_flow_ids:
                flow_id = f"{flow_id}-{scenario_index}"
            used_flow_ids.add(flow_id)
            flows.append(
                _scenario_flow(
                    flow_id=flow_id,
                    requirement_id=requirement_id,
                    scenario=scenario,
                    element_ids=tuple(scenario_element_ids),
                    example=values,
                )
            )

    return tuple(elements), tuple(flows)


def _scenario_flow(
    *,
    flow_id: str,
    requirement_id: str,
    scenario: _GherkinScenario,
    element_ids: tuple[str, ...],
    example: dict[str, str],
) -> RequirementFlow:
    branch_id = f"{flow_id}:branch:main"
    nodes = tuple(
        RequirementFlowNode(
            id=f"{flow_id}:node:{index + 1}",
            requirement_id=requirement_id,
            flow_id=flow_id,
            branch_id=branch_id,
            element_id=element_id,
            outcome=(
                RequirementPathOutcome.SUCCESS
                if index == len(element_ids) - 1
                else None
            ),
        )
        for index, element_id in enumerate(element_ids)
    )
    edges = tuple(
        RequirementFlowEdge(
            id=f"{flow_id}:edge:{index}",
            requirement_id=requirement_id,
            flow_id=flow_id,
            source_node_id=nodes[index - 1].id,
            target_node_id=nodes[index].id,
            kind=RequirementFlowEdgeKind.NEXT,
            order_index=index - 1,
        )
        for index in range(1, len(nodes))
    )
    return RequirementFlow(
        id=flow_id,
        requirement_id=requirement_id,
        title=scenario.title,
        entry_node_id=nodes[0].id,
        branches=(
            RequirementFlowBranch(
                id=branch_id,
                requirement_id=requirement_id,
                flow_id=flow_id,
                title=scenario.title,
                kind=RequirementFlowBranchKind.MAIN,
                entry_node_id=nodes[0].id,
                order_index=0,
                metadata={"scenario_kind": _scenario_kind(scenario)},
            ),
        ),
        nodes=nodes,
        edges=edges,
        metadata={
            "source_kind": "gherkin-scenario",
            "scenario_kind": _scenario_kind(scenario),
            "tags": scenario.tags,
            "source_line": scenario.line,
            "example": example,
        },
    )


def _scenario_requirement_id(
    scenario: _GherkinScenario,
    *,
    feature: _GherkinFeature,
) -> str:
    for tag in scenario.tags:
        if re.fullmatch(r"uc[-_.]?\d+", tag, re.IGNORECASE):
            return identifier(tag)
    return identifier(scenario.title, fallback=feature.id)


def _requirement_title(title: str) -> str:
    return re.sub(
        r"\s+-\s+(?:main|alternative(?:\s+.+)?)$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()


def _scenario_kind(scenario: _GherkinScenario) -> str:
    value = " ".join((scenario.title, *scenario.tags)).casefold()
    return "alternative" if "alternative" in value else "main"


def _step_kind(keyword: str, text: str) -> str:
    prefix = text.partition(":")[0].strip().casefold().replace(" ", "_")
    if prefix in {
        "constraint",
        "context",
        "postcondition",
        "precondition",
        "primary_actor",
        "related_information",
        "scope",
        "stakeholder_interest",
        "trigger",
    }:
        return prefix
    return keyword


def _substitute_examples(text: str, values: dict[str, str]) -> str:
    for name, value in values.items():
        text = text.replace(f"<{name}>", value)
    return text


def _table_cells(value: str) -> tuple[str, ...]:
    return tuple(
        cell.strip().replace(r"\|", "|") for cell in value.strip("|").split("|")
    )
