from __future__ import annotations

import logging

from reqtrace.ingestion.common.models import (
    NormalizedActionRecord,
    NormalizedEvidenceBatch,
    NormalizedEvidenceElementRecord,
    NormalizedEvidenceStateRecord,
    NormalizedExecutionRunRecord,
    NormalizedObservationRecord,
    NormalizedTransitionRecord,
)
from reqtrace.ingestion.common.validation import validate_evidence_batch
from reqtrace.ingestion.evidence.models import ParsedEvidenceSource

logger = logging.getLogger(__name__)


class EvidenceAdapter:
    def ingest(self, parsed_source: ParsedEvidenceSource) -> NormalizedEvidenceBatch:
        logger.info("Starting evidence normalization: source=%s", parsed_source.source_name)
        try:
            run = NormalizedExecutionRunRecord(
                id=parsed_source.run.id,
                tool_name=parsed_source.run.tool_name,
                status=parsed_source.run.status,
                tool_run_id=parsed_source.run.tool_run_id,
                sequence_number=parsed_source.run.sequence_number,
                started_at=parsed_source.run.started_at,
                ended_at=parsed_source.run.ended_at,
                source_type=parsed_source.source_type,
                source_name=parsed_source.source_name,
                native_id=parsed_source.run.native_id,
                path_or_uri=parsed_source.path_or_uri,
                attributes=parsed_source.run.attributes,
            )

            states = [
                NormalizedEvidenceStateRecord(
                    id=item.id,
                    tool_state_id_abstract=item.tool_state_id_abstract,
                    tool_state_id_concrete=item.tool_state_id_concrete,
                    name=item.name,
                    title=item.title,
                    url=item.url,
                    dom_signature=item.dom_signature,
                    source_type=parsed_source.source_type,
                    source_name=parsed_source.source_name,
                    native_id=item.native_id,
                    path_or_uri=parsed_source.path_or_uri,
                    attributes=item.attributes,
                )
                for item in parsed_source.states
            ]

            elements = [
                NormalizedEvidenceElementRecord(
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
                for item in parsed_source.elements
            ]

            actions = [
                NormalizedActionRecord(
                    id=item.id,
                    kind=item.kind,
                    description=item.description,
                    tool_action_id_abstract=item.tool_action_id_abstract,
                    tool_action_id_concrete=item.tool_action_id_concrete,
                    source_state_id=item.source_state_id,
                    target_element_id=item.target_element_id,
                    attributes=item.attributes,
                )
                for item in parsed_source.actions
            ]

            transitions = [
                NormalizedTransitionRecord(
                    id=item.id,
                    from_state_id=item.from_state_id,
                    action_id=item.action_id,
                    to_state_id=item.to_state_id,
                    run_id=item.run_id,
                    order_index=item.order_index,
                    occurred_at=item.occurred_at,
                    attributes=item.attributes,
                )
                for item in parsed_source.transitions
            ]

            observations = [
                NormalizedObservationRecord(
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
                for item in parsed_source.observations
            ]

            batch = NormalizedEvidenceBatch(
                states=states,
                elements=elements,
                actions=actions,
                transitions=transitions,
                runs=[run],
                observations=observations,
                attachments=[],
            )
            validate_evidence_batch(batch)
            logger.info(
                "Completed evidence normalization: states=%d elements=%d actions=%d transitions=%d runs=%d observations=%d",
                len(batch.states),
                len(batch.elements),
                len(batch.actions),
                len(batch.transitions),
                len(batch.runs),
                len(batch.observations),
            )
            return batch
        except Exception:
            logger.exception("Evidence normalization failed: source=%s", parsed_source.source_name)
            raise
