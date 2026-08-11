/// <reference lib="webworker" />

import { loadPyodide, type PyodideInterface } from "pyodide";

import { userFacingErrorMessage } from "../error-message.ts";
import bridgeSource from "./worker-bridge.py?raw";
import type { AnalysisProgress } from "../types.ts";
import type { WorkerRequest, WorkerResponse } from "./worker-protocol.ts";

type BridgeResponse =
  | { ok: true; value: unknown }
  | { ok: false; error: { name: string; message: string } };

type PythonBridge = ((
  operation: string,
  payload: string,
  progress: (value: string) => void,
) => string) & { destroy(): void };

const workerScope = self as unknown as DedicatedWorkerGlobalScope;
let runtimePromise: Promise<{ pyodide: PyodideInterface; bridge: PythonBridge }> | null = null;

workerScope.addEventListener("message", (event: MessageEvent<WorkerRequest>) => {
  void handleMessage(event.data);
});

async function handleMessage(request: WorkerRequest): Promise<void> {
  let response: WorkerResponse;
  try {
    const { bridge } = await initializeRuntime();
    const reportProgress = (value: string): void => {
      const progress = parseProgress(value);
      workerScope.postMessage({
        id: request.id,
        type: "progress",
        progress,
      } satisfies WorkerResponse);
    };
    const bridgeResponse = parseBridgeResponse(
      bridge(request.operation, JSON.stringify(request.payload), reportProgress),
    );
    response = bridgeResponse.ok
      ? { id: request.id, type: "result", ok: true, value: bridgeResponse.value }
      : { id: request.id, type: "result", ok: false, error: bridgeResponse.error };
  } catch (error) {
    response = {
      id: request.id,
      type: "result",
      ok: false,
      error: {
        name: error instanceof Error ? error.name : "WorkerError",
        message: userFacingErrorMessage(error, "The analysis worker could not start."),
      },
    };
  }
  workerScope.postMessage(response);
}

function parseProgress(value: string): AnalysisProgress {
  const parsed: unknown = JSON.parse(value);
  if (typeof parsed !== "object" || parsed === null || !("phase" in parsed)) {
    throw new Error("The Python worker returned an invalid progress event.");
  }
  const progress = parsed as Record<string, unknown>;
  return {
    phase: String(progress.phase),
    message: typeof progress.message === "string" ? progress.message : null,
    completed: typeof progress.completed === "number" ? progress.completed : null,
    total: typeof progress.total === "number" ? progress.total : null,
    metadata:
      typeof progress.metadata === "object" && progress.metadata !== null
        ? (progress.metadata as AnalysisProgress["metadata"])
        : {},
  };
}

function initializeRuntime(): Promise<{ pyodide: PyodideInterface; bridge: PythonBridge }> {
  runtimePromise ??= loadRuntime().catch((error: unknown) => {
    runtimePromise = null;
    throw error;
  });
  return runtimePromise;
}

async function loadRuntime(): Promise<{ pyodide: PyodideInterface; bridge: PythonBridge }> {
  const runtimeRoot = new URL(`${import.meta.env.BASE_URL}python/`, workerScope.location.origin);
  const manifestResponse = await fetch(new URL("manifest.json", runtimeRoot));
  if (!manifestResponse.ok) {
    throw new Error(`Could not load the Python runtime manifest (${manifestResponse.status}).`);
  }
  const manifest = parseManifest(await manifestResponse.json());
  const pyodideRoot = new URL("pyodide/", runtimeRoot).href;
  const pyodide = await loadPyodide({ indexURL: pyodideRoot, packageBaseUrl: pyodideRoot });
  for (const wheel of manifest.wheels) {
    await pyodide.loadPackage(new URL(wheel, runtimeRoot).href);
  }
  const bridge = pyodide.runPython(bridgeSource) as PythonBridge;
  return { pyodide, bridge };
}

function parseManifest(value: unknown): { wheels: string[] } {
  if (
    typeof value !== "object" ||
    value === null ||
    !("wheels" in value) ||
    !Array.isArray(value.wheels) ||
    !value.wheels.every((wheel) => typeof wheel === "string")
  ) {
    throw new Error("The Python runtime manifest is invalid.");
  }
  return { wheels: value.wheels };
}

function parseBridgeResponse(value: string): BridgeResponse {
  const parsed: unknown = JSON.parse(value);
  if (typeof parsed !== "object" || parsed === null || !("ok" in parsed)) {
    throw new Error("The Python worker returned an invalid response.");
  }
  if (parsed.ok === true && "value" in parsed) {
    return { ok: true, value: parsed.value };
  }
  if (
    parsed.ok === false &&
    "error" in parsed &&
    typeof parsed.error === "object" &&
    parsed.error !== null &&
    "name" in parsed.error &&
    typeof parsed.error.name === "string" &&
    "message" in parsed.error &&
    typeof parsed.error.message === "string"
  ) {
    return { ok: false, error: { name: parsed.error.name, message: parsed.error.message } };
  }
  throw new Error("The Python worker returned an invalid response.");
}

export {};
