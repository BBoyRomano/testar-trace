"""User-story requirement adapters."""

from collections.abc import Mapping
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

__all__ = ["load_user_story_json"]


@dataclass(slots=True, frozen=True)
class _UserStory:
    """A parsed user story before canonical mapping."""

    id: str
    title: str
    role: str | None = None
    goal: str | None = None
    benefit: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_UserStory.id must not be blank.")
        if not self.title.strip():
            raise ValueError("_UserStory.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    @property
    def summary(self) -> str | None:
        """Return the story in role-goal-benefit form when available."""
        parts = []
        if self.role:
            parts.append(f"As a {self.role}")
        if self.goal:
            parts.append(f"I want {self.goal}")
        if self.benefit:
            parts.append(f"so that {self.benefit}")
        return ", ".join(parts) or None


@dataclass(slots=True, frozen=True)
class _UserStoryDocument:
    """A parsed source document containing user stories."""

    title: str
    stories: tuple[_UserStory, ...]
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("_UserStoryDocument.title must not be blank.")
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))


def load_user_story_json(source: SourceInput) -> RequirementSet:
    """Load user-story requirements from a JSON object."""
    data = _require_mapping(source.data, context=f"{source.name} JSON")
    document = _parse_user_story_json(data, source=source)
    return _map_user_story_document(document, source=source)


def _parse_user_story_json(
    data: Mapping[str, object],
    *,
    source: SourceInput,
) -> _UserStoryDocument:
    title = _story_title(data, source)
    story = _UserStory(
        id=_story_id(data, fallback_title=title),
        title=title,
        role=_optional_text(data.get("role") or data.get("Role") or data.get("AsA")),
        goal=_optional_text(data.get("goal") or data.get("Goal") or data.get("IWant")),
        benefit=_optional_text(
            data.get("benefit") or data.get("Benefit") or data.get("SoThat"),
        ),
        metadata=_story_metadata(data),
    )
    return _UserStoryDocument(title=title, stories=(story,))


def _map_user_story_document(
    document: _UserStoryDocument,
    *,
    source: SourceInput,
) -> RequirementSet:
    document_id = f"{slugify(document.title)}-doc"
    requirements = tuple(
        RequirementArtifact(
            id=story.id,
            title=story.title,
            summary=story.summary,
            document_id=document_id,
            metadata=story.metadata,
        )
        for story in document.stories
    )
    fragments = tuple(
        fragment
        for story in document.stories
        for fragment in _map_user_story_fragments(story)
    )
    scenarios = tuple(
        RequirementScenario(
            id=f"{story.id}:scenario:main",
            requirement_id=story.id,
            kind="user-story",
            title=story.title,
            fragment_ids=tuple(
                fragment.id
                for fragment in fragments
                if fragment.requirement_id == story.id
            ),
            order_index=0,
            metadata={"source_kind": "user_story"},
        )
        for story in document.stories
        if any(fragment.requirement_id == story.id for fragment in fragments)
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
    )


def _map_user_story_fragments(story: _UserStory) -> tuple[RequirementFragment, ...]:
    fragments: list[RequirementFragment] = []
    if story.role:
        fragments.append(
            _story_fragment(story, index=1, kind="role", text=f"As a {story.role}"),
        )
    if story.goal:
        fragments.append(
            _story_fragment(
                story,
                index=len(fragments) + 1,
                kind="goal",
                text=story.goal,
            ),
        )
    if story.benefit:
        fragments.append(
            _story_fragment(
                story,
                index=len(fragments) + 1,
                kind="benefit",
                text=story.benefit,
            ),
        )
    if not fragments:
        fragments.append(
            _story_fragment(story, index=1, kind="summary", text=story.title),
        )
    return tuple(fragments)


def _story_fragment(
    story: _UserStory,
    *,
    index: int,
    kind: str,
    text: str,
) -> RequirementFragment:
    return RequirementFragment(
        id=f"{story.id}:fragment:{index}",
        requirement_id=story.id,
        text=text,
        kind=kind,
        order_index=index,
    )


def _story_title(data: Mapping[str, object], source: SourceInput) -> str:
    for key in ("title", "name", "Name", "summary", "Summary"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return _source_stem(source)


def _story_id(data: Mapping[str, object], *, fallback_title: str) -> str:
    for key in ("id", "ID", "Id", "key", "Key", "identifier", "Identifier"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return slugify(value)

    slug = slugify(fallback_title, fallback="")
    return slug or "user-story"


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _story_metadata(data: Mapping[str, object]) -> dict[str, object]:
    ignored = {
        "id",
        "ID",
        "Id",
        "key",
        "Key",
        "identifier",
        "Identifier",
        "title",
        "name",
        "Name",
        "summary",
        "Summary",
        "role",
        "Role",
        "AsA",
        "goal",
        "Goal",
        "IWant",
        "benefit",
        "Benefit",
        "SoThat",
    }
    return {key: value for key, value in data.items() if key not in ignored}


def _require_mapping(value: object, *, context: str) -> dict[str, object]:
    if not _is_object_dict(value):
        raise TypeError(f"{context} must be an object with string keys.")
    return value


def _is_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _source_stem(source: SourceInput) -> str:
    return source.name.rsplit(".", maxsplit=1)[0] or source.name
