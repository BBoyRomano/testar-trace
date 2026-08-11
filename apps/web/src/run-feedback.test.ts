import { describe, expect, it } from "vite-plus/test";

import { backgroundRunFeedback } from "./run-feedback.ts";

describe("backgroundRunFeedback", () => {
  it("offers to open a completed background analysis", () => {
    expect(backgroundRunFeedback({ id: "run-1", status: "complete" })).toEqual({
      state: "complete",
      text: "Analysis complete.",
      presentation: "toast",
      action: { label: "View analysis", action: "view-analysis", runId: "run-1" },
    });
  });

  it("keeps a failed background analysis visible until it is dismissed or opened", () => {
    expect(backgroundRunFeedback({ id: "run-1", status: "failed" })).toEqual({
      state: "error",
      text: "Analysis failed.",
      presentation: "toast",
      action: { label: "View details", action: "view-analysis", runId: "run-1" },
    });
  });

  it("does not notify for running or explicitly cancelled analyses", () => {
    expect(backgroundRunFeedback({ id: "run-1", status: "running" })).toBeNull();
    expect(backgroundRunFeedback({ id: "run-1", status: "cancelled" })).toBeNull();
  });
});
