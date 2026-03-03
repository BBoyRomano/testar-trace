# Data

This directory contains research input artifacts used in this study.

## Structure

- [`stories/`](stories/) — Structured user stories (YAML or JSON)
- [`models/development/`](models/development/) — GUI State Models used during method development
- [`models/evaluation/`](models/evaluation/) — Frozen GUI State Models used for evaluation

## GUI State Models

GUI State Models are exported from TESTAR using the built-in JSON export functionality.

### File Naming Convention

`<SUT>-<phase>-<strategy>-v<version>.json`

Example:

`parabank-eval-llm-v1.json`

Exact configuration details for each model are documented in [`docs/experiment-configs/`](../docs/experiment-configs/).
