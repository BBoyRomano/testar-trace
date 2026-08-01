import type {
  AnalysisResult,
  EvidenceBundle,
  EvidenceGraph,
  EvidenceRefKind,
  EvidenceReference,
  RawSource,
  RequirementBundle,
  RequirementCoverage,
  RequirementItem,
  ScenarioCoverage,
  SequenceStep,
} from "./types";

export type CanonicalEvidenceSet = {
  id: string;
  title: string;
  states?: CanonicalEvidenceState[];
  actions?: CanonicalEvidenceAction[];
  transitions?: CanonicalEvidenceTransition[];
  elements?: unknown[];
  artifacts?: unknown[];
};

type CanonicalEvidenceState = {
  id?: unknown;
  name?: unknown;
  title?: unknown;
  url?: unknown;
};

type CanonicalEvidenceAction = {
  id?: unknown;
  description?: unknown;
};

type CanonicalEvidenceTransition = {
  id?: unknown;
  from_state_id?: unknown;
  action_id?: unknown;
  to_state_id?: unknown;
};

export type CanonicalRequirementSet = {
  requirements?: CanonicalRequirement[];
  fragments?: CanonicalFragment[];
  scenarios?: CanonicalScenario[];
};

type CanonicalRequirement = {
  id: string;
  title: string;
  summary?: string | null;
  actor?: string | null;
  document_id?: string | null;
};

type CanonicalFragment = {
  id: string;
  requirement_id: string;
  kind: string;
  text: string;
  branch_id?: string | null;
};

type CanonicalScenario = {
  id: string;
  requirement_id: string;
  title: string;
  kind: string;
  fragment_ids: string[];
  metadata?: Record<string, string | number | boolean | null>;
};

export type CanonicalTraceabilityResult = {
  id: string;
  title: string;
  created_at: string;
  summary: CanonicalTraceabilitySummary;
  coverage?: CanonicalCoverage[];
  occurrences?: CanonicalOccurrence[];
  fragment_alignments?: CanonicalFragmentAlignment[];
};

type CanonicalTraceabilitySummary = {
  total_requirements: number;
  covered_requirements: number;
  partially_covered_requirements: number;
  uncovered_requirements: number;
  metadata?: Record<string, unknown>;
};

type CanonicalCoverage = {
  requirement_id: string;
  status: string;
  coverage_ratio?: number | null;
  metadata?: Record<string, unknown>;
};

type CanonicalScenarioCoverage = {
  scenario_id?: unknown;
  kind?: unknown;
  status?: unknown;
  coverage_ratio?: unknown;
  best_occurrence_id?: unknown;
  matched_fragment_count?: unknown;
  total_fragment_count?: unknown;
};

type CanonicalOccurrence = {
  id: string;
  evidence_path?: CanonicalEvidenceRef[];
};

type CanonicalFragmentAlignment = {
  fragment_id: string;
  occurrence_id: string;
  evidence_refs?: CanonicalEvidenceRef[];
  fragment_kind?: string | null;
  score?: number | null;
  metadata?: Record<string, unknown>;
};

type CanonicalEvidenceRef = {
  kind: string;
  evidence_id: string;
};

export function mapCanonicalEvidence(
  data: CanonicalEvidenceSet,
  source: RawSource,
): EvidenceBundle {
  return {
    id: data.id,
    name: data.title || source.name,
    sourceKind: "file",
    kind: "",
    loadedAt: new Date().toISOString(),
    source,
    text: source.text,
    stateCount: data.states?.length ?? 0,
    actionCount: data.actions?.length ?? 0,
    transitionCount: data.transitions?.length ?? 0,
    elementCount: data.elements?.length ?? 0,
    stats: {
      states: data.states?.length ?? 0,
      actions: data.actions?.length ?? 0,
      transitions: data.transitions?.length ?? 0,
      widgets: data.elements?.length ?? 0,
      artifacts: data.artifacts?.length ?? 0,
    },
    graph: mapEvidenceGraph(data),
  };
}

function mapEvidenceGraph(data: CanonicalEvidenceSet): EvidenceGraph {
  const states = data.states ?? [];
  const actions = data.actions ?? [];
  const stateIds = new Set(states.map((state) => stringValue(state.id, "")).filter(Boolean));
  const actionIds = new Set(actions.map((action) => stringValue(action.id, "")).filter(Boolean));

  return {
    nodes: [
      ...states
        .map((state) => {
          const id = stringValue(state.id, "");
          return id === ""
            ? null
            : {
                id,
                kind: "state" as const,
                label: firstText(state.title, state.name, state.url, id),
              };
        })
        .filter((node) => node !== null),
      ...actions
        .map((action) => {
          const id = stringValue(action.id, "");
          return id === ""
            ? null
            : {
                id,
                kind: "action" as const,
                label: firstText(action.description, id),
              };
        })
        .filter((node) => node !== null),
    ],
    edges: (data.transitions ?? [])
      .map((transition) => {
        const id = stringValue(transition.id, "");
        const source = stringValue(transition.from_state_id, "");
        const actionId = stringValue(transition.action_id, "");
        const target = stringValue(transition.to_state_id, "");
        if (
          id === "" ||
          source === "" ||
          actionId === "" ||
          !stateIds.has(source) ||
          !actionIds.has(actionId)
        ) {
          return [];
        }
        const sourceEdge = {
          id: `${id}:action`,
          kind: "transition" as const,
          source,
          target: actionId,
          label: id,
          transitionId: id,
        };
        if (target === "" || !stateIds.has(target)) {
          return [sourceEdge];
        }
        return [
          sourceEdge,
          {
            id: `${id}:target`,
            kind: "transition" as const,
            source: actionId,
            target,
            label: id,
            transitionId: id,
          },
        ];
      })
      .flat(),
  };
}

export function mapCanonicalRequirements(data: CanonicalRequirementSet): RequirementItem[] {
  const fragments = data.fragments ?? [];
  const scenarios = data.scenarios ?? [];
  return (data.requirements ?? []).map((requirement) => ({
    id: requirement.id,
    title: requirement.title,
    summary: requirement.summary ?? "",
    actor: requirement.actor ?? "",
    sourceName: requirement.document_id ?? "canonical requirements",
    fragments: fragments
      .filter((fragment) => fragment.requirement_id === requirement.id)
      .map((fragment) => ({
        id: fragment.id,
        requirementId: fragment.requirement_id,
        kind: fragment.kind,
        text: fragment.text,
        branchId: fragment.branch_id ?? null,
      })),
    scenarios: scenarios
      .filter((scenario) => scenario.requirement_id === requirement.id)
      .map((scenario) => ({
        id: scenario.id,
        requirementId: scenario.requirement_id,
        title: scenario.title,
        kind: scenario.kind,
        fragmentIds: scenario.fragment_ids,
        metadata: scenario.metadata ?? {},
      })),
  }));
}

export function mapCanonicalAnalysisResult(
  data: CanonicalTraceabilityResult,
  requirements: RequirementBundle,
  evidence: EvidenceBundle,
): AnalysisResult {
  const coverage = data.coverage ?? [];
  const scenarios = coverage.flatMap((item) => scenarioCoverageItems(item.metadata));
  return {
    id: data.id,
    title: data.title,
    method: stringValue(data.summary.metadata?.method, data.id),
    createdAt: data.created_at,
    requirementsName: requirements.name,
    evidenceName: evidence.name,
    summary: {
      requirementCount: data.summary.total_requirements,
      scenarioCount: scenarios.length,
      coveredRequirements: data.summary.covered_requirements,
      partiallyCoveredRequirements: data.summary.partially_covered_requirements,
      uncoveredRequirements: data.summary.uncovered_requirements,
      totalCoverage: numberValue(data.summary.metadata?.requirements_coverage_ratio),
      averageScenarioCoverage: average(scenarios.map((item) => numberValue(item.coverage_ratio))),
    },
    coverage: coverage.map((item) => mapCanonicalCoverage(item, data, requirements)),
  };
}

function mapCanonicalCoverage(
  item: CanonicalCoverage,
  result: CanonicalTraceabilityResult,
  requirements: RequirementBundle,
): RequirementCoverage {
  const requirement = requirements.requirements.find(
    (candidate) => candidate.id === item.requirement_id,
  );
  const scenarioItems = scenarioCoverageItems(item.metadata);
  return {
    requirementId: item.requirement_id,
    title: stringValue(item.metadata?.requirement_title, requirement?.title ?? item.requirement_id),
    status: coverageStatus(item.status),
    coverageRatio: item.coverage_ratio ?? 0,
    scenarios: scenarioItems.map((scenario) => mapScenarioCoverage(scenario, result, requirement)),
  };
}

function mapScenarioCoverage(
  item: CanonicalScenarioCoverage,
  result: CanonicalTraceabilityResult,
  requirement: RequirementItem | undefined,
): ScenarioCoverage {
  const scenarioId = stringValue(item.scenario_id, "scenario");
  const scenario = requirement?.scenarios.find((candidate) => candidate.id === scenarioId);
  const bestOccurrenceId = stringValue(item.best_occurrence_id, "");
  const sequence =
    requirement === undefined || scenario === undefined
      ? []
      : scenario.fragmentIds.map((fragmentId) =>
          mapSequenceStep(
            fragmentId,
            requirement,
            result.fragment_alignments ?? [],
            result.occurrences ?? [],
            bestOccurrenceId,
          ),
        );

  return {
    scenarioId,
    requirementId: requirement?.id ?? "",
    title: scenario?.title ?? scenarioId,
    kind: stringValue(item.kind, scenario?.kind ?? "scenario"),
    status: coverageStatus(stringValue(item.status, "not-covered")),
    coverageRatio: numberValue(item.coverage_ratio),
    matchedFragments: integerValue(item.matched_fragment_count),
    totalFragments: integerValue(item.total_fragment_count),
    sequence,
  };
}

function mapSequenceStep(
  fragmentId: string,
  requirement: RequirementItem,
  alignments: CanonicalFragmentAlignment[],
  occurrences: CanonicalOccurrence[],
  bestOccurrenceId: string,
): SequenceStep {
  const fragment = requirement.fragments.find((item) => item.id === fragmentId);
  const alignment = alignments.find(
    (item) =>
      item.fragment_id === fragmentId &&
      (bestOccurrenceId === "" || item.occurrence_id === bestOccurrenceId),
  );
  const occurrence = occurrences.find((item) => item.id === alignment?.occurrence_id);
  const evidenceRefs = evidenceReferences(
    alignment?.evidence_refs ?? occurrence?.evidence_path ?? [],
  );
  const evidenceRef = evidenceRefs[0];
  const evidenceText = stringValue(
    alignment?.metadata?.evidence_text,
    evidenceRef?.evidenceId ?? "No nearby evidence candidate",
  );
  return {
    fragmentId,
    fragmentText: fragment?.text ?? fragmentId,
    fragmentKind: fragment?.kind ?? alignment?.fragment_kind ?? "fragment",
    evidenceId: evidenceRef?.evidenceId ?? "unmatched",
    evidenceLabel: evidenceText,
    evidenceKind: evidenceRef?.kind ?? "transition",
    evidenceRefs,
    score: alignment?.score ?? 0,
    matched: alignment !== undefined,
  };
}

function scenarioCoverageItems(
  metadata: Record<string, unknown> | undefined,
): CanonicalScenarioCoverage[] {
  const value = metadata?.scenario_coverage;
  return Array.isArray(value)
    ? value.filter(isRecord).map((item) => item as CanonicalScenarioCoverage)
    : [];
}

function coverageStatus(value: string): "covered" | "partially-covered" | "not-covered" {
  if (value === "covered" || value === "partially-covered") {
    return value;
  }
  return "not-covered";
}

function evidenceReferences(refs: CanonicalEvidenceRef[]): EvidenceReference[] {
  return refs
    .map((ref) => ({
      kind: evidenceKind(ref.kind),
      evidenceId: ref.evidence_id,
    }))
    .filter((ref) => ref.evidenceId.length > 0);
}

function evidenceKind(value: string | undefined): EvidenceRefKind {
  if (
    value === "artifact" ||
    value === "state" ||
    value === "transition" ||
    value === "action" ||
    value === "element"
  ) {
    return value;
  }
  return "transition";
}

function average(values: number[]): number {
  return values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length;
}

function numberValue(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function integerValue(value: unknown): number {
  return Number.isInteger(value) ? Number(value) : 0;
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function firstText(...values: unknown[]): string {
  for (const value of values) {
    if (typeof value === "string" && value.trim().length > 0) {
      return value.trim();
    }
  }
  return "";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
