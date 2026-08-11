import { describe, expect, it } from "vite-plus/test";

import { isWorkerResponse } from "./worker-protocol.ts";

describe("worker response protocol", () => {
  it("accepts structured incremental progress without treating it as the final response", () => {
    expect(
      isWorkerResponse({
        id: "request-1",
        type: "progress",
        progress: {
          phase: "lexical.matching",
          message: "Matched requirement element STEP-1",
          completed: 1,
          total: 4,
          metadata: {},
        },
      }),
    ).toBe(true);
  });

  it("keeps final success and failure responses explicit", () => {
    expect(isWorkerResponse({ id: "request-1", type: "result", ok: true, value: {} })).toBe(true);
    expect(
      isWorkerResponse({
        id: "request-1",
        type: "result",
        ok: false,
        error: { name: "ValueError", message: "Invalid input" },
      }),
    ).toBe(true);
  });
});
