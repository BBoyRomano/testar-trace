import { describe, expect, it } from "vite-plus/test";

import { parseRoute, routePath } from "./routes.ts";

describe("application routes", () => {
  it("maps each screen to a stable path", () => {
    expect(routePath("analyses")).toBe("/analyses");
    expect(routePath("new-analysis")).toBe("/analyses/new");
    expect(routePath("requirements")).toBe("/analyses/new/requirements");
    expect(routePath("state-models")).toBe("/analyses/new/state-models");
    expect(routePath("result", "analysis/1")).toBe("/analyses/analysis%2F1");
  });

  it("parses routes and tolerates a trailing slash", () => {
    expect(parseRoute("/analyses/")).toEqual({ view: "analyses" });
    expect(parseRoute("/analyses/new/requirements")).toEqual({ view: "requirements" });
    expect(parseRoute("/analyses/analysis%2F1")).toEqual({
      view: "result",
      runId: "analysis/1",
    });
  });

  it("rejects unknown and malformed paths", () => {
    expect(parseRoute("/")).toBeNull();
    expect(parseRoute("/unknown")).toBeNull();
    expect(parseRoute("/analyses/%E0%A4%A")).toBeNull();
  });
});
