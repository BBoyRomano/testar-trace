# Presentation

## Purpose

The presentation layer handles user interaction for configuring runs, executing methods, and inspecting/sharing results.

It includes a CLI and a local Tkinter GUI.

## Boundaries

Presentation is responsible for:

- collecting user input (requirements, evidence, method)
- invoking application-layer use-cases
- rendering run summaries and requirement-level outcomes
- initiating JSON import/export actions

Presentation is not responsible for:

- source parsing and ingestion validation internals
- traceability scoring/method logic
- persistence adapter implementation

## Package structure

```text
src/reqtrace/presentation/
  exceptions.py
  runtime.py
  cli/
    main.py
    rendering.py
  gui/
    app.py
    controller.py
    views.py
```

`runtime.py` is the shared bridge for CLI/GUI request building and execution wiring.

## CLI

Primary commands:

- `reqtrace methods`
- `reqtrace formats`
- `reqtrace run`
- `reqtrace show-result`
- `reqtrace ui`

`reqtrace run` supports one or many `--requirements` paths, including directories.

## GUI

Current GUI behavior:

- start multiple runs
- immediate run enqueue/focus in history with async preparation state
- live in-flight run progress (per-requirement status and aggregate progress)
- cooperative cancellation for queued and running jobs
- import and export JSON results
- delete local history entries
- inspect run summary and per-requirement outcomes
- persist run history across sessions using local storage (`.reqtrace/gui-history`)

Concurrency and run events are handled by an application-level async executor.
For GUI responsiveness during CPU-heavy methods, analysis execution runs in
process workers (spawn backend), while the Tk main loop stays interactive.

## Import/export

Result import/export uses JSON serialization of `TraceabilityResult` through application and infrastructure boundaries.

This keeps sharing/reproducibility simple and local-first.
