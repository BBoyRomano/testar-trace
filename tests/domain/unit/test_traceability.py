import pytest

from reqtrace.domain.traceability.enums import (
    ConfidenceLabel,
    CoverageStatus,
    CoverageSubjectType,
    EvidenceTargetType,
    LinkType,
    TraceEvidenceKind,
)
from reqtrace.domain.traceability.models import CoverageAssessment, TraceEvidence, TraceLink


def test_trace_link_can_link_fragment_to_transition() -> None:
    link = TraceLink(
        id="link-1",
        analysis_run_id="analysis-1",
        requirement_fragment_id="frag-1",
        evidence_target_type=EvidenceTargetType.TRANSITION,
        evidence_target_id="tr-1",
        link_type=LinkType.COVERS,
        score=0.9,
        confidence_label=ConfidenceLabel.HIGH,
    )

    assert link.evidence_target_type == EvidenceTargetType.TRANSITION
    assert link.confidence_label == ConfidenceLabel.HIGH


def test_coverage_assessment_supports_partial_coverage() -> None:
    coverage = CoverageAssessment(
        id="cov-1",
        analysis_run_id="analysis-1",
        subject_type=CoverageSubjectType.REQUIREMENT,
        subject_id="req-1",
        coverage_status=CoverageStatus.PARTIALLY_COVERED,
        coverage_ratio=0.5,
        confidence_ratio=0.7,
        covered_fragment_count=2,
        total_fragment_count=4,
        supporting_run_count=1,
    )

    assert coverage.coverage_status == CoverageStatus.PARTIALLY_COVERED
    assert coverage.coverage_ratio == 0.5


def test_invalid_fragment_counts_are_rejected() -> None:
    with pytest.raises(ValueError):
        CoverageAssessment(
            id="cov-1",
            analysis_run_id="analysis-1",
            subject_type=CoverageSubjectType.REQUIREMENT,
            subject_id="req-1",
            coverage_status=CoverageStatus.UNCOVERED,
            covered_fragment_count=5,
            total_fragment_count=4,
        )


def test_trace_evidence_can_be_created() -> None:
    evidence = TraceEvidence(
        id="tev-1",
        trace_link_id="link-1",
        evidence_kind=TraceEvidenceKind.TEXT_MATCH,
        matched_tokens=["sample", "action"],
    )

    assert evidence.trace_link_id == "link-1"
    assert evidence.matched_tokens == ["sample", "action"]


def test_trace_link_rejects_score_above_one() -> None:
    with pytest.raises(ValueError):
        TraceLink(
            id="link-1",
            analysis_run_id="analysis-1",
            requirement_fragment_id="frag-1",
            evidence_target_type=EvidenceTargetType.TRANSITION,
            evidence_target_id="tr-1",
            link_type=LinkType.COVERS,
            score=1.1,
        )


def test_trace_link_accepts_score_boundary_values() -> None:
    low = TraceLink(
        id="link-low",
        analysis_run_id="analysis-1",
        requirement_fragment_id="frag-1",
        evidence_target_type=EvidenceTargetType.TRANSITION,
        evidence_target_id="tr-1",
        link_type=LinkType.COVERS,
        score=0.0,
    )
    high = TraceLink(
        id="link-high",
        analysis_run_id="analysis-1",
        requirement_fragment_id="frag-1",
        evidence_target_type=EvidenceTargetType.TRANSITION,
        evidence_target_id="tr-1",
        link_type=LinkType.COVERS,
        score=1.0,
    )

    assert low.score == 0.0
    assert high.score == 1.0


def test_trace_evidence_requires_content_or_anchor() -> None:
    with pytest.raises(ValueError):
        TraceEvidence(
            id="tev-1",
            trace_link_id="link-1",
            evidence_kind=TraceEvidenceKind.TEXT_MATCH,
        )


def test_trace_evidence_with_anchor_only_is_valid() -> None:
    evidence = TraceEvidence(
        id="tev-1",
        trace_link_id="link-1",
        evidence_kind=TraceEvidenceKind.STRUCTURAL_MATCH,
        transition_id="tr-1",
    )

    assert evidence.transition_id == "tr-1"


def test_trace_evidence_with_artifact_anchor_only_is_valid() -> None:
    evidence = TraceEvidence(
        id="tev-artifact",
        trace_link_id="link-1",
        evidence_kind=TraceEvidenceKind.OTHER,
        artifact_id="artifact-1",
    )

    assert evidence.artifact_id == "artifact-1"


def test_coverage_assessment_rejects_inconsistent_covered_ratio() -> None:
    with pytest.raises(ValueError):
        CoverageAssessment(
            id="cov-1",
            analysis_run_id="analysis-1",
            subject_type=CoverageSubjectType.REQUIREMENT,
            subject_id="req-1",
            coverage_status=CoverageStatus.COVERED,
            coverage_ratio=0.0,
        )


def test_coverage_assessment_rejects_inconsistent_uncovered_ratio() -> None:
    with pytest.raises(ValueError):
        CoverageAssessment(
            id="cov-1",
            analysis_run_id="analysis-1",
            subject_type=CoverageSubjectType.REQUIREMENT,
            subject_id="req-1",
            coverage_status=CoverageStatus.UNCOVERED,
            coverage_ratio=1.0,
        )


def test_partial_trace_link_is_valid() -> None:
    link = TraceLink(
        id="link-1",
        analysis_run_id="analysis-1",
        requirement_fragment_id="frag-1",
        evidence_target_type=EvidenceTargetType.TRANSITION,
        evidence_target_id="tr-1",
        link_type=LinkType.PARTIALLY_COVERS,
    )

    assert link.link_type == LinkType.PARTIALLY_COVERS


def test_supports_trace_link_is_valid() -> None:
    link = TraceLink(
        id="link-2",
        analysis_run_id="analysis-1",
        requirement_fragment_id="frag-1",
        evidence_target_type=EvidenceTargetType.OBSERVATION,
        evidence_target_id="obs-1",
        link_type=LinkType.SUPPORTS,
    )

    assert link.link_type == LinkType.SUPPORTS


def test_trace_link_can_target_evidence_artifact() -> None:
    link = TraceLink(
        id="link-artifact",
        analysis_run_id="analysis-1",
        requirement_fragment_id="frag-1",
        evidence_target_type=EvidenceTargetType.EVIDENCE_ARTIFACT,
        evidence_target_id="artifact-1",
        link_type=LinkType.SUPPORTS,
    )

    assert link.evidence_target_type == EvidenceTargetType.EVIDENCE_ARTIFACT
