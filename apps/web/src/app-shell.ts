import { icon } from "./icons.ts";
import { routePath } from "./routes.ts";
import { LOCAL_PROCESSING_MESSAGE } from "./ui-copy.ts";

/**
 * Renders the persistent application chrome and modal surfaces.
 * Feature pages are rendered separately into the #view landmark.
 */
export function renderAppShell(): string {
  return `
    <div class="app-shell">
      <a class="skip-link" href="#view">Skip to main content</a>
      <header class="app-header">
        <a class="brand" href="${routePath("analyses")}" data-route aria-label="Go to analyses">
          <span class="brand-mark" aria-hidden="true">T</span>
          <span><strong>TESTAR Trace</strong><small>Requirements traceability</small></span>
        </a>
        <div class="app-actions">
          <button id="global-new-analysis" type="button" data-action="start-new-analysis" aria-label="New analysis">${icon("newAnalysis")}<span class="action-label-full" aria-hidden="true">New analysis</span><span class="action-label-short" aria-hidden="true">New</span></button>
          <button type="button" class="secondary" data-action="open-import-dialog" aria-label="Import analysis">${icon("import")}<span class="action-label-full" aria-hidden="true">Import analysis</span><span class="action-label-short" aria-hidden="true">Import</span></button>
          <button type="button" class="tertiary utility-button" data-action="open-help" aria-label="Open help" title="Help">${icon("help")}</button>
        </div>
      </header>
      <main id="view" class="main-content"></main>
      ${helpDialog()}
      ${importDialog()}
      ${confirmationDialog()}
      <input id="requirements-file-input" type="file" multiple hidden />
      <input id="requirements-directory-input" type="file" webkitdirectory multiple hidden />
      <input id="state-model-file-input" type="file" multiple hidden />
      <input id="state-model-directory-input" type="file" webkitdirectory multiple hidden />
      <p id="selection-announcer" class="visually-hidden" aria-live="polite" aria-atomic="true"></p>
    </div>`;
}

function helpDialog(): string {
  return `
    <dialog id="help-dialog" class="help-dialog" aria-labelledby="help-dialog-title" aria-describedby="help-dialog-description">
      <div class="dialog-header"><h2 id="help-dialog-title">Using TESTAR Trace</h2><button type="button" class="icon-button" data-action="close-help" aria-label="Close help">${icon("close")}</button></div>
      <p id="help-dialog-description" class="dialog-description">Compare requirements with TESTAR state models, assess completeness, and inspect the trace evidence behind each result.</p>
      <ol class="help-steps" aria-label="How to run an analysis">
        <li><span aria-hidden="true">1</span><div><strong>Add sources</strong><p>Select requirement and state-model files or folders. Supported requirement formats can be mixed.</p></div></li>
        <li><span aria-hidden="true">2</span><div><strong>Run the analysis</strong><p>Choose a traceability method and follow its progress while it runs locally.</p></div></li>
        <li><span aria-hidden="true">3</span><div><strong>Review results</strong><p>Explore completeness by requirement and requirement path, then inspect supporting trace evidence.</p></div></li>
      </ol>
      <div class="help-data">
        <section class="help-data-item"><span class="help-data-icon" aria-hidden="true">${icon("inspect")}</span><div><h3>Understanding results</h3><dl class="help-definitions"><div><dt>Requirement completeness</dt><dd>Whether the selected method finds support for every applicable requirement path and obligation in the available state models. Not assessable means the method could not establish a conclusion; it is different from incomplete.</dd></div><div><dt>Evidence coverage</dt><dd>How much required content and flow structure is supported by trace evidence.</dd></div><div><dt>Requirement path</dt><dd>One complete route through an authored main, alternative, or exception flow.</dd></div></dl></div></section>
        <section class="help-data-item"><span class="help-data-icon" aria-hidden="true">${icon("local")}</span><div><h3>Your data stays local</h3><p>${LOCAL_PROCESSING_MESSAGE} Completed analyses are stored in this browser until you delete them.</p></div></section>
        <section class="help-data-item"><span class="help-data-icon" aria-hidden="true">${icon("export")}</span><div><h3>Share analyses</h3><p><strong>Export analysis</strong> creates a portable TESTAR Trace analysis file with its original source text, requirements, state models, and results. <strong>Export selected</strong> combines the selected analyses into one file. <strong>Import analysis</strong> restores either file without analyzing its sources again.</p></div></section>
      </div>
    </dialog>`;
}

function importDialog(): string {
  return `
    <dialog id="import-dialog" class="import-dialog" aria-labelledby="import-dialog-title" aria-describedby="import-dialog-description import-local-processing">
      <div class="dialog-header"><h2 id="import-dialog-title">Import analysis</h2><button type="button" class="icon-button" data-action="close-import-dialog" aria-label="Close import dialog">${icon("close")}</button></div>
      <p id="import-dialog-description" class="dialog-description">Restore one or more completed analyses from a TESTAR Trace analysis file, including their requirements, state models, and results. Source files are not analyzed again.</p>
      <div class="source-dropzone import-dropzone" data-drop-target="analysis-import">
        <span class="dropzone-icon">${icon("import")}</span>
        <div class="dropzone-copy"><strong><span class="drop-label-desktop">Drop a TESTAR Trace analysis file</span><span class="drop-label-touch">Add a TESTAR Trace analysis file</span></strong><p>Use .testar-analysis.json for one analysis or .testar-analyses.json for multiple analyses.</p></div>
        <div class="source-actions"><button id="choose-import-file" type="button" data-action="choose-import-file">${icon("files")}Choose analysis file</button></div>
      </div>
      <p id="import-local-processing" class="local-processing dialog-local-processing">${icon("local")}${LOCAL_PROCESSING_MESSAGE}</p>
      <p id="import-feedback" class="import-feedback" role="status" aria-live="polite"></p>
      <div id="import-progress" class="transfer-progress" role="progressbar" aria-label="Import progress" hidden><span></span></div>
      <div id="import-transfer-actions" class="dialog-transfer-actions" hidden><button id="cancel-import" type="button" class="secondary compact-action" data-action="cancel-import">${icon("cancel")}Cancel import</button></div>
      <input id="import-file-input" type="file" accept=".testar-analysis.json,.testar-analyses.json" hidden />
    </dialog>`;
}

function confirmationDialog(): string {
  return `
    <dialog id="confirmation-dialog" class="confirmation-dialog" aria-labelledby="confirmation-dialog-title" aria-describedby="confirmation-dialog-message">
      <form method="dialog">
        <span class="confirmation-icon" aria-hidden="true">${icon("delete")}</span>
        <div><h2 id="confirmation-dialog-title">Delete analysis?</h2><p id="confirmation-dialog-message" class="dialog-description"></p></div>
        <div class="dialog-actions"><button id="confirmation-cancel" type="submit" class="secondary" value="cancel">Cancel</button><button id="confirmation-confirm" type="submit" class="destructive" value="confirm">Delete</button></div>
      </form>
    </dialog>`;
}
