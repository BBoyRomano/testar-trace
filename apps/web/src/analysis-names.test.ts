import { describe, expect, it } from "vite-plus/test";

import { analysisExportFileName, suggestedAnalysisName } from "./analysis-names.ts";

describe("suggestedAnalysisName", () => {
  it("describes the analyzed content instead of its source files", () => {
    expect(suggestedAnalysisName({ requirementCount: 22, stateModelCount: 4 })).toBe(
      "22 requirements · 4 state models",
    );
  });

  it("uses correct singular labels", () => {
    expect(suggestedAnalysisName({ requirementCount: 1, stateModelCount: 1 })).toBe(
      "1 requirement · 1 state model",
    );
  });

  it("keeps useful placeholders while an input is missing", () => {
    expect(suggestedAnalysisName({ requirementCount: 22 })).toBe("22 requirements · state models");
    expect(suggestedAnalysisName({ stateModelCount: 4 })).toBe("Requirements · 4 state models");
    expect(suggestedAnalysisName()).toBe("Untitled analysis");
  });
});

describe("analysisExportFileName", () => {
  it("derives a filesystem-safe export name from the visible analysis name", () => {
    expect(analysisExportFileName("22 requirements · 4 state models")).toBe(
      "22-requirements-4-state-models.testar-analysis.json",
    );
  });

  it("normalizes custom names and keeps a useful fallback", () => {
    expect(analysisExportFileName("  TBUIS — Completeness  ")).toBe(
      "tbuis-completeness.testar-analysis.json",
    );
    expect(analysisExportFileName("---")).toBe("analysis.testar-analysis.json");
  });
});
