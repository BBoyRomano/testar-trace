import { describe, expect, it } from "vite-plus/test";

import {
  analysisImportOutcomeMessage,
  createPortableAnalysesBundle,
  createPortableAnalysisBundle,
  parseAnalysisFile,
  selectAnalysisImportFile,
} from "./result-files.ts";
import type { AnalysisResult, AnalysisRun } from "./types.ts";

const validResult = {
  schemaVersion: 1,
  id: "result-1",
  title: "Example analysis",
  methodId: "lexical",
  methodName: "Lexical",
  createdAt: "2026-08-03T10:00:00.000Z",
  requirementsName: "requirements.json",
  stateModelsName: "state-model.json",
  pathsExhaustive: true,
  paths: [],
  pathDiagnostics: [],
  assessments: [],
  links: [],
  occurrences: [],
  summary: {
    totalRequirements: 1,
    coveredRequirements: 1,
    partiallyCoveredRequirements: 0,
    uncoveredRequirements: 0,
    completeRequirements: 1,
    incompleteRequirements: 0,
    notAssessableRequirements: 0,
    totalPaths: 1,
    completePaths: 1,
    incompletePaths: 0,
    notAssessablePaths: 0,
    totalLinks: 2,
    totalOccurrences: 0,
    overallCoverageRatio: 1,
  },
} satisfies AnalysisResult;

describe("portable analysis bundles", () => {
  it("round-trips the result and both inspectable input snapshots", () => {
    const run = portableRun();
    const bundle = createPortableAnalysisBundle(run);
    const imported = parseAnalysisFile(JSON.stringify(bundle))[0]!;

    expect(imported.result).toEqual(validResult);
    expect(imported.requirements.requirements[0]?.title).toBe("Log in");
    expect(imported.requirements.sources[0]?.text).toBe("# Log in");
    expect(imported.stateModels.models[0]?.graph.nodes[0]?.label).toBe("Login");
    expect(imported.stateModels.sources[0]?.text).toBe('{"states":[]}');
  });

  it("round-trips a portable multi-analysis export", () => {
    const bundle = createPortableAnalysesBundle([portableRun()]);
    const imported = parseAnalysisFile(JSON.stringify(bundle));

    expect(bundle.kind).toBe("testar-trace-analyses");
    expect(imported).toHaveLength(1);
    expect(imported[0]?.analysis.title).toBe("Example analysis");
  });

  it("rejects result-only JSON", () => {
    expect(() => parseAnalysisFile(JSON.stringify(validResult))).toThrow(
      "not a supported TESTAR Trace analysis file",
    );
  });

  it("explains unsupported portable schema versions", () => {
    const bundle = { ...createPortableAnalysisBundle(portableRun()), schemaVersion: 99 };
    expect(() => parseAnalysisFile(JSON.stringify(bundle))).toThrow(
      "Analysis schema version 99 is not supported",
    );
  });
});

describe("selectAnalysisImportFile", () => {
  it("accepts exactly one portable analysis or analyses file", () => {
    const file = { name: "example.TESTAR-ANALYSIS.JSON" };
    expect(selectAnalysisImportFile([file])).toBe(file);
    expect(selectAnalysisImportFile([{ name: "example.testar-analyses.json" }]).name).toBe(
      "example.testar-analyses.json",
    );
  });

  it("rejects multiple files and non-JSON files", () => {
    expect(() => selectAnalysisImportFile([])).toThrow("one TESTAR Trace analysis file");
    expect(() => selectAnalysisImportFile([{ name: "one.json" }, { name: "two.json" }])).toThrow(
      "one TESTAR Trace analysis file",
    );
    expect(() => selectAnalysisImportFile([{ name: "analysis.json" }])).toThrow(
      ".testar-analysis.json or .testar-analyses.json file",
    );
  });

  it("rejects analysis files that exceed the import safety limit", () => {
    expect(() =>
      selectAnalysisImportFile([
        { name: "large.testar-analysis.json", size: 50 * 1024 * 1024 + 1 },
      ]),
    ).toThrow("50 MiB");
  });
});

describe("analysisImportOutcomeMessage", () => {
  it("distinguishes new, updated, and mixed imports", () => {
    expect(analysisImportOutcomeMessage(1, 0)).toBe("Analysis imported.");
    expect(analysisImportOutcomeMessage(1, 1)).toBe("Existing analysis updated.");
    expect(analysisImportOutcomeMessage(3, 1)).toBe("2 analyses imported · 1 updated.");
  });
});

function portableRun(): AnalysisRun {
  return {
    id: validResult.id,
    title: validResult.title,
    status: "complete",
    methodId: validResult.methodId,
    methodName: validResult.methodName,
    createdAt: validResult.createdAt,
    progress: 1,
    message: "Complete",
    result: validResult,
    requirements: {
      id: "requirements-1",
      name: "Requirements",
      sourceKind: "files",
      loadedAt: validResult.createdAt,
      adapterId: "use-case",
      sources: [
        { id: "requirement-source", name: "requirements.md", format: "md", text: "# Log in" },
      ],
      requirements: [
        {
          id: "REQ-1",
          title: "Log in",
          summary: "A user logs in",
          body: "A user logs in",
          actor: "User",
          scope: "Authentication",
          level: "user-goal",
          sourceName: "requirements.md",
          elements: [],
          flows: [],
        },
      ],
    },
    stateModels: {
      id: "models-1",
      name: "Models",
      loadedAt: validResult.createdAt,
      adapterId: "testar",
      sources: [
        {
          id: "model-source",
          name: "state-model.json",
          format: "json",
          text: '{"states":[]}',
        },
      ],
      models: [
        {
          id: "model-1",
          title: "Authentication",
          layer: "mixed",
          entities: [],
          graph: { nodes: [{ id: "state-1", label: "Login", initial: true }], edges: [] },
          counts: { state: 1, widget: 0, action: 0, transition: 0 },
        },
      ],
    },
  };
}
