/// <reference lib="webworker" />

import {
  createPortableAnalysesBundle,
  createPortableAnalysisBundle,
  parseAnalysisFile,
  selectAnalysisImportFile,
} from "../result-files.ts";
import type { AnalysisRun, PortableAnalysisBundle } from "../types.ts";
import type {
  ExportTransferPayload,
  ImportTransferPayload,
  TransferProgress,
  TransferRequest,
  TransferResponse,
} from "./transfer-protocol.ts";

const workerScope = self as unknown as DedicatedWorkerGlobalScope;

workerScope.addEventListener("message", (event: MessageEvent<TransferRequest>) => {
  void handleRequest(event.data);
});

async function handleRequest(request: TransferRequest): Promise<void> {
  try {
    const value =
      request.operation === "import-analysis"
        ? await importAnalysis(request.id, request.payload)
        : exportAnalyses(request.id, request.payload);
    workerScope.postMessage({
      id: request.id,
      type: "result",
      ok: true,
      value,
    } satisfies TransferResponse);
  } catch (error) {
    workerScope.postMessage({
      id: request.id,
      type: "result",
      ok: false,
      error: {
        name: error instanceof Error ? error.name : "Error",
        message: error instanceof Error ? error.message : String(error),
      },
    } satisfies TransferResponse);
  }
}

async function importAnalysis(
  id: string,
  payload: ImportTransferPayload,
): Promise<PortableAnalysisBundle[]> {
  const file = selectAnalysisImportFile([payload.file]);
  progress(id, { phase: "reading", message: `Reading ${file.name}…` });
  const text = await file.text();
  progress(id, { phase: "validating", message: "Parsing and validating analysis data…" });
  return parseAnalysisFile(text);
}

function exportAnalyses(id: string, payload: ExportTransferPayload): Blob {
  progress(id, { phase: "preparing", message: "Preparing analysis data…" });
  const bundle =
    payload.kind === "single"
      ? createPortableAnalysisBundle(requiredRun(payload))
      : createPortableAnalysesBundle(payload.runs);
  progress(id, { phase: "serializing", message: "Creating the export file…" });
  return new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
}

function requiredRun(payload: ExportTransferPayload): AnalysisRun {
  const run = payload.runs[0];
  if (run === undefined) throw new Error("Select an analysis to export.");
  return run;
}

function progress(id: string, value: TransferProgress): void {
  workerScope.postMessage({ id, type: "progress", progress: value } satisfies TransferResponse);
}
