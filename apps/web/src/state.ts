import type {
  AnalysisRun,
  EvidenceBundle,
  FeedbackMessage,
  LoadState,
  ParserKey,
  RequirementBundle,
  TraceMethodKey,
  ViewName,
} from "./types";

const RUNS_KEY = "reqtrace.web.runs";
const RESULTS_DB_NAME = "reqtrace.web.results";
const RESULTS_STORE_NAME = "analysis-results";

export type AppState = {
  view: ViewName;
  loadState: LoadState;
  loadMessage: string;
  requirementsFeedback: FeedbackMessage | null;
  evidenceFeedback: FeedbackMessage | null;
  analysisFeedback: FeedbackMessage | null;
  requirements: RequirementBundle | null;
  evidence: EvidenceBundle | null;
  runs: AnalysisRun[];
  parsers: ParserKey[];
  methods: TraceMethodKey[];
  selectedMethod: TraceMethodKey;
  selectedRunId: string;
  selectedRequirementId: string;
  selectedScenarioId: string;
  selectedStepId: string;
  showFullEvidenceSource: boolean;
};

export function createInitialState(): AppState {
  const runs = loadRuns();
  return {
    view: "workspace",
    loadState: "empty",
    loadMessage: "",
    requirementsFeedback: null,
    evidenceFeedback: null,
    analysisFeedback: null,
    requirements: null,
    evidence: null,
    runs,
    parsers: [],
    methods: [],
    selectedMethod: "",
    selectedRunId: runs[0]?.id ?? "",
    selectedRequirementId: "",
    selectedScenarioId: "",
    selectedStepId: "",
    showFullEvidenceSource: false,
  };
}

export function loadRuns(): AnalysisRun[] {
  try {
    const value = localStorage.getItem(RUNS_KEY);
    const runs = value === null ? [] : (JSON.parse(value) as AnalysisRun[]);
    return runs.map((run) =>
      run.status === "running" ||
      (run.status === "failed" && run.message === "Analysis was interrupted before it finished.")
        ? {
            ...run,
            status: "cancelled",
            progress: 0,
            message: "Analysis was interrupted before it finished.",
          }
        : run,
    );
  } catch {
    return [];
  }
}

export function persistRuns(runs: AnalysisRun[]): void {
  try {
    localStorage.setItem(RUNS_KEY, JSON.stringify(runs.map(compactRun)));
  } catch (error) {
    console.warn("Could not persist ReqTrace runs.", error);
  }
}

export async function hydrateRunResults(runs: AnalysisRun[]): Promise<AnalysisRun[]> {
  const db = await openResultsDatabase();
  const hydrated = await Promise.all(
    runs.map(async (run) => {
      if (run.status !== "complete" || run.result !== null) {
        return run;
      }
      const result = await getStoredResult(db, run.id);
      return result === null ? run : { ...run, result };
    }),
  );
  db.close();
  return hydrated;
}

export async function saveRunResult(run: AnalysisRun): Promise<void> {
  if (run.result === null) {
    return;
  }
  const db = await openResultsDatabase();
  await putStoredResult(db, run.id, run.result);
  db.close();
}

export async function deleteRunResult(runId: string): Promise<void> {
  const db = await openResultsDatabase();
  await deleteStoredResult(db, runId);
  db.close();
}

function compactRun(run: AnalysisRun): AnalysisRun {
  return run.result === null ? run : { ...run, result: null };
}

function openResultsDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(RESULTS_DB_NAME, 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(RESULTS_STORE_NAME);
    };
  });
}

function getStoredResult(db: IDBDatabase, runId: string): Promise<AnalysisRun["result"]> {
  return new Promise((resolve, reject) => {
    const request = db
      .transaction(RESULTS_STORE_NAME, "readonly")
      .objectStore(RESULTS_STORE_NAME)
      .get(runId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve((request.result as AnalysisRun["result"]) ?? null);
  });
}

function putStoredResult(
  db: IDBDatabase,
  runId: string,
  result: NonNullable<AnalysisRun["result"]>,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = db
      .transaction(RESULTS_STORE_NAME, "readwrite")
      .objectStore(RESULTS_STORE_NAME)
      .put(result, runId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

function deleteStoredResult(db: IDBDatabase, runId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = db
      .transaction(RESULTS_STORE_NAME, "readwrite")
      .objectStore(RESULTS_STORE_NAME)
      .delete(runId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}
