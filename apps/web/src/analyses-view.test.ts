import { describe, expect, it, vi } from "vite-plus/test";

vi.mock("./icons.ts", () => ({
  icon: (name: string) => `<svg data-icon="${name}"></svg>`,
}));

import { analysisRun, resultDetailState } from "./testing/view-fixtures.ts";
import { renderAnalysesOverview, renderOverviewCompleteness } from "./views.ts";

describe("analyses view", () => {
  it("summarizes completeness without repeating a fully assessable remainder", () => {
    const html = renderOverviewCompleteness(analysisRun(0, 4, 0), 0);

    expect(html).toContain("0 of 4 complete");
    expect(html).not.toContain("4 incomplete requirements");
  });

  it("explains incomplete and not-assessable requirements separately", () => {
    const html = renderOverviewCompleteness(analysisRun(1, 2, 1), 0.25);

    expect(html).toContain("1 of 4 complete");
    expect(html).toContain("2 incomplete requirements · 1 requirement not assessable");
  });

  it("supports selecting every matching analysis beyond the current page", () => {
    const state = resultDetailState("partial");
    state.view = "analyses";
    const original = state.runs[0];
    if (original === undefined) throw new Error("Missing analysis fixture.");
    state.runs = Array.from({ length: 11 }, (_, index) => ({
      ...structuredClone(original),
      id: `run-${index}`,
      title: `Analysis ${index + 1}`,
      createdAt: new Date(Date.UTC(2026, 7, index + 1)).toISOString(),
    }));
    state.selectedAnalysisIds = ["run-10"];

    const html = renderAnalysesOverview(state);

    expect(html).toContain('class="analysis-table batch-mode"');
    expect(html).toContain('data-action="select-all-filtered-analyses"');
    expect(html).toContain("Select all 11");
    expect(html).toContain('class="batch-actions"');
  });

  it("distinguishes run status from completeness and explains disabled bulk export", () => {
    const state = resultDetailState("partial");
    state.view = "analyses";

    const finishedHtml = renderAnalysesOverview(state);
    expect(finishedHtml).toContain("Finished");
    expect(finishedHtml).toContain("9 Aug 2026");

    const analysis = state.runs[0];
    if (analysis === undefined) throw new Error("Missing analysis fixture.");
    analysis.status = "failed";
    analysis.result = null;
    state.selectedAnalysisIds = [analysis.id];

    const failedHtml = renderAnalysesOverview(state);
    expect(failedHtml).toContain("Export requires finished analyses with saved inputs.");
    expect(failedHtml).toContain('disabled aria-describedby="batch-export-description"');
  });
});
