import { describe, expect, it } from "vite-plus/test";

import { stateNodeDisplayName } from "./state-model-labels.ts";

describe("state-model display labels", () => {
  it("keeps authored page titles", () => {
    expect(
      stateNodeDisplayName({
        id: "state-1",
        label: "Login Page",
        title: "Login Page",
        url: "https://example.test/application/login?error",
        initial: false,
      }),
    ).toBe("Login Page");
  });

  it("reduces URL labels to their page or view name", () => {
    expect(
      stateNodeDisplayName({
        id: "state-1",
        label: "https://example.test/application/teacher-view/overview?tab=active",
        initial: false,
      }),
    ).toBe("Overview");
  });

  it("uses the URL as a fallback for generic source labels", () => {
    expect(
      stateNodeDisplayName({
        id: "state-1",
        label: "State",
        url: "https://example.test/student-view",
        initial: false,
      }),
    ).toBe("Student view");
  });
});
