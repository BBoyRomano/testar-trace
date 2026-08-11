import cytoscape, { type ElementDefinition, type StylesheetJson } from "cytoscape";

import { PATH_TONE_COUNT, pathHighlightColors } from "./path-colors.ts";
import { stateNodeDisplayName } from "./state-model-labels.ts";
import type { StateModel } from "./types.ts";

export interface StateModelGraphInput {
  model: StateModel;
  targetScores?: Map<string, number>;
  targetMarkers?: Map<string, string[]>;
  targetTones?: Map<string, number>;
  targetPriorities?: Map<string, number>;
  directTargets?: Set<string>;
}

export interface StateModelGraphController {
  readonly modelId: string;
  destroy(): void;
  fit(): void;
  resize(): void;
  updateEvidence(input: StateModelGraphInput): void;
  zoomIn(): void;
  zoomOut(): void;
}

export function mountStateModelGraph(
  input: StateModelGraphInput,
  container = document.querySelector<HTMLElement>("#state-model-graph"),
): StateModelGraphController | null {
  if (container === null) return null;
  if (input.model.graph.nodes.length === 0) {
    container.innerHTML = `<div class="empty-state"><strong>No graph nodes</strong><p>This state model has no graphable states.</p></div>`;
    return {
      modelId: input.model.id,
      destroy: () => container.replaceChildren(),
      fit: () => {},
      resize: () => {},
      updateEvidence: () => {},
      zoomIn: () => {},
      zoomOut: () => {},
    };
  }

  const graph = cytoscape({
    container,
    elements: graphElements(
      input.model,
      input.targetScores ?? new Map(),
      input.targetMarkers ?? new Map(),
      input.targetTones ?? new Map(),
      input.targetPriorities ?? new Map(),
      input.directTargets ?? new Set(),
    ),
    layout: {
      name: "breadthfirst",
      directed: true,
      padding: 48,
      spacingFactor: 1.32,
      avoidOverlap: true,
    },
    minZoom: 0.08,
    maxZoom: 3,
    style: graphStyle(),
  });

  const focusElement = (selected: cytoscape.SingularElementArgument): void => {
    const selectedCollection = graph.getElementById(selected.id());
    const neighborhood = selected.isNode()
      ? selectedCollection.closedNeighborhood()
      : selectedCollection.connectedNodes().union(selectedCollection);
    graph.elements().addClass("dimmed").removeClass("selected context");
    neighborhood.removeClass("dimmed");
    selected.addClass("selected");
    if (selected.isNode()) selected.connectedEdges().addClass("context");
  };
  const clearFocus = (): void => {
    graph.elements().removeClass("dimmed selected context");
  };
  const fit = (): void => {
    graph.fit(undefined, 36);
  };
  const zoomBy = (factor: number): void => {
    const level = Math.min(3, Math.max(0.08, graph.zoom() * factor));
    graph.zoom({
      level,
      renderedPosition: { x: container.clientWidth / 2, y: container.clientHeight / 2 },
    });
  };
  let resizeFrame = 0;
  const resizeObserver =
    typeof ResizeObserver === "undefined"
      ? null
      : new ResizeObserver(() => {
          if (container.clientWidth === 0 || container.clientHeight === 0) return;
          window.cancelAnimationFrame(resizeFrame);
          resizeFrame = window.requestAnimationFrame(() => {
            graph.resize();
            fit();
          });
        });
  resizeObserver?.observe(container);

  graph.on("tap", "node, edge", (event) => {
    focusElement(event.target);
  });
  graph.on("tap", (event) => {
    if (event.target === graph) {
      clearFocus();
    }
  });
  graph.on("mouseover", "edge", (event) => event.target.addClass("hovered"));
  graph.on("mouseout", "edge", (event) => event.target.removeClass("hovered"));
  window.setTimeout(fit);
  return {
    modelId: input.model.id,
    destroy: () => {
      resizeObserver?.disconnect();
      window.cancelAnimationFrame(resizeFrame);
      graph.destroy();
    },
    fit,
    resize: () => graph.resize(),
    updateEvidence: (nextInput) => {
      if (nextInput.model.id !== input.model.id) return;
      const nextElements = graphElements(
        nextInput.model,
        nextInput.targetScores ?? new Map(),
        nextInput.targetMarkers ?? new Map(),
        nextInput.targetTones ?? new Map(),
        nextInput.targetPriorities ?? new Map(),
        nextInput.directTargets ?? new Set(),
      );
      graph.batch(() => {
        for (const definition of nextElements) {
          const id = String(definition.data.id);
          const element = graph.getElementById(id);
          if (element.empty()) continue;
          element.removeData("displayLabel markerLabel score tone direct");
          element.data({
            displayLabel: definition.data.displayLabel,
            score: definition.data.score,
            tone: definition.data.tone,
            direct: definition.data.direct,
            ...(definition.data.markerLabel === undefined
              ? {}
              : { markerLabel: definition.data.markerLabel }),
          });
        }
      });
    },
    zoomIn: () => zoomBy(1.2),
    zoomOut: () => zoomBy(1 / 1.2),
  };
}

export function graphElements(
  model: StateModel,
  scores: Map<string, number>,
  markers: Map<string, string[]>,
  tones: Map<string, number>,
  priorities: Map<string, number>,
  directTargets: Set<string>,
): ElementDefinition[] {
  const markersFor = (keys: string[]): string[] => {
    const values = new Set<string>();
    for (const key of keys) {
      for (const marker of markers.get(key) ?? []) values.add(marker);
    }
    return [...values];
  };
  const evidence = (
    keys: string[],
  ): { score: number; tone: number; markers: string[]; direct: boolean } => {
    let score = 0;
    let preferred = { priority: Number.POSITIVE_INFINITY, tone: -1 };
    for (const key of keys) {
      score = Math.max(score, scores.get(key) ?? 0);
      const priority = priorities.get(key);
      if (priority !== undefined && priority < preferred.priority) {
        preferred = { priority, tone: tones.get(key) ?? -1 };
      }
    }
    return {
      score,
      tone: preferred.tone,
      markers: markersFor(keys),
      direct: keys.some((key) => directTargets.has(key)),
    };
  };
  const stateEvidence = (
    stateId: string,
  ): { score: number; tone: number; markers: string[]; direct: boolean } => {
    const directKeys = [
      `state:${stateId}`,
      ...model.entities
        .filter((entity) => entity.stateId === stateId && entity.kind === "widget")
        .map((entity) => `${entity.kind}:${entity.id}`),
    ];
    const match = evidence([
      `state-model:${model.id}`,
      ...directKeys,
      ...model.graph.edges
        .filter((edge) => edge.source === stateId || edge.target === stateId)
        .map((edge) => `transition:${edge.id}`),
    ]);
    return {
      ...match,
      markers: markersFor(directKeys),
      direct: directKeys.some((key) => directTargets.has(key)),
    };
  };
  return [
    ...model.graph.nodes.map((node) => {
      const match = stateEvidence(node.id);
      const markerLabel = formatMarkers(match.markers);
      const label = truncate(compactNodeLabel(node));
      return {
        data: {
          id: node.id,
          label,
          displayLabel: graphDisplayLabel(markerLabel, label),
          ...(markerLabel === "" ? {} : { markerLabel }),
          score: match.score,
          tone: match.tone,
          direct: match.direct ? "yes" : "no",
          initial: node.initial ? "yes" : "no",
        },
      };
    }),
    ...model.graph.edges.map((edge) => {
      const directKeys = [`transition:${edge.id}`];
      const match = {
        ...evidence([`state-model:${model.id}`, ...directKeys]),
        markers: markersFor(directKeys),
        direct: directKeys.some((key) => directTargets.has(key)),
      };
      const markerLabel = formatMarkers(match.markers);
      const label = truncate(compactActionLabel(edge), 56);
      return {
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label,
          displayLabel: graphDisplayLabel(markerLabel, label),
          ...(markerLabel === "" ? {} : { markerLabel }),
          score: match.score,
          tone: match.tone,
          direct: match.direct ? "yes" : "no",
        },
      };
    }),
  ];
}

function compactNodeLabel(node: StateModel["graph"]["nodes"][number]): string {
  return stateNodeDisplayName(node);
}

function compactActionLabel(edge: StateModel["graph"]["edges"][number]): string {
  const label = edge.label.trim();
  return label === edge.id || label === edge.actionId ? "" : label;
}

function graphDisplayLabel(markerLabel: string, sourceLabel: string): string {
  return [markerLabel, sourceLabel].filter((value) => value !== "").join(" · ");
}

function graphStyle(): StylesheetJson {
  const styles: StylesheetJson = [
    {
      selector: "node",
      style: {
        "background-color": "#eef2f7",
        "border-color": "#bcc7d5",
        "border-width": 1.5,
        color: "#344056",
        "font-family": "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        "font-size": 10.5,
        height: 34,
        label: "data(displayLabel)",
        "min-zoomed-font-size": 8,
        "overlay-opacity": 0,
        "text-background-color": "#ffffff",
        "text-background-opacity": 0.94,
        "text-background-padding": "4px",
        "text-margin-y": 3,
        "text-max-width": "150px",
        "text-valign": "bottom",
        "text-wrap": "ellipsis",
        "transition-duration": 160,
        "transition-property": "background-color, border-color, opacity",
        width: 34,
      },
    },
    {
      selector: "node[initial = 'yes']",
      style: {
        "border-color": "#56657c",
        "border-width": 3,
        height: 38,
        shape: "round-rectangle",
        width: 38,
      },
    },
    {
      selector: "edge",
      style: {
        "curve-style": "round-taxi",
        "taxi-direction": "downward",
        "taxi-turn": 18,
        "font-family": "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        "line-color": "#cdd5e1",
        "target-arrow-color": "#cdd5e1",
        "target-arrow-shape": "triangle",
        "arrow-scale": 0.85,
        "transition-duration": 160,
        "transition-property": "line-color, target-arrow-color, opacity, width",
        width: 1.5,
      },
    },
    {
      selector: "edge[score > 0], edge.context, edge.hovered, edge.selected",
      style: {
        label: "data(displayLabel)",
        color: "#344056",
        "font-size": 9,
        "font-weight": 600,
        "min-zoomed-font-size": 8,
        "text-background-color": "#ffffff",
        "text-background-opacity": 0.94,
        "text-background-padding": "4px",
        "text-background-shape": "roundrectangle",
        "text-border-color": "#d5dce7",
        "text-border-opacity": 1,
        "text-border-width": 1,
        "text-margin-y": -6,
        "text-max-width": "180px",
        "text-wrap": "ellipsis",
      },
    },
    {
      selector: "[markerLabel]",
      style: {
        "font-size": 9,
        "font-weight": 700,
        "min-zoomed-font-size": 8,
        "text-background-color": "#ffffff",
        "text-background-opacity": 1,
        "text-background-padding": "4px",
        "text-background-shape": "roundrectangle",
        "text-border-color": "#bcc7d5",
        "text-border-opacity": 1,
        "text-border-width": 1,
      },
    },
    {
      selector: "node[score > 0][tone = -1]",
      style: {
        "background-color": "#d7dee9",
        "border-color": "#475467",
      },
    },
    {
      selector: "edge[score > 0][tone = -1]",
      style: {
        "line-color": "#53627a",
        "target-arrow-color": "#53627a",
        width: 2.5,
      },
    },
    {
      selector: "edge[score > 0][direct = 'no']",
      style: { "line-style": "dashed", width: 2.5 },
    },
    {
      selector: "node[score > 0][direct = 'yes']",
      style: { "border-width": 4 },
    },
    {
      selector: "edge[score > 0][direct = 'yes']",
      style: { "line-style": "solid", width: 4 },
    },
    { selector: ".dimmed", style: { opacity: 0.14 } },
    {
      selector: ".selected",
      style: {
        "border-color": "#182033",
        "border-width": 3,
        opacity: 1,
        "z-index": 10,
        "overlay-color": "#3857d6",
        "overlay-opacity": 0.08,
        "overlay-padding": 6,
      },
    },
    {
      selector: "edge.selected",
      style: {
        width: 4,
      },
    },
  ];
  for (let tone = 0; tone < PATH_TONE_COUNT; tone += 1) {
    const colors = pathHighlightColors(tone);
    styles.push({
      selector: `node[score > 0][tone = ${tone}]`,
      style: {
        "background-color": colors.weak,
        "border-color": colors.border,
      },
    });
    styles.push({
      selector: `node[score > 0][direct = 'yes'][tone = ${tone}]`,
      style: {
        "background-color": colors.strong,
      },
    });
    styles.push({
      selector: `edge[score > 0][tone = ${tone}]`,
      style: {
        "line-color": colors.strong,
        "target-arrow-color": colors.strong,
      },
    });
    styles.push({
      selector: `[markerLabel][tone = ${tone}]`,
      style: {
        color: colors.border,
        "text-background-color": colors.labelBackground,
        "text-border-color": colors.weak,
      },
    });
  }
  return styles;
}

function truncate(value: string, maximumLength = 72): string {
  return value.length > maximumLength
    ? `${value.slice(0, Math.max(0, maximumLength - 3))}...`
    : value;
}

function formatMarkers(markers: string[]): string {
  if (markers.length === 0) return "";
  if (markers.length <= 3) return markers.join(" · ");
  return `${markers.slice(0, 3).join(" · ")} +${markers.length - 3}`;
}
