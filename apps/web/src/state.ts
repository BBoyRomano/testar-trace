import { loadRuns } from "./analysis-storage.ts";
import type {
  AdapterDescriptor,
  AnalysisRun,
  AnalysisSort,
  AnalysisStatusFilter,
  FeedbackMessage,
  LoadState,
  MethodDescriptor,
  RequirementBundle,
  ResultRequirementFilter,
  SelectableResultScopeKind,
  StateModelBundle,
  ViewName,
} from "./types.ts";

export {
  deleteRunResult,
  hydrateRunResults,
  loadRuns,
  persistRuns,
  saveRunResult,
  saveRunResults,
} from "./analysis-storage.ts";

export type AppState = {
  view: ViewName;
  loadState: LoadState;
  catalogLoadState: "loading" | "ready" | "error";
  resultsLoadState: "loading" | "ready" | "error";
  requirementsFeedback: FeedbackMessage | null;
  stateModelsFeedback: FeedbackMessage | null;
  analysisFeedback: FeedbackMessage | null;
  requirements: RequirementBundle | null;
  stateModels: StateModelBundle | null;
  runs: AnalysisRun[];
  requirementAdapters: AdapterDescriptor[];
  stateModelAdapters: AdapterDescriptor[];
  methods: MethodDescriptor[];
  selectedMethodId: string;
  selectedRunId: string;
  selectedRequirementId: string;
  selectedResultScopeKind: SelectableResultScopeKind;
  selectedResultScopeId: string;
  selectedElementId: string;
  selectedStateModelId: string;
  resultWorkspaceTab: "paths" | "graph";
  analysisQuery: string;
  analysisStatusFilter: AnalysisStatusFilter;
  analysisMethodFilter: string;
  analysisSort: AnalysisSort;
  analysisPage: number;
  analysisPageSize: number;
  selectedAnalysisIds: string[];
  resultRequirementQuery: string;
  resultRequirementFilter: ResultRequirementFilter;
  requirementQuery: string;
  analysisName: string;
  renamingRunId: string;
  renameDraft: string;
};

export function createInitialState(): AppState {
  const runs = loadRuns();
  return {
    view: "analyses",
    loadState: "empty",
    catalogLoadState: "loading",
    resultsLoadState: "loading",
    requirementsFeedback: null,
    stateModelsFeedback: null,
    analysisFeedback: null,
    requirements: null,
    stateModels: null,
    runs,
    requirementAdapters: [],
    stateModelAdapters: [],
    methods: [],
    selectedMethodId: "graph-alignment",
    selectedRunId: runs[0]?.id ?? "",
    selectedRequirementId: "",
    selectedResultScopeKind: "requirement",
    selectedResultScopeId: "",
    selectedElementId: "",
    selectedStateModelId: "",
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
