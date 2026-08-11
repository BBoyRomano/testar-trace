import { describe, expect, it } from "vite-plus/test";

import { graphElements } from "./state-model-graph.ts";
import type { StateModel } from "./types.ts";

describe("state-model path highlighting", () => {
  it("keeps the branch node in the main color and colors alternative arrows and targets", () => {
    const elements = graphElements(
      model,
      new Map([
        ["transition:main-edge", 0.6],
        ["transition:alternative-edge", 0.9],
      ]),
      new Map([
        ["transition:main-edge", ["3"]],
        ["transition:alternative-edge", ["4"]],
      ]),
      new Map([
        ["transition:main-edge", 0],
        ["transition:alternative-edge", 1],
      ]),
      new Map([
        ["transition:main-edge", 0],
        ["transition:alternative-edge", 1],
      ]),
      new Set(["transition:main-edge", "transition:alternative-edge"]),
    );

    expect(data(elements, "branch")).toMatchObject({ tone: 0, score: 0.9 });
    expect(data(elements, "main-edge")).toMatchObject({
      tone: 0,
      score: 0.6,
      markerLabel: "3",
      displayLabel: "3 · Continue",
      direct: "yes",
    });
    expect(data(elements, "alternative-edge")).toMatchObject({
      tone: 1,
      score: 0.9,
      markerLabel: "4",
      displayLabel: "4 · Branch",
      direct: "yes",
    });
    expect(data(elements, "alternative-target")).toMatchObject({ tone: 1, score: 0.9 });
    expect(data(elements, "branch")).not.toHaveProperty("markerLabel");
    expect(data(elements, "branch")).toMatchObject({ direct: "no" });
    expect(data(elements, "alternative-target")).not.toHaveProperty("markerLabel");
    expect(data(elements, "alternative-target")).toMatchObject({ direct: "no" });
  });

  it("numbers a state when the resolved completeness step directly matches that state", () => {
    const elements = graphElements(
      model,
      new Map([["state:alternative-target", 0.8]]),
      new Map([["state:alternative-target", ["Pre", "2", "Post"]]]),
      new Map([["state:alternative-target", 1]]),
      new Map([["state:alternative-target", 1]]),
      new Set(["state:alternative-target"]),
    );

    expect(data(elements, "alternative-target")).toMatchObject({
      tone: 1,
      score: 0.8,
      markerLabel: "Pre · 2 · Post",
      displayLabel: "Pre · 2 · Post · Alternative step",
      direct: "yes",
    });
  });

  it("shows a requirement marker without inventing a label for an unnamed state", () => {
    const unnamedModel: StateModel = {
      ...model,
      graph: {
        nodes: [{ id: "unnamed", label: "", initial: true }],
        edges: [],
      },
    };
    const elements = graphElements(
      unnamedModel,
      new Map([["state:unnamed", 0.75]]),
      new Map([["state:unnamed", ["1"]]]),
      new Map([["state:unnamed", 0]]),
      new Map([["state:unnamed", 0]]),
      new Set(["state:unnamed"]),
    );

    expect(data(elements, "unnamed")).toMatchObject({
      label: "",
      markerLabel: "1",
      displayLabel: "1",
      direct: "yes",
    });
  });

  it("removes legacy technical prefixes from source page labels", () => {
    const legacyModel: StateModel = {
      ...model,
      graph: {
        nodes: [{ id: "login", label: "S01 · Login Page", initial: true }],
        edges: [],
      },
    };

    const elements = graphElements(
      legacyModel,
      new Map(),
      new Map(),
      new Map(),
      new Map(),
      new Set(),
    );

    expect(data(elements, "login")).toMatchObject({
      label: "Login Page",
      displayLabel: "Login Page",
    });
  });
});

const model: StateModel = {
  id: "model",
  title: "Branching model",
  layer: "mixed",
  entities: [],
  counts: { state: 3, widget: 0, action: 0, transition: 2 },
  graph: {
    nodes: [
      { id: "branch", label: "Step 3", initial: false },
      { id: "main-target", label: "Step 4", initial: false },
      { id: "alternative-target", label: "Alternative step", initial: false },
    ],
    edges: [
      {
        id: "main-edge",
        source: "branch",
        target: "main-target",
        label: "Continue",
        actionId: "continue",
      },
      {
        id: "alternative-edge",
        source: "branch",
        target: "alternative-target",
        label: "Branch",
        actionId: "branch",
      },
    ],
  },
};

function data(
  elements: ReturnType<typeof graphElements>,
  id: string,
): Record<string, unknown> | undefined {
  return elements.find((element) => element.data.id === id)?.data;
}
