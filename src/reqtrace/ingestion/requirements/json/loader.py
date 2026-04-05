from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.requirements.enums import RequirementFormat, RequirementNotation
from reqtrace.ingestion.common.exceptions import SourceParseError, SourceValidationError
from reqtrace.ingestion.common.normalization import normalize_text
from reqtrace.ingestion.requirements.models import (
    ParsedAlternativeFlow,
    ParsedRequirementRecord,
    ParsedRequirementsSource,
)

logger = logging.getLogger(__name__)


class JsonRequirementsLoader:
    def load(self, source: str | Path) -> ParsedRequirementsSource:
        path = Path(source)
        logger.debug("Starting JSON requirements load.", extra={"source_path": str(path)})
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            logger.error(
                "JSON requirements read failed.",
                exc_info=exc,
                extra={"source_path": str(path)},
            )
            raise SourceParseError(f"Could not read JSON source: {path}") from exc
        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid JSON requirements source.",
                exc_info=exc,
                extra={"source_path": str(path)},
            )
            raise SourceParseError(f"Invalid JSON requirements source: {path}") from exc

        try:
            parsed = self.load_payload(payload=payload, source_name="json", path_or_uri=str(path))
            logger.debug(
                "Completed JSON requirements load.",
                extra={"source_path": str(path), "requirement_count": len(parsed.requirements)},
            )
            return parsed
        except Exception as exc:
            logger.error(
                "JSON requirements load failed.",
                exc_info=exc,
                extra={"source_path": str(path)},
            )
            raise

    def load_payload(
        self,
        *,
        payload: dict[str, Any] | list[dict[str, Any]],
        source_name: str = "json",
        path_or_uri: str | None = None,
    ) -> ParsedRequirementsSource:
        rows: list[dict[str, Any]]
        document_title: str | None = None

        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            if isinstance(payload.get("use_cases"), list):
                rows = payload["use_cases"]
                format_name = normalize_text(str(payload.get("format") or "Use cases"))
                document_title = format_name or "Use cases"
            elif isinstance(payload.get("requirements"), list):
                rows = payload["requirements"]
                document_title = normalize_text(str(payload.get("title") or "Requirements"))
            else:
                rows = [payload]
                document_title = normalize_text(str(payload.get("title") or "Requirement"))
        else:
            raise SourceValidationError("JSON requirements payload must be an object or list.")

        requirements: list[ParsedRequirementRecord] = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise SourceValidationError(f"JSON requirements entry #{index} must be an object.")

            title = normalize_text(row.get("title") or row.get("name"))
            if title is None:
                raise SourceValidationError(
                    f"JSON requirements entry #{index} is missing a non-empty title."
                )

            alternative_flows = self._extract_alternative_flows(row.get("alternative_flows"))
            requirements.append(
                ParsedRequirementRecord(
                    title=title,
                    external_id=normalize_text(row.get("id") or row.get("external_id")),
                    actor=normalize_text(row.get("primary_actor") or row.get("actor")),
                    body=normalize_text(
                        row.get("context_of_use") or row.get("summary") or row.get("body")
                    ),
                    scope=normalize_text(row.get("scope")),
                    level=normalize_text(row.get("level")),
                    trigger=normalize_text(row.get("trigger")),
                    preconditions=self._extract_text_list(row.get("preconditions")),
                    main_steps=self._extract_text_list(
                        row.get("main_success_scenario") or row.get("main_steps")
                    ),
                    alternative_steps=[],
                    alternative_flows=alternative_flows,
                    postconditions=self._extract_text_list(row.get("postconditions")),
                    constraints=self._extract_text_list(row.get("constraints")),
                    related_information=self._extract_text_list(row.get("related_information")),
                    notation=RequirementNotation.USE_CASE,
                    file_format=RequirementFormat.JSON,
                    metadata=self._extract_metadata(row),
                )
            )

        if not requirements:
            raise SourceValidationError("JSON requirements payload is empty.")

        return ParsedRequirementsSource(
            document_title=document_title,
            requirements=requirements,
            source_type=SourceType.FILE,
            source_name=source_name,
            path_or_uri=path_or_uri,
        )

    @staticmethod
    def _extract_text_list(value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise SourceValidationError("Expected a list of strings in JSON requirements payload.")
        result: list[str] = []
        for item in value:
            normalized = normalize_text(item)
            if normalized is not None:
                result.append(normalized)
        return result

    def _extract_alternative_flows(self, value: Any) -> list[ParsedAlternativeFlow]:
        if value is None:
            return []
        if isinstance(value, list):
            if not value:
                return []
            if all(isinstance(item, str) for item in value):
                return [
                    ParsedAlternativeFlow(
                        title="Alternative flow",
                        steps=self._extract_text_list(value),
                        postconditions=[],
                        metadata={},
                    )
                ]
            flows: list[ParsedAlternativeFlow] = []
            for item in value:
                if not isinstance(item, dict):
                    raise SourceValidationError("alternative_flows entries must be objects.")
                flows.append(
                    ParsedAlternativeFlow(
                        external_id=normalize_text(item.get("id")),
                        title=normalize_text(item.get("title")),
                        steps=self._extract_text_list(item.get("steps")),
                        postconditions=self._extract_text_list(item.get("postconditions")),
                        metadata={},
                    )
                )
            return flows
        raise SourceValidationError("alternative_flows must be a list when provided.")

    @staticmethod
    def _extract_metadata(row: dict[str, Any]) -> dict[str, Any]:
        preserved_keys = {
            "stakeholders_and_interests",
            "technology_and_data_variations",
        }
        return {key: row[key] for key in preserved_keys if key in row}
