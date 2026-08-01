import re
import unicodedata

from reqtrace.ingestion.common.exceptions import NormalizationError


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    collapsed = " ".join(value.split())
    return collapsed or None


def normalize_identifier(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise NormalizationError(f"Failed to derive identifier from value: {value!r}")
    return normalized
