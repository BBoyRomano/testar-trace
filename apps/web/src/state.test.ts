import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import { analysisRun } from "./testing/view-fixtures.ts";
import { createInitialState, hydrateRunResults, loadRuns, persistRuns } from "./state.ts";

const storage = new Map<string, string>();

beforeEach(() => {
  storage.clear();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => storage.set(key, value),
  });
});

afterEach(() => vi.unstubAllGlobals());

describe("run metadata persistence", () => {
  it("starts with stable defaults when storage is empty or invalid", () => {
    expect(createInitialState()).toMatchObject({
      view: "analyses",
      loadState: "empty",
      selectedMethodId: "graph-alignment",
      runs: [],
    });

    storage.set("testar-trace.web.runs.v2", "not JSON");
    expect(loadRuns()).toEqual([]);
    storage.set("testar-trace.web.runs.v2", "{}");
    expect(loadRuns()).toEqual([]);
  });

  it("marks an interrupted run as cancelled and discards stale result payloads", () => {
    storage.set(
      "testar-trace.web.runs.v2",
      JSON.stringify([
        {
          id: "run-1",
          title: "Checkout",
          status: "running",
          methodId: "graph-alignment",
          methodName: "Graph alignment",
          createdAt: "2026-08-09T10:00:00Z",
          progress: 0.75,
          message: "Matching paths",
          result: null,
        },
      ]),
    );

    expect(loadRuns()).toEqual([
      expect.objectContaining({
        id: "run-1",
        status: "cancelled",
        progress: 0,
        message: "Analysis was interrupted.",
        result: null,
        requirements: null,
        stateModels: null,
      }),
    ]);
  });

  it("stores only lightweight run metadata and preserves actionable failures", () => {
    const completed = analysisRun(1, 0, 0);
    const failed = { ...analysisRun(0, 1, 0), id: "failed", status: "failed" as const };
    failed.message = "Python worker stopped.";

    persistRuns([completed, failed]);

    const saved = JSON.parse(storage.get("testar-trace.web.runs.v2") ?? "[]") as Array<
      Record<string, unknown>
    >;
    expect(saved[0]).toMatchObject({ result: null, message: "" });
    expect(saved[0]).not.toHaveProperty("requirements");
    expect(saved[0]).not.toHaveProperty("stateModels");
    expect(saved[1]).toMatchObject({ status: "failed", message: "Python worker stopped." });
  });

  it("surfaces browser storage failures to the caller", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: () => {
        throw new DOMException("Storage quota exceeded.", "QuotaExceededError");
      },
    });

    expect(() => persistRuns([analysisRun(1, 0, 0)])).toThrow("Storage quota exceeded");
  });

  it("closes a database connection that succeeds after a blocked open was rejected", async () => {
    const close = vi.fn();
    const request = {
      error: null,
      result: { close },
      onblocked: null as ((event: Event) => void) | null,
      onerror: null as ((event: Event) => void) | null,
      onsuccess: null as ((event: Event) => void) | null,
      onupgradeneeded: null as ((event: Event) => void) | null,
    };
    vi.stubGlobal("indexedDB", {
      open: () => request as unknown as IDBOpenDBRequest,
    });

    const hydration = hydrateRunResults([]);
    request.onblocked?.(new Event("blocked"));
    await expect(hydration).rejects.toThrow("Browser storage is blocked by another tab");

    request.onsuccess?.(new Event("success"));
    expect(close).toHaveBeenCalledOnce();
  });
});
