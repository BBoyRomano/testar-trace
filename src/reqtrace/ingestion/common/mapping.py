from reqtrace.domain.common.value_objects import SourceRef
from reqtrace.domain.evidence.models import (
    Action,
    ApplicationState,
    Attachment,
    ExecutionRun,
    Observation,
    Transition,
    UIElement,
)
from reqtrace.domain.requirements.models import (
    RequirementArtifact,
    RequirementFlow,
    RequirementFlowEdge,
    RequirementFragment,
)
from reqtrace.ingestion.common.models import NormalizedEvidenceBatch, NormalizedRequirementBatch
from reqtrace.ingestion.common.provenance import build_provenance


def map_requirements_batch_to_domain(batch: NormalizedRequirementBatch):
    requirements = [
        RequirementArtifact(
            id=item.id,
            kind=item.kind,
            title=item.title,
            external_id=item.external_id,
            summary=item.summary,
            body=item.body,
            actor=item.actor,
            scope=item.scope,
            level=item.level,
            source_ref=SourceRef(
                source_type=item.source_type,
                source_name=item.source_name,
                native_id=item.native_id,
                path_or_uri=item.path_or_uri,
            ),
            provenance=build_provenance(
                source_type=item.source_type,
                source_name=item.source_name,
                native_id=item.native_id,
                path_or_uri=item.path_or_uri,
                parser_name="ingestion-mapper",
            ),
            metadata=item.metadata,
        )
        for item in batch.requirements
    ]
    fragments = [
        RequirementFragment(
            id=item.id,
            requirement_id=item.requirement_id,
            kind=item.kind,
            text=item.text,
            order_index=item.order_index,
            branch_id=item.branch_id,
            parent_fragment_id=item.parent_fragment_id,
            metadata=item.metadata,
        )
        for item in batch.fragments
    ]
    flows = [
        RequirementFlow(
            id=item.id,
            requirement_id=item.requirement_id,
            name=item.name,
            flow_kind=item.flow_kind,
            entry_fragment_id=item.entry_fragment_id,
            metadata=item.metadata,
        )
        for item in batch.flows
    ]
    flow_edges = [
        RequirementFlowEdge(
            id=item.id,
            requirement_id=item.requirement_id,
            from_fragment_id=item.from_fragment_id,
            to_fragment_id=item.to_fragment_id,
            edge_kind=item.edge_kind,
            condition_label=item.condition_label,
            metadata=item.metadata,
        )
        for item in batch.flow_edges
    ]
    return {
        "requirements": requirements,
        "fragments": fragments,
        "flows": flows,
        "flow_edges": flow_edges,
    }


def map_evidence_batch_to_domain(batch: NormalizedEvidenceBatch):
    states = [
        ApplicationState(
            id=item.id,
            tool_state_id_abstract=item.tool_state_id_abstract,
            tool_state_id_concrete=item.tool_state_id_concrete,
            name=item.name,
            title=item.title,
            url=item.url,
            dom_signature=item.dom_signature,
            source_ref=SourceRef(
                source_type=item.source_type,
                source_name=item.source_name,
                native_id=item.native_id,
                path_or_uri=item.path_or_uri,
            ),
            provenance=build_provenance(
                source_type=item.source_type,
                source_name=item.source_name,
                native_id=item.native_id,
                path_or_uri=item.path_or_uri,
                parser_name="ingestion-mapper",
            ),
            attributes=item.attributes,
        )
        for item in batch.states
    ]
    elements = [
        UIElement(
            id=item.id,
            state_id=item.state_id,
            tool_element_id_abstract=item.tool_element_id_abstract,
            tool_element_id_concrete=item.tool_element_id_concrete,
            tag_name=item.tag_name,
            role=item.role,
            text=item.text,
            title=item.title,
            href=item.href,
            css_selector=item.css_selector,
            path=item.path,
            attributes=item.attributes,
        )
        for item in batch.elements
    ]
    actions = [
        Action(
            id=item.id,
            kind=item.kind,
            description=item.description,
            tool_action_id_abstract=item.tool_action_id_abstract,
            tool_action_id_concrete=item.tool_action_id_concrete,
            source_state_id=item.source_state_id,
            target_element_id=item.target_element_id,
            attributes=item.attributes,
        )
        for item in batch.actions
    ]
    transitions = [
        Transition(
            id=item.id,
            from_state_id=item.from_state_id,
            action_id=item.action_id,
            to_state_id=item.to_state_id,
            run_id=item.run_id,
            order_index=item.order_index,
            occurred_at=item.occurred_at,
            attributes=item.attributes,
        )
        for item in batch.transitions
    ]
    runs = [
        ExecutionRun(
            id=item.id,
            tool_name=item.tool_name,
            status=item.status,
            tool_run_id=item.tool_run_id,
            sequence_number=item.sequence_number,
            started_at=item.started_at,
            ended_at=item.ended_at,
            source_ref=SourceRef(
                source_type=item.source_type,
                source_name=item.source_name,
                native_id=item.native_id,
                path_or_uri=item.path_or_uri,
            ),
            provenance=build_provenance(
                source_type=item.source_type,
                source_name=item.source_name,
                native_id=item.native_id,
                path_or_uri=item.path_or_uri,
                parser_name="ingestion-mapper",
            ),
            attributes=item.attributes,
        )
        for item in batch.runs
    ]
    observations = [
        Observation(
            id=item.id,
            run_id=item.run_id,
            kind=item.kind,
            text=item.text,
            state_id=item.state_id,
            transition_id=item.transition_id,
            observed_at=item.observed_at,
            severity=item.severity,
            attributes=item.attributes,
        )
        for item in batch.observations
    ]
    attachments = [
        Attachment(
            id=item.id,
            kind=item.kind,
            path_or_uri=item.path_or_uri,
            run_id=item.run_id,
            state_id=item.state_id,
            observation_id=item.observation_id,
            metadata=item.metadata,
        )
        for item in batch.attachments
    ]
    return {
        "states": states,
        "elements": elements,
        "actions": actions,
        "transitions": transitions,
        "runs": runs,
        "observations": observations,
        "attachments": attachments,
    }
