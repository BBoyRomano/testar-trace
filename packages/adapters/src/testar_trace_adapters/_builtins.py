"""Built-in adapter definitions."""

from testar_trace.domain.requirements import RequirementSet
from testar_trace.domain.state_models import StateModel
from testar_trace_adapters.registry import Adapter, AdapterRegistry
from testar_trace_adapters.requirements.formal import (
    is_formal_requirements,
    parse_formal_requirements,
)
from testar_trace_adapters.requirements.gherkin import (
    is_gherkin_feature,
    parse_gherkin_feature,
)
from testar_trace_adapters.requirements.use_cases import (
    is_use_case_source,
    parse_use_cases,
)
from testar_trace_adapters.requirements.user_stories import (
    is_user_story_source,
    parse_user_stories,
)
from testar_trace_adapters.state_models.testar import (
    is_testar_state_model,
    parse_testar_state_model,
)


def create_builtin_adapter_registry() -> AdapterRegistry:
    """Create a registry containing the built-in adapters."""
    registry = AdapterRegistry()
    registry.register_requirement(
        Adapter[RequirementSet](
            id="formal",
            name="Formal requirements",
            formats=("json",),
            adapt=parse_formal_requirements,
            detect=is_formal_requirements,
        )
    )
    registry.register_requirement(
        Adapter[RequirementSet](
            id="use-case",
            name="Use case",
            formats=("json", "md", "markdown"),
            adapt=parse_use_cases,
            detect=is_use_case_source,
        )
    )
    registry.register_requirement(
        Adapter[RequirementSet](
            id="user-story",
            name="User story",
            formats=("json",),
            adapt=parse_user_stories,
            detect=is_user_story_source,
        )
    )
    registry.register_requirement(
        Adapter[RequirementSet](
            id="gherkin",
            name="Gherkin",
            formats=("feature",),
            adapt=parse_gherkin_feature,
            detect=is_gherkin_feature,
        )
    )
    registry.register_state_model(
        Adapter[StateModel](
            id="testar",
            name="TESTAR state model",
            formats=("json",),
            adapt=parse_testar_state_model,
            detect=is_testar_state_model,
        )
    )
    return registry
