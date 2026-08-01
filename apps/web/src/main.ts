import "./style.css";
import {
  analyzeViaApi,
  fetchAvailableMethods,
  fetchAvailableParsers,
  parseEvidenceViaApi,
  parseRequirementsViaApi,
  validateEvidenceViaApi,
  validateRequirementsViaApi,
} from "./api";
import { mountEvidenceGraph, mountSequenceEvidenceGraph } from "./evidence-graph";
import { readSourceFile, selectSupportedSourceFiles, sourceName } from "./source-files";
import {
  createInitialState,
  deleteRunResult,
  hydrateRunResults,
  persistRuns,
  saveRunResult,
} from "./state";
import type { AnalysisResult, AnalysisRun, RequirementBundle, ViewName } from "./types";
import {
  renderEvidenceDetail,
  renderRequirementsDetail,
  renderResultDetail,
  renderWorkspace,
  selectedCoverage,
  selectedScenario,
  selectedRun,
} from "./views";

const state = createInitialState();
const activeAnalysisAborts = new Map<string, AbortController>();
let cleanupEvidenceGraph: (() => void) | null = null;

const app = requiredElement(document.querySelector<HTMLDivElement>("#app"), "Missing #app root.");

app.innerHTML = `
  <div class="app-shell">
    <header class="app-header">
      <div>
        <p class="eyebrow">ReqTrace</p>
        <h1>Traceability workspace</h1>
      </div>
      <nav aria-label="Workspace navigation">
        <button type="button" data-action="show-workspace">Workspace</button>
        <button type="button" class="secondary" data-action="show-requirements">Requirements</button>
        <button type="button" class="secondary" data-action="show-evidence">Evidence</button>
        <button type="button" class="secondary" data-action="show-result">Result</button>
      </nav>
    </header>
    <main id="view" class="view" aria-live="polite"></main>
    <input id="requirements-file-input" type="file" hidden />
    <input id="requirements-directory-input" type="file" webkitdirectory multiple hidden />
    <input id="evidence-file-input" type="file" hidden />
    <input id="result-file-input" type="file" accept=".json" hidden />
  </div>
`;

const view = requiredElement(
  document.querySelector<HTMLDivElement>("#view"),
  "Missing #view root.",
);
const requirementsFileInput = requiredElement(
  document.querySelector<HTMLInputElement>("#requirements-file-input"),
  "Missing requirements file input.",
);
const requirementsDirectoryInput = requiredElement(
  document.querySelector<HTMLInputElement>("#requirements-directory-input"),
  "Missing requirements directory input.",
);
const evidenceFileInput = requiredElement(
  document.querySelector<HTMLInputElement>("#evidence-file-input"),
  "Missing evidence file input.",
);
const resultFileInput = requiredElement(
  document.querySelector<HTMLInputElement>("#result-file-input"),
  "Missing result file input.",
);

document.addEventListener("click", handleClick);
document.addEventListener("change", handleChange);
document.addEventListener("keydown", handleKeyDown);
requirementsFileInput.addEventListener("change", () => {
  void handleRequirementsFiles(Array.from(requirementsFileInput.files ?? []), "file");
  requirementsFileInput.value = "";
});
requirementsDirectoryInput.addEventListener("change", () => {
  void handleRequirementsFiles(Array.from(requirementsDirectoryInput.files ?? []), "directory");
  requirementsDirectoryInput.value = "";
});
evidenceFileInput.addEventListener("change", () => {
  const file = evidenceFileInput.files?.[0];
  if (file !== undefined) {
    void handleEvidenceFile(file);
  }
  evidenceFileInput.value = "";
});
resultFileInput.addEventListener("change", () => {
  const file = resultFileInput.files?.[0];
  if (file !== undefined) {
    void importResult(file);
  }
  resultFileInput.value = "";
});

render();
void loadParserCatalog();
void loadMethodCatalog();
void hydrateStoredRunResults();

function render(): void {
  cleanupEvidenceGraph?.();
  cleanupEvidenceGraph = null;
  view.innerHTML = renderCurrentView();
  if (state.view === "evidence" && state.evidence !== null) {
    cleanupEvidenceGraph = mountEvidenceGraph(state.evidence);
  }
  if (state.view === "result" && state.evidence !== null) {
    const run = selectedRun(state);
    const coverage =
      run?.result === null || run?.result === undefined
        ? null
        : selectedCoverage(state, run.result);
    const scenario = selectedScenario(state, coverage);
    if (scenario !== null) {
      cleanupEvidenceGraph = mountSequenceEvidenceGraph({
        evidence: state.evidence,
        scenario,
        selectedStepId: state.selectedStepId,
        onSelectStep: (stepId) => {
          state.selectedStepId = stepId;
          render();
        },
      });
    }
  }
  for (const button of document.querySelectorAll<HTMLButtonElement>("[data-action^='show-']")) {
    const action = button.dataset.action ?? "";
    const targetView = action.replace("show-", "");
    button.classList.toggle("active", targetView === state.view);
  }
}

function renderCurrentView(): string {
  if (state.view === "requirements") {
    return renderRequirementsDetail(state);
  }
  if (state.view === "evidence") {
    return renderEvidenceDetail(state);
  }
  if (state.view === "result") {
    return renderResultDetail(state);
  }
  return renderWorkspace(state);
}

function handleClick(event: MouseEvent): void {
  const control = (event.target as HTMLElement).closest<HTMLElement>("[data-action]");
  if (control === null) {
    return;
  }

  const action = control.dataset.action ?? "";
  if (action.startsWith("show-")) {
    showView(action.replace("show-", "") as ViewName);
    return;
  }

  switch (action) {
    case "load-requirements-file":
      requirementsFileInput.click();
      break;
    case "load-requirements-directory":
      requirementsDirectoryInput.click();
      break;
    case "load-evidence-file":
      evidenceFileInput.click();
      break;
    case "inspect-requirements":
      showView("requirements");
      break;
    case "inspect-evidence":
      showView("evidence");
      break;
    case "inspect-selected-result":
      showView("result");
      break;
    case "clear-requirements":
      state.requirements = null;
      state.selectedRequirementId = "";
      state.selectedScenarioId = "";
      state.requirementsFeedback = null;
      state.loadState = "empty";
      state.loadMessage = "";
      render();
      break;
    case "clear-evidence":
      state.evidence = null;
      state.evidenceFeedback = null;
      state.showFullEvidenceSource = false;
      state.loadState = "empty";
      state.loadMessage = "";
      render();
      break;
    case "start-analysis":
      void startAnalysis();
      break;
    case "cancel-selected":
      cancelSelectedAnalysis();
      break;
    case "import-result":
      resultFileInput.click();
      break;
    case "export-selected":
      exportSelectedRun();
      break;
    case "delete-selected":
      deleteSelectedRun();
      break;
    case "select-run":
      selectRun(control.dataset.runId ?? "");
      break;
    case "view-run":
      viewRun(control.dataset.runId ?? "");
      break;
    case "select-requirement":
      selectRequirement(control.dataset.requirementId ?? "");
      break;
    case "select-coverage":
      selectCoverage(control.dataset.requirementId ?? "");
      break;
    case "select-scenario":
      state.selectedScenarioId = control.dataset.scenarioId ?? "";
      state.selectedStepId = firstMatchedStepId();
      render();
      break;
    case "select-step":
      state.selectedStepId = control.dataset.stepId ?? "";
      render();
      break;
    case "toggle-full-evidence-source":
      state.showFullEvidenceSource = !state.showFullEvidenceSource;
      render();
      break;
    case "dismiss-requirements-feedback":
      state.requirementsFeedback = null;
      render();
      break;
    case "dismiss-evidence-feedback":
      state.evidenceFeedback = null;
      render();
      break;
    case "dismiss-analysis-feedback":
      state.analysisFeedback = null;
      render();
      break;
  }
}

function handleChange(event: Event): void {
  const control = event.target as HTMLElement;
  if (control instanceof HTMLSelectElement && control.id === "method-select") {
    state.selectedMethod = control.value;
  }
}

function handleKeyDown(event: KeyboardEvent): void {
  if (event.key !== "Enter" && event.key !== " ") {
    return;
  }
  const control = (event.target as HTMLElement).closest<HTMLElement>("[data-action='select-run']");
  if (control === null) {
    return;
  }
  event.preventDefault();
  selectRun(control.dataset.runId ?? "");
}

async function handleRequirementsFiles(
  files: File[],
  sourceKind: "file" | "directory",
): Promise<void> {
  const selected =
    sourceKind === "directory"
      ? selectSupportedSourceFiles(files, supportedFileFormats("requirements"))
      : files.filter((file) => supportedFileFormats("requirements").has(formatFromName(file.name)));
  if (selected.length === 0) {
    setSourceFeedback("requirements", "error", "No supported requirements files were selected.");
    return;
  }

  setSourceFeedback("requirements", "running", "Loading requirements...");
  try {
    const sources = await Promise.all(selected.map(readSourceFile));
    await validateRequirementsViaApi(sources);
    const requirements = await parseRequirementsViaApi(sources);
    if (requirements.length === 0) {
      throw new Error("No requirements were found in the selected source.");
    }
    const bundle: RequirementBundle = {
      id: crypto.randomUUID(),
      name: sourceKind === "directory" ? directoryName(selected) : sourceName(selected[0]),
      sourceKind,
      kind: "",
      loadedAt: new Date().toISOString(),
      sources,
      requirements,
    };
    state.requirements = bundle;
    state.selectedRequirementId = requirements[0]?.id ?? "";
    state.selectedScenarioId = requirements[0]?.scenarios[0]?.id ?? "";
    setSourceFeedback("requirements", "ready", `${requirements.length} requirements loaded.`);
  } catch (error) {
    setSourceFeedback("requirements", "error", errorToMessage(error));
  }
}

async function handleEvidenceFile(file: File): Promise<void> {
  setSourceFeedback("evidence", "running", "Loading evidence...");
  try {
    const source = await readSourceFile(file);
    await validateEvidenceViaApi(source);
    const evidence = await parseEvidenceViaApi(source);
    state.evidence = evidence;
    state.showFullEvidenceSource = false;
    setSourceFeedback(
      "evidence",
      "ready",
      `${evidence.stateCount} states and ${evidence.transitionCount} transitions loaded.`,
    );
  } catch (error) {
    setSourceFeedback("evidence", "error", errorToMessage(error));
  }
}

async function startAnalysis(): Promise<void> {
  if (state.requirements === null || state.evidence === null) {
    state.analysisFeedback = {
      state: "error",
      text: "Load both requirements and evidence before starting an analysis.",
    };
    render();
    return;
  }

  const method = state.selectedMethod;
  if (method === "") {
    state.analysisFeedback = {
      state: "error",
      text: "Trace methods are not available from the ReqTrace API.",
    };
    render();
    return;
  }
  const run: AnalysisRun = {
    id: crypto.randomUUID(),
    title: `${state.requirements.name} vs ${state.evidence.name}`,
    status: "running",
    method,
    createdAt: new Date().toISOString(),
    progress: 0.12,
    message: "Preparing analysis.",
    result: null,
  };
  state.runs = [run, ...state.runs];
  state.selectedRunId = run.id;
  persistRuns(state.runs);
  const abort = new AbortController();
  activeAnalysisAborts.set(run.id, abort);
  render();

  const progressTimer = window.setInterval(() => {
    if (run.status !== "running") {
      return;
    }
    run.progress = Math.min(0.88, run.progress + 0.08);
    run.message = progressMessage(run.progress);
    persistRuns(state.runs);
    render();
  }, 700);

  try {
    const result = await analyzeViaApi({
      method,
      requirements: state.requirements,
      evidence: state.evidence,
      signal: abort.signal,
    });
    run.status = "complete";
    run.progress = 1;
    run.message = "Analysis complete.";
    run.result = result;
    state.selectedRequirementId = result.coverage[0]?.requirementId ?? "";
    state.selectedScenarioId = result.coverage[0]?.scenarios[0]?.scenarioId ?? "";
    state.selectedStepId = firstMatchedStepId();
    try {
      await saveRunResult(run);
    } catch (error) {
      state.analysisFeedback = {
        state: "error",
        text: `Analysis completed, but browser history could not save the result: ${errorToMessage(error)}`,
      };
    }
    persistRuns(state.runs);
  } catch (error) {
    if (isAbortError(error)) {
      run.status = "cancelled";
      run.message = "Analysis cancelled.";
    } else {
      run.status = "failed";
      run.message = errorToMessage(error);
    }
  } finally {
    window.clearInterval(progressTimer);
    activeAnalysisAborts.delete(run.id);
    if (run.status !== "complete") {
      persistRuns(state.runs);
    }
    render();
  }
}

function cancelSelectedAnalysis(): void {
  const run = selectedRun(state);
  if (run === null) {
    return;
  }
  activeAnalysisAborts.get(run.id)?.abort();
}

async function importResult(file: File): Promise<void> {
  try {
    const result = JSON.parse(await file.text()) as AnalysisResult;
    if (typeof result.id !== "string" || typeof result.title !== "string") {
      throw new Error("Selected file is not a ReqTrace analysis result.");
    }
    const run: AnalysisRun = {
      id: result.id,
      title: result.title,
      status: "complete",
      method: result.method,
      createdAt: result.createdAt,
      progress: 1,
      message: "Imported result.",
      result,
    };
    state.runs = [run, ...state.runs.filter((item) => item.id !== run.id)];
    state.selectedRunId = run.id;
    await saveRunResult(run);
    persistRuns(state.runs);
    state.analysisFeedback = { state: "complete", text: "Analysis result imported." };
    render();
  } catch (error) {
    state.analysisFeedback = { state: "error", text: errorToMessage(error) };
    render();
  }
}

function exportSelectedRun(): void {
  const run = selectedRun(state);
  if (run?.result === null || run?.result === undefined) {
    state.analysisFeedback = { state: "error", text: "Select a completed result to export." };
    render();
    return;
  }
  const blob = new Blob([JSON.stringify(run.result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${run.result.id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function deleteSelectedRun(): void {
  const run = selectedRun(state);
  if (run === null || !window.confirm(`Delete analysis "${run.title}"?`)) {
    return;
  }
  if (run.status === "running") {
    activeAnalysisAborts.get(run.id)?.abort();
    activeAnalysisAborts.delete(run.id);
  }
  state.runs = state.runs.filter((item) => item.id !== run.id);
  state.selectedRunId = state.runs[0]?.id ?? "";
  void deleteRunResult(run.id);
  persistRuns(state.runs);
  render();
}

function selectRun(runId: string): void {
  state.selectedRunId = runId;
  const run = selectedRun(state);
  state.selectedRequirementId =
    run?.result?.coverage[0]?.requirementId ?? state.selectedRequirementId;
  state.selectedScenarioId =
    run?.result?.coverage[0]?.scenarios[0]?.scenarioId ?? state.selectedScenarioId;
  state.selectedStepId = firstMatchedStepId();
  render();
}

function viewRun(runId: string): void {
  state.selectedRunId = runId;
  const run = selectedRun(state);
  state.selectedRequirementId =
    run?.result?.coverage[0]?.requirementId ?? state.selectedRequirementId;
  state.selectedScenarioId =
    run?.result?.coverage[0]?.scenarios[0]?.scenarioId ?? state.selectedScenarioId;
  state.selectedStepId = firstMatchedStepId();
  state.view = "result";
  render();
}

function selectRequirement(requirementId: string): void {
  state.selectedRequirementId = requirementId;
  const requirement = state.requirements?.requirements.find((item) => item.id === requirementId);
  state.selectedScenarioId = requirement?.scenarios[0]?.id ?? "";
  render();
}

function selectCoverage(requirementId: string): void {
  state.selectedRequirementId = requirementId;
  const run = selectedRun(state);
  const coverage = run?.result?.coverage.find((item) => item.requirementId === requirementId);
  state.selectedScenarioId = coverage?.scenarios[0]?.scenarioId ?? "";
  state.selectedStepId = firstMatchedStepId();
  render();
}

function showView(viewName: ViewName): void {
  state.view = viewName;
  render();
}

function firstMatchedStepId(): string {
  const run = selectedRun(state);
  if (run?.result === null || run?.result === undefined) {
    return "";
  }
  const coverage = selectedCoverage(state, run.result);
  const scenario = selectedScenario(state, coverage);
  return scenario?.sequence.find((step) => step.matched)?.fragmentId ?? "";
}

async function loadParserCatalog(): Promise<void> {
  try {
    state.parsers = await fetchAvailableParsers();
    const formats = [...supportedFileFormats("requirements")].map((format) => `.${format}`);
    requirementsFileInput.accept = formats.join(",");
    requirementsDirectoryInput.accept = formats.join(",");
    evidenceFileInput.accept = [...supportedFileFormats("evidence")]
      .map((format) => `.${format}`)
      .join(",");
  } catch (error) {
    state.analysisFeedback = {
      state: "error",
      text: parserCatalogErrorMessage(error),
    };
  }
  render();
}

function setSourceFeedback(
  source: "requirements" | "evidence",
  loadState: typeof state.loadState,
  message: string,
): void {
  const feedback = { state: loadState, text: message };
  if (source === "requirements") {
    state.requirementsFeedback = feedback;
  } else {
    state.evidenceFeedback = feedback;
  }
  state.loadState = loadState;
  state.loadMessage = message;
  render();
}

async function loadMethodCatalog(): Promise<void> {
  try {
    const methods = await fetchAvailableMethods();
    state.methods = methods;
    if (!methods.includes(state.selectedMethod)) {
      state.selectedMethod = methods[0] ?? "";
    }
  } catch (error) {
    state.analysisFeedback = { state: "error", text: errorToMessage(error) };
  }
  render();
}

async function hydrateStoredRunResults(): Promise<void> {
  try {
    state.runs = await hydrateRunResults(state.runs);
  } catch (error) {
    state.analysisFeedback = { state: "error", text: errorToMessage(error) };
  }
  render();
}

function directoryName(files: File[]): string {
  const first = sourceName(files[0]);
  const parts = first.replaceAll("\\", "/").split("/");
  return parts.length > 1 ? parts[0] : "requirements directory";
}

function supportedFileFormats(artifact: string): Set<string> {
  const formats = new Set(
    state.parsers
      .filter((parser) => parser.artifact === artifact)
      .map((parser) => parser.format)
      .filter((format) => format !== "jira" && !format.endsWith("-api")),
  );
  return formats;
}

function formatFromName(name: string): string {
  const parts = name.split(".");
  return parts.length > 1 ? (parts.at(-1)?.toLowerCase() ?? "") : "";
}

function progressMessage(progress: number): string {
  if (progress < 0.35) {
    return "Preparing scenario paths.";
  }
  if (progress < 0.65) {
    return "Matching evidence candidates.";
  }
  return "Scoring candidate matches.";
}

function errorToMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function parserCatalogErrorMessage(error: unknown): string {
  const message = errorToMessage(error);
  return message === "Unknown endpoint."
    ? "ReqTrace API is running an older server. Restart it so parser discovery and automatic loading are available."
    : message;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function requiredElement<T extends Element>(element: T | null, message: string): T {
  if (element === null) {
    throw new Error(message);
  }
  return element;
}
