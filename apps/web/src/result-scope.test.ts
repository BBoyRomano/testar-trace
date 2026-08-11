import { describe, expect, it } from "vite-plus/test";

import {
  bestEvidenceStateModelId,
  filterResultRequirementIds,
  linksForScope,
  occurrenceTargetEvidence,
  occurrencesForScope,
  pathAccentIndex,
  pathBranchKind,
  requirementElementTone,
  resolveResultScope,
  strongestTargetScores,
  strongestTargetStepNumbers,
  strongestTargetTones,
} from "./result-scope.ts";
import type { AnalysisResult, RequirementItem } from "./types.ts";

const result = {
  paths: [
    {
      id: "path-1",
      requirementId: "REQ-1",
      flowId: "flow-1",
      title: "Main",
      branchIds: ["main"],
      elementIds: ["step-1"],
      outcome: "success",
      orderIndex: 0,
      resolution: "explicit",
    },
  ],
  links: [
    {
      id: "link-1",
      requirementId: "REQ-1",
      requirementElementId: "step-1",
      stateModelId: "model-1",
      target: { kind: "transition", targetId: "transition-1" },
      score: 0.42,
      occurrenceId: null,
      rationale: "",
    },
    {
      id: "link-2",
      requirementId: "REQ-1",
      requirementElementId: "step-2",
      stateModelId: "model-1",
      target: { kind: "transition", targetId: "transition-1" },
      score: 0.91,
      occurrenceId: null,
      rationale: "",
    },
  ],
} as AnalysisResult;

describe("result scope", () => {
  it("restricts lexical links to elements on a selected requirement path", () => {
    const scope = resolveResultScope(result, "REQ-1", "path-1");
    expect(linksForScope(result, scope, "model-1").map((item) => item.id)).toEqual(["link-1"]);
  });

  it("resolves authored flow, branch, and step scopes without inventing new assessments", () => {
    const branchScope = resolveResultScope(result, "REQ-1", "main", "", "branch", requirement);
    expect(branchScope).toMatchObject({
      kind: "branch",
      assessmentKind: "branch",
      assessmentId: "main",
    });
    expect([...branchScope.elementIds!]).toEqual(["step-1"]);

    const stepScope = resolveResultScope(result, "REQ-1", "flow-1", "step-1", "flow", requirement);
    expect(stepScope).toMatchObject({
      kind: "element",
      assessmentKind: "flow",
      assessmentId: "flow-1",
    });
    expect(linksForScope(result, stepScope, "model-1").map((item) => item.id)).toEqual(["link-1"]);
  });

  it("uses the strongest score for each highlighted target", () => {
    const scope = resolveResultScope(result, "REQ-1", "");
    const scores = strongestTargetScores(linksForScope(result, scope, "model-1"));
    expect(scores.get("transition:transition-1")).toBe(0.91);
  });

  it("associates highlighted targets with their resolved-path step numbers", () => {
    const numberedRequirement = {
      ...requirement,
      elements: requirement.elements.map((element) =>
        element.id === "step-1" ? { ...element, kind: "main_step" } : element,
      ),
    };
    const numbers = strongestTargetStepNumbers(result.links, result, numberedRequirement);
    expect(numbers.get("transition:transition-1")).toEqual([1]);
  });

  it("builds graph evidence only from an ordered occurrence", () => {
    const numberedRequirement = {
      ...requirement,
      elements: requirement.elements.map((element) =>
        element.id === "step-1" ? { ...element, kind: "main_step" } : element,
      ),
    };
    const occurrenceResult = {
      ...result,
      occurrences: [
        {
          id: "occurrence-1",
          requirementId: "REQ-1",
          flowId: "flow-1",
          pathId: "path-1",
          stateModelId: "model-1",
          evidenceBasis: "state-model-graph",
          status: "full",
          score: 0.8,
          targetPath: [{ kind: "transition", targetId: "transition-1" }],
          coveredElementIds: ["step-1"],
          missingElementIds: [],
          linkIds: ["link-1"],
        },
      ],
    } as AnalysisResult;
    const scope = resolveResultScope(occurrenceResult, "REQ-1", "");
    const occurrences = occurrencesForScope(occurrenceResult, scope, "model-1");
    const evidence = occurrenceTargetEvidence(occurrenceResult, occurrences, numberedRequirement);

    expect(evidence.scores.get("transition:transition-1")).toBe(0.8);
    expect(evidence.markers.get("transition:transition-1")).toEqual(["1"]);
    expect(evidence.directTargets.has("transition:transition-1")).toBe(true);
    expect(evidence.tones.get("transition:transition-1")).toBe(0);
    expect(occurrenceTargetEvidence(result, [], numberedRequirement).scores.size).toBe(0);
  });

  it("chooses the strongest evidence model for the selected scope", () => {
    const occurrenceResult = {
      ...result,
      occurrences: [
        {
          id: "partial-occurrence",
          requirementId: "REQ-1",
          flowId: "flow-1",
          pathId: "path-1",
          stateModelId: "model-1",
          status: "partial",
          score: 0.95,
          targetPath: [],
          coveredElementIds: ["step-1"],
          missingElementIds: [],
          linkIds: [],
        },
        {
          id: "full-occurrence",
          requirementId: "REQ-1",
          flowId: "flow-1",
          pathId: "path-1",
          stateModelId: "model-2",
          status: "full",
          score: 0.7,
          targetPath: [],
          coveredElementIds: ["step-1"],
          missingElementIds: [],
          linkIds: [],
        },
      ],
    } as AnalysisResult;
    const scope = resolveResultScope(occurrenceResult, "REQ-1", "path-1");

    expect(bestEvidenceStateModelId(occurrenceResult, scope, ["model-1", "model-2"])).toBe(
      "model-2",
    );
  });

  it("projects a shared action only onto its selected route transition", () => {
    const numberedRequirement = {
      ...requirement,
      elements: requirement.elements.map((element) =>
        element.id === "step-1" ? { ...element, kind: "main_step" } : element,
      ),
    };
    const actionResult = {
      ...result,
      links: [
        {
          ...result.links[0]!,
          id: "action-link",
          target: { kind: "action", targetId: "shared-action" },
          occurrenceId: "action-occurrence",
          metadata: { route_transition_id: "chosen-transition" },
        },
      ],
      occurrences: [
        {
          id: "action-occurrence",
          requirementId: "REQ-1",
          flowId: "flow-1",
          pathId: "path-1",
          stateModelId: "model-1",
          status: "full",
          score: 0.8,
          targetPath: [
            { kind: "transition", targetId: "chosen-transition" },
            { kind: "action", targetId: "shared-action" },
          ],
          coveredElementIds: ["step-1"],
          missingElementIds: [],
          linkIds: ["action-link"],
        },
      ],
    } as AnalysisResult;
    const sharedActionModel = {
      id: "model-1",
      title: "Shared action model",
      layer: "abstract",
      entities: [],
      counts: { state: 3, widget: 0, action: 1, transition: 2 },
      graph: {
        nodes: [
          { id: "source-a", label: "Source A", initial: true },
          { id: "source-b", label: "Source B", initial: false },
          { id: "target", label: "Target", initial: false },
        ],
        edges: [
          {
            id: "chosen-transition",
            source: "source-a",
            target: "target",
            label: "Continue",
            actionId: "shared-action",
          },
          {
            id: "other-transition",
            source: "source-b",
            target: "target",
            label: "Continue",
            actionId: "shared-action",
          },
        ],
      },
    };
    const evidence = occurrenceTargetEvidence(
      actionResult,
      actionResult.occurrences,
      numberedRequirement,
      null,
      sharedActionModel,
    );

    expect(evidence.markers.get("transition:chosen-transition")).toEqual(["1"]);
    expect(evidence.directTargets.has("transition:chosen-transition")).toBe(true);
    expect(evidence.markers.has("action:shared-action")).toBe(false);
    expect(evidence.scores.has("transition:other-transition")).toBe(false);
  });

  it("labels direct evidence for conditions, triggers, flow steps, and postconditions", () => {
    const kinds = ["constraint", "precondition", "trigger", "main_step", "postcondition"];
    const targets = [
      { kind: "widget", targetId: "widget-1" },
      { kind: "state", targetId: "state-entry" },
      { kind: "transition", targetId: "transition-trigger" },
      { kind: "action", targetId: "action-step" },
      { kind: "state", targetId: "state-exit" },
    ];
    const requirementWithObligations: RequirementItem = {
      ...requirement,
      elements: kinds.map((kind, index) => ({
        id: `element-${index}`,
        requirementId: requirement.id,
        kind,
        text: kind,
        orderIndex: index,
      })),
    };
    const obligationResult = {
      ...result,
      paths: [
        {
          ...result.paths[0]!,
          elementIds: requirementWithObligations.elements.map((element) => element.id),
        },
      ],
      links: targets.map((target, index) => ({
        ...result.links[0]!,
        id: `obligation-link-${index}`,
        requirementElementId: `element-${index}`,
        target,
        occurrenceId: "obligation-occurrence",
      })),
      occurrences: [
        {
          id: "obligation-occurrence",
          requirementId: requirement.id,
          flowId: "flow-1",
          pathId: "path-1",
          stateModelId: "model-1",
          status: "full",
          score: 0.9,
          targetPath: targets,
          coveredElementIds: requirementWithObligations.elements.map((element) => element.id),
          missingElementIds: [],
          linkIds: targets.map((_, index) => `obligation-link-${index}`),
        },
      ],
    } as AnalysisResult;

    const evidence = occurrenceTargetEvidence(
      obligationResult,
      obligationResult.occurrences,
      requirementWithObligations,
    );

    expect(evidence.markers.get("widget:widget-1")).toEqual(["Constraint"]);
    expect(evidence.markers.get("state:state-entry")).toEqual(["Pre"]);
    expect(evidence.markers.get("transition:transition-trigger")).toEqual(["Trigger"]);
    expect(evidence.markers.get("action:action-step")).toEqual(["1"]);
    expect(evidence.markers.get("state:state-exit")).toEqual(["Post"]);
    expect([...evidence.directTargets].every((target) => evidence.tones.get(target) === 0)).toBe(
      true,
    );
  });

  it("classifies requirement paths by their most specific authored flow", () => {
    const path = result.paths[0]!;
    expect(pathBranchKind(path, branchedRequirement)).toBe("main");
    expect(
      pathBranchKind({ ...path, branchIds: ["main", "alternative"] }, branchedRequirement),
    ).toBe("alternative");
    expect(pathBranchKind({ ...path, branchIds: ["main", "exception"] }, branchedRequirement)).toBe(
      "exception",
    );
  });

  it("uses a stable color for paths sharing their first alternative branch", () => {
    const path = result.paths[0]!;
    expect(pathAccentIndex(path, branchedRequirement)).toBe(0);
    expect(
      pathAccentIndex({ ...path, branchIds: ["main", "alternative"] }, branchedRequirement),
    ).toBe(1);
  });

  it("uses nine alternative tones before cycling without changing the main tone", () => {
    const manyBranches: RequirementItem = {
      ...branchedRequirement,
      flows: branchedRequirement.flows.map((flow) => ({
        ...flow,
        branches: [
          flow.branches[0]!,
          ...Array.from({ length: 10 }, (_, index) => ({
            id: `alternative-${index + 1}`,
            title: `Alternative ${index + 1}`,
            kind: "alternative" as const,
            entryNodeId: "node-1",
            orderIndex: index + 1,
            resolution: "explicit" as const,
          })),
        ],
      })),
    };
    const path = result.paths[0]!;

    expect(pathAccentIndex({ ...path, branchIds: ["main", "alternative-9"] }, manyBranches)).toBe(
      9,
    );
    expect(pathAccentIndex({ ...path, branchIds: ["main", "alternative-10"] }, manyBranches)).toBe(
      1,
    );
    expect(pathAccentIndex(path, manyBranches)).toBe(0);
  });

  it("gives the main path color precedence over later alternative paths", () => {
    const coloredRequirement: RequirementItem = {
      ...branchedRequirement,
      elements: [
        {
          id: "main-step",
          requirementId: "REQ-1",
          kind: "main_step",
          text: "Continue",
          orderIndex: 0,
        },
        {
          id: "alt-step",
          requirementId: "REQ-1",
          kind: "alternative_step",
          text: "Cancel",
          orderIndex: 1,
        },
      ],
    };
    const coloredResult = {
      ...result,
      paths: [
        {
          ...result.paths[0]!,
          id: "path-main",
          branchIds: ["main"],
          elementIds: ["main-step"],
          orderIndex: 0,
        },
        {
          ...result.paths[0]!,
          id: "path-alternative",
          branchIds: ["main", "alternative"],
          elementIds: ["alt-step"],
          orderIndex: 1,
        },
      ],
      links: [
        {
          ...result.links[0]!,
          requirementElementId: "main-step",
          occurrenceId: "occurrence-main",
          score: 0.3,
        },
        {
          ...result.links[1]!,
          requirementElementId: "alt-step",
          occurrenceId: "occurrence-alternative",
          score: 0.9,
        },
      ],
      occurrences: [
        {
          id: "occurrence-alternative",
          requirementId: "REQ-1",
          flowId: "flow-1",
          pathId: "path-alternative",
          stateModelId: "model-1",
          status: "full",
          score: 0.9,
          targetPath: [{ kind: "transition", targetId: "transition-1" }],
          coveredElementIds: ["alt-step"],
          missingElementIds: [],
          linkIds: ["link-2"],
        },
        {
          id: "occurrence-main",
          requirementId: "REQ-1",
          flowId: "flow-1",
          pathId: "path-main",
          stateModelId: "model-1",
          status: "full",
          score: 0.3,
          targetPath: [{ kind: "transition", targetId: "transition-1" }],
          coveredElementIds: ["main-step"],
          missingElementIds: [],
          linkIds: ["link-1"],
        },
      ],
    } as AnalysisResult;

    expect(requirementElementTone(coloredResult, coloredRequirement, "main-step")).toBe(0);
    expect(requirementElementTone(coloredResult, coloredRequirement, "alt-step")).toBe(1);
    expect(
      strongestTargetTones(coloredResult.links, coloredResult, coloredRequirement).get(
        "transition:transition-1",
      ),
    ).toBe(0);
    const occurrenceEvidence = occurrenceTargetEvidence(
      coloredResult,
      coloredResult.occurrences,
      coloredRequirement,
    );
    expect(occurrenceEvidence.scores.get("transition:transition-1")).toBe(0.9);
    expect(occurrenceEvidence.tones.get("transition:transition-1")).toBe(0);
    expect(occurrenceEvidence.priorities.get("transition:transition-1")).toBe(0);

    const branchingResult = {
      ...coloredResult,
      paths: [
        {
          ...coloredResult.paths[1]!,
          id: "path-branching",
          elementIds: ["main-step", "alt-step"],
        },
      ],
      links: [
        {
          ...coloredResult.links[0]!,
          target: { kind: "transition", targetId: "transition-main" },
          occurrenceId: "occurrence-branching",
        },
        {
          ...coloredResult.links[1]!,
          target: { kind: "transition", targetId: "transition-alternative" },
          occurrenceId: "occurrence-branching",
        },
      ],
      occurrences: [
        {
          ...coloredResult.occurrences[0]!,
          id: "occurrence-branching",
          pathId: "path-branching",
          targetPath: [
            { kind: "transition", targetId: "transition-main" },
            { kind: "transition", targetId: "transition-branch" },
            { kind: "transition", targetId: "transition-alternative" },
          ],
          coveredElementIds: ["main-step", "alt-step"],
          linkIds: ["link-1", "link-2"],
        },
      ],
    } as AnalysisResult;
    const branchEvidence = occurrenceTargetEvidence(
      branchingResult,
      branchingResult.occurrences,
      coloredRequirement,
    );
    expect(branchEvidence.tones.get("transition:transition-main")).toBe(0);
    expect(branchEvidence.tones.get("transition:transition-branch")).toBe(1);
    expect(branchEvidence.tones.get("transition:transition-alternative")).toBe(1);
    expect(branchEvidence.markers.get("transition:transition-main")).toEqual(["1"]);
    expect(branchEvidence.markers.get("transition:transition-branch")).toBeUndefined();
    expect(branchEvidence.markers.get("transition:transition-alternative")).toEqual(["2"]);

    const alternativeStepEvidence = occurrenceTargetEvidence(
      branchingResult,
      branchingResult.occurrences,
      coloredRequirement,
      new Set(["alt-step"]),
    );
    expect(alternativeStepEvidence.scores.get("transition:transition-main")).toBeUndefined();
    expect(alternativeStepEvidence.scores.get("transition:transition-branch")).toBeUndefined();
    expect(alternativeStepEvidence.scores.get("transition:transition-alternative")).toBe(0.9);
    expect(alternativeStepEvidence.tones.get("transition:transition-alternative")).toBe(1);
    expect(alternativeStepEvidence.markers.get("transition:transition-alternative")).toEqual(["2"]);
  });

  it("searches requirements while preserving source order and filters completeness", () => {
    const second = { ...requirement, id: "REQ-2", title: "Cancel enrollment" };
    const assessments = [
      {
        scopeKind: "requirement",
        scopeId: "REQ-1",
        viewKind: "state-model-collection",
        completeness: "complete",
      },
      {
        scopeKind: "requirement",
        scopeId: "REQ-2",
        viewKind: "state-model-collection",
        completeness: "incomplete",
      },
    ] as AnalysisResult["assessments"];

    expect(
      filterResultRequirementIds({
        ids: ["REQ-2", "REQ-1"],
        requirements: [requirement, second],
        assessments,
        query: "cancel",
        filter: "all",
      }),
    ).toEqual(["REQ-2"]);
    expect(
      filterResultRequirementIds({
        ids: ["REQ-2", "REQ-1"],
        requirements: [requirement, second],
        assessments,
        query: "",
        filter: "complete",
      }),
    ).toEqual(["REQ-1"]);
  });
});

const requirement: RequirementItem = {
  id: "REQ-1",
  title: "Example",
  summary: "",
  actor: "",
  sourceName: "requirements.md",
  elements: [
    { id: "step-1", requirementId: "REQ-1", kind: "step", text: "First", orderIndex: 0 },
    { id: "step-2", requirementId: "REQ-1", kind: "step", text: "Second", orderIndex: 1 },
  ],
  flows: [
    {
      id: "flow-1",
      requirementId: "REQ-1",
      title: "Main flow",
      entryNodeId: "node-1",
      branches: [
        {
          id: "main",
          title: "Main",
          kind: "main",
          entryNodeId: "node-1",
          resolution: "explicit",
        },
      ],
      nodes: [
        {
          id: "node-1",
          branchId: "main",
          elementId: "step-1",
          outcome: "success",
        },
      ],
    },
  ],
};

const branchedRequirement: RequirementItem = {
  ...requirement,
  flows: requirement.flows.map((flow) => ({
    ...flow,
    branches: [
      ...flow.branches,
      {
        id: "alternative",
        title: "Alternative",
        kind: "alternative",
        entryNodeId: "node-1",
        resolution: "explicit",
      },
      {
        id: "exception",
        title: "Exception",
        kind: "exception",
        entryNodeId: "node-1",
        resolution: "explicit",
      },
    ],
  })),
};
