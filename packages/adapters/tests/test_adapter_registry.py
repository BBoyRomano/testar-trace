import pytest

from testar_trace.domain.requirements import Requirement, RequirementSet
from testar_trace_adapters import (
    Adapter,
    AdapterRegistry,
    SourceArtifact,
    create_builtin_adapter_registry,
)


def _custom_adapter(source: SourceArtifact) -> RequirementSet:
    return RequirementSet(
        requirements=(Requirement(id=source.id, title=source.name),),
    )


def test_registry_registers_typed_requirement_adapter() -> None:
    adapter = Adapter[RequirementSet](
        id="custom",
        name="Custom",
        formats=(".TXT",),
        adapt=_custom_adapter,
    )
    registry = AdapterRegistry()

    registry.register_requirement(adapter)

    assert registry.get_requirement("custom") is adapter
    assert adapter.formats == ("txt",)
    assert tuple(registry.requirement_adapters()) == (adapter,)


def test_registry_rejects_duplicate_without_replace() -> None:
    adapter = Adapter[RequirementSet](
        id="custom",
        name="Custom",
        formats=("txt",),
        adapt=_custom_adapter,
    )
    registry = AdapterRegistry()
    registry.register_requirement(adapter)

    with pytest.raises(ValueError, match="already registered"):
        registry.register_requirement(adapter)


def test_builtin_registries_are_fresh_and_complete() -> None:
    first = create_builtin_adapter_registry()
    second = create_builtin_adapter_registry()

    assert first is not second
    assert [item.id for item in first.requirement_adapters()] == [
        "formal",
        "use-case",
        "user-story",
        "gherkin",
    ]
    assert [item.id for item in first.state_model_adapters()] == ["testar"]


def test_adapter_validates_public_identifier() -> None:
    with pytest.raises(ValueError, match="adapter id"):
        Adapter[RequirementSet](
            id="Not Valid",
            name="Invalid",
            formats=("txt",),
            adapt=_custom_adapter,
        )
