import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import { WorkerClient } from "./worker-client.ts";

class FakeWorker extends EventTarget {
  static instances: FakeWorker[] = [];

  terminated = false;
  messages: unknown[] = [];

  constructor() {
    super();
    FakeWorker.instances.push(this);
  }

  postMessage(value: unknown): void {
    this.messages.push(value);
  }

  terminate(): void {
    this.terminated = true;
  }

  fail(message: string): void {
    this.dispatchEvent(Object.assign(new Event("error"), { message }));
  }
}

beforeEach(() => {
  FakeWorker.instances = [];
  vi.stubGlobal("Worker", FakeWorker);
});

afterEach(() => vi.unstubAllGlobals());

describe("WorkerClient", () => {
  it("rejects pending work after a worker crash and recreates the worker", async () => {
    const client = new WorkerClient();
    const firstRequest = client.request("catalog");
    const firstWorker = FakeWorker.instances[0]!;

    firstWorker.fail("Python worker crashed.");

    await expect(firstRequest).rejects.toThrow("Python worker crashed");
    expect(firstWorker.terminated).toBe(true);

    void client.request("catalog");
    expect(FakeWorker.instances).toHaveLength(2);
  });

  it("cancels all pending work and terminates the active worker", async () => {
    const client = new WorkerClient();
    const controller = new AbortController();
    const request = client.request("analyze", {}, { signal: controller.signal });
    const worker = FakeWorker.instances[0]!;

    controller.abort();

    await expect(request).rejects.toMatchObject({ name: "AbortError" });
    expect(worker.terminated).toBe(true);
  });
});
