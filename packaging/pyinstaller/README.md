# PyInstaller build setup

This folder contains the executable build configuration for ReqTrace.

## Outputs

- Windows:
  - `reqtrace.exe` (CLI)
  - `reqtrace-gui.exe` (GUI)
- macOS/Linux:
  - `reqtrace` (CLI)
  - `reqtrace-gui` (GUI)

## Local build

From repository root:

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev,packaging]"
pyinstaller packaging/pyinstaller/reqtrace-cli.spec
pyinstaller packaging/pyinstaller/reqtrace-gui.spec
```

Build outputs are written to:

- Windows:
  - `dist/reqtrace.exe`
  - `dist/reqtrace-gui.exe`
- macOS/Linux:
  - `dist/reqtrace`
  - `dist/reqtrace-gui`

## Notes

- Build on the target OS you want to distribute for.
- The included GitHub workflow builds Windows, macOS, and Linux artifacts on demand.
- The GUI executable uses spawned worker processes for analysis execution to keep the UI responsive.
