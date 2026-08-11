import pytest

from testar_trace.domain.requirement_paths import PathMaterializationResult
from testar_trace.domain.requirements import (
    RequirementBranchResolution,
    RequirementPath,
    RequirementPathOutcome,
)
from testar_trace.domain.traceability import (
    AssessabilityStatus,
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageAssessment,
    CoverageStatus,
    TraceabilityResult,
    TraceEvidenceBasis,
    TraceLink,
    TraceOccurrence,
    TraceOccurrenceStatus,
    TraceTargetKind,
    TraceTargetRef,
)


def test_occurrence_is_scoped_to_one_requirement_path_and_state_model() -> None:
    occurrence = TraceOccurrence(
        id="occurrence-1",
        requirement_id="UC-04",
        flow_id="UC-04:flow",
        path_id="UC-04:path:main",
        state_model_id="model-3",
        evidence_basis=TraceEvidenceBasis.STATE_MODEL_GRAPH,
        status=TraceOccurrenceStatus.PARTIAL,
        target_path=(
            TraceTargetRef(
                kind=TraceTargetKind.TRANSITION,
                target_id="transition-1",
            ),
        ),
        covered_element_ids=("step-1",),
        missing_element_ids=("step-2",),
    )

    assert occurrence.state_model_id == "model-3"
    assert occurrence.path_id == "UC-04:path:main"


def test_sequence_occurrence_requires_a_sequence_id() -> None:
    with pytest.raises(ValueError, match="execution_sequence_id is required"):
        TraceOccurrence(
            id="occurrence-1",
            requirement_id="UC-04",
            flow_id="UC-04:flow",
            path_id="UC-04:path:main",
            state_model_id="model-3",
            evidence_basis=TraceEvidenceBasis.EXECUTION_SEQUENCE,
            status=TraceOccurrenceStatus.PARTIAL,
            target_path=(
                TraceTargetRef(kind=TraceTargetKind.STATE, target_id="state-1"),
            ),
        )


def test_collection_assessment_can_aggregate_contributions_from_models() -> None:
    assessment = CoverageAssessment(
        id="UC-04:path:main:collection",
        scope_kind=AssessmentScopeKind.PATH,
        scope_id="UC-04:path:main",
        requirement_ids=("UC-04",),
        view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
        state_model_collection_id="benchmark-models",
        state_model_ids=("model-1", "model-3"),
        status=CoverageStatus.COVERED,
        assessability=AssessabilityStatus.FULL,
        completeness=CompletenessStatus.COMPLETE,
        covered_element_ids=("step-1", "step-2"),
        coverage_ratio=1.0,
    )

    assert assessment.state_model_ids == ("model-1", "model-3")


def test_lexical_link_identifies_element_and_original_state_model() -> None:
    link = TraceLink(
        id="link-1",
        requirement_id="UC-04",
        requirement_element_id="UC-04:step-4",
        state_model_id="model-3",
        target_ref=TraceTargetRef(
            kind=TraceTargetKind.TRANSITION,
            target_id="transition-18",
        ),
        score=0.82,
        rationale="Matched tokens: cancel, registration",
    )

    assert link.requirement_element_id == "UC-04:step-4"
    assert link.state_model_id == "model-3"


def test_result_exposes_path_occurrence_and_highlight_targets() -> None:
    path = RequirementPath(
        id="UC-04:path:main",
        requirement_id="UC-04",
        flow_id="UC-04:flow",
        title="Main",
        branch_ids=("main",),
        node_ids=("node-1",),
        edge_ids=(),
        element_ids=("step-1",),
        outcome=RequirementPathOutcome.SUCCESS,
        order_index=0,
        resolution=RequirementBranchResolution.EXPLICIT,
    )
    target = TraceTargetRef(
        kind=TraceTargetKind.TRANSITION,
        target_id="transition-1",
    )
    link = TraceLink(
        id="link-1",
        requirement_id="UC-04",
        requirement_element_id="step-1",
        state_model_id="model-3",
        target_ref=target,
        score=0.9,
        occurrence_id="occurrence-1",
    )
    occurrence = TraceOccurrence(
        id="occurrence-1",
        requirement_id="UC-04",
        flow_id="UC-04:flow",
        path_id=path.id,
        state_model_id="model-3",
        evidence_basis=TraceEvidenceBasis.STATE_MODEL_GRAPH,
        status=TraceOccurrenceStatus.FULL,
        target_path=(target,),
        covered_element_ids=("step-1",),
        link_ids=(link.id,),
        score=0.9,
    )

    def complete_assessment(
        identifier: str,
        scope_kind: AssessmentScopeKind,
        scope_id: str,
    ) -> CoverageAssessment:
        return CoverageAssessment(
            id=identifier,
            scope_kind=scope_kind,
            scope_id=scope_id,
            requirement_ids=("UC-04",),
            view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
            state_model_collection_id="models",
            state_model_ids=("model-3",),
            status=CoverageStatus.COVERED,
            assessability=AssessabilityStatus.FULL,
            completeness=CompletenessStatus.COMPLETE,
            occurrence_ids=(occurrence.id,),
            covered_element_ids=("step-1",),
            coverage_ratio=1.0,
        )

    result = TraceabilityResult(
        id="result-1",
        title="Result",
        path_materialization=PathMaterializationResult(
            paths=(path,),
            bounded=False,
        ),
        assessments=(
            complete_assessment(
                "set",
                AssessmentScopeKind.REQUIREMENT_SET,
                "requirements",
            ),
            complete_assessment(
                "requirement",
                AssessmentScopeKind.REQUIREMENT,
                "UC-04",
            ),
            complete_assessment(
                "path",
                AssessmentScopeKind.PATH,
                path.id,
            ),
        ),
        links=(link,),
        occurrences=(occurrence,),
    )

    assert result.summary.overall_coverage_ratio == 1.0
    assert result.summary.complete_paths == 1
    assert result.occurrences[0].target_path == (target,)
