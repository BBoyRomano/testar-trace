# Documentation

This directory holds project-level documentation for ReqTrace.

## What lives here

- `architecture/`: current architecture and layer responsibilities
- `roadmap.md`: implementation roadmap by thesis phase
- `planning.md`: high-level DSRM timeline
- `archived-v0/`: legacy material kept only for historical context

## Reading order

1. `architecture/00-overview.md`
2. `architecture/01-domain-model.md`
3. `architecture/02-ingestion.md`
4. `architecture/03-trace-analysis.md`
5. `architecture/04-presentation.md`
6. `architecture/05-infrastructure.md`
7. `architecture/trace-methods/*.md` (method-specific details)

## Scope rule

Keep this folder focused on design and project-level planning.
Do not duplicate folder-level operational notes that already belong in:

- root `README.md` (setup + usage)
- `suts/README.md` and `suts/<sut>/README.md` (dataset/evidence policy)
- `tests/README.md` (test strategy)
