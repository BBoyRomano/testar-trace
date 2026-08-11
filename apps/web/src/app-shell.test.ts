import { describe, expect, it, vi } from "vite-plus/test";

vi.mock("./icons.ts", () => ({
  icon: (name: string) => `<svg data-icon="${name}"></svg>`,
}));

import { renderAppShell } from "./app-shell.ts";

describe("application shell", () => {
  it("provides the persistent landmarks, actions, dialogs, and live region", () => {
    const html = renderAppShell();

    expect(html).toContain('<a class="skip-link" href="#view">');
    expect(html).toContain('<main id="view" class="main-content"></main>');
    expect(html).toContain('data-action="start-new-analysis"');
    expect(html).toContain('data-action="open-import-dialog"');
    expect(html).toContain('dialog id="help-dialog"');
    expect(html).toContain('dialog id="import-dialog"');
    expect(html).toContain('dialog id="confirmation-dialog"');
    expect(html).toContain('id="selection-announcer"');
  });

  it("keeps import privacy, file-format, and analysis copy internally consistent", () => {
    const html = renderAppShell();

    expect(html).toContain(
      "Files are processed locally in your browser and are not uploaded anywhere.",
    );
    expect(html).toContain(".testar-analysis.json for one analysis");
    expect(html).toContain(".testar-analyses.json for multiple analyses");
    expect(html).not.toContain("bulk export");
  });
});
