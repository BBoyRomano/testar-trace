import { describe, expect, it } from "vite-plus/test";

import { PATH_TONE_COUNT, pathHighlightColors, pathToneVariables } from "./path-colors.ts";

describe("path colors", () => {
  it("provides ten distinct theme-compatible categorical tones", () => {
    const colors = Array.from({ length: PATH_TONE_COUNT }, (_, index) =>
      pathHighlightColors(index),
    );

    expect(PATH_TONE_COUNT).toBe(10);
    expect(new Set(colors.map((color) => color.strong)).size).toBe(PATH_TONE_COUNT);
    expect(pathToneVariables(0)).toContain("--path-accent:#3857d6");
  });

  it("cycles deterministically after the supported palette", () => {
    expect(pathHighlightColors(PATH_TONE_COUNT)).toEqual(pathHighlightColors(0));
    expect(pathHighlightColors(-1)).toEqual(pathHighlightColors(PATH_TONE_COUNT - 1));
  });
});
