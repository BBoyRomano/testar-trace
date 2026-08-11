import "./style.css";

import { getAnalysisPage, nextDuplicateTitle } from "./analysis-list.ts";
import { analysisExportFileName, suggestedAnalysisName } from "./analysis-names.ts";
import { mountAppShell } from "./app-elements.ts";
import { renderAppShell } from "./app-shell.ts";
import { analyze, fetchCatalog, parseRequirements, parseStateModels } from "./engine.ts";
import { userFacingErrorMessage } from "./error-message.ts";
import { icon } from "./icons.ts";
import {
  bestEvidenceStateModelId,
  filterResultRequirementIds,
  occurrenceTargetEvidence,
  occurrencesForScope,
  resolveResultScope,
} from "./result-scope.ts";
import { parseRoute, routePath, type AppRoute } from "./routes.ts";
import { analysisImportOutcomeMessage } from "./result-files.ts";
import { backgroundRunFeedback } from "./run-feedback.ts";
import {
  filesFromDataTransfer,
  mergeRawSources,
  readSourceFile,
  selectSupportedSourceFiles,
  sourceName,
  validateSourceFiles,
} from "./source-files.ts";
import {
  createInitialState,
  deleteRunResult,
  hydrateRunResults,
  persistRuns,
  saveRunResult,
  saveRunResults,
} from "./state.ts";
import type {
  AnalysisRun,
  AnalysisProgress,
  AnalysisSort,
  AnalysisStatusFilter,
  FeedbackMessage,
  RawSource,
  ResultRequirementFilter,
  SelectableResultScopeKind,
  ViewName,
} from "./types.ts";
import {
  exportAnalysesInBackground,
  importAnalysisInBackground,
} from "./worker/transfer-client.ts";
import type { StateModelGraphController, StateModelGraphInput } from "./state-model-graph.ts";
import {
  methodDescription,
  renderAnalysesOverview,
  renderNewAnalysis,
  renderRequirementsDetail,
  renderResultDetail,
  renderResultPathPanel,
  renderStateModelsDetail,
  selectedRun,
} from "./views.ts";

const state = createInitialState();
const activeAnalysisAborts = new Map<string, AbortController>();
let graphController: StateModelGraphController | null = null;
let graphMountRequest = 0;
let searchRenderTimer: number | null = null;
let resultSearchRenderTimer: number | null = null;
let requirementSearchRenderTimer: number | null = null;
let importDialogTrigger: HTMLElement | null = null;
let activeImportAbort: AbortController | null = null;
let activeExportAbort: AbortController | null = null;
let progressRenderFrame: number | null = null;
let confirmationResolve: ((confirmed: boolean) => void) | null = null;
let feedbackToastTimer: number | null = null;
let scheduledFeedbackToast: FeedbackMessage | null = null;
let catalogLoadPromise: Promise<void> | null = null;

const FEEDBACK_TOAST_DURATION_MS = 8_000;

const {
  view,
  globalNewAnalysisButton,
  helpDialog,
  importDialog,
  confirmationDialog,
  confirmationDialogTitle,
  confirmationDialogMessage,
  confirmationCancelButton,
  confirmationConfirmButton,
  requirementsFileInput,
  requirementsDirectoryInput,
  stateModelFileInput,
  stateModelDirectoryInput,
  importFileInput,
} = mountAppShell(renderAppShell());

document.addEventListener("click", handleClick);
document.addEventListener("change", handleChange);
document.addEventListener("input", handleInput);
document.addEventListener("keydown", handleKeyDown);
document.addEventListener("submit", handleSubmit);
document.addEventListener("toggle", handlePopoverToggle, true);
document.addEventListener("dragover", handleDragOver);
document.addEventListener("dragleave", handleDragLeave);
document.addEventListener("drop", handleDrop);
requirementsFileInput.addEventListener("change", () => {
  void loadRequirementFiles(Array.from(requirementsFileInput.files ?? []), "files");
  requirementsFileInput.value = "";
});
requirementsDirectoryInput.addEventListener("change", () => {
  void loadRequirementFiles(Array.from(requirementsDirectoryInput.files ?? []), "directory");
  requirementsDirectoryInput.value = "";
});
stateModelFileInput.addEventListener("change", () => {
  void loadStateModelFiles(Array.from(stateModelFileInput.files ?? []));
  stateModelFileInput.value = "";
});
stateModelDirectoryInput.addEventListener("change", () => {
  void loadStateModelFiles(Array.from(stateModelDirectoryInput.files ?? []));
  stateModelDirectoryInput.value = "";
});
importFileInput.addEventListener("change", () => {
  void importAnalysisFiles(Array.from(importFileInput.files ?? []));
  importFileInput.value = "";
});
importDialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeImportDialog();
});
confirmationDialog.addEventListener("close", () => {
  confirmationResolve?.(confirmationDialog.returnValue === "confirm");
  confirmationResolve = null;
});
window.addEventListener("popstate", applyRouteFromLocation);
window.addEventListener("beforeunload", handleBeforeUnload);

applyRouteFromLocation();
void hydrateStoredRunResults();

interface RenderOptions {
  preserveGraph?: boolean;
  preserveScroll?: boolean;
}

interface ScrollSnapshot {
  left: number;
  top: number;
  elements: Map<string, { left: number; top: number }>;
}

function render(options: RenderOptions = {}): void {
  const currentGraphRequest = ++graphMountRequest;
  const scrollSnapshot = options.preserveScroll ? captureScrollPositions() : null;
  const currentModelId = selectedModelId();
  const currentGraphContainer = document.querySelector<HTMLElement>("#state-model-graph");
  const preserveGraph =
    options.preserveGraph === true &&
    graphController !== null &&
    graphController.modelId === currentModelId &&
    currentGraphContainer !== null;
  const graphHoldingArea = preserveGraph ? document.createDocumentFragment() : null;
  if (graphHoldingArea !== null && currentGraphContainer !== null) {
    graphHoldingArea.append(currentGraphContainer);
  } else {
    graphController?.destroy();
    graphController = null;
  }
  view.ariaBusy = String(
    state.loadState === "running" ||
      (state.view === "result" && state.resultsLoadState === "loading"),
  );
  view.innerHTML = renderCurrentView();
  if (currentGraphContainer !== null && graphHoldingArea !== null) {
    document.querySelector("#state-model-graph")?.replaceWith(currentGraphContainer);
  }
  for (const checkbox of document.querySelectorAll<HTMLInputElement>(
    'input[data-indeterminate="true"]',
  )) {
    checkbox.indeterminate = true;
  }
  document.title = currentDocumentTitle();
  globalNewAnalysisButton.disabled = state.view === "new-analysis";
  globalNewAnalysisButton.classList.toggle("current-view-action", state.view === "new-analysis");
  if (scrollSnapshot !== null) restoreScrollPositions(scrollSnapshot);
  syncFeedbackToastTimer();
  void mountCurrentGraph(currentGraphRequest, preserveGraph);
}

function syncFeedbackToastTimer(): void {
  const feedback = state.analysisFeedback;
  const dismissAutomatically = feedback?.presentation === "toast" && feedback.state === "complete";
  if (dismissAutomatically && feedback === scheduledFeedbackToast) return;
  if (feedbackToastTimer !== null) window.clearTimeout(feedbackToastTimer);
  feedbackToastTimer = null;
  scheduledFeedbackToast = dismissAutomatically ? feedback : null;
  if (scheduledFeedbackToast === null) return;
  const scheduled = scheduledFeedbackToast;
  feedbackToastTimer = window.setTimeout(() => {
    feedbackToastTimer = null;
    scheduledFeedbackToast = null;
    if (state.analysisFeedback !== scheduled) return;
    state.analysisFeedback = null;
    renderPreservingViewport();
  }, FEEDBACK_TOAST_DURATION_MS);
}

function currentDocumentTitle(): string {
  if (state.view === "new-analysis") return "New analysis · TESTAR Trace";
  if (state.view === "requirements") return "Review requirements · TESTAR Trace";
  if (state.view === "state-models") return "Review state models · TESTAR Trace";
  if (state.view === "result") {
    const run = selectedRun(state);
    return run === null ? "Results · TESTAR Trace" : `${run.title} · TESTAR Trace`;
  }
  return "Analyses · TESTAR Trace";
}

function renderCurrentView(): string {
  if (state.view === "analyses") return renderAnalysesOverview(state);
  if (state.view === "new-analysis") return renderNewAnalysis(state);
  if (state.view === "requirements") return renderRequirementsDetail(state);
  if (state.view === "state-models") return renderStateModelsDetail(state);
  if (state.view === "result") return renderResultDetail(state);
  return renderAnalysesOverview(state);
}

async function mountCurrentGraph(requestId: number, reuseGraph = false): Promise<void> {
  const models = state.stateModels?.models ?? [];
  const model = models.find((item) => item.id === state.selectedStateModelId) ?? models[0];
  const container = document.querySelector<HTMLElement>("#state-model-graph");
  if (model === undefined || container === null) return;
  container.ariaBusy = "true";
  const graphInput = currentGraphInput(model);
  try {
    const { mountStateModelGraph } = await import("./state-model-graph.ts");
    if (
      requestId !== graphMountRequest ||
      !container.isConnected ||
      document.querySelector("#state-model-graph") !== container
    )
      return;
    container.ariaBusy = "false";
    if (reuseGraph && graphController?.modelId === model.id) {
      graphController.updateEvidence(graphInput);
      window.requestAnimationFrame(() => graphController?.resize());
    } else {
      graphController?.destroy();
      graphController = mountStateModelGraph(graphInput, container);
    }
  } catch (error) {
    if (requestId !== graphMountRequest || !container.isConnected) return;
    container.ariaBusy = "false";
    container.innerHTML = `<div class="empty-state"><strong>Graph unavailable</strong><p>The state model could not be displayed.</p></div>`;
    console.error("Could not render the state-model graph.", error);
  }
}

function currentGraphInput(
  model: NonNullable<typeof state.stateModels>["models"][number],
): StateModelGraphInput {
  const graphInput: StateModelGraphInput = { model };
  const run = selectedRun(state);
  if (state.view === "result" && run?.result !== null && run?.result !== undefined) {
    const scope = resolveResultScope(
      run.result,
      state.selectedRequirementId,
      state.selectedResultScopeId,
      state.selectedElementId,
      state.selectedResultScopeKind,
      state.requirements?.requirements.find((item) => item.id === state.selectedRequirementId),
    );
    const occurrences = occurrencesForScope(run.result, scope, model.id);
    const requirement = state.requirements?.requirements.find(
      (item) => item.id === scope.requirementId,
    );
    if (requirement !== undefined) {
      const evidence = occurrenceTargetEvidence(
        run.result,
        occurrences,
        requirement,
        scope.kind === "element" ? scope.elementIds : null,
        model,
      );
      graphInput.targetScores = evidence.scores;
      graphInput.targetMarkers = evidence.markers;
      graphInput.targetTones = evidence.tones;
      graphInput.targetPriorities = evidence.priorities;
      graphInput.directTargets = evidence.directTargets;
    }
  }
  return graphInput;
}

function selectedModelId(): string | null {
  const models = state.stateModels?.models ?? [];
  return models.find((item) => item.id === state.selectedStateModelId)?.id ?? models[0]?.id ?? null;
}

function captureScrollPositions(): ScrollSnapshot {
  const elements = new Map<string, { left: number; top: number }>();
  for (const element of document.querySelectorAll<HTMLElement>("[data-scroll-key]")) {
    const key = element.dataset.scrollKey;
    if (key !== undefined) elements.set(key, { left: element.scrollLeft, top: element.scrollTop });
  }
  return { left: window.scrollX, top: window.scrollY, elements };
}

function restoreScrollPositions(snapshot: ScrollSnapshot): void {
  const restore = (): void => {
    window.scrollTo(snapshot.left, snapshot.top);
    for (const [key, position] of snapshot.elements) {
      const element = document.querySelector<HTMLElement>(`[data-scroll-key="${key}"]`);
      if (element !== null) {
        element.scrollLeft = position.left;
        element.scrollTop = position.top;
      }
    }
  };
  restore();
  window.requestAnimationFrame(restore);
}

function renderResultInteraction(options: { preserveGraph?: boolean } = {}): void {
  render({ preserveGraph: options.preserveGraph ?? true, preserveScroll: true });
}

function updateResultEvidenceInteraction(
  options: {
    updatePathPanel?: boolean;
    updateGraph?: boolean;
  } = {},
): void {
  const scrollSnapshot = captureScrollPositions();
  const run = selectedRun(state);
  const requirement = state.requirements?.requirements.find(
    (item) => item.id === state.selectedRequirementId,
  );
  const result = run?.result;
  const workspace = document.querySelector<HTMLElement>(".path-evidence-workspace");
  const pathPanel = document.querySelector<HTMLElement>("#path-workspace-panel");
  const model =
    state.stateModels?.models.find((item) => item.id === state.selectedStateModelId) ??
    state.stateModels?.models[0];
  if (
    result === null ||
    result === undefined ||
    requirement === undefined ||
    workspace === null ||
    pathPanel === null ||
    model === undefined ||
    graphController?.modelId !== model.id
  ) {
    renderResultInteraction();
    return;
  }

  if (options.updatePathPanel ?? true) {
    const pathScrollTop = pathPanel.scrollTop;
    pathPanel.innerHTML = renderResultPathPanel(requirement, result, state);
    pathPanel.scrollTop = pathScrollTop;
  }
  workspace.classList.toggle("workspace-view-paths", state.resultWorkspaceTab === "paths");
  workspace.classList.toggle("workspace-view-graph", state.resultWorkspaceTab === "graph");
  for (const tab of workspace.querySelectorAll<HTMLButtonElement>("[data-workspace-tab]")) {
    const selected = tab.dataset.workspaceTab === state.resultWorkspaceTab;
    tab.classList.toggle("selected", selected);
    tab.ariaSelected = String(selected);
  }
  if (options.updateGraph ?? true) {
    graphController.updateEvidence(currentGraphInput(model));
  }
  restoreScrollPositions(scrollSnapshot);
  window.requestAnimationFrame(() => graphController?.resize());
}

function resetResultPathScroll(): void {
  const pathPanel = document.querySelector<HTMLElement>("#path-workspace-panel");
  if (pathPanel !== null) pathPanel.scrollTop = 0;
}

function handleClick(event: MouseEvent): void {
  const routeLink = closestElement(event.target, "a[data-route]");
  if (routeLink !== null) {
    const href = routeLink.getAttribute("href");
    const route = href === null ? null : parseRoute(new URL(href, window.location.href).pathname);
    if (route !== null) {
      event.preventDefault();
      navigateToRoute(route);
      return;
    }
  }
  const control = closestElement(event.target, "[data-action]");
  if (control === null) return;
  const action = control.dataset.action ?? "";
  const actionMenu = control.closest<HTMLElement>("[data-run-actions-menu]");
  if (actionMenu?.matches(":popover-open")) actionMenu.hidePopover();
  if (action.startsWith("show-")) {
    const candidate = action.slice(5);
    if (isViewName(candidate)) showView(candidate);
    return;
  }

  switch (action) {
    case "start-new-analysis":
      beginNewAnalysis();
      break;
    case "open-help":
      helpDialog.showModal();
      break;
    case "close-help":
      helpDialog.close();
      break;
    case "open-import-dialog":
      importDialogTrigger = control;
      setImportFeedback();
      importDialog.showModal();
      document.querySelector<HTMLButtonElement>("#choose-import-file")?.focus();
      break;
    case "close-import-dialog":
      closeImportDialog();
      break;
    case "choose-import-file":
      importFileInput.click();
      break;
    case "cancel-import":
      activeImportAbort?.abort();
      break;
    case "load-requirements-files":
      requirementsFileInput.click();
      break;
    case "load-requirements-directory":
      requirementsDirectoryInput.click();
      break;
    case "load-state-model-files":
      stateModelFileInput.click();
      break;
    case "load-state-model-directory":
      stateModelDirectoryInput.click();
      break;
    case "remove-requirement-source":
      void removeRequirementSource(control.dataset.sourceId ?? "");
      break;
    case "remove-state-model-source":
      void removeStateModelSource(control.dataset.sourceId ?? "");
      break;
    case "clear-requirements":
      state.requirements = null;
      state.requirementsFeedback = null;
      state.selectedRequirementId = "";
      state.requirementQuery = "";
      render();
      break;
    case "clear-state-models":
      state.stateModels = null;
      state.stateModelsFeedback = null;
      state.selectedStateModelId = "";
      render();
      break;
    case "start-analysis":
      void startAnalysis();
      break;
    case "cancel-run":
      cancelAnalysis(control.dataset.runId ?? "");
      break;
    case "export-run":
      exportRun(control.dataset.runId ?? "");
      break;
    case "export-selected-runs":
      exportSelectedRuns();
      break;
    case "cancel-export":
      activeExportAbort?.abort();
      break;
    case "delete-run":
      void deleteRun(control.dataset.runId ?? "");
      break;
    case "delete-selected-runs":
      void deleteSelectedRuns();
      break;
    case "clear-analysis-selection":
      clearAnalysisSelectionAndRestoreFocus();
      break;
    case "select-all-filtered-analyses":
      state.selectedAnalysisIds = getAnalysisPage(state.runs, analysisListOptions()).filteredIds;
      renderPreservingViewport();
      announceAnalysisSelection();
      break;
    case "rename-run":
      beginRenameRun(control.dataset.runId ?? "");
      break;
    case "cancel-rename-run":
      cancelRenameRun();
      break;
    case "duplicate-run":
      void duplicateRun(control.dataset.runId ?? "");
      break;
    case "reset-analysis-filters":
      resetAnalysisFilters();
      break;
    case "reset-result-requirement-filters":
      state.resultRequirementQuery = "";
      state.resultRequirementFilter = "all";
      ensureSelectedResultRequirement();
      renderResultInteraction();
      break;
    case "reset-requirement-search":
      state.requirementQuery = "";
      ensureSelectedStandaloneRequirement();
      render();
      break;
    case "graph-fit":
      graphController?.fit();
      break;
    case "graph-zoom-in":
      graphController?.zoomIn();
      break;
    case "graph-zoom-out":
      graphController?.zoomOut();
      break;
    case "previous-analysis-page":
      state.analysisPage = Math.max(1, state.analysisPage - 1);
      render();
      break;
    case "next-analysis-page":
      state.analysisPage += 1;
      render();
      break;
    case "select-requirement":
      resetResultPathScroll();
      state.selectedRequirementId = control.dataset.requirementId ?? "";
      state.selectedResultScopeKind = "requirement";
      state.selectedResultScopeId = state.selectedRequirementId;
      state.selectedElementId = "";
      state.resultWorkspaceTab = "graph";
      if (state.view === "result") {
        selectBestEvidenceModelForCurrentScope();
        renderResultInteraction();
      } else render({ preserveScroll: true });
      restoreRequirementSelectionFocus();
      announceSelection(`Requirement ${state.selectedRequirementId} selected.`);
      break;
    case "select-result-scope":
      if (isSelectableResultScopeKind(control.dataset.scopeKind)) {
        state.selectedResultScopeKind = control.dataset.scopeKind;
        state.selectedResultScopeId = control.dataset.scopeId ?? state.selectedRequirementId;
        state.selectedElementId = "";
        selectBestEvidenceModelForCurrentScope();
        renderResultInteraction();
      }
      break;
    case "select-path":
      resetResultPathScroll();
      state.selectedResultScopeKind = (control.dataset.scopeKind ??
        "path") as typeof state.selectedResultScopeKind;
      state.selectedResultScopeId = control.dataset.scopeId ?? control.dataset.pathId ?? "";
      state.selectedElementId = "";
      state.resultWorkspaceTab = state.selectedResultScopeKind === "path" ? "paths" : "graph";
      selectBestEvidenceModelForCurrentScope();
      updateResultEvidenceInteraction();
      break;
    case "select-path-step":
      state.selectedElementId =
        state.selectedElementId === (control.dataset.elementId ?? "")
          ? ""
          : (control.dataset.elementId ?? "");
      state.resultWorkspaceTab = "graph";
      updateResultEvidenceInteraction();
      break;
    case "set-result-workspace-tab":
      if (control.dataset.workspaceTab === "paths" || control.dataset.workspaceTab === "graph") {
        state.resultWorkspaceTab = control.dataset.workspaceTab;
      }
      updateResultEvidenceInteraction({ updatePathPanel: false, updateGraph: false });
      break;
    case "dismiss-requirements-feedback":
      state.requirementsFeedback = null;
      render();
      break;
    case "dismiss-state-models-feedback":
      state.stateModelsFeedback = null;
      render();
      break;
    case "dismiss-analysis-feedback":
      state.analysisFeedback = null;
      syncFeedbackToastTimer();
      render();
      break;
    case "view-analysis": {
      const runId = control.dataset.runId ?? "";
      state.analysisFeedback = null;
      syncFeedbackToastTimer();
      if (state.runs.some((run) => run.id === runId)) {
        state.selectedRunId = "";
        navigateToRoute({ view: "result", runId });
      } else {
        navigateToRoute({ view: "analyses" });
      }
      break;
    }
  }
}

function handleChange(event: Event): void {
  const target = event.target;
  if (!(target instanceof HTMLSelectElement || target instanceof HTMLInputElement)) return;
  if (target.id === "method-select") {
    state.selectedMethodId = target.value;
    const help = document.querySelector<HTMLElement>("#method-select-help");
    if (help !== null) help.textContent = methodDescription(target.value);
  }
  if (target.id === "state-model-select") {
    state.selectedStateModelId = target.value;
    if (state.view === "result") renderResultInteraction({ preserveGraph: false });
    else render();
  }
  if (target.id === "result-path-select") {
    resetResultPathScroll();
    const requirementId = target.dataset.requirementId ?? state.selectedRequirementId;
    state.selectedResultScopeKind = target.value === "" ? "requirement" : "path";
    state.selectedResultScopeId = target.value === "" ? requirementId : target.value;
    state.selectedElementId = "";
    state.resultWorkspaceTab = target.value === "" ? "graph" : "paths";
    selectBestEvidenceModelForCurrentScope();
    updateResultEvidenceInteraction();
  }
  if (target.id === "analysis-status-filter" && isAnalysisStatusFilter(target.value)) {
    state.analysisStatusFilter = target.value;
    state.analysisPage = 1;
    render();
    announceAnalysisResults();
  }
  if (target.id === "analysis-method-filter") {
    state.analysisMethodFilter = target.value;
    state.analysisPage = 1;
    render();
    announceAnalysisResults();
  }
  if (target.id === "analysis-sort" && isAnalysisSort(target.value)) {
    state.analysisSort = target.value;
    state.analysisPage = 1;
    render();
  }
  if (target instanceof HTMLInputElement && target.id === "select-page-analyses") {
    const visibleIds = Array.from(
      document.querySelectorAll<HTMLInputElement>("[data-analysis-select]"),
      (checkbox) => checkbox.dataset.analysisSelect ?? "",
    ).filter((id) => id !== "");
    setAnalysisSelection(visibleIds, target.checked);
    renderPreservingViewport();
    announceAnalysisSelection();
  }
  if (target instanceof HTMLInputElement && target.dataset.analysisSelect !== undefined) {
    setAnalysisSelection([target.dataset.analysisSelect], target.checked);
    renderPreservingViewport();
    announceAnalysisSelection();
  }
  if (target.id === "result-requirement-filter" && isResultRequirementFilter(target.value)) {
    state.resultRequirementFilter = target.value;
    ensureSelectedResultRequirement();
    renderResultInteraction();
  }
}

function handleInput(event: Event): void {
  const target = event.target;
  if (!(target instanceof HTMLInputElement)) return;
  if (target.id === "analysis-search") {
    state.analysisQuery = target.value;
    state.analysisPage = 1;
    if (searchRenderTimer !== null) window.clearTimeout(searchRenderTimer);
    searchRenderTimer = window.setTimeout(() => {
      render();
      const search = document.querySelector<HTMLInputElement>("#analysis-search");
      search?.focus();
      search?.setSelectionRange(search.value.length, search.value.length);
      announceAnalysisResults();
      searchRenderTimer = null;
    }, 120);
  }
  if (target.id === "analysis-name") state.analysisName = target.value;
  if (target.id === "rename-run-input") state.renameDraft = target.value;
  if (target.id === "result-requirement-search") {
    state.resultRequirementQuery = target.value;
    if (resultSearchRenderTimer !== null) window.clearTimeout(resultSearchRenderTimer);
    resultSearchRenderTimer = window.setTimeout(() => {
      ensureSelectedResultRequirement();
      renderResultInteraction();
      const search = document.querySelector<HTMLInputElement>("#result-requirement-search");
      search?.focus();
      search?.setSelectionRange(search.value.length, search.value.length);
      resultSearchRenderTimer = null;
    }, 120);
  }
  if (target.id === "requirement-search") {
    state.requirementQuery = target.value;
    if (requirementSearchRenderTimer !== null) window.clearTimeout(requirementSearchRenderTimer);
    requirementSearchRenderTimer = window.setTimeout(() => {
      ensureSelectedStandaloneRequirement();
      render({ preserveScroll: true });
      const search = document.querySelector<HTMLInputElement>("#requirement-search");
      search?.focus();
      search?.setSelectionRange(search.value.length, search.value.length);
      requirementSearchRenderTimer = null;
    }, 120);
  }
}

function renderPreservingViewport(): void {
  render({ preserveGraph: state.view === "result", preserveScroll: true });
}

function handleSubmit(event: SubmitEvent): void {
  if (event.target instanceof HTMLFormElement && event.target.id === "new-analysis-form") {
    event.preventDefault();
    void startAnalysis();
    return;
  }
  const form = closestElement(event.target, "[data-rename-run-id]");
  if (!(form instanceof HTMLFormElement)) return;
  event.preventDefault();
  void saveRunName(form.dataset.renameRunId ?? "");
}

function positionRunActions(menu: HTMLElement, control: HTMLElement): void {
  const triggerRect = control.getBoundingClientRect();
  const menuRect = menu.getBoundingClientRect();
  const viewportPadding = 8;
  const gap = 6;
  const left = Math.min(
    window.innerWidth - menuRect.width - viewportPadding,
    Math.max(viewportPadding, triggerRect.right - menuRect.width),
  );
  const below = triggerRect.bottom + gap;
  const top =
    below + menuRect.height <= window.innerHeight - viewportPadding
      ? below
      : Math.max(viewportPadding, triggerRect.top - menuRect.height - gap);
  menu.style.left = `${left}px`;
  menu.style.top = `${top}px`;
}

function handlePopoverToggle(event: Event): void {
  const menu = event.target;
  if (!(menu instanceof HTMLElement) || !menu.matches("[data-run-actions-menu]")) return;
  const trigger = document.querySelector<HTMLElement>(`[data-menu-id="${CSS.escape(menu.id)}"]`);
  const toggle = event as ToggleEvent;
  const open = toggle.newState === "open";
  trigger?.setAttribute("aria-expanded", String(open));
  if (!open || trigger === null) return;
  positionRunActions(menu, trigger);
  menu.querySelector<HTMLButtonElement>('[role="menuitem"]')?.focus({ preventScroll: true });
}

function handleKeyDown(event: KeyboardEvent): void {
  if (event.key === "Escape" && importDialog.open) {
    event.preventDefault();
    closeImportDialog();
    return;
  }
  const workspaceTab = closestElement(event.target, '[role="tab"][data-workspace-tab]');
  if (workspaceTab !== null) {
    const tabs = Array.from(
      workspaceTab.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]') ?? [],
    );
    const currentIndex = tabs.indexOf(workspaceTab as HTMLButtonElement);
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % tabs.length;
    if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex !== null && tabs.length > 0) {
      event.preventDefault();
      tabs[nextIndex]?.click();
      tabs[nextIndex]?.focus({ preventScroll: true });
      return;
    }
  }
  const menu = document.querySelector<HTMLElement>("[data-run-actions-menu]:popover-open");
  if (menu === null) {
    if (
      event.key === "Escape" &&
      !helpDialog.open &&
      !confirmationDialog.open &&
      state.view === "analyses" &&
      state.selectedAnalysisIds.length > 0
    ) {
      event.preventDefault();
      clearAnalysisSelectionAndRestoreFocus();
    }
    return;
  }
  const trigger = document.querySelector<HTMLElement>(`[data-menu-id="${CSS.escape(menu.id)}"]`);
  if (event.key === "Escape") {
    event.preventDefault();
    menu.hidePopover();
    trigger?.focus();
    return;
  }
  if (!menu.contains(event.target as Node)) return;
  const items = Array.from(menu.querySelectorAll<HTMLButtonElement>('[role="menuitem"]'));
  if (items.length === 0) return;
  const currentIndex = items.indexOf(document.activeElement as HTMLButtonElement);
  let nextIndex: number | null = null;
  if (event.key === "ArrowDown") nextIndex = (currentIndex + 1) % items.length;
  if (event.key === "ArrowUp") nextIndex = (currentIndex - 1 + items.length) % items.length;
  if (event.key === "Home") nextIndex = 0;
  if (event.key === "End") nextIndex = items.length - 1;
  if (nextIndex === null) return;
  event.preventDefault();
  items[nextIndex]?.focus();
}

function handleDragOver(event: DragEvent): void {
  const dropZone = closestElement(event.target, "[data-drop-target]");
  if (dropZone === null || !event.dataTransfer?.types.includes("Files")) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "copy";
  dropZone.classList.add("drag-active");
}

function handleDragLeave(event: DragEvent): void {
  const dropZone = closestElement(event.target, "[data-drop-target]");
  if (dropZone === null || dropZone.contains(event.relatedTarget as Node | null)) return;
  dropZone.classList.remove("drag-active");
}

function handleDrop(event: DragEvent): void {
  const dropZone = closestElement(event.target, "[data-drop-target]");
  if (dropZone === null || event.dataTransfer === null) return;
  event.preventDefault();
  dropZone.classList.remove("drag-active");
  const target = dropZone.dataset.dropTarget;
  void filesFromDataTransfer(event.dataTransfer)
    .then((files) => {
      if (target === "requirements") {
        const sourceKind = files.some((file) => sourceName(file).includes("/"))
          ? "directory"
          : "files";
        return loadRequirementFiles(files, sourceKind);
      }
      if (target === "state-models") return loadStateModelFiles(files);
      if (target === "analysis-import") return importAnalysisFiles(files);
    })
    .catch((error: unknown) => {
      if (target === "requirements") {
        setFeedback("requirements", "error", errorMessage(error));
      } else if (target === "state-models") {
        setFeedback("state-models", "error", errorMessage(error));
      } else {
        setImportFeedback("error", errorMessage(error));
      }
    });
}

function handleBeforeUnload(event: BeforeUnloadEvent): void {
  const hasUnexportedDraft =
    ["new-analysis", "requirements", "state-models"].includes(state.view) &&
    (state.requirements !== null || state.stateModels !== null);
  if (!hasUnexportedDraft) return;
  event.preventDefault();
  event.returnValue = "";
}

async function loadRequirementFiles(
  files: File[],
  sourceKind: "files" | "directory",
): Promise<void> {
  const selected = selectSupportedSourceFiles(files, supportedFormats(state.requirementAdapters));
  if (selected.length === 0) {
    setFeedback("requirements", "error", "No supported requirement files were selected.");
    return;
  }
  try {
    validateSourceFiles(selected);
    const addedSources = await Promise.all(selected.map(readSourceFile));
    const currentSources = state.requirements?.sources ?? [];
    const combinedSourceKind =
      currentSources.length === 0 || state.requirements?.sourceKind === sourceKind
        ? sourceKind
        : "files";
    await parseRequirementSources(
      mergeRawSources(currentSources, addedSources),
      combinedSourceKind,
    );
  } catch (error) {
    setFeedback("requirements", "error", errorMessage(error));
  }
}

async function loadStateModelFiles(files: File[]): Promise<void> {
  const selected = selectSupportedSourceFiles(files, supportedFormats(state.stateModelAdapters));
  if (selected.length === 0) {
    setFeedback("state-models", "error", "No supported state-model files were selected.");
    return;
  }
  try {
    validateSourceFiles(selected);
    const addedSources = await Promise.all(selected.map(readSourceFile));
    await parseStateModelSources(mergeRawSources(state.stateModels?.sources ?? [], addedSources));
  } catch (error) {
    setFeedback("state-models", "error", errorMessage(error));
  }
}

async function parseRequirementSources(
  sources: RawSource[],
  sourceKind: "files" | "directory",
): Promise<void> {
  setFeedback("requirements", "running", "Reading requirements…");
  const bundle = await parseRequirements({
    sources,
    name: sourceCollectionName(sources, sourceKind),
    sourceKind,
    adapterId: "",
  });
  if (bundle.requirements.length === 0) throw new Error("No requirements were found.");
  state.requirements = bundle;
  state.selectedRequirementId = bundle.requirements[0]?.id ?? "";
  setFeedback(
    "requirements",
    "ready",
    `${bundle.requirements.length.toLocaleString()} ${bundle.requirements.length === 1 ? "requirement" : "requirements"} loaded.`,
  );
}

async function parseStateModelSources(sources: RawSource[]): Promise<void> {
  setFeedback("state-models", "running", "Reading state models…");
  const bundle = await parseStateModels({
    sources,
    name: sourceCollectionName(sources, "files"),
    adapterId: "",
  });
  state.stateModels = bundle;
  state.selectedStateModelId = bundle.models[0]?.id ?? "";
  const states = bundle.models.reduce((sum, model) => sum + model.counts.state, 0);
  setFeedback(
    "state-models",
    "ready",
    `${bundle.models.length.toLocaleString()} ${bundle.models.length === 1 ? "state model" : "state models"} with ${states.toLocaleString()} ${states === 1 ? "state" : "states"} loaded.`,
  );
}

async function removeRequirementSource(sourceId: string): Promise<void> {
  const bundle = state.requirements;
  if (bundle === null) return;
  const sources = bundle.sources.filter((source) => source.id !== sourceId);
  if (sources.length === 0) {
    state.requirements = null;
    state.requirementsFeedback = null;
    state.selectedRequirementId = "";
    state.requirementQuery = "";
    render();
    return;
  }
  try {
    await parseRequirementSources(sources, bundle.sourceKind);
  } catch (error) {
    setFeedback("requirements", "error", errorMessage(error));
  }
}

async function removeStateModelSource(sourceId: string): Promise<void> {
  const bundle = state.stateModels;
  if (bundle === null) return;
  const sources = bundle.sources.filter((source) => source.id !== sourceId);
  if (sources.length === 0) {
    state.stateModels = null;
    state.stateModelsFeedback = null;
    state.selectedStateModelId = "";
    render();
    return;
  }
  try {
    await parseStateModelSources(sources);
  } catch (error) {
    setFeedback("state-models", "error", errorMessage(error));
  }
}

async function startAnalysis(): Promise<void> {
  if (state.requirements === null || state.stateModels === null) {
    state.analysisFeedback = { state: "error", text: "Add requirements and state models first." };
    render();
    return;
  }
  const requirements = state.requirements;
  const stateModels = state.stateModels;
  const method = state.methods.find((item) => item.id === state.selectedMethodId);
  if (method === undefined) {
    state.analysisFeedback = { state: "error", text: "Select a traceability method." };
    render();
    return;
  }
  const run: AnalysisRun = {
    id: crypto.randomUUID(),
    title:
      state.analysisName.trim() ||
      suggestedAnalysisName({
        requirementCount: requirements.requirements.length,
        stateModelCount: stateModels.models.length,
      }),
    status: "running",
    methodId: method.id,
    methodName: method.name,
    createdAt: new Date().toISOString(),
    progress: 0,
    message: "Preparing the analysis…",
    result: null,
    requirements,
    stateModels,
  };
  state.analysisFeedback = null;
  state.runs = [run, ...state.runs];
  state.selectedRequirementId = requirements.requirements[0]?.id ?? "";
  state.selectedResultScopeKind = "requirement";
  state.selectedResultScopeId = state.selectedRequirementId;
  state.selectedElementId = "";
  state.resultWorkspaceTab = "graph";
  state.selectedStateModelId = stateModels.models[0]?.id ?? "";
  state.analysisSort = "created-desc";
  state.analysisPage = 1;
  persistRunIndex();
  const abort = new AbortController();
  activeAnalysisAborts.set(run.id, abort);
  navigateToRoute({ view: "result", runId: run.id });
  try {
    run.result = await analyze({
      resultId: run.id,
      method,
      requirements,
      stateModels,
      signal: abort.signal,
      onProgress: (progress) => updateRunProgress(run, progress),
    });
    run.result.title = run.title;
    run.status = "complete";
    run.progress = 1;
    run.message = "";
    const viewingCompletedRun = isViewingRun(run.id);
    if (viewingCompletedRun) {
      state.selectedRequirementId = requirementIds(run.result)[0] ?? "";
      state.selectedResultScopeKind = "requirement";
      state.selectedResultScopeId = state.selectedRequirementId;
      state.selectedElementId = "";
      state.resultWorkspaceTab = "graph";
      selectBestEvidenceModelForCurrentScope();
    }
    if (progressRenderFrame !== null) {
      window.cancelAnimationFrame(progressRenderFrame);
      progressRenderFrame = null;
    }
    persistRunIndex();
    let saved = true;
    try {
      await saveRunResult(run);
    } catch (error) {
      saved = false;
      state.analysisFeedback = {
        state: "error",
        text: `Analysis completed, but it could not be saved locally: ${errorMessage(error)}`,
      };
    }
    if (!isViewingRun(run.id) && saved) {
      state.analysisFeedback = backgroundRunFeedback(run);
    }
  } catch (error) {
    run.status = isAbortError(error) ? "cancelled" : "failed";
    run.message = isAbortError(error) ? "Analysis cancelled." : errorMessage(error);
    if (!isViewingRun(run.id)) state.analysisFeedback = backgroundRunFeedback(run);
  } finally {
    activeAnalysisAborts.delete(run.id);
    persistRunIndex();
    if (isViewingRun(run.id)) render();
    else renderPreservingViewport();
  }
}

function isViewingRun(runId: string): boolean {
  return state.view === "result" && state.selectedRunId === runId;
}

function cancelAnalysis(runId: string): void {
  activeAnalysisAborts.get(runId)?.abort();
}

async function importAnalysisFiles(files: File[]): Promise<void> {
  if (files.length !== 1) {
    setImportFeedback("error", "Choose one TESTAR Trace analysis file.");
    return;
  }
  const file = files[0];
  if (file !== undefined) await importResult(file);
}

async function importResult(file: File): Promise<void> {
  activeImportAbort?.abort();
  const controller = new AbortController();
  activeImportAbort = controller;
  setImportBusy(true);
  setImportFeedback("running", `Preparing ${file.name}…`);
  try {
    const imported = await importAnalysisInBackground(file, {
      signal: controller.signal,
      onProgress: (progress) => setImportFeedback("running", progress.message),
    });
    const runs: AnalysisRun[] = imported.map((bundle) => ({
      id: bundle.result.id,
      title: bundle.result.title,
      status: "complete",
      methodId: bundle.result.methodId,
      methodName: bundle.result.methodName,
      createdAt: bundle.result.createdAt,
      progress: 1,
      message: "",
      result: bundle.result,
      requirements: bundle.requirements,
      stateModels: bundle.stateModels,
    }));
    const primary = runs[0];
    const primaryBundle = imported[0];
    if (primary === undefined || primaryBundle === undefined) {
      throw new Error("The selected file does not contain any analyses.");
    }
    setImportFeedback(
      "running",
      imported.length === 1 ? "Saving imported analysis…" : "Saving imported analyses…",
    );
    await saveRunResults(runs, controller.signal);

    const existingRunIds = new Set(state.runs.map((run) => run.id));
    const updatedCount = runs.filter((run) => existingRunIds.has(run.id)).length;
    const importedIds = new Set(runs.map((run) => run.id));
    state.runs = [...runs, ...state.runs.filter((item) => !importedIds.has(item.id))];
    state.selectedRunId = primary.id;
    state.selectedRequirementId = requirementIds(primary.result!)[0] ?? "";
    state.selectedResultScopeKind = "requirement";
    state.selectedResultScopeId = state.selectedRequirementId;
    state.selectedElementId = "";
    state.resultWorkspaceTab = "graph";
    state.requirements = primaryBundle.requirements;
    state.stateModels = primaryBundle.stateModels;
    state.selectedStateModelId = primaryBundle.stateModels.models[0]?.id ?? "";
    state.selectedAnalysisIds = [];
    if (persistRunIndex()) {
      state.analysisFeedback = {
        state: "complete",
        text: analysisImportOutcomeMessage(runs.length, updatedCount),
        presentation: "toast",
      };
    }
    state.analysisSort = "created-desc";
    state.analysisPage = 1;
    importDialog.close();
    importDialogTrigger = null;
    navigateToRoute(
      runs.length === 1 ? { view: "result", runId: primary.id } : { view: "analyses" },
    );
  } catch (error) {
    setImportFeedback(
      isAbortError(error) ? "cancelled" : "error",
      isAbortError(error)
        ? "Import cancelled. No analyses were added or updated."
        : errorMessage(error),
    );
  } finally {
    if (activeImportAbort === controller) {
      activeImportAbort = null;
      setImportBusy(false);
    }
  }
}

function setImportFeedback(stateName?: "running" | "error" | "cancelled", text = ""): void {
  const feedback = document.querySelector<HTMLElement>("#import-feedback");
  if (feedback === null) return;
  feedback.className = `import-feedback${stateName === undefined ? "" : ` ${stateName}`}`;
  feedback.setAttribute("role", stateName === "error" ? "alert" : "status");
  feedback.setAttribute("aria-live", stateName === "error" ? "assertive" : "polite");
  feedback.replaceChildren();
  if (text === "") return;
  if (stateName !== undefined) {
    const statusIcon = document.createElement("span");
    statusIcon.className = "feedback-state-icon";
    statusIcon.ariaHidden = "true";
    statusIcon.innerHTML = icon(
      stateName === "error" ? "error" : stateName === "cancelled" ? "cancelled" : "loading",
      stateName === "running" ? "spinning" : "",
    );
    feedback.append(statusIcon);
  }
  feedback.append(document.createTextNode(text));
}

function setImportBusy(busy: boolean): void {
  importDialog.ariaBusy = String(busy);
  const chooseButton = document.querySelector<HTMLButtonElement>("#choose-import-file");
  if (chooseButton !== null) chooseButton.disabled = busy;
  const closeButton = importDialog.querySelector<HTMLButtonElement>(
    '[data-action="close-import-dialog"]',
  );
  if (closeButton !== null) closeButton.disabled = busy;
  const cancelButton = document.querySelector<HTMLButtonElement>("#cancel-import");
  if (cancelButton !== null) {
    cancelButton.disabled = !busy;
  }
  const transferActions = document.querySelector<HTMLElement>("#import-transfer-actions");
  if (transferActions !== null) transferActions.hidden = !busy;
  const progress = document.querySelector<HTMLElement>("#import-progress");
  if (progress !== null) progress.hidden = !busy;
  const dropzone = importDialog.querySelector<HTMLElement>("[data-drop-target='analysis-import']");
  if (dropzone !== null) dropzone.inert = busy;
}

function closeImportDialog(): void {
  if (importDialog.ariaBusy === "true") return;
  importDialog.close();
  importDialogTrigger?.focus();
  importDialogTrigger = null;
}

function exportRun(runId: string): void {
  const run = state.runs.find((item) => item.id === runId);
  if (run === undefined) return;
  void startExport([run], "single", analysisExportFileName(run.title));
}

function exportSelectedRuns(): void {
  const selected = state.runs.filter((run) => state.selectedAnalysisIds.includes(run.id));
  const date = new Date().toISOString().slice(0, 10);
  void startExport(selected, "bulk", `testar-trace-analyses-${date}.testar-analyses.json`);
}

async function startExport(
  runs: AnalysisRun[],
  kind: "single" | "bulk",
  fileName: string,
): Promise<void> {
  if (activeExportAbort !== null) return;
  const controller = new AbortController();
  activeExportAbort = controller;
  state.analysisFeedback = { state: "running", text: "Preparing export…" };
  renderPreservingViewport();
  try {
    const blob = await exportAnalysesInBackground(runs, kind, {
      signal: controller.signal,
      onProgress: (progress) => {
        state.analysisFeedback = { state: "running", text: progress.message };
        renderPreservingViewport();
      },
    });
    downloadBlob(blob, fileName);
    state.analysisFeedback = {
      state: "complete",
      text: `${runs.length === 1 ? "Analysis" : `${runs.length} analyses`} exported.`,
      presentation: "toast",
    };
  } catch (error) {
    state.analysisFeedback = {
      state: isAbortError(error) ? "cancelled" : "error",
      text: isAbortError(error) ? "Export cancelled." : errorMessage(error),
    };
  } finally {
    if (activeExportAbort === controller) activeExportAbort = null;
    renderPreservingViewport();
  }
}

function downloadBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url));
}

function updateRunProgress(run: AnalysisRun, progress: AnalysisProgress): void {
  if (run.status !== "running") return;
  run.progressDetail = progress;
  run.progress = progressRatio(progress);
  run.message = progress.message ?? progress.phase;
  if (progressRenderFrame !== null) return;
  progressRenderFrame = window.requestAnimationFrame(() => {
    progressRenderFrame = null;
    if (isViewingRun(run.id) || state.view === "analyses") renderPreservingViewport();
  });
}

function progressRatio(progress: AnalysisProgress): number {
  if (progress.phase === "analysis.completed") return 1;
  if (progress.phase.endsWith(".completed")) return 0.96;
  if (progress.completed !== null && progress.total !== null && progress.total > 0) {
    return Math.min(0.92, 0.08 + (progress.completed / progress.total) * 0.84);
  }
  return progress.phase === "analysis.started" ? 0.03 : 0.08;
}

function beginRenameRun(runId: string): void {
  const run = state.runs.find((item) => item.id === runId);
  if (run === undefined) return;
  state.renamingRunId = run.id;
  state.renameDraft = run.title;
  render();
  const input = document.querySelector<HTMLInputElement>("#rename-run-input");
  input?.focus();
  input?.select();
}

function cancelRenameRun(): void {
  state.renamingRunId = "";
  state.renameDraft = "";
  render();
}

async function saveRunName(runId: string): Promise<void> {
  const run = state.runs.find((item) => item.id === runId);
  const title = state.renameDraft.trim();
  if (run === undefined || title === "") return;
  run.title = title;
  if (run.result !== null) {
    run.result.title = title;
    try {
      await saveRunResult(run);
    } catch (error) {
      state.analysisFeedback = { state: "error", text: errorMessage(error) };
    }
  }
  state.renamingRunId = "";
  state.renameDraft = "";
  persistRunIndex();
  render();
}

async function duplicateRun(runId: string): Promise<void> {
  const source = state.runs.find((item) => item.id === runId);
  if (source?.result === null || source?.result === undefined) return;
  const duplicatingOpenRun = state.view === "result" && state.selectedRunId === source.id;
  const id = crypto.randomUUID();
  const createdAt = new Date().toISOString();
  const title = nextDuplicateTitle(
    source.title,
    state.runs.map((run) => run.title),
  );
  const result = structuredClone(source.result);
  result.id = id;
  result.title = title;
  result.createdAt = createdAt;
  const duplicate: AnalysisRun = {
    ...source,
    id,
    title,
    createdAt,
    message: "",
    result,
  };
  try {
    await saveRunResult(duplicate);
    state.runs = [duplicate, ...state.runs];
    state.selectedRunId = duplicate.id;
    state.analysisSort = "created-desc";
    state.analysisPage = 1;
    persistRunIndex();
    if (duplicatingOpenRun) {
      navigateToRoute({ view: "result", runId: duplicate.id });
      return;
    }
  } catch (error) {
    state.analysisFeedback = {
      state: "error",
      text: errorMessage(
        error,
        "File support could not be prepared. Reload the page and try again.",
      ),
    };
  }
  render();
}

async function deleteRun(runId: string): Promise<void> {
  const run = state.runs.find((item) => item.id === runId) ?? null;
  if (run === null) return;
  const confirmed = await requestConfirmation(
    "Delete analysis?",
    `“${run.title}” and its saved results will be permanently deleted.`,
    "Delete analysis",
  );
  if (!confirmed) return;
  const deletingOpenRun = state.view === "result" && state.selectedRunId === run.id;
  activeAnalysisAborts.get(run.id)?.abort();
  state.runs = state.runs.filter((item) => item.id !== run.id);
  state.selectedAnalysisIds = state.selectedAnalysisIds.filter((id) => id !== run.id);
  state.selectedRunId = state.runs[0]?.id ?? "";
  if (state.renamingRunId === run.id) {
    state.renamingRunId = "";
    state.renameDraft = "";
  }
  state.analysisPage = 1;
  void deleteRunResult(run.id).catch((error: unknown) => {
    state.analysisFeedback = { state: "error", text: errorMessage(error) };
    render();
  });
  persistRunIndex();
  if (deletingOpenRun) navigateToRoute({ view: "analyses" }, true);
  else render();
}

async function deleteSelectedRuns(): Promise<void> {
  const selected = state.runs.filter((run) => state.selectedAnalysisIds.includes(run.id));
  if (selected.length === 0) return;
  const multiple = selected.length > 1;
  const confirmed = await requestConfirmation(
    multiple ? `Delete ${selected.length} selected analyses?` : "Delete selected analysis?",
    multiple
      ? "The selected analyses and their saved results will be permanently deleted."
      : "The selected analysis and its saved result will be permanently deleted.",
    `Delete ${multiple ? "analyses" : "analysis"}`,
  );
  if (!confirmed) return;
  const ids = new Set(selected.map((run) => run.id));
  for (const run of selected) activeAnalysisAborts.get(run.id)?.abort();
  state.runs = state.runs.filter((run) => !ids.has(run.id));
  state.selectedAnalysisIds = [];
  state.selectedRunId = state.runs[0]?.id ?? "";
  state.analysisPage = 1;
  persistRunIndex();
  try {
    await Promise.all(selected.map((run) => deleteRunResult(run.id)));
  } catch (error) {
    state.analysisFeedback = { state: "error", text: errorMessage(error) };
  }
  render();
}

function requestConfirmation(
  title: string,
  message: string,
  confirmLabel: string,
): Promise<boolean> {
  if (confirmationDialog.open) return Promise.resolve(false);
  confirmationDialogTitle.textContent = title;
  confirmationDialogMessage.textContent = message;
  confirmationConfirmButton.textContent = confirmLabel;
  confirmationDialog.returnValue = "cancel";
  confirmationDialog.showModal();
  confirmationCancelButton.focus();
  return new Promise((resolve) => {
    confirmationResolve = resolve;
  });
}

function beginNewAnalysis(): void {
  state.requirements = null;
  state.stateModels = null;
  state.requirementsFeedback = null;
  state.stateModelsFeedback = null;
  state.analysisFeedback = null;
  state.analysisName = "";
  state.selectedRequirementId = "";
  state.selectedResultScopeKind = "requirement";
  state.selectedResultScopeId = "";
  state.selectedElementId = "";
  state.selectedStateModelId = "";
  state.resultWorkspaceTab = "graph";
  state.resultRequirementQuery = "";
  state.resultRequirementFilter = "all";
  state.requirementQuery = "";
  state.selectedAnalysisIds = [];
  navigateToRoute({ view: "new-analysis" });
}

function setAnalysisSelection(ids: string[], selected: boolean): void {
  const next = new Set(state.selectedAnalysisIds);
  for (const id of ids) {
    if (selected) next.add(id);
    else next.delete(id);
  }
  const validIds = new Set(state.runs.map((run) => run.id));
  state.selectedAnalysisIds = [...next].filter((id) => validIds.has(id));
}

function clearAnalysisSelectionAndRestoreFocus(): void {
  const visibleCheckboxes = Array.from(
    document.querySelectorAll<HTMLInputElement>("[data-analysis-select]"),
  );
  const focusId =
    state.selectedAnalysisIds.find((id) =>
      visibleCheckboxes.some((checkbox) => checkbox.dataset.analysisSelect === id),
    ) ?? visibleCheckboxes[0]?.dataset.analysisSelect;
  state.selectedAnalysisIds = [];
  renderPreservingViewport();
  const focusTarget =
    focusId === undefined
      ? document.querySelector<HTMLInputElement>("#analysis-search")
      : document.querySelector<HTMLInputElement>(`[data-analysis-select="${CSS.escape(focusId)}"]`);
  focusTarget?.focus({ preventScroll: true });
  announceSelection("Analysis selection cleared.");
}

function announceAnalysisSelection(): void {
  const count = state.selectedAnalysisIds.length;
  announceSelection(`${count} ${count === 1 ? "analysis" : "analyses"} selected.`);
}

function announceAnalysisResults(): void {
  const count = getAnalysisPage(state.runs, analysisListOptions()).totalItems;
  announceSelection(`${count} matching ${count === 1 ? "analysis" : "analyses"}.`);
}

function ensureSelectedResultRequirement(): void {
  const run = selectedRun(state);
  if (run?.result === null || run?.result === undefined) return;
  const ids = [...new Set(requirementIds(run.result))];
  const visibleIds = filterResultRequirementIds({
    ids,
    requirements: state.requirements?.requirements ?? [],
    assessments: run.result.assessments,
    query: state.resultRequirementQuery,
    filter: state.resultRequirementFilter,
  });
  if (visibleIds.includes(state.selectedRequirementId)) return;
  const previousRequirementId = state.selectedRequirementId;
  state.selectedRequirementId = visibleIds[0] ?? "";
  state.selectedResultScopeKind = "requirement";
  state.selectedResultScopeId = state.selectedRequirementId;
  state.selectedElementId = "";
  state.resultWorkspaceTab = "graph";
  selectBestEvidenceModelForCurrentScope();
  if (previousRequirementId !== state.selectedRequirementId && state.selectedRequirementId !== "") {
    announceSelection(`Showing the first matching requirement: ${state.selectedRequirementId}.`);
  }
}

function ensureSelectedStandaloneRequirement(): void {
  const requirements = state.requirements?.requirements ?? [];
  const query = state.requirementQuery.trim().toLocaleLowerCase();
  const visibleIds = requirements
    .filter(
      (item) =>
        query === "" ||
        [item.id, item.title, item.summary, item.actor].some((value) =>
          value.toLocaleLowerCase().includes(query),
        ),
    )
    .map((item) => item.id);
  if (visibleIds.includes(state.selectedRequirementId)) return;
  state.selectedRequirementId = visibleIds[0] ?? "";
  if (state.selectedRequirementId !== "") {
    announceSelection(`Showing the first matching requirement: ${state.selectedRequirementId}.`);
  }
}

function selectBestEvidenceModelForCurrentScope(): void {
  const run = selectedRun(state);
  const result = run?.result;
  const modelIds = state.stateModels?.models.map((model) => model.id) ?? [];
  if (result === null || result === undefined || modelIds.length === 0) return;
  const requirement = state.requirements?.requirements.find(
    (item) => item.id === state.selectedRequirementId,
  );
  const scope = resolveResultScope(
    result,
    state.selectedRequirementId,
    state.selectedResultScopeId,
    state.selectedElementId,
    state.selectedResultScopeKind,
    requirement,
  );
  const previousModelId = state.selectedStateModelId;
  state.selectedStateModelId = bestEvidenceStateModelId(result, scope, modelIds);
  if (
    state.view === "result" &&
    modelIds.length > 1 &&
    previousModelId !== "" &&
    previousModelId !== state.selectedStateModelId
  ) {
    const selectedName =
      state.stateModels?.models.find((model) => model.id === state.selectedStateModelId)
        ?.sourceName ?? "state model";
    announceSelection(`Best matching state model selected: ${selectedName}.`);
  }
}

function announceSelection(message: string): void {
  const announcer = document.querySelector<HTMLElement>("#selection-announcer");
  if (announcer === null) return;
  announcer.textContent = "";
  window.requestAnimationFrame(() => {
    announcer.textContent = message;
  });
}

function restoreRequirementSelectionFocus(): void {
  const selectedId = state.selectedRequirementId;
  const selectedControl = Array.from(
    document.querySelectorAll<HTMLButtonElement>('[data-action="select-requirement"]'),
  ).find((control) => control.dataset.requirementId === selectedId);
  selectedControl?.focus({ preventScroll: true });
}

function resetAnalysisFilters(): void {
  state.analysisQuery = "";
  state.analysisStatusFilter = "all";
  state.analysisMethodFilter = "all";
  state.analysisPage = 1;
  render();
  announceAnalysisResults();
}

function analysisListOptions() {
  return {
    query: state.analysisQuery,
    status: state.analysisStatusFilter,
    methodId: state.analysisMethodFilter,
    sort: state.analysisSort,
    page: state.analysisPage,
    pageSize: state.analysisPageSize,
  };
}

async function loadCatalog(): Promise<void> {
  try {
    const catalog = await fetchCatalog();
    state.requirementAdapters = catalog.requirement_adapters;
    state.stateModelAdapters = catalog.state_model_adapters;
    state.methods = catalog.methods.filter((method) => method.id !== "noop");
    if (!state.methods.some((item) => item.id === state.selectedMethodId)) {
      state.selectedMethodId =
        state.methods.find((method) => method.id === "graph-alignment")?.id ??
        state.methods[0]?.id ??
        "";
    }
    setAcceptedFormats(requirementsFileInput, catalog.requirement_adapters);
    setAcceptedFormats(requirementsDirectoryInput, catalog.requirement_adapters);
    setAcceptedFormats(stateModelFileInput, catalog.state_model_adapters);
    setAcceptedFormats(stateModelDirectoryInput, catalog.state_model_adapters);
    state.catalogLoadState = "ready";
  } catch (error) {
    state.catalogLoadState = "error";
    state.analysisFeedback = { state: "error", text: errorMessage(error) };
  }
  render();
}

function ensureCatalogLoaded(): void {
  if (state.catalogLoadState === "ready" || catalogLoadPromise !== null) return;
  catalogLoadPromise = loadCatalog().finally(() => {
    catalogLoadPromise = null;
  });
}

async function hydrateStoredRunResults(): Promise<void> {
  try {
    state.runs = await hydrateRunResults(state.runs);
    state.resultsLoadState = "ready";
    if (state.view === "result") restoreRunContext(selectedRun(state));
  } catch (error) {
    state.resultsLoadState = "error";
    state.analysisFeedback = { state: "error", text: errorMessage(error) };
  }
  render();
}

function restoreRunContext(run: AnalysisRun | null): void {
  state.requirements = run?.requirements ?? null;
  state.stateModels = run?.stateModels ?? null;
  const modelIds = state.stateModels?.models.map((model) => model.id) ?? [];
  if (!modelIds.includes(state.selectedStateModelId)) {
    state.selectedStateModelId = modelIds[0] ?? "";
  }
  if (run?.result !== null && run?.result !== undefined) {
    const ids = requirementIds(run.result);
    if (!ids.includes(state.selectedRequirementId)) {
      state.selectedRequirementId = ids[0] ?? "";
      state.selectedResultScopeKind = "requirement";
      state.selectedResultScopeId = state.selectedRequirementId;
      state.selectedElementId = "";
      state.resultWorkspaceTab = "graph";
    }
  }
}

function setFeedback(
  target: "requirements" | "state-models",
  loadState: typeof state.loadState,
  text: string,
): void {
  const feedback = { state: loadState, text };
  if (target === "requirements") state.requirementsFeedback = feedback;
  else state.stateModelsFeedback = feedback;
  state.loadState = loadState;
  render();
}

function persistRunIndex(): boolean {
  try {
    persistRuns(state.runs);
    return true;
  } catch (error) {
    state.analysisFeedback = {
      state: "error",
      text: `Analyses could not be saved in this browser. Export important results before closing this tab. ${errorMessage(error)}`,
      presentation: "toast",
    };
    return false;
  }
}

function supportedFormats(adapters: { formats: string[] }[]): Set<string> {
  return new Set(adapters.flatMap((adapter) => adapter.formats));
}

function setAcceptedFormats(input: HTMLInputElement, adapters: { formats: string[] }[]): void {
  input.accept = [...supportedFormats(adapters)].map((format) => `.${format}`).join(",");
}

function sourceCollectionName(sources: RawSource[], sourceKind: "files" | "directory"): string {
  const first = sources[0];
  if (sources.length === 1 && first !== undefined) return first.name;
  if (sourceKind === "directory" && first !== undefined) {
    return first.name.replaceAll("\\", "/").split("/")[0] || "Source folder";
  }
  return `${sources.length} source ${sources.length === 1 ? "file" : "files"}`;
}

function requirementIds(result: NonNullable<AnalysisRun["result"]>): string[] {
  return result.assessments
    .filter(
      (item) => item.scopeKind === "requirement" && item.viewKind === "state-model-collection",
    )
    .flatMap((item) => item.requirementIds);
}

function showView(viewName: ViewName): void {
  if (viewName === "result") {
    if (state.selectedRunId !== "") {
      navigateToRoute({ view: "result", runId: state.selectedRunId });
    }
    return;
  }
  navigateToRoute({ view: viewName });
}

function applyRouteFromLocation(): void {
  const route = parseRoute(window.location.pathname);
  if (route === null) {
    navigateToRoute({ view: "analyses" }, true);
    return;
  }
  applyRoute(route);
}

function navigateToRoute(route: AppRoute, replace = false): void {
  const path = route.view === "result" ? routePath("result", route.runId) : routePath(route.view);
  if (replace) window.history.replaceState(null, "", path);
  else if (window.location.pathname !== path) window.history.pushState(null, "", path);
  applyRoute(route);
}

function applyRoute(route: AppRoute): void {
  if (route.view === "requirements" && state.requirements === null) {
    navigateToRoute({ view: "new-analysis" }, true);
    return;
  }
  if (route.view === "state-models" && state.stateModels === null) {
    navigateToRoute({ view: "new-analysis" }, true);
    return;
  }
  if (route.view === "result") {
    const run = state.runs.find((item) => item.id === route.runId);
    if (run === undefined) {
      navigateToRoute({ view: "analyses" }, true);
      return;
    }
    const changedRun = state.selectedRunId !== run.id;
    state.selectedRunId = run.id;
    restoreRunContext(run);
    if (changedRun) {
      state.resultRequirementQuery = "";
      state.resultRequirementFilter = "all";
      const ids =
        run.result === null
          ? (run.requirements?.requirements.map((item) => item.id) ?? [])
          : requirementIds(run.result);
      state.selectedRequirementId = ids[0] ?? "";
      state.selectedResultScopeKind = "requirement";
      state.selectedResultScopeId = state.selectedRequirementId;
      state.selectedElementId = "";
      state.resultWorkspaceTab = "graph";
      selectBestEvidenceModelForCurrentScope();
    }
  }
  state.view = route.view;
  if (["new-analysis", "requirements", "state-models"].includes(route.view)) {
    ensureCatalogLoaded();
  }
  render();
  window.scrollTo(0, 0);
  const heading = view.querySelector<HTMLElement>("h1");
  if (heading !== null) {
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
  }
}

function closestElement(target: EventTarget | null, selector: string): HTMLElement | null {
  return target instanceof Element ? target.closest<HTMLElement>(selector) : null;
}

function isViewName(value: string): value is ViewName {
  return ["analyses", "new-analysis", "requirements", "state-models", "result"].includes(value);
}

function isAnalysisStatusFilter(value: string): value is AnalysisStatusFilter {
  return ["all", "running", "complete", "cancelled", "failed"].includes(value);
}

function isAnalysisSort(value: string): value is AnalysisSort {
  return ["created-desc", "created-asc", "name-asc", "completeness-desc"].includes(value);
}

function isResultRequirementFilter(value: string): value is ResultRequirementFilter {
  return ["all", "complete", "incomplete", "not-assessable"].includes(value);
}

function isSelectableResultScopeKind(
  value: string | undefined,
): value is SelectableResultScopeKind {
  return value !== undefined && ["requirement", "flow", "branch", "path"].includes(value);
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function errorMessage(error: unknown, fallback?: string): string {
  return userFacingErrorMessage(error, fallback);
}
