import { PATH_TONE_COUNT } from "./path-colors.ts";
import type {
  AnalysisResult,
  AssessmentScopeKind,
  CoverageAssessment,
  RequirementBranch,
  RequirementItem,
  RequirementPath,
  ResultRequirementFilter,
  SelectableResultScopeKind,
  StateModel,
  TraceLink,
  TraceOccurrence,
} from "./types.ts";

export type ResultScope = {
  kind: "requirement" | "flow" | "branch" | "path" | "element";
  id: string;
  requirementId: string;
  elementIds: Set<string> | null;
  assessmentKind: "requirement" | "flow" | "branch" | "path";
  assessmentId: string;
};

export function resolveResultScope(
  result: AnalysisResult,
  requirementId: string,
  pathId: string,
  elementId = "",
  selectedKind: SelectableResultScopeKind = "path",
  requirement?: RequirementItem,
): ResultScope {
  const selected = resolveAssessmentSelection(
    result,
    requirementId,
    selectedKind,
    pathId,
    requirement,
  );
  if (elementId !== "" && (selected.elementIds === null || selected.elementIds.has(elementId))) {
    return {
      kind: "element",
      id: elementId,
      requirementId,
      elementIds: new Set([elementId]),
      assessmentKind: selected.kind,
      assessmentId: selected.id,
    };
  }
  return {
    kind: selected.kind,
    id: selected.id,
    requirementId,
    elementIds: selected.elementIds,
    assessmentKind: selected.kind,
    assessmentId: selected.id,
  };
}

function resolveAssessmentSelection(
  result: AnalysisResult,
  requirementId: string,
  selectedKind: SelectableResultScopeKind,
  selectedId: string,
  requirement?: RequirementItem,
): {
  kind: SelectableResultScopeKind;
  id: string;
  elementIds: Set<string> | null;
} {
  if (selectedKind === "path") {
    const path = result.paths.find(
      (item) => item.id === selectedId && item.requirementId === requirementId,
    );
    if (path !== undefined) {
      return { kind: "path", id: path.id, elementIds: new Set(path.elementIds) };
    }
  }
  if (selectedKind === "flow") {
    const flow = requirement?.flows.find((item) => item.id === selectedId);
    if (flow !== undefined) {
      return {
        kind: "flow",
        id: flow.id,
        elementIds: new Set(flow.nodes.map((node) => node.elementId)),
      };
    }
  }
  if (selectedKind === "branch") {
    for (const flow of requirement?.flows ?? []) {
      if (!flow.branches.some((branch) => branch.id === selectedId)) continue;
      return {
        kind: "branch",
        id: selectedId,
        elementIds: new Set(
          flow.nodes.filter((node) => node.branchId === selectedId).map((node) => node.elementId),
        ),
      };
    }
  }
  return { kind: "requirement", id: requirementId, elementIds: null };
}

export function pathsForRequirement(
  result: AnalysisResult,
  requirementId: string,
): RequirementPath[] {
  return result.paths.filter((path) => path.requirementId === requirementId);
}

export function pathBranchKind(
  path: RequirementPath,
  requirement: RequirementItem,
): RequirementBranch["kind"] {
  const kinds = new Set(
    requirement.flows
      .flatMap((flow) => flow.branches)
      .filter((branch) => path.branchIds.includes(branch.id))
      .map((branch) => branch.kind),
  );
  if (kinds.has("exception")) return "exception";
  if (kinds.has("alternative")) return "alternative";
  return "main";
}

export function pathAccentIndex(path: RequirementPath, requirement: RequirementItem): number {
  const priority = pathPriorityIndex(path, requirement);
  return priority === 0 ? 0 : ((priority - 1) % (PATH_TONE_COUNT - 1)) + 1;
}

export function pathPriorityIndex(path: RequirementPath, requirement: RequirementItem): number {
  if (pathBranchKind(path, requirement) === "main") return 0;
  const alternatives = requirement.flows.flatMap((flow) =>
    flow.branches
      .map((branch, authoredIndex) => ({ branch, authoredIndex }))
      .filter(({ branch }) => branch.kind !== "main")
      .sort(
        (left, right) =>
          (left.branch.orderIndex ?? left.authoredIndex) -
            (right.branch.orderIndex ?? right.authoredIndex) ||
          left.authoredIndex - right.authoredIndex,
      )
      .map(({ branch }) => branch),
  );
  const firstBranchIndex = alternatives.findIndex((branch) => path.branchIds.includes(branch.id));
  return firstBranchIndex < 0 ? alternatives.length + 1 : firstBranchIndex + 1;
}

export function filterResultRequirementIds(input: {
  ids: string[];
  requirements: RequirementItem[];
  assessments: CoverageAssessment[];
  query: string;
  filter: ResultRequirementFilter;
}): string[] {
  const query = input.query.trim().toLocaleLowerCase();
  return input.ids.filter((id) => {
    const requirement = input.requirements.find((item) => item.id === id);
    const assessment = input.assessments.find(
      (item) =>
        item.scopeKind === "requirement" &&
        item.scopeId === id &&
        item.viewKind === "state-model-collection",
    );
    const matchesQuery =
      query === "" ||
      [id, requirement?.title ?? "", requirement?.summary ?? "", requirement?.actor ?? ""].some(
        (value) => value.toLocaleLowerCase().includes(query),
      );
    const matchesFilter =
      input.filter === "all" || (assessment?.completeness ?? "not-assessable") === input.filter;
    return matchesQuery && matchesFilter;
  });
}

export function assessmentForScope(
  result: AnalysisResult,
  scope: ResultScope,
  stateModelId = "",
): CoverageAssessment | null {
  const viewKind = stateModelId === "" ? "state-model-collection" : "state-model";
  return (
    result.assessments.find(
      (item) =>
        item.scopeKind === scope.assessmentKind &&
        item.scopeId === scope.assessmentId &&
        item.viewKind === viewKind &&
        (stateModelId === "" || item.stateModelIds.includes(stateModelId)),
    ) ?? null
  );
}

export function assessmentsForRequirement(
  result: AnalysisResult,
  requirementId: string,
  scopeKind?: AssessmentScopeKind,
): CoverageAssessment[] {
  return result.assessments.filter(
    (item) =>
      item.requirementIds.includes(requirementId) &&
      item.viewKind === "state-model-collection" &&
      (scopeKind === undefined || item.scopeKind === scopeKind),
  );
}

export function linksForScope(
  result: AnalysisResult,
  scope: ResultScope,
  stateModelId: string,
): TraceLink[] {
  return result.links.filter((link) => {
    if (link.requirementId !== scope.requirementId || link.stateModelId !== stateModelId) {
      return false;
    }
    if (scope.elementIds === null) {
      return true;
    }
    return link.requirementElementId !== null && scope.elementIds.has(link.requirementElementId);
  });
}

export function occurrencesForScope(
  result: AnalysisResult,
  scope: ResultScope,
  stateModelId: string,
): TraceOccurrence[] {
  return result.occurrences.filter((occurrence) => {
    if (
      occurrence.requirementId !== scope.requirementId ||
      occurrence.stateModelId !== stateModelId
    ) {
      return false;
    }
    if (scope.kind === "path") return occurrence.pathId === scope.id;
    if (scope.elementIds === null) return true;
    return occurrence.coveredElementIds.some((elementId) => scope.elementIds?.has(elementId));
  });
}

export function bestEvidenceStateModelId(
  result: AnalysisResult,
  scope: ResultScope,
  stateModelIds: readonly string[],
): string {
  let bestId = stateModelIds[0] ?? "";
  let bestRank: readonly number[] = [-1, -1, -1, -1];
  for (const stateModelId of stateModelIds) {
    const occurrences = occurrencesForScope(result, scope, stateModelId);
    const fullPaths = new Set(
      occurrences
        .filter((occurrence) => occurrence.status === "full")
        .map((occurrence) => occurrence.pathId),
    ).size;
    const coveredElements = new Set(
      occurrences.flatMap((occurrence) => occurrence.coveredElementIds),
    ).size;
    const strongestScore = Math.max(-1, ...occurrences.map((occurrence) => occurrence.score ?? -1));
    const rank = [fullPaths, coveredElements, occurrences.length, strongestScore] as const;
    if (compareEvidenceRank(rank, bestRank) > 0) {
      bestId = stateModelId;
      bestRank = rank;
    }
  }
  return bestId;
}

function compareEvidenceRank(left: readonly number[], right: readonly number[]): number {
  for (let index = 0; index < Math.max(left.length, right.length); index += 1) {
    const difference = (left[index] ?? -1) - (right[index] ?? -1);
    if (difference !== 0) return difference;
  }
  return 0;
}

export function occurrenceTargetEvidence(
  result: AnalysisResult,
  occurrences: TraceOccurrence[],
  requirement: RequirementItem,
  elementIds: ReadonlySet<string> | null = null,
  model?: StateModel,
): {
  scores: Map<string, number>;
  markers: Map<string, string[]>;
  tones: Map<string, number>;
  priorities: Map<string, number>;
  directTargets: Set<string>;
} {
  const scores = new Map<string, number>();
  const tones = new Map<string, number>();
  const priorities = new Map<string, number>();
  const targetMarkers = new Map<string, Set<string>>();
  const directTargets = new Set<string>();
  const linksById = new Map(result.links.map((link) => [link.id, link]));

  for (const occurrence of occurrences) {
    const path = result.paths.find(
      (item) => item.id === occurrence.pathId && item.requirementId === requirement.id,
    );
    if (path === undefined) continue;
    const pathPriority = pathPriorityIndex(path, requirement);
    const pathTone = pathAccentIndex(path, requirement);
    const score = occurrence.score === null ? 1 : Math.max(occurrence.score, 0.01);
    const linkedPriorities = new Map<string, number>();
    const linkedTones = new Map<string, number>();
    const elementMarkers = pathElementMarkers(path, requirement);
    const routeTransitionsByLink = routeTransitionIds(occurrence, linksById);
    for (const linkId of occurrence.linkIds) {
      const link = linksById.get(linkId);
      if (link?.requirementElementId === null || link?.requirementElementId === undefined) continue;
      if (elementIds !== null && !elementIds.has(link.requirementElementId)) continue;
      const routeTransitionId =
        typeof link.metadata?.route_transition_id === "string"
          ? link.metadata.route_transition_id
          : routeTransitionsByLink.get(link.id);
      const key =
        link.target.kind === "action" && routeTransitionId !== undefined
          ? `transition:${routeTransitionId}`
          : `${link.target.kind}:${link.target.targetId}`;
      directTargets.add(key);
      scores.set(key, Math.max(scores.get(key) ?? 0, link.score));
      const priority = requirementElementPriority(result, requirement, link.requirementElementId);
      const tone = requirementElementTone(result, requirement, link.requirementElementId);
      preferTargetColor({ priorities: linkedPriorities, tones: linkedTones }, key, priority, tone);
      preferTargetColor({ priorities, tones }, key, priority, tone);

      const marker = elementMarkers.get(link.requirementElementId);
      if (marker === undefined) continue;
      const markers = targetMarkers.get(key) ?? new Set<string>();
      markers.add(marker);
      targetMarkers.set(key, markers);
    }
    const completeRouteKeys = graphRouteKeys(occurrence, model);
    const routeKeys =
      elementIds === null
        ? completeRouteKeys
        : completeRouteKeys.filter((key) => linkedPriorities.has(key));
    const nextLinkedColors = Array.from<{ priority: number; tone: number } | undefined>({
      length: routeKeys.length,
    });
    let nextLinked: { priority: number; tone: number } | undefined;
    for (let index = routeKeys.length - 1; index >= 0; index -= 1) {
      const key = routeKeys[index]!;
      const priority = linkedPriorities.get(key);
      const tone = linkedTones.get(key);
      if (priority !== undefined && tone !== undefined) nextLinked = { priority, tone };
      nextLinkedColors[index] = nextLinked;
    }
    let previousLinked: { priority: number; tone: number } | undefined;
    for (const [index, key] of routeKeys.entries()) {
      scores.set(key, Math.max(scores.get(key) ?? 0, score));
      const linkedPriority = linkedPriorities.get(key);
      const linkedTone = linkedTones.get(key);
      if (linkedPriority !== undefined && linkedTone !== undefined) {
        previousLinked = { priority: linkedPriority, tone: linkedTone };
      }
      const segmentColor =
        (linkedPriority === undefined || linkedTone === undefined
          ? nextLinkedColors[index]
          : { priority: linkedPriority, tone: linkedTone }) ?? previousLinked;
      preferTargetColor(
        { priorities, tones },
        key,
        segmentColor?.priority ?? pathPriority,
        segmentColor?.tone ?? pathTone,
      );
    }
  }

  return {
    scores,
    tones,
    priorities,
    directTargets,
    markers: new Map([...targetMarkers].map(([key, markers]) => [key, [...markers]])),
  };
}

function routeTransitionIds(
  occurrence: TraceOccurrence,
  linksById: ReadonlyMap<string, TraceLink>,
): Map<string, string> {
  const result = new Map<string, string>();
  let currentTransition: string | undefined;
  let linkIndex = 0;
  for (const target of occurrence.targetPath) {
    if (target.kind === "transition") currentTransition = target.targetId;
    const linkId = occurrence.linkIds[linkIndex];
    if (linkId === undefined) break;
    const link = linksById.get(linkId);
    if (
      link !== undefined &&
      link.target.kind === target.kind &&
      link.target.targetId === target.targetId
    ) {
      if (currentTransition !== undefined) result.set(link.id, currentTransition);
      linkIndex += 1;
      if (target.kind === "transition") currentTransition = undefined;
    }
  }
  return result;
}

function graphRouteKeys(occurrence: TraceOccurrence, model: StateModel | undefined): string[] {
  const keys: string[] = [];
  for (const target of occurrence.targetPath) {
    if (!isStateModelTarget(target.kind)) continue;
    if (target.kind !== "action") {
      keys.push(`${target.kind}:${target.targetId}`);
      continue;
    }
    const matchingEdges =
      model?.graph.edges.filter((edge) => edge.actionId === target.targetId) ?? [];
    if (matchingEdges.length === 1) keys.push(`transition:${matchingEdges[0]!.id}`);
  }
  return [...new Set(keys)];
}

function isStateModelTarget(kind: string): boolean {
  return kind === "state" || kind === "widget" || kind === "action" || kind === "transition";
}

function pathElementMarkers(
  path: RequirementPath,
  requirement: RequirementItem,
): Map<string, string> {
  const markers = new Map<string, string>();
  let stepNumber = 0;
  for (const elementId of path.elementIds) {
    const element = requirement.elements.find((item) => item.id === elementId);
    if (element === undefined) continue;
    if (element.kind === "main_step" || element.kind === "alternative_step") {
      stepNumber += 1;
      markers.set(elementId, String(stepNumber));
      continue;
    }
    const marker = {
      constraint: "Constraint",
      precondition: "Pre",
      trigger: "Trigger",
      postcondition: "Post",
      alternative_postcondition: "Post",
    }[element.kind];
    if (marker !== undefined) markers.set(elementId, marker);
  }
  return markers;
}

export function strongestTargetScores(links: TraceLink[]): Map<string, number> {
  const scores = new Map<string, number>();
  for (const link of links) {
    const key = `${link.target.kind}:${link.target.targetId}`;
    scores.set(key, Math.max(scores.get(key) ?? 0, link.score));
  }
  return scores;
}

export function strongestTargetTones(
  links: TraceLink[],
  result: AnalysisResult,
  requirement: RequirementItem,
): Map<string, number> {
  const tones = new Map<string, number>();
  const priorities = new Map<string, number>();
  for (const link of links) {
    const key = `${link.target.kind}:${link.target.targetId}`;
    preferTargetColor(
      { priorities, tones },
      key,
      requirementElementPriority(result, requirement, link.requirementElementId),
      requirementElementTone(result, requirement, link.requirementElementId),
    );
  }
  return tones;
}

export function strongestTargetStepNumbers(
  links: TraceLink[],
  result: AnalysisResult,
  requirement: RequirementItem,
): Map<string, number[]> {
  const elementNumbers = new Map<string, Set<number>>();
  for (const path of pathsForRequirement(result, requirement.id)) {
    let stepNumber = 0;
    for (const elementId of path.elementIds) {
      const element = requirement.elements.find((item) => item.id === elementId);
      if (element?.kind !== "main_step" && element?.kind !== "alternative_step") continue;
      stepNumber += 1;
      const numbers = elementNumbers.get(elementId) ?? new Set<number>();
      numbers.add(stepNumber);
      elementNumbers.set(elementId, numbers);
    }
  }

  const targetNumbers = new Map<string, Set<number>>();
  for (const link of links) {
    if (link.requirementElementId === null) continue;
    const numbers = elementNumbers.get(link.requirementElementId);
    if (numbers === undefined) continue;
    const key = `${link.target.kind}:${link.target.targetId}`;
    const existing = targetNumbers.get(key) ?? new Set<number>();
    for (const number of numbers) existing.add(number);
    targetNumbers.set(key, existing);
  }

  return new Map(
    [...targetNumbers].map(([key, numbers]) => [key, [...numbers].sort((a, b) => a - b)]),
  );
}

export function requirementElementTone(
  result: AnalysisResult,
  requirement: RequirementItem,
  elementId: string | null,
): number {
  const priority = requirementElementPriority(result, requirement, elementId);
  return priority < 0 ? -1 : priority === 0 ? 0 : ((priority - 1) % 6) + 1;
}

function requirementElementPriority(
  result: AnalysisResult,
  requirement: RequirementItem,
  elementId: string | null,
): number {
  if (elementId === null) return -1;
  const element = requirement.elements.find((item) => item.id === elementId);
  if (element === undefined) return -1;
  if (
    ["constraint", "precondition", "trigger", "main_step", "postcondition"].includes(element.kind)
  ) {
    return 0;
  }
  const priorities = pathsForRequirement(result, requirement.id)
    .filter((item) => item.elementIds.includes(elementId))
    .map((item) => pathPriorityIndex(item, requirement));
  return priorities.length === 0 ? -1 : Math.min(...priorities);
}

function preferTargetColor(
  target: { priorities: Map<string, number>; tones: Map<string, number> },
  key: string,
  priority: number,
  tone: number,
): void {
  if (priority < 0 || tone < 0) return;
  const current = target.priorities.get(key);
  if (current !== undefined && current <= priority) return;
  target.priorities.set(key, priority);
  target.tones.set(key, tone);
}
