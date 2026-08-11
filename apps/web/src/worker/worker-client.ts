import type { AnalysisProgress } from "../types.ts";
import { isWorkerResponse, type WorkerOperation } from "./worker-protocol.ts";

type PendingRequest = {
  resolve(value: unknown): void;
  reject(reason: unknown): void;
  signal?: AbortSignal;
  abortListener?: () => void;
  onProgress?: (progress: AnalysisProgress) => void;
};

type RequestOptions = {
  signal?: AbortSignal;
  onProgress?: (progress: AnalysisProgress) => void;
};

export class WorkerClient {
  private worker: Worker | null = null;
  private readonly pending = new Map<string, PendingRequest>();

  request<T>(
    operation: WorkerOperation,
    payload: unknown = {},
    options: RequestOptions = {},
  ): Promise<T> {
    if (options.signal?.aborted === true) {
      return Promise.reject(abortError());
    }

    const worker = this.getWorker();
    const id = crypto.randomUUID();
    return new Promise<T>((resolve, reject) => {
      const pending: PendingRequest = {
        resolve: (value) => resolve(value as T),
        reject,
      };
      if (options.onProgress !== undefined) pending.onProgress = options.onProgress;
      if (options.signal !== undefined) {
        pending.signal = options.signal;
        pending.abortListener = () => this.reset(abortError());
        options.signal.addEventListener("abort", pending.abortListener, { once: true });
      }
      this.pending.set(id, pending);
      worker.postMessage({ id, operation, payload });
    });
  }

  private getWorker(): Worker {
    if (this.worker !== null) {
      return this.worker;
    }
    const worker = new Worker(new URL("./pyodide.worker.ts", import.meta.url), { type: "module" });
    worker.addEventListener("message", (event: MessageEvent<unknown>) => {
      if (this.worker !== worker || !isWorkerResponse(event.data)) {
        return;
      }
      const pending = this.pending.get(event.data.id);
      if (pending === undefined) {
        return;
      }
      if (event.data.type === "progress") {
        pending.onProgress?.(event.data.progress);
        return;
      }
      this.pending.delete(event.data.id);
      removeAbortListener(pending);
      if (event.data.ok) {
        pending.resolve(event.data.value);
      } else {
        const error = new Error(event.data.error.message);
        error.name = event.data.error.name;
        pending.reject(error);
      }
    });
    worker.addEventListener("error", (event) => {
      if (this.worker === worker) {
        this.reset(new Error(event.message || "The analysis worker stopped unexpectedly."));
      }
    });
    this.worker = worker;
    return worker;
  }

  private reset(reason: unknown): void {
    this.worker?.terminate();
    this.worker = null;
    for (const pending of this.pending.values()) {
      removeAbortListener(pending);
      pending.reject(reason);
    }
    this.pending.clear();
  }
}

function removeAbortListener(pending: PendingRequest): void {
  if (pending.signal !== undefined && pending.abortListener !== undefined) {
    pending.signal.removeEventListener("abort", pending.abortListener);
  }
}

function abortError(): DOMException {
  return new DOMException("The analysis was cancelled.", "AbortError");
}
