from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from reqtrace.domain.common.enums import SourceType
from reqtrace.domain.evidence.enums import (
    ActionKind,
    EvidenceArtifactKind,
    EvidenceTool,
    ExecutionRunStatus,
    StateModelLayer,
)
from reqtrace.ingestion.common.exceptions import SourceParseError, SourceValidationError
from reqtrace.ingestion.evidence.models import (
    ParsedEvidenceAction,
    ParsedEvidenceArtifact,
    ParsedEvidenceElement,
    ParsedEvidenceRun,
    ParsedEvidenceSource,
    ParsedEvidenceState,
    ParsedEvidenceTransition,
)

logger = logging.getLogger(__name__)


class TestarLoader:
    def load(self, source: str | Path) -> ParsedEvidenceSource:
        source_path = Path(source)
        logger.debug("Starting TESTAR load.", extra={"source_path": str(source_path)})
        source_type = SourceType.DIRECTORY if source_path.is_dir() else SourceType.FILE
        if source_type is SourceType.DIRECTORY:
            run_root = source_path
            model_path = self._resolve_model_json_path(run_root)
        else:
            run_root = self._resolve_run_root_for_model_file(source_path)
            model_path = source_path

        try:
            payload = json.loads(model_path.read_text(encoding="utf-8"))
        except OSError as exc:
            logger.error(
                "TESTAR read failed.",
                exc_info=exc,
                extra={"model_path": str(model_path)},
            )
            raise SourceParseError(f"Could not read TESTAR source: {model_path}") from exc
        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid TESTAR JSON.",
                exc_info=exc,
                extra={"model_path": str(model_path)},
            )
            raise SourceParseError(f"Invalid TESTAR JSON: {model_path}") from exc

        try:
            parsed = self.load_payload(
                payload=payload,
                source_name="testar",
                path_or_uri=str(source_path),
                source_type=source_type,
                model_path_or_uri=str(model_path),
                run_folder_name=run_root.name,
            )
            parsed.artifacts.extend(
                self._discover_artifacts(
                    run=parsed.run,
                    source_name=parsed.source_name,
                    source_type=source_type,
                    source_path=source_path,
                    model_path=model_path,
                    run_root=run_root,
                )
            )
            logger.debug(
                "Completed TESTAR load.",
                extra={
                    "source_path": str(source_path),
                    "state_count": len(parsed.states),
                    "action_count": len(parsed.actions),
                    "transition_count": len(parsed.transitions),
                },
            )
            return parsed
        except Exception as exc:
            logger.error(
                "TESTAR payload validation failed.",
                exc_info=exc,
                extra={"source_path": str(source_path)},
            )
            raise

    def load_payload(
        self,
        *,
        payload: dict[str, Any],
        source_name: str = "testar",
        path_or_uri: str | None = None,
        source_type: SourceType = SourceType.FILE,
        model_path_or_uri: str | None = None,
        run_folder_name: str | None = None,
    ) -> ParsedEvidenceSource:
        if not isinstance(payload, dict):
            raise SourceValidationError("TESTAR payload must be an object.")

        states_payload = payload.get("ConcreteState")
        actions_payload = payload.get("ConcreteAction")
        transitions_payload = payload.get("ConcreteTransitions")
        if not isinstance(states_payload, list):
            raise SourceValidationError("TESTAR payload is missing list 'ConcreteState'.")
        if not isinstance(actions_payload, list):
            raise SourceValidationError("TESTAR payload is missing list 'ConcreteAction'.")
        if not isinstance(transitions_payload, list):
            raise SourceValidationError("TESTAR payload is missing list 'ConcreteTransitions'.")

        run_id = self._build_run_id(model_path_or_uri, run_folder_name)
        run = ParsedEvidenceRun(
            id=run_id,
            tool_name="TESTAR",
            tool=EvidenceTool.TESTAR,
            status=ExecutionRunStatus.COMPLETED,
            tool_run_id=run_folder_name,
            native_id=Path(model_path_or_uri).name if model_path_or_uri else None,
            state_model_layers=[
                StateModelLayer.ABSTRACT,
                StateModelLayer.CONCRETE,
                StateModelLayer.SEQUENCE,
            ],
            attributes={
                "initial_url": payload.get("InitialUrl"),
                "initial_page": payload.get("InitialPage"),
                "state_count": len(states_payload),
                "action_count": len(actions_payload),
                "transition_count": len(transitions_payload),
            },
        )

        states: list[ParsedEvidenceState] = []
        elements: list[ParsedEvidenceElement] = []
        element_lookup: dict[tuple[str, str], str] = {}

        for state_payload in states_payload:
            if not isinstance(state_payload, dict):
                raise SourceValidationError("Each TESTAR state must be an object.")
            state_id = self._required_str(
                state_payload.get("AbstractID"), "ConcreteState.AbstractID"
            )
            widget_tree = state_payload.get("WidgetTree", [])
            if not isinstance(widget_tree, list):
                raise SourceValidationError(f"WidgetTree must be a list for state {state_id!r}.")

            states.append(
                ParsedEvidenceState(
                    id=state_id,
                    tool_state_id_abstract=state_id,
                    name=state_payload.get("WebTitle") or payload.get("InitialPage"),
                    title=state_payload.get("WebTitle"),
                    url=state_payload.get("WebHref"),
                    native_id=state_id,
                    attributes=self._remaining(
                        state_payload,
                        exclude={"AbstractID", "WebTitle", "WebHref", "WidgetTree"},
                    ),
                )
            )

            for node in self._flatten_widget_tree(widget_tree):
                node_abstract_id = node.get("AbstractID")
                node_concrete_id = node.get("ConcreteID")
                node_local_id = node.get("id")
                if not any(
                    isinstance(v, str) and v.strip()
                    for v in (node_concrete_id, node_abstract_id, node_local_id)
                ):
                    continue
                element_key = self._first_non_empty(
                    node_concrete_id, node_abstract_id, node_local_id
                )
                assert element_key is not None
                element_id = f"{state_id}:{element_key}"
                if isinstance(node_abstract_id, str) and node_abstract_id.strip():
                    element_lookup[(state_id, node_abstract_id)] = element_id

                elements.append(
                    ParsedEvidenceElement(
                        id=element_id,
                        state_id=state_id,
                        tool_element_id_abstract=node_abstract_id,
                        tool_element_id_concrete=node_concrete_id,
                        tag_name=node.get("WebTagName"),
                        role=node.get("Role") or node.get("WebAriaRole") or node.get("WebType"),
                        text=node.get("WebTextContent")
                        or node.get("WebInnerText")
                        or node.get("Desc"),
                        title=node.get("WebTitle") or node.get("Title"),
                        href=node.get("WebHref"),
                        css_selector=node.get("WebCssSelector"),
                        path=node.get("Path"),
                        attributes=self._remaining(
                            node,
                            exclude={
                                "id",
                                "AbstractID",
                                "ConcreteID",
                                "WebTagName",
                                "Role",
                                "WebAriaRole",
                                "WebType",
                                "WebTextContent",
                                "WebInnerText",
                                "Desc",
                                "WebTitle",
                                "Title",
                                "WebHref",
                                "WebCssSelector",
                                "Path",
                                "children",
                            },
                        ),
                    )
                )

        actions: list[ParsedEvidenceAction] = []
        action_ids: set[str] = set()
        for action_payload in actions_payload:
            if not isinstance(action_payload, dict):
                raise SourceValidationError("Each TESTAR action must be an object.")
            action_id = self._required_str(
                action_payload.get("AbstractID"), "ConcreteAction.AbstractID"
            )
            if action_id in action_ids:
                continue
            action_ids.add(action_id)
            actions.append(
                ParsedEvidenceAction(
                    id=action_id,
                    kind=self._infer_action_kind(action_payload),
                    description=action_payload.get("Desc"),
                    tool_action_id_abstract=action_id,
                    attributes=self._remaining(
                        action_payload,
                        exclude={
                            "AbstractID",
                            "Desc",
                            "WebHref",
                            "WebCssClasses",
                            "WebTagName",
                            "WebOuterHTML",
                            "WebCssSelector",
                        },
                    )
                    | {
                        "href": action_payload.get("WebHref"),
                        "css_classes": action_payload.get("WebCssClasses"),
                        "tag_name": action_payload.get("WebTagName"),
                        "outer_html": action_payload.get("WebOuterHTML"),
                        "css_selector": action_payload.get("WebCssSelector"),
                    },
                )
            )

        transitions: list[ParsedEvidenceTransition] = []
        for index, transition_payload in enumerate(transitions_payload):
            if not isinstance(transition_payload, dict):
                raise SourceValidationError("Each TESTAR transition must be an object.")
            source_state_id = self._required_str(
                transition_payload.get("Source"), "ConcreteTransitions.Source"
            )
            target_state_id = self._required_str(
                transition_payload.get("Target"), "ConcreteTransitions.Target"
            )
            action_id = self._required_str(
                transition_payload.get("Action"), "ConcreteTransitions.Action"
            )
            transitions.append(
                ParsedEvidenceTransition(
                    id=f"tr-{index:05d}-{source_state_id}-{action_id}-{target_state_id}",
                    from_state_id=source_state_id,
                    action_id=action_id,
                    to_state_id=target_state_id,
                    run_id=run_id,
                    order_index=index,
                    attributes=self._remaining(
                        transition_payload,
                        exclude={"Source", "Target", "Action"},
                    ),
                )
            )

        # Enrich actions with a representative source state / target element
        # when a match is obvious.
        source_states_by_action: dict[str, str] = {}
        for transition in transitions:
            source_states_by_action.setdefault(transition.action_id, transition.from_state_id)
        for action in actions:
            source_state_id = source_states_by_action.get(action.id)
            if source_state_id is None:
                continue
            action.source_state_id = source_state_id
            target_element_id = element_lookup.get((source_state_id, action.id))
            if target_element_id is not None:
                action.target_element_id = target_element_id

        return ParsedEvidenceSource(
            run=run,
            states=states,
            elements=elements,
            actions=actions,
            transitions=transitions,
            observations=[],
            artifacts=[],
            source_type=source_type,
            source_name=source_name,
            path_or_uri=path_or_uri,
        )

    @staticmethod
    def _build_run_id(model_path_or_uri: str | None, run_folder_name: str | None) -> str:
        if run_folder_name is not None and run_folder_name.strip():
            return f"run-{run_folder_name.strip()}"
        if model_path_or_uri is None:
            return "testar-model-run"
        path = Path(model_path_or_uri)
        folder_name = path.parent.name.strip()
        if folder_name:
            return f"run-{folder_name}"
        return f"run-{path.stem}"

    @staticmethod
    def _resolve_model_json_path(run_root: Path) -> Path:
        candidates = [run_root / "model" / "model.json", run_root / "model.json"]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise SourceParseError(
            "Could not locate TESTAR model JSON in run directory. "
            "Expected 'model/model.json' or 'model.json'."
        )

    @staticmethod
    def _resolve_run_root_for_model_file(model_path: Path) -> Path:
        if model_path.name == "model.json" and model_path.parent.name == "model":
            return model_path.parent.parent
        return model_path.parent

    def _discover_artifacts(
        self,
        *,
        run: ParsedEvidenceRun,
        source_name: str,
        source_type: SourceType,
        source_path: Path,
        model_path: Path,
        run_root: Path,
    ) -> list[ParsedEvidenceArtifact]:
        artifacts: list[ParsedEvidenceArtifact] = []
        artifacts.append(
            ParsedEvidenceArtifact(
                id=f"{run.id}:model-json",
                kind=EvidenceArtifactKind.STATE_MODEL_JSON,
                path_or_uri=str(model_path),
                run_id=run.id,
                model_layer=StateModelLayer.CONCRETE,
                source_type=SourceType.FILE,
                native_id=model_path.name,
                metadata={"source_name": source_name},
            )
        )

        amp_path = model_path.with_suffix(".amp")
        if amp_path.is_file():
            artifacts.append(
                ParsedEvidenceArtifact(
                    id=f"{run.id}:model-amp",
                    kind=EvidenceArtifactKind.STATE_MODEL_AMP,
                    path_or_uri=str(amp_path),
                    run_id=run.id,
                    model_layer=StateModelLayer.CONCRETE,
                    source_type=SourceType.FILE,
                    native_id=amp_path.name,
                    metadata={"source_name": source_name},
                )
            )

        output_path = run_root / "output"
        if source_type is SourceType.DIRECTORY and output_path.exists():
            artifacts.append(
                ParsedEvidenceArtifact(
                    id=f"{run.id}:output",
                    kind=EvidenceArtifactKind.RUN_OUTPUT_DIRECTORY,
                    path_or_uri=str(output_path),
                    run_id=run.id,
                    model_layer=StateModelLayer.SEQUENCE,
                    source_type=SourceType.DIRECTORY,
                    native_id=output_path.name,
                    metadata={"source_name": source_name},
                )
            )

        metadata_path = run_root / "metadata.json"
        if source_type is SourceType.DIRECTORY and metadata_path.is_file():
            run.attributes["metadata_path"] = str(metadata_path)
            try:
                metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                logger.warning(
                    "Could not parse TESTAR run metadata.",
                    extra={"metadata_path": str(metadata_path)},
                )
                return artifacts
            raw_output_dir = metadata_payload.get("raw_output_dir")
            if isinstance(raw_output_dir, str) and raw_output_dir.strip():
                raw_output_path = run_root / raw_output_dir
                artifacts.append(
                    ParsedEvidenceArtifact(
                        id=f"{run.id}:raw-output",
                        kind=EvidenceArtifactKind.RUN_OUTPUT_DIRECTORY,
                        path_or_uri=str(raw_output_path),
                        run_id=run.id,
                        model_layer=StateModelLayer.SEQUENCE,
                        source_type=SourceType.DIRECTORY,
                        native_id=raw_output_path.name,
                        metadata={
                            "source_name": source_name,
                            "exists": raw_output_path.exists(),
                            "from_metadata": True,
                        },
                    )
                )

        if source_type is SourceType.FILE:
            run.attributes["source_path"] = str(source_path)

        return artifacts

    @staticmethod
    def _required_str(value: Any, field_name: str) -> str:
        if isinstance(value, str) and value.strip():
            return value
        raise SourceValidationError(f"TESTAR field {field_name!r} must be a non-empty string.")

    @staticmethod
    def _flatten_widget_tree(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        flattened: list[dict[str, Any]] = []
        stack = list(reversed(nodes))
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                flattened.append(node)
                if "children" in node:
                    children = node.get("children")
                    if not isinstance(children, list):
                        raise SourceValidationError("TESTAR widget tree 'children' must be a list.")
                    stack.extend(reversed(children))
            else:
                raise SourceValidationError("TESTAR widget tree nodes must be objects.")
        return flattened

    @staticmethod
    def _remaining(payload: dict[str, Any], *, exclude: set[str]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if key not in exclude}

    @staticmethod
    def _first_non_empty(*values: Any) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value
        return None

    @staticmethod
    def _infer_action_kind(action_payload: dict[str, Any]) -> ActionKind:
        description = str(action_payload.get("Desc") or "").lower()
        tag_name = str(action_payload.get("WebTagName") or "").lower()
        href = action_payload.get("WebHref")
        if "type" in description or "input" in description:
            return ActionKind.TYPE
        if "select" in description:
            return ActionKind.SELECT
        if "submit" in description:
            return ActionKind.SUBMIT
        if href or tag_name == "a":
            return ActionKind.NAVIGATE
        if "click" in description:
            return ActionKind.CLICK
        return ActionKind.OTHER
