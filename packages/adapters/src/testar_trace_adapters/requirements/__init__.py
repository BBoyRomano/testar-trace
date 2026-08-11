"""Built-in requirement adapters."""

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
    parse_use_case_json,
    parse_use_case_markdown,
    parse_use_cases,
)
from testar_trace_adapters.requirements.user_stories import (
    is_user_story_source,
    parse_user_stories,
)

__all__ = [
    "is_formal_requirements",
    "is_gherkin_feature",
    "is_use_case_source",
    "is_user_story_source",
    "parse_formal_requirements",
    "parse_gherkin_feature",
    "parse_use_case_json",
    "parse_use_case_markdown",
    "parse_use_cases",
    "parse_user_stories",
]
