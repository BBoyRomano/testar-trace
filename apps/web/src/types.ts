export type LoadState = "empty" | "ready" | "running" | "complete" | "cancelled" | "error";

export type ViewName = "analyses" | "new-analysis" | "requirements" | "state-models" | "result";

export type AnalysisStatusFilter = "all" | AnalysisRun["status"];

export type AnalysisSort = "created-desc" | "created-asc" | "name-asc" | "completeness-desc";

export type FeedbackMessage = {
  state: LoadState;
  text: string;
  presentation?: "inline" | "toast";
  action?: {
    label: string;
    action: "view-analysis";
    runId: string;
  };
};

export type AdapterDescriptor = {
  id: string;
  name: string;
  formats: string[];
};

export type MethodDescriptor = { id: string; name: string };

export type JsonValue = string | number | boolean | null | JsonValue[] | JsonObject;
export type JsonObject = { [key: string]: JsonValue };

export type RawSource = {
  id: string;
  name: string;
  format: string;
  text: string;
  uri?: string;
};

export type RequirementElement = {
  id: string;
  requirementId: string;
  kind: string;
  text: string;
  orderIndex: number | null;
  metadata?: JsonObject;
};

export type RequirementBranch = {
  id: string;
  title: string;
  kind: "main" | "alternative" | "exception";
  entryNodeId: string;
  orderIndex?: number | null;
  resolution: "explicit" | "inferred" | "ambiguous";
  metadata?: JsonObject;
};

export type RequirementFlowNode = {
  id: string;
  branchId: string;
  elementId: string;
  outcome: string | null;
};

export type RequirementFlowEdge = {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  kind: "next" | "branch" | "rejoin" | "repeat";
  branchId: string | null;
  orderIndex: number | null;
};

export type RequirementFlow = {
  id: string;
  requirementId: string;
  title: string;
  entryNodeId: string;
  branches: RequirementBranch[];
  nodes: RequirementFlowNode[];
  edges?: RequirementFlowEdge[];
  metadata?: JsonObject;
};

export type RequirementItem = {
  id: string;
  title: string;
  summary: string;
  body?: string;
  actor: string;
  scope?: string;
  level?: string;
  sourceName: string;
  metadata?: JsonObject;
  elements: RequirementElement[];
  flows: RequirementFlow[];
};

export type RequirementBundle = {
  id: string;
  name: string;
  sourceKind: "files" | "directory";
  loadedAt: string;
  adapterId: string;
  sources: RawSource[];
  requirements: RequirementItem[];
};

export type StateModelEntityKind = "state" | "widget" | "action" | "transition";

export type StateModelEntity = {
  id: string;
  kind: StateModelEntityKind;
  label: string;
  stateModelId: string;
  stateId?: string;
  actionId?: string;
  sourceStateId?: string;
  targetStateId?: string;
  title?: string;
  url?: string;
  text?: string;
  role?: string;
  tagName?: string;
  href?: string;
  cssSelector?: string;
  description?: string;
  value?: string;
  targetWidgetId?: string;
  nativeId?: string;
  sourceLocation?: string;
  metadata?: JsonObject;
};

export type StateModelGraph = {
  nodes: Array<{
    id: string;
    label: string;
    shortId?: string;
    title?: string;
    url?: string;
    initial: boolean;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    label: string;
    actionId: string;
  }>;
};

export type StateModel = {
  id: string;
  title: string;
  sourceName?: string;
  layer: string;
  entities: StateModelEntity[];
  graph: StateModelGraph;
  counts: Record<StateModelEntityKind, number>;
};

export type StateModelBundle = {
  id: string;
  name: string;
  loadedAt: string;
  adapterId: string;
  sources: RawSource[];
  models: StateModel[];
};

export type AssessmentScopeKind = "path" | "branch" | "flow" | "requirement" | "requirement-set";
export type SelectableResultScopeKind = "requirement" | "flow" | "branch" | "path";

export type CoverageStatus = "covered" | "partially-covered" | "not-covered";
export type CompletenessStatus = "complete" | "incomplete" | "not-assessable";
export type ResultRequirementFilter = "all" | CompletenessStatus;

export type RequirementPath = {
  id: string;
  requirementId: string;
  flowId: string;
  title: string;
  branchIds: string[];
  nodeIds?: string[];
  edgeIds?: string[];
  elementIds: string[];
  outcome: string;
  orderIndex: number;
  resolution: string;
  metadata?: JsonObject;
};

export type PathDiagnostic = {
  code: string;
  flowId: string;
  message: string;
  nodeId?: string | null;
  edgeId?: string | null;
};

export type CoverageAssessment = {
  id: string;
  scopeKind: AssessmentScopeKind;
  scopeId: string;
  requirementIds: string[];
  viewKind: "state-model" | "state-model-collection";
  stateModelIds: string[];
  status: CoverageStatus;
  assessability: "full" | "partial" | "none" | "unknown";
  completeness: CompletenessStatus;
  occurrenceIds: string[];
  coveredElementIds: string[];
  missingElementIds: string[];
  coverageRatio: number | null;
  rationale: string;
  metadata?: JsonObject;
};

export type TraceTargetKind =
  | "state-model"
  | "state"
  | "widget"
  | "action"
  | "transition"
  | "execution-sequence"
  | "execution-step";

export type TraceTarget = { kind: TraceTargetKind; targetId: string };

export type TraceLink = {
  id: string;
  requirementId: string;
  requirementElementId: string | null;
  stateModelId: string;
  target: TraceTarget;
  score: number;
  occurrenceId: string | null;
  rationale: string;
  metadata?: JsonObject;
};

export type TraceOccurrence = {
  id: string;
  requirementId: string;
  flowId: string;
  pathId: string;
  stateModelId: string;
  evidenceBasis?: "state-model-graph" | "execution-sequence" | "formal-model-check";
  status: "full" | "partial";
  executionSequenceId?: string | null;
  score: number | null;
  targetPath: TraceTarget[];
  coveredElementIds: string[];
  missingElementIds: string[];
  linkIds: string[];
  rationale?: string;
  metadata?: JsonObject;
};

export type AnalysisSummary = {
  totalRequirements: number;
  coveredRequirements: number;
  partiallyCoveredRequirements: number;
  uncoveredRequirements: number;
  completeRequirements: number;
  incompleteRequirements: number;
  notAssessableRequirements: number;
  totalPaths: number;
  completePaths: number;
  incompletePaths: number;
  notAssessablePaths: number;
  totalLinks: number;
  totalOccurrences: number;
  overallCoverageRatio: number | null;
};

export type AnalysisResult = {
  schemaVersion: 1;
  id: string;
  title: string;
  methodId: string;
  methodName: string;
  createdAt: string;
  requirementsName: string;
  stateModelsName: string;
  pathsExhaustive: boolean;
  paths: RequirementPath[];
  pathDiagnostics: PathDiagnostic[];
  assessments: CoverageAssessment[];
  links: TraceLink[];
  occurrences: TraceOccurrence[];
  summary: AnalysisSummary;
};

export type AnalysisRun = {
  id: string;
  title: string;
  status: "running" | "complete" | "cancelled" | "failed";
  methodId: string;
  methodName: string;
  createdAt: string;
  progress: number;
  message: string;
  progressDetail?: AnalysisProgress;
  result: AnalysisResult | null;
  requirements: RequirementBundle | null;
  stateModels: StateModelBundle | null;
};

export type AnalysisProgress = {
  phase: string;
  message: string | null;
  completed: number | null;
  total: number | null;
  metadata: JsonObject;
};

export type PortableAnalysisBundle = {
  kind: "testar-trace-analysis";
  schemaVersion: 2;
  exportedAt: string;
  analysis: {
    id: string;
    title: string;
    status: "complete";
    methodId: string;
    methodName: string;
    createdAt: string;
  };
  requirements: RequirementBundle;
  stateModels: StateModelBundle;
  result: AnalysisResult;
};

export type PortableAnalysesBundle = {
  kind: "testar-trace-analyses";
  schemaVersion: 1;
  exportedAt: string;
  analyses: PortableAnalysisBundle[];
};
