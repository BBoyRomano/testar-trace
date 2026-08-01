"""Loading functions for ReqTrace adapters."""

# ruff: noqa: A002

from collections.abc import Iterable
from pathlib import Path
from typing import cast

from reqtrace.models.evidence import EvidenceSet
from reqtrace.models.requirements import (
    RequirementArtifact,
    RequirementDocument,
    RequirementFragment,
    RequirementScenario,
    RequirementSet,
)

from reqtrace_adapters._utils import normalize_format, normalize_key
from reqtrace_adapters.registry import available_parsers, get_parser
from reqtrace_adapters.sources.base import Source, SourceInput
from reqtrace_adapters.sources.directory import DirectorySource
from reqtrace_adapters.sources.file import FileSource

__all__ = [
    "load_evidence",
    "load_requirements",
    "validate_evidence",
    "validate_requirements",
]

_REQUIREMENTS_ARTIFACT = "requirements"
_EVIDENCE_ARTIFACT = "evidence"


def load_requirements(
    source: str | Path | Source,
    *,
    kind: str,
    format: str | None = None,
    pattern: str = "*",
    recursive: bool = False,
) -> RequirementSet:
    """Load requirements from a path or source."""
    normalized_kind = _normalize_kind(kind)
    inputs = _load_source_inputs(source, pattern=pattern, recursive=recursive)

    return _merge_requirement_sets(
        _parse_requirement_input(item, kind=normalized_kind, format=format)
        for item in inputs
    )


def load_evidence(
    source: str | Path | Source,
    *,
    kind: str,
    format: str | None = None,
) -> EvidenceSet:
    """Load test evidence from a path or source."""
    normalized_kind = _normalize_kind(kind)
    inputs = _load_source_inputs(source, pattern="*", recursive=False)

    if len(inputs) != 1:
        raise ValueError("Evidence loading expects exactly one source input.")

    return _parse_evidence_input(
        inputs[0],
        kind=normalized_kind,
        format=format,
    )


def validate_requirements(
    source: str | Path | Source,
    *,
    kind: str = "auto",
    format: str | None = None,
    pattern: str = "*",
    recursive: bool = False,
) -> None:
    """Validate that a source can be loaded as requirements."""
    load_requirements(
        source,
        kind=kind,
        format=format,
        pattern=pattern,
        recursive=recursive,
    )


def validate_evidence(
    source: str | Path | Source,
    *,
    kind: str = "auto",
    format: str | None = None,
) -> None:
    """Validate that a source can be loaded as evidence."""
    load_evidence(source, kind=kind, format=format)


def _load_source_inputs(
    source: str | Path | Source,
    *,
    pattern: str,
    recursive: bool,
) -> tuple[SourceInput, ...]:
    if not isinstance(source, str | Path):
        return source.load()

    path = Path(source)
    if path.is_dir():
        return DirectorySource(path, pattern=pattern, recursive=recursive).load()

    return FileSource(path).load()


def _parse_requirement_input(
    source: SourceInput,
    *,
    kind: str,
    format: str | None,
) -> RequirementSet:
    parser_format = normalize_format(format or source.format)
    if kind == "auto":
        return _parse_requirement_input_auto(source, format=parser_format)

    parser = get_parser(_REQUIREMENTS_ARTIFACT, kind, parser_format)

    if parser is None:
        available = ", ".join("/".join(key) for key in available_parsers())
        raise ValueError(
            f"No requirement parser registered for {kind}/{parser_format}. "
            f"Available parsers: {available or 'none'}",
        )

    result = cast("RequirementSet", parser(source))
    _require_loaded_requirements(result, source=source)
    return result


def _parse_evidence_input(
    source: SourceInput,
    *,
    kind: str,
    format: str | None,
) -> EvidenceSet:
    parser_format = normalize_format(format or source.format)
    if kind == "auto":
        return _parse_evidence_input_auto(source, format=parser_format)

    parser = get_parser(_EVIDENCE_ARTIFACT, kind, parser_format)

    if parser is None:
        available = ", ".join("/".join(key) for key in available_parsers())
        raise ValueError(
            f"No evidence parser registered for {kind}/{parser_format}. "
            f"Available parsers: {available or 'none'}",
        )

    result = cast("EvidenceSet", parser(source))
    _require_loaded_evidence(result, source=source)
    return result


def _normalize_kind(kind: str) -> str:
    normalized_kind = normalize_key(kind)
    return normalized_kind


def _parse_requirement_input_auto(
    source: SourceInput,
    *,
    format: str,
) -> RequirementSet:
    matches: list[tuple[str, RequirementSet]] = []
    errors: list[str] = []

    for _, parser_kind, parser_format in _candidate_parser_keys(
        artifact=_REQUIREMENTS_ARTIFACT,
        format=format,
    ):
        parser = get_parser(_REQUIREMENTS_ARTIFACT, parser_kind, parser_format)
        if parser is None:
            continue
        try:
            result = cast("RequirementSet", parser(source))
            _require_loaded_requirements(result, source=source)
        except (TypeError, ValueError) as error:
            errors.append(f"{parser_kind}: {error}")
            continue
        matches.append((parser_kind, result))

    if len(matches) == 1:
        return matches[0][1]
    if len(matches) > 1:
        kinds = ", ".join(kind for kind, _ in matches)
        raise ValueError(
            f"{source.name} matched multiple requirement parsers: {kinds}. "
            "Specify kind explicitly.",
        )

    details = "; ".join(errors)
    raise ValueError(
        f"No requirement parser could load {source.name} as {format}. "
        f"{details}".rstrip(),
    )


def _parse_evidence_input_auto(
    source: SourceInput,
    *,
    format: str,
) -> EvidenceSet:
    matches: list[tuple[str, EvidenceSet]] = []
    errors: list[str] = []

    for _, parser_kind, parser_format in _candidate_parser_keys(
        artifact=_EVIDENCE_ARTIFACT,
        format=format,
    ):
        parser = get_parser(_EVIDENCE_ARTIFACT, parser_kind, parser_format)
        if parser is None:
            continue
        try:
            result = cast("EvidenceSet", parser(source))
            _require_loaded_evidence(result, source=source)
            matches.append((parser_kind, result))
        except (TypeError, ValueError) as error:
            errors.append(f"{parser_kind}: {error}")

    if len(matches) == 1:
        return matches[0][1]
    if len(matches) > 1:
        kinds = ", ".join(kind for kind, _ in matches)
        raise ValueError(
            f"{source.name} matched multiple evidence parsers: {kinds}. "
            "Specify kind explicitly.",
        )

    details = "; ".join(errors)
    raise ValueError(
        f"No evidence parser could load {source.name} as {format}. {details}".rstrip(),
    )


def _candidate_parser_keys(
    *,
    artifact: str,
    format: str,
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        key for key in available_parsers() if key[0] == artifact and key[2] == format
    )


def _require_loaded_requirements(
    requirements: RequirementSet,
    *,
    source: SourceInput,
) -> None:
    if not requirements.requirements:
        raise ValueError(f"No requirements found in {source.name}.")


def _require_loaded_evidence(
    evidence: EvidenceSet,
    *,
    source: SourceInput,
) -> None:
    if any(
        (
            evidence.states,
            evidence.elements,
            evidence.actions,
            evidence.transitions,
        ),
    ):
        return
    raise ValueError(f"No evidence items found in {source.name}.")


def _merge_requirement_sets(
    requirement_sets: Iterable[RequirementSet],
) -> RequirementSet:
    loaded_sets = tuple(requirement_sets)

    documents: list[RequirementDocument] = []
    requirements: list[RequirementArtifact] = []
    fragments: list[RequirementFragment] = []
    scenarios: list[RequirementScenario] = []

    seen_document_ids: set[str] = set()
    seen_requirement_ids: set[str] = set()
    seen_fragment_ids: set[str] = set()
    seen_scenario_ids: set[str] = set()

    for requirement_set in loaded_sets:
        document_id_map: dict[str, str] = {}

        for document in requirement_set.documents:
            document_id = _deduplicate_id(document.id, seen_document_ids)
            document_id_map[document.id] = document_id

            documents.append(
                RequirementDocument(
                    id=document_id,
                    title=document.title,
                    source_ref=document.source_ref,
                    metadata=document.metadata,
                ),
            )

        requirement_id_map: dict[str, str] = {}

        for requirement in requirement_set.requirements:
            requirement_id = _deduplicate_id(requirement.id, seen_requirement_ids)
            requirement_id_map[requirement.id] = requirement_id

            document_id = requirement.document_id
            if document_id is not None:
                document_id = document_id_map.get(document_id, document_id)

            requirements.append(
                RequirementArtifact(
                    id=requirement_id,
                    title=requirement.title,
                    summary=requirement.summary,
                    body=requirement.body,
                    actor=requirement.actor,
                    scope=requirement.scope,
                    level=requirement.level,
                    document_id=document_id,
                    metadata=requirement.metadata,
                ),
            )

        fragment_id_map: dict[str, str] = {}

        for fragment in requirement_set.fragments:
            fragment_id = _deduplicate_id(fragment.id, seen_fragment_ids)
            fragment_id_map[fragment.id] = fragment_id

            fragments.append(
                RequirementFragment(
                    id=fragment_id,
                    requirement_id=requirement_id_map.get(
                        fragment.requirement_id,
                        fragment.requirement_id,
                    ),
                    text=fragment.text,
                    kind=fragment.kind,
                    order_index=fragment.order_index,
                    branch_id=fragment.branch_id,
                    metadata=fragment.metadata,
                ),
            )

        for scenario in requirement_set.scenarios:
            scenario_id = _deduplicate_id(scenario.id, seen_scenario_ids)
            scenarios.append(
                RequirementScenario(
                    id=scenario_id,
                    requirement_id=requirement_id_map.get(
                        scenario.requirement_id,
                        scenario.requirement_id,
                    ),
                    title=scenario.title,
                    kind=scenario.kind,
                    fragment_ids=tuple(
                        fragment_id_map.get(fragment_id, fragment_id)
                        for fragment_id in scenario.fragment_ids
                    ),
                    order_index=scenario.order_index,
                    metadata=scenario.metadata,
                ),
            )

    return RequirementSet(
        documents=tuple(documents),
        requirements=tuple(requirements),
        fragments=tuple(fragments),
        scenarios=tuple(scenarios),
        metadata={"source_count": len(loaded_sets)},
    )


def _deduplicate_id(base_id: str, seen: set[str]) -> str:
    if base_id not in seen:
        seen.add(base_id)
        return base_id

    index = 2
    candidate = f"{base_id}-{index}"

    while candidate in seen:
        index += 1
        candidate = f"{base_id}-{index}"

    seen.add(candidate)
    return candidate
