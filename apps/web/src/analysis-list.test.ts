import { describe, expect, it } from "vite-plus/test";

import {
  getAnalysisPage,
  nextDuplicateTitle,
  overallCompleteness,
  secondaryAnalysisActions,
} from "./analysis-list.ts";
import type { AnalysisRun } from "./types.ts";

const runs: [AnalysisRun, AnalysisRun, AnalysisRun] = [
  run("a", "Checkout", "lexical", "complete", "2026-08-01T10:00:00Z", 1, 0, 0),
  run("b", "Authentication", "noop", "failed", "2026-08-03T10:00:00Z"),
  run("c", "Enrollment", "lexical", "running", "2026-08-02T10:00:00Z"),
];

describe("analysis overview", () => {
  it("searches and filters across analysis metadata", () => {
    const page = getAnalysisPage(runs, {
      query: "check",
      status: "complete",
      methodId: "lexical",
      sort: "created-desc",
      page: 1,
      pageSize: 10,
    });
    expect(page.items.map((item) => item.id)).toEqual(["a"]);
    expect(page.filteredIds).toEqual(["a"]);
  });

  it("sorts completeness with unavailable values last", () => {
    const page = getAnalysisPage(runs, {
      query: "",
      status: "all",
      methodId: "all",
      sort: "completeness-desc",
      page: 1,
      pageSize: 10,
    });
    expect(page.items.map((item) => item.id)).toEqual(["a", "b", "c"]);
    expect(overallCompleteness(runs[0])).toBe(1);
    expect(overallCompleteness(runs[1])).toBeNull();
    expect(
      overallCompleteness(
        run("na", "Not assessable", "lexical", "complete", "2026-08-04T10:00:00Z", 0, 0, 1),
      ),
    ).toBeNull();
    expect(
      overallCompleteness(
        run("i", "Incomplete", "sequence", "complete", "2026-08-04T10:00:00Z", 0, 2, 0),
      ),
    ).toBe(0);
  });

  it("clamps pagination and reports the visible range", () => {
    const page = getAnalysisPage(runs, {
      query: "",
      status: "all",
      methodId: "all",
      sort: "created-desc",
      page: 8,
      pageSize: 2,
    });
    expect(page).toMatchObject({ page: 2, totalPages: 2, start: 3, end: 3, totalItems: 3 });
  });

  it("keeps the primary row action visible and moves secondary actions into the menu", () => {
    expect(secondaryAnalysisActions(runs[2])).toEqual(["rename", "duplicate", "export", "delete"]);
    expect(secondaryAnalysisActions(runs[1])).toEqual(["rename", "delete"]);
    expect(secondaryAnalysisActions(runs[0])).toEqual(["rename", "duplicate", "export", "delete"]);
    expect(secondaryAnalysisActions(runs[1], true)).toEqual([
      "rename",
      "duplicate",
      "export",
      "delete",
    ]);
  });

  it("numbers duplicate titles without nesting copy suffixes", () => {
    const titles = ["Checkout", "Checkout (copy)", "Checkout (copy 2)"];
    expect(nextDuplicateTitle("Checkout", titles)).toBe("Checkout (copy 3)");
    expect(nextDuplicateTitle("Checkout (copy)", titles)).toBe("Checkout (copy 3)");
    expect(nextDuplicateTitle("Checkout (copy 2)", titles)).toBe("Checkout (copy 3)");
    expect(nextDuplicateTitle("Enrollment", titles)).toBe("Enrollment (copy)");
  });
});

function run(
  id: string,
  title: string,
  methodId: string,
  status: AnalysisRun["status"],
  createdAt: string,
  completeRequirements = 0,
  incompleteRequirements = 0,
  notAssessableRequirements = 0,
): AnalysisRun {
  const value: AnalysisRun = {
    id,
    title,
    methodId,
    methodName: methodId === "lexical" ? "Lexical" : "No-op",
    status,
    createdAt,
    progress: status === "complete" ? 1 : 0.3,
    message: "",
    result: null,
    requirements: null,
    stateModels: null,
  };
  if (status === "complete") {
    const totalRequirements =
      completeRequirements + incompleteRequirements + notAssessableRequirements;
    value.result = {
      summary: {
        totalRequirements,
        completeRequirements,
        incompleteRequirements,
        notAssessableRequirements,
      },
    } as AnalysisRun["result"];
  }
  return value;
}
