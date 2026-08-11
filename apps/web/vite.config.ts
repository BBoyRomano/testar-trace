import { defineConfig } from "vite-plus";

export default defineConfig({
  optimizeDeps: {
    exclude: ["pyodide"],
  },
  fmt: {},
  lint: {
    jsPlugins: [{ name: "vite-plus", specifier: "vite-plus/oxlint-plugin" }],
    rules: { "vite-plus/prefer-vite-plus-imports": "error" },
    options: { typeAware: true, typeCheck: true },
  },
  test: {
    include: ["src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.test.ts", "src/testing/**"],
      thresholds: {
        statements: 39,
        branches: 42,
        functions: 53,
        lines: 40,
      },
    },
  },
});
