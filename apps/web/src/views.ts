import {
  getAnalysisPage,
  overallCompleteness,
  secondaryAnalysisActions,
  type AnalysisRowAction,
} from "./analysis-list.ts";
import { suggestedAnalysisName } from "./analysis-names.ts";
import { icon, type AppIcon } from "./icons.ts";
import { PATH_TONE_COUNT, pathToneVariables } from "./path-colors.ts";
import { routePath } from "./routes.ts";
import { stateNodeDisplayName } from "./state-model-labels.ts";
import {
  assessmentForScope,
  filterResultRequirementIds,
  occurrencesForScope,
  pathAccentIndex,
  pathBranchKind,
  pathPriorityIndex,
  pathsForRequirement,
  requirementElementTone,
  resolveResultScope,
} from "./result-scope.ts";
import type { AppState } from "./state.ts";
import type {
  AdapterDescriptor,
  AnalysisProgress,
  AnalysisResult,
  AnalysisRun,
  CoverageAssessment,
  JsonValue,
  RequirementBranch,
  RequirementItem,
  RequirementPath,
  RawSource,
  StateModel,
  TraceOccurrence,
} from "./types.ts";
import { LOCAL_PROCESSING_MESSAGE } from "./ui-copy.ts";

export function renderAnalysesOverview(state: AppState): string {
  const page = getAnalysisPage(state.runs, {
    query: state.analysisQuery,
    status: state.analysisStatusFilter,
    methodId: state.analysisMethodFilter,
    sort: state.analysisSort,
    page: state.analysisPage,
    pageSize: state.analysisPageSize,
  });
  const selectedRuns = state.runs.filter((run) => state.selectedAnalysisIds.includes(run.id));
  return `
    <section class="page analyses-page" aria-labelledby="analyses-title">
      <header class="page-header">
        <div><h1 id="analyses-title">Analyses</h1><p>Create, import, review, and export requirements traceability analyses.</p></div>
      </header>
      <div class="page-content analyses-content">
        ${renderFeedback(state.analysisFeedback, "dismiss-analysis-feedback")}
        ${
          state.runs.length === 0
            ? renderAnalysesEmptyState()
            : `
          <div class="analysis-toolbar-slot">
          ${
            selectedRuns.length > 0
              ? renderAnalysisBatchToolbar(selectedRuns, page.totalItems)
              : `<search class="analysis-toolbar" aria-label="Search and filter analyses">
            <label class="search-field ${state.analysisQuery.trim() === "" ? "" : "active-filter"}"><span class="visually-hidden">Search by analysis name</span>${icon("search")}<input id="analysis-search" type="search" placeholder="Search by analysis name…" value="${escapeHtml(state.analysisQuery)}"></label>
            <label><span>Status</span><span class="select-control ${state.analysisStatusFilter === "all" ? "" : "active-filter"}"><select id="analysis-status-filter">${statusFilterOptions(state.analysisStatusFilter)}</select>${icon("expand", "select-chevron")}</span></label>
            <label><span>Method</span><span class="select-control ${state.analysisMethodFilter === "all" ? "" : "active-filter"}"><select id="analysis-method-filter">${methodFilterOptions(state)}</select>${icon("expand", "select-chevron")}</span></label>
            <label><span>Sort by</span><span class="select-control"><select id="analysis-sort">${sortOptions(state.analysisSort)}</select>${icon("expand", "select-chevron")}</span></label>
          </search>`
          }
          </div>
          <div class="analysis-results-region">
            ${page.totalItems === 0 ? renderFilteredEmptyState() : renderAnalysisTable(page.items, state)}
            ${renderAnalysisPagination(page)}
          </div>
        `
        }
      </div>
    </section>`;
}

export function renderNewAnalysis(state: AppState): string {
  const suggestedName = suggestedAnalysisName({
    requirementCount: state.requirements?.requirements.length,
    stateModelCount: state.stateModels?.models.length,
  });
  const hasRequirements = state.requirements !== null;
  const hasStateModels = state.stateModels !== null;
  const analysisNameHelp =
    hasRequirements && hasStateModels
      ? `Leave blank to use <strong>${escapeHtml(suggestedName)}</strong>.`
      : hasRequirements || hasStateModels
        ? "Add the remaining source to generate the analysis name."
        : "A name will be generated after you add sources.";
  const methodsLoading = state.catalogLoadState === "loading";
  const methodOptions = methodsLoading
    ? `<option>Loading methods…</option>`
    : state.methods.length === 0
      ? `<option>No methods available</option>`
      : state.methods
          .map(
            (method) =>
              `<option value="${escapeHtml(method.id)}" ${method.id === state.selectedMethodId ? "selected" : ""}>${escapeHtml(method.name)}${method.id === "graph-alignment" ? " (recommended)" : ""}</option>`,
          )
          .join("");
  const selectedMethod = state.methods.find((method) => method.id === state.selectedMethodId);
  return `
    <section class="page new-analysis-page" aria-labelledby="page-title">
      <header class="page-header detail-header">
        ${backLink("analyses", "Back to analyses")}
        <div class="detail-heading"><h1 id="page-title">New analysis</h1><p>Name the analysis, select a method, and add requirements and state models.</p></div>
      </header>
      <form id="new-analysis-form" class="page-content new-analysis-content">
        <div class="analysis-basics">
          <div class="form-field analysis-name-field"><div class="field-label-row"><label for="analysis-name">Analysis name</label><span class="field-meta">Optional</span></div><input id="analysis-name" type="text" maxlength="120" autocomplete="off" placeholder="${escapeHtml(suggestedName)}" value="${escapeHtml(state.analysisName)}" aria-describedby="analysis-name-help"><small id="analysis-name-help">${analysisNameHelp}</small></div>
          <div class="form-field"><label for="method-select">Traceability method</label><span class="select-control"><select id="method-select" aria-describedby="method-select-help" ${methodsLoading || state.methods.length === 0 ? "disabled" : ""}>${methodOptions}</select>${icon("expand", "select-chevron")}</span><small id="method-select-help">${escapeHtml(methodDescription(selectedMethod?.id ?? ""))}</small></div>
        </div>
        <div class="source-grid">
          ${renderRequirementSource(state)}
          ${renderStateModelSource(state)}
        </div>
        ${renderAnalysisLauncher(state)}
      </form>
    </section>`;
}

export function renderRequirementsDetail(state: AppState): string {
  const bundle = state.requirements;
  if (bundle === null) return emptyDetail("Requirements", "No requirements loaded.");
  const query = state.requirementQuery.trim().toLocaleLowerCase();
  const visibleRequirements =
    query === ""
      ? bundle.requirements
      : bundle.requirements.filter((item) =>
          [item.id, item.title, item.summary, item.actor].some((value) =>
            value.toLocaleLowerCase().includes(query),
          ),
        );
  const selected =
    visibleRequirements.find((item) => item.id === state.selectedRequirementId) ??
    visibleRequirements[0] ??
    null;
  return `
    <section class="page source-review-page" aria-labelledby="page-title">
      ${reviewHeader("Review requirements", "Inspect the parsed requirements, flows, and traceable elements before running the analysis.", bundle.name)}
      <div class="page-content review-page-content">
      <div class="content-panel review-layout requirements-review">
      <aside class="review-navigation" aria-labelledby="review-requirements-title"><div class="review-navigation-scroll" data-scroll-key="requirements-list">
        <div class="panel-header review-panel-header"><h2 id="review-requirements-title">Parsed requirements</h2><small>${countLabel(bundle.requirements.length, "requirement")}</small></div>
        <div class="metric-strip">
          ${metric(
            "Flows",
            bundle.requirements.reduce((sum, item) => sum + item.flows.length, 0),
          )}
          ${metric(
            "Traceable elements",
            bundle.requirements.reduce((sum, item) => sum + item.elements.length, 0),
          )}
        </div>
        ${bundle.requirements.length <= 1 ? "" : `<search class="requirements-toolbar" aria-label="Search requirements"><label class="search-field ${query === "" ? "" : "active-filter"}"><span class="visually-hidden">Search requirements</span>${icon("search")}<input id="requirement-search" type="search" placeholder="Search requirements…" value="${escapeHtml(state.requirementQuery)}"></label>${query === "" ? "" : `<small aria-live="polite">${visibleRequirements.length.toLocaleString()} of ${countLabel(bundle.requirements.length, "requirement")}</small>`}</search>`}
        <div class="requirements-selection-scroll">${visibleRequirements.length === 0 ? `<div class="requirements-filter-empty"><strong>No matching requirements</strong><p>Try a different search term.</p><button type="button" class="tertiary" data-action="reset-requirement-search">${icon("reset")}Clear search</button></div>` : `<div class="item-list">${visibleRequirements.map((item) => requirementRow(item, selected?.id)).join("")}</div>`}</div>
      </div></aside>
      <section class="review-content inspector-panel" aria-label="Selected requirement preview">
        ${selected === null ? emptyState("No requirements", "This requirement set is empty.") : requirementInspector(selected, bundle.sources, bundle.adapterId)}
      </section>
      </div>
      </div>
    </section>`;
}

export function renderStateModelsDetail(state: AppState): string {
  const bundle = state.stateModels;
  if (bundle === null) return emptyDetail("State models", "No state models loaded.");
  const model = selectedModel(state);
  if (model === null) return emptyDetail("State models", "The collection is empty.");
  return `
    <section class="page source-review-page" aria-labelledby="page-title">
      ${reviewHeader("Review state models", "Inspect the parsed states, transitions, actions, and page labels before running the analysis.", bundle.name)}
      <div class="page-content review-page-content">
      <div class="content-panel inspector-panel model-review-panel">
        ${modelPicker(bundle.models, model.id)}
        <div class="metric-strip">
          ${metric("States", model.counts.state)}${metric("Transitions", model.counts.transition)}
          ${metric("Actions", model.counts.action)}${metric("Widgets", model.counts.widget)}
        </div>
        <div class="panel-header graph-section-header"><div><p class="heading-context">${escapeHtml(humanizeToken(model.layer))} model</p><h2>${escapeHtml(model.title)}</h2></div><small>${countLabel(model.graph.nodes.length, "node")} · ${countLabel(model.graph.edges.length, "edge")}</small></div>
        <p class="graph-context">Page and action labels come from the parsed state model. Select a state or transition to focus its immediate connections.</p>
        ${graphCanvas(model, `State-model graph for ${model.title}. State labels and transition actions come from the parsed state model.`, "standalone-graph-shell")}
        ${stateModelTable(model)}
        <section class="review-source-section" aria-labelledby="review-source-files-title">
          <div class="panel-header"><h2 id="review-source-files-title">Source files</h2><small>${countLabel(bundle.sources.length, "state-model file")}</small></div>
          <p class="source-panel-description">These original files are used to create this preview and remain part of the analysis snapshot.</p>
          ${reviewSourceFileList(bundle.sources)}
        </section>
      </div>
      </div>
    </section>`;
}

export function renderResultDetail(state: AppState): string {
  const run = selectedRun(state);
  if (run === null) return emptyDetail("Results", "No analysis selected.");
  if (run.result === null) {
    const storedResultLoading = run.status === "complete" && state.resultsLoadState === "loading";
    const runContent = `${renderRunState(run, state)}${run.status === "running" ? runningResultShell(run, state) : ""}`;
    return `<section class="page result-page" aria-labelledby="page-title">${resultHeader(run, state)}<div class="page-content">${storedResultLoading ? storedResultLoadingShell() : runContent}</div></section>`;
  }
  const result = run.result;
  const assessedRequirementIds = result.assessments
    .filter(
      (item) => item.scopeKind === "requirement" && item.viewKind === "state-model-collection",
    )
    .map((item) => item.scopeId);
  const requirementIds =
    assessedRequirementIds.length > 0
      ? assessedRequirementIds
      : (state.requirements?.requirements.map((item) => item.id) ?? []);
  const visibleRequirementIds = filterResultRequirementIds({
    ids: requirementIds,
    requirements: state.requirements?.requirements ?? [],
    assessments: result.assessments,
    query: state.resultRequirementQuery,
    filter: state.resultRequirementFilter,
  });
  const requirementId = visibleRequirementIds.includes(state.selectedRequirementId)
    ? state.selectedRequirementId
    : (visibleRequirementIds[0] ?? "");
  const requirement = state.requirements?.requirements.find((item) => item.id === requirementId);
  const scope = resolveResultScope(
    result,
    requirementId,
    state.selectedResultScopeId,
    state.selectedElementId,
    state.selectedResultScopeKind,
    requirement,
  );
  const model = selectedModel(state);
  const occurrences = model === null ? [] : occurrencesForScope(result, scope, model.id);
  return `
    <section class="page result-page" aria-labelledby="page-title">
      ${resultHeader(run, state)}
      <div class="page-content">
      ${renderFeedback(state.analysisFeedback, "dismiss-analysis-feedback")}
      ${resultMetrics(result, state.stateModels?.models.length ?? 0)}
      ${result.pathDiagnostics.length === 0 ? "" : `<div class="feedback warning inline-feedback result-diagnostics" role="status"><span class="feedback-state-icon" aria-hidden="true">${icon("warning")}</span><span>${countLabel(result.pathDiagnostics.length, "requirement path")} could not be fully resolved. Results for affected paths may be limited.</span></div>`}
      <div class="content-panel result-layout result-inspector-shell">
      <aside class="result-nav"><div class="result-nav-scroll" data-scroll-key="result-requirements">
        <div class="panel-header"><h2>Requirements</h2>${resultRequirementCount(state, visibleRequirementIds.length, requirementIds.length)}</div>
        ${resultRequirementToolbar(state, requirementIds.length)}
        <div class="item-list">${
          visibleRequirementIds.length === 0
            ? `<div class="result-filter-empty"><strong>No matching requirements</strong><p>Adjust the search or completeness filter.</p><button type="button" class="tertiary" data-action="reset-result-requirement-filters">${icon("reset")}Reset filters</button></div>`
            : visibleRequirementIds
                .map((id) => resultRequirementRow(id, result, state, requirementId))
                .join("")
        }</div>
      </div></aside>
      <div class="result-workspace">
        <section class="graph-panel result-graph">
          ${resultGraphPanel(state, requirement, model, occurrences, scope.kind, result)}
        </section>
        <section class="result-inspector">
          ${
            requirement === undefined
              ? visibleRequirementIds.length === 0
                ? emptyState(
                    "No requirement selected",
                    "Adjust the requirement search or completeness filter.",
                  )
                : `${emptyState("Requirement details unavailable", "This analysis does not contain an inspectable requirement snapshot.")}${scopeSelector(result, requirementId, scope.id)}${assessmentPanel(assessmentForScope(result, scope), state, scope.elementIds)}`
              : resultRequirementInspector(
                  requirement,
                  result,
                  state.requirements?.sources ?? [],
                  state.requirements?.adapterId ?? "",
                )
          }
        </section>
      </div>
      </div>
      </div>
    </section>`;
}

export function selectedRun(state: AppState): AnalysisRun | null {
  return state.runs.find((run) => run.id === state.selectedRunId) ?? state.runs[0] ?? null;
}

function renderRequirementSource(state: AppState): string {
  const bundle = state.requirements;
  return `<section class="source-card" aria-labelledby="requirements-source-title">
    <div class="source-card-header"><span class="source-icon">${icon("requirements")}</span><div><h2 id="requirements-source-title">Requirements</h2><p class="source-status ${state.requirementsFeedback?.state ?? (bundle !== null ? "ready" : state.requirementAdapters.length === 0 ? "running" : "")}"${sourceStatusRole(state.requirementsFeedback, bundle !== null)}>${feedbackText(state.requirementsFeedback, bundle === null ? requirementSourceHint(state.requirementAdapters) : `${countLabel(bundle.requirements.length, "requirement")} from ${countLabel(bundle.sources.length, "file")}`)}</p></div></div>
    <div class="source-dropzone ${bundle === null ? "" : "compact"}" data-drop-target="requirements">
      <span class="dropzone-icon">${icon("upload")}</span>
      <div class="dropzone-copy"><strong>${bundle === null ? `<span class="drop-label-desktop">Drop requirement files or folders</span><span class="drop-label-touch">Add requirement files or folders</span>` : "Add more sources"}</strong><p>${supportedFormatsText(state.requirementAdapters, "requirement files")} Mixed formats are supported.</p></div>
      <div class="source-actions"><button type="button" ${bundle === null ? "" : `class="secondary"`} data-action="load-requirements-files">${icon("files")}${bundle === null ? "Choose files" : "Add files"}</button><button type="button" class="secondary" data-action="load-requirements-directory">${icon("folder")}${bundle === null ? "Choose folder" : "Add folder"}</button></div>
    </div>
    ${renderSelectedSources(bundle?.sources ?? [], "requirements", bundle !== null)}
  </section>`;
}

function renderStateModelSource(state: AppState): string {
  const bundle = state.stateModels;
  return `<section class="source-card" aria-labelledby="state-model-source-title">
    <div class="source-card-header"><span class="source-icon">${icon("stateModels")}</span><div><h2 id="state-model-source-title">State models</h2><p class="source-status ${state.stateModelsFeedback?.state ?? (bundle !== null ? "ready" : state.stateModelAdapters.length === 0 ? "running" : "")}"${sourceStatusRole(state.stateModelsFeedback, bundle !== null)}>${feedbackText(state.stateModelsFeedback, bundle === null ? stateModelSourceHint(state.stateModelAdapters) : `${countLabel(bundle.models.length, "state model")} from ${countLabel(bundle.sources.length, "file")}`)}</p></div></div>
    <div class="source-dropzone ${bundle === null ? "" : "compact"}" data-drop-target="state-models">
      <span class="dropzone-icon">${icon("upload")}</span>
      <div class="dropzone-copy"><strong>${bundle === null ? `<span class="drop-label-desktop">Drop state-model files or folders</span><span class="drop-label-touch">Add state-model files or folders</span>` : "Add more sources"}</strong><p>Add TESTAR state-model files in JSON format. Each file must contain one state model.</p></div>
      <div class="source-actions"><button type="button" ${bundle === null ? "" : `class="secondary"`} data-action="load-state-model-files">${icon("files")}${bundle === null ? "Choose files" : "Add files"}</button><button type="button" class="secondary" data-action="load-state-model-directory">${icon("folder")}${bundle === null ? "Choose folder" : "Add folder"}</button></div>
    </div>
    ${renderSelectedSources(bundle?.sources ?? [], "state-models", bundle !== null)}
  </section>`;
}

function sourceStatusRole(feedback: AppState["requirementsFeedback"], loaded: boolean): string {
  if (feedback?.state === "error") return ' role="alert"';
  return feedback !== null || loaded ? ' role="status"' : "";
}

function renderAnalysisLauncher(state: AppState): string {
  const ready =
    state.requirements !== null && state.stateModels !== null && state.methods.length > 0;
  return `<footer class="analysis-launcher">
    <p class="local-processing">${icon("local")}${LOCAL_PROCESSING_MESSAGE}</p>
    <button type="submit" class="primary-action" ${ready ? "" : "disabled"}>${icon("run")}Run analysis</button>
    ${renderFeedback(state.analysisFeedback, "dismiss-analysis-feedback")}
  </footer>`;
}

function renderSelectedSources(
  sources: RawSource[],
  kind: "requirements" | "state-models",
  loaded: boolean,
): string {
  if (sources.length === 0) return "";
  const inspectAction = kind === "requirements" ? "show-requirements" : "show-state-models";
  const clearAction = kind === "requirements" ? "clear-requirements" : "clear-state-models";
  const removeAction =
    kind === "requirements" ? "remove-requirement-source" : "remove-state-model-source";
  const inspectLabel = kind === "requirements" ? "Review requirements" : "Review state models";
  const visibleSources = sources.slice(0, 6);
  const remainingSources = sources.slice(6);
  const sourceRows = (items: RawSource[]): string =>
    items
      .map(
        (source) =>
          `<li><span class="selected-source-name">${icon("file")}<span><strong title="${escapeHtml(source.name)}">${escapeHtml(source.name)}</strong><small>${escapeHtml(formatLabel(source.format))}</small></span></span><button type="button" class="icon-action remove-source-action" data-action="${removeAction}" data-source-id="${escapeHtml(source.id)}" aria-label="Remove ${escapeHtml(source.name)}" title="Remove file">${icon("close")}</button></li>`,
      )
      .join("");
  return `<div class="selected-sources">
    <div class="selected-sources-header"><strong>Selected files <span>${sources.length}</span></strong><div><button type="button" class="tertiary compact-action" data-action="${inspectAction}" ${loaded ? "" : "disabled"}>${icon("inspect")}${inspectLabel}</button><button type="button" class="tertiary compact-action clear-sources-action" data-action="${clearAction}">${icon("close")}Clear files</button></div></div>
    <ul>${sourceRows(visibleSources)}</ul>
    ${remainingSources.length === 0 ? "" : `<details class="additional-sources">${disclosureSummary(`Show ${countLabel(remainingSources.length, "more file")}`)}<ul>${sourceRows(remainingSources)}</ul></details>`}
  </div>`;
}

function reviewSourceFileList(sources: RawSource[]): string {
  const visibleSources = sources.slice(0, 6);
  const remainingSources = sources.slice(6);
  const rows = (items: RawSource[]): string =>
    items
      .map(
        (source) =>
          `<li><span>${icon("file")}<strong>${escapeHtml(source.name)}</strong></span><small>${escapeHtml(formatLabel(source.format))}</small></li>`,
      )
      .join("");
  return `<ul class="source-file-list">${rows(visibleSources)}</ul>${remainingSources.length === 0 ? "" : `<details class="additional-sources review-additional-sources">${disclosureSummary(`Show ${countLabel(remainingSources.length, "more file")}`)}<ul class="source-file-list">${rows(remainingSources)}</ul></details>`}`;
}

function renderAnalysesEmptyState(): string {
  return `<section class="analyses-empty" aria-labelledby="analyses-empty-title">
    <div class="empty-illustration" aria-hidden="true">${icon("emptyAnalyses")}</div>
    <h2 id="analyses-empty-title">No analyses yet</h2>
    <p>Start a new analysis or import an exported TESTAR Trace analysis file.</p>
    <div class="empty-actions"><button type="button" data-action="start-new-analysis">${icon("newAnalysis")}New analysis</button><button type="button" class="secondary" data-action="open-import-dialog">${icon("import")}Import analysis</button></div>
    <ol class="how-it-works" aria-label="How an analysis works">
      <li><span aria-hidden="true">1</span><strong>Add sources</strong><p>Select requirement and state-model files or folders.</p></li>
      <li><span aria-hidden="true">2</span><strong>Run the analysis</strong><p>Choose a traceability method and evaluate completeness with supporting trace evidence.</p></li>
      <li><span aria-hidden="true">3</span><strong>Review results</strong><p>Explore completeness, requirement paths, and matched state-model elements.</p></li>
    </ol>
  </section>`;
}

function renderFilteredEmptyState(): string {
  return `<div class="filtered-empty"><strong>No analyses match these filters</strong><p>Adjust the search or filters to see more results.</p><button type="button" class="secondary" data-action="reset-analysis-filters">${icon("reset")}Reset filters</button></div>`;
}

export function methodDescription(methodId: string): string {
  if (methodId === "graph-alignment") {
    return "Recommended for completeness checks. Aligns each requirement path to a connected state-model route.";
  }
  if (methodId === "execution-alignment") {
    return "Checks requirement paths against recorded execution sequences. Use when state models contain execution data.";
  }
  if (methodId === "automata-conformance") {
    return "Performs strict formal conformance checking. Best for explicitly structured requirements; ambiguous content may be not assessable.";
  }
  if (methodId === "lexical") {
    return "Matches requirement terms without enforcing path order or connectivity. Useful for evidence coverage, not behavioral completeness.";
  }
  return methodId === ""
    ? "Choose how requirement paths are evaluated against the state models."
    : "Evaluates requirement paths and elements against the state models.";
}

function renderAnalysisTable(runs: AnalysisRun[], state: AppState): string {
  const selected = new Set(state.selectedAnalysisIds);
  const selectedOnPage = runs.filter((run) => selected.has(run.id)).length;
  const allOnPageSelected = runs.length > 0 && selectedOnPage === runs.length;
  const mixed = selectedOnPage > 0 && !allOnPageSelected;
  return `<div class="analysis-table-wrap"><table class="analysis-table${state.selectedAnalysisIds.length > 0 ? " batch-mode" : ""}">
    <caption class="visually-hidden">Saved traceability analyses</caption>
    <thead><tr><th scope="col" class="selection-column"><label><span class="visually-hidden">Select all analyses on this page</span><input id="select-page-analyses" type="checkbox" ${allOnPageSelected ? "checked" : ""} ${mixed ? `data-indeterminate="true" aria-checked="mixed"` : ""}></label></th><th scope="col" class="name-column">Analysis</th><th scope="col" class="method-column">Method</th><th scope="col" class="status-column">Status</th><th scope="col" class="completeness-column">Completeness</th><th scope="col" class="created-column">Created</th><th scope="col" class="actions-column"><span class="visually-hidden">Actions</span></th></tr></thead>
    <tbody>${runs.map((run, index) => renderAnalysisRow(run, state, index)).join("")}</tbody>
  </table></div>`;
}

function renderAnalysisRow(run: AnalysisRun, state: AppState, rowIndex: number): string {
  const completeness = overallCompleteness(run);
  const completenessLoading =
    run.status === "complete" && run.result === null && state.resultsLoadState === "loading";
  const restoringResult =
    run.status === "complete" && run.result === null && state.resultsLoadState === "loading";
  const secondaryActions = secondaryAnalysisActions(run, restoringResult);
  const menuId = `analysis-actions-${rowIndex}`;
  const selected = state.selectedAnalysisIds.includes(run.id);
  const batchMode = state.selectedAnalysisIds.length > 0;
  return `<tr class="${selected ? "selected" : ""}">
    <td class="selection-cell" data-label="Select"><label><span class="visually-hidden">Select ${escapeHtml(run.title)}</span><input type="checkbox" data-analysis-select="${escapeHtml(run.id)}" ${selected ? "checked" : ""}></label></td>
    <td class="analysis-name-cell" data-label="Analysis">${renderAnalysisNameCell(run, state)}</td>
    <td class="method-cell" data-label="Method">${methodChip(methodDisplayName(run, state))}</td>
    <td class="status-cell" data-label="Status">${statusPill(run.status)}${run.status === "running" ? `<div class="row-progress" role="progressbar" aria-label="Analysis progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(run.progress * 100)}"><span style="width:${Math.round(run.progress * 100)}%"></span></div>` : ""}</td>
    <td class="completeness-cell" data-label="Completeness">${completenessLoading ? `<span class="completeness-loading" role="status"><span class="visually-hidden">Loading completeness for ${escapeHtml(run.title)}</span></span>` : renderOverviewCompleteness(run, completeness)}</td>
    <td class="created-cell" data-label="Created"><span class="compact-field-label">Created</span>${renderCreatedAt(run.createdAt)}</td>
    <td class="actions-cell" data-label="Actions"><div class="table-actions ${batchMode ? "batch-disabled" : ""}" ${batchMode ? `inert aria-hidden="true"` : ""}>
      ${
        run.status === "running"
          ? `<button type="button" class="icon-action danger" data-action="cancel-run" data-run-id="${escapeHtml(run.id)}" aria-label="Cancel ${escapeHtml(run.title)}" title="Cancel analysis">${icon("cancel")}</button>`
          : `<a class="icon-action primary" href="${routePath("result", run.id)}" data-route aria-label="View ${escapeHtml(run.title)}" title="View results">${icon("inspect")}</a>`
      }
      <button type="button" class="icon-action" data-menu-id="${menuId}" popovertarget="${menuId}" popovertargetaction="toggle" aria-label="More actions for ${escapeHtml(run.title)}" aria-haspopup="menu" aria-expanded="false" aria-controls="${menuId}" title="More actions">${icon("more")}</button>
      <div id="${menuId}" class="row-action-menu" style="--menu-item-count:${secondaryActions.length}" data-run-actions-menu popover="auto" role="menu" aria-label="Actions for ${escapeHtml(run.title)}">${secondaryActions
        .map((action) =>
          renderRowMenuAction(
            action,
            run,
            run.result === null && (action === "duplicate" || action === "export"),
          ),
        )
        .join("")}</div>
    </div></td>
  </tr>`;
}

function renderAnalysisBatchToolbar(runs: AnalysisRun[], totalMatching: number): string {
  const exportable = runs.every(
    (run) =>
      run.status === "complete" &&
      run.result !== null &&
      run.requirements !== null &&
      run.stateModels !== null,
  );
  const exportTitle = exportable
    ? `Export ${countLabel(runs.length, "selected analysis", "selected analyses")}`
    : "All selected analyses must be finished and contain their saved inputs before export.";
  const exportDescription = exportable
    ? ""
    : `<small id="batch-export-description" class="batch-action-note">Export requires finished analyses with saved inputs.</small>`;
  const selectAll =
    runs.length < totalMatching
      ? `<button type="button" class="batch-action batch-select-all" data-action="select-all-filtered-analyses">Select all ${totalMatching.toLocaleString()}</button>`
      : "";
  return `<section class="analysis-batch-toolbar" aria-label="Selected analysis actions"><div class="batch-selection-summary"><strong>${countLabel(runs.length, "analysis", "analyses")} selected</strong>${selectAll}</div><div class="batch-actions">${exportDescription}<button type="button" class="batch-action" data-action="export-selected-runs" ${exportable ? "" : `disabled aria-describedby="batch-export-description"`} title="${escapeHtml(exportTitle)}">${icon("export")}Export selected</button><button type="button" class="batch-action danger" data-action="delete-selected-runs">${icon("delete")}Delete selected</button></div><button type="button" class="batch-action icon-only" data-action="clear-analysis-selection" aria-label="Clear selection" title="Clear selection">${icon("close")}</button></section>`;
}

function renderAnalysisNameCell(run: AnalysisRun, state: AppState): string {
  if (state.renamingRunId !== run.id) {
    return `<a class="analysis-name" href="${routePath("result", run.id)}" data-route aria-label="View ${escapeHtml(run.title)}" title="${escapeHtml(run.title)}"><strong>${escapeHtml(run.title)}</strong></a>`;
  }
  return `<form class="inline-rename" data-rename-run-id="${escapeHtml(run.id)}">
    <label class="visually-hidden" for="rename-run-input">Analysis name</label>
    <input id="rename-run-input" type="text" maxlength="120" autocomplete="off" required value="${escapeHtml(state.renameDraft)}">
    <button type="submit" class="icon-action primary" aria-label="Save analysis name" title="Save name">${icon("save")}</button>
    <button type="button" class="icon-action" data-action="cancel-rename-run" aria-label="Cancel renaming" title="Cancel">${icon("close")}</button>
  </form>`;
}

export function renderOverviewCompleteness(run: AnalysisRun, value: number | null): string {
  if (run.status !== "complete" || run.result === null) {
    return `<span class="unavailable" title="Completeness unavailable">—</span>`;
  }
  const summary = run.result.summary;
  if (summary.totalRequirements === 0) {
    return `<span class="unavailable" title="No requirements were assessed">—</span>`;
  }
  if (summary.notAssessableRequirements === summary.totalRequirements) {
    return `<span class="completeness-chip not-assessable">${completenessStatusIcon("not-assessable")}Not assessable</span>`;
  }
  if (value === 1)
    return `<span class="completeness-chip complete">${completenessStatusIcon("complete")}Complete</span>`;
  const notes =
    summary.notAssessableRequirements === 0
      ? []
      : [
          summary.incompleteRequirements > 0
            ? countLabel(summary.incompleteRequirements, "incomplete requirement")
            : "",
          countLabel(
            summary.notAssessableRequirements,
            "requirement not assessable",
            "requirements not assessable",
          ),
        ].filter((item) => item !== "");
  return `<span class="overview-completeness"><strong>${summary.completeRequirements} of ${summary.totalRequirements} complete</strong>${notes.length === 0 ? "" : `<small>${notes.join(" · ")}</small>`}</span>`;
}

function renderRowMenuAction(
  action: AnalysisRowAction,
  run: AnalysisRun,
  disabled = false,
): string {
  const details = {
    rename: { label: "Rename", iconName: "rename", action: "rename-run" },
    duplicate: { label: "Duplicate", iconName: "duplicate", action: "duplicate-run" },
    export: { label: "Export", iconName: "export", action: "export-run" },
    delete: { label: "Delete", iconName: "delete", action: "delete-run" },
  } as const;
  const item = details[action];
  const unavailableTitle = disabled
    ? `${item.label} is available when the analysis result is ready.`
    : "";
  return `<button type="button" role="menuitem" class="${action === "delete" ? "danger" : ""}" data-action="${item.action}" data-run-id="${escapeHtml(run.id)}" ${disabled ? `disabled title="${escapeHtml(unavailableTitle)}"` : ""}>${icon(item.iconName)}${item.label}</button>`;
}

function renderAnalysisPagination(page: ReturnType<typeof getAnalysisPage>): string {
  if (page.totalItems === 0) return "";
  const rangeLabel = `Showing analyses ${page.start} through ${page.end} of ${page.totalItems}`;
  return `<footer class="analysis-pagination"><p aria-label="${rangeLabel}">${page.start}–${page.end} of ${page.totalItems} ${page.totalItems === 1 ? "analysis" : "analyses"}</p>
    ${page.totalPages <= 1 ? "" : `<nav aria-label="Analysis pages"><button type="button" class="secondary" data-action="previous-analysis-page" ${page.page === 1 ? "disabled" : ""} aria-label="Previous page">${icon("previous")}</button><span>Page ${page.page} of ${page.totalPages}</span><button type="button" class="secondary" data-action="next-analysis-page" ${page.page === page.totalPages ? "disabled" : ""} aria-label="Next page">${icon("next")}</button></nav>`}
  </footer>`;
}

function statusFilterOptions(selected: string): string {
  return [
    ["all", "All statuses"],
    ["complete", "Finished"],
    ["running", "Running"],
    ["failed", "Failed"],
    ["cancelled", "Cancelled"],
  ]
    .map(
      ([value, label]) =>
        `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`,
    )
    .join("");
}

function methodFilterOptions(state: AppState): string {
  const methods = new Map(state.methods.map((item) => [item.id, item.name]));
  for (const run of state.runs) {
    if (!methods.has(run.methodId)) methods.set(run.methodId, run.methodName);
  }
  return `<option value="all" ${state.analysisMethodFilter === "all" ? "selected" : ""}>All methods</option>${[...methods].map(([id, name]) => `<option value="${escapeHtml(id)}" ${id === state.analysisMethodFilter ? "selected" : ""}>${escapeHtml(name)}</option>`).join("")}`;
}

function sortOptions(selected: string): string {
  return [
    ["created-desc", "Newest first"],
    ["created-asc", "Oldest first"],
    ["name-asc", "Analysis name A–Z"],
    ["completeness-desc", "Highest completeness"],
  ]
    .map(
      ([value, label]) =>
        `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`,
    )
    .join("");
}

function renderRunState(run: AnalysisRun, state: AppState): string {
  if (run.status === "running") {
    const detail = run.progressDetail;
    const completed = detail?.completed ?? null;
    const total = detail?.total ?? null;
    const determinate = completed !== null && total !== null && total > 0;
    const phaseProgress = determinate ? completed / total : null;
    const helper = determinate
      ? `${completed.toLocaleString()} of ${total.toLocaleString()} requirement elements`
      : "You can leave this page and return while the analysis continues.";
    return `<section class="analysis-progress-panel" aria-labelledby="analysis-progress-title">
      <div class="progress-heading"><div><p class="heading-context">Analysis running</p><h2 id="analysis-progress-title">${escapeHtml(progressPhaseLabel(detail?.phase ?? "analysis.started"))}</h2></div><button type="button" class="secondary danger" data-action="cancel-run" data-run-id="${escapeHtml(run.id)}">${icon("cancel")}Cancel</button></div>
      <div class="progress-bar ${determinate ? "" : "indeterminate"}" role="progressbar" aria-label="${escapeHtml(run.message)}" aria-valuemin="0" aria-valuemax="100" ${phaseProgress === null ? "" : `aria-valuenow="${Math.round(phaseProgress * 100)}"`}><span style="${phaseProgress === null ? "" : `width:${Math.round(phaseProgress * 100)}%`}"></span></div>
      <div class="progress-copy"><p>${escapeHtml(run.message)}</p><small>${escapeHtml(helper)}</small></div>
      <p class="local-processing progress-local">${icon("local")}${LOCAL_PROCESSING_MESSAGE}</p>
      <p class="visually-hidden" aria-live="polite">${escapeHtml(run.message)}${determinate ? `, ${completed} of ${total}` : ""}</p>
    </section>`;
  }
  if (run.status === "complete") {
    if (state.resultsLoadState === "error") {
      return `<p class="feedback error inline-feedback" role="alert">${feedbackStateIcon("error")}<span>Saved results could not be loaded from this browser.</span></p>`;
    }
    return emptyState(
      "Results unavailable",
      "The saved analysis metadata is available, but its result data could not be loaded.",
    );
  }
  const feedbackState = run.status === "failed" ? "error" : "empty";
  return `<p class="feedback ${feedbackState} inline-feedback" role="${run.status === "failed" ? "alert" : "status"}">${feedbackStateIcon(run.status)}<span>${escapeHtml(run.message)}</span></p>`;
}

function storedResultLoadingShell(): string {
  return `<div class="stored-result-loading" aria-busy="true" aria-label="Loading saved analysis results">
    ${pendingResultMetrics()}
    <div class="content-panel result-layout result-inspector-shell loading-result-layout">
      <aside class="result-nav"><div class="result-nav-scroll loading-panel"><div class="panel-header"><h2>Requirements</h2><span class="skeleton-line skeleton-count" aria-hidden="true"></span></div><span class="skeleton-line"></span><span class="skeleton-line"></span><span class="skeleton-line"></span></div></aside>
      <div class="result-workspace">
        <section class="graph-panel result-graph graph-panel-loading"><div class="graph-heading"><h2 id="result-state-model-title">State model</h2></div>${storedResultEvidenceSkeleton()}</section>
        <section class="result-inspector loading-panel"><div class="inspector-heading"><div><span class="skeleton-line skeleton-caption"></span><span class="skeleton-line skeleton-heading"></span></div><span class="completeness-chip pending">${completenessStatusIcon("pending")}Loading</span></div><span class="skeleton-line"></span><span class="skeleton-line"></span><span class="skeleton-line"></span></section>
      </div>
    </div>
    <p class="visually-hidden" role="status">Loading saved analysis results.</p>
  </div>`;
}

function storedResultEvidenceSkeleton(): string {
  return `<section class="state-model-evidence" aria-labelledby="result-state-model-title"><div class="path-evidence-workspace workspace-view-graph loading-evidence-workspace"><div class="path-workspace-switcher pending-path-switcher"><div class="path-workspace-controls"><div><strong>Requirement path</strong><span class="skeleton-line skeleton-select" aria-hidden="true"></span></div><div><strong>State model</strong><span class="skeleton-line skeleton-model-select" aria-hidden="true"></span></div></div></div><section id="path-workspace-panel" class="path-workspace-detail" aria-hidden="true"><div class="pending-path-detail"><span></span><span></span><span></span><span></span></div></section><section id="graph-workspace-panel" class="graph-workspace-stage" aria-hidden="true"><span class="skeleton-line skeleton-legend"></span><span class="skeleton-graph"></span></section></div></section>`;
}

function pendingResultMetrics(run?: AnalysisRun): string {
  const pathCount = progressMetadataNumber(run?.progressDetail, "total_paths");
  const pendingValue = `<strong class="pending-metric-value"><span class="skeleton-line" aria-hidden="true"></span><span class="visually-hidden">Pending</span></strong>`;
  return `<section class="result-dashboard loading-dashboard" aria-label="Analysis summary">
    <article class="summary-card headline-summary"><span>Requirements complete</span>${pendingValue}<small><span class="skeleton-line skeleton-copy" aria-hidden="true"></span></small></article>
    <article class="summary-card"><span>Paths complete</span>${pendingValue}<small>${pathCount === null ? `<span class="skeleton-line skeleton-copy" aria-hidden="true"></span>` : `${countLabel(pathCount, "path")} identified`}</small></article>
    <article class="summary-card"><span>Evidence coverage</span>${pendingValue}<span class="skeleton-meter" aria-hidden="true"></span><small>Share of required elements supported by trace evidence</small></article>
  </section>`;
}

function progressMetadataNumber(
  progress: AnalysisProgress | undefined,
  key: string,
): number | null {
  const value = progress?.metadata[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function progressPhaseLabel(phase: string): string {
  if (phase.includes("matching")) return "Matching requirement elements";
  if (phase.includes("assessing")) return "Building result assessments";
  if (phase.includes("completed")) return "Finalizing results";
  if (phase.includes("noop")) return "Preparing diagnostic result";
  return "Preparing requirements and state models";
}

function runningResultShell(run: AnalysisRun, state: AppState): string {
  const requirements = run.requirements;
  const stateModels = run.stateModels;
  if (requirements === null || stateModels === null) return "";
  const query = state.resultRequirementQuery.trim().toLocaleLowerCase();
  const visibleRequirements = requirements.requirements.filter(
    (requirement) =>
      query === "" || `${requirement.id} ${requirement.title}`.toLocaleLowerCase().includes(query),
  );
  const selectedRequirement =
    visibleRequirements.find((item) => item.id === state.selectedRequirementId) ??
    visibleRequirements[0];
  const selectedModel =
    stateModels.models.find((item) => item.id === state.selectedStateModelId) ??
    stateModels.models[0];
  return `<div class="running-result" aria-busy="true" aria-label="Analysis in progress">
    ${pendingResultMetrics(run)}
    <div class="content-panel result-layout result-inspector-shell">
      <aside class="result-nav"><div class="result-nav-scroll" data-scroll-key="result-requirements">
        <div class="panel-header"><h2>Requirements</h2>${resultRequirementCount(state, visibleRequirements.length, requirements.requirements.length)}</div>
        ${resultRequirementToolbar(state, requirements.requirements.length, true)}
        <div class="item-list">${
          visibleRequirements.length === 0
            ? `<div class="result-filter-empty"><strong>No matching requirements</strong><p>Adjust the requirement search.</p><button type="button" class="tertiary" data-action="reset-result-requirement-filters">${icon("reset")}Clear search</button></div>`
            : visibleRequirements
                .map(
                  (requirement) =>
                    `<button type="button" class="coverage-row ${requirement.id === selectedRequirement?.id ? "selected" : ""}" data-action="select-requirement" data-requirement-id="${escapeHtml(requirement.id)}"${requirement.id === selectedRequirement?.id ? ' aria-current="true"' : ""}><span><strong>${escapeHtml(requirement.id)} · ${escapeHtml(requirement.title)}</strong><span class="requirement-row-meta"><small>Assessment pending</small><span class="completeness-chip pending">${completenessStatusIcon("pending")}Analyzing</span></span></span></button>`,
                )
                .join("")
        }</div>
      </div></aside>
      <div class="result-workspace">
        <section class="graph-panel result-graph running-graph">
          <div class="graph-heading"><h2 id="result-state-model-title">State model</h2></div>
          ${pendingEvidenceWorkspace(state, selectedRequirement !== undefined, selectedModel)}
        </section>
        <section class="result-inspector">
          ${selectedRequirement === undefined ? emptyState("No requirement selected", "Adjust the requirement search.") : pendingRequirementInspector(selectedRequirement, requirements.sources, requirements.adapterId)}
        </section>
      </div>
    </div>
    <p class="visually-hidden" role="status">${escapeHtml(run.message)}</p>
  </div>`;
}

function pendingRequirementInspector(
  requirement: RequirementItem,
  sources: RawSource[],
  adapterId: string,
): string {
  return `<div class="inspector-heading result-requirement-heading"><div><p class="heading-context">${escapeHtml(requirementHeadingContext(adapterId, requirement))}</p><h2>${escapeHtml(requirement.title)}</h2></div><span class="completeness-chip pending">${completenessStatusIcon("pending")}Analyzing</span></div>
    ${resultRequirementSpecification(requirement, sources, adapterId)}`;
}

function pendingEvidenceWorkspace(
  state: AppState,
  requirementAvailable: boolean,
  model: StateModel | undefined,
): string {
  const modelControl = resultModelControl(state.stateModels?.models ?? [], model?.id ?? "");
  const navigation = requirementAvailable
    ? `<div class="path-workspace-switcher pending-path-switcher" aria-label="Requirement paths loading"><div class="path-workspace-controls"><div><strong>Requirement path</strong><span class="skeleton-line skeleton-select" aria-hidden="true"></span></div>${modelControl}</div></div><section id="path-workspace-panel" class="path-workspace-detail" data-scroll-key="result-path-details" role="tabpanel" aria-labelledby="path-workspace-tab-paths"><div class="pending-path-detail" aria-hidden="true"><span></span><span></span><span></span><span></span></div></section>`
    : `<div class="path-workspace-switcher"><div class="path-workspace-controls"><div><strong>Requirement path</strong><small>No requirement selected</small></div>${modelControl}</div></div><section id="path-workspace-panel" class="path-workspace-detail" data-scroll-key="result-path-details" role="tabpanel" aria-labelledby="path-workspace-tab-paths"><div class="path-workspace-prompt"><strong>No requirement selected</strong><p>Choose a requirement to inspect its paths when analysis completes.</p></div></section>`;
  const graph =
    model === undefined
      ? emptyState("State model unavailable", "The input snapshot could not be displayed.")
      : graphCanvas(
          model,
          "State model while completeness evidence is analyzed",
          "result-graph-shell",
        );
  return `<section class="state-model-evidence" aria-labelledby="result-state-model-title"><div class="path-evidence-workspace workspace-view-${state.resultWorkspaceTab}">${pathWorkspaceTabs(state)}${navigation}<section id="graph-workspace-panel" class="graph-workspace-stage" role="tabpanel" aria-labelledby="path-workspace-tab-graph">${model === undefined ? "" : stateModelLegend(model, [], null, undefined)}${graph}${model === undefined ? "" : stateModelTable(model)}</section></div></section>`;
}

function resultHeader(run: AnalysisRun, state: AppState): string {
  const portable = run.requirements !== null && run.stateModels !== null;
  const exportReady = run.status === "complete" && run.result !== null && portable;
  const restoringResult =
    run.status === "complete" && run.result === null && state.resultsLoadState === "loading";
  const menuActions = secondaryAnalysisActions(run, restoringResult).filter(
    (action) => action !== "export",
  );
  const exportVisible = secondaryAnalysisActions(run, restoringResult).includes("export");
  const exportTitle = exportReady
    ? "Export analysis"
    : run.status === "running"
      ? "Export is available when the analysis is complete."
      : state.resultsLoadState === "loading"
        ? "Loading the analysis data required for export."
        : "Export requires a complete analysis with its input snapshots.";
  const menuId = "result-actions-menu";
  return `<header class="page-header detail-header result-header">
    ${backLink("analyses", "Back to analyses")}
    <div class="result-header-main"><div>${renderResultTitle(run, state)}<div class="result-metadata"><span class="result-metadata-item">${statusPill(run.status)}</span><span class="result-metadata-item">${methodChip(methodDisplayName(run, state))}</span><span class="result-metadata-item">Created ${escapeHtml(formatAnalysisDateTime(run.createdAt))}</span></div></div>
    <div class="result-header-actions">${exportVisible ? `<button type="button" class="secondary" data-action="export-run" data-run-id="${escapeHtml(run.id)}" ${exportReady ? "" : "disabled"} title="${escapeHtml(exportTitle)}">${icon("export")}Export analysis</button>` : ""}${menuActions.length === 0 ? "" : `<button type="button" class="icon-action result-more-action" data-menu-id="${menuId}" popovertarget="${menuId}" popovertargetaction="toggle" aria-label="More actions for ${escapeHtml(run.title)}" aria-haspopup="menu" aria-expanded="false" aria-controls="${menuId}" title="More actions">${icon("more")}</button><div id="${menuId}" class="row-action-menu" style="--menu-item-count:${menuActions.length}" data-run-actions-menu popover="auto" role="menu" aria-label="Actions for ${escapeHtml(run.title)}">${menuActions.map((action) => renderRowMenuAction(action, run, action === "duplicate" && run.result === null)).join("")}</div>`}</div></div>
  </header>`;
}

function renderResultTitle(run: AnalysisRun, state: AppState): string {
  if (state.renamingRunId !== run.id) {
    return `<h1 id="page-title">${analysisTitleMarkup(run.title)}</h1>`;
  }
  return `<form class="inline-rename result-title-rename" data-rename-run-id="${escapeHtml(run.id)}">
    <label class="visually-hidden" for="rename-run-input">Analysis name</label>
    <input id="rename-run-input" type="text" maxlength="120" required value="${escapeHtml(state.renameDraft)}">
    <button type="submit" class="icon-action primary" aria-label="Save analysis name" title="Save name">${icon("save")}</button>
    <button type="button" class="icon-action" data-action="cancel-rename-run" aria-label="Cancel renaming" title="Cancel">${icon("close")}</button>
  </form>`;
}

function analysisTitleMarkup(title: string): string {
  return escapeHtml(title).replaceAll(" · ", "&nbsp;·&nbsp;");
}

function requirementRow(item: RequirementItem, selectedId: string | undefined): string {
  const selected = item.id === selectedId;
  return `<button type="button" class="item-row ${selected ? "selected" : ""}" data-action="select-requirement" data-requirement-id="${escapeHtml(item.id)}"${selected ? ' aria-current="true"' : ""}><span><strong>${escapeHtml(item.id)} · ${escapeHtml(item.title)}</strong><small>${countLabel(item.flows.length, "flow")} · ${countLabel(item.elements.length, "traceable element")}</small></span></button>`;
}

function requirementInspector(
  requirement: RequirementItem,
  sources: RawSource[],
  adapterId: string,
): string {
  return `<div class="inspector-heading"><div><p class="heading-context">${escapeHtml(requirementHeadingContext(adapterId, requirement))}</p><h2>${escapeHtml(requirement.title)}</h2></div><span class="subtle">${escapeHtml(requirement.actor || "Actor not specified")}</span></div>
    ${resultRequirementSpecification(requirement, sources, adapterId)}`;
}

function resultRequirementInspector(
  requirement: RequirementItem,
  result: AnalysisResult,
  sources: RawSource[],
  adapterId: string,
): string {
  const requirementAssessment = collectionAssessment(result, "requirement", requirement.id);
  return `<div class="inspector-heading result-requirement-heading"><div><p class="heading-context">${escapeHtml(requirementHeadingContext(adapterId, requirement))}</p><h2>${escapeHtml(requirement.title)}</h2></div><div class="requirement-assessment-status">${completenessBadge(requirementAssessment)}</div></div>
    ${resultAssessmentDetails(requirementAssessment)}
    ${resultRequirementSpecification(requirement, sources, adapterId)}
    ${resultAdditionalElements(requirement, requirementAssessment, null)}`;
}

function resultRequirementSpecification(
  requirement: RequirementItem,
  sources: RawSource[],
  adapterId: string,
): string {
  const useCaseFormat = isUseCaseRequirement(adapterId, requirement);
  const constraints = requirement.elements
    .filter((element) => element.kind === "constraint")
    .map((element) => element.text);
  const preconditions = requirement.elements
    .filter((element) => element.kind === "precondition")
    .map((element) => element.text);
  const triggers = requirement.elements
    .filter((element) => element.kind === "trigger")
    .map((element) => element.text);
  const postconditions = requirement.elements
    .filter((element) => element.kind === "postcondition")
    .map((element) => element.text);
  const metadata = requirement.metadata ?? {};
  const sourceText = requirementSourceText(requirement, sources);
  const knownMetadata = new Set([
    "stakeholders",
    "technology_and_data_variations",
    "related_information",
    "source_index",
    "source_name",
  ]);
  const leadFields: Array<[string, string[]]> = [];
  const trailingFields: Array<[string, string[]]> = [];
  const addField = (fields: Array<[string, string[]]>, label: string, values: string[]): void => {
    if (values.length > 0) fields.push([label, values]);
  };
  addField(leadFields, "Context of use", requirement.summary === "" ? [] : [requirement.summary]);
  addField(leadFields, "Scope", requirement.scope ? [requirement.scope] : []);
  addField(leadFields, "Level", requirement.level ? [requirement.level] : []);
  addField(leadFields, "Primary actor", requirement.actor === "" ? [] : [requirement.actor]);
  addField(leadFields, "Stakeholders and interests", metadataValues(metadata.stakeholders));
  addField(leadFields, "Constraints", constraints);
  addField(leadFields, "Preconditions", preconditions);
  addField(leadFields, "Trigger", triggers);
  const technologyVariations = firstAvailableValues(
    metadataValues(metadata.technology_and_data_variations),
    markdownSectionValues(sourceText, "Technology and Data Variations List"),
  );
  addField(
    trailingFields,
    "Technology and data variations list",
    technologyVariations.length === 0 ? ["None specified"] : technologyVariations,
  );
  addField(trailingFields, "Related information", metadataValues(metadata.related_information));
  for (const [key, value] of Object.entries(metadata)) {
    if (!knownMetadata.has(key)) {
      addField(trailingFields, humanizeToken(key), metadataValues(value));
    }
  }
  addField(trailingFields, "Source", requirement.sourceName === "" ? [] : [requirement.sourceName]);
  const sourceDisclosure =
    sourceText !== "" && sourceText !== requirement.summary
      ? `<details class="requirement-body-detail">${disclosureSummary("View original source")}<div class="source-snippet"><div class="source-snippet-header"><span>${icon("file")}<strong>Original source</strong></span><small title="${escapeHtml(requirementSourceName(requirement))}">${escapeHtml(requirementSourceName(requirement))}</small></div><pre><code>${escapeHtml(sourceText)}</code></pre></div></details>`
      : "";
  const preserveSourceFlowTitles = adapterId === "gherkin";
  const mainFlows = requirement.flows.flatMap((flow) =>
    flow.branches
      .filter((branch) => branch.kind === "main")
      .map((branch) => authoredFlowDetail(requirement, flow, branch, preserveSourceFlowTitles)),
  );
  const alternativeFlows = requirement.flows.flatMap((flow) =>
    flow.branches
      .filter((branch) => branch.kind === "alternative")
      .map((branch) => authoredFlowDetail(requirement, flow, branch, false)),
  );
  const exceptionFlows = requirement.flows.flatMap((flow) =>
    flow.branches
      .filter((branch) => branch.kind === "exception")
      .map((branch) => authoredFlowDetail(requirement, flow, branch, false)),
  );
  const sourceFlowFields =
    adapterId === "gherkin"
      ? [requirementFlowField("Scenarios", mainFlows)]
      : adapterId === "user-story"
        ? [
            requirementFlowField("Acceptance criteria", [
              ...mainFlows,
              ...alternativeFlows,
              ...exceptionFlows,
            ]),
          ]
        : [
            requirementFlowField(useCaseFormat ? "Main success scenario" : "Main flow", mainFlows),
            requirementFieldList(
              postconditions.length === 0 ? [] : [["Postconditions", postconditions]],
            ),
            requirementFlowField("Alternative flows", alternativeFlows),
            requirementFlowField("Exception flows", exceptionFlows),
          ];
  const specificationTitle = useCaseFormat
    ? "Use case specification"
    : adapterId === "gherkin"
      ? "Gherkin specification"
      : adapterId === "user-story"
        ? "User story"
        : "Requirement specification";
  const specificationDescription =
    adapterId === "gherkin"
      ? "Feature scenarios shown with their source-format terminology."
      : adapterId === "user-story"
        ? "The user story and its authored acceptance criteria."
        : "Authored content, organized in the same order as the source.";
  const content = [
    requirementFieldList(leadFields),
    ...sourceFlowFields,
    requirementFieldList(trailingFields),
    sourceDisclosure,
  ].join("");
  if (content === "") return "";
  return `<section class="requirement-result-section requirement-overview requirement-specification" aria-labelledby="requirement-specification-title"><div class="section-heading"><div><h3 id="requirement-specification-title">${specificationTitle}</h3><p>${specificationDescription}</p></div></div>${content}</section>`;
}

function requirementHeadingContext(adapterId: string, requirement: RequirementItem): string {
  const type = isUseCaseRequirement(adapterId, requirement)
    ? "Use case"
    : adapterId === "user-story"
      ? "User story"
      : adapterId === "gherkin"
        ? "Gherkin requirement"
        : "Requirement";
  return `${type} ${requirement.id}`;
}

function isUseCaseRequirement(adapterId: string, requirement: RequirementItem): boolean {
  const normalizedAdapterId = adapterId.trim().toLocaleLowerCase().replaceAll("_", "-");
  if (normalizedAdapterId !== "") return normalizedAdapterId.includes("use-case");
  const metadata = requirement.metadata ?? {};
  return ["stakeholders", "technology_and_data_variations", "related_information"].some((key) =>
    Object.hasOwn(metadata, key),
  );
}

function requirementFieldList(fields: Array<[string, string[]]>): string {
  if (fields.length === 0) return "";
  return `<dl>${fields.map(([label, values]) => `<div><dt>${escapeHtml(label)}</dt><dd>${values.length === 1 ? escapeHtml(values[0] ?? "") : `<ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul>`}</dd></div>`).join("")}</dl>`;
}

function requirementFlowField(label: string, flows: string[]): string {
  if (flows.length === 0) return "";
  return `<dl class="requirement-flow-fields"><div><dt>${escapeHtml(label)}</dt><dd><div class="flow-stack">${flows.join("")}</div></dd></div></dl>`;
}

function firstAvailableValues(primary: string[], fallback: string[]): string[] {
  return primary.length > 0 ? primary : fallback;
}

function requirementSourceText(requirement: RequirementItem, sources: RawSource[]): string {
  if (requirement.body?.trim()) return requirement.body.trim();
  return (
    sources.find((source) => source.name === requirementSourceName(requirement))?.text.trim() ?? ""
  );
}

function requirementSourceName(requirement: RequirementItem): string {
  const metadataSourceName = requirement.metadata?.source_name;
  if (typeof metadataSourceName === "string" && metadataSourceName.trim() !== "") {
    return metadataSourceName.trim();
  }
  return requirement.sourceName || "Requirement source";
}

function markdownSectionValues(sourceText: string, heading: string): string[] {
  if (sourceText === "") return [];
  const normalizedHeading = heading.toLocaleLowerCase();
  const lines = sourceText.split(/\r?\n/);
  const start = lines.findIndex(
    (line) => markdownHeadingText(line).toLocaleLowerCase() === normalizedHeading,
  );
  if (start < 0) return [];
  const values: string[] = [];
  for (const line of lines.slice(start + 1)) {
    if (markdownHeadingText(line) !== "") break;
    const value = line
      .trim()
      .replace(/^[-*+]\s+/, "")
      .replace(/^\d+[.)]\s+/, "")
      .trim();
    if (value !== "" && value !== "---") values.push(value);
  }
  return values;
}

function markdownHeadingText(line: string): string {
  const trimmed = line.trim();
  const hashHeading = /^#{1,6}\s+(.+?)\s*$/.exec(trimmed);
  if (hashHeading?.[1]) return hashHeading[1].replace(/[*_]+/g, "").trim();
  const boldHeading = /^\*\*(.+?)\*\*$/.exec(trimmed);
  return boldHeading?.[1]?.trim() ?? "";
}

function authoredFlowDetail(
  requirement: RequirementItem,
  flow: RequirementItem["flows"][number],
  branch: RequirementBranch,
  preserveSourceTitle: boolean,
): string {
  const branchElements = flow.nodes
    .filter((node) => node.branchId === branch.id)
    .map((node) => requirement.elements.find((element) => element.id === node.elementId))
    .filter((element): element is RequirementItem["elements"][number] => element !== undefined);
  const firstAlternative = branchElements.find((element) => element.kind === "alternative_step");
  const genericAlternativeTitle = /^Alternative(?:\s+flow)?\s+[\w.-]+$/i.test(branch.title.trim());
  const title = preserveSourceTitle
    ? branch.title
    : branch.kind === "main"
      ? "Flow elements"
      : genericAlternativeTitle && firstAlternative !== undefined
        ? `${branchSourceLabel(branch)}. ${firstAlternative.text}`
        : branch.title.replace(/^(?:Alternative|Exception)(?:\s+flow)?\s+/i, "");
  const elements = branchElements.filter((element) => {
    if (preserveSourceTitle) return true;
    if (branch.kind === "main") return element.kind === "main_step";
    if (genericAlternativeTitle && element.id === firstAlternative?.id) return false;
    return element.kind === "alternative_step" || element.kind === "alternative_postcondition";
  });
  return `<details class="flow-detail" name="requirement-flow-detail"><summary><span class="flow-title"><span class="branch-dot ${branch.kind}"></span>${escapeHtml(title)}</span><span class="flow-summary-meta"><small>${countLabel(elements.length, branch.kind === "main" ? "step" : "item")}</small><span class="disclosure-chevron" aria-hidden="true">${icon("expand")}</span></span></summary>${elements.length === 0 ? `<p class="section-empty branch-empty">No authored flow elements are available.</p>` : `<ol class="element-sequence">${elements.map((element, index) => `<li><span class="path-step-index" aria-hidden="true">${index + 1}</span><div><span class="element-kind">${escapeHtml(element.kind === "alternative_postcondition" ? "Postcondition" : "Step")}</span><p>${escapeHtml(element.text)}</p></div></li>`).join("")}</ol>`}</details>`;
}

function branchSourceLabel(branch: RequirementBranch): string {
  const value = branch.metadata?.branch_label;
  if (typeof value === "string" && value.trim() !== "") return value.trim();
  return branch.title.replace(/^(?:Alternative|Exception)(?:\s+flow)?\s+/i, "").trim();
}

function resultPathWorkspace(
  requirement: RequirementItem,
  result: AnalysisResult,
  state: AppState,
): string {
  const models = state.stateModels?.models ?? [];
  const modelControl = resultModelControl(models, selectedModel(state)?.id ?? "");
  const paths = [...pathsForRequirement(result, requirement.id)].sort(
    (left, right) =>
      pathPriorityIndex(left, requirement) - pathPriorityIndex(right, requirement) ||
      left.orderIndex - right.orderIndex,
  );
  if (paths.length === 0) {
    return `<div class="path-workspace-switcher"><div class="path-workspace-controls"><label for="result-path-select"><span>Requirement path</span><span class="select-control"><select id="result-path-select" disabled><option>No requirement paths</option></select>${icon("expand", "select-chevron")}</span></label>${modelControl}</div></div><section id="path-workspace-panel" class="path-workspace-detail" data-scroll-key="result-path-details" role="tabpanel" aria-labelledby="path-workspace-tab-paths"><div class="path-workspace-empty">${emptyState("No requirement paths", "No complete paths could be derived from the authored flows.")}</div></section>`;
  }
  const selectedPath =
    state.selectedResultScopeKind === "path"
      ? paths.find((path) => path.id === state.selectedResultScopeId)
      : undefined;
  const allPathsSelected = selectedPath === undefined;
  return `<div class="path-workspace-switcher"><div class="path-workspace-controls"><label for="result-path-select"><span>Requirement path</span><span class="select-control"><select id="result-path-select" data-requirement-id="${escapeHtml(requirement.id)}"><option value="" ${allPathsSelected ? "selected" : ""}>All requirement paths (${paths.length.toLocaleString()})</option>${paths.map((path) => `<option value="${escapeHtml(path.id)}" ${path.id === selectedPath?.id ? "selected" : ""}>${escapeHtml(pathDisplayLabel(path, requirement))}</option>`).join("")}</select>${icon("expand", "select-chevron")}</span></label>${modelControl}</div></div><section id="path-workspace-panel" class="path-workspace-detail" data-scroll-key="result-path-details" role="tabpanel" aria-labelledby="path-workspace-tab-paths">${renderResultPathPanel(requirement, result, state)}</section>`;
}

export function renderResultPathPanel(
  requirement: RequirementItem,
  result: AnalysisResult,
  state: AppState,
): string {
  const selectedPath =
    state.selectedResultScopeKind === "path"
      ? pathsForRequirement(result, requirement.id).find(
          (path) => path.id === state.selectedResultScopeId,
        )
      : undefined;
  return selectedPath === undefined
    ? `<div class="path-workspace-prompt"><strong>All requirement paths are highlighted</strong><p>Choose a requirement path to compare all of its required elements with the evidence found in the state model.</p></div>`
    : resultSelectedPath(requirement, selectedPath, result, state);
}

function pathWorkspaceTabs(state: AppState): string {
  const pathsSelected = state.resultWorkspaceTab === "paths";
  return `<div class="path-workspace-tabs" role="tablist" aria-label="Evidence workspace view"><button id="path-workspace-tab-paths" type="button" role="tab" data-action="set-result-workspace-tab" data-workspace-tab="paths" aria-controls="path-workspace-panel" aria-selected="${pathsSelected}" tabindex="${pathsSelected ? "0" : "-1"}" class="${pathsSelected ? "selected" : ""}">Path steps</button><button id="path-workspace-tab-graph" type="button" role="tab" data-action="set-result-workspace-tab" data-workspace-tab="graph" aria-controls="graph-workspace-panel" aria-selected="${!pathsSelected}" tabindex="${pathsSelected ? "-1" : "0"}" class="${pathsSelected ? "" : "selected"}">State model</button></div>`;
}

function resultSelectedPath(
  requirement: RequirementItem,
  path: RequirementPath,
  result: AnalysisResult,
  state: AppState,
): string {
  const occurrence = pathOccurrence(path, result, state);
  const found = new Set(occurrence?.coveredElementIds ?? []);
  const inspectedModel = selectedModel(state);
  const assessment = collectionAssessment(result, "path", path.id);
  let stepIndex = 0;
  const steps = path.elementIds
    .map((elementId) => requirement.elements.find((item) => item.id === elementId))
    .filter((element): element is RequirementItem["elements"][number] => element !== undefined);
  return `<div class="selected-path"><div class="selected-path-heading"><div><h3>${escapeHtml(pathDisplayLabel(path, requirement))}</h3><small>${countLabel(steps.length, "element")} · ${escapeHtml(humanizeToken(path.outcome))} outcome</small>${inspectedModel === null ? "" : modelPathEvidence(occurrence, inspectedModel)}</div>${completenessBadge(assessment)}</div><div class="path-evidence-key" aria-label="Element evidence status in the selected state model"><span>${icon("matched")}Found in this model</span><span>${icon("missing")}Not found in this model</span></div><p class="selected-path-guidance">Select an element to focus its evidence in the graph.</p><ol class="element-sequence requirement-path-steps">${steps
    .map((element) => {
      const numbered = isNumberedStep(element.kind);
      const sequenceStatus = found.has(element.id) ? "found" : "missing";
      const tone = requirementElementTone(result, requirement, element.id);
      const toneClass = tone < 0 ? "path-tone-neutral" : `path-tone-${tone}`;
      if (numbered) stepIndex += 1;
      const selected = state.selectedElementId === element.id;
      const statusLabel =
        sequenceStatus === "found"
          ? "Found in the selected state model"
          : "Not found in the selected state model";
      const status = `<span class="sequence-status ${sequenceStatus}" role="img" aria-label="${statusLabel}" title="${statusLabel}">${icon(sequenceStatus === "found" ? "matched" : "missing")}</span>`;
      const toneStyle = tone < 0 ? "" : ` style="${pathToneVariables(tone)}"`;
      return `<li class="${toneClass} ${selected ? "selected" : ""}"${toneStyle}><button type="button" class="path-step-content" data-action="select-path-step" data-element-id="${escapeHtml(element.id)}" aria-pressed="${selected}"><span class="path-step-marker ${numbered ? "numbered" : "contextual"}" aria-hidden="true">${numbered ? stepIndex : ""}</span><span class="path-step-copy ${numbered ? "numbered" : ""}">${numbered ? "" : `<span class="element-kind">${escapeHtml(pathElementKindLabel(element.kind))}</span>`}<p>${escapeHtml(element.text)}</p></span>${status}</button></li>`;
    })
    .join("")}</ol></div>`;
}

function pathOccurrence(
  path: RequirementPath,
  result: AnalysisResult,
  state: AppState,
): TraceOccurrence | undefined {
  const selectedModelId = state.selectedStateModelId || state.stateModels?.models[0]?.id || "";
  return preferredCompletenessOccurrence(
    result.occurrences.filter(
      (occurrence) => occurrence.pathId === path.id && occurrence.stateModelId === selectedModelId,
    ),
  );
}

function preferredCompletenessOccurrence(
  occurrences: TraceOccurrence[],
): TraceOccurrence | undefined {
  return [...occurrences].sort(
    (left, right) =>
      Number(right.status === "full") - Number(left.status === "full") ||
      right.coveredElementIds.length - left.coveredElementIds.length ||
      (right.score ?? -1) - (left.score ?? -1) ||
      left.id.localeCompare(right.id),
  )[0];
}

function modelPathEvidence(occurrence: TraceOccurrence | undefined, model: StateModel): string {
  const modelName = stateModelPickerLabel(model);
  if (occurrence === undefined) {
    return `<span class="model-evidence-summary missing">${icon("missing")}Not found in ${escapeHtml(modelName)}</span>`;
  }
  if (occurrence.status === "full") {
    return `<span class="model-evidence-summary complete">${icon("matched")}Complete in ${escapeHtml(modelName)}</span>`;
  }
  return `<span class="model-evidence-summary partial">${icon("unmatched")}Partial in ${escapeHtml(modelName)}</span>`;
}

function isNumberedStep(kind: string): boolean {
  return kind === "main_step" || kind === "alternative_step";
}

function pathElementKindLabel(kind: string): string {
  if (isNumberedStep(kind)) return "Step";
  if (kind === "alternative_postcondition") return "Postcondition";
  return humanizeToken(kind);
}

function pathDisplayLabel(path: RequirementPath, requirement?: RequirementItem): string {
  if (requirement === undefined) return path.title;
  const kind = pathBranchKind(path, requirement);
  if (kind === "main") return "Main path";
  const branchLabels = requirement.flows.flatMap((flow) =>
    flow.branches
      .filter((branch) => branch.kind === kind && path.branchIds.includes(branch.id))
      .map(branchSourceLabel),
  );
  const prefix = kind === "exception" ? "Exception path" : "Alternative path";
  return branchLabels.length === 0 ? prefix : `${prefix} ${branchLabels.join(" + ")}`;
}

function metadataValues(value: JsonValue | undefined): string[] {
  if (value === undefined || value === null) return [];
  if (Array.isArray(value)) return value.flatMap(metadataValues);
  if (typeof value === "object") {
    return Object.entries(value).flatMap(([key, item]) =>
      metadataValues(item).map((text) => `${humanizeToken(key)}: ${text}`),
    );
  }
  return [String(value)];
}

export function resultMetrics(result: AnalysisResult, stateModelCount = 0): string {
  const summary = result.summary;
  const requirementCoverage = summary.overallCoverageRatio;
  const completenessValue =
    summary.totalRequirements === 0
      ? "No requirements"
      : summary.notAssessableRequirements === summary.totalRequirements
        ? "Not assessable"
        : `${summary.completeRequirements} of ${summary.totalRequirements} complete`;
  const completenessDetail =
    summary.totalRequirements === 0
      ? "No requirements were available to assess"
      : summary.notAssessableRequirements > 0
        ? `${summary.incompleteRequirements} incomplete · ${summary.notAssessableRequirements} not assessable`
        : summary.incompleteRequirements === 0
          ? "All requirements are complete"
          : countLabel(summary.incompleteRequirements, "incomplete requirement");
  const completenessScope =
    stateModelCount > 1 && summary.totalRequirements > 0
      ? ` across ${countLabel(stateModelCount, "state model")}`
      : "";
  const pathCompletenessValue =
    summary.totalPaths === 0
      ? "No paths"
      : summary.notAssessablePaths === summary.totalPaths
        ? "Not assessable"
        : `${summary.completePaths} of ${summary.totalPaths} complete`;
  const pathCompletenessDetail =
    summary.totalPaths === 0
      ? "No requirement paths were available to assess."
      : summary.notAssessablePaths > 0
        ? `${summary.incompletePaths} incomplete · ${summary.notAssessablePaths} not assessable`
        : summary.incompletePaths === 0
          ? "All requirement paths are complete."
          : `${countLabel(summary.incompletePaths, "incomplete path")}.`;
  return `<section class="result-dashboard" aria-label="Analysis summary">
    <article class="summary-card headline-summary"><span>Requirements complete</span><strong>${completenessValue}</strong><small>${completenessDetail}${completenessScope}.</small></article>
    <article class="summary-card"><span>Paths complete</span><strong>${pathCompletenessValue}</strong><small>${pathCompletenessDetail}</small></article>
    <article class="summary-card evidence-summary"><span>Evidence coverage</span><strong>${percent(requirementCoverage)}</strong>${requirementCoverage === null ? "" : `<progress class="${requirementCoverage === 1 ? "complete" : ""}" max="100" value="${Math.round(requirementCoverage * 100)}" aria-label="Evidence coverage: ${percent(requirementCoverage)}"></progress>`}<small>Share of required elements supported by trace evidence</small></article>
  </section>`;
}

function collectionAssessment(
  result: AnalysisResult,
  scopeKind: CoverageAssessment["scopeKind"],
  scopeId: string,
): CoverageAssessment | null {
  return (
    result.assessments.find(
      (item) =>
        item.scopeKind === scopeKind &&
        item.scopeId === scopeId &&
        item.viewKind === "state-model-collection",
    ) ?? null
  );
}

export function completenessBadge(assessment: CoverageAssessment | null): string {
  if (assessment === null) {
    return `<span class="completeness-chip unavailable">${icon("unavailable")}${completenessBadgeLabel(assessment)}</span>`;
  }
  const status = assessment.completeness;
  return `<span class="completeness-chip ${status}">${completenessStatusIcon(status)}${completenessBadgeLabel(assessment)}</span>`;
}

export function completenessBadgeLabel(assessment: CoverageAssessment | null): string {
  return assessment === null ? "Not available" : completenessLabel(assessment.completeness);
}

function resultRequirementRow(
  id: string,
  result: AnalysisResult,
  state: AppState,
  selectedId: string,
): string {
  const assessment = result.assessments.find(
    (item) =>
      item.scopeKind === "requirement" &&
      item.scopeId === id &&
      item.viewKind === "state-model-collection",
  );
  const requirement = state.requirements?.requirements.find((item) => item.id === id);
  const pathCount = pathsForRequirement(result, id).length;
  const selected = id === selectedId;
  return `<button type="button" class="coverage-row ${selected ? "selected" : ""}" data-action="select-requirement" data-requirement-id="${escapeHtml(id)}"${selected ? ' aria-current="true"' : ""}><span><strong>${escapeHtml(id)}${requirement === undefined ? "" : ` · ${escapeHtml(requirement.title)}`}</strong><span class="requirement-row-meta"><small>${countLabel(pathCount, "path")}</small>${completenessBadge(assessment ?? null)}</span></span></button>`;
}

function resultRequirementToolbar(
  state: AppState,
  requirementCount: number,
  assessmentPending = false,
): string {
  if (requirementCount <= 1) return "";
  return `<search class="result-requirement-toolbar" aria-label="${assessmentPending ? "Search requirements" : "Search and filter requirements"}"><label class="search-field ${state.resultRequirementQuery.trim() === "" ? "" : "active-filter"}"><span class="visually-hidden">Search requirements</span>${icon("search")}<input id="result-requirement-search" type="search" placeholder="Search requirements…" value="${escapeHtml(state.resultRequirementQuery)}"></label>${assessmentPending ? "" : `<label><span class="visually-hidden">Filter by completeness</span><span class="select-control ${state.resultRequirementFilter === "all" ? "" : "active-filter"}"><select id="result-requirement-filter"><option value="all" ${state.resultRequirementFilter === "all" ? "selected" : ""}>All results</option><option value="complete" ${state.resultRequirementFilter === "complete" ? "selected" : ""}>Complete</option><option value="incomplete" ${state.resultRequirementFilter === "incomplete" ? "selected" : ""}>Incomplete</option><option value="not-assessable" ${state.resultRequirementFilter === "not-assessable" ? "selected" : ""}>Not assessable</option></select>${icon("expand", "select-chevron")}</span></label>`}</search>`;
}

function resultRequirementCount(state: AppState, visible: number, total: number): string {
  const filtered =
    state.resultRequirementFilter !== "all" || state.resultRequirementQuery.trim() !== "";
  const text = filtered ? `${visible} of ${total}` : String(total);
  const label = filtered
    ? `${visible} of ${countLabel(total, "requirement")}`
    : countLabel(total, "requirement");
  return `<small aria-label="${escapeHtml(label)}">${escapeHtml(text)}</small>`;
}

function scopeSelector(
  result: AnalysisResult,
  requirementId: string,
  selectedScopeId: string,
): string {
  const paths = pathsForRequirement(result, requirementId);
  return `<div class="scope-header"><div><p class="heading-context">Completeness scope</p><h2>${escapeHtml(requirementId)}</h2></div><span>${countLabel(paths.length, "path")}</span></div>
    <div class="scope-tabs" role="group" aria-label="Completeness scope">
      <button type="button" class="${selectedScopeId === requirementId ? "selected" : ""}" data-action="select-path" data-scope-kind="requirement" data-scope-id="${escapeHtml(requirementId)}" aria-pressed="${selectedScopeId === requirementId}"><strong>Entire requirement</strong><small>All flows and branches</small></button>
      ${paths.map((path) => pathTab(path, selectedScopeId)).join("")}
    </div>`;
}

function pathTab(path: RequirementPath, selectedId: string): string {
  const selected = path.id === selectedId;
  return `<button type="button" class="${selected ? "selected" : ""}" data-action="select-path" data-scope-kind="path" data-scope-id="${escapeHtml(path.id)}" aria-pressed="${selected}"><strong>Path ${path.orderIndex + 1}</strong><small>${escapeHtml(humanizeToken(path.outcome))} · ${countLabel(path.elementIds.length, "element")}</small></button>`;
}

function assessmentPanel(
  assessment: CoverageAssessment | null,
  state: AppState,
  scopedElements: Set<string> | null,
): string {
  if (assessment === null)
    return emptyState("No assessment", "Results are not available for this scope.");
  const requirement = state.requirements?.requirements.find(
    (item) => item.id === assessment.requirementIds[0],
  );
  const elements =
    requirement?.elements.filter(
      (item) => scopedElements === null || scopedElements.has(item.id),
    ) ?? [];
  const covered = new Set(assessment.coveredElementIds);
  return `<div class="assessment-summary"><div><span class="completeness-chip ${assessment.completeness}">${completenessStatusIcon(assessment.completeness)}${completenessLabel(assessment.completeness)}</span><h3>Completeness assessment</h3><p>${escapeHtml(assessment.rationale)}</p></div></div>
    <div class="element-coverage"><h3>Traceable elements</h3>${elements.length === 0 ? `<p class="subtle">Load the matching requirement sources to inspect individual elements.</p>` : `<ol>${elements.map((element) => `<li class="${covered.has(element.id) ? "covered" : "missing"}"><span class="element-status ${covered.has(element.id) ? "covered" : "missing"}" role="img" aria-label="${covered.has(element.id) ? "Covered" : "Missing"}">${icon(covered.has(element.id) ? "matched" : "missing")}</span><div><strong>${escapeHtml(humanizeToken(element.kind))}</strong><p>${escapeHtml(element.text)}</p></div></li>`).join("")}</ol>`}</div>`;
}

function resultAssessmentDetails(assessment: CoverageAssessment | null): string {
  if (assessment === null || assessment.rationale.trim() === "") return "";
  const label =
    assessment.completeness === "not-assessable"
      ? "Why not assessable?"
      : "How completeness was assessed";
  return `<details class="assessment-details">${disclosureSummary(label)}<p>${escapeHtml(assessment.rationale)}</p></details>`;
}

function resultAdditionalElements(
  requirement: RequirementItem,
  assessment: CoverageAssessment | null,
  scopedElements: Set<string> | null,
): string {
  if (assessment === null) return "";
  const elements = requirement.elements.filter(
    (item) => scopedElements === null || scopedElements.has(item.id),
  );
  const authoredElementIds = new Set(
    requirement.flows.flatMap((flow) => flow.nodes.map((node) => node.elementId)),
  );
  const additionalElements =
    authoredElementIds.size === 0
      ? elements.filter((element) => element.kind !== "constraint")
      : elements.filter(
          (element) => !authoredElementIds.has(element.id) && element.kind !== "constraint",
        );
  if (additionalElements.length === 0) return "";
  return `<section class="requirement-result-section element-coverage"><div class="section-heading"><div><h3>${authoredElementIds.size === 0 ? "Requirement elements" : "Other requirement elements"}</h3><p>Conditions and other traceable content outside the authored flows.</p></div></div><ol>${additionalElements
    .map((element) => {
      return `<li><div><strong>${escapeHtml(humanizeToken(element.kind))}</strong><p>${escapeHtml(element.text)}</p></div></li>`;
    })
    .join("")}</ol></section>`;
}

function graphCanvas(model: StateModel, ariaLabel: string, className: string): string {
  return `<div class="graph-canvas-shell ${className}"><div class="graph-toolbar" role="toolbar" aria-label="State-model graph controls"><button type="button" class="icon-action" data-action="graph-zoom-out" aria-label="Zoom out" title="Zoom out">${icon("zoomOut")}</button><button type="button" class="icon-action" data-action="graph-zoom-in" aria-label="Zoom in" title="Zoom in">${icon("zoomIn")}</button><button type="button" class="icon-action" data-action="graph-fit" aria-label="Fit state model to view" title="Fit model to view">${icon("fit")}</button></div><div id="state-model-graph" class="evidence-graph result-evidence-graph" role="img" aria-label="${escapeHtml(ariaLabel)}" data-model-id="${escapeHtml(model.id)}"></div></div>`;
}

function stateModelTable(model: StateModel): string {
  const nodes = new Map(model.graph.nodes.map((node) => [node.id, node]));
  const outgoing = new Map<string, StateModel["graph"]["edges"]>();
  for (const edge of model.graph.edges) {
    const edges = outgoing.get(edge.source) ?? [];
    edges.push(edge);
    outgoing.set(edge.source, edges);
  }
  const rows = model.graph.nodes.flatMap((node) => {
    const edges = outgoing.get(node.id) ?? [];
    if (edges.length === 0) {
      return `<tr><th scope="row">${stateNodeLabel(node)}${node.initial ? ` <span class="table-state-marker">Initial</span>` : ""}</th><td><span class="subtle">No outgoing transition</span></td><td>—</td></tr>`;
    }
    return edges.map((edge) => {
      const target = nodes.get(edge.target);
      const action = edge.label.trim() || edge.actionId || "Unlabelled transition";
      return `<tr><th scope="row">${stateNodeLabel(node)}${node.initial ? ` <span class="table-state-marker">Initial</span>` : ""}</th><td>${escapeHtml(action)}</td><td>${target === undefined ? escapeHtml(edge.target) : stateNodeLabel(target)}</td></tr>`;
    });
  });
  return `<details class="graph-data-view"><summary><span>${icon("table")}View model as table</span><small>${countLabel(model.graph.nodes.length, "state")} · ${countLabel(model.graph.edges.length, "transition")}</small><span class="disclosure-chevron" aria-hidden="true">${icon("expand")}</span></summary><div class="graph-data-scroll"><table><caption class="visually-hidden">States and transitions in ${escapeHtml(model.title)}</caption><thead><tr><th scope="col">From state</th><th scope="col">Action</th><th scope="col">To state</th></tr></thead><tbody>${rows.join("")}</tbody></table></div></details>`;
}

function stateNodeLabel(node: StateModel["graph"]["nodes"][number]): string {
  return escapeHtml(stateNodeDisplayName(node) || node.shortId || node.id);
}

function resultGraphPanel(
  state: AppState,
  requirement: RequirementItem | undefined,
  model: StateModel | null,
  occurrences: TraceOccurrence[],
  scopeKind: string,
  result: AnalysisResult,
): string {
  if (model === null)
    return `<div class="graph-heading"><h2 id="result-state-model-title">State model</h2></div>${emptyState("State model unavailable", "Load the state-model sources used by this result to restore the evidence view.")}`;
  const models = state.stateModels?.models ?? [];
  const stepSelected = scopeKind === "element" && state.selectedElementId !== "";
  const evidenceNotice =
    occurrences.length > 0
      ? ""
      : stepSelected
        ? "No evidence for the selected element in this model."
        : `No ordered path evidence${requirement === undefined ? "" : ` for ${requirement.id}`} in this model.`;
  const unavailableNavigation = `<div class="path-workspace-switcher"><div class="path-workspace-controls"><div><strong>Requirement path</strong><small>Requirements unavailable</small></div>${resultModelControl(models, model.id)}</div></div><section id="path-workspace-panel" class="path-workspace-detail" data-scroll-key="result-path-details" role="tabpanel" aria-labelledby="path-workspace-tab-paths"><div class="path-workspace-prompt"><strong>Requirements unavailable</strong><p>Restore the requirement snapshot to inspect requirement paths.</p></div></section>`;
  return `<div class="graph-heading"><h2 id="result-state-model-title">State model</h2></div>
    <section class="state-model-evidence" aria-labelledby="result-state-model-title">
    <div class="path-evidence-workspace workspace-view-${state.resultWorkspaceTab}">${pathWorkspaceTabs(state)}${requirement === undefined ? unavailableNavigation : resultPathWorkspace(requirement, result, state)}<section id="graph-workspace-panel" class="graph-workspace-stage" role="tabpanel" aria-labelledby="path-workspace-tab-graph">${evidenceNotice === "" ? "" : `<p class="graph-evidence-notice" role="status">${icon("notAssessable")}<span>${escapeHtml(evidenceNotice)}</span></p>`}${stateModelLegend(model, occurrences, result, requirement)}${graphCanvas(model, "State model with source-derived page and action labels, color-coded requirement paths, direct evidence, route connectors, and requirement-element markers", "result-graph-shell")}${stateModelTable(model)}</section></div></section>`;
}

function stateModelLegend(
  model: StateModel,
  occurrences: TraceOccurrence[],
  result: AnalysisResult | null,
  requirement: RequirementItem | undefined,
): string {
  const modelItems: string[] = [];
  const flowItems: string[] = [];
  const evidenceItems: string[] = [];
  if (model.graph.nodes.some((node) => node.initial)) {
    modelItems.push(
      `<span><i class="graph-legend-swatch initial" aria-hidden="true"></i>Initial state</span>`,
    );
  }
  if (result !== null) {
    const pathIds = new Set(occurrences.map((occurrence) => occurrence.pathId));
    const paths = result.paths
      .filter((path) => pathIds.has(path.id))
      .sort(
        (left, right) =>
          (requirement === undefined
            ? left.orderIndex - right.orderIndex
            : pathPriorityIndex(left, requirement) - pathPriorityIndex(right, requirement)) ||
          left.orderIndex - right.orderIndex,
      );
    for (const [index, path] of paths.entries()) {
      const tone =
        requirement === undefined ? index % PATH_TONE_COUNT : pathAccentIndex(path, requirement);
      flowItems.push(
        `<span><i class="graph-legend-swatch path-tone-${tone}" style="${pathToneVariables(tone)}" aria-hidden="true"></i>${escapeHtml(pathDisplayLabel(path, requirement))}</span>`,
      );
    }
    if (occurrences.length > 0) {
      evidenceItems.push(
        `<span><i class="graph-legend-line direct" aria-hidden="true"></i>Direct evidence</span>`,
        `<span><i class="graph-legend-line connector" aria-hidden="true"></i>Route connector</span>`,
      );
    }
  }
  const groups = [
    flowItems.length === 0
      ? ""
      : `<span class="graph-legend-group"><strong>Requirement paths</strong>${flowItems.join("")}</span>`,
    evidenceItems.length === 0
      ? ""
      : `<span class="graph-legend-group"><strong>Evidence</strong>${evidenceItems.join("")}</span>`,
    modelItems.length === 0
      ? ""
      : `<span class="graph-legend-group"><strong>Model</strong>${modelItems.join("")}</span>`,
  ].join("");
  return groups === ""
    ? ""
    : `<div class="graph-legend" aria-label="State model legend">${groups}</div>`;
}

function selectedModel(state: AppState): StateModel | null {
  const models = state.stateModels?.models ?? [];
  return models.find((item) => item.id === state.selectedStateModelId) ?? models[0] ?? null;
}

function modelPicker(models: StateModel[], selectedId: string): string {
  if (models.length <= 1) return "";
  return `<label class="model-picker"><span>State model</span><span class="select-control"><select id="state-model-select">${models.map((model) => `<option value="${escapeHtml(model.id)}" ${model.id === selectedId ? "selected" : ""}>${escapeHtml(stateModelPickerLabel(model))}</option>`).join("")}</select>${icon("expand", "select-chevron")}</span></label>`;
}

function resultModelPicker(models: StateModel[], selectedId: string): string {
  return `<label class="result-model-picker"><span>State model</span><span class="select-control"><select id="state-model-select" aria-describedby="result-model-context">${models.map((model) => `<option value="${escapeHtml(model.id)}" ${model.id === selectedId ? "selected" : ""}>${escapeHtml(stateModelPickerLabel(model))}</option>`).join("")}</select>${icon("expand", "select-chevron")}</span></label><small id="result-model-context" class="result-model-context">Graph shows this model; summary metrics include all ${models.length.toLocaleString()} state models.</small>`;
}

function resultModelControl(models: StateModel[], selectedId: string): string {
  if (models.length === 0) {
    return `<div class="result-model-static"><span>State model</span><small>Unavailable</small></div>`;
  }
  if (models.length > 1) return resultModelPicker(models, selectedId);
  const model = models[0];
  if (model === undefined) return "";
  const label = stateModelPickerLabel(model);
  return `<div class="result-model-static"><span>State model</span><strong title="${escapeHtml(label)}">${escapeHtml(label)}</strong></div>`;
}

function stateModelPickerLabel(model: StateModel): string {
  return model.sourceName ?? model.title;
}

function disclosureSummary(label: string): string {
  return `<summary><span>${escapeHtml(label)}</span><span class="disclosure-chevron" aria-hidden="true">${icon("expand")}</span></summary>`;
}

function supportedFormatsText(adapters: AdapterDescriptor[], sourceLabel: string): string {
  const labels = [...new Set(adapters.flatMap((adapter) => adapter.formats).map(formatLabel))];
  if (labels.length === 0) return `Add supported ${sourceLabel}.`;
  return `Add ${sentenceList(labels)} ${sourceLabel}.`;
}

function formatLabel(format: string): string {
  const normalized = format.trim().replace(/^\./, "").toLocaleLowerCase();
  const labels: Record<string, string> = {
    feature: "Gherkin",
    gherkin: "Gherkin",
    json: "JSON",
    md: "Markdown",
    markdown: "Markdown",
    yaml: "YAML",
    yml: "YAML",
  };
  return labels[normalized] ?? normalized.toLocaleUpperCase();
}

function sentenceList(values: string[]): string {
  if (values.length <= 1) return values[0] ?? "supported";
  if (values.length === 2) return `${values[0]} and ${values[1]}`;
  return `${values.slice(0, -1).join(", ")}, or ${values.at(-1)}`;
}

function requirementSourceHint(adapters: AdapterDescriptor[]): string {
  return adapters.length === 0 ? "Preparing file support…" : "No files selected";
}

function stateModelSourceHint(adapters: AdapterDescriptor[]): string {
  return adapters.length === 0 ? "Preparing file support…" : "No files selected";
}

function countLabel(count: number, singular: string, plural = `${singular}s`): string {
  return `${count.toLocaleString()} ${count === 1 ? singular : plural}`;
}

function feedbackText(feedback: AppState["requirementsFeedback"], fallback: string): string {
  const fallbackState = fallback.endsWith("…") ? "running" : undefined;
  return `${feedbackStateIcon(feedback?.state ?? fallbackState)}<span>${escapeHtml(feedback?.text ?? fallback)}</span>`;
}

function renderFeedback(feedback: AppState["analysisFeedback"], dismissAction: string): string {
  if (feedback === null) return "";
  const role = feedback.state === "error" ? "alert" : "status";
  const toast = feedback.presentation === "toast";
  const dismissButton = `<button type="button" class="${toast ? "icon-action feedback-dismiss-action" : "icon-button"}" aria-label="Dismiss notification" title="Dismiss" data-action="${dismissAction}">${icon("close")}</button>`;
  const toastAction =
    feedback.action === undefined
      ? ""
      : `<button type="button" class="tertiary compact-action feedback-toast-action" data-action="${feedback.action.action}" data-run-id="${escapeHtml(feedback.action.runId)}">${escapeHtml(feedback.action.label)}</button>`;
  const action =
    feedback.state === "running"
      ? `<button type="button" class="secondary compact-action feedback-cancel-action" data-action="cancel-export">${icon("cancel")}Cancel export</button>`
      : toast
        ? `<div class="feedback-toast-actions">${toastAction}${dismissButton}</div>`
        : dismissButton;
  return `<div class="feedback-row ${feedback.state}${toast ? " feedback-toast" : ""}"><p class="feedback ${feedback.state} inline-feedback" role="${role}" aria-atomic="true">${feedbackStateIcon(feedback.state)}<span>${escapeHtml(feedback.text)}</span></p>${action}</div>`;
}

function feedbackStateIcon(state: string | undefined): string {
  const iconName = feedbackIconName(state);
  return iconName === null
    ? ""
    : `<span class="feedback-state-icon" aria-hidden="true">${icon(iconName, state === "running" ? "spinning" : "")}</span>`;
}

export function feedbackIconName(state: string | undefined): AppIcon | null {
  if (state === "running") return "loading";
  if (state === "ready" || state === "complete") return "matched";
  if (state === "error" || state === "failed") return "error";
  if (state === "cancelled") return "cancelled";
  return null;
}

function detailHeader(label: string, title: string): string {
  return `<header class="page-header detail-header">${backLink("analyses", "Back to analyses")}<div class="detail-heading"><p class="heading-context">${escapeHtml(label)}</p><h1 id="page-title">${escapeHtml(title)}</h1></div></header>`;
}

function reviewHeader(title: string, description: string, sourceName: string): string {
  return `<header class="page-header detail-header review-header">${backLink("new-analysis", "Back to new analysis")}<div class="detail-heading"><h1 id="page-title">${escapeHtml(title)}</h1><p>${escapeHtml(description)}</p><p class="review-source-context">${icon("file")}<span>Source set</span><strong>${escapeHtml(sourceName)}</strong></p></div></header>`;
}

function backLink(view: "analyses" | "new-analysis", label: string): string {
  return `<a class="back-link" href="${routePath(view)}" data-route>${icon("back")}<span>${label}</span></a>`;
}

function emptyDetail(label: string, message: string): string {
  return `<section class="page" aria-labelledby="page-title">${detailHeader(label, message)}<div class="page-content">${emptyState(label, message)}</div></section>`;
}

function emptyState(title: string, message: string): string {
  return `<div class="empty-state"><strong>${escapeHtml(title)}</strong><p>${escapeHtml(message)}</p></div>`;
}

function metric(label: string, value: string | number): string {
  return `<div class="metric"><strong>${escapeHtml(String(value))}</strong><span>${escapeHtml(label)}</span></div>`;
}

function methodChip(methodName: string): string {
  return `<span class="method-chip" title="Traceability method: ${escapeHtml(methodName)}">${escapeHtml(methodName)}</span>`;
}

function methodDisplayName(run: AnalysisRun, state: AppState): string {
  return state.methods.find((method) => method.id === run.methodId)?.name ?? run.methodName;
}

function statusPill(status: string): string {
  const labels: Record<string, string> = {
    cancelled: "Cancelled",
    complete: "Finished",
    failed: "Failed",
    running: "Running",
  };
  const statusIcon = {
    cancelled: icon("cancelled"),
    complete: icon("matched"),
    failed: icon("error"),
    running: icon("loading", "spinning"),
  }[status];
  return `<span class="status-pill ${escapeHtml(status)}">${statusIcon ?? ""}${escapeHtml(labels[status] ?? status)}</span>`;
}

function percent(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function capitalize(value: string): string {
  return value.length === 0 ? value : `${value[0]?.toLocaleUpperCase()}${value.slice(1)}`;
}

function humanizeToken(value: string): string {
  return capitalize(value.replaceAll("_", " ").replaceAll("-", " "));
}

function completenessLabel(status: CoverageAssessment["completeness"]): string {
  return {
    complete: "Complete",
    incomplete: "Incomplete",
    "not-assessable": "Not assessable",
  }[status];
}

function completenessStatusIcon(status: string): string {
  if (status === "complete") return icon("matched");
  if (status === "incomplete") return icon("unmatched");
  if (status === "not-assessable") return icon("notAssessable");
  if (status === "pending") return icon("loading", "spinning");
  return "";
}

function renderCreatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return `<time>${escapeHtml(value)}</time>`;
  }
  return `<time datetime="${escapeHtml(value)}"><span>${escapeHtml(formatAnalysisDate(date))}</span><small>${escapeHtml(formatAnalysisTime(date))}</small></time>`;
}

function formatAnalysisDateTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : `${formatAnalysisDate(date)}, ${formatAnalysisTime(date)}`;
}

function formatAnalysisDate(date: Date): string {
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatAnalysisTime(date: Date): string {
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
