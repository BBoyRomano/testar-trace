from __future__ import annotations

from collections.abc import Mapping

from reqtrace.analysis.evidence_v1 import EvidenceV1Analyzer
from reqtrace.analysis.keyword_v1 import KeywordV1Analyzer


_ANALYZERS: Mapping[str, object] = {
    KeywordV1Analyzer.name: KeywordV1Analyzer(),
    EvidenceV1Analyzer.name: EvidenceV1Analyzer(),
}


def get_analyzer(name: str = KeywordV1Analyzer.name) -> object:
    try:
        return _ANALYZERS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported analyzer: {name}") from exc
