import type {
  AnalysisResult,
  AnalysisRun,
  PortableAnalysesBundle,
  PortableAnalysisBundle,
  RequirementBundle,
  StateModelBundle,
} from "./types.ts";

const MAX_ANALYSIS_IMPORT_BYTES = 50 * 1024 * 1024;

export function selectAnalysisImportFile<T extends { name: string; size?: number }>(files: T[]): T {
  if (files.length !== 1) {
    throw new Error("Choose one TESTAR Trace analysis file.");
  }
  const file = files[0];
  const name = file?.name.toLocaleLowerCase() ?? "";
  if (!name.endsWith(".testar-analysis.json") && !name.endsWith(".testar-analyses.json")) {
    throw new Error(
      "Choose a .testar-analysis.json or .testar-analyses.json file exported by TESTAR Trace.",
    );
  }
  if (typeof file?.size === "number" && file.size > MAX_ANALYSIS_IMPORT_BYTES) {
    throw new Error("The selected analysis file exceeds the supported 50 MiB limit.");
  }
  return file as T;
}

export function analysisImportOutcomeMessage(totalCount: number, updatedCount: number): string {
  const importedCount = totalCount - updatedCount;
  if (updatedCount === 0) {
    return importedCount === 1 ? "Analysis imported." : `${analysisCount(importedCount)} imported.`;
  }
  if (importedCount === 0) {
    return updatedCount === 1
      ? "Existing analysis updated."
      : `${analysisCount(updatedCount, "existing ")} updated.`;
  }
  return `${analysisCount(importedCount)} imported · ${updatedCount.toLocaleString()} updated.`;
}

function analysisCount(count: number, prefix = ""): string {
  return `${count} ${prefix}${count === 1 ? "analysis" : "analyses"}`;
}

export function parseAnalysisFile(text: string): PortableAnalysisBundle[] {
  const value = parseJson(text);
  assertSupportedEnvelopeVersion(value);
  if (isPortableAnalysisBundle(value)) return [value];
  if (isPortableAnalysesBundle(value)) return value.analyses;
  throw new Error("The selected file is not a supported TESTAR Trace analysis file.");
}

function assertSupportedEnvelopeVersion(value: unknown): void {
  if (!isRecord(value) || typeof value.kind !== "string") return;
  if (value.kind === "testar-trace-analysis" && value.schemaVersion !== 2) {
    throw new Error(
      `Analysis schema version ${String(value.schemaVersion)} is not supported. This version of TESTAR Trace supports version 2.`,
    );
  }
  if (value.kind === "testar-trace-analyses" && value.schemaVersion !== 1) {
    throw new Error(
      `Bulk analysis schema version ${String(value.schemaVersion)} is not supported. This version of TESTAR Trace supports version 1.`,
    );
  }
}

export function createPortableAnalysisBundle(run: AnalysisRun): PortableAnalysisBundle {
  if (run.status !== "complete" || run.result === null) {
    throw new Error("Only a completed analysis can be exported.");
  }
  if (run.requirements === null || run.stateModels === null) {
    throw new Error(
      "This analysis does not contain the requirements and state models needed for export.",
    );
  }
  return {
    kind: "testar-trace-analysis",
    schemaVersion: 2,
    exportedAt: new Date().toISOString(),
    analysis: {
      id: run.id,
      title: run.title,
      status: "complete",
      methodId: run.methodId,
      methodName: run.methodName,
      createdAt: run.createdAt,
    },
    requirements: run.requirements,
    stateModels: run.stateModels,
    result: run.result,
  };
}

export function createPortableAnalysesBundle(runs: AnalysisRun[]): PortableAnalysesBundle {
  if (runs.length === 0) throw new Error("Select at least one analysis to export.");
  return {
    kind: "testar-trace-analyses",
    schemaVersion: 1,
    exportedAt: new Date().toISOString(),
    analyses: runs.map(createPortableAnalysisBundle),
  };
}

function parseJson(text: string): unknown {
  let value: unknown;
  try {
    value = JSON.parse(text) as unknown;
  } catch (error) {
    throw new Error("The selected analysis file is not valid JSON.", { cause: error });
  }
  return value;
}

export function isPortableAnalysisBundle(value: unknown): value is PortableAnalysisBundle {
  if (
    !isRecord(value) ||
    value.kind !== "testar-trace-analysis" ||
    value.schemaVersion !== 2 ||
    typeof value.exportedAt !== "string" ||
    !isRecord(value.analysis)
  ) {
    return false;
  }
  return (
    hasStrings(value.analysis, ["id", "title", "methodId", "methodName", "createdAt"]) &&
    value.analysis.status === "complete" &&
    isRequirementBundle(value.requirements) &&
    isStateModelBundle(value.stateModels) &&
    isAnalysisResult(value.result) &&
    value.analysis.id === value.result.id
  );
}

export function isPortableAnalysesBundle(value: unknown): value is PortableAnalysesBundle {
  return (
    isRecord(value) &&
    value.kind === "testar-trace-analyses" &&
    value.schemaVersion === 1 &&
    typeof value.exportedAt === "string" &&
    Array.isArray(value.analyses) &&
    value.analyses.length > 0 &&
    value.analyses.every(isPortableAnalysisBundle)
  );
}

export function isAnalysisResult(value: unknown): value is AnalysisResult {
  if (!isRecord(value) || value.schemaVersion !== 1) {
    return false;
  }
  return (
    hasStrings(value, [
      "id",
      "title",
      "methodId",
      "methodName",
      "createdAt",
      "requirementsName",
      "stateModelsName",
    ]) &&
    typeof value.pathsExhaustive === "boolean" &&
    Array.isArray(value.paths) &&
    value.paths.every(isPath) &&
    Array.isArray(value.pathDiagnostics) &&
    value.pathDiagnostics.every(isPathDiagnostic) &&
    Array.isArray(value.assessments) &&
    value.assessments.every(isAssessment) &&
    Array.isArray(value.links) &&
    value.links.every(isLink) &&
    Array.isArray(value.occurrences) &&
    value.occurrences.every(isOccurrence) &&
    isSummary(value.summary)
  );
}

function isPath(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["id", "requirementId", "flowId", "title", "outcome", "resolution"]) &&
    hasStringArray(value.branchIds) &&
    (value.nodeIds === undefined || hasStringArray(value.nodeIds)) &&
    (value.edgeIds === undefined || hasStringArray(value.edgeIds)) &&
    hasStringArray(value.elementIds) &&
    isFiniteNumber(value.orderIndex)
  );
}

function isPathDiagnostic(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["code", "flowId", "message"]) &&
    isOptionalString(value.nodeId) &&
    isOptionalString(value.edgeId)
  );
}

export function isRequirementBundle(value: unknown): value is RequirementBundle {
  if (
    !isRecord(value) ||
    !hasStrings(value, ["id", "name", "loadedAt", "adapterId"]) ||
    !["files", "directory"].includes(String(value.sourceKind)) ||
    !Array.isArray(value.sources) ||
    !value.sources.every(isRawSource) ||
    !Array.isArray(value.requirements)
  ) {
    return false;
  }
  return value.requirements.every(
    (requirement) =>
      isRecord(requirement) &&
      hasStrings(requirement, ["id", "title", "summary", "actor", "sourceName"]) &&
      isOptionalString(requirement.body) &&
      isOptionalString(requirement.scope) &&
      isOptionalString(requirement.level) &&
      Array.isArray(requirement.elements) &&
      requirement.elements.every(isRequirementElement) &&
      Array.isArray(requirement.flows) &&
      requirement.flows.every(isRequirementFlow),
  );
}

export function isStateModelBundle(value: unknown): value is StateModelBundle {
  if (
    !isRecord(value) ||
    !hasStrings(value, ["id", "name", "loadedAt", "adapterId"]) ||
    !Array.isArray(value.sources) ||
    !value.sources.every(isRawSource) ||
    !Array.isArray(value.models)
  ) {
    return false;
  }
  return value.models.every(isStateModel);
}

function isRawSource(value: unknown): boolean {
  return isRecord(value) && hasStrings(value, ["id", "name", "format", "text"]);
}

function isRequirementElement(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["id", "requirementId", "kind", "text"]) &&
    (value.orderIndex === null || isFiniteNumber(value.orderIndex))
  );
}

function isRequirementFlow(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["id", "requirementId", "title", "entryNodeId"]) &&
    Array.isArray(value.branches) &&
    value.branches.every(
      (branch) =>
        isRecord(branch) &&
        hasStrings(branch, ["id", "title", "kind", "entryNodeId", "resolution"]),
    ) &&
    Array.isArray(value.nodes) &&
    value.nodes.every(
      (node) =>
        isRecord(node) &&
        hasStrings(node, ["id", "branchId", "elementId"]) &&
        isOptionalString(node.outcome),
    ) &&
    (value.edges === undefined ||
      (Array.isArray(value.edges) &&
        value.edges.every(
          (edge) =>
            isRecord(edge) && hasStrings(edge, ["id", "sourceNodeId", "targetNodeId", "kind"]),
        )))
  );
}

function isStateModel(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["id", "title", "layer"]) &&
    Array.isArray(value.entities) &&
    value.entities.every(
      (entity) => isRecord(entity) && hasStrings(entity, ["id", "kind", "label", "stateModelId"]),
    ) &&
    isRecord(value.graph) &&
    Array.isArray(value.graph.nodes) &&
    value.graph.nodes.every(
      (node) =>
        isRecord(node) && hasStrings(node, ["id", "label"]) && typeof node.initial === "boolean",
    ) &&
    Array.isArray(value.graph.edges) &&
    value.graph.edges.every(
      (edge) => isRecord(edge) && hasStrings(edge, ["id", "source", "target", "label", "actionId"]),
    ) &&
    isRecord(value.counts)
  );
}

function isAssessment(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, [
      "id",
      "scopeKind",
      "scopeId",
      "viewKind",
      "status",
      "assessability",
      "completeness",
      "rationale",
    ]) &&
    hasStringArray(value.requirementIds) &&
    hasStringArray(value.stateModelIds) &&
    hasStringArray(value.occurrenceIds) &&
    hasStringArray(value.coveredElementIds) &&
    hasStringArray(value.missingElementIds) &&
    (value.coverageRatio === null || isFiniteNumber(value.coverageRatio))
  );
}

function isLink(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["id", "requirementId", "stateModelId", "rationale"]) &&
    (value.requirementElementId === null || typeof value.requirementElementId === "string") &&
    (value.occurrenceId === null || typeof value.occurrenceId === "string") &&
    isFiniteNumber(value.score) &&
    isTarget(value.target)
  );
}

function isOccurrence(value: unknown): boolean {
  return (
    isRecord(value) &&
    hasStrings(value, ["id", "requirementId", "flowId", "pathId", "stateModelId", "status"]) &&
    (value.score === null || isFiniteNumber(value.score)) &&
    Array.isArray(value.targetPath) &&
    value.targetPath.every(isTarget) &&
    hasStringArray(value.coveredElementIds) &&
    hasStringArray(value.missingElementIds) &&
    hasStringArray(value.linkIds)
  );
}

function isTarget(value: unknown): boolean {
  return isRecord(value) && hasStrings(value, ["kind", "targetId"]);
}

function isSummary(value: unknown): boolean {
  if (!isRecord(value)) {
    return false;
  }
  const numberKeys = [
    "totalRequirements",
    "coveredRequirements",
    "partiallyCoveredRequirements",
    "uncoveredRequirements",
    "completeRequirements",
    "incompleteRequirements",
    "notAssessableRequirements",
    "totalPaths",
    "completePaths",
    "incompletePaths",
    "notAssessablePaths",
    "totalLinks",
    "totalOccurrences",
  ];
  return (
    numberKeys.every((key) => isFiniteNumber(value[key])) &&
    (value.overallCoverageRatio === null || isFiniteNumber(value.overallCoverageRatio))
  );
}

function hasStrings(value: Record<string, unknown>, keys: string[]): boolean {
  return keys.every((key) => typeof value[key] === "string");
}

function hasStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isOptionalString(value: unknown): boolean {
  return value === undefined || value === null || typeof value === "string";
}
