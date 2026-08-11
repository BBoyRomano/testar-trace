export type AppElements = {
  view: HTMLDivElement;
  globalNewAnalysisButton: HTMLButtonElement;
  helpDialog: HTMLDialogElement;
  importDialog: HTMLDialogElement;
  confirmationDialog: HTMLDialogElement;
  confirmationDialogTitle: HTMLElement;
  confirmationDialogMessage: HTMLElement;
  confirmationCancelButton: HTMLButtonElement;
  confirmationConfirmButton: HTMLButtonElement;
  requirementsFileInput: HTMLInputElement;
  requirementsDirectoryInput: HTMLInputElement;
  stateModelFileInput: HTMLInputElement;
  stateModelDirectoryInput: HTMLInputElement;
  importFileInput: HTMLInputElement;
};

export function mountAppShell(markup: string): AppElements {
  const app = requiredElement(document.querySelector<HTMLDivElement>("#app"), "Missing #app root.");
  app.innerHTML = markup;
  return {
    view: requiredElement(document.querySelector<HTMLDivElement>("#view"), "Missing #view root."),
    globalNewAnalysisButton: requiredElement(
      document.querySelector<HTMLButtonElement>("#global-new-analysis"),
      "Missing global New analysis action.",
    ),
    helpDialog: requiredElement(
      document.querySelector<HTMLDialogElement>("#help-dialog"),
      "Missing help dialog.",
    ),
    importDialog: requiredElement(
      document.querySelector<HTMLDialogElement>("#import-dialog"),
      "Missing import dialog.",
    ),
    confirmationDialog: requiredElement(
      document.querySelector<HTMLDialogElement>("#confirmation-dialog"),
      "Missing confirmation dialog.",
    ),
    confirmationDialogTitle: requiredElement(
      document.querySelector<HTMLElement>("#confirmation-dialog-title"),
      "Missing confirmation dialog title.",
    ),
    confirmationDialogMessage: requiredElement(
      document.querySelector<HTMLElement>("#confirmation-dialog-message"),
      "Missing confirmation dialog message.",
    ),
    confirmationCancelButton: requiredElement(
      document.querySelector<HTMLButtonElement>("#confirmation-cancel"),
      "Missing confirmation cancel action.",
    ),
    confirmationConfirmButton: requiredElement(
      document.querySelector<HTMLButtonElement>("#confirmation-confirm"),
      "Missing confirmation action.",
    ),
    requirementsFileInput: requiredElement(
      document.querySelector<HTMLInputElement>("#requirements-file-input"),
      "Missing requirements input.",
    ),
    requirementsDirectoryInput: requiredElement(
      document.querySelector<HTMLInputElement>("#requirements-directory-input"),
      "Missing requirements directory input.",
    ),
    stateModelFileInput: requiredElement(
      document.querySelector<HTMLInputElement>("#state-model-file-input"),
      "Missing state-model input.",
    ),
    stateModelDirectoryInput: requiredElement(
      document.querySelector<HTMLInputElement>("#state-model-directory-input"),
      "Missing state-model directory input.",
    ),
    importFileInput: requiredElement(
      document.querySelector<HTMLInputElement>("#import-file-input"),
      "Missing import file input.",
    ),
  };
}

function requiredElement<T extends Element>(element: T | null, message: string): T {
  if (element === null) throw new Error(message);
  return element;
}
