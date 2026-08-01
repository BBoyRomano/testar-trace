# ReqTrace Apps

ReqTrace applications use the packages as the source of truth:

- `reqtrace` contains canonical models, progress/cancellation, serialization, and analysis methods.
- `reqtrace-adapters` loads external requirement and evidence inputs into canonical models.
- `reqtrace-api` exposes those packages to browser and future desktop frontends.
- `reqtrace-web` is the browser UI.
- `reqtrace-cli` is the terminal UI.

The old Tkinter desktop app has been archived under
`packages/_archive/reqtrace-desktop-v0` because it still used the previous
`reqtrace.application.*` architecture.

Run the web app with the API:

```cmd
uv run reqtrace-api --host 127.0.0.1 --port 8765
```

```cmd
cd apps\web
vp dev --host 127.0.0.1 --port 5173
```

The web app uses the API for requirement parsing, evidence parsing, and
analysis. The browser layer should only map canonical API JSON into view models.

The web workspace has three primary areas:

- load and inspect requirement/evidence sources;
- run cancellable analyses while keeping the loaded sources available;
- inspect, import, export, and delete saved analysis results.

Keep requirement parsing, evidence parsing, and traceability logic in the
packages/API. The web app should stay a thin, responsive view over canonical
models and results.
