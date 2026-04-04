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


class EvidenceTool(StrEnum):
    TESTAR = "testar"
    OTHER = "other"


class StateModelLayer(StrEnum):
    ABSTRACT = "abstract"
    CONCRETE = "concrete"
    SEQUENCE = "sequence"


class EvidenceArtifactKind(StrEnum):
    STATE_MODEL_JSON = "state_model_json"
    STATE_MODEL_AMP = "state_model_amp"
    ORIENTDB_EXPORT = "orientdb_export"
    RUN_OUTPUT_DIRECTORY = "run_output_directory"
    LOG_ARCHIVE = "log_archive"
    OTHER = "other"
