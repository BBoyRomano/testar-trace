class IngestionError(Exception):
    pass


class UnsupportedSourceError(IngestionError):
    pass


class SourceParseError(IngestionError):
    pass


class SourceValidationError(IngestionError):
    pass


class NormalizationError(IngestionError):
    pass


class IngestionValidationError(IngestionError):
    pass
