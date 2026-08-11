"""Coverage and completeness aggregation for coherent path methods."""

from collections.abc import Iterable
from dataclasses import dataclass

from testar_trace.domain.provenance import SourceRef
from testar_trace.domain.requirement_paths import PathMaterializationResult
from testar_trace.domain.requirements import RequirementPath, RequirementSet
from testar_trace.domain.state_models import StateModelCollection
from testar_trace.domain.traceability import (
    AssessabilityStatus,
    AssessmentScopeKind,
    AssessmentViewKind,
    CompletenessStatus,
    CoverageAssessment,
    CoverageStatus,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PathFinding:
    """One method's conclusion for a path in one state model."""

    path_id: str
    state_model_id: str
    assessable: bool
    occurrence_id: str | None = None
    covered_element_ids: tuple[str, ...] = ()
    missing_element_ids: tuple[str, ...] = ()
    rationale: str = ""

    @property
    def complete(self) -> bool:
        return self.assessable and not self.missing_element_ids


@dataclass(frozen=True, slots=True)
class _Scope:
    kind: AssessmentScopeKind
    id: str
    assessment_key: str
    requirement_ids: tuple[str, ...]
    element_ids: tuple[str, ...]
    paths: tuple[RequirementPath, ...]
    exhaustive: bool


def build_path_assessments(
    *,
    method_id: str,
    evidence_label: str,
    requirements: RequirementSet,
    state_models: StateModelCollection,
    materialization: PathMaterializationResult,
    findings: Iterable[PathFinding],
) -> tuple[CoverageAssessment, ...]:
    """Build path and aggregate assessments without weakening coherence."""
    finding_by_key = {
        (finding.path_id, finding.state_model_id): finding for finding in findings
    }
    assessments: list[CoverageAssessment] = []
    model_ids = tuple(model.id for model in state_models.models)

    for scope in _scopes(requirements, materialization):
        assessments.append(
            _assessment_for_scope(
                method_id=method_id,
                evidence_label=evidence_label,
                state_models=state_models,
                scope=scope,
                view_kind=AssessmentViewKind.STATE_MODEL_COLLECTION,
                state_model_ids=model_ids,
                findings=finding_by_key,
            )
        )
        for model_id in model_ids:
            assessments.append(
                _assessment_for_scope(
                    method_id=method_id,
                    evidence_label=evidence_label,
                    state_models=state_models,
                    scope=scope,
                    view_kind=AssessmentViewKind.STATE_MODEL,
                    state_model_ids=(model_id,),
                    findings=finding_by_key,
                )
            )
    return tuple(assessments)


def requirement_source_refs(requirements: RequirementSet) -> tuple[SourceRef, ...]:
    """Return unique provenance references from requirement input."""
    refs: list[SourceRef] = []
    for document in requirements.documents:
        if document.source_ref is not None and document.source_ref not in refs:
            refs.append(document.source_ref)
    for requirement in requirements.requirements:
        if requirement.source_ref is not None and requirement.source_ref not in refs:
            refs.append(requirement.source_ref)
    for element in requirements.elements:
        if element.source_ref is not None and element.source_ref not in refs:
            refs.append(element.source_ref)
    return tuple(refs)


def _assessment_for_scope(
    *,
    method_id: str,
    evidence_label: str,
    state_models: StateModelCollection,
    scope: _Scope,
    view_kind: AssessmentViewKind,
    state_model_ids: tuple[str, ...],
    findings: dict[tuple[str, str], PathFinding],
) -> CoverageAssessment:
    path_conclusions = tuple(
        _path_conclusion(path, state_model_ids, findings) for path in scope.paths
    )
    occurrence_ids = _unique(
        occurrence_id
        for conclusion in path_conclusions
        for occurrence_id in conclusion.occurrence_ids
    )
    covered = _unique(
        element_id
        for conclusion in path_conclusions
        for element_id in conclusion.covered_element_ids
        if element_id in scope.element_ids
    )
    missing = tuple(
        element_id for element_id in scope.element_ids if element_id not in covered
    )
    assessability = _assessability(path_conclusions, scope.element_ids)
    ratio = (
        len(covered) / len(scope.element_ids)
        if scope.element_ids and assessability is not AssessabilityStatus.NONE
        else None
    )
    status = _coverage_status(ratio)
    completeness = _completeness(path_conclusions, exhaustive=scope.exhaustive)
    rationale = _rationale(
        evidence_label,
        path_conclusions,
        completeness=completeness,
        exhaustive=scope.exhaustive,
    )
    view_key = (
        f"collection:{state_models.id}"
        if view_kind is AssessmentViewKind.STATE_MODEL_COLLECTION
        else f"model:{state_model_ids[0]}"
    )
    return CoverageAssessment(
        id=(
            f"{method_id}:assessment:{scope.kind.value}:"
            f"{scope.assessment_key}:{view_key}"
        ),
        scope_kind=scope.kind,
        scope_id=scope.id,
        requirement_ids=scope.requirement_ids,
        view_kind=view_kind,
        state_model_collection_id=state_models.id,
        state_model_ids=state_model_ids,
        status=status,
        assessability=assessability,
        completeness=completeness,
        occurrence_ids=occurrence_ids,
        covered_element_ids=covered,
        missing_element_ids=missing,
        coverage_ratio=ratio,
        rationale=rationale,
        metadata={
            "method": method_id,
            "path_count": len(path_conclusions),
            "complete_path_count": sum(item.complete for item in path_conclusions),
            "evidence": evidence_label,
            "path_materialization_exhaustive": scope.exhaustive,
        },
    )


@dataclass(frozen=True, slots=True)
class _PathConclusion:
    assessable: bool
    complete: bool
    occurrence_ids: tuple[str, ...]
    covered_element_ids: tuple[str, ...]


def _path_conclusion(
    path: RequirementPath,
    state_model_ids: tuple[str, ...],
    findings: dict[tuple[str, str], PathFinding],
) -> _PathConclusion:
    selected = tuple(
        finding
        for state_model_id in state_model_ids
        if (finding := findings.get((path.id, state_model_id))) is not None
    )
    assessable = any(finding.assessable for finding in selected)
    complete = any(finding.complete for finding in selected)
    return _PathConclusion(
        assessable=assessable,
        complete=complete,
        occurrence_ids=_unique(
            finding.occurrence_id
            for finding in selected
            if finding.occurrence_id is not None
        ),
        covered_element_ids=_unique(
            element_id
            for finding in selected
            for element_id in finding.covered_element_ids
        ),
    )


def _coverage_status(ratio: float | None) -> CoverageStatus:
    if ratio is None or ratio == 0.0:
        return CoverageStatus.NOT_COVERED
    if ratio == 1.0:
        return CoverageStatus.COVERED
    return CoverageStatus.PARTIALLY_COVERED


def _assessability(
    conclusions: tuple[_PathConclusion, ...],
    element_ids: tuple[str, ...],
) -> AssessabilityStatus:
    if (
        not conclusions
        or not element_ids
        or not any(item.assessable for item in conclusions)
    ):
        return AssessabilityStatus.NONE
    if all(item.assessable for item in conclusions):
        return AssessabilityStatus.FULL
    return AssessabilityStatus.PARTIAL


def _completeness(
    conclusions: tuple[_PathConclusion, ...],
    *,
    exhaustive: bool,
) -> CompletenessStatus:
    if not conclusions:
        return CompletenessStatus.NOT_ASSESSABLE
    if any(item.assessable and not item.complete for item in conclusions):
        return CompletenessStatus.INCOMPLETE
    if exhaustive and all(item.complete for item in conclusions):
        return CompletenessStatus.COMPLETE
    return CompletenessStatus.NOT_ASSESSABLE


def _rationale(
    evidence_label: str,
    conclusions: tuple[_PathConclusion, ...],
    *,
    completeness: CompletenessStatus,
    exhaustive: bool,
) -> str:
    total = len(conclusions)
    complete = sum(item.complete for item in conclusions)
    if total == 0:
        return "No materialized requirement paths are available for this scope."
    if completeness is CompletenessStatus.COMPLETE:
        return f"All {total} requirement paths have coherent {evidence_label}."
    if completeness is CompletenessStatus.INCOMPLETE:
        return (
            f"{complete} of {total} requirement paths have coherent {evidence_label}; "
            "at least one assessed path is incomplete."
        )
    if not exhaustive:
        return (
            "Completeness is not assessable because requirement-path "
            "materialization was not exhaustive."
        )
    return f"The available inputs do not permit {evidence_label} for every requirement path."


def _scopes(
    requirements: RequirementSet,
    materialization: PathMaterializationResult,
) -> tuple[_Scope, ...]:
    paths = materialization.paths
    scopes: list[_Scope] = []
    requirement_ids = tuple(requirement.id for requirement in requirements.requirements)
    all_element_ids = tuple(element.id for element in requirements.elements)
    path_element_ids = {element_id for path in paths for element_id in path.element_ids}
    scopes.append(
        _Scope(
            kind=AssessmentScopeKind.REQUIREMENT_SET,
            id="requirements",
            assessment_key="requirement-set",
            requirement_ids=requirement_ids,
            element_ids=all_element_ids,
            paths=paths,
            exhaustive=(
                materialization.is_exhaustive
                and set(all_element_ids) <= path_element_ids
            ),
        )
    )
    diagnostic_flow_ids = {item.flow_id for item in materialization.diagnostics}

    for requirement in requirements.requirements:
        requirement_flows = requirements.flows_for(requirement.id)
        requirement_flow_ids = {flow.id for flow in requirement_flows}
        requirement_paths = tuple(
            path for path in paths if path.requirement_id == requirement.id
        )
        requirement_element_ids = tuple(
            element.id for element in requirements.elements_for(requirement.id)
        )
        represented_element_ids = {
            element_id for path in requirement_paths for element_id in path.element_ids
        }
        scopes.append(
            _Scope(
                kind=AssessmentScopeKind.REQUIREMENT,
                id=requirement.id,
                assessment_key=requirement.id,
                requirement_ids=(requirement.id,),
                element_ids=requirement_element_ids,
                paths=requirement_paths,
                exhaustive=(
                    not bool(requirement_flow_ids & diagnostic_flow_ids)
                    and set(requirement_element_ids) <= represented_element_ids
                ),
            )
        )
        for flow in requirement_flows:
            flow_paths = tuple(path for path in paths if path.flow_id == flow.id)
            flow_element_ids = _unique(node.element_id for node in flow.nodes)
            scopes.append(
                _Scope(
                    kind=AssessmentScopeKind.FLOW,
                    id=flow.id,
                    assessment_key=flow.id,
                    requirement_ids=(requirement.id,),
                    element_ids=flow_element_ids,
                    paths=flow_paths,
                    exhaustive=flow.id not in diagnostic_flow_ids,
                )
            )
            for branch in flow.branches:
                scopes.append(
                    _Scope(
                        kind=AssessmentScopeKind.BRANCH,
                        id=branch.id,
                        assessment_key=f"{flow.id}:{branch.id}",
                        requirement_ids=(requirement.id,),
                        element_ids=_unique(
                            node.element_id
                            for node in flow.nodes
                            if node.branch_id == branch.id
                        ),
                        paths=tuple(
                            path for path in flow_paths if branch.id in path.branch_ids
                        ),
                        exhaustive=flow.id not in diagnostic_flow_ids,
                    )
                )

    for path in paths:
        scopes.append(
            _Scope(
                kind=AssessmentScopeKind.PATH,
                id=path.id,
                assessment_key=path.id,
                requirement_ids=(path.requirement_id,),
                element_ids=_unique(path.element_ids),
                paths=(path,),
                exhaustive=True,
            )
        )
    return tuple(scopes)


def _unique[T](values: Iterable[T]) -> tuple[T, ...]:
    return tuple(dict.fromkeys(values))
