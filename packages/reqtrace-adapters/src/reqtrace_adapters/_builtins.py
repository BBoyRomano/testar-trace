"""Built-in parser registrations."""

from reqtrace_adapters.evidence import testar
from reqtrace_adapters.registry import register_builtin_parser
from reqtrace_adapters.requirements import gherkin, use_cases, user_stories

__all__ = ["register_builtin_parsers"]


def register_builtin_parsers() -> None:
    """Register parsers shipped with reqtrace-adapters."""
    register_builtin_parser(
        "requirements",
        "use-case",
        "md",
        use_cases.load_use_case_markdown,
        replace=True,
    )
    register_builtin_parser(
        "requirements",
        "use-case",
        "json",
        use_cases.load_use_case_json,
        replace=True,
    )
    register_builtin_parser(
        "requirements",
        "user-story",
        "json",
        user_stories.load_user_story_json,
        replace=True,
    )
    register_builtin_parser(
        "requirements",
        "gherkin",
        "feature",
        gherkin.load_gherkin_feature,
        replace=True,
    )
    register_builtin_parser(
        "evidence",
        "testar-state-model",
        "json",
        testar.load_testar_state_model_json,
        replace=True,
    )
