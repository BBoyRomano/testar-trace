import { isAnalysisResult, isRequirementBundle, isStateModelBundle } from "./result-files.ts";
import type { AnalysisResult, AnalysisRun, RequirementBundle, StateModelBundle } from "./types.ts";

const RUNS_KEY = "testar-trace.web.runs.v2";
const RESULTS_DB_NAME = "testar-trace.web.results";
const RESULTS_DATABASE_VERSION = 2;
const RESULTS_STORE_NAME = "analysis-results-v2";

export function loadRuns(): AnalysisRun[] {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(RUNS_KEY) ?? "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isPersistedRun).map((run) => ({
      ...run,
      status: run.status === "running" ? "cancelled" : run.status,
      progress: run.status === "running" ? 0 : run.progress,
      message:
        run.status === "running"
          ? "Analysis was interrupted."
          : run.status === "complete"
            ? ""
            : run.message,
      result: null,
      requirements: null,
      stateModels: null,
    }));
  } catch {
    return [];
  }
}

export function persistRuns(runs: AnalysisRun[]): void {
  localStorage.setItem(
    RUNS_KEY,
    JSON.stringify(
      runs.map((run) => ({
        id: run.id,
        title: run.title,
        status: run.status,
        methodId: run.methodId,
        methodName: run.methodName,
        createdAt: run.createdAt,
        progress: run.progress,
        message: run.status === "failed" || run.status === "cancelled" ? run.message : "",
        result: null,
      })),
    ),
  );
}

export async function hydrateRunResults(runs: AnalysisRun[]): Promise<AnalysisRun[]> {
  const db = await openResultsDatabase();
  try {
    return await Promise.all(
      runs.map(async (run) => {
        if (run.status !== "complete" || run.result !== null) return run;
        const stored = await getStoredAnalysis(db, run.id);
        return stored === null ? run : { ...run, ...stored };
      }),
    );
  } finally {
    db.close();
  }
}

export async function saveRunResult(run: AnalysisRun): Promise<void> {
  await saveRunResults([run]);
}

export async function saveRunResults(runs: AnalysisRun[], signal?: AbortSignal): Promise<void> {
  const storable = runs.filter(
    (run): run is AnalysisRun & { result: AnalysisResult } => run.result !== null,
  );
  if (storable.length === 0) return;
  signal?.throwIfAborted();
  const db = await openResultsDatabase();
  try {
    signal?.throwIfAborted();
    const transaction = db.transaction(RESULTS_STORE_NAME, "readwrite");
    const abort = (): void => {
      try {
        transaction.abort();
      } catch {
        // The transaction has already committed; the visible operation may finish normally.
      }
    };
    signal?.addEventListener("abort", abort, { once: true });
    try {
      const store = transaction.objectStore(RESULTS_STORE_NAME);
      for (const run of storable) {
        store.put(
          {
            result: run.result,
            requirements: run.requirements,
            stateModels: run.stateModels,
          } satisfies StoredAnalysis,
          run.id,
        );
      }
      await databaseTransaction(transaction);
    } finally {
      signal?.removeEventListener("abort", abort);
    }
  } finally {
    db.close();
  }
}

export async function deleteRunResult(runId: string): Promise<void> {
  const db = await openResultsDatabase();
  try {
    await databaseRequest(
      db.transaction(RESULTS_STORE_NAME, "readwrite").objectStore(RESULTS_STORE_NAME).delete(runId),
    );
  } finally {
    db.close();
  }
}

function openResultsDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(RESULTS_DB_NAME, RESULTS_DATABASE_VERSION);
    let blocked = false;
    request.onerror = () => reject(request.error);
    request.onblocked = () => {
      blocked = true;
      reject(new Error("Browser storage is blocked by another tab."));
    };
    request.onsuccess = () => {
      if (blocked) {
        request.result.close();
        return;
      }
      request.result.onversionchange = () => request.result.close();
      resolve(request.result);
    };
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(RESULTS_STORE_NAME)) {
        request.result.createObjectStore(RESULTS_STORE_NAME);
      }
    };
  });
}

type StoredAnalysis = {
  result: AnalysisResult;
  requirements: RequirementBundle | null;
  stateModels: StateModelBundle | null;
};

async function getStoredAnalysis(db: IDBDatabase, runId: string): Promise<StoredAnalysis | null> {
  const value = await databaseRequest(
    db.transaction(RESULTS_STORE_NAME, "readonly").objectStore(RESULTS_STORE_NAME).get(runId),
  );
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  const stored = value as Record<string, unknown>;
  if (!isAnalysisResult(stored.result)) return null;
  return {
    result: stored.result,
    requirements: isRequirementBundle(stored.requirements) ? stored.requirements : null,
    stateModels: isStateModelBundle(stored.stateModels) ? stored.stateModels : null,
  };
}

function databaseRequest(request: IDBRequest): Promise<unknown> {
  return new Promise((resolve, reject) => {
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function databaseTransaction(transaction: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    transaction.onabort = () => reject(transaction.error ?? abortError());
    transaction.onerror = () => reject(transaction.error ?? new Error("Browser storage failed."));
    transaction.oncomplete = () => resolve();
  });
}

function abortError(): DOMException {
  return new DOMException("The storage operation was cancelled.", "AbortError");
}

function isPersistedRun(value: unknown): value is AnalysisRun {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const run = value as Record<string, unknown>;
  return (
    typeof run.id === "string" &&
    typeof run.title === "string" &&
    ["running", "complete", "cancelled", "failed"].includes(String(run.status)) &&
    typeof run.methodId === "string" &&
    typeof run.methodName === "string" &&
    typeof run.createdAt === "string" &&
    typeof run.progress === "number" &&
    typeof run.message === "string" &&
    run.result === null
  );
}
