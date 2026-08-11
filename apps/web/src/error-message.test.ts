import { describe, expect, it } from "vite-plus/test";

import { userFacingErrorMessage } from "./error-message.ts";

describe("userFacingErrorMessage", () => {
  it("keeps useful Error and string messages", () => {
    expect(userFacingErrorMessage(new Error("The file is invalid."))).toBe("The file is invalid.");
    expect(userFacingErrorMessage(" Import cancelled. ")).toBe("Import cancelled.");
  });

  it("reads message properties from serialized errors", () => {
    expect(userFacingErrorMessage({ message: "The worker stopped." })).toBe("The worker stopped.");
  });

  it("replaces empty and object-string messages with contextual fallback copy", () => {
    const fallback = "File support could not be prepared. Reload the page and try again.";
    expect(userFacingErrorMessage({}, fallback)).toBe(fallback);
    expect(userFacingErrorMessage(new Error("[object Object]"), fallback)).toBe(fallback);
    expect(userFacingErrorMessage(new Error("Program terminated with exit(1)"), fallback)).toBe(
      fallback,
    );
    expect(userFacingErrorMessage("   ", fallback)).toBe(fallback);
  });
});
