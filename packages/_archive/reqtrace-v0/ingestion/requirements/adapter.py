from __future__ import annotations

import logging
from pathlib import Path

from reqtrace.domain.requirements.enums import (
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFragmentKind,
    RequirementKind,
    RequirementNotation,
)
from reqtrace.ingestion.common.exceptions import NormalizationError
from reqtrace.ingestion.common.models import (
    NormalizedRequirementBatch,
    NormalizedRequirementDocumentRecord,
    NormalizedRequirementFlowEdgeRecord,
    NormalizedRequirementFlowRecord,
    NormalizedRequirementFragmentRecord,
    NormalizedRequirementRecord,
)
from reqtrace.ingestion.common.normalization import normalize_identifier
from reqtrace.ingestion.common.validation import validate_requirement_batch
from reqtrace.ingestion.requirements.models import (
    ParsedAlternativeFlow,
    ParsedRequirementRecord,
    ParsedRequirementsSource,
)

logger = logging.getLogger(__name__)


class DefaultRequirementsNormalizer:
    def ingest(self, parsed_source: ParsedRequirementsSource) -> NormalizedRequirementBatch:
        logger.debug(
            "Starting requirements normalization.",
            extra={
                "source_name": parsed_source.source_name,
                "requirement_count": len(parsed_source.requirements),
            },
        )
        try:
            if not parsed_source.requirements:
                raise NormalizationError("No parsed requirements available for normalization.")

            document_hint = parsed_source.document_title or parsed_source.source_name
            if parsed_source.path_or_uri is not None:
                document_hint = Path(parsed_source.path_or_uri).stem or document_hint
            document_base = normalize_identifier(document_hint)
            if not document_base:
                raise NormalizationError("Failed to derive requirement document identifier.")
            document_id = f"{document_base}-doc"

            first_requirement = parsed_source.requirements[0]
            document = NormalizedRequirementDocumentRecord(
                id=document_id,
                title=parsed_source.document_title or first_requirement.title,
                notation=first_requirement.notation,
                file_format=first_requirement.file_format,
                source_type=parsed_source.source_type,
                source_name=parsed_source.source_name,
                native_id=first_requirement.external_id,
                path_or_uri=parsed_source.path_or_uri,
            )

            fragments: list[NormalizedRequirementFragmentRecord] = []
            flows: list[NormalizedRequirementFlowRecord] = []
            flow_edges: list[NormalizedRequirementFlowEdgeRecord] = []
            requirements: list[NormalizedRequirementRecord] = []
            used_requirement_ids: set[str] = set()

            def add_flow(
                *,
                requirement_id: str,
                name: str,
                flow_kind: RequirementFlowKind,
                items: list[str],
                fragment_kind: RequirementFragmentKind,
                branch_id: str | None = None,
            ) -> None:
                if not items:
                    return

                flow_id = f"{requirement_id}-{normalize_identifier(name) or 'flow'}"
                entry_fragment_id = None
                previous_fragment_id = None

                for index, item in enumerate(items, start=1):
                    fragment_id = f"{flow_id}-frag-{index}"
                    if entry_fragment_id is None:
                        entry_fragment_id = fragment_id

                    fragments.append(
                        NormalizedRequirementFragmentRecord(
                            id=fragment_id,
                            requirement_id=requirement_id,
                            kind=fragment_kind,
                            text=item,
                            order_index=index,
                            branch_id=branch_id,
                        )
                    )

                    if previous_fragment_id is not None:
                        flow_edges.append(
                            NormalizedRequirementFlowEdgeRecord(
                                id=f"{flow_id}-edge-{index - 1}",
                                requirement_id=requirement_id,
                                from_fragment_id=previous_fragment_id,
                                to_fragment_id=fragment_id,
                                edge_kind=RequirementFlowEdgeKind.NEXT,
                            )
                        )
                    previous_fragment_id = fragment_id

                flows.append(
                    NormalizedRequirementFlowRecord(
                        id=flow_id,
                        requirement_id=requirement_id,
                        name=name,
                        flow_kind=flow_kind,
                        entry_fragment_id=entry_fragment_id,
                    )
                )

            def unique_requirement_id(item: ParsedRequirementRecord) -> str:
                base_id = normalize_identifier(item.external_id or item.title)
                if not base_id:
                    raise NormalizationError(
                        "Failed to derive requirement identifier from title/external id."
                    )
                candidate = base_id
                suffix = 2
                while candidate in used_requirement_ids:
                    candidate = f"{base_id}-{suffix}"
                    suffix += 1
                used_requirement_ids.add(candidate)
                return candidate

            for item in parsed_source.requirements:
                requirement_id = unique_requirement_id(item)
                requirements.append(
                    NormalizedRequirementRecord(
                        id=requirement_id,
                        kind=self._kind_from_notation(item.notation),
                        title=item.title,
                        external_id=item.external_id,
                        body=item.body,
                        actor=item.actor,
                        scope=item.scope,
                        level=item.level,
                        notation=item.notation,
                        file_format=item.file_format,
                        document_id=document_id,
                        source_type=parsed_source.source_type,
                        source_name=parsed_source.source_name,
                        native_id=item.external_id,
                        path_or_uri=parsed_source.path_or_uri,
                        metadata=item.metadata,
                    )
                )

                add_flow(
                    requirement_id=requirement_id,
                    name="Preconditions",
                    flow_kind=RequirementFlowKind.MAIN,
                    items=item.preconditions,
                    fragment_kind=RequirementFragmentKind.PRECONDITION,
                )
                if item.trigger:
                    add_flow(
                        requirement_id=requirement_id,
                        name="Trigger",
                        flow_kind=RequirementFlowKind.MAIN,
                        items=[item.trigger],
                        fragment_kind=RequirementFragmentKind.TRIGGER,
                    )
                add_flow(
                    requirement_id=requirement_id,
                    name="Main flow",
                    flow_kind=RequirementFlowKind.MAIN,
                    items=item.main_steps,
                    fragment_kind=RequirementFragmentKind.MAIN_STEP,
                )
                alternative_flows = item.alternative_flows
                if not alternative_flows and item.alternative_steps:
                    alternative_flows = [
                        ParsedAlternativeFlow(
                            title="Alternative flow",
                            steps=item.alternative_steps,
                        )
                    ]
                for index, flow in enumerate(alternative_flows, start=1):
                    flow_name = flow.title or f"Alternative flow {index}"
                    flow_items = [*flow.steps, *flow.postconditions]
                    add_flow(
                        requirement_id=requirement_id,
                        name=flow_name,
                        flow_kind=RequirementFlowKind.ALTERNATIVE,
                        items=flow_items,
                        fragment_kind=RequirementFragmentKind.ALTERNATIVE_STEP,
                        branch_id=f"alt-{index}",
                    )
                add_flow(
                    requirement_id=requirement_id,
                    name="Postconditions",
                    flow_kind=RequirementFlowKind.MAIN,
                    items=item.postconditions,
                    fragment_kind=RequirementFragmentKind.POSTCONDITION,
                )
                add_flow(
                    requirement_id=requirement_id,
                    name="Constraints",
                    flow_kind=RequirementFlowKind.MAIN,
                    items=item.constraints,
                    fragment_kind=RequirementFragmentKind.CONSTRAINT,
                )
                add_flow(
                    requirement_id=requirement_id,
                    name="Related information",
                    flow_kind=RequirementFlowKind.MAIN,
                    items=item.related_information,
                    fragment_kind=RequirementFragmentKind.RELATED_INFORMATION,
                )

            batch = NormalizedRequirementBatch(
                documents=[document],
                requirements=requirements,
                fragments=fragments,
                flows=flows,
                flow_edges=flow_edges,
            )
            validate_requirement_batch(batch)
            logger.debug(
                "Completed requirements normalization.",
                extra={
                    "source_name": parsed_source.source_name,
                    "requirements": len(batch.requirements),
                    "fragments": len(batch.fragments),
                    "flows": len(batch.flows),
                    "flow_edges": len(batch.flow_edges),
                },
            )
            return batch
        except Exception as exc:
            logger.error(
                "Requirements normalization failed.",
                exc_info=exc,
                extra={"source_name": parsed_source.source_name},
            )
            raise

    @staticmethod
    def _kind_from_notation(notation: RequirementNotation) -> RequirementKind:
        if notation is RequirementNotation.USER_STORY:
            return RequirementKind.USER_STORY
        if notation is RequirementNotation.GHERKIN:
            return RequirementKind.GHERKIN_SCENARIO
        if notation is RequirementNotation.FORMAL:
            return RequirementKind.FORMAL_REQUIREMENT
        return RequirementKind.USE_CASE


# Backward-compatible alias (kept to avoid breaking existing imports).
RequirementsAdapter = DefaultRequirementsNormalizer
