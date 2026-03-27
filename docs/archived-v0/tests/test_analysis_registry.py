from reqtrace.analysis.keyword_v1 import KeywordV1Analyzer
from reqtrace.analysis.registry import get_analyzer


def test_get_default_analyzer() -> None:
    analyzer = get_analyzer()

    assert isinstance(analyzer, KeywordV1Analyzer)


def test_get_keyword_v1_analyzer() -> None:
    analyzer = get_analyzer("keyword_v1")

    assert isinstance(analyzer, KeywordV1Analyzer)
