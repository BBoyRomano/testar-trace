import { describe, expect, it, vi } from "vite-plus/test";

vi.mock("./icons.ts", () => ({
  icon: (name: string) => `<svg data-icon="${name}"></svg>`,
}));

import type { AnalysisResult } from "./types.ts";
import { assessment, occurrence, resultDetailState, stateModel } from "./testing/view-fixtures.ts";
import {
  completenessBadgeLabel,
  feedbackIconName,
  renderResultDetail,
  resultMetrics,
} from "./views.ts";

describe("result view semantics", () => {
  it("distinguishes unavailable assessments, failed operations, and incomplete results", () => {
    expect(completenessBadgeLabel(null)).toBe("Not available");
    expect(feedbackIconName("failed")).toBe("error");
    expect(feedbackIconName("error")).toBe("error");
    expect(feedbackIconName("cancelled")).toBe("cancelled");
  });

  it("shows concise completeness metrics and keeps coverage secondary", () => {
    const html = resultMetrics({
      summary: {
        totalRequirements: 4,
        completeRequirements: 0,
        incompleteRequirements: 4,
        notAssessableRequirements: 0,
        coveredRequirements: 0,
        partiallyCoveredRequirements: 0,
        uncoveredRequirements: 4,
        totalPaths: 0,
        completePaths: 0,
        incompletePaths: 0,
        notAssessablePaths: 0,
        overallCoverageRatio: null,
      },
    } as AnalysisResult);

    expect(html).toContain("0 of 4 complete");
    expect(html).toContain("4 incomplete requirements.");
    expect(html).toContain("Paths complete");
    expect(html).toContain("Evidence coverage");
    expect(html.match(/class="summary-card/g)).toHaveLength(3);
  });

  it("keeps graph inspection before the authored specification in one document flow", () => {
    const html = renderResultDetail(resultDetailState("partial"));
    const graphStart = html.indexOf('class="graph-panel result-graph"');
    const inspectorStart = html.indexOf('class="result-inspector"');

    expect(graphStart).toBeGreaterThan(-1);
    expect(inspectorStart).toBeGreaterThan(graphStart);
    expect(html).toContain('class="content-panel result-layout result-inspector-shell"');
    expect(html).toContain('id="result-path-select"');
    expect(html).toContain(">All requirement paths (1)</option>");
    expect(html).toContain("Use case specification");
    expect(html).toContain("Main success scenario");
    expect(html).toContain("Alternative flows");
    expect(html).toContain("Technology and data variations list");
    expect(html).toContain('class="source-snippet"');
    expect(html).not.toContain("Highlighted evidence");
  });

  it("preserves source-specific Gherkin and user-story terminology", () => {
    const gherkin = resultDetailState("partial");
    if (gherkin.requirements !== null) gherkin.requirements.adapterId = "gherkin";
    const gherkinHtml = renderResultDetail(gherkin);
    expect(gherkinHtml).toContain("Gherkin specification");
    expect(gherkinHtml).toContain("<dt>Scenarios</dt>");
    expect(gherkinHtml).not.toContain("<dt>Main success scenario</dt>");

    const userStory = resultDetailState("partial");
    if (userStory.requirements !== null) userStory.requirements.adapterId = "user-story";
    const userStoryHtml = renderResultDetail(userStory);
    expect(userStoryHtml).toContain('<h3 id="requirement-specification-title">User story</h3>');
    expect(userStoryHtml).toContain("<dt>Acceptance criteria</dt>");
    expect(userStoryHtml).not.toContain("<dt>Alternative flows</dt>");
  });

  it("recovers explicit N/A values from saved source text", () => {
    const state = resultDetailState("partial");
    const requirement = state.requirements?.requirements[0];
    if (requirement !== undefined) {
      requirement.body = "";
      requirement.metadata = { related_information: ["Payment policy"] };
    }
    if (state.requirements !== null) {
      state.requirements.sources = [
        {
          id: "checkout.md",
          name: "checkout.md",
          format: "md",
          text: "**Technology and Data Variations List**\nN/A",
        },
      ];
    }

    const html = renderResultDetail(state);
    expect(html).toContain("N/A");
    expect(html).not.toContain("None specified");
  });

  it("uses the best occurrence and keeps collection metrics stable across model selection", () => {
    const state = resultDetailState("partial");
    state.runs[0]?.result?.occurrences.push(
      occurrence(
        "occurrence-full",
        "full",
        ["precondition-1", "trigger-1", "step-1", "step-2", "postcondition-1"],
        [],
      ),
    );
    state.runs[0]?.result?.assessments.splice(
      0,
      2,
      assessment("requirement", "UC-01", "complete"),
      assessment("path", "path-main", "complete"),
    );
    state.stateModels?.models.push({
      ...stateModel(),
      id: "model-2",
      title: "secondary.json",
      sourceName: "secondary.json",
    });

    const primaryHtml = renderResultDetail(state);
    expect(primaryHtml).toContain("Complete in model.json");
    expect(primaryHtml).not.toContain('class="sequence-status missing"');
    expect(primaryHtml).toContain("across 2 state models.");

    state.selectedStateModelId = "model-2";
    const secondaryHtml = renderResultDetail(state);
    expect(secondaryHtml).toContain("0 of 1 complete");
    expect(secondaryHtml).toContain("Not found in secondary.json");
  });

  it("uses inline status for active exports and compact toasts for completed work", () => {
    const running = resultDetailState("partial");
    running.analysisFeedback = { state: "running", text: "Creating the export file…" };
    const runningHtml = renderResultDetail(running);
    expect(runningHtml).toContain('data-action="cancel-export"');
    expect(runningHtml).not.toContain('data-action="dismiss-analysis-feedback"');

    const completed = resultDetailState("partial");
    completed.analysisFeedback = {
      state: "complete",
      text: "Analysis imported.",
      presentation: "toast",
    };
    const completedHtml = renderResultDetail(completed);
    expect(completedHtml).toContain("feedback-toast");
    expect(completedHtml).toContain('aria-label="Dismiss notification"');
  });
});
