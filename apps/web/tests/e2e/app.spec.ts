import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const requirementFile = fileURLToPath(
  new URL(
    "../../../../benchmarks/tbuis/requirements/use-cases/uc-01-application-login.md",
    import.meta.url,
  ),
);
const stateModelFile = fileURLToPath(
  new URL("../../../../benchmarks/tbuis/evidence/uc-01.json", import.meta.url),
);

async function expectNoAutomaticAccessibilityViolations(page: Page): Promise<void> {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(result.violations).toEqual([]);
}

async function waitForFileSupport(page: Page): Promise<void> {
  await expect(page.getByLabel("Traceability method")).toBeEnabled({ timeout: 30_000 });
}

async function expectNoHorizontalPageOverflow(page: Page): Promise<void> {
  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);
}

test("runs, reviews, persists, exports, and imports an analysis", async ({ page }) => {
  await page.goto("/analyses");
  const emptyState = page.getByLabel("No analyses yet");
  await expect(emptyState.getByRole("heading", { name: "No analyses yet" })).toBeVisible();
  await emptyState.getByRole("button", { name: "New analysis" }).click();
  await waitForFileSupport(page);

  await page.locator("#requirements-file-input").setInputFiles(requirementFile);
  const requirements = page.getByRole("region", { name: "Requirements" });
  await expect(requirements.getByText("1 requirement loaded.")).toBeVisible();
  await requirements.getByRole("button", { name: "Review requirements" }).click();
  await expect(page).toHaveURL(/\/analyses\/new\/requirements$/);
  await expect(page.getByRole("heading", { name: "Review requirements" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Application login" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);
  await page.getByRole("link", { name: "Back to new analysis" }).click();

  await page.locator("#state-model-file-input").setInputFiles(stateModelFile);
  const stateModels = page.getByRole("region", { name: "State models" });
  await expect(stateModels.getByText("1 state model with 17 states loaded.")).toBeVisible();
  await stateModels.getByRole("button", { name: "Review state models" }).click();
  await expect(page).toHaveURL(/\/analyses\/new\/state-models$/);
  await expect(page.getByRole("heading", { name: "Review state models" })).toBeVisible();
  await expect(page.getByLabel(/State-model graph for/)).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);
  await page.getByRole("link", { name: "Back to new analysis" }).click();
  await expectNoAutomaticAccessibilityViolations(page);

  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page).toHaveURL(/\/analyses\/[^/]+$/);
  await expect(page.getByText("Finished", { exact: true })).toBeVisible({ timeout: 60_000 });
  const title = await page.getByRole("heading", { level: 1 }).textContent();
  expect(title).toBeTruthy();
  await expect(page.getByRole("region", { name: "Analysis summary" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);

  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title ?? "");
  await expect(page.getByText("Finished", { exact: true })).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export analysis" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.testar-analysis\.json$/);
  const exportedFile = await download.path();
  expect(exportedFile).not.toBeNull();

  await page.getByRole("banner").getByRole("button", { name: "Import analysis" }).click();
  await page.locator("#import-file-input").setInputFiles({
    name: download.suggestedFilename(),
    mimeType: "application/json",
    buffer: await readFile(exportedFile ?? ""),
  });
  await expect(page.getByText("Existing analysis updated.")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expectNoHorizontalPageOverflow(page);
  await expectNoAutomaticAccessibilityViolations(page);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.getByRole("link", { name: "Go to analyses" }).click();
  await expect(page.getByRole("table", { name: "Saved traceability analyses" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);
  await page.getByRole("checkbox", { name: `Select ${title ?? "analysis"}` }).check();
  await expect(page.getByRole("region", { name: "Selected analysis actions" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);
});

test("keeps empty, creation, and dialog surfaces accessible", async ({ page }) => {
  const pythonRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/python/")) pythonRequests.push(request.url());
  });
  await page.goto("/analyses");
  await expectNoAutomaticAccessibilityViolations(page);

  await page.getByRole("button", { name: "Open help" }).click();
  await expect(page.getByRole("dialog", { name: "Using TESTAR Trace" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);
  await page.getByRole("button", { name: "Close help" }).click();

  await page.getByRole("banner").getByRole("button", { name: "Import analysis" }).click();
  await expect(page.getByRole("dialog", { name: "Import analysis" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);
  await page.locator("#import-file-input").setInputFiles({
    name: "invalid.testar-analysis.json",
    mimeType: "application/json",
    buffer: Buffer.from("not valid JSON"),
  });
  await expect(page.getByText("The selected analysis file is not valid JSON.")).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Import analysis" })).toBeVisible();
  await expectNoAutomaticAccessibilityViolations(page);

  await page.locator("#import-file-input").setInputFiles({
    name: "future.testar-analysis.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify({ kind: "testar-trace-analysis", schemaVersion: 99 })),
  });
  await expect(page.getByText(/Analysis schema version 99 is not supported/)).toBeVisible();
  await page.getByRole("button", { name: "Close import dialog" }).click();
  expect(pythonRequests).toEqual([]);

  await page.getByRole("banner").getByRole("button", { name: "New analysis" }).click();
  await waitForFileSupport(page);
  expect(pythonRequests.length).toBeGreaterThan(0);
  await expectNoAutomaticAccessibilityViolations(page);

  for (const width of [320, 620, 900, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByRole("heading", { name: "New analysis" })).toBeVisible();
    await expectNoHorizontalPageOverflow(page);
  }
});

test("supports direct SPA routes and recovers unknown routes", async ({ page }) => {
  await page.goto("/analyses/new");
  await expect(page.getByRole("heading", { name: "New analysis" })).toBeVisible();

  await page.goto("/not-a-route");
  await expect(page).toHaveURL(/\/analyses$/);
  await expect(page.getByRole("heading", { name: "Analyses", exact: true })).toBeVisible();
});
