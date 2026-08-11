export interface AnalysisNameCounts {
  requirementCount?: number | undefined;
  stateModelCount?: number | undefined;
}

export function suggestedAnalysisName(counts: AnalysisNameCounts = {}): string {
  if (counts.requirementCount === undefined && counts.stateModelCount === undefined) {
    return "Untitled analysis";
  }
  const requirements =
    counts.requirementCount === undefined
      ? "Requirements"
      : countLabel(counts.requirementCount, "requirement");
  const stateModels =
    counts.stateModelCount === undefined
      ? "state models"
      : countLabel(counts.stateModelCount, "state model");
  return `${requirements} · ${stateModels}`;
}

export function analysisExportFileName(title: string): string {
  const normalized = title
    .normalize("NFKD")
    .replaceAll(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "-")
    .replaceAll(/^-+|-+$/g, "");
  return `${normalized || "analysis"}.testar-analysis.json`;
}

function countLabel(count: number, singular: string): string {
  return `${count} ${count === 1 ? singular : `${singular}s`}`;
}
