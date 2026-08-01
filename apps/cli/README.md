# reqtrace-cli

Command-line interface for ReqTrace.

## Scope

This package provides a thin CLI over:

- `reqtrace` for analysis
- `reqtrace-adapters` for input loading

## Commands

- `reqtrace methods`
- `reqtrace formats`
- `reqtrace show-requirements --requirements ...`
- `reqtrace analyze --requirements ... --evidence ...`
- `reqtrace show-report report.json`

`analyze` defaults to:

- `--method noop`
- `--requirements-kind use-case`
- `--evidence-kind testar-state-model`

Use `--method sequence` to produce full and partial sequence matches between
requirement fragments and ordered execution evidence.

Use `--requirements-format`, `--evidence-format`, `--requirements-pattern`, and
`--requirements-recursive` when you need to be more explicit about input
loading.

## Output modes

- default human-readable text
- `--json` for machine-readable stdout
- `--summary-only` for compact summaries

The CLI is intentionally thin: it loads inputs with `reqtrace-adapters`, then
passes normalized models to `reqtrace.analyze_traceability`.

## Inspection

Inspect loaded requirements:

```bash
reqtrace show-requirements --requirements requirements --requirements-kind use-case --requirements-pattern "*.md"
```

Focus on one requirement:

```bash
reqtrace show-requirements --requirements requirements --requirements-kind use-case --requirements-pattern "*.md" --requirement-id application-login
```

Save a report, then inspect one requirement's sequences and alignments:

```bash
reqtrace analyze --requirements requirements --requirements-kind use-case --requirements-pattern "*.md" --evidence model.json --evidence-kind testar-state-model --method sequence --output report.json --summary-only
reqtrace show-report report.json --requirement-id application-login --with-occurrences --with-alignments --limit 5
```
