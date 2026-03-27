from reqtrace.domain.common.enum_base import StrEnum


class LinkType(StrEnum):
    COVERS = "covers"
    PARTIALLY_COVERS = "partially_covers"
    SUPPORTS = "supports"


class CoverageStatus(StrEnum):
    COVERED = "covered"
    PARTIALLY_COVERED = "partially_covered"
    UNCOVERED = "uncovered"
    UNCERTAIN = "uncertain"


class ConfidenceLabel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EvidenceTargetType(StrEnum):
    APPLICATION_STATE = "application_state"
    UI_ELEMENT = "ui_element"
    ACTION = "action"
    TRANSITION = "transition"
    OBSERVATION = "observation"
    ATTACHMENT = "attachment"


class CoverageSubjectType(StrEnum):
    REQUIREMENT = "requirement"
    REQUIREMENT_FRAGMENT = "requirement_fragment"
    REQUIREMENT_FLOW = "requirement_flow"


class TraceEvidenceKind(StrEnum):
    TEXT_MATCH = "text_match"
    TOKEN_MATCH = "token_match"
    STRUCTURAL_MATCH = "structural_match"
    TRANSITION_PATH = "transition_path"
    OBSERVATION = "observation"
    OTHER = "other"
