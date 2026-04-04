# Archived v0.x Implementation

This folder contains the original implementation before the architecture refactoring (v0.x).

## Contents

- `architecture/` - Old architecture documentation snapshots
  - `analysis-approaches.md` - Old analysis approaches
  - `analyzers.md` - Old analyzer documentation
  - `architecture.md` - Old architecture overview
  - `architecture.old.md` - Previous architecture version
  - `phases.md` - Old development phases
  - `phases.old.md` - Previous phases documentation
  - `trace-results.md` - Old trace results documentation
  - `v1.md` - Old v1 architecture
  - `v1.old.md` - Previous v1 documentation

## Purpose

This archive serves as:
1. **Reference** - Historical architecture decisions and terminology
2. **History** - Earlier design snapshots while the new layered architecture stabilized
3. **Context** - Supporting material when comparing thesis write-up revisions

## Note

The v0.x code is no longer active and is not authoritative for current development.
All new development should target the current architecture layers:
- `src/reqtrace/ingestion/` - New ingestion layer
- `src/reqtrace/domain/` - New domain models
- `src/reqtrace/application/` - New application services and methods
- `src/reqtrace/infrastructure/` - Persistence and serialization adapters
- `src/reqtrace/presentation/` - New presentation layer

See `docs/architecture/` for the authoritative architecture documentation set (00-05).
