from __future__ import annotations

import logging

from reqtrace.domain.requirements.enums import (
    RequirementFlowEdgeKind,
    RequirementFlowKind,
    RequirementFragmentKind,
    RequirementKind,
)
from reqtrace.ingestion.common.exceptions import NormalizationError
from reqtrace.ingestion.common.models import (
    NormalizedRequirementBatch,
    NormalizedRequirementFlowEdgeRecord,
    NormalizedRequirementFlowRecord,
    NormalizedRequirementFragmentRecord,
    NormalizedRequirementRecord,
)
from reqtrace.ingestion.common.normalization import normalize_identifier
from reqtrace.ingestion.common.validation import validate_requirement_batch
from reqtrace.ingestion.requirements.models import ParsedRequirementsSource

logger = logging.getLogger(__name__)


class RequirementsAdapter:
    def ingest(self, parsed_source: ParsedRequirementsSource) -> NormalizedRequirementBatch:
        logger.info("Starting requirements normalization: source=%s", parsed_source.source_name)
        try:
            requirement_id = normalize_identifier(parsed_source.external_id or parsed_source.title)
            if not requirement_id:
                raise NormalizationError("Failed to derive requirement identifier.")

            requirement = NormalizedRequirementRecord(
                id=requirement_id,
                kind=RequirementKind.USE_CASE,
                title=parsed_source.title,
                external_id=parsed_source.external_id,
                actor=parsed_source.actor,
                body=parsed_source.body,
                source_type=parsed_source.source_type,
                source_name=parsed_source.source_name,
                native_id=parsed_source.external_id,
                path_or_uri=parsed_source.path_or_uri,
            )

            fragments: list[NormalizedRequirementFragmentRecord] = []
            flows: list[NormalizedRequirementFlowRecord] = []
            flow_edges: list[NormalizedRequirementFlowEdgeRecord] = []
            fragment_counter = 1

            def add_flow(name: str, flow_kind: RequirementFlowKind, items: list[str], fragment_kind: RequirementFragmentKind) -> None:
                nonlocal fragment_counter
                if not items:
                    return

                flow_id = f"{requirement_id}-{name.lower().replace(' ', '-')}"
                entry_fragment_id = None
                previous_fragment_id = None
                branch_id = "alt-1" if flow_kind == RequirementFlowKind.ALTERNATIVE else None

                for index, item in enumerate(items, start=1):
                    fragment_id = f"{requirement_id}-frag-{fragment_counter}"
                    fragment_counter += 1
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
                                id=f"{flow_id}-edge-{index-1}",
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

            add_flow("Preconditions", RequirementFlowKind.MAIN, parsed_source.preconditions, RequirementFragmentKind.PRECONDITION)
            add_flow("Main flow", RequirementFlowKind.MAIN, parsed_source.main_steps, RequirementFragmentKind.MAIN_STEP)
            add_flow("Alternative flow", RequirementFlowKind.ALTERNATIVE, parsed_source.alternative_steps, RequirementFragmentKind.ALTERNATIVE_STEP)
            add_flow("Postconditions", RequirementFlowKind.MAIN, parsed_source.postconditions, RequirementFragmentKind.POSTCONDITION)

            batch = NormalizedRequirementBatch(
                requirements=[requirement],
                fragments=fragments,
                flows=flows,
                flow_edges=flow_edges,
            )
            validate_requirement_batch(batch)
            logger.info(
                "Completed requirements normalization: requirements=%d fragments=%d flows=%d flow_edges=%d",
                len(batch.requirements),
                len(batch.fragments),
                len(batch.flows),
                len(batch.flow_edges),
            )
            return batch
        except Exception:
            logger.exception("Requirements normalization failed: source=%s", parsed_source.source_name)
            raise
