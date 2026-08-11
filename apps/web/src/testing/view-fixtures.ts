import type { AppState } from "../state.ts";
import type {
  AnalysisResult,
  AnalysisRun,
  RequirementItem,
  StateModel,
  TraceOccurrence,
} from "../types.ts";

export function resultDetailState(status: TraceOccurrence["status"]): AppState {
  const requirement = useCaseRequirement();
  const model = stateModel();
  const result: AnalysisResult = {
    schemaVersion: 1,
    id: "result-1",
    title: "Checkout completeness",
    methodId: "graph-alignment",
    methodName: "Graph alignment",
    createdAt: "2026-08-09T10:00:00Z",
    requirementsName: "checkout.md",
    stateModelsName: "model.json",
    pathsExhaustive: true,
    paths: [
      {
        id: "path-main",
        requirementId: requirement.id,
        flowId: "flow-1",
        title: "Main flow / Success",
        branchIds: ["branch-main"],
        elementIds: ["precondition-1", "trigger-1", "step-1", "step-2", "postcondition-1"],
        outcome: "success",
        orderIndex: 0,
        resolution: "explicit",
      },
    ],
    pathDiagnostics: [],
    assessments: [
      assessment("requirement", requirement.id, status === "full" ? "complete" : "incomplete"),
      assessment("path", "path-main", status === "full" ? "complete" : "incomplete"),
    ],
    links: [],
    occurrences: [
      occurrence(
        "occurrence-1",
        status,
        status === "full"
          ? ["precondition-1", "trigger-1", "step-1", "step-2", "postcondition-1"]
          : ["precondition-1", "trigger-1", "step-1"],
        status === "full" ? [] : ["step-2", "postcondition-1"],
      ),
    ],
    summary: {
      totalRequirements: 1,
      coveredRequirements: status === "full" ? 1 : 0,
      partiallyCoveredRequirements: status === "partial" ? 1 : 0,
      uncoveredRequirements: 0,
      completeRequirements: status === "full" ? 1 : 0,
      incompleteRequirements: status === "partial" ? 1 : 0,
      notAssessableRequirements: 0,
      totalPaths: 1,
      completePaths: status === "full" ? 1 : 0,
      incompletePaths: status === "partial" ? 1 : 0,
      notAssessablePaths: 0,
      totalLinks: 0,
      totalOccurrences: 1,
      overallCoverageRatio: status === "full" ? 1 : 0.5,
    },
  };
  const analysis: AnalysisRun = {
    id: "analysis-1",
    title: "Checkout completeness",
    methodId: result.methodId,
    methodName: result.methodName,
    status: "complete",
    createdAt: result.createdAt,
    progress: 1,
    message: "",
    requirements: {
      id: "requirements-1",
      name: "checkout.md",
      sourceKind: "files",
      loadedAt: result.createdAt,
      adapterId: "use-cases",
      sources: [],
      requirements: [requirement],
    },
    stateModels: {
      id: "models-1",
      name: "model.json",
      loadedAt: result.createdAt,
      adapterId: "testar",
      sources: [],
      models: [model],
    },
    result,
  };
  return {
    view: "result",
    loadState: "complete",
    catalogLoadState: "ready",
    resultsLoadState: "ready",
    requirementsFeedback: null,
    stateModelsFeedback: null,
    analysisFeedback: null,
    requirements: analysis.requirements,
    stateModels: analysis.stateModels,
    runs: [analysis],
    requirementAdapters: [],
    stateModelAdapters: [],
    methods: [{ id: result.methodId, name: result.methodName }],
    selectedMethodId: result.methodId,
    selectedRunId: analysis.id,
    selectedRequirementId: requirement.id,
    selectedResultScopeKind: "path",
    selectedResultScopeId: "path-main",
    selectedElementId: "",
    selectedStateModelId: model.id,
    resultWorkspaceTab: "graph",
    analysisQuery: "",
    analysisStatusFilter: "all",
    analysisMethodFilter: "all",
    analysisSort: "created-desc",
    analysisPage: 1,
    analysisPageSize: 10,
    selectedAnalysisIds: [],
    resultRequirementQuery: "",
    resultRequirementFilter: "all",
    requirementQuery: "",
    analysisName: "",
    renamingRunId: "",
    renameDraft: "",
  };
}

export function useCaseRequirement(): RequirementItem {
  return {
    id: "UC-01",
    title: "Complete checkout",
    summary: "A shopper completes checkout.",
    body: "**Technology and Data Variations List**\nN/A",
    actor: "Shopper",
    sourceName: "checkout.md",
    metadata: {
      technology_and_data_variations: ["N/A"],
      related_information: ["Payment policy"],
    },
    elements: [
      {
        id: "precondition-1",
        requirementId: "UC-01",
        kind: "precondition",
        text: "The shopper has items in the cart.",
        orderIndex: 0,
      },
      {
        id: "trigger-1",
        requirementId: "UC-01",
        kind: "trigger",
        text: "The shopper starts checkout.",
        orderIndex: 1,
      },
      {
        id: "step-1",
        requirementId: "UC-01",
        kind: "main_step",
        text: "The shopper reviews the cart.",
        orderIndex: 2,
      },
      {
        id: "step-2",
        requirementId: "UC-01",
        kind: "main_step",
        text: "The shopper confirms payment.",
        orderIndex: 3,
      },
      {
        id: "step-alt-1",
        requirementId: "UC-01",
        kind: "alternative_step",
        text: "The shopper chooses another payment method.",
        orderIndex: 4,
        metadata: { source_label: "5a" },
      },
      {
        id: "postcondition-1",
        requirementId: "UC-01",
        kind: "postcondition",
        text: "The order is created.",
        orderIndex: 5,
      },
    ],
    flows: [
      {
        id: "flow-1",
        requirementId: "UC-01",
        title: "Complete checkout",
        entryNodeId: "node-1",
        branches: [
          {
            id: "branch-main",
            title: "Main flow",
            kind: "main",
            entryNodeId: "node-1",
            resolution: "explicit",
          },
          {
            id: "branch-payment-declined",
            title: "Payment declined",
            kind: "alternative",
            entryNodeId: "node-alt-1",
            resolution: "explicit",
            metadata: { branch_label: "5a" },
          },
        ],
        nodes: [
          {
            id: "node-precondition",
            branchId: "branch-main",
            elementId: "precondition-1",
            outcome: null,
          },
          {
            id: "node-trigger",
            branchId: "branch-main",
            elementId: "trigger-1",
            outcome: null,
          },
          { id: "node-1", branchId: "branch-main", elementId: "step-1", outcome: null },
          { id: "node-2", branchId: "branch-main", elementId: "step-2", outcome: null },
          {
            id: "node-postcondition",
            branchId: "branch-main",
            elementId: "postcondition-1",
            outcome: "success",
          },
          {
            id: "node-alt-1",
            branchId: "branch-payment-declined",
            elementId: "step-alt-1",
            outcome: "retry",
          },
        ],
      },
    ],
  };
}

export function stateModel(): StateModel {
  return {
    id: "model-1",
    title: "model.json",
    sourceName: "model.json",
    layer: "abstract",
    entities: [],
    graph: {
      nodes: [
        { id: "state-1", label: "Cart", initial: true },
        { id: "state-2", label: "Payment", initial: false },
      ],
      edges: [
        {
          id: "transition-1",
          source: "state-1",
          target: "state-2",
          label: "Pay",
          actionId: "action-1",
        },
      ],
    },
    counts: { state: 2, widget: 0, action: 1, transition: 1 },
  };
}

export function occurrence(
  id: string,
  status: TraceOccurrence["status"],
  coveredElementIds: string[],
  missingElementIds: string[],
): TraceOccurrence {
  return {
    id,
    requirementId: "UC-01",
    flowId: "flow-1",
    pathId: "path-main",
    stateModelId: "model-1",
    status,
    score: status === "full" ? 1 : 0.5,
    targetPath: [],
    coveredElementIds,
    missingElementIds,
    linkIds: [],
  };
}

export function assessment(
  scopeKind: "requirement" | "path",
  scopeId: string,
  completeness: "complete" | "incomplete",
): AnalysisResult["assessments"][number] {
  return {
    id: `assessment-${scopeId}`,
    scopeKind,
    scopeId,
    requirementIds: ["UC-01"],
    viewKind: "state-model-collection",
    stateModelIds: ["model-1"],
    status: completeness === "complete" ? "covered" : "partially-covered",
    assessability: "full",
    completeness,
    occurrenceIds: ["occurrence-1"],
    coveredElementIds: completeness === "complete" ? ["step-1", "step-2"] : ["step-1"],
    missingElementIds: completeness === "complete" ? [] : ["step-2"],
    coverageRatio: completeness === "complete" ? 1 : 0.5,
    rationale: "Completeness is based on ordered path evidence.",
  };
}

export function analysisRun(
  completeRequirements: number,
  incompleteRequirements: number,
  notAssessableRequirements: number,
): AnalysisRun {
  const totalRequirements =
    completeRequirements + incompleteRequirements + notAssessableRequirements;
  return {
    id: "analysis-1",
    title: "Checkout",
    methodId: "lexical",
    methodName: "Lexical",
    status: "complete",
    createdAt: "2026-08-09T10:00:00Z",
    progress: 1,
    message: "",
    requirements: null,
    stateModels: null,
    result: {
      summary: {
        totalRequirements,
        completeRequirements,
        incompleteRequirements,
        notAssessableRequirements,
      },
    } as AnalysisRun["result"],
  };
}
