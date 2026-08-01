# I/O boundaries

## Purpose

ReqTrace keeps canonical result JSON load/save in the core package (`reqtrace.io`).

Interface-app-specific persistence concerns live in interface apps, not in the
core package.

## Current scope

- JSON serialization/deserialization for `TraceabilityResult` in `reqtrace.io`
- app-local result history or workspace state in interface apps

## Package structure

Core:

```text
src/reqtrace/io.py
```

Interface apps:

```text
apps/api/src/reqtrace_api/
apps/web/src/
```

## Design rules

- Keep adapters focused on I/O boundaries and persistence policy.
- Use atomic write patterns where practical.
- Raise public persistence errors from the core (`reqtrace.errors.PersistenceError`).
- Avoid embedding application orchestration logic in persistence modules.

