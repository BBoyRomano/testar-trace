from __future__ import annotations

import re

from reqtrace.domain.requirements import (
    Requirement,
    RequirementCatalog,
    RequirementKind,
    RequirementUnit,
    RequirementUnitKind,
)


SECTION_NAMES = {
    "Context of Use": "context_of_use",
    "Scope": "scope",
    "Level": "level",
    "Primary Actor": "primary_actor",
    "Stakeholders and Interests": "stakeholders_and_interests",
    "Constraints": "constraints",
    "Preconditions": "preconditions",
    "Trigger": "trigger",
    "Main Success Scenario": "main_success_scenario",
    "Postconditions": "postconditions",
    "Alternative Flows": "alternative_flows",
    "Technology and Data Variations List": "technology_and_data_variations",
    "Related Information": "related_information",
}


USE_CASE_HEADER_RE = re.compile(r"^##\s+(UC\.\d+)\s+—\s+(.+)$", re.MULTILINE)
ALT_FLOW_TITLE_RE = re.compile(r"^- \*\*(.+?)\*\*$")
NUMBERED_ITEM_RE = re.compile(r"^\d+\.\s+(.*)$")
NESTED_ITEM_RE = re.compile(r"^\s*-\s+\d+[a-zA-Z-]*\.\s+(.*)$")
BULLET_ITEM_RE = re.compile(r"^- (.*)$")


def _slice_use_case_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(USE_CASE_HEADER_RE.finditer(text))
    blocks: list[tuple[str, str, str]] = []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + \
            1 < len(matches) else len(text)
        use_case_id = match.group(1)
        title = match.group(2).strip()
        body = text[start:end].strip()
        blocks.append((use_case_id, title, body))

    return blocks


def _parse_section_map(body: str) -> dict[str, str]:
    lines = body.splitlines()
    section_map: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("**") and stripped.endswith("**"):
            section_title = stripped.removeprefix("**").removesuffix("**")
            if section_title in SECTION_NAMES:
                current_section = SECTION_NAMES[section_title]
                section_map.setdefault(current_section, [])
                continue

        if current_section is not None:
            section_map[current_section].append(line)

    return {
        key: "\n".join(value).strip()
        for key, value in section_map.items()
    }


def _parse_numbered_list(section_text: str) -> list[str]:
    items: list[str] = []

    for line in section_text.splitlines():
        stripped = line.strip()
        match = NUMBERED_ITEM_RE.match(stripped)
        if match:
            items.append(match.group(1).strip())

    return items


def _parse_bullet_list(section_text: str) -> list[str]:
    items: list[str] = []

    for line in section_text.splitlines():
        stripped = line.strip()
        match = BULLET_ITEM_RE.match(stripped)
        if match and not stripped.startswith("- **"):
            items.append(match.group(1).strip())

    return items


def _parse_single_value(section_text: str) -> str | None:
    value = section_text.strip()
    if not value or value == "N/A":
        return None
    return value


def _parse_list_or_empty(section_text: str) -> list[str]:
    value = section_text.strip()
    if not value or value == "N/A":
        return []
    numbered = _parse_numbered_list(value)
    if numbered:
        return numbered
    bullets = _parse_bullet_list(value)
    if bullets:
        return bullets
    return [value]


def _parse_alternative_flows(section_text: str, use_case_id: str) -> list[dict]:
    if not section_text.strip() or section_text.strip() == "N/A":
        return []

    lines = section_text.splitlines()
    flows: list[dict] = []
    current_flow: dict | None = None
    collecting_postconditions = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        title_match = ALT_FLOW_TITLE_RE.match(stripped)
        if title_match:
            if current_flow is not None:
                flows.append(current_flow)

            title = title_match.group(1).strip()
            suffix = title.split(".", 1)[0].replace(" ", "")
            current_flow = {
                "id": f"{use_case_id}.alt.{suffix}",
                "title": title,
                "steps": [],
                "postconditions": [],
            }
            collecting_postconditions = False
            continue

        if current_flow is None:
            continue

        if stripped == "Postconditions:":
            collecting_postconditions = True
            continue

        nested_match = NESTED_ITEM_RE.match(line)
        if nested_match:
            current_flow["steps"].append(nested_match.group(1).strip())
            continue

        numbered_match = NUMBERED_ITEM_RE.match(stripped)
        if numbered_match and collecting_postconditions:
            current_flow["postconditions"].append(
                numbered_match.group(1).strip())

    if current_flow is not None:
        flows.append(current_flow)

    return flows


def _build_units(use_case: dict) -> tuple[RequirementUnit, ...]:
    units: list[RequirementUnit] = []

    for index, text in enumerate(use_case["preconditions"], start=1):
        units.append(
            RequirementUnit(
                id=f"{use_case['id']}.pre.{index}",
                kind=RequirementUnitKind.PRECONDITION,
                text=text,
            )
        )

    if use_case["trigger"] is not None:
        units.append(
            RequirementUnit(
                id=f"{use_case['id']}.trigger.1",
                kind=RequirementUnitKind.TRIGGER,
                text=use_case["trigger"],
            )
        )

    for index, text in enumerate(use_case["main_success_scenario"], start=1):
        units.append(
            RequirementUnit(
                id=f"{use_case['id']}.step.{index}",
                kind=RequirementUnitKind.STEP,
                text=text,
                metadata={
                    "flow": "main",
                    "source_section": "main_success_scenario",
                    "sequence": index,
                },
            )
        )

    for index, text in enumerate(use_case["postconditions"], start=1):
        units.append(
            RequirementUnit(
                id=f"{use_case['id']}.post.{index}",
                kind=RequirementUnitKind.POSTCONDITION,
                text=text,
            )
        )

    for flow in use_case["alternative_flows"]:
        for index, text in enumerate(flow["steps"], start=1):
            units.append(
                RequirementUnit(
                    id=f"{flow['id']}.step.{index}",
                    kind=RequirementUnitKind.STEP,
                    text=text,
                    metadata={
                        "flow": "alternative",
                        "alternative_flow_id": flow["id"],
                        "alternative_flow_title": flow["title"],
                        "source_section": "alternative_flows.steps",
                        "sequence": index,
                    },
                )
            )

        for index, text in enumerate(flow["postconditions"], start=1):
            units.append(
                RequirementUnit(
                    id=f"{flow['id']}.post.{index}",
                    kind=RequirementUnitKind.POSTCONDITION,
                    text=text,
                    metadata={
                        "flow": "alternative",
                        "alternative_flow_id": flow["id"],
                        "alternative_flow_title": flow["title"],
                        "source_section": "alternative_flows.postconditions",
                        "sequence": index,
                    },
                )
            )

    return tuple(units)


def load_use_cases_markdown_requirement_catalog(data: dict) -> RequirementCatalog:
    text = data["content"]
    requirements: list[Requirement] = []

    for use_case_id, title, body in _slice_use_case_blocks(text):
        section_map = _parse_section_map(body)

        use_case = {
            "id": use_case_id,
            "title": title,
            "context_of_use": _parse_single_value(section_map.get("context_of_use", "")),
            "scope": _parse_single_value(section_map.get("scope", "")),
            "level": _parse_single_value(section_map.get("level", "")),
            "primary_actor": _parse_single_value(section_map.get("primary_actor", "")),
            "stakeholders_and_interests": _parse_list_or_empty(
                section_map.get("stakeholders_and_interests", "")
            ),
            "constraints": _parse_list_or_empty(section_map.get("constraints", "")),
            "preconditions": _parse_list_or_empty(section_map.get("preconditions", "")),
            "trigger": _parse_single_value(section_map.get("trigger", "")),
            "main_success_scenario": _parse_list_or_empty(
                section_map.get("main_success_scenario", "")
            ),
            "postconditions": _parse_list_or_empty(section_map.get("postconditions", "")),
            "alternative_flows": _parse_alternative_flows(
                section_map.get("alternative_flows", ""),
                use_case_id,
            ),
            "technology_and_data_variations": _parse_list_or_empty(
                section_map.get("technology_and_data_variations", "")
            ),
            "related_information": _parse_list_or_empty(
                section_map.get("related_information", "")
            ),
        }

        requirements.append(
            Requirement(
                id=use_case["id"],
                kind=RequirementKind.USE_CASE,
                title=use_case["title"],
                summary=use_case["context_of_use"],
                actor=use_case["primary_actor"],
                units=_build_units(use_case),
                metadata={
                    "source_format": "tbuis_use_cases_markdown_v1",
                    "scope": use_case["scope"],
                    "level": use_case["level"],
                    "stakeholders_and_interests": use_case["stakeholders_and_interests"],
                    "constraints": use_case["constraints"],
                    "technology_and_data_variations": use_case["technology_and_data_variations"],
                    "related_information": use_case["related_information"],
                },
            )
        )

    return RequirementCatalog(
        requirements=tuple(requirements),
        metadata={
            "format": "tbuis_use_cases_markdown_v1",
        },
    )
