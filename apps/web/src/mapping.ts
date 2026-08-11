import type {
  AnalysisResult,
  CoverageAssessment,
  JsonObject,
  RawSource,
  RequirementBundle,
  RequirementItem,
  RequirementPath,
  StateModel,
  StateModelBundle,
  StateModelEntity,
  TraceLink,
  TraceOccurrence,
  TraceTarget,
} from "./types.ts";

type CanonicalRequirementSet = {
  documents?: Array<{ id: string; title: string }>;
  requirements?: Array<{
    id: string;
    title: string;
    summary?: string | null;
    body?: string | null;
    actor?: string | null;
    scope?: string | null;
    level?: string | null;
    document_id?: string | null;
    metadata?: Record<string, unknown>;
  }>;
  elements?: Array<{
    id: string;
    requirement_id: string;
    text: string;
    kind: string;
    order_index?: number | null;
    metadata?: Record<string, unknown>;
  }>;
  flows?: CanonicalFlow[];
};

type CanonicalFlow = {
  id: string;
  requirement_id: string;
  title: string;
  entry_node_id: string;
  branches?: Array<{
    id: string;
    title: string;
    kind: "main" | "alternative" | "exception";
    entry_node_id: string;
    order_index?: number | null;
    resolution: "explicit" | "inferred" | "ambiguous";
    metadata?: Record<string, unknown>;
  }>;
  nodes?: Array<{
    id: string;
    branch_id: string;
    element_id: string;
    outcome?: string | null;
  }>;
  edges?: Array<{
    id: string;
    source_node_id: string;
    target_node_id: string;
    kind: "next" | "branch" | "rejoin" | "repeat";
    branch_id?: string | null;
    order_index?: number | null;
  }>;
  metadata?: Record<string, unknown>;
};

type CanonicalStateModelCollection = {
  id: string;
  title: string;
  models?: CanonicalStateModel[];
};

type CanonicalStateModel = {
  id: string;
  title: string;
  layer: string;
  source_ref?: CanonicalSourceRef | null;
  initial_state_ids?: string[];
  states?: Array<{
    id: string;
    name?: string | null;
    title?: string | null;
    url?: string | null;
    source_ref?: CanonicalSourceRef | null;
    metadata?: Record<string, unknown>;
  }>;
  widgets?: Array<{
    id: string;
    state_id: string;
    tag_name?: string | null;
    text?: string | null;
    title?: string | null;
    role?: string | null;
    href?: string | null;
    css_selector?: string | null;
    source_ref?: CanonicalSourceRef | null;
    metadata?: Record<string, unknown>;
  }>;
  actions?: Array<{
    id: string;
    description?: string | null;
    target_widget_id?: string | null;
    value?: string | null;
    source_ref?: CanonicalSourceRef | null;
    metadata?: Record<string, unknown>;
  }>;
  transitions?: Array<{
    id: string;
    source_state_id: string;
    action_id: string;
    target_state_id?: string | null;
    source_ref?: CanonicalSourceRef | null;
    metadata?: Record<string, unknown>;
  }>;
};

type CanonicalSourceRef = {
  source_name?: string | null;
  native_id?: string | null;
  location?: string | null;
};

type CanonicalResult = {
  id: string;
  title: string;
  path_materialization: {
    bounded: boolean;
    paths?: CanonicalPath[];
    diagnostics?: Array<{
      code: string;
      flow_id: string;
      message: string;
      node_id?: string | null;
      edge_id?: string | null;
    }>;
  };
  assessments?: CanonicalAssessment[];
  links?: CanonicalLink[];
  occurrences?: CanonicalOccurrence[];
  metadata?: Record<string, unknown>;
  summary: Record<string, number | null>;
};

type CanonicalPath = {
  id: string;
  requirement_id: string;
  flow_id: string;
  title: string;
  branch_ids: string[];
  node_ids: string[];
  edge_ids: string[];
  element_ids: string[];
  outcome: string;
  order_index: number;
  resolution: string;
  metadata?: Record<string, unknown>;
};

type CanonicalAssessment = {
  id: string;
  scope_kind: CoverageAssessment["scopeKind"];
  scope_id: string;
  requirement_ids: string[];
  view_kind: CoverageAssessment["viewKind"];
  state_model_ids: string[];
  status: CoverageAssessment["status"];
  assessability: CoverageAssessment["assessability"];
  completeness: CoverageAssessment["completeness"];
  occurrence_ids?: string[];
  covered_element_ids?: string[];
  missing_element_ids?: string[];
  coverage_ratio?: number | null;
  rationale?: string | null;
  metadata?: Record<string, unknown>;
};

type CanonicalLink = {
  id: string;
  requirement_id: string;
  requirement_element_id?: string | null;
  state_model_id: string;
  target_ref: { kind: TraceTarget["kind"]; target_id: string };
  score: number;
  occurrence_id?: string | null;
  rationale?: string | null;
  metadata?: Record<string, unknown>;
};

type CanonicalOccurrence = {
  id: string;
  requirement_id: string;
  flow_id: string;
  path_id: string;
  state_model_id: string;
  evidence_basis: "state-model-graph" | "execution-sequence" | "formal-model-check";
  status: TraceOccurrence["status"];
  execution_sequence_id?: string | null;
  score?: number | null;
  target_path?: Array<{ kind: TraceTarget["kind"]; target_id: string }>;
  covered_element_ids?: string[];
  missing_element_ids?: string[];
  link_ids?: string[];
  rationale?: string | null;
  metadata?: Record<string, unknown>;
};

export function mapRequirements(input: {
  data: CanonicalRequirementSet;
  sources: RawSource[];
  name: string;
  sourceKind: RequirementBundle["sourceKind"];
  adapterId: string;
}): RequirementBundle {
  const documents = new Map((input.data.documents ?? []).map((item) => [item.id, item.title]));
  const elements = input.data.elements ?? [];
  const flows = input.data.flows ?? [];
  const requirements: RequirementItem[] = (input.data.requirements ?? []).map((item) => ({
    id: item.id,
    title: item.title,
    summary: item.summary ?? "",
    body: item.body ?? "",
    actor: item.actor ?? "",
    scope: item.scope ?? "",
    level: item.level ?? "",
    sourceName: documents.get(item.document_id ?? "") ?? input.name,
    metadata: jsonObject(item.metadata),
    elements: elements
      .filter((element) => element.requirement_id === item.id)
      .map((element) => ({
        id: element.id,
        requirementId: element.requirement_id,
        kind: element.kind,
        text: element.text,
        orderIndex: element.order_index ?? null,
        metadata: jsonObject(element.metadata),
      })),
    flows: flows
      .filter((flow) => flow.requirement_id === item.id)
      .map((flow) => ({
        id: flow.id,
        requirementId: flow.requirement_id,
        title: flow.title,
        entryNodeId: flow.entry_node_id,
        branches: (flow.branches ?? []).map((branch) => ({
          id: branch.id,
          title: branch.title,
          kind: branch.kind,
          entryNodeId: branch.entry_node_id,
          orderIndex: branch.order_index ?? null,
          resolution: branch.resolution,
          metadata: jsonObject(branch.metadata),
        })),
        nodes: (flow.nodes ?? []).map((node) => ({
          id: node.id,
          branchId: node.branch_id,
          elementId: node.element_id,
          outcome: node.outcome ?? null,
        })),
        edges: (flow.edges ?? []).map((edge) => ({
          id: edge.id,
          sourceNodeId: edge.source_node_id,
          targetNodeId: edge.target_node_id,
          kind: edge.kind,
          branchId: edge.branch_id ?? null,
          orderIndex: edge.order_index ?? null,
        })),
        metadata: jsonObject(flow.metadata),
      })),
  }));
  return {
    id: crypto.randomUUID(),
    name: input.name,
    sourceKind: input.sourceKind,
    loadedAt: new Date().toISOString(),
    adapterId: input.adapterId,
    sources: input.sources,
    requirements,
  };
}

export function mapStateModels(input: {
  data: CanonicalStateModelCollection;
  sources: RawSource[];
  name: string;
  adapterId: string;
}): StateModelBundle {
  return {
    id: input.data.id,
    name: input.data.title || input.name,
    loadedAt: new Date().toISOString(),
    adapterId: input.adapterId,
    sources: input.sources,
    models: (input.data.models ?? []).map(mapStateModel),
  };
}

function mapStateModel(model: CanonicalStateModel): StateModel {
  const states = model.states ?? [];
  const widgets = model.widgets ?? [];
  const actions = model.actions ?? [];
  const transitions = model.transitions ?? [];
  const sourceName = fileName(model.source_ref?.source_name);
  const widgetsById = new Map(widgets.map((item) => [item.id, item]));
  const actionsById = new Map(actions.map((item) => [item.id, item]));
  const stateLabels = new Map(
    states.map((item, index) => [item.id, compactStateLabel(item, index, states.length)]),
  );
  const entities: StateModelEntity[] = [
    ...states.map((item) => ({
      id: item.id,
      kind: "state" as const,
      label: stateDisplayName(item),
      stateModelId: model.id,
      ...(stateLabels.get(item.id)?.title === undefined
        ? {}
        : { title: stateLabels.get(item.id)?.title as string }),
      ...(item.url === null || item.url === undefined ? {} : { url: item.url }),
      ...sourceDetails(item.source_ref, item.metadata),
    })),
    ...widgets.map((item) => ({
      id: item.id,
      kind: "widget" as const,
      label: firstText(item.text, item.title, item.role, item.id),
      stateModelId: model.id,
      stateId: item.state_id,
      ...(item.text === null || item.text === undefined ? {} : { text: item.text }),
      ...(item.title === null || item.title === undefined ? {} : { title: item.title }),
      ...(item.role === null || item.role === undefined ? {} : { role: item.role }),
      ...(item.tag_name === null || item.tag_name === undefined ? {} : { tagName: item.tag_name }),
      ...(item.href === null || item.href === undefined ? {} : { href: item.href }),
      ...(item.css_selector === null || item.css_selector === undefined
        ? {}
        : { cssSelector: item.css_selector }),
      ...sourceDetails(item.source_ref, item.metadata),
    })),
    ...actions.map((item) => ({
      id: item.id,
      kind: "action" as const,
      label: firstText(item.description, item.value, item.id),
      stateModelId: model.id,
      ...(item.description === null || item.description === undefined
        ? {}
        : { description: item.description }),
      ...(item.value === null || item.value === undefined ? {} : { value: item.value }),
      ...(item.target_widget_id === null || item.target_widget_id === undefined
        ? {}
        : { targetWidgetId: item.target_widget_id }),
      ...(widgetsById.get(item.target_widget_id ?? "")?.state_id === undefined
        ? {}
        : { stateId: widgetsById.get(item.target_widget_id ?? "")?.state_id as string }),
      ...sourceDetails(item.source_ref, item.metadata),
    })),
    ...transitions.map((item) => ({
      id: item.id,
      kind: "transition" as const,
      label: actionsById.get(item.action_id)?.description ?? item.id,
      stateModelId: model.id,
      stateId: item.source_state_id,
      actionId: item.action_id,
      sourceStateId: item.source_state_id,
      ...(item.target_state_id === null || item.target_state_id === undefined
        ? {}
        : { targetStateId: item.target_state_id }),
      ...sourceDetails(item.source_ref, item.metadata),
    })),
  ];
  return {
    id: model.id,
    title: model.title,
    ...(sourceName === undefined ? {} : { sourceName }),
    layer: model.layer,
    entities,
    counts: {
      state: states.length,
      widget: widgets.length,
      action: actions.length,
      transition: transitions.length,
    },
    graph: {
      nodes: states.map((item, index) => ({
        id: item.id,
        label: stateLabels.get(item.id)?.label ?? "",
        shortId: stateLabels.get(item.id)?.shortId ?? `S${index + 1}`,
        ...(stateLabels.get(item.id)?.title === undefined
          ? {}
          : { title: stateLabels.get(item.id)?.title as string }),
        ...(item.url === null || item.url === undefined ? {} : { url: item.url }),
        initial: (model.initial_state_ids ?? []).includes(item.id),
      })),
      edges: transitions
        .filter((item) => item.target_state_id !== null && item.target_state_id !== undefined)
        .map((item) => ({
          id: item.id,
          source: item.source_state_id,
          target: item.target_state_id as string,
          label: actionsById.get(item.action_id)?.description ?? "",
          actionId: item.action_id,
        })),
    },
  };
}

function fileName(value: string | null | undefined): string | undefined {
  if (value === null || value === undefined || value.trim() === "") return undefined;
  return value.replaceAll("\\", "/").split("/").at(-1) ?? value;
}

export function mapAnalysisResult(input: {
  data: CanonicalResult;
  resultId: string;
  requirements: RequirementBundle;
  stateModels: StateModelBundle;
  method: { id: string; name: string };
}): AnalysisResult {
  const paths = (input.data.path_materialization.paths ?? []).map(mapPath);
  const summary = input.data.summary;
  return {
    schemaVersion: 1,
    id: input.resultId,
    title: input.data.title,
    methodId: input.method.id,
    methodName: input.method.name,
    createdAt: new Date().toISOString(),
    requirementsName: input.requirements.name,
    stateModelsName: input.stateModels.name,
    pathsExhaustive:
      !input.data.path_materialization.bounded &&
      (input.data.path_materialization.diagnostics ?? []).length === 0,
    paths,
    pathDiagnostics: (input.data.path_materialization.diagnostics ?? []).map((item) => ({
      code: item.code,
      flowId: item.flow_id,
      message: item.message,
      nodeId: "node_id" in item && typeof item.node_id === "string" ? item.node_id : null,
      edgeId: "edge_id" in item && typeof item.edge_id === "string" ? item.edge_id : null,
    })),
    assessments: (input.data.assessments ?? []).map(mapAssessment),
    links: (input.data.links ?? []).map(mapLink),
    occurrences: (input.data.occurrences ?? []).map(mapOccurrence),
    summary: {
      totalRequirements: numeric(summary.total_requirements),
      coveredRequirements: numeric(summary.covered_requirements),
      partiallyCoveredRequirements: numeric(summary.partially_covered_requirements),
      uncoveredRequirements: numeric(summary.uncovered_requirements),
      completeRequirements: numeric(summary.complete_requirements),
      incompleteRequirements: numeric(summary.incomplete_requirements),
      notAssessableRequirements: numeric(summary.not_assessable_requirements),
      totalPaths: numeric(summary.total_paths),
      completePaths: numeric(summary.complete_paths),
      incompletePaths: numeric(summary.incomplete_paths),
      notAssessablePaths: numeric(summary.not_assessable_paths),
      totalLinks: numeric(summary.total_links),
      totalOccurrences: numeric(summary.total_occurrences),
      overallCoverageRatio: nullableNumber(summary.overall_coverage_ratio),
    },
  };
}

function mapPath(item: CanonicalPath): RequirementPath {
  return {
    id: item.id,
    requirementId: item.requirement_id,
    flowId: item.flow_id,
    title: item.title,
    branchIds: item.branch_ids,
    nodeIds: item.node_ids,
    edgeIds: item.edge_ids,
    elementIds: item.element_ids,
    outcome: item.outcome,
    orderIndex: item.order_index,
    resolution: item.resolution,
    metadata: jsonObject(item.metadata),
  };
}

function mapAssessment(item: CanonicalAssessment): CoverageAssessment {
  return {
    id: item.id,
    scopeKind: item.scope_kind,
    scopeId: item.scope_id,
    requirementIds: item.requirement_ids,
    viewKind: item.view_kind,
    stateModelIds: item.state_model_ids,
    status: item.status,
    assessability: item.assessability,
    completeness: item.completeness,
    occurrenceIds: item.occurrence_ids ?? [],
    coveredElementIds: item.covered_element_ids ?? [],
    missingElementIds: item.missing_element_ids ?? [],
    coverageRatio: item.coverage_ratio ?? null,
    rationale: item.rationale ?? "",
    metadata: jsonObject(item.metadata),
  };
}

function mapLink(item: CanonicalLink): TraceLink {
  return {
    id: item.id,
    requirementId: item.requirement_id,
    requirementElementId: item.requirement_element_id ?? null,
    stateModelId: item.state_model_id,
    target: { kind: item.target_ref.kind, targetId: item.target_ref.target_id },
    score: item.score,
    occurrenceId: item.occurrence_id ?? null,
    rationale: item.rationale ?? "",
    metadata: jsonObject(item.metadata),
  };
}

function mapOccurrence(item: CanonicalOccurrence): TraceOccurrence {
  return {
    id: item.id,
    requirementId: item.requirement_id,
    flowId: item.flow_id,
    pathId: item.path_id,
    stateModelId: item.state_model_id,
    evidenceBasis: item.evidence_basis,
    status: item.status,
    executionSequenceId: item.execution_sequence_id ?? null,
    score: item.score ?? null,
    targetPath: (item.target_path ?? []).map((target) => ({
      kind: target.kind,
      targetId: target.target_id,
    })),
    coveredElementIds: item.covered_element_ids ?? [],
    missingElementIds: item.missing_element_ids ?? [],
    linkIds: item.link_ids ?? [],
    rationale: item.rationale ?? "",
    metadata: jsonObject(item.metadata),
  };
}

function jsonObject(value: Record<string, unknown> | undefined): JsonObject {
  return (value ?? {}) as JsonObject;
}

function firstText(...values: Array<string | null | undefined>): string {
  return values.find((value) => value !== null && value !== undefined && value.trim() !== "") ?? "";
}

function stateDisplayName(state: {
  id: string;
  name?: string | null;
  title?: string | null;
  url?: string | null;
}): string {
  return firstText(statePageLabel(state), state.id);
}

function compactStateLabel(
  state: { id: string; name?: string | null; title?: string | null; url?: string | null },
  index: number,
  total: number,
): { label: string; shortId: string; title?: string } {
  const width = Math.max(2, String(total).length);
  const shortId = `S${String(index + 1).padStart(width, "0")}`;
  const title = statePageLabel(state);
  return title === "" ? { label: "", shortId } : { label: title, shortId, title };
}

function statePageLabel(state: {
  id: string;
  name?: string | null;
  title?: string | null;
  url?: string | null;
}): string {
  const authoredName = firstText(state.title, state.name);
  if (authoredName !== "" && authoredName !== state.id) return authoredName;
  return pageName(state.url);
}

function pageName(value: string | null | undefined): string {
  if (value === null || value === undefined || value.trim() === "") return "";
  try {
    const url = new URL(value, "https://state-model.invalid");
    const segment = url.pathname.split("/").filter(Boolean).at(-1);
    if (segment === undefined) return "Home";
    return decodeURIComponent(segment)
      .replace(/\.[a-z0-9]+$/i, "")
      .replaceAll(/[-_]+/g, " ")
      .replace(/^./, (character) => character.toLocaleUpperCase());
  } catch {
    return value;
  }
}

function sourceDetails(
  sourceRef: CanonicalSourceRef | null | undefined,
  metadata: Record<string, unknown> | undefined,
): Pick<StateModelEntity, "nativeId" | "sourceLocation" | "metadata"> {
  const nativeId = firstText(
    sourceRef?.native_id,
    typeof metadata?.testar_abstract_id === "string" ? metadata.testar_abstract_id : undefined,
  );
  return {
    ...(nativeId === "" ? {} : { nativeId }),
    ...(sourceRef?.location === null || sourceRef?.location === undefined
      ? {}
      : { sourceLocation: sourceRef.location }),
    ...(metadata === undefined ? {} : { metadata: jsonObject(metadata) }),
  };
}

function numeric(value: number | null | undefined): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function nullableNumber(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
