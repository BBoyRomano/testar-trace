import pytest

from reqtrace.ingestion.common.exceptions import NormalizationError
from reqtrace.ingestion.common.normalization import normalize_identifier, normalize_text


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  sample   text  ") == "sample text"


def test_normalize_identifier_slugifies_text() -> None:
    assert normalize_identifier(" UC.01 Login ") == "uc-01-login"


def test_normalize_identifier_rejects_empty_slug() -> None:
    with pytest.raises(NormalizationError, match="Failed to derive identifier"):
        normalize_identifier("---")
