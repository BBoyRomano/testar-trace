import type { AnalysisRun, PortableAnalysisBundle } from "../types.ts";
import {
  isTransferResponse,
  type TransferOperation,
  type TransferProgress,
  type TransferRequest,
} from "./transfer-protocol.ts";

type TransferOptions = {
  signal: AbortSignal;
  onProgress?: (progress: TransferProgress) => void;
};

export function importAnalysisInBackground(
  file: File,
  options: TransferOptions,
): Promise<PortableAnalysisBundle[]> {
  return runTransfer("import-analysis", { file }, options);
}

export function exportAnalysesInBackground(
  runs: AnalysisRun[],
  kind: "single" | "bulk",
  options: TransferOptions,
): Promise<Blob> {
  return runTransfer("export-analyses", { kind, runs }, options);
}

function runTransfer<T>(
  operation: TransferOperation,
  payload: TransferRequest["payload"],
  options: TransferOptions,
): Promise<T> {
  if (options.signal.aborted) return Promise.reject(abortError());
  const worker = new Worker(new URL("./transfer.worker.ts", import.meta.url), { type: "module" });
  const id = crypto.randomUUID();
  return new Promise<T>((resolve, reject) => {
    let settled = false;
    const finish = (callback: () => void): void => {
      if (settled) return;
      settled = true;
      options.signal.removeEventListener("abort", abort);
      worker.terminate();
      callback();
    };
    const abort = (): void => finish(() => reject(abortError()));
    options.signal.addEventListener("abort", abort, { once: true });
    worker.addEventListener("message", (event: MessageEvent<unknown>) => {
      if (!isTransferResponse(event.data) || event.data.id !== id) return;
      const response = event.data;
      if (response.type === "progress") {
        options.onProgress?.(response.progress);
        return;
      }
      if (response.ok) finish(() => resolve(response.value as T));
      else {
        const error = new Error(response.error.message);
        error.name = response.error.name;
        finish(() => reject(error));
      }
    });
    worker.addEventListener("error", (event) => {
      finish(() => reject(new Error(event.message || "The file transfer stopped unexpectedly.")));
    });
    worker.postMessage({ id, operation, payload } as TransferRequest);
  });
}

function abortError(): DOMException {
  return new DOMException("The file transfer was cancelled.", "AbortError");
}
