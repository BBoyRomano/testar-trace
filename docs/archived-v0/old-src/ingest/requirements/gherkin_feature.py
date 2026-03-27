from __future__ import annotations

from reqtrace.domain.requirements import (
    Requirement,
    RequirementCatalog,
    RequirementKind,
    RequirementUnit,
    RequirementUnitKind,
)


def load_gherkin_feature_requirement_catalog(data: dict) -> RequirementCatalog:
    content = data["content"]
    lines = [line.rstrip() for line in content.splitlines()]

    feature_title: str | None = None
    requirements: list[Requirement] = []

    current_scenario_title: str | None = None
    current_units: list[RequirementUnit] = []
    current_actor: str | None = None
    step_counters = {
        RequirementUnitKind.PRECONDITION: 0,
        RequirementUnitKind.STEP: 0,
        RequirementUnitKind.POSTCONDITION: 0,
    }
    current_phase: RequirementUnitKind | None = None

    def flush_current_scenario() -> None:
        nonlocal current_scenario_title, current_units, current_actor, step_counters, current_phase

        if current_scenario_title is None:
            return

        requirement_id = f"GHERKIN.{len(requirements) + 1:02d}"
        requirements.append(
            Requirement(
                id=requirement_id,
                kind=RequirementKind.FEATURE,
                title=current_scenario_title,
                summary=feature_title,
                actor=current_actor,
                units=tuple(current_units),
                metadata={
                    "source_format": "gherkin_feature_v1",
                    "feature": feature_title,
                },
            )
        )

        current_scenario_title = None
        current_units = []
        current_actor = None
        step_counters = {
            RequirementUnitKind.PRECONDITION: 0,
            RequirementUnitKind.STEP: 0,
            RequirementUnitKind.POSTCONDITION: 0,
        }
        current_phase = None

    for raw_line in lines:
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("Feature:"):
            feature_title = line.removeprefix("Feature:").strip()
            continue

        if line.startswith("Scenario:"):
            flush_current_scenario()
            current_scenario_title = line.removeprefix("Scenario:").strip()
            continue

        if current_scenario_title is None:
            continue

        keyword: str | None = None
        text: str | None = None

        for candidate in ("Given", "When", "Then", "And"):
            prefix = f"{candidate} "
            if line.startswith(prefix):
                keyword = candidate
                text = line[len(prefix):].strip()
                break

        if keyword is None or text is None:
            continue

        if keyword == "Given":
            current_phase = RequirementUnitKind.PRECONDITION
            kind = RequirementUnitKind.PRECONDITION
        elif keyword == "When":
            current_phase = RequirementUnitKind.STEP
            kind = RequirementUnitKind.STEP
        elif keyword == "Then":
            current_phase = RequirementUnitKind.POSTCONDITION
            kind = RequirementUnitKind.POSTCONDITION
        else:
            if current_phase is None:
                continue
            kind = current_phase

        step_counters[kind] += 1

        suffix = {
            RequirementUnitKind.PRECONDITION: "pre",
            RequirementUnitKind.STEP: "step",
            RequirementUnitKind.POSTCONDITION: "post",
        }[kind]

        requirement_index = len(requirements) + 1
        unit_id = f"GHERKIN.{requirement_index:02d}.{suffix}.{step_counters[kind]}"

        current_units.append(
            RequirementUnit(
                id=unit_id,
                kind=kind,
                text=text,
                metadata={
                    "gherkin_keyword": keyword,
                    "sequence": step_counters[kind],
                },
            )
        )

        lowered = text.lower()
        if current_actor is None and " as " in f" {lowered} ":
            parts = lowered.split(" as ", 1)
            current_actor = parts[1].strip()

    flush_current_scenario()

    return RequirementCatalog(
        requirements=tuple(requirements),
        metadata={
            "format": "gherkin_feature_v1",
        },
    )
