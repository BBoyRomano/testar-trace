# Architecture overview

## Purpose

ReqTrace ingests requirements and testing evidence, executes a traceability method, and returns structured results.

## End-to-end flow

```text
requirements/evidence inputs
-> adapter loaders + normalization
-> core model snapshots
-> traceability method execution
-> result model
-> interface adapters (CLI/API/Web)
```

## Core layers (`packages/reqtrace/src/reqtrace/`)

### Models

Stable source-agnostic concepts for requirements, evidence, and traceability.

### Traceability

Method contracts, built-in methods, method registry, progress reporting, and analysis orchestration.

### Public API

Small root exports for common library use, with deeper modules available for advanced use.

## Adapter package (`packages/reqtrace-adapters/src/reqtrace_adapters/`)

Source-specific parsing, validation, loading, and normalization into core `reqtrace` models.

## Interface apps (`apps/`)

- `apps/cli` (`reqtrace-cli`)
- `apps/api` (`reqtrace-api`)
- `apps/web` (`reqtrace-web`)

## Repository map

```text
docs/
packages/reqtrace/
packages/reqtrace-adapters/
packages/_archive/
apps/cli/
apps/api/
apps/web/
packages/reqtrace/tests/
packages/reqtrace-adapters/tests/
apps/cli/tests/
```

