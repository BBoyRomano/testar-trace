from __future__ import annotations

from reqtrace.domain.requirements import (
    Requirement,
    RequirementCatalog,
    RequirementKind,
    RequirementUnit,
    RequirementUnitKind,
)


def _build_precondition_units(use_case: dict) -> list[RequirementUnit]:
    return [
        RequirementUnit(
            id=f"{use_case['id']}.pre.{index}",
            kind=RequirementUnitKind.PRECONDITION,
            text=text,
        )
        for index, text in enumerate(use_case.get("preconditions", []), start=1)
    ]


def _build_trigger_units(use_case: dict) -> list[RequirementUnit]:
    trigger = use_case.get("trigger")
    if not trigger:
        return []

    return [
        RequirementUnit(
            id=f"{use_case['id']}.trigger.1",
            kind=RequirementUnitKind.TRIGGER,
            text=trigger,
        )
    ]


def _build_main_step_units(use_case: dict) -> list[RequirementUnit]:
    return [
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
        for index, text in enumerate(
            use_case.get("main_success_scenario", []),
            start=1,
        )
    ]


def _build_postcondition_units(use_case: dict) -> list[RequirementUnit]:
    return [
        RequirementUnit(
            id=f"{use_case['id']}.post.{index}",
            kind=RequirementUnitKind.POSTCONDITION,
            text=text,
        )
        for index, text in enumerate(use_case.get("postconditions", []), start=1)
    ]


def _build_alternative_flow_units(use_case: dict) -> list[RequirementUnit]:
    units: list[RequirementUnit] = []

    for flow in use_case.get("alternative_flows", []):
        flow_id = flow["id"]

        for index, text in enumerate(flow.get("steps", []), start=1):
            units.append(
                RequirementUnit(
                    id=f"{flow_id}.step.{index}",
                    kind=RequirementUnitKind.STEP,
                    text=text,
                    metadata={
                        "flow": "alternative",
                        "alternative_flow_id": flow_id,
                        "alternative_flow_title": flow["title"],
                        "source_section": "alternative_flows.steps",
                        "sequence": index,
                    },
                )
            )

        for index, text in enumerate(flow.get("postconditions", []), start=1):
            units.append(
                RequirementUnit(
                    id=f"{flow_id}.post.{index}",
                    kind=RequirementUnitKind.POSTCONDITION,
                    text=text,
                    metadata={
                        "flow": "alternative",
                        "alternative_flow_id": flow_id,
                        "alternative_flow_title": flow["title"],
                        "source_section": "alternative_flows.postconditions",
                        "sequence": index,
                    },
                )
            )

    return units


def load_use_cases_json_requirement_catalog(data: dict) -> RequirementCatalog:
    requirements: list[Requirement] = []

    for use_case in data.get("use_cases", []):
        units = (
            _build_precondition_units(use_case)
            + _build_trigger_units(use_case)
            + _build_main_step_units(use_case)
            + _build_postcondition_units(use_case)
            + _build_alternative_flow_units(use_case)
        )

        requirements.append(
            Requirement(
                id=use_case["id"],
                kind=RequirementKind.USE_CASE,
                title=use_case["title"],
                summary=use_case.get("context_of_use"),
                actor=use_case.get("primary_actor"),
                units=tuple(units),
                metadata={
                    "source_format": "tbuis_use_cases_v1",
                    "scope": use_case.get("scope"),
                    "level": use_case.get("level"),
                    "stakeholders_and_interests": use_case.get(
                        "stakeholders_and_interests", []
                    ),
                    "constraints": use_case.get("constraints", []),
                    "technology_and_data_variations": use_case.get(
                        "technology_and_data_variations", []
                    ),
                    "related_information": use_case.get("related_information", []),
                },
            )
        )

    return RequirementCatalog(
        requirements=tuple(requirements),
        metadata={
            "format": data.get("format", "tbuis_use_cases_v1"),
        },
    )
