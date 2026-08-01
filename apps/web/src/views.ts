import type { AppState } from "./state";
import type {
  AnalysisResult,
  AnalysisRun,
  RequirementCoverage,
  RequirementItem,
  RequirementScenario,
  ScenarioCoverage,
  SequenceStep,
} from "./types";

export function renderWorkspace(state: AppState): string {
  const selected = selectedRun(state);
  return `
    <section class="workspace-grid" aria-label="ReqTrace workspace">
      <div class="panel history-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Analyses</p>
            <h2>Manage results</h2>
          </div>
          <div class="history-actions">
            <button type="button" class="secondary" data-action="import-result">Import</button>
            <button type="button" class="secondary" data-action="export-selected" ${selected?.result === null || selected === null ? "disabled" : ""}>Export</button>
            <button type="button" class="secondary" data-action="cancel-selected" ${selected?.status === "running" ? "" : "disabled"}>Cancel</button>
            <button type="button" class="ghost danger" data-action="delete-selected" ${selected === null ? "disabled" : ""}>Delete</button>
          </div>
        </div>
        ${renderRunsList(state)}
      </div>

      <div class="panel source-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Inputs</p>
            <h2>Sources</h2>
          </div>
        </div>
        ${renderRequirementSource(state)}
        ${renderEvidenceSource(state)}
        ${renderAnalysisLauncher(state)}
      </div>
    </section>
  `;
}

export function renderRequirementsDetail(state: AppState): string {
  const bundle = state.requirements;
  if (bundle === null) {
    return renderEmptyDetail(
      "No requirements loaded",
      "Load a requirements file or directory first.",
    );
  }
  const requirement = selectedRequirement(state);
  return `
    ${detailHeader("Requirements", bundle.name, "show-workspace")}
    <section class="detail-grid requirements-detail">
      <aside class="panel list-panel" aria-label="Requirement list">
        <div class="metric-strip">
          ${metric("Use cases", String(bundle.requirements.length))}
          ${metric("Scenarios", String(totalScenarios(bundle.requirements)))}
          ${metric("Fragments", String(totalFragments(bundle.requirements)))}
        </div>
        <div class="item-list">
          ${bundle.requirements.map((item) => renderRequirementListItem(item, requirement?.id)).join("")}
        </div>
      </aside>
      <section class="panel inspector-panel" aria-label="Requirement details">
        ${requirement === null ? emptyState("No requirement selected", "Choose a use case to inspect.") : renderRequirementInspector(requirement, state)}
      </section>
    </section>
  `;
}

export function renderEvidenceDetail(state: AppState): string {
  const evidence = state.evidence;
  if (evidence === null) {
    return renderEmptyDetail("No evidence loaded", "Load a TESTAR state model JSON file first.");
  }
  const rawSource = state.showFullEvidenceSource ? evidence.text : previewText(evidence.text);
  return `
    ${detailHeader("Evidence", evidence.name, "show-workspace")}
    <section class="evidence-stack">
      <div class="panel inspector-panel">
        <div class="metric-strip">
          ${Object.entries(evidence.stats)
            .filter(([label, value]) => value > 0 && (label !== "artifacts" || value > 1))
            .map(([label, value]) => metric(titleCase(label), String(value)))
            .join("")}
        </div>
        <div class="panel-header graph-section-header">
          <div>
            <p class="eyebrow">State model</p>
            <h2>Graph preview</h2>
          </div>
          <small>${evidence.graph.nodes.length} nodes, ${evidence.graph.edges.length} edges</small>
        </div>
        <div id="evidence-graph" class="evidence-graph" aria-label="Evidence state model graph"></div>
      </div>
      <div class="panel code-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Raw source</p>
            <h2>${escapeHtml(evidence.source.name)}</h2>
          </div>
          <button type="button" class="secondary" data-action="toggle-full-evidence-source">
            ${state.showFullEvidenceSource ? "Show preview" : "Show full source"}
          </button>
        </div>
        <pre>${escapeHtml(rawSource)}</pre>
      </div>
    </section>
  `;
}

export function renderResultDetail(state: AppState): string {
  const run = selectedRun(state);
  if (run === null) {
    return renderEmptyDetail(
      "No analysis selected",
      "Select an analysis from the workspace history.",
    );
  }
  if (run.result === null) {
    return `
      ${detailHeader("Analysis result", run.title, "show-workspace")}
      <section class="panel">
        ${renderRunState(run)}
      </section>
    `;
  }
  const coverage = selectedCoverage(state, run.result);
  const scenario = selectedScenario(state, coverage);
  return `
    ${detailHeader("Analysis result", run.result.title, "show-workspace")}
    <section class="result-dashboard">
      ${renderResultMetrics(run.result)}
    </section>
    <section class="detail-grid result-detail">
      <aside class="panel list-panel" aria-label="Use case coverage">
        <div class="item-list">
          ${run.result.coverage.map((item) => renderCoverageListItem(item, coverage?.requirementId)).join("")}
        </div>
      </aside>
      <section class="panel inspector-panel">
        ${coverage === null ? emptyState("No use case selected", "Choose a covered use case.") : renderCoverageInspector(coverage, scenario, state)}
      </section>
      <section class="panel graph-panel">
        ${scenario === null ? emptyState("No scenario selected", "Choose a scenario to preview the sequence.") : renderSequenceGraph(scenario, state)}
      </section>
    </section>
  `;
}

export function selectedRun(state: AppState): AnalysisRun | null {
  return state.runs.find((run) => run.id === state.selectedRunId) ?? state.runs[0] ?? null;
}

export function selectedRequirement(state: AppState): RequirementItem | null {
  const requirements = state.requirements?.requirements ?? [];
  return (
    requirements.find((item) => item.id === state.selectedRequirementId) ?? requirements[0] ?? null
  );
}

export function selectedCoverage(
  state: AppState,
  result: AnalysisResult,
): RequirementCoverage | null {
  return (
    result.coverage.find((item) => item.requirementId === state.selectedRequirementId) ??
    result.coverage[0] ??
    null
  );
}

export function selectedScenario(
  state: AppState,
  coverage: RequirementCoverage | null,
): ScenarioCoverage | null {
  const scenarios = coverage?.scenarios ?? [];
  return (
    scenarios.find((item) => item.scenarioId === state.selectedScenarioId) ?? scenarios[0] ?? null
  );
}

function renderRequirementSource(state: AppState): string {
  const bundle = state.requirements;
  return `
    <section class="source-block">
      <div>
        <h3>Requirements</h3>
        <p class="${state.requirementsFeedback?.state === "error" ? "source-status error" : "source-status"}">
          ${requirementStatusText(state)}
        </p>
      </div>
      <div class="source-actions">
        <button type="button" data-action="load-requirements-file">File</button>
        <button type="button" class="secondary" data-action="load-requirements-directory">Directory</button>
        <button type="button" class="secondary" data-action="inspect-requirements" ${bundle === null ? "disabled" : ""}>Inspect</button>
        <button type="button" class="ghost danger" data-action="clear-requirements" ${bundle === null ? "disabled" : ""}>Clear</button>
      </div>
    </section>
  `;
}

function renderEvidenceSource(state: AppState): string {
  const evidence = state.evidence;
  return `
    <section class="source-block">
      <div>
        <h3>Evidence</h3>
        <p class="${state.evidenceFeedback?.state === "error" ? "source-status error" : "source-status"}">
          ${evidenceStatusText(state)}
        </p>
      </div>
      <div class="source-actions">
        <button type="button" data-action="load-evidence-file">File</button>
        <button type="button" class="secondary" data-action="inspect-evidence" ${evidence === null ? "disabled" : ""}>Inspect</button>
        <button type="button" class="ghost danger" data-action="clear-evidence" ${evidence === null ? "disabled" : ""}>Clear</button>
      </div>
    </section>
  `;
}

function renderAnalysisLauncher(state: AppState): string {
  const ready = state.requirements !== null && state.evidence !== null && state.methods.length > 0;
  return `
    <section class="analysis-launcher">
      <h3>Analysis</h3>
      <label>
        Method
        <select id="method-select">
          ${state.methods.map((method) => `<option value="${escapeHtml(method)}" ${method === state.selectedMethod ? "selected" : ""}>${escapeHtml(methodLabel(method))}</option>`).join("")}
        </select>
      </label>
      <button type="button" data-action="start-analysis" ${ready ? "" : "disabled"}>Start analysis</button>
      ${renderFeedback(state.analysisFeedback, "dismiss-analysis-feedback")}
    </section>
  `;
}

function renderRunsList(state: AppState): string {
  if (state.runs.length === 0) {
    return emptyState("No saved analyses", "Completed and imported results appear here.");
  }
  return `
    <div class="run-list">
      ${state.runs
        .map(
          (run) => `
            <div class="run-row ${run.id === state.selectedRunId ? "selected" : ""}" data-action="select-run" data-run-id="${escapeHtml(run.id)}" role="button" tabindex="0">
              <span>
                <strong>${escapeHtml(run.title)}</strong>
                <small>${escapeHtml(run.method)} | ${formatDate(run.createdAt)}</small>
              </span>
              ${statusPill(run.status)}
              <div class="row-actions">
                <button type="button" data-action="view-run" data-run-id="${escapeHtml(run.id)}">View</button>
              </div>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderRunState(run: AnalysisRun): string {
  if (run.status === "running") {
    return `
      <div class="running-state">
        <div class="progress-bar"><span style="width: ${boundedPercent(run.progress)}%"></span></div>
        <p>${escapeHtml(run.message)}</p>
        <div class="skeleton-lines" aria-hidden="true"><span></span><span></span><span></span></div>
      </div>
    `;
  }
  if (run.status === "failed") {
    return `<p class="feedback error">${escapeHtml(run.message)}</p>`;
  }
  if (run.status === "cancelled") {
    return `<p class="feedback empty">Analysis cancelled.</p>`;
  }
  return `<p class="feedback complete">${escapeHtml(run.message || "Analysis complete.")}</p>`;
}

function renderResultMetrics(result: AnalysisResult): string {
  return `
    <div class="metric-strip dashboard-metrics">
      ${metric("Requirements", String(result.summary.requirementCount))}
      ${metric("Coverage", percent(result.summary.totalCoverage))}
      ${metric("Covered", String(result.summary.coveredRequirements))}
      ${metric("Partial", String(result.summary.partiallyCoveredRequirements))}
      ${metric("Uncovered", String(result.summary.uncoveredRequirements))}
    </div>
  `;
}

function renderFeedback(feedback: AppState["requirementsFeedback"], dismissAction: string): string {
  if (feedback === null) {
    return "";
  }
  return `
    <div class="feedback-row">
      <p class="feedback ${feedback.state}">${escapeHtml(feedback.text)}</p>
      <button type="button" class="icon-button" aria-label="Dismiss message" data-action="${dismissAction}">x</button>
    </div>
  `;
}

function renderRequirementListItem(item: RequirementItem, selectedId: string | undefined): string {
  return `
    <button type="button" class="item-row ${item.id === selectedId ? "selected" : ""}" data-action="select-requirement" data-requirement-id="${escapeHtml(item.id)}">
      <span>
        <strong>${escapeHtml(item.id)}: ${escapeHtml(item.title)}</strong>
        <small>${item.scenarios.length} scenarios, ${item.fragments.length} fragments</small>
      </span>
    </button>
  `;
}

function renderRequirementInspector(requirement: RequirementItem, state: AppState): string {
  return `
    <div class="inspector-heading">
      <div>
        <p class="eyebrow">${escapeHtml(requirement.id)}</p>
        <h2>${escapeHtml(requirement.title)}</h2>
      </div>
      <span class="subtle">${escapeHtml(requirement.actor || "No actor")}</span>
    </div>
    ${requirement.summary === "" ? "" : `<p class="summary-text">${escapeHtml(requirement.summary)}</p>`}
    <div class="scenario-stack">
      ${requirement.scenarios.map((scenario, index) => renderRequirementScenario(scenario, requirement, state, index)).join("")}
    </div>
  `;
}

function renderRequirementScenario(
  scenario: RequirementScenario,
  requirement: RequirementItem,
  state: AppState,
  index: number,
): string {
  const open =
    scenario.id === state.selectedScenarioId || (state.selectedScenarioId === "" && index === 0);
  const fragments = scenario.fragmentIds
    .map((id) => requirement.fragments.find((fragment) => fragment.id === id))
    .filter((fragment) => fragment !== undefined);
  return `
    <details class="scenario-detail" ${open ? "open" : ""}>
      <summary>
        <span class="scenario-title"><span class="disclosure" aria-hidden="true"></span>${index + 1}. ${escapeHtml(scenario.title)}</span>
        <small>${escapeHtml(scenario.kind)} | ${fragments.length} fragments</small>
      </summary>
      <ol class="fragment-path">
        ${fragments
          .map(
            (fragment) => `
              <li>
                <span class="fragment-kind">${escapeHtml(fragment.kind)}</span>
                <strong>${escapeHtml(fragment.id)}</strong>
                <p>${escapeHtml(fragment.text)}</p>
              </li>
            `,
          )
          .join("")}
      </ol>
    </details>
  `;
}

function renderCoverageListItem(item: RequirementCoverage, selectedId: string | undefined): string {
  return `
    <button type="button" class="coverage-row ${item.requirementId === selectedId ? "selected" : ""}" data-action="select-coverage" data-requirement-id="${escapeHtml(item.requirementId)}">
      <span>
        <strong>${escapeHtml(item.requirementId)}: ${escapeHtml(item.title)}</strong>
        <small>${item.scenarios.length} scenarios</small>
      </span>
      <span class="coverage-chip ${item.status}">${percent(item.coverageRatio)}</span>
    </button>
  `;
}

function renderCoverageInspector(
  coverage: RequirementCoverage,
  scenario: ScenarioCoverage | null,
  state: AppState,
): string {
  return `
    <div class="inspector-heading">
      <div>
        <p class="eyebrow">${escapeHtml(coverage.status)}</p>
        <h2>${escapeHtml(coverage.requirementId)}: ${escapeHtml(coverage.title)}</h2>
      </div>
      <span class="coverage-chip ${coverage.status}">${percent(coverage.coverageRatio)}</span>
    </div>
    <div class="scenario-tabs">
      ${coverage.scenarios
        .map(
          (item) => `
            <button type="button" class="${item.scenarioId === scenario?.scenarioId ? "selected" : ""}" data-action="select-scenario" data-scenario-id="${escapeHtml(item.scenarioId)}">
              ${escapeHtml(item.title)}
              <small>${percent(item.coverageRatio)}</small>
            </button>
          `,
        )
        .join("")}
    </div>
    ${scenario === null ? emptyState("No scenario selected", "Choose a scenario to inspect.") : renderScenarioSequence(scenario, state)}
  `;
}

function renderScenarioSequence(scenario: ScenarioCoverage, state: AppState): string {
  const contextSteps = scenario.sequence.filter(isContextStep);
  const pathSteps = scenario.sequence.filter(isPathStep);
  const outcomeSteps = scenario.sequence.filter(isOutcomeStep);
  const otherSteps = scenario.sequence.filter(
    (step) => !isContextStep(step) && !isPathStep(step) && !isOutcomeStep(step),
  );
  return `
    <div class="scenario-summary">
      <strong>${escapeHtml(scenario.title)}</strong>
      <span>${escapeHtml(scenario.status)} | ${scenario.matchedFragments}/${scenario.totalFragments} fragments</span>
    </div>
    ${renderSequenceGroup("Context", contextSteps, state)}
    ${renderSequenceGroup("Path", pathSteps, state, true)}
    ${renderSequenceGroup("Outcome", outcomeSteps, state)}
    ${renderSequenceGroup("Other", otherSteps, state)}
  `;
}

function renderSequenceGroup(
  title: string,
  steps: SequenceStep[],
  state: AppState,
  numbered = false,
): string {
  if (steps.length === 0) {
    return "";
  }
  return `
    <section class="sequence-group">
      <h3>${escapeHtml(title)}</h3>
      <ol class="sequence-list">
        ${steps.map((step, index) => renderSequenceStep(step, state, numbered ? index + 1 : null)).join("")}
      </ol>
    </section>
  `;
}

function renderSequenceStep(
  step: SequenceStep,
  state: AppState,
  displayIndex: number | null,
): string {
  return `
    <li class="${step.fragmentId === state.selectedStepId ? "selected" : ""}">
      <button type="button" data-action="select-step" data-step-id="${escapeHtml(step.fragmentId)}">
        <span class="${displayIndex === null ? "fragment-kind" : "step-index"}">${displayIndex === null ? escapeHtml(step.fragmentKind) : displayIndex}</span>
        <span>
          <strong>${displayIndex === null ? "" : `${escapeHtml(step.fragmentKind)}: `}${escapeHtml(step.fragmentText)}</strong>
          <small>${step.matched ? `${escapeHtml(step.evidenceKind)} ${escapeHtml(step.evidenceId)} | score ${step.score.toFixed(3)}` : "No matching evidence step"}</small>
        </span>
      </button>
    </li>
  `;
}

function isContextStep(step: SequenceStep): boolean {
  const kind = normalizedKind(step.fragmentKind);
  return kind.includes("constraint") || kind.includes("precondition") || kind.includes("trigger");
}

function isPathStep(step: SequenceStep): boolean {
  const kind = normalizedKind(step.fragmentKind);
  return kind.includes("step") && !kind.includes("postcondition");
}

function isOutcomeStep(step: SequenceStep): boolean {
  return normalizedKind(step.fragmentKind).includes("postcondition");
}

function renderSequenceGraph(scenario: ScenarioCoverage, state: AppState): string {
  if (state.evidence === null) {
    return `
      <div class="graph-heading">
        <div>
          <p class="eyebrow">Evidence path</p>
          <h2>${escapeHtml(scenario.title)}</h2>
        </div>
      </div>
      ${emptyState("Evidence graph unavailable", "Load the evidence source used for this analysis to inspect the path graph.")}
    `;
  }
  return `
    <div class="graph-heading">
      <div>
        <p class="eyebrow">Evidence path</p>
        <h2>${escapeHtml(scenario.title)}</h2>
      </div>
    </div>
    <div id="sequence-evidence-graph" class="evidence-graph sequence-evidence-graph" aria-label="Best evidence sequence graph"></div>
  `;
}

function renderEmptyDetail(title: string, message: string): string {
  return `
    ${detailHeader(title, message, "show-workspace")}
    <section class="panel">
      ${emptyState(title, message)}
    </section>
  `;
}

function detailHeader(label: string, title: string, backAction: string): string {
  return `
    <header class="detail-header">
      <div class="detail-title-row">
        <button type="button" class="back-button" data-action="${backAction}" aria-label="Back to workspace"></button>
        <div>
        <p class="eyebrow">${escapeHtml(label)}</p>
        <h1>${escapeHtml(title)}</h1>
        </div>
      </div>
    </header>
  `;
}

function metric(label: string, value: string): string {
  return `
    <div class="metric">
      <strong>${escapeHtml(value)}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
}

function emptyState(title: string, message: string): string {
  return `
    <div class="empty-state">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function statusPill(status: string): string {
  return `<span class="status-pill ${escapeHtml(status)}">${escapeHtml(status)}</span>`;
}

function totalScenarios(requirements: RequirementItem[]): number {
  return requirements.reduce((total, item) => total + item.scenarios.length, 0);
}

function totalFragments(requirements: RequirementItem[]): number {
  return requirements.reduce((total, item) => total + item.fragments.length, 0);
}

function titleCase(value: string): string {
  return value.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function normalizedKind(value: string): string {
  return value.trim().toLowerCase().replaceAll("_", "-");
}

function methodLabel(value: string): string {
  return titleCase(value.replaceAll("-", " "));
}

function requirementStatusText(state: AppState): string {
  if (state.requirementsFeedback?.state === "error") {
    return escapeHtml(state.requirementsFeedback.text);
  }
  if (state.requirementsFeedback?.state === "running") {
    return "Loading requirements...";
  }
  if (state.requirements !== null) {
    return `${state.requirements.requirements.length} requirements loaded from ${escapeHtml(state.requirements.name)}.`;
  }
  return `No requirements loaded. ${supportedFormatsText(state, "requirements")}`;
}

function evidenceStatusText(state: AppState): string {
  if (state.evidenceFeedback?.state === "error") {
    return escapeHtml(state.evidenceFeedback.text);
  }
  if (state.evidenceFeedback?.state === "running") {
    return "Loading evidence...";
  }
  if (state.evidence !== null) {
    return `${escapeHtml(state.evidence.name)} loaded with ${state.evidence.stateCount} states, ${state.evidence.actionCount} actions, and ${state.evidence.transitionCount} transitions.`;
  }
  return `No evidence loaded. ${supportedFormatsText(state, "evidence")}`;
}

function supportedFormatsText(state: AppState, artifact: string): string {
  const formats = [
    ...new Set(
      state.parsers
        .filter((parser) => parser.artifact === artifact)
        .map((parser) => parser.format)
        .filter((format) => format !== "jira" && !format.endsWith("-api")),
    ),
  ];
  return formats.length === 0
    ? ""
    : `Supported files: ${formats.map((format) => `.${format}`).join(", ")}.`;
}

function previewText(value: string): string {
  return value.length > 8000 ? `${value.slice(0, 8000)}\n...` : value;
}

function boundedPercent(value: number): number {
  return Math.max(4, Math.min(100, Math.round(value * 100)));
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
