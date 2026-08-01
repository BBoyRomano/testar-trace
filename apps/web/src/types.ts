export type LoadState = "empty" | "ready" | "running" | "complete" | "error";

export type ViewName = "workspace" | "requirements" | "evidence" | "result";

export type ParserKey = {
  artifact: string;
  kind: string;
  format: string;
};

export type TraceMethodKey = string;

export type FeedbackMessage = {
  state: LoadState;
  text: string;
};

export type RequirementFragment = {
  id: string;
  requirementId: string;
  kind: string;
  text: string;
  branchId: string | null;
};

export type RequirementScenario = {
  id: string;
  requirementId: string;
  title: string;
  kind: string;
  fragmentIds: string[];
  metadata: Record<string, string | number | boolean | null>;
};

export type RequirementItem = {
  id: string;
  title: string;
  summary: string;
  actor: string;
  sourceName: string;
  fragments: RequirementFragment[];
  scenarios: RequirementScenario[];
};

export type RequirementBundle = {
  id: string;
  name: string;
  sourceKind: "file" | "directory" | "platform";
  kind: string;
  loadedAt: string;
  sources: RawSource[];
  requirements: RequirementItem[];
};

export type EvidenceBundle = {
  id: string;
  name: string;
  sourceKind: "file" | "cloud";
  kind: string;
  loadedAt: string;
  source: RawSource;
  text: string;
  stateCount: number;
  actionCount: number;
  transitionCount: number;
  elementCount: number;
  stats: Record<string, number>;
  graph: EvidenceGraph;
};

export type EvidenceGraph = {
  nodes: EvidenceGraphNode[];
  edges: EvidenceGraphEdge[];
};

export type EvidenceGraphNode = {
  id: string;
  kind: "state" | "action";
  label: string;
};

export type EvidenceGraphEdge = {
  id: string;
  kind: "transition";
  source: string;
  target: string;
  label: string;
  transitionId: string;
};

export type RawSource = {
  name: string;
  format: string;
  text: string;
};

export type ScenarioCoverage = {
  scenarioId: string;
  requirementId: string;
  title: string;
  kind: string;
  status: "covered" | "partially-covered" | "not-covered";
  coverageRatio: number;
  matchedFragments: number;
  totalFragments: number;
  sequence: SequenceStep[];
};

export type RequirementCoverage = {
  requirementId: string;
  title: string;
  status: "covered" | "partially-covered" | "not-covered";
  coverageRatio: number;
  scenarios: ScenarioCoverage[];
};

export type SequenceStep = {
  fragmentId: string;
  fragmentText: string;
  fragmentKind: string;
  evidenceId: string;
  evidenceLabel: string;
  evidenceKind: EvidenceRefKind;
  evidenceRefs: EvidenceReference[];
  score: number;
  matched: boolean;
};

export type EvidenceRefKind = "artifact" | "state" | "transition" | "action" | "element";

export type EvidenceReference = {
  kind: EvidenceRefKind;
  evidenceId: string;
};

export type AnalysisSummary = {
  requirementCount: number;
  scenarioCount: number;
  coveredRequirements: number;
  partiallyCoveredRequirements: number;
  uncoveredRequirements: number;
  totalCoverage: number;
  averageScenarioCoverage: number;
};

export type AnalysisResult = {
  id: string;
  title: string;
  method: string;
  createdAt: string;
  requirementsName: string;
  evidenceName: string;
  summary: AnalysisSummary;
  coverage: RequirementCoverage[];
};

export type AnalysisRun = {
  id: string;
  title: string;
  status: "running" | "complete" | "cancelled" | "failed";
  method: string;
  createdAt: string;
  progress: number;
  message: string;
  result: AnalysisResult | null;
};
