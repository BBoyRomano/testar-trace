import type { AnalysisRun, AnalysisSort, AnalysisStatusFilter } from "./types.ts";

export type AnalysisListOptions = {
  query: string;
  status: AnalysisStatusFilter;
  methodId: string;
  sort: AnalysisSort;
  page: number;
  pageSize: number;
};

export type AnalysisPage = {
  items: AnalysisRun[];
  filteredIds: string[];
  totalItems: number;
  totalPages: number;
  page: number;
  start: number;
  end: number;
};

export type AnalysisRowAction = "rename" | "duplicate" | "export" | "delete";

export function getAnalysisPage(runs: AnalysisRun[], options: AnalysisListOptions): AnalysisPage {
  const query = options.query.trim().toLocaleLowerCase();
  const filtered = runs.filter(
    (run) =>
      (query === "" ||
        `${run.title} ${run.methodName} ${run.status}`.toLocaleLowerCase().includes(query)) &&
      (options.status === "all" || run.status === options.status) &&
      (options.methodId === "all" || run.methodId === options.methodId),
  );
  filtered.sort((left, right) => compareRuns(left, right, options.sort));

  const pageSize = Math.max(1, Math.floor(options.pageSize));
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const page = Math.min(totalPages, Math.max(1, Math.floor(options.page)));
  const startIndex = (page - 1) * pageSize;
  const items = filtered.slice(startIndex, startIndex + pageSize);
  return {
    items,
    filteredIds: filtered.map((run) => run.id),
    totalItems: filtered.length,
    totalPages,
    page,
    start: filtered.length === 0 ? 0 : startIndex + 1,
    end: startIndex + items.length,
  };
}

export function overallCompleteness(run: AnalysisRun): number | null {
  if (run.status !== "complete" || run.result === null) return null;
  const summary = run.result.summary;
  if (summary.totalRequirements === 0 || summary.notAssessableRequirements > 0) return null;
  return summary.completeRequirements / summary.totalRequirements;
}

export function secondaryAnalysisActions(
  run: AnalysisRun,
  restoringResult = false,
): AnalysisRowAction[] {
  const resultWillBecomeAvailable = run.status === "running" || restoringResult;
  if (run.result === null && !resultWillBecomeAvailable) return ["rename", "delete"];
  return ["rename", "duplicate", "export", "delete"];
}

export function nextDuplicateTitle(title: string, existingTitles: Iterable<string>): string {
  const root = title.replace(/\s+\(copy(?:\s+\d+)?\)$/iu, "").trim() || title.trim();
  const existing = new Set(Array.from(existingTitles, (value) => value.trim().toLocaleLowerCase()));
  const firstCopy = `${root} (copy)`;
  if (!existing.has(firstCopy.toLocaleLowerCase())) return firstCopy;
  let index = 2;
  while (existing.has(`${root} (copy ${index})`.toLocaleLowerCase())) index += 1;
  return `${root} (copy ${index})`;
}

function compareRuns(left: AnalysisRun, right: AnalysisRun, sort: AnalysisSort): number {
  if (sort === "name-asc") return compareText(left.title, right.title) || newestFirst(left, right);
  if (sort === "created-asc")
    return timestamp(left) - timestamp(right) || compareText(left.title, right.title);
  if (sort === "completeness-desc") {
    return (
      (overallCompleteness(right) ?? -1) - (overallCompleteness(left) ?? -1) ||
      newestFirst(left, right)
    );
  }
  return newestFirst(left, right) || compareText(left.title, right.title);
}

function newestFirst(left: AnalysisRun, right: AnalysisRun): number {
  return timestamp(right) - timestamp(left);
}

function timestamp(run: AnalysisRun): number {
  const value = Date.parse(run.createdAt);
  return Number.isNaN(value) ? 0 : value;
}

function compareText(left: string, right: string): number {
  return left.localeCompare(right, undefined, { sensitivity: "base" });
}
