"""Gherkin requirement adapters."""

from dataclasses import dataclass

from reqtrace.models.requirements import (
    RequirementArtifact,
    RequirementDocument,
    RequirementFragment,
    RequirementScenario,
    RequirementSet,
)

from reqtrace_adapters._utils import slugify, source_ref_from_source
from reqtrace_adapters.sources.base import SourceInput

__all__ = ["load_gherkin_feature"]


@dataclass(slots=True, frozen=True)
class _GherkinStep:
    """A parsed Gherkin step."""

    keyword: str
    text: str
    order_index: int

    def __post_init__(self) -> None:
        if not self.keyword.strip():
            raise ValueError("_GherkinStep.keyword must not be blank.")
        if not self.text.strip():
            raise ValueError("_GherkinStep.text must not be blank.")
        if self.order_index < 0:
            raise ValueError("_GherkinStep.order_index must be non-negative.")


@dataclass(slots=True, frozen=True)
class _GherkinFeature:
    """A parsed Gherkin feature before canonical mapping."""

    id: str
    title: str
    steps: tuple[_GherkinStep, ...]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("_GherkinFeature.id must not be blank.")
        if not self.title.strip():
            raise ValueError("_GherkinFeature.title must not be blank.")


def load_gherkin_feature(source: SourceInput) -> RequirementSet:
    """Load requirements from Gherkin feature text."""
    if not isinstance(source.data, str):
        raise TypeError(f"{source.name} feature input must be text.")

    feature = _parse_gherkin_feature(source.data, source=source)
    return _map_gherkin_feature(feature, source=source)


def _parse_gherkin_feature(text: str, *, source: SourceInput) -> _GherkinFeature:
    title = None
    steps: list[_GherkinStep] = []
    step_index = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("Feature:"):
            title = line.partition(":")[2].strip()
            continue

        lowered = line.lower()
        for keyword in ("given", "when", "then", "and", "but"):
            prefix = f"{keyword} "
            if lowered.startswith(prefix):
                step_index += 1
                steps.append(
                    _GherkinStep(
                        keyword=keyword,
                        text=line,
                        order_index=step_index,
                    ),
                )
                break

    if title is None:
        raise ValueError(f"Feature file must contain a Feature header: {source.name}")

    return _GherkinFeature(
        id=slugify(title, fallback="gherkin-feature"),
        title=title,
        steps=tuple(steps),
    )


def _map_gherkin_feature(
    feature: _GherkinFeature,
    *,
    source: SourceInput,
) -> RequirementSet:
    document_id = f"{slugify(feature.title)}-doc"
    fragments = tuple(
        RequirementFragment(
            id=f"{feature.id}:fragment:{step.order_index}",
            requirement_id=feature.id,
            text=step.text,
            kind=step.keyword,
            order_index=step.order_index,
        )
        for step in feature.steps
    )

    return RequirementSet(
        documents=(
            RequirementDocument(
                id=document_id,
                title=feature.title,
                source_ref=source_ref_from_source(source),
            ),
        ),
        requirements=(
            RequirementArtifact(
                id=feature.id,
                title=feature.title,
                document_id=document_id,
            ),
        ),
        fragments=fragments,
        scenarios=(
            RequirementScenario(
                id=f"{feature.id}:scenario:main",
                requirement_id=feature.id,
                kind="gherkin-scenario",
                title=feature.title,
                fragment_ids=tuple(fragment.id for fragment in fragments),
                order_index=0,
                metadata={"source_kind": "feature"},
            ),
        )
        if fragments
        else (),
    )
