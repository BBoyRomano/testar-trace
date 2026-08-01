# PyInstaller build setup

This folder contains the executable build configuration for ReqTrace.

## Outputs

- Windows:
  - `reqtrace.exe` (CLI)
  - `reqtrace-desktop.exe` (desktop app)
- macOS/Linux:
  - `reqtrace` (CLI)
  - `reqtrace-desktop` (desktop app)

## Local build

From repository root:

```powershell
python -m pip install --upgrade pip
python -m pip install uv
uv sync --group dev --group build --locked
uv run pyinstaller packaging/pyinstaller/reqtrace-cli.spec
uv run pyinstaller packaging/pyinstaller/reqtrace-desktop.spec
```

Build outputs are written to:

- Windows:
  - `dist/reqtrace.exe`
  - `dist/reqtrace-desktop.exe`
- macOS/Linux:
  - `dist/reqtrace`
  - `dist/reqtrace-desktop`

## Notes

- Build on the target OS you want to distribute for.
- The included GitHub workflow builds Windows, macOS, and Linux artifacts on demand.
- The desktop executable uses spawned worker processes for analysis execution to keep the UI responsive.

