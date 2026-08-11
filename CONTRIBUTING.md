# Contributing to TESTAR Trace

## Before changing code

1. Read `README.md`, `AGENTS.md`, and the relevant package or application
   README.
2. Keep the dependency direction `apps -> adapters -> core` intact.
3. Confirm whether a change affects a public API, serialized format, benchmark,
   dependency, or release process.
4. Keep generated output and unrelated cleanup out of the change.

## Development setup

```text
uv sync --all-packages --all-groups --locked
cd apps/web
vp install
```

Use the locked tools and dependencies. Do not edit `uv.lock`, generated Python
runtime assets, or build output manually.

## Validation

Run the focused tests needed during development and the broadest practical
checks before submitting a change. The canonical command lists are maintained
in `AGENTS.md` and `apps/web/AGENTS.md`.

Behavior changes require tests. Changes to commands, formats, architecture,
terminology, or public behavior require corresponding documentation updates.

## Changes and reviews

- Work on a short-lived branch and merge through a pull request; do not push
  changes directly to `main`.
- Keep changes focused and explain their user-visible or architectural impact.
- Call out compatibility, migration, benchmark, privacy, and performance risks.
- Do not weaken checks or add exclusions to make validation pass.
- Use Conventional Commits for repository commits.
- Prefer squash merging so each pull request contributes one coherent change to
  `main`.
- Do not include credentials, personal data, proprietary artifacts, or
  machine-specific paths.
