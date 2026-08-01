import cytoscape, { type ElementDefinition } from "cytoscape";

import type { EvidenceBundle, ScenarioCoverage, SequenceStep } from "./types";

export function mountEvidenceGraph(evidence: EvidenceBundle): () => void {
  const container = document.querySelector<HTMLElement>("#evidence-graph");
  if (container === null) {
    return () => {};
  }

  if (evidence.graph.nodes.length === 0) {
    container.innerHTML = `<div class="empty-state"><strong>No graph nodes</strong><p>The loaded evidence does not expose graphable states or actions.</p></div>`;
    return () => {
      container.replaceChildren();
    };
  }

  const graph = cytoscape({
    container,
    elements: graphElements(evidence),
    layout: {
      name: "breadthfirst",
      directed: true,
      padding: 34,
      spacingFactor: 1.15,
      avoidOverlap: true,
    },
    minZoom: 0.12,
    maxZoom: 2.4,
    wheelSensitivity: 0.18,
    style: graphStyle(),
  });

  graph.on("tap", "node, edge", (event) => {
    const selected = event.target;
    const neighborhood = selected.isNode()
      ? selected.closedNeighborhood()
      : selected.connectedNodes().union(selected);
    graph.elements().addClass("dimmed").removeClass("selected");
    neighborhood.removeClass("dimmed").addClass("selected");
  });

  graph.on("tap", (event) => {
    if (event.target === graph) {
      graph.elements().removeClass("dimmed selected");
    }
  });

  window.setTimeout(() => graph.fit(undefined, 34));

  return () => {
    graph.destroy();
  };
}

export function mountSequenceEvidenceGraph(input: {
  evidence: EvidenceBundle;
  scenario: ScenarioCoverage;
  selectedStepId: string;
  onSelectStep: (stepId: string) => void;
}): () => void {
  const container = document.querySelector<HTMLElement>("#sequence-evidence-graph");
  if (container === null) {
    return () => {};
  }

  const elements = sequenceGraphElements(input.evidence, input.scenario);
  if (elements.length === 0) {
    container.innerHTML = `<div class="empty-state"><strong>No matched evidence path</strong><p>The selected scenario has no matched evidence sequence.</p></div>`;
    return () => {
      container.replaceChildren();
    };
  }

  const graph = cytoscape({
    container,
    elements,
    layout: {
      name: "breadthfirst",
      directed: true,
      padding: 28,
      spacingFactor: 1.18,
      avoidOverlap: true,
    },
    minZoom: 0.16,
    maxZoom: 2.8,
    wheelSensitivity: 0.18,
    style: graphStyle(),
  });

  graph.on("tap", "node, edge", (event) => {
    const stepId = event.target.data("stepId") as string | undefined;
    if (stepId !== undefined && stepId.length > 0) {
      input.onSelectStep(stepId);
    }
  });

  highlightSequenceStep(graph, input.selectedStepId);
  window.setTimeout(() => graph.fit(undefined, 26));

  return () => {
    graph.destroy();
  };
}

function graphElements(evidence: EvidenceBundle): ElementDefinition[] {
  return [
    ...evidence.graph.nodes.map((node) => ({
      data: {
        id: node.id,
        kind: node.kind,
        label: truncate(node.label || node.id),
      },
    })),
    ...evidence.graph.edges.map((edge) => ({
      data: {
        id: edge.id,
        kind: edge.kind,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        transitionId: edge.transitionId,
      },
    })),
  ];
}

function sequenceGraphElements(
  evidence: EvidenceBundle,
  scenario: ScenarioCoverage,
): ElementDefinition[] {
  const matchedSteps = scenario.sequence.filter((step) => step.matched);
  const stepByEvidenceId = stepEvidenceMap(matchedSteps);
  const nodeIds = new Set<string>();
  const transitionIds = new Set<string>();

  for (const step of matchedSteps) {
    for (const ref of stepRefs(step)) {
      if (ref.kind === "state" || ref.kind === "action") {
        nodeIds.add(ref.evidenceId);
      }
      if (ref.kind === "transition") {
        transitionIds.add(ref.evidenceId);
      }
    }
  }

  const edges = evidence.graph.edges.filter(
    (edge) =>
      transitionIds.has(edge.transitionId) || nodeIds.has(edge.source) || nodeIds.has(edge.target),
  );
  for (const edge of edges) {
    nodeIds.add(edge.source);
    nodeIds.add(edge.target);
  }

  return [
    ...evidence.graph.nodes
      .filter((node) => nodeIds.has(node.id))
      .map((node) => ({
        data: {
          id: node.id,
          kind: node.kind,
          label: truncate(node.label || node.id),
          stepId: stepByEvidenceId.get(node.id) ?? "",
        },
        classes: stepByEvidenceId.has(node.id) ? "matched" : "",
      })),
    ...edges.map((edge) => ({
      data: {
        id: edge.id,
        kind: edge.kind,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        transitionId: edge.transitionId,
        stepId: stepByEvidenceId.get(edge.transitionId) ?? "",
      },
      classes: stepByEvidenceId.has(edge.transitionId) ? "matched" : "",
    })),
  ];
}

function stepEvidenceMap(steps: SequenceStep[]): Map<string, string> {
  const map = new Map<string, string>();
  for (const step of steps) {
    for (const ref of stepRefs(step)) {
      if (!map.has(ref.evidenceId)) {
        map.set(ref.evidenceId, step.fragmentId);
      }
    }
  }
  return map;
}

function stepRefs(step: SequenceStep): SequenceStep["evidenceRefs"] {
  const refs = Array.isArray(step.evidenceRefs) ? step.evidenceRefs : [];
  return refs.length > 0 ? refs : [{ kind: step.evidenceKind, evidenceId: step.evidenceId }];
}

function highlightSequenceStep(graph: cytoscape.Core, selectedStepId: string): void {
  graph.elements().removeClass("selected dimmed");
  if (selectedStepId === "") {
    return;
  }
  const selected = graph.elements().filter((element) => element.data("stepId") === selectedStepId);
  if (selected.empty()) {
    return;
  }
  graph.elements().addClass("dimmed");
  selected
    .union(selected.connectedNodes())
    .union(selected.connectedEdges())
    .removeClass("dimmed")
    .addClass("selected");
  graph.animate({
    center: { eles: selected },
    duration: 180,
  });
}

function graphStyle(): cytoscape.StylesheetJson {
  return [
    {
      selector: "node",
      style: {
        "background-color": "#8fb8ff",
        "border-color": "#b9d1ff",
        "border-width": 1,
        color: "#eef3f8",
        "font-size": 10,
        height: 28,
        label: "data(label)",
        "min-zoomed-font-size": 8,
        "overlay-opacity": 0,
        "text-background-color": "#151b23",
        "text-background-opacity": 0.86,
        "text-background-padding": "3px",
        "text-max-width": "120px",
        "text-valign": "bottom",
        "text-wrap": "ellipsis",
        width: 28,
      },
    },
    {
      selector: "node[kind = 'action']",
      style: {
        "background-color": "#80c99b",
        shape: "round-rectangle",
        height: 20,
        width: 44,
      },
    },
    {
      selector: "edge",
      style: {
        "curve-style": "bezier",
        "line-color": "#3c4a59",
        "target-arrow-color": "#3c4a59",
        "target-arrow-shape": "triangle",
        width: 1.4,
      },
    },
    {
      selector: ".matched",
      style: {
        "border-color": "#d8b56b",
        "border-width": 2,
        "line-color": "#d8b56b",
        "target-arrow-color": "#d8b56b",
      },
    },
    {
      selector: ".dimmed",
      style: {
        opacity: 0.18,
      },
    },
    {
      selector: ".selected",
      style: {
        "background-color": "#d8b56b",
        "border-color": "#f0d38e",
        "line-color": "#d8b56b",
        "target-arrow-color": "#d8b56b",
        opacity: 1,
        "z-index": 10,
      },
    },
    {
      selector: "edge.selected",
      style: {
        label: "data(transitionId)",
        "font-size": 9,
        "text-background-color": "#151b23",
        "text-background-opacity": 0.9,
        "text-background-padding": "3px",
        width: 3,
      },
    },
  ];
}

function truncate(value: string): string {
  return value.length > 80 ? `${value.slice(0, 77)}...` : value;
}
