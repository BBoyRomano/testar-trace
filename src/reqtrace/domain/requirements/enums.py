from reqtrace.domain.common.enum_base import StrEnum


class RequirementKind(StrEnum):
    USE_CASE = "use_case"
    USER_STORY = "user_story"
    FORMAL_REQUIREMENT = "formal_requirement"
    GHERKIN_SCENARIO = "gherkin_scenario"
    ACCEPTANCE_CRITERION = "acceptance_criterion"


class RequirementNotation(StrEnum):
    USE_CASE = "use_case"
    USER_STORY = "user_story"
    GHERKIN = "gherkin"
    NATURAL_LANGUAGE = "natural_language"
    FORMAL = "formal"


class RequirementFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    FEATURE = "feature"
    REQIF = "reqif"
    YAML = "yaml"
    XML = "xml"
    HTML = "html"
    TEXT = "text"
    OTHER = "other"


class RequirementFragmentKind(StrEnum):
    PRECONDITION = "precondition"
    TRIGGER = "trigger"
    MAIN_STEP = "main_step"
    ALTERNATIVE_STEP = "alternative_step"
    POSTCONDITION = "postcondition"
    CONSTRAINT = "constraint"
    RELATED_INFORMATION = "related_information"
    GIVEN = "given"
    WHEN = "when"
    THEN = "then"


class RequirementFlowKind(StrEnum):
    MAIN = "main"
    ALTERNATIVE = "alternative"


class RequirementFlowEdgeKind(StrEnum):
    NEXT = "next"
    BRANCH = "branch"
    RESUME = "resume"
    TERMINATES = "terminates"
