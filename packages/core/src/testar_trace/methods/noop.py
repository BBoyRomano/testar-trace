"""Diagnostic no-op trace method."""

from testar_trace.domain.provenance import SourceRef
from testar_trace.domain.requirement_paths import (
    PathMaterializationResult,
    materialize_requirement_paths,
)
from testar_trace.domain.requirements import RequirementSet
from testar_trace.domain.state_models import StateModelCollection
from testar_trace.domain.traceability import (
    AssessabilityStatus,
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageAssessment,
    CoverageStatus,
    TraceabilityResult,
)
from testar_trace.execution import TraceContext

__all__ = ["trace_with_noop"]

_METHOD_ID = "noop"
_RATIONALE = "No matching was attempted by the diagnostic no-op trace method."


def trace_with_noop(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    context: TraceContext,
) -> TraceabilityResult:
    """Return a valid result without performing trace matching."""
    context.raise_if_cancelled()
    context.report(
        "noop.started",
        message="No-op trace method started",
    )

    path_materialization = materialize_requirement_paths(requirements)
    context.report(
        "noop.assessing",
        message="Building diagnostic coverage assessments",
    )
    assessments = _not_assessed_scopes(
        requirements,
        state_models,
        path_materialization,
    )

    result = TraceabilityResult(
        id=_METHOD_ID,
        title="No-op traceability result",
        path_materialization=path_materialization,
        assessments=assessments,
        requirement_source_refs=_requirement_source_refs(requirements),
        state_model_source_refs=state_models.source_refs,
        metadata={
            "method": _METHOD_ID,
            "diagnostic": True,
            "matching_performed": False,
            "state_model_collection_id": state_models.id,
        },
    )

    context.raise_if_cancelled()
    context.report(
        "noop.completed",
        message="No-op trace method completed",
        completed=len(requirements.requirements),
        total=len(requirements.requirements),
    )

    return result


def _not_assessed_scopes(
    requirements: RequirementSet,
    state_models: StateModelCollection,
    path_materialization: PathMaterializationResult,
) -> tuple[CoverageAssessment, ...]:
    requirement_ids = tuple(requirement.id for requirement in requirements.requirements)
    state_model_ids = tuple(model.id for model in state_models.models)
    assessments = [
        _not_assessed(
            assessment_id=f"{_METHOD_ID}:assessment:requirement-set",
            scope_kind=AssessmentScopeKind.REQUIREMENT_SET,
            scope_id="requirements",
            requirement_ids=requirement_ids,
            state_models=state_models,
            state_model_ids=state_model_ids,
        )
    ]

    paths_by_flow_id: dict[str, list[str]] = {}
    for path in path_materialization.paths:
        paths_by_flow_id.setdefault(path.flow_id, []).append(path.id)

    for requirement in requirements.requirements:
        assessments.append(
            _not_assessed(
                assessment_id=(f"{_METHOD_ID}:assessment:requirement:{requirement.id}"),
                scope_kind=AssessmentScopeKind.REQUIREMENT,
                scope_id=requirement.id,
                requirement_ids=(requirement.id,),
                state_models=state_models,
                state_model_ids=state_model_ids,
            )
        )
        for flow in requirements.flows_for(requirement.id):
            assessments.append(
                _not_assessed(
                    assessment_id=f"{_METHOD_ID}:assessment:flow:{flow.id}",
                    scope_kind=AssessmentScopeKind.FLOW,
                    scope_id=flow.id,
                    requirement_ids=(requirement.id,),
                    state_models=state_models,
                    state_model_ids=state_model_ids,
                )
            )
            for branch in flow.branches:
                assessments.append(
                    _not_assessed(
                        assessment_id=(
                            f"{_METHOD_ID}:assessment:branch:{flow.id}:{branch.id}"
                        ),
                        scope_kind=AssessmentScopeKind.BRANCH,
                        scope_id=branch.id,
                        requirement_ids=(requirement.id,),
                        state_models=state_models,
                        state_model_ids=state_model_ids,
                    )
                )
            for path_id in paths_by_flow_id.get(flow.id, []):
                assessments.append(
                    _not_assessed(
                        assessment_id=f"{_METHOD_ID}:assessment:path:{path_id}",
                        scope_kind=AssessmentScopeKind.PATH,
                        scope_id=path_id,
                        requirement_ids=(requirement.id,),
                        state_models=state_models,
                        state_model_ids=state_model_ids,
                    )
                )

    return tuple(assessments)


def _not_assessed(
    *,
    assessment_id: str,
    scope_kind: AssessmentScopeKind,
    scope_id: str,
    requirement_ids: tuple[str, ...],
    state_models: StateModelCollection,
    state_model_ids: tuple[str, ...],
) -> CoverageAssessment:
    return CoverageAssessment(
        id=assessment_id,
        scope_kind=scope_kind,
        scope_id=scope_id,
        requirement_ids=requirement_ids,
        view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
        state_model_collection_id=state_models.id,
        state_model_ids=state_model_ids,
        status=CoverageStatus.NOT_COVERED,
        assessability=AssessabilityStatus.NONE,
        completeness=CompletenessStatus.NOT_ASSESSABLE,
        rationale=_RATIONALE,
    )


def _requirement_source_refs(
    requirements: RequirementSet,
) -> tuple[SourceRef, ...]:
    refs: list[SourceRef] = []

    for document in requirements.documents:
        if document.source_ref is not None and document.source_ref not in refs:
            refs.append(document.source_ref)

    for requirement in requirements.requirements:
        if requirement.source_ref is not None and requirement.source_ref not in refs:
            refs.append(requirement.source_ref)

    return tuple(refs)
