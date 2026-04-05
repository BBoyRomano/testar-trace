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

- `reqtrace-cli-<platform>`: CLI bundle
- `reqtrace-gui-<platform>`: GUI bundle

Current platform suffixes:

- `windows-x64`
- `macos-x64`
- `linux-x64`

Each workflow run also performs a smoke test by executing the built CLI with
`--help` before artifacts are uploaded.
