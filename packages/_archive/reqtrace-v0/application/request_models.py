"""Application request/input snapshot models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from reqtrace.application.exceptions import InvalidTraceabilityRequestError
from reqtrace.domain.evidence.models import (
    Action,
    ApplicationState,
    Attachment,
    EvidenceArtifact,
    ExecutionRun,
    Observation,
    Transition,
    UIElement,
)
from reqtrace.domain.requirements.models import (
    RequirementArtifact,
    RequirementDocument,
    RequirementFlow,
    RequirementFlowEdge,
    RequirementFragment,
)


class RequirementSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    documents: list[RequirementDocument] = Field(default_factory=list)
    requirements: list[RequirementArtifact] = Field(default_factory=list)
    fragments: list[RequirementFragment] = Field(default_factory=list)
    flows: list[RequirementFlow] = Field(default_factory=list)
    flow_edges: list[RequirementFlowEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "RequirementSnapshot":
        requirement_ids = [item.id for item in self.requirements]
        fragment_ids = [item.id for item in self.fragments]
        flow_ids = [item.id for item in self.flows]
        flow_edge_ids = [item.id for item in self.flow_edges]
        document_ids = [item.id for item in self.documents]

        _ensure_unique(requirement_ids, "requirement")
        _ensure_unique(fragment_ids, "fragment")
        _ensure_unique(flow_ids, "flow")
        _ensure_unique(flow_edge_ids, "flow edge")
        _ensure_unique(document_ids, "document")

        requirement_set = set(requirement_ids)
        fragment_set = set(fragment_ids)
        document_set = set(document_ids)
        fragment_requirement = {item.id: item.requirement_id for item in self.fragments}

        for requirement in self.requirements:
            if requirement.document_id and requirement.document_id not in document_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown document_id for requirement: {requirement.document_id}"
                )

        for fragment in self.fragments:
            if fragment.requirement_id not in requirement_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown requirement_id for fragment: {fragment.requirement_id}"
                )

        for flow in self.flows:
            if flow.requirement_id not in requirement_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown requirement_id for flow: {flow.requirement_id}"
                )
            if flow.entry_fragment_id and flow.entry_fragment_id not in fragment_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown entry_fragment_id for flow: {flow.entry_fragment_id}"
                )
            if flow.entry_fragment_id:
                owner = fragment_requirement[flow.entry_fragment_id]
                if owner != flow.requirement_id:
                    raise InvalidTraceabilityRequestError(
                        "Flow entry fragment belongs to another requirement: "
                        f"{flow.entry_fragment_id}"
                    )

        for edge in self.flow_edges:
            if edge.requirement_id not in requirement_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown requirement_id for flow edge: {edge.requirement_id}"
                )
            if edge.from_fragment_id not in fragment_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown from_fragment_id for flow edge: {edge.from_fragment_id}"
                )
            if edge.to_fragment_id not in fragment_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown to_fragment_id for flow edge: {edge.to_fragment_id}"
                )
        return self

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "RequirementSnapshot":
        required_keys = {"requirements", "fragments", "flows", "flow_edges"}
        missing_keys = sorted(required_keys.difference(mapping))
        if missing_keys:
            raise InvalidTraceabilityRequestError(
                f"Requirement mapping is missing required keys: {', '.join(missing_keys)}"
            )
        return cls(
            documents=list(mapping.get("documents", [])),
            requirements=list(mapping["requirements"]),
            fragments=list(mapping["fragments"]),
            flows=list(mapping["flows"]),
            flow_edges=list(mapping["flow_edges"]),
        )

    def iter_requirements(self, selected_ids: list[str] | None = None) -> list[RequirementArtifact]:
        if not selected_ids:
            return list(self.requirements)
        selected_set = set(selected_ids)
        return [req for req in self.requirements if req.id in selected_set]

    def fragments_for(self, requirement_id: str) -> list[RequirementFragment]:
        return [
            fragment for fragment in self.fragments if fragment.requirement_id == requirement_id
        ]


class EvidenceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifacts: list[EvidenceArtifact] = Field(default_factory=list)
    states: list[ApplicationState] = Field(default_factory=list)
    elements: list[UIElement] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    runs: list[ExecutionRun] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "EvidenceSnapshot":
        state_ids = [item.id for item in self.states]
        element_ids = [item.id for item in self.elements]
        action_ids = [item.id for item in self.actions]
        transition_ids = [item.id for item in self.transitions]
        run_ids = [item.id for item in self.runs]
        observation_ids = [item.id for item in self.observations]
        attachment_ids = [item.id for item in self.attachments]
        artifact_ids = [item.id for item in self.artifacts]

        _ensure_unique(state_ids, "state")
        _ensure_unique(element_ids, "element")
        _ensure_unique(action_ids, "action")
        _ensure_unique(transition_ids, "transition")
        _ensure_unique(run_ids, "run")
        _ensure_unique(observation_ids, "observation")
        _ensure_unique(attachment_ids, "attachment")
        _ensure_unique(artifact_ids, "artifact")

        state_set = set(state_ids)
        element_set = set(element_ids)
        action_set = set(action_ids)
        transition_set = set(transition_ids)
        run_set = set(run_ids)
        observation_set = set(observation_ids)

        for element in self.elements:
            if element.state_id not in state_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown state_id for element: {element.state_id}"
                )
        for action in self.actions:
            if action.source_state_id and action.source_state_id not in state_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown source_state_id for action: {action.source_state_id}"
                )
            if action.target_element_id and action.target_element_id not in element_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown target_element_id for action: {action.target_element_id}"
                )
        for transition in self.transitions:
            if transition.from_state_id not in state_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown from_state_id for transition: {transition.from_state_id}"
                )
            if transition.action_id not in action_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown action_id for transition: {transition.action_id}"
                )
            if transition.to_state_id and transition.to_state_id not in state_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown to_state_id for transition: {transition.to_state_id}"
                )
            if transition.run_id and transition.run_id not in run_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown run_id for transition: {transition.run_id}"
                )
        for observation in self.observations:
            if observation.run_id not in run_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown run_id for observation: {observation.run_id}"
                )
            if observation.state_id and observation.state_id not in state_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown state_id for observation: {observation.state_id}"
                )
            if observation.transition_id and observation.transition_id not in transition_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown transition_id for observation: {observation.transition_id}"
                )
        for attachment in self.attachments:
            if attachment.run_id and attachment.run_id not in run_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown run_id for attachment: {attachment.run_id}"
                )
            if attachment.state_id and attachment.state_id not in state_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown state_id for attachment: {attachment.state_id}"
                )
            if attachment.observation_id and attachment.observation_id not in observation_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown observation_id for attachment: {attachment.observation_id}"
                )
        for artifact in self.artifacts:
            if artifact.run_id and artifact.run_id not in run_set:
                raise InvalidTraceabilityRequestError(
                    f"Unknown run_id for artifact: {artifact.run_id}"
                )
        return self

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "EvidenceSnapshot":
        required_keys = {
            "states",
            "elements",
            "actions",
            "transitions",
            "runs",
            "observations",
            "attachments",
        }
        missing_keys = sorted(required_keys.difference(mapping))
        if missing_keys:
            raise InvalidTraceabilityRequestError(
                f"Evidence mapping is missing required keys: {', '.join(missing_keys)}"
            )
        return cls(
            artifacts=list(mapping.get("artifacts", [])),
            states=list(mapping["states"]),
            elements=list(mapping["elements"]),
            actions=list(mapping["actions"]),
            transitions=list(mapping["transitions"]),
            runs=list(mapping["runs"]),
            observations=list(mapping["observations"]),
            attachments=list(mapping["attachments"]),
        )


class TraceabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method_name: str = Field(default="baseline", min_length=1)
    requirements: RequirementSnapshot
    evidence: EvidenceSnapshot
    selected_requirement_ids: list[str] = Field(default_factory=list)
    selected_evidence_run_ids: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_selected_ids(self) -> "TraceabilityRequest":
        if self.selected_requirement_ids:
            known = {req.id for req in self.requirements.requirements}
            unknown = sorted(set(self.selected_requirement_ids).difference(known))
            if unknown:
                raise InvalidTraceabilityRequestError(
                    "Unknown selected requirement ids: " + ", ".join(unknown)
                )

        if self.selected_evidence_run_ids:
            known = {run.id for run in self.evidence.runs}
            unknown = sorted(set(self.selected_evidence_run_ids).difference(known))
            if unknown:
                raise InvalidTraceabilityRequestError(
                    "Unknown selected evidence run ids: " + ", ".join(unknown)
                )
        return self


def _ensure_unique(values: list[str], label: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        raise InvalidTraceabilityRequestError(
            f"Duplicate {label} ids found: {', '.join(sorted(duplicates))}"
        )
