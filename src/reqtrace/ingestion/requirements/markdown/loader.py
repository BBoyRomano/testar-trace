from __future__ import annotations

import logging
import re
from pathlib import Path

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


class MarkdownRequirementsLoader:
    def load(self, source: str | Path) -> ParsedRequirementsSource:
        path = Path(source)
        logger.debug("Starting markdown requirements load.", extra={"source_path": str(path)})
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error(
                "Markdown requirements read failed.",
                exc_info=exc,
                extra={"source_path": str(path)},
            )
            raise SourceParseError(f"Could not read markdown source: {path}") from exc

        try:
            parsed = self.load_text(text=text, source_name="markdown", path_or_uri=str(path))
            logger.debug(
                "Completed markdown requirements load.",
                extra={"source_path": str(path), "requirement_count": len(parsed.requirements)},
            )
            return parsed
        except Exception as exc:
            logger.error(
                "Markdown requirements load failed.",
                exc_info=exc,
                extra={"source_path": str(path)},
            )
            raise

    def load_text(
        self,
        *,
        text: str,
        source_name: str = "markdown",
        path_or_uri: str | None = None,
    ) -> ParsedRequirementsSource:
        if not text.strip():
            raise SourceValidationError("Markdown source is empty.")

        lines = [line.rstrip() for line in text.splitlines()]
        title = None
        external_id = None
        actor = None
        current_section = None

        preconditions: list[str] = []
        triggers: list[str] = []
        main_steps: list[str] = []
        alternative_steps: list[str] = []
        postconditions: list[str] = []
        constraints: list[str] = []
        related_information: list[str] = []

        section_map = {
            "preconditions": preconditions,
            "trigger": triggers,
            "main flow": main_steps,
            "alternative flow": alternative_steps,
            "postconditions": postconditions,
            "constraints": constraints,
            "related information": related_information,
        }

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("# "):
                title = normalize_text(line[2:])
                continue
            if line.lower().startswith("id:"):
                external_id = normalize_text(line.split(":", 1)[1])
                continue
            if line.lower().startswith("actor:"):
                actor = normalize_text(line.split(":", 1)[1])
                continue

            lowered = line.lower().rstrip(":")
            if lowered.startswith("## "):
                section_title = lowered[3:]
                current_section = section_map.get(section_title)
                continue

            if current_section is None:
                continue

            cleaned = re.sub(r"^[-*+]\s*", "", line)
            cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)
            normalized_entry = normalize_text(cleaned)
            if normalized_entry is None:
                raise SourceValidationError("Markdown section entry must not be empty.")
            current_section.append(normalized_entry)

        if not title:
            raise SourceValidationError("Markdown source is missing a top-level title.")
        if not main_steps and not preconditions and not alternative_steps and not postconditions:
            raise SourceValidationError(
                "Markdown source does not contain any supported requirement sections."
            )

        return ParsedRequirementsSource(
            document_title=title,
            requirements=[
                ParsedRequirementRecord(
                    title=title,
                    external_id=external_id,
                    actor=actor,
                    body=None,
                    trigger=triggers[0] if triggers else None,
                    preconditions=preconditions,
                    main_steps=main_steps,
                    alternative_steps=alternative_steps,
                    alternative_flows=(
                        [
                            ParsedAlternativeFlow(
                                title="Alternative flow",
                                steps=alternative_steps,
                                postconditions=[],
                                metadata={},
                            )
                        ]
                        if alternative_steps
                        else []
                    ),
                    postconditions=postconditions,
                    constraints=constraints,
                    related_information=related_information,
                    notation=RequirementNotation.USE_CASE,
                    file_format=RequirementFormat.MARKDOWN,
                    metadata={},
                )
            ],
            source_type=SourceType.FILE,
            source_name=source_name,
            path_or_uri=path_or_uri,
        )
