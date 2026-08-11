# TESTAR Trace Web Development Instructions

Read [../../AGENTS.md](../../AGENTS.md) for repository-wide architecture, terminology, dependency, validation, and completion requirements.

## Application Boundaries

- Keep the application entirely client-side unless explicitly requested otherwise.
- Keep canonical domain models, traceability methods, and analysis logic in `testar-trace`.
- Keep external-format parsing and conversion in `testar-trace-adapters`.
- Run the Python packages locally through Pyodide in a Web Worker. Do not reimplement traceability logic in TypeScript.
- Keep browser-specific user-interface, persistence, import/export, visualization, and workflow-orchestration logic in this application.
- Store lightweight analysis metadata in local storage and completed portable analysis data in IndexedDB. Surface persistence failures to the user.
- Keep imported data, configuration, history, and analysis results local to the browser unless the user explicitly exports them.
- Use Cytoscape for interactive state-model and traceability visualizations where appropriate.

## Development Rules

- Consult the version-matched Vite+ documentation under `node_modules/vite-plus/docs` before changing toolchain configuration.
- Keep long-running Python analysis outside the browser's main thread.
- Define explicit, typed, JSON-compatible messages between TypeScript and the Pyodide worker.
- Treat stored-data and exported-data format changes as deliberate compatibility changes.
- Keep `main.ts` focused on application orchestration. Put persistence, file handling, mapping, routing, graph rendering, reusable view rendering, and other independently testable responsibilities in named modules.
- Regenerate the Python runtime assets with `vp run prepare:python` or a script that invokes it; never edit generated wheels or runtime files manually.
- Validate file counts, file sizes, supported extensions, and import schema versions before expensive parsing or persistence.
- Escape every imported or user-provided value interpolated into HTML. Prefer `textContent` when updating dynamic DOM content directly.
- Add or update tests when user-visible behaviour, persistence, import/export, visualization, or worker communication changes.
- Preserve semantic structure, keyboard usability, focus management, reduced-motion behaviour, forced-colors support, touch targets, and visible focus when changing the interface. Do not use colour as the only status indicator.
- Reuse the established design tokens, component patterns, Lucide icon set, terminology, and copy style. Avoid one-off visual variants unless the interaction has a distinct meaning.
- Preserve the lazy state-model graph and worker boundaries; do not move Cytoscape, Pyodide, or analysis execution into the initial main-thread bundle without measured justification.

## Tests and Validation

- Use focused unit tests for deterministic logic and edge cases. Use browser tests for complete workflows; broad end-to-end coverage does not replace useful unit-level failure diagnostics.
- For applicable changes, run `vp check` and `vp run test:coverage`.
- For production code, dependencies, build configuration, workers, or static assets, also run `vp run build` and `vp run check:bundle`.
- For routing, persistence, import/export, source review, analysis execution, accessibility, or responsive-layout changes, run `vp run test:e2e`. If the production build is already current, `vp run test:e2e:prepared` may be used instead.
- Browser tests must run against the production preview and remain green in Chromium, Firefox, and WebKit. Keep the tested page free from horizontal document overflow at supported viewport widths.
- Treat automated accessibility checks as regression protection. Report when manual keyboard, screen-reader, zoom, forced-colors, reduced-motion, touch, or performance inspection could not be completed.

<!--VITE PLUS START-->

# Using Vite+, the Unified Toolchain for the Web

This project is using Vite+, a unified toolchain built on top of Vite, Rolldown, Vitest, tsdown, Oxlint, Oxfmt, and Vite Task. Vite+ wraps runtime management, package management, and frontend tooling in a single global CLI called `vp`. Vite+ is distinct from Vite, and it invokes Vite through `vp dev` and `vp build`. Run `vp help` to print a list of commands and `vp <command> --help` for information about a specific command.

Docs are local at `node_modules/vite-plus/docs` or online at https://viteplus.dev/guide/.

## Built-in Commands vs Scripts

`vp <name>` runs a built-in command. `vp run <name>` runs a `package.json` script or a `vite.config.ts` task. Scripts cannot overwrite built-ins, so `vp dev` and `vp run dev` may do different things. Check `package.json` and `vite.config.ts` first, and run `vp run <name>` when the project defines a script or task with that name.

## Review Checklist

- [ ] Run `vp install` after pulling remote changes and before getting started.
- [ ] Run `vp check` and `vp test` to format, lint, type check and test changes.
- [ ] Check if there are `vite.config.ts` tasks or `package.json` scripts necessary for validation, run via `vp run <script>`.
- [ ] If setup, runtime, or package-manager behavior looks wrong, run `vp env doctor` and include its output when asking for help.

<!--VITE PLUS END-->
