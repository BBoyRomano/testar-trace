import { describe, expect, it, vi } from "vite-plus/test";

vi.mock("./icons.ts", () => ({
  icon: (name: string) => `<svg data-icon="${name}"></svg>`,
}));

import { resultDetailState } from "./testing/view-fixtures.ts";
import { methodDescription, renderNewAnalysis } from "./views.ts";

describe("new analysis view", () => {
  it("explains completeness methods and the boundary of lexical matching", () => {
    expect(methodDescription("graph-alignment")).toContain("Recommended");
    expect(methodDescription("graph-alignment")).toContain("connected state-model route");
    expect(methodDescription("lexical")).toContain("not behavioral completeness");
  });

  it("derives source actions, formats, and compact file lists from the current catalog", () => {
    const state = resultDetailState("partial");
    state.view = "new-analysis";
    state.requirementAdapters = [
      { id: "use-cases", name: "Use cases", formats: ["md", "json"] },
      { id: "gherkin", name: "Gherkin", formats: ["feature"] },
    ];
    if (state.requirements !== null) {
      state.requirements.sources = Array.from({ length: 7 }, (_, index) => ({
        id: `source-${index}`,
        name: `requirement-${index}.md`,
        format: "md",
        text: "Requirement",
      }));
    }

    const html = renderNewAnalysis(state);

    expect(html).toContain('class="source-dropzone compact"');
    expect(html).toContain("Add Markdown, JSON, or Gherkin requirement files");
    expect(html.match(/Add more sources/g)).toHaveLength(2);
    expect(html).toContain("Show 1 more file");
    expect(html).toContain('class="icon-action remove-source-action"');
  });

  it("adapts instructions and generated-name guidance to source readiness", () => {
    const state = resultDetailState("partial");
    state.view = "new-analysis";
    state.requirements = null;
    state.stateModels = null;

    const emptyHtml = renderNewAnalysis(state);
    expect(emptyHtml).toContain("A name will be generated after you add sources.");
    expect(emptyHtml).toContain("Drop requirement files or folders");
    expect(emptyHtml).toContain("are not uploaded anywhere");
    expect(emptyHtml).not.toContain("Add requirements and state models to run the analysis.");
    expect(emptyHtml).not.toContain('id="analysis-readiness"');

    state.requirements = resultDetailState("partial").requirements;
    const partiallyLoadedHtml = renderNewAnalysis(state);
    expect(partiallyLoadedHtml).toContain(
      "Add the remaining source to generate the analysis name.",
    );
    expect(partiallyLoadedHtml).toMatch(/class="source-status[^"]*" role="status"/);
  });

  it("escapes user-controlled analysis names and source metadata", () => {
    const state = resultDetailState("partial");
    state.view = "new-analysis";
    state.analysisName = `"><img src=x onerror="alert(1)">`;
    state.requirements?.sources.push({
      id: "malicious-source",
      name: `<script>alert("source")</script>.md`,
      format: "md",
      text: "Requirement",
    });

    const html = renderNewAnalysis(state);

    expect(html).not.toContain("<img src=x");
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
    expect(html).toContain("&lt;img src=x");
  });
});
