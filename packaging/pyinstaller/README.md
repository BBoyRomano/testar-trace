# PyInstaller build setup

This folder contains the executable build configuration for ReqTrace.

## Outputs

- `reqtrace.exe` (CLI)
- `reqtrace-gui.exe` (GUI)

## Local build (Windows)

From repository root:

```powershell
python -m pip install --upgrade pip
pip install -e ".[dev,packaging]"
pyinstaller packaging/pyinstaller/reqtrace-cli.spec
pyinstaller packaging/pyinstaller/reqtrace-gui.spec
```

Build outputs are written to:

- `dist/reqtrace/reqtrace.exe`
- `dist/reqtrace-gui/reqtrace-gui.exe`

## Notes

- Build on the target OS you want to distribute for.
- The included GitHub workflow builds Windows artifacts on demand.
