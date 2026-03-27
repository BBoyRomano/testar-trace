from __future__ import annotations

from reqtrace.domain.requirements import (
    Requirement,
    RequirementCatalog,
    RequirementKind,
    RequirementUnit,
    RequirementUnitKind,
)


def load_canonical_json_requirement_catalog(data: dict) -> RequirementCatalog:
    requirements = tuple(
        Requirement(
            id=item["id"],
            kind=RequirementKind(item["kind"]),
            title=item["title"],
            summary=item.get("summary"),
            actor=item.get("actor"),
            units=tuple(
                RequirementUnit(
                    id=unit["id"],
                    kind=RequirementUnitKind(unit["kind"]),
                    text=unit["text"],
                    metadata=unit.get("metadata", {}),
                )
                for unit in item.get("units", [])
            ),
            metadata=item.get("metadata", {}),
        )
        for item in data.get("requirements", [])
    )

    return RequirementCatalog(
        requirements=requirements,
        metadata=data.get("metadata", {}),
    )
