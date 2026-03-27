from reqtrace.domain.common.enum_base import StrEnum


class SourceType(StrEnum):
    FILE = "file"
    API = "api"
    IMPORT = "import"
    GENERATED = "generated"
