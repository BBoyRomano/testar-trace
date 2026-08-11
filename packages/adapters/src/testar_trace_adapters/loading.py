"""Source loading, adapter selection, and canonical aggregation."""

from collections.abc import Iterable

from testar_trace.domain.formal_requirements import FormalRequirementSet
from testar_trace.domain.requirements import RequirementSet
from testar_trace.domain.state_models import StateModel, StateModelCollection
from testar_trace_adapters._builtins import create_builtin_adapter_registry
from testar_trace_adapters.registry import Adapter, AdapterRegistry
from testar_trace_adapters.source import (
    SourceArtifact,
    SourceValue,
    read_source_artifacts,
)

__all__ = ["load_requirements", "load_state_models"]


def load_requirements(
    source: SourceValue,
    *,
    adapter: str | Adapter[RequirementSet] | None = None,
    registry: AdapterRegistry | None = None,
    pattern: str = "*",
    recursive: bool = False,
) -> RequirementSet:
    """Load one or more artifacts into one canonical requirement set."""
    artifacts = read_source_artifacts(
        source,
        pattern=pattern,
        recursive=recursive,
    )
    _require_unique_artifact_ids(artifacts)
    selected_registry = registry or create_builtin_adapter_registry()
    sets = tuple(
        _adapt_requirement(
            artifact,
            adapter=adapter,
            registry=selected_registry,
        )
        for artifact in artifacts
    )
    return _combine_requirement_sets(sets, artifacts=artifacts)


def load_state_models(
    source: SourceValue,
    *,
    adapter: str | Adapter[StateModel] | None = None,
    registry: AdapterRegistry | None = None,
    pattern: str = "*",
    recursive: bool = False,
    collection_id: str = "state-models",
    title: str = "State models",
) -> StateModelCollection:
    """Load one state model per artifact into one canonical collection."""
    artifacts = read_source_artifacts(
        source,
        pattern=pattern,
        recursive=recursive,
    )
    _require_unique_artifact_ids(artifacts)
    selected_registry = registry or create_builtin_adapter_registry()
    models = tuple(
        _adapt_state_model(
            artifact,
            adapter=adapter,
            registry=selected_registry,
        )
        for artifact in artifacts
    )
    return StateModelCollection(
        id=collection_id,
        title=title,
        models=models,
        metadata={"source_artifact_ids": tuple(item.id for item in artifacts)},
    )


def _adapt_requirement(
    artifact: SourceArtifact,
    *,
    adapter: str | Adapter[RequirementSet] | None,
    registry: AdapterRegistry,
) -> RequirementSet:
    selected = _select_adapter(
        artifact,
        requested=adapter,
        registered=tuple(registry.requirement_adapters()),
        get=registry.get_requirement,
        target="requirements",
    )
    result = selected(artifact)
    if not isinstance(result, RequirementSet):
        raise TypeError("a requirement adapter must return RequirementSet")
    return result


def _adapt_state_model(
    artifact: SourceArtifact,
    *,
    adapter: str | Adapter[StateModel] | None,
    registry: AdapterRegistry,
) -> StateModel:
    selected = _select_adapter(
        artifact,
        requested=adapter,
        registered=tuple(registry.state_model_adapters()),
        get=registry.get_state_model,
        target="state model",
    )
    result = selected(artifact)
    if not isinstance(result, StateModel):
        raise TypeError("a state-model adapter must return StateModel")
    return result


def _select_adapter[T](
    artifact: SourceArtifact,
    *,
    requested: str | Adapter[T] | None,
    registered: tuple[Adapter[T], ...],
    get,
    target: str,
) -> Adapter[T]:
    if isinstance(requested, Adapter):
        if artifact.format not in requested.formats:
            raise ValueError(
                f"adapter {requested.id!r} does not support {artifact.format!r}"
            )
        return requested
    if isinstance(requested, str):
        selected = get(requested)
        if selected is None:
            raise ValueError(f"unknown {target} adapter: {requested!r}")
        if artifact.format not in selected.formats:
            raise ValueError(
                f"adapter {selected.id!r} does not support {artifact.format!r}"
            )
        return selected
    if requested is not None:
        raise TypeError("adapter must be an adapter id, Adapter, or None")

    format_matches = tuple(
        candidate for candidate in registered if artifact.format in candidate.formats
    )
    detected = tuple(
        candidate for candidate in format_matches if candidate.supports(artifact)
    )
    if len(detected) == 1:
        return detected[0]
    if not detected:
        raise ValueError(
            f"no {target} adapter recognized {artifact.name!r} "
            f"with format {artifact.format!r}"
        )
    adapter_ids = ", ".join(candidate.id for candidate in detected)
    raise ValueError(
        f"multiple {target} adapters recognized {artifact.name!r}: {adapter_ids}"
    )


def _combine_requirement_sets(
    sets: Iterable[RequirementSet],
    *,
    artifacts: tuple[SourceArtifact, ...],
) -> RequirementSet:
    values = tuple(sets)
    formalizations = tuple(
        value.formalization for value in values if value.formalization is not None
    )
    formalization: FormalRequirementSet | None = None
    if formalizations:
        first = formalizations[0]
        if any(
            item.status is not first.status
            or item.policy != first.policy
            or item.schema_version != first.schema_version
            for item in formalizations[1:]
        ):
            raise ValueError(
                "combined formal requirements must use the same status, policy, "
                "and schema version"
            )
        formalization = FormalRequirementSet(
            status=first.status,
            observables=tuple(
                item for value in formalizations for item in value.observables
            ),
            bindings=tuple(item for value in formalizations for item in value.bindings),
            policy=first.policy,
            schema_version=first.schema_version,
            metadata={"source_artifact_ids": tuple(item.id for item in artifacts)},
        )
    return RequirementSet(
        documents=tuple(item for value in values for item in value.documents),
        requirements=tuple(item for value in values for item in value.requirements),
        elements=tuple(item for value in values for item in value.elements),
        flows=tuple(item for value in values for item in value.flows),
        formalization=formalization,
        metadata={"source_artifact_ids": tuple(item.id for item in artifacts)},
    )


def _require_unique_artifact_ids(
    artifacts: tuple[SourceArtifact, ...],
) -> None:
    seen: set[str] = set()
    for artifact in artifacts:
        if artifact.id in seen:
            raise ValueError(f"duplicate source artifact id: {artifact.id!r}")
        seen.add(artifact.id)
