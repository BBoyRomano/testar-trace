import { describe, expect, it, vi } from "vite-plus/test";

vi.mock("./icons.ts", () => ({
  icon: (name: string) => `<svg data-icon="${name}"></svg>`,
}));

import { resultDetailState, useCaseRequirement } from "./testing/view-fixtures.ts";
import { renderRequirementsDetail, renderStateModelsDetail } from "./views.ts";

describe("requirements review view", () => {
  it("provides scalable navigation and a single selected-detail workspace", () => {
    const state = resultDetailState("partial");
    state.view = "requirements";
    state.requirements?.requirements.push({
      ...useCaseRequirement(),
      id: "UC-02",
      title: "Cancel checkout",
    });

    const html = renderRequirementsDetail(state);

    expect(html).toContain('id="requirement-search"');
    expect(html).toContain('data-scroll-key="requirements-list"');
    expect(html).toContain("2 requirements");
    expect(html).toContain('class="content-panel review-layout requirements-review"');
    expect(html).toContain('<aside class="review-navigation"');
    expect(html).toContain('class="review-content inspector-panel"');
    expect(html).toContain('aria-current="true"');
    expect(html).not.toContain("aria-pressed");
  });
});

describe("state-model review view", () => {
  it("renders the graph as an accessible image with a table alternative", () => {
    const state = resultDetailState("partial");
    state.view = "state-models";

    const html = renderStateModelsDetail(state);

    expect(html).toContain('id="state-model-graph"');
    expect(html).toContain('class="evidence-graph result-evidence-graph" role="img"');
    expect(html).toContain('aria-label="State-model graph controls"');
    expect(html).toContain("View model as table");
    expect(html).toContain("From state");
    expect(html).toContain("Pay");
    expect(html).not.toContain("graph-selection-inspector");
  });

  it("keeps original model files available without duplicating raw graph text", () => {
    const state = resultDetailState("partial");
    state.view = "state-models";
    if (state.stateModels !== null) {
      state.stateModels.sources = Array.from({ length: 8 }, (_, index) => ({
        id: `model-${index}`,
        name: `model-${index}.json`,
        format: "json",
        text: '{"graph":{}}',
      }));
    }

    const html = renderStateModelsDetail(state);

    expect(html).toContain("8 state-model files");
    expect(html).toContain("These original files are used to create this preview");
    expect(html).toContain("Show 2 more files");
    expect(html).not.toContain('{"graph":{}}');
  });
});
