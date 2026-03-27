# Archived v0.x Implementation

This folder contains the original implementation before the architecture refactoring (v0.x).

## Contents

- `old-src/` - Legacy source code modules
  - `analysis/` - Old analysis algorithms (keyword_v1, path_occurrence_v1, etc.)
  - `export/` - Old export functionality (json_report.py)
  - `ingest/` - Old ingestion layer (requirements, state_models)
  - `ui/` - Old presentation UI code
- `tests/` - Original test suite for v0.x
- `architecture/` - Old architecture documentation
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
1. **Reference** - Implementation details and patterns for comparison
2. **Migration source** - Code to port to new architecture as needed
3. **History** - Full git history available via `git log`

## Note

The v0.x code is no longer active. All new development should target the new architecture layers:
- `src/reqtrace/ingestion/` - New ingestion layer
- `src/reqtrace/domain/` - New domain models
- `src/reqtrace/application/trace_analysis/` - New analysis engine
- `src/reqtrace/presentation/` - New presentation layer

See `docs/architecture/` for detailed architecture documentation (00-04).
