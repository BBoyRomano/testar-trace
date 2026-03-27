from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from reqtrace.analysis.keyword_v1 import KeywordV1Analyzer
from reqtrace.analysis.registry import get_analyzer
from reqtrace.application.events import (
    AnalysisCompleted,
    AnalysisStarted,
    RequirementAnalysisCompleted,
    RequirementAnalysisStarted,
)
from reqtrace.domain.coverage import CoverageReport
from reqtrace.ingest.requirements import load_requirement_catalog
from reqtrace.ingest.state_models import load_state_graph


@dataclass(frozen=True)
class AnalyzeCoverageRequest:
    state_path: str
    requirements_path: str
    analyzer_name: str = KeywordV1Analyzer.name


class AnalyzeCoverageUseCase:
    def execute(
        self,
        request: AnalyzeCoverageRequest,
        event_handler: Callable[[object], None] | None = None,
    ) -> CoverageReport:
        state_graph = load_state_graph(request.state_path)
        requirement_catalog = load_requirement_catalog(
            request.requirements_path)

        if event_handler is not None:
            event_handler(
                AnalysisStarted(
                    requirement_count=len(requirement_catalog.requirements),
                )
            )

        analyzer = get_analyzer(request.analyzer_name)
        report = analyzer.analyze(state_graph, requirement_catalog)

        if event_handler is not None:
            for result in report.results:
                event_handler(
                    RequirementAnalysisStarted(
                        requirement_id=result.requirement_id,
                    )
                )
                event_handler(
                    RequirementAnalysisCompleted(
                        requirement_id=result.requirement_id,
                        status=result.status.value,
                    )
                )

            event_handler(
                AnalysisCompleted(
                    requirement_count=len(requirement_catalog.requirements),
                )
            )

        return CoverageReport(
            results=report.results,
            summary=report.summary,
            metadata={
                "state_path": request.state_path,
                "requirements_path": request.requirements_path,
                "state_count": len(state_graph.states),
                "transition_count": len(state_graph.transitions),
                "requirement_count": len(requirement_catalog.requirements),
                "status": "analyzed",
                "analyzer": request.analyzer_name,
            },
        )
