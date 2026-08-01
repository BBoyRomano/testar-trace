"""Use-case requirement adapters."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TypeGuard

from reqtrace.models.requirements import (
    RequirementArtifact,
    RequirementDocument,
    RequirementFragment,
    RequirementScenario,
    RequirementSet,
)

from reqtrace_adapters._utils import (
    freeze_metadata,
    slugify,
    source_ref_from_source,
)
from reqtrace_adapters.sources.base import SourceInput

__all__ = [
    "load_use_case_json",
    "load_use_case_markdown",
]


@dataclass(slots=True, frozen=True)
class _UseCaseStep:
    """One ordered step or condition in a use case."""

    text: str
    kind: str
    order_index: int
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("_UseCaseStep.text must not be blank.")
        if not self.kind.strip():
            raise ValueError("_UseCaseStep.kind must not be blank.")
        if self.order_index < 0:
            raise ValueError("_UseCaseStep.order_index must be non-negative.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _UseCaseFlow:
    """A named use-case flow."""

    id: str
    steps: tuple[_UseCaseStep, ...]
    title: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_UseCaseFlow.id must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _UseCase:
    """A parsed use-case requirement before canonical mapping."""

    id: str
    title: str
    summary: str | None = None
    body: str | None = None
    actor: str | None = None
    scope: str | None = None
    level: str | None = None
    constraints: tuple[_UseCaseStep, ...] = ()
    preconditions: tuple[_UseCaseStep, ...] = ()
    triggers: tuple[_UseCaseStep, ...] = ()
    main_flow: tuple[_UseCaseStep, ...] = ()
    alternative_flows: tuple[_UseCaseFlow, ...] = ()
    postconditions: tuple[_UseCaseStep, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_UseCase.id must not be blank.")
        if not self.title.strip():
            raise ValueError("_UseCase.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


@dataclass(slots=True, frozen=True)
class _UseCaseDocument:
    """A parsed source document containing use cases."""

    title: str
    use_cases: tuple[_UseCase, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("_UseCaseDocument.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


def load_use_case_json(source: SourceInput) -> RequirementSet:
    """Load use-case requirements from a JSON object."""
    data = _require_mapping(source.data, context=f"{source.name} JSON")
    document = _parse_use_case_json(data, source=source)
    return _map_use_case_document(document, source=source)


def load_use_case_markdown(source: SourceInput) -> RequirementSet:
    """Load use-case requirements from Markdown text."""
    if not isinstance(source.data, str):
        raise TypeError(f"{source.name} Markdown input must be text.")

    document = _parse_use_case_markdown(source.data, source=source)
    return _map_use_case_document(document, source=source)


def _parse_use_case_json(
    data: Mapping[str, object],
    *,
    source: SourceInput,
) -> _UseCaseDocument:
    document_title = _document_title(data, source)
    entries = _extract_use_case_entries(data) or [data]
    use_cases = tuple(
        _parse_use_case_entry(entry, index=index, source=source)
        for index, entry in enumerate(entries, start=1)
    )
    return _UseCaseDocument(title=document_title, use_cases=use_cases)


def _parse_use_case_markdown(text: str, *, source: SourceInput) -> _UseCaseDocument:
    lines = [line.rstrip() for line in text.splitlines()]
    document_title = _markdown_document_title(lines, source)
    blocks = _markdown_use_case_blocks(lines)

    if blocks:
        return _UseCaseDocument(
            title=document_title,
            use_cases=tuple(
                _parse_markdown_use_case_block(
                    heading=heading,
                    lines=block_lines,
                    index=index,
                    source=source,
                )
                for index, (heading, block_lines) in enumerate(blocks, start=1)
            ),
        )

    title = next(
        (line[2:].strip() for line in lines if line.strip().startswith("# ")),
        None,
    )
    if title is None:
        raise ValueError(
            "Markdown use case must contain a top-level title or use-case "
            f"heading: {source.name}",
        )

    return _UseCaseDocument(
        title=title,
        use_cases=(
            _parse_markdown_use_case_block(
                heading=title,
                lines=lines,
                index=1,
                source=source,
            ),
        ),
    )


def _parse_markdown_use_case_block(
    *,
    heading: str,
    lines: list[str],
    index: int,
    source: SourceInput,
) -> _UseCase:
    heading_id, title = _parse_markdown_use_case_heading(heading)
    fields: dict[str, str] = {"id": heading_id} if heading_id is not None else {}
    section_lines: dict[str, list[str]] = {}
    section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line == "---":
            continue

        bold_heading = _bold_heading(line)
        if bold_heading is not None:
            section = _markdown_use_case_section(bold_heading)
            continue

        if line.startswith("## "):
            section = _markdown_use_case_section(line[3:].strip())
            continue

        if line.startswith("#"):
            continue

        key, value = _split_markdown_field(line)
        if section is None and key is not None and value:
            fields[key] = value
            continue

        if section is not None:
            section_lines.setdefault(section, []).append(line)

    markdown_id = fields.get("id") or fields.get("identifier")
    requirement_id = (
        slugify(markdown_id)
        if markdown_id
        else slugify(title, fallback=f"use-case-{index}")
    )
    actor = _first_text(
        fields.get("actor"),
        fields.get("primary_actor"),
        _section_scalar(section_lines, "primary_actor"),
    )
    return _UseCase(
        id=requirement_id,
        title=title,
        summary=_first_text(
            fields.get("summary"),
            fields.get("description"),
            _section_scalar(section_lines, "context"),
        ),
        actor=actor,
        scope=_first_text(fields.get("scope"), _section_scalar(section_lines, "scope")),
        level=_first_text(fields.get("level"), _section_scalar(section_lines, "level")),
        constraints=_markdown_steps_from_section(section_lines, "constraints"),
        preconditions=_markdown_steps_from_section(section_lines, "preconditions"),
        triggers=_markdown_steps_from_section(section_lines, "trigger"),
        main_flow=_markdown_steps_from_section(section_lines, "main_flow"),
        alternative_flows=_markdown_alternative_flows_from_lines(
            section_lines.get("alternative_flow", []),
        ),
        postconditions=_markdown_steps_from_section(section_lines, "postconditions"),
        metadata={
            **_markdown_metadata(fields),
            **_markdown_section_metadata(section_lines),
            "source_index": index,
            "source_name": source.name,
        },
    )


def _map_use_case_document(
    document: _UseCaseDocument,
    *,
    source: SourceInput,
) -> RequirementSet:
    for use_case in document.use_cases:
        _require_use_case_content(use_case, source=source)

    document_id = f"{slugify(document.title)}-doc"
    requirements = tuple(
        RequirementArtifact(
            id=use_case.id,
            title=use_case.title,
            summary=use_case.summary,
            body=use_case.body,
            actor=use_case.actor,
            scope=use_case.scope,
            level=use_case.level,
            document_id=document_id,
            metadata=use_case.metadata,
        )
        for use_case in document.use_cases
    )
    fragments = tuple(
        fragment
        for use_case in document.use_cases
        for fragment in _map_use_case_fragments(use_case)
    )
    scenarios = tuple(
        scenario
        for use_case in document.use_cases
        for scenario in _map_use_case_scenarios(use_case, fragments)
    )

    return RequirementSet(
        documents=(
            RequirementDocument(
                id=document_id,
                title=document.title,
                source_ref=source_ref_from_source(source),
                metadata=document.metadata,
            ),
        ),
        requirements=requirements,
        fragments=fragments,
        scenarios=scenarios,
        metadata={},
    )


def _require_use_case_content(use_case: _UseCase, *, source: SourceInput) -> None:
    if not any(
        (
            use_case.constraints,
            use_case.preconditions,
            use_case.triggers,
            use_case.main_flow,
            use_case.alternative_flows,
            use_case.postconditions,
        ),
    ):
        raise ValueError(
            f"Use case {use_case.id!r} in {source.name} does not contain "
            "conditions, triggers, flow steps, or postconditions.",
        )


def _markdown_document_title(lines: list[str], source: SourceInput) -> str:
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return _source_stem(source)


def _markdown_use_case_blocks(
    lines: list[str],
) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("## ") and _looks_like_markdown_use_case_heading(
            line[3:].strip(),
        ):
            if current_heading is not None:
                blocks.append((current_heading, current_lines))
            current_heading = line[3:].strip()
            current_lines = []
            continue

        if current_heading is not None:
            current_lines.append(raw_line)

    if current_heading is not None:
        blocks.append((current_heading, current_lines))

    return blocks


def _looks_like_markdown_use_case_heading(heading: str) -> bool:
    use_case_id, _ = _parse_markdown_use_case_heading(heading)
    return use_case_id is not None


def _parse_markdown_use_case_heading(
    heading: str,
) -> tuple[str | None, str]:
    normalized = heading.strip().strip("*")
    match = re.match(
        r"^(?P<id>[A-Za-z]+[.\-]?\d+)\s*(?:[-\u2013\u2014]|â€”)\s*(?P<title>.+)$",
        normalized,
    )
    if match is None:
        return None, normalized

    return match.group("id"), match.group("title").strip()


def _bold_heading(line: str) -> str | None:
    match = re.match(r"^\*\*(.+?)\*\*$", line.strip())
    if match is None:
        return None
    return match.group(1).strip()


def _markdown_use_case_section(heading: str) -> str | None:
    normalized = heading.strip().lower().replace("_", " ").replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).rstrip(":")
    if normalized == "context of use":
        return "context"
    if normalized == "scope":
        return "scope"
    if normalized == "level":
        return "level"
    if normalized == "primary actor":
        return "primary_actor"
    if normalized in {"stakeholders and interests", "stakeholders"}:
        return "stakeholders"
    if normalized in {"constraint", "constraints"}:
        return "constraints"
    if normalized in {"precondition", "preconditions"}:
        return "preconditions"
    if normalized == "trigger":
        return "trigger"
    if normalized in {"main flow", "basic flow", "main success scenario"}:
        return "main_flow"
    if normalized in {
        "alternative flow",
        "alternative flows",
        "alternate flow",
        "alternate flows",
        "exception flow",
        "exception flows",
    }:
        return "alternative_flow"
    if normalized in {"postcondition", "postconditions"}:
        return "postconditions"
    if normalized == "technology and data variations list":
        return "technology_and_data_variations"
    if normalized == "related information":
        return "related_information"
    return None


def _markdown_steps_from_section(
    section_lines: Mapping[str, list[str]],
    section: str,
) -> tuple[_UseCaseStep, ...]:
    steps: list[_UseCaseStep] = []
    for line in section_lines.get(section, []):
        step = _parse_markdown_step(
            line,
            section=section,
            order_index=len(steps) + 1,
        )
        if step is not None:
            steps.append(step)
    return tuple(steps)


def _markdown_alternative_flows_from_lines(
    lines: list[str],
) -> tuple[_UseCaseFlow, ...]:
    flows: list[_UseCaseFlow] = []
    current_label: str | None = None
    current_title: str | None = None
    current_steps: list[_UseCaseStep] = []
    current_postconditions = False

    def finish_flow() -> None:
        if current_label is None or current_title is None:
            return
        flow_id = f"alt-{slugify(current_label, fallback=str(len(flows) + 1))}"
        flows.append(
            _UseCaseFlow(
                id=flow_id,
                title=f"Alternative {current_label}",
                steps=tuple(current_steps),
                metadata=_alternative_flow_metadata(current_label, current_steps),
            ),
        )

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        parsed_heading = _alternative_heading(line)
        if parsed_heading is not None:
            finish_flow()
            current_label, current_title = parsed_heading
            current_postconditions = False
            current_steps = [
                _UseCaseStep(
                    text=current_title,
                    kind="alternative_step",
                    order_index=1,
                    metadata=_alternative_label_metadata(current_label),
                ),
            ]
            continue

        if current_label is None:
            continue

        if line.lower().rstrip(":") == "postconditions":
            current_postconditions = True
            continue

        step = _parse_markdown_step(
            line,
            section="alternative_flow",
            order_index=len(current_steps) + 1,
            force_kind="alternative_postcondition"
            if current_postconditions
            else "alternative_step",
        )
        if step is not None:
            current_steps.append(step)

    finish_flow()
    if not flows and lines:
        return _markdown_alternative_flows(
            list(_markdown_steps_from_lines(lines, section="alternative_flow")),
        )
    return tuple(flows)


def _markdown_steps_from_lines(
    lines: list[str],
    *,
    section: str,
) -> tuple[_UseCaseStep, ...]:
    steps: list[_UseCaseStep] = []
    for line in lines:
        step = _parse_markdown_step(
            line,
            section=section,
            order_index=len(steps) + 1,
        )
        if step is not None:
            steps.append(step)
    return tuple(steps)


def _alternative_heading(line: str) -> tuple[str, str] | None:
    cleaned = re.sub(r"^[-*+]\s*", "", line.strip())
    match = re.match(r"^\*\*(\d+[A-Za-z])\.\s*(.+?)\*\*$", cleaned)
    if match is None:
        return None
    return match.group(1).lower(), match.group(2).strip()


def _alternative_label_metadata(label: str) -> dict[str, object]:
    origin_match = re.match(r"^(\d+)", label)
    return {
        "source_label": label,
        "branch_label": label,
        "branch_origin_step": int(origin_match.group(1))
        if origin_match is not None
        else None,
    }


def _referenced_main_postcondition_indices(values: Iterable[str]) -> tuple[int, ...]:
    indices: set[int] = set()
    for value in values:
        if "main postcondition" not in value.lower():
            continue
        for range_text in re.findall(r"\d+(?:\s*-\s*\d+)?", value):
            start_text, separator, end_text = range_text.partition("-")
            start = int(start_text.strip())
            end = int(end_text.strip()) if separator else start
            lower, upper = sorted((start, end))
            indices.update(range(lower, upper + 1))
    return tuple(sorted(indices))


def _continued_main_step(values: Iterable[str]) -> int | None:
    for value in values:
        lowered = value.lower()
        if "main" not in lowered or "step" not in lowered:
            continue
        if not any(
            marker in lowered for marker in ("continue", "continues", "proceed")
        ):
            continue

        match = re.search(r"\bstep\s+(\d+)\b", lowered)
        if match is not None:
            return int(match.group(1))

    return None


def _parse_markdown_step(
    line: str,
    *,
    section: str,
    order_index: int,
    force_kind: str | None = None,
) -> _UseCaseStep | None:
    cleaned = re.sub(r"^[-*+]\s*", "", line)
    cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned).strip()
    if not cleaned or cleaned.upper() == "N/A":
        return None

    kind = force_kind or _markdown_step_kind(section, cleaned)
    metadata: dict[str, object] = {}
    if kind == "alternative_postcondition":
        cleaned = re.sub(r"^postcondition\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    else:
        source_label, branch_label, origin_step, text = _split_alternative_label(
            cleaned,
        )
        if source_label is not None:
            metadata["source_label"] = source_label
            metadata["branch_label"] = branch_label
            metadata["branch_origin_step"] = origin_step
            cleaned = text

    return _UseCaseStep(
        text=cleaned,
        kind=kind,
        order_index=order_index,
        metadata=metadata,
    )


def _markdown_step_kind(section: str, text: str) -> str:
    if section == "constraints":
        return "constraint"
    if section == "preconditions":
        return "precondition"
    if section == "trigger":
        return "trigger"
    if section == "postconditions":
        return "postcondition"
    if section == "alternative_flow":
        if text.lower().startswith("postcondition:"):
            return "alternative_postcondition"
        return "alternative_step"
    return "main_step"


def _split_alternative_label(
    text: str,
) -> tuple[str | None, str | None, int | None, str]:
    match = re.match(r"^(\d+[A-Za-z](?:-\d+)?)\.\s*(.+)$", text)
    if match is None:
        return None, None, None, text

    source_label = match.group(1)
    branch_label = source_label.split("-", maxsplit=1)[0].lower()
    origin_match = re.match(r"^(\d+)", branch_label)
    origin_step = int(origin_match.group(1)) if origin_match is not None else None
    return source_label, branch_label, origin_step, match.group(2).strip()


def _markdown_alternative_flows(
    steps: list[_UseCaseStep],
) -> tuple[_UseCaseFlow, ...]:
    if not steps:
        return ()

    grouped: dict[str, list[_UseCaseStep]] = {}
    current_branch = "1"
    for step in steps:
        branch_label = step.metadata.get("branch_label")
        if isinstance(branch_label, str) and branch_label:
            current_branch = branch_label
        grouped.setdefault(current_branch, []).append(step)

    flows: list[_UseCaseFlow] = []
    for index, (branch_label, branch_steps) in enumerate(grouped.items(), start=1):
        flow_id = f"alt-{slugify(branch_label, fallback=str(index))}"
        metadata = _alternative_flow_metadata(branch_label, branch_steps)
        flows.append(
            _UseCaseFlow(
                id=flow_id,
                title=f"Alternative {branch_label}",
                steps=tuple(branch_steps),
                metadata=metadata,
            ),
        )
    return tuple(flows)


def _alternative_flow_metadata(
    branch_label: str,
    steps: list[_UseCaseStep],
) -> dict[str, object]:
    origin_steps = [
        step.metadata.get("branch_origin_step")
        for step in steps
        if isinstance(step.metadata.get("branch_origin_step"), int)
    ]
    combined_text = " ".join(step.text.lower() for step in steps)
    postcondition_refs = _referenced_main_postcondition_indices(
        step.text for step in steps
    )
    continues_from_main_step = _continued_main_step(step.text for step in steps)
    return {
        "branch_label": branch_label,
        "branches_from_main_step": min(origin_steps) if origin_steps else None,
        "terminates": "cannot proceed" in combined_text,
        "continues_to_postconditions": "main postcondition" in combined_text,
        "continues_from_main_step": continues_from_main_step,
        "referenced_postcondition_indices": postcondition_refs,
        "path_confidence": "inferred",
    }


def _split_markdown_field(line: str) -> tuple[str | None, str | None]:
    key, separator, value = line.partition(":")
    if not separator:
        return None, None

    normalized_key = key.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized_key not in {
        "id",
        "identifier",
        "actor",
        "primary_actor",
        "summary",
        "description",
        "scope",
        "level",
    }:
        return None, None

    return normalized_key, value.strip()


def _section_scalar(
    section_lines: Mapping[str, list[str]],
    section: str,
) -> str | None:
    values = _section_texts(section_lines.get(section, []))
    if not values:
        return None
    if len(values) == 1 and values[0].upper() == "N/A":
        return None
    return " ".join(values)


def _section_texts(lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        cleaned = re.sub(r"^[-*+]\s*", "", line.strip())
        cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned).strip()
        if cleaned and cleaned.upper() != "N/A":
            values.append(cleaned)
    return values


def _markdown_section_metadata(
    section_lines: Mapping[str, list[str]],
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    for key in (
        "stakeholders",
        "technology_and_data_variations",
        "related_information",
    ):
        values = _section_texts(section_lines.get(key, []))
        if values:
            metadata[key] = tuple(values)
    return metadata


def _first_text(*values: str | None) -> str | None:
    for value in values:
        if value is not None and value.strip():
            return value.strip()
    return None


def _markdown_metadata(fields: Mapping[str, str]) -> dict[str, object]:
    return {
        key: value
        for key, value in fields.items()
        if key not in {"id", "identifier", "actor", "primary_actor"}
    }


def _parse_use_case_entry(
    entry: Mapping[str, object],
    *,
    index: int,
    source: SourceInput,
) -> _UseCase:
    title = _entry_title(entry, index=index, source=source)
    requirement_id = _entry_id(entry, fallback_title=title, index=index)
    step_index = 0

    constraints, step_index = _parse_steps(
        entry.get("Constraints") or entry.get("constraints"),
        kind="constraint",
        start_index=step_index,
    )
    preconditions, step_index = _parse_steps(
        entry.get("Preconditions") or entry.get("preconditions"),
        kind="precondition",
        start_index=step_index,
    )
    triggers, step_index = _parse_steps(
        entry.get("Trigger") or entry.get("trigger") or entry.get("triggers"),
        kind="trigger",
        start_index=step_index,
    )
    main_flow, step_index = _parse_steps(
        entry.get("BasicFlow")
        or entry.get("basic_flow")
        or entry.get("MainFlow")
        or entry.get("mainFlow")
        or entry.get("main_steps")
        or entry.get("main_success_scenario"),
        kind="main_step",
        start_index=step_index,
    )

    alternative_flows: list[_UseCaseFlow] = []
    for alt_index, alt_item in enumerate(
        _alternative_flow_items(
            entry.get("AlternativeFlows")
            or entry.get("alternative_flows")
            or entry.get("alternativeFlows"),
        ),
        start=1,
    ):
        flow, step_index = _parse_alternative_flow_entry(
            alt_item,
            index=alt_index,
            start_index=step_index,
        )
        alternative_flows.append(flow)

    postconditions, _ = _parse_steps(
        entry.get("Postconditions") or entry.get("postconditions"),
        kind="postcondition",
        start_index=step_index,
    )

    return _UseCase(
        id=requirement_id,
        title=title,
        summary=_entry_summary(entry),
        body=_entry_body(entry),
        actor=_entry_actor(entry),
        scope=_entry_scope(entry),
        level=_entry_level(entry),
        constraints=constraints,
        preconditions=preconditions,
        triggers=triggers,
        main_flow=main_flow,
        alternative_flows=tuple(alternative_flows),
        postconditions=postconditions,
        metadata={"source_index": index, **_entry_metadata(entry)},
    )


def _map_use_case_fragments(use_case: _UseCase) -> tuple[RequirementFragment, ...]:
    fragments: list[RequirementFragment] = []
    order_index = 0

    for step in use_case.constraints:
        order_index += 1
        fragments.append(_map_step(use_case, step, order_index=order_index))

    for step in use_case.preconditions:
        order_index += 1
        fragments.append(_map_step(use_case, step, order_index=order_index))

    for step in use_case.triggers:
        order_index += 1
        fragments.append(_map_step(use_case, step, order_index=order_index))

    for step in use_case.main_flow:
        order_index += 1
        fragments.append(_map_step(use_case, step, order_index=order_index))

    for flow in use_case.alternative_flows:
        for step in flow.steps:
            order_index += 1
            fragments.append(
                _map_step(
                    use_case,
                    step,
                    order_index=order_index,
                    branch_id=flow.id,
                ),
            )

    for step in use_case.postconditions:
        order_index += 1
        fragments.append(_map_step(use_case, step, order_index=order_index))

    return tuple(fragments)


def _map_use_case_scenarios(
    use_case: _UseCase,
    fragments: tuple[RequirementFragment, ...],
) -> tuple[RequirementScenario, ...]:
    use_case_fragments = tuple(
        fragment for fragment in fragments if fragment.requirement_id == use_case.id
    )
    global_preconditions = tuple(
        fragment
        for fragment in use_case_fragments
        if fragment.branch_id is None and fragment.kind == "precondition"
    )
    triggers = tuple(
        fragment
        for fragment in use_case_fragments
        if fragment.branch_id is None and fragment.kind == "trigger"
    )
    main_steps = tuple(
        fragment
        for fragment in use_case_fragments
        if fragment.branch_id is None and fragment.kind == "main_step"
    )
    global_postconditions = tuple(
        fragment
        for fragment in use_case_fragments
        if fragment.branch_id is None and fragment.kind == "postcondition"
    )

    scenarios: list[RequirementScenario] = []
    main_fragment_ids = _fragment_ids(
        global_preconditions + triggers + main_steps + global_postconditions,
    )
    if main_fragment_ids:
        scenarios.append(
            RequirementScenario(
                id=f"{use_case.id}:scenario:main",
                requirement_id=use_case.id,
                kind="main",
                title="Main flow",
                fragment_ids=main_fragment_ids,
                order_index=0,
                metadata={"source_kind": "main_flow"},
            ),
        )

    for flow_index, flow in enumerate(use_case.alternative_flows, start=1):
        flow_fragments = tuple(
            fragment for fragment in use_case_fragments if fragment.branch_id == flow.id
        )
        branches_from_step = flow.metadata.get("branches_from_main_step")
        main_prefix = (
            main_steps[:branches_from_step]
            if isinstance(branches_from_step, int)
            else ()
        )
        continues_from_step = flow.metadata.get("continues_from_main_step")
        main_suffix = (
            main_steps[continues_from_step - 1 :]
            if isinstance(continues_from_step, int)
            else ()
        )
        global_tail = _selected_postconditions(
            global_postconditions,
            flow.metadata,
            include_all=bool(main_suffix),
        )
        scenario_fragments = (
            global_preconditions
            + triggers
            + main_prefix
            + flow_fragments
            + main_suffix
            + global_tail
        )
        fragment_ids = _fragment_ids(
            scenario_fragments,
        )
        if not fragment_ids:
            continue

        branch_fragment_id = (
            main_steps[branches_from_step - 1].id
            if isinstance(branches_from_step, int)
            and 0 < branches_from_step <= len(main_steps)
            else None
        )
        metadata = {
            "source_kind": "alternative_flow",
            "branch_id": flow.id,
            **flow.metadata,
        }
        if branch_fragment_id is not None:
            metadata["branches_from"] = branch_fragment_id

        scenarios.append(
            RequirementScenario(
                id=f"{use_case.id}:scenario:{flow.id}",
                requirement_id=use_case.id,
                kind="alternative",
                title=flow.title or flow.id,
                fragment_ids=fragment_ids,
                order_index=flow_index,
                metadata=metadata,
            ),
        )

    return tuple(scenarios)


def _fragment_ids(
    fragments: tuple[RequirementFragment, ...],
) -> tuple[str, ...]:
    fragment_ids: list[str] = []
    seen: set[str] = set()
    for fragment in fragments:
        if fragment.id in seen:
            continue
        fragment_ids.append(fragment.id)
        seen.add(fragment.id)
    return tuple(fragment_ids)


def _selected_postconditions(
    postconditions: tuple[RequirementFragment, ...],
    metadata: Mapping[str, object],
    *,
    include_all: bool = False,
) -> tuple[RequirementFragment, ...]:
    indices = metadata.get("referenced_postcondition_indices")
    if isinstance(indices, tuple) and indices:
        wanted = {index for index in indices if isinstance(index, int)}
        return tuple(
            postcondition
            for index, postcondition in enumerate(postconditions, start=1)
            if index in wanted
        )

    if include_all or metadata.get("continues_to_postconditions") is True:
        return postconditions

    return ()


def _map_step(
    use_case: _UseCase,
    step: _UseCaseStep,
    *,
    order_index: int,
    branch_id: str | None = None,
) -> RequirementFragment:
    return RequirementFragment(
        id=f"{use_case.id}:fragment:{order_index}",
        requirement_id=use_case.id,
        text=step.text,
        kind=step.kind,
        order_index=order_index,
        branch_id=branch_id,
        metadata=step.metadata,
    )


def _parse_steps(
    value: object,
    *,
    kind: str,
    start_index: int,
) -> tuple[tuple[_UseCaseStep, ...], int]:
    steps: list[_UseCaseStep] = []
    order_index = start_index

    for text in _step_texts(value):
        order_index += 1
        steps.append(_UseCaseStep(text=text, kind=kind, order_index=order_index))

    return tuple(steps), order_index


def _parse_alternative_flow_entry(
    value: object,
    *,
    index: int,
    start_index: int,
) -> tuple[_UseCaseFlow, int]:
    flow_id = f"alt-{index}"
    title: str | None = None
    metadata: dict[str, object] = {"path_confidence": "structured"}

    if _is_object_dict(value):
        flow_id = _alternative_flow_id(value, fallback=flow_id)
        title = _alternative_flow_title(value)
        metadata.update(_alternative_flow_object_metadata(value, title=title))
        step_value = value.get("steps") or value.get("Steps") or value.get("flow")
        postcondition_value = value.get("postconditions") or value.get("Postconditions")
    else:
        step_value = value
        postcondition_value = None

    steps: list[_UseCaseStep] = []
    order_index = start_index
    if title is not None:
        order_index += 1
        steps.append(
            _UseCaseStep(
                text=title,
                kind="alternative_step",
                order_index=order_index,
                metadata=metadata,
            ),
        )

    parsed_steps, order_index = _parse_steps(
        step_value,
        kind="alternative_step",
        start_index=order_index,
    )
    steps.extend(parsed_steps)

    parsed_postconditions, order_index = _parse_steps(
        postcondition_value,
        kind="alternative_postcondition",
        start_index=order_index,
    )
    steps.extend(parsed_postconditions)

    return (
        _UseCaseFlow(
            id=flow_id,
            title=f"Alternative {metadata.get('branch_label') or index}",
            steps=tuple(steps),
            metadata=metadata,
        ),
        order_index,
    )


def _alternative_flow_id(value: Mapping[str, object], *, fallback: str) -> str:
    for key in ("id", "ID", "Id", "key", "Key"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            branch_label = _alternative_branch_label(candidate)
            if branch_label is not None:
                return f"alt-{slugify(branch_label)}"
            return f"alt-{slugify(candidate)}"
    return fallback


def _alternative_flow_title(value: Mapping[str, object]) -> str | None:
    for key in ("title", "Title", "name", "Name", "description", "Description"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return _strip_alternative_title_label(candidate.strip())
    return None


def _strip_alternative_title_label(value: str) -> str:
    return re.sub(r"^\s*\d+[A-Za-z]\.\s*", "", value).strip()


def _alternative_flow_object_metadata(
    value: Mapping[str, object],
    *,
    title: str | None,
) -> dict[str, object]:
    label = _alternative_branch_label(title or "") or _alternative_branch_label(
        str(value.get("id") or ""),
    )
    metadata: dict[str, object] = {}
    if label is not None:
        metadata.update(_alternative_label_metadata(label))
        branch_origin_step = metadata.get("branch_origin_step")
        if isinstance(branch_origin_step, int):
            metadata["branches_from_main_step"] = branch_origin_step
    combined_values = [
        title or "",
        *_step_texts(value.get("steps") or value.get("Steps")),
        *_step_texts(value.get("postconditions") or value.get("Postconditions")),
    ]
    combined_text = " ".join(combined_values).lower()
    metadata["terminates"] = "cannot proceed" in combined_text
    metadata["continues_to_postconditions"] = "main postcondition" in combined_text
    metadata["continues_from_main_step"] = _continued_main_step(combined_values)
    metadata["referenced_postcondition_indices"] = (
        _referenced_main_postcondition_indices(combined_values)
    )
    return metadata


def _alternative_branch_label(value: str) -> str | None:
    match = re.search(r"\b(\d+[A-Za-z])\b", value)
    if match is None:
        return None
    return match.group(1).lower()


def _document_title(data: Mapping[str, object], source: SourceInput) -> str:
    for key in ("title", "name", "Name", "document_title", "DocumentTitle"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return _source_stem(source)


def _extract_use_case_entries(data: Mapping[str, object]) -> list[dict[str, object]]:
    collection_keys = (
        "use_cases",
        "useCases",
        "UseCases",
        "cases",
        "Cases",
        "requirements",
        "Requirements",
        "items",
        "Items",
    )

    for key in collection_keys:
        entries = _coerce_entry_list(data.get(key))
        if entries:
            return entries

    return [
        value
        for value in data.values()
        if _is_object_dict(value) and _looks_like_use_case(value)
    ]


def _coerce_entry_list(value: object) -> list[dict[str, object]]:
    if isinstance(value, list):
        return [item for item in value if _is_object_dict(item)]
    if _is_object_dict(value):
        return [item for item in value.values() if _is_object_dict(item)]
    return []


def _looks_like_use_case(value: Mapping[str, object]) -> bool:
    return any(
        key in value
        for key in (
            "BasicFlow",
            "basic_flow",
            "MainFlow",
            "mainFlow",
            "main_steps",
            "main_success_scenario",
            "context_of_use",
            "AlternativeFlows",
            "alternative_flows",
            "alternativeFlows",
            "Preconditions",
            "preconditions",
            "primary_actor",
            "Actors",
            "actor",
            "Actor",
        )
    )


def _entry_title(
    entry: Mapping[str, object],
    *,
    index: int,
    source: SourceInput,
) -> str:
    for key in (
        "title",
        "name",
        "Name",
        "use_case",
        "useCase",
        "UseCase",
        "Summary",
        "summary",
        "Id",
        "ID",
        "id",
    ):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"{_source_stem(source)}-{index}"


def _entry_id(entry: Mapping[str, object], *, fallback_title: str, index: int) -> str:
    for key in ("id", "ID", "Id", "key", "Key", "identifier", "Identifier"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return slugify(value)

    for key in ("number", "Number", "code", "Code"):
        value = entry.get(key)
        if value is not None and str(value).strip():
            return slugify(str(value))

    slug = slugify(fallback_title, fallback="")
    return slug or f"use-case-{index}"


def _entry_summary(entry: Mapping[str, object]) -> str | None:
    for key in (
        "summary",
        "Summary",
        "description",
        "Description",
        "goal",
        "Goal",
        "brief",
        "Brief",
        "context_of_use",
        "ContextOfUse",
    ):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _entry_body(entry: Mapping[str, object]) -> str | None:
    for key in ("body", "Body", "details", "Details", "text", "Text"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _entry_actor(entry: Mapping[str, object]) -> str | None:
    for key in ("actor", "Actor", "primary_actor", "PrimaryActor", "primaryActor"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    actors = entry.get("Actors")
    if isinstance(actors, list):
        values = [str(item).strip() for item in actors if str(item).strip()]
        return ", ".join(values) or None

    if isinstance(actors, str) and actors.strip():
        return actors.strip()

    return None


def _entry_scope(entry: Mapping[str, object]) -> str | None:
    for key in ("scope", "Scope"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _entry_level(entry: Mapping[str, object]) -> str | None:
    for key in ("level", "Level"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _entry_metadata(entry: Mapping[str, object]) -> dict[str, object]:
    ignored = {
        "id",
        "ID",
        "Id",
        "key",
        "Key",
        "identifier",
        "Identifier",
        "number",
        "Number",
        "code",
        "Code",
        "title",
        "name",
        "Name",
        "use_case",
        "useCase",
        "UseCase",
        "summary",
        "Summary",
        "description",
        "Description",
        "goal",
        "Goal",
        "brief",
        "Brief",
        "body",
        "Body",
        "details",
        "Details",
        "text",
        "Text",
        "actor",
        "Actor",
        "primary_actor",
        "PrimaryActor",
        "primaryActor",
        "Actors",
        "scope",
        "Scope",
        "level",
        "Level",
        "constraints",
        "Constraints",
        "trigger",
        "Trigger",
        "triggers",
        "Preconditions",
        "preconditions",
        "BasicFlow",
        "basic_flow",
        "MainFlow",
        "mainFlow",
        "main_steps",
        "main_success_scenario",
        "AlternativeFlows",
        "alternative_flows",
        "alternativeFlows",
        "Postconditions",
        "postconditions",
    }
    return {key: value for key, value in entry.items() if key not in ignored}


def _alternative_flow_items(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    return [value]


def _step_texts(value: object) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []

    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_step_texts(item))
        return items

    if _is_object_dict(value):
        for key in (
            "steps",
            "Steps",
            "flow",
            "Flow",
            "items",
            "Items",
            "BasicFlow",
            "basic_flow",
            "MainFlow",
            "mainFlow",
        ):
            nested_items = _step_texts(value.get(key))
            if nested_items:
                return nested_items

        for key in (
            "text",
            "Text",
            "step",
            "Step",
            "description",
            "Description",
            "name",
            "Name",
            "title",
            "Title",
        ):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return [nested.strip()]

        return [
            item.strip()
            for item in value.values()
            if isinstance(item, str) and item.strip()
        ]

    text = str(value).strip()
    return [text] if text else []


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _require_mapping(value: object, *, context: str) -> dict[str, object]:
    if not _is_object_dict(value):
        raise TypeError(f"{context} must be an object with string keys.")
    return value


def _source_stem(source: SourceInput) -> str:
    return source.name.rsplit(".", maxsplit=1)[0] or source.name
