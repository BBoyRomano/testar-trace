import { describe, expect, it } from "vite-plus/test";

import { mapRequirements, mapStateModels } from "./mapping.ts";

const source = { id: "source-1", name: "input.json", format: "json", text: "{}" };

describe("canonical data mapping", () => {
  it("maps authored flows and branches without flattening their structure", () => {
    const bundle = mapRequirements({
      name: "Requirements",
      sourceKind: "files",
      adapterId: "use-case",
      sources: [source],
      data: {
        requirements: [
          {
            id: "REQ-1",
            title: "Log in",
            actor: "Student",
            scope: "Authentication",
            level: "user-goal",
            body: "The student authenticates.",
          },
        ],
        elements: [
          {
            id: "STEP-1",
            requirement_id: "REQ-1",
            kind: "step",
            text: "Submit",
            metadata: { source_keyword: "When" },
          },
        ],
        flows: [
          {
            id: "FLOW-1",
            requirement_id: "REQ-1",
            title: "Login",
            entry_node_id: "NODE-1",
            branches: [
              {
                id: "MAIN",
                title: "Main",
                kind: "main",
                entry_node_id: "NODE-1",
                resolution: "explicit",
              },
            ],
            nodes: [{ id: "NODE-1", branch_id: "MAIN", element_id: "STEP-1" }],
            edges: [],
          },
        ],
      },
    });

    expect(bundle.requirements[0]).toMatchObject({
      id: "REQ-1",
      body: "The student authenticates.",
      scope: "Authentication",
      level: "user-goal",
      elements: [{ id: "STEP-1", metadata: { source_keyword: "When" } }],
      flows: [{ id: "FLOW-1", branches: [{ id: "MAIN", kind: "main" }], edges: [] }],
    });
  });

  it("keeps states as nodes and transitions as direct graph edges", () => {
    const bundle = mapStateModels({
      name: "Models",
      adapterId: "testar",
      sources: [source],
      data: {
        id: "collection",
        title: "Models",
        models: [
          {
            id: "model-1",
            title: "Login model",
            layer: "mixed",
            source_ref: { source_name: "runs/login/model.json" },
            states: [
              {
                id: "STATE-1",
                title: "Login",
                url: "https://example.test/login",
                source_ref: { native_id: "SA-login", location: "ConcreteState[0]" },
              },
              { id: "STATE-2", title: "Dashboard" },
            ],
            actions: [{ id: "ACTION-1", description: "Submit" }],
            transitions: [
              {
                id: "TRANSITION-1",
                source_state_id: "STATE-1",
                action_id: "ACTION-1",
                target_state_id: "STATE-2",
              },
            ],
          },
        ],
      },
    });

    expect(bundle.models[0]?.graph.nodes).toHaveLength(2);
    expect(bundle.models[0]?.graph.nodes[0]).toMatchObject({
      label: "Login",
      shortId: "S01",
      title: "Login",
      url: "https://example.test/login",
    });
    expect(bundle.models[0]?.entities[0]).toMatchObject({
      nativeId: "SA-login",
      sourceLocation: "ConcreteState[0]",
    });
    expect(bundle.models[0]?.sourceName).toBe("model.json");
    expect(bundle.models[0]?.graph.edges).toEqual([
      {
        id: "TRANSITION-1",
        source: "STATE-1",
        target: "STATE-2",
        label: "Submit",
        actionId: "ACTION-1",
      },
    ]);
  });

  it("omits technical graph labels when the source has no meaningful page or action name", () => {
    const bundle = mapStateModels({
      name: "Models",
      adapterId: "testar",
      sources: [source],
      data: {
        id: "collection",
        title: "Models",
        models: [
          {
            id: "model-1",
            title: "Unlabelled model",
            layer: "mixed",
            states: [{ id: "STATE-1" }, { id: "STATE-2", name: "STATE-2" }],
            actions: [{ id: "ACTION-1" }],
            transitions: [
              {
                id: "TRANSITION-1",
                source_state_id: "STATE-1",
                action_id: "ACTION-1",
                target_state_id: "STATE-2",
              },
            ],
          },
        ],
      },
    });

    expect(bundle.models[0]?.graph.nodes[0]).toMatchObject({ label: "" });
    expect(bundle.models[0]?.graph.nodes[0]).not.toHaveProperty("title");
    expect(bundle.models[0]?.graph.nodes[1]).toMatchObject({ label: "" });
    expect(bundle.models[0]?.graph.edges[0]).toMatchObject({ label: "" });
  });
});
