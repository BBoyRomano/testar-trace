from __future__ import annotations

from collections.abc import Mapping

from reqtrace.analysis.evidence_v1 import EvidenceV1Analyzer
from reqtrace.analysis.keyword_v1 import KeywordV1Analyzer
from reqtrace.analysis.occurrence_v1 import OccurrenceV1Analyzer
from reqtrace.analysis.ordered_path_v1 import OrderedPathV1Analyzer
from reqtrace.analysis.path_occurrence_v1 import PathOccurrenceV1Analyzer


_ANALYZERS: Mapping[str, object] = {
    KeywordV1Analyzer.name: KeywordV1Analyzer(),
    EvidenceV1Analyzer.name: EvidenceV1Analyzer(),
    OccurrenceV1Analyzer.name: OccurrenceV1Analyzer(),
    PathOccurrenceV1Analyzer.name: PathOccurrenceV1Analyzer(),
    OrderedPathV1Analyzer.name: OrderedPathV1Analyzer(),
}


def get_analyzer(name: str = KeywordV1Analyzer.name) -> object:
    try:
        return _ANALYZERS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported analyzer: {name}") from exc
