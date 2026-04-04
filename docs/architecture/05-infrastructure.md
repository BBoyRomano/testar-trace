# Infrastructure

## Purpose

The infrastructure layer provides technical adapters for persistence and serialization.

It keeps file-system and serialization concerns out of presentation and core method logic.

## Current scope

- JSON serialization/deserialization for `TraceabilityResult`
- JSON-backed repository for persisted GUI run history
- infrastructure-specific exception types for persistence/serialization failures

## Package structure

```text
src/reqtrace/infrastructure/
  exceptions.py
  serialization/
    traceability_report_json.py
  persistence/
    run_history_json.py
```

## Design rules

- Keep adapters focused on I/O boundaries.
- Use atomic write patterns where practical.
- Raise infrastructure-specific exceptions and let upper layers decide UX messaging.
- Avoid embedding application orchestration logic in infrastructure modules.
