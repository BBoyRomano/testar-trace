from __future__ import annotations

import csv
import io
import re

from reqtrace.domain.requirements import (
    Requirement,
    RequirementCatalog,
    RequirementKind,
    RequirementUnit,
    RequirementUnitKind,
)


USER_STORY_ACTOR_RE = re.compile(
    r"^\s*As\s+a[n]?\s+(.*?),\s*I\s+want\s+to\s+",
    re.IGNORECASE,
)


def _parse_actor(story: str) -> str | None:
    match = USER_STORY_ACTOR_RE.match(story)
    if match is None:
        return None

    actor = match.group(1).strip()
    return actor or None


def _parse_acceptance_criteria(value: str) -> list[str]:
    if not value.strip():
        return []

    parts = [part.strip() for part in value.split("||")]
    return [part for part in parts if part]


def load_user_stories_csv_requirement_catalog(data: dict) -> RequirementCatalog:
    content = data["content"]
    reader = csv.DictReader(io.StringIO(content))
    requirements: list[Requirement] = []

    for row in reader:
        story_id = row["id"].strip()
        title = row["title"].strip()
        story = row["story"].strip()
        acceptance_criteria = _parse_acceptance_criteria(
            row.get("acceptance_criteria", "")
        )

        units: list[RequirementUnit] = [
            RequirementUnit(
                id=f"{story_id}.step.1",
                kind=RequirementUnitKind.STEP,
                text=story,
                metadata={
                    "source_section": "story",
                    "sequence": 1,
                },
            )
        ]

        for index, criterion in enumerate(acceptance_criteria, start=1):
            units.append(
                RequirementUnit(
                    id=f"{story_id}.post.{index}",
                    kind=RequirementUnitKind.POSTCONDITION,
                    text=criterion,
                    metadata={
                        "source_section": "acceptance_criteria",
                        "sequence": index,
                    },
                )
            )

        requirements.append(
            Requirement(
                id=story_id,
                kind=RequirementKind.USER_STORY,
                title=title,
                summary=story,
                actor=_parse_actor(story),
                units=tuple(units),
                metadata={
                    "source_format": "user_stories_csv_v1",
                },
            )
        )

    return RequirementCatalog(
        requirements=tuple(requirements),
        metadata={
            "format": "user_stories_csv_v1",
        },
    )
