# Packaging

This directory contains distribution-oriented assets that are intentionally
kept separate from runtime source code in `src/`.

## Current contents

- `pyinstaller/`: executable build specs and entry points
- GitHub Actions workflow (`.github/workflows/build-executables.yml`) that
  builds executables for Windows, macOS, and Linux

## Scope

- build-time configuration only
- no runtime app logic
- no research data or evaluation outputs

## Executable artifacts

The build workflow produces two artifacts per platform:

- `reqtrace-cli-<platform>`: CLI executable (single-file)
- `reqtrace-desktop-<platform>`: Desktop executable (single-file)

Current platform suffixes:

- `windows-x64`
- `macos`
- `linux-x64`

Each workflow run performs a CLI smoke test by executing the built binary with
`--help` before artifacts are uploaded.

