import { describe, expect, it } from "vite-plus/test";

import { isTransferResponse } from "./transfer-protocol.ts";

describe("transfer worker protocol", () => {
  it("accepts progress and result messages from the transfer worker", () => {
    expect(
      isTransferResponse({
        id: "transfer-1",
        type: "progress",
        progress: { phase: "reading", message: "Reading analysis…" },
      }),
    ).toBe(true);
    expect(
      isTransferResponse({
        id: "transfer-1",
        type: "result",
        ok: false,
        error: { name: "Error", message: "Invalid analysis." },
      }),
    ).toBe(true);
  });

  it("rejects malformed worker messages", () => {
    expect(isTransferResponse(null)).toBe(false);
    expect(isTransferResponse({ id: "transfer-1", type: "progress", progress: {} })).toBe(false);
    expect(
      isTransferResponse({
        id: "transfer-1",
        type: "progress",
        progress: { phase: "unknown", message: "Working…" },
      }),
    ).toBe(false);
    expect(
      isTransferResponse({ id: "transfer-1", type: "result", ok: false, error: "Invalid" }),
    ).toBe(false);
  });
});
