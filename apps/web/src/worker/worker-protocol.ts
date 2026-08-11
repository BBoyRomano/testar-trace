import type { AnalysisProgress } from "../types.ts";

export type WorkerOperation = "catalog" | "parse-requirements" | "parse-state-models" | "analyze";

export type WorkerRequest = {
  id: string;
  operation: WorkerOperation;
  payload: unknown;
};

export type WorkerResponse =
  | { id: string; type: "progress"; progress: AnalysisProgress }
  | { id: string; type: "result"; ok: true; value: unknown }
  | { id: string; type: "result"; ok: false; error: { name: string; message: string } };

export function isWorkerResponse(value: unknown): value is WorkerResponse {
  if (!isRecord(value) || typeof value.id !== "string") {
    return false;
  }
  if (value.type === "progress") return isProgress(value.progress);
  if (value.type !== "result" || typeof value.ok !== "boolean") return false;
  if (value.ok) {
    return "value" in value;
  }
  return (
    isRecord(value.error) &&
    typeof value.error.name === "string" &&
    typeof value.error.message === "string"
  );
}

function isProgress(value: unknown): value is AnalysisProgress {
  return (
    isRecord(value) &&
    typeof value.phase === "string" &&
    (value.message === null || typeof value.message === "string") &&
    (value.completed === null || isNonNegativeNumber(value.completed)) &&
    (value.total === null || isNonNegativeNumber(value.total)) &&
    isRecord(value.metadata)
  );
}

function isNonNegativeNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
