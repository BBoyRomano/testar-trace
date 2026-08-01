# Repository structure

## Top-level layout

```text
packages/
  reqtrace/
    pyproject.toml
    src/reqtrace/
    tests/
  reqtrace-adapters/
    pyproject.toml
    src/reqtrace_adapters/
    tests/
  _archive/
    reqtrace-desktop-v0/
    reqtrace-v0/
    reqtrace-cli-v0/

apps/
  api/
    pyproject.toml
  cli/
    pyproject.toml
  web/

docs/
suts/
papers/
pyproject.toml
uv.lock
```

## Policy

- `packages/reqtrace` is the distributable core library.
- `packages/reqtrace-adapters` contains file-format and external-source adapters.
- `apps/*` are runnable interfaces with separate package metadata where needed.
- `apps/cli` publishes the `reqtrace-cli` distribution.
- `apps/api` publishes the `reqtrace-api` distribution.
- Keep web runtime/build dependencies isolated in `apps/web`.
- Keep one workspace lockfile (`uv.lock`) at repository root for active Python members.
- Keep the root `pyproject.toml` as workspace and tooling configuration, not a distributable package.
- Avoid coupling interface adapters back into the core package.
- Archived code under `packages/_archive` is reference-only and excluded from active tooling.

## Layering rules

- `reqtrace` must not import from adapter or app packages.
- `reqtrace-adapters` may import from `reqtrace` but not from app packages.
- Core package modules must not import from interface app packages.
- Public root modules remain a curated compatibility boundary over internal modules.

These boundaries should be enforced by package-local tests as the active packages mature.

## Naming rules

- Distribution names use hyphens, for example `reqtrace-adapters`.
- Import package names use underscores, for example `reqtrace_adapters`.
- App folders use short role names, for example `apps/cli`, while their Python
  project names remain publishable names such as `reqtrace-cli`.

## Workspace membership

The active uv workspace currently includes:

- `packages/reqtrace`
- `packages/reqtrace-adapters`
- `apps/cli`
- `apps/api`

The previous desktop app is archived under `packages/_archive/reqtrace-desktop-v0`
until a new desktop frontend is designed against the current API/package split.
