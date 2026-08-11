import type { AnalysisRun, FeedbackMessage } from "./types.ts";

export function backgroundRunFeedback(
  run: Pick<AnalysisRun, "id" | "status">,
): FeedbackMessage | null {
  if (run.status === "complete") {
    return {
      state: "complete",
      text: "Analysis complete.",
      presentation: "toast",
      action: { label: "View analysis", action: "view-analysis", runId: run.id },
    };
  }
  if (run.status === "failed") {
    return {
      state: "error",
      text: "Analysis failed.",
      presentation: "toast",
      action: { label: "View details", action: "view-analysis", runId: run.id },
    };
  }
  return null;
}
