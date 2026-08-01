from collections import Counter

from reqtrace.ingestion.common.exceptions import IngestionValidationError
from reqtrace.ingestion.common.models import NormalizedEvidenceBatch, NormalizedRequirementBatch


def _ensure_unique_ids(values: list[str], label: str) -> None:
    duplicates = [item for item, count in Counter(values).items() if count > 1]
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise IngestionValidationError(f"Duplicate {label} ids found: {joined}")


def validate_requirement_batch(batch: NormalizedRequirementBatch) -> None:
    document_ids = [item.id for item in batch.documents]
    requirement_ids = [item.id for item in batch.requirements]
    fragment_ids = [item.id for item in batch.fragments]
    flow_ids = [item.id for item in batch.flows]
    edge_ids = [item.id for item in batch.flow_edges]

    _ensure_unique_ids(document_ids, "document")
    _ensure_unique_ids(requirement_ids, "requirement")
    _ensure_unique_ids(fragment_ids, "fragment")
    _ensure_unique_ids(flow_ids, "flow")
    _ensure_unique_ids(edge_ids, "flow edge")

    document_id_set = set(document_ids)
    requirement_id_set = set(requirement_ids)
    fragment_id_set = set(fragment_ids)
    fragment_requirement_by_id = {
        fragment.id: fragment.requirement_id for fragment in batch.fragments
    }

    for requirement in batch.requirements:
        if requirement.document_id is not None and requirement.document_id not in document_id_set:
            raise IngestionValidationError(
                f"Unknown document_id for requirement: {requirement.document_id}"
            )

    for fragment in batch.fragments:
        if fragment.requirement_id not in requirement_id_set:
            raise IngestionValidationError(
                f"Unknown requirement_id for fragment: {fragment.requirement_id}"
            )

    for flow in batch.flows:
        if flow.requirement_id not in requirement_id_set:
            raise IngestionValidationError(
                f"Unknown requirement_id for flow: {flow.requirement_id}"
            )
        if flow.entry_fragment_id is not None and flow.entry_fragment_id not in fragment_id_set:
            raise IngestionValidationError(
                f"Unknown entry_fragment_id for flow: {flow.entry_fragment_id}"
            )
        if flow.entry_fragment_id is not None:
            entry_requirement_id = fragment_requirement_by_id[flow.entry_fragment_id]
            if entry_requirement_id != flow.requirement_id:
                raise IngestionValidationError(
                    "Flow entry_fragment_id "
                    f"{flow.entry_fragment_id!r} belongs to a different requirement: "
                    f"{entry_requirement_id}"
                )

    for edge in batch.flow_edges:
        if edge.requirement_id not in requirement_id_set:
            raise IngestionValidationError(
                f"Unknown requirement_id for flow edge: {edge.requirement_id}"
            )
        if edge.from_fragment_id not in fragment_id_set:
            raise IngestionValidationError(
                f"Unknown from_fragment_id for flow edge: {edge.from_fragment_id}"
            )
        if edge.to_fragment_id not in fragment_id_set:
            raise IngestionValidationError(
                f"Unknown to_fragment_id for flow edge: {edge.to_fragment_id}"
            )
        from_requirement_id = fragment_requirement_by_id[edge.from_fragment_id]
        if from_requirement_id != edge.requirement_id:
            raise IngestionValidationError(
                "Flow edge from_fragment_id "
                f"{edge.from_fragment_id!r} belongs to a different requirement: "
                f"{from_requirement_id}"
            )
        to_requirement_id = fragment_requirement_by_id[edge.to_fragment_id]
        if to_requirement_id != edge.requirement_id:
            raise IngestionValidationError(
                "Flow edge to_fragment_id "
                f"{edge.to_fragment_id!r} belongs to a different requirement: "
                f"{to_requirement_id}"
            )


def validate_evidence_batch(batch: NormalizedEvidenceBatch) -> None:
    state_ids = [item.id for item in batch.states]
    element_ids = [item.id for item in batch.elements]
    action_ids = [item.id for item in batch.actions]
    transition_ids = [item.id for item in batch.transitions]
    run_ids = [item.id for item in batch.runs]
    observation_ids = [item.id for item in batch.observations]
    attachment_ids = [item.id for item in batch.attachments]
    artifact_ids = [item.id for item in batch.artifacts]

    _ensure_unique_ids(state_ids, "state")
    _ensure_unique_ids(element_ids, "element")
    _ensure_unique_ids(action_ids, "action")
    _ensure_unique_ids(transition_ids, "transition")
    _ensure_unique_ids(run_ids, "run")
    _ensure_unique_ids(observation_ids, "observation")
    _ensure_unique_ids(attachment_ids, "attachment")
    _ensure_unique_ids(artifact_ids, "artifact")

    state_id_set = set(state_ids)
    element_id_set = set(element_ids)
    action_id_set = set(action_ids)
    transition_id_set = set(transition_ids)
    run_id_set = set(run_ids)
    observation_id_set = set(observation_ids)

    for element in batch.elements:
        if element.state_id not in state_id_set:
            raise IngestionValidationError(f"Unknown state_id for element: {element.state_id}")

    for action in batch.actions:
        if action.source_state_id is not None and action.source_state_id not in state_id_set:
            raise IngestionValidationError(
                f"Unknown source_state_id for action: {action.source_state_id}"
            )
        if action.target_element_id is not None and action.target_element_id not in element_id_set:
            raise IngestionValidationError(
                f"Unknown target_element_id for action: {action.target_element_id}"
            )

    for transition in batch.transitions:
        if transition.from_state_id not in state_id_set:
            raise IngestionValidationError(
                f"Unknown from_state_id for transition: {transition.from_state_id}"
            )
        if transition.action_id not in action_id_set:
            raise IngestionValidationError(
                f"Unknown action_id for transition: {transition.action_id}"
            )
        if transition.to_state_id is not None and transition.to_state_id not in state_id_set:
            raise IngestionValidationError(
                f"Unknown to_state_id for transition: {transition.to_state_id}"
            )
        if transition.run_id is not None and transition.run_id not in run_id_set:
            raise IngestionValidationError(f"Unknown run_id for transition: {transition.run_id}")

    for observation in batch.observations:
        if observation.run_id not in run_id_set:
            raise IngestionValidationError(f"Unknown run_id for observation: {observation.run_id}")
        if observation.state_id is not None and observation.state_id not in state_id_set:
            raise IngestionValidationError(
                f"Unknown state_id for observation: {observation.state_id}"
            )
        if (
            observation.transition_id is not None
            and observation.transition_id not in transition_id_set
        ):
            raise IngestionValidationError(
                f"Unknown transition_id for observation: {observation.transition_id}"
            )

    for attachment in batch.attachments:
        if attachment.run_id is not None and attachment.run_id not in run_id_set:
            raise IngestionValidationError(f"Unknown run_id for attachment: {attachment.run_id}")
        if attachment.state_id is not None and attachment.state_id not in state_id_set:
            raise IngestionValidationError(
                f"Unknown state_id for attachment: {attachment.state_id}"
            )
        if (
            attachment.observation_id is not None
            and attachment.observation_id not in observation_id_set
        ):
            raise IngestionValidationError(
                f"Unknown observation_id for attachment: {attachment.observation_id}"
            )

    for artifact in batch.artifacts:
        if artifact.run_id is not None and artifact.run_id not in run_id_set:
            raise IngestionValidationError(f"Unknown run_id for artifact: {artifact.run_id}")
