from reqtrace.domain.common.enum_base import StrEnum


class ActionKind(StrEnum):
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    NAVIGATE = "navigate"
    SUBMIT = "submit"
    OTHER = "other"


class ObservationKind(StrEnum):
    ASSERTION = "assertion"
    MESSAGE = "message"
    ERROR = "error"
    VERDICT = "verdict"
    OTHER = "other"


class AttachmentKind(StrEnum):
    SCREENSHOT = "screenshot"
    LOG = "log"
    REPORT = "report"
    EXPORT = "export"
    OTHER = "other"


class ExecutionRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
