# Windows desktop release

Build on Windows with Node.js 22.12 or later, npm, and Python 3.12. Install the
workspace dependencies with `npm ci` and `uv sync --dev`. A real, validated
publication must already exist in `data/serving/`; the build never downloads data
or substitutes generated measurements.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-release.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke-backend.ps1
```

The release contains `UrbanFlow-Setup-1.0.0.exe` and
`UrbanFlow-Portable-1.0.0.zip`, SHA256 sidecars, and `release-manifest.json` with
the snapshot metadata. The setup supports a user-selected installation path.
Extract the complete portable ZIP into a normal user-owned folder, then start
`UrbanFlow.exe` there. Keep all extracted resources together.

The desktop shell starts its bundled FastAPI executable on an available IPv4
loopback port, waits for `/health`, then opens the bundled interface. Closing
the application terminates its backend child process. No WSL, Python install,
Colab session, internet connection, or database is required for the bundled
snapshot. The UI identifies this data source as `local_snapshot`.

Electron uses a sandboxed renderer, context isolation, disabled Node.js,
denied permissions, restricted navigation, and a content security policy.
The preload exposes only version metadata. The release contains no `.env`
files or MongoDB credentials. To connect a personal deployment to MongoDB,
set `URBANFLOW_MONGODB_URI` in the launching environment or in the external
`%APPDATA%/UrbanFlow/.env` file. For public distribution, use a hosted API
instead of distributing shared database credentials.

Backend logs are written to `%APPDATA%/UrbanFlow/backend.log`. A desktop smoke
run can be triggered explicitly from a terminal:

```powershell
& 'release/win-unpacked/UrbanFlow.exe' '--smoke-output=C:/temp/urbanflow-smoke.json'
```

This checks that the renderer has loaded, the overview API responds, Node.js
is unavailable in the renderer, and the limited preload metadata is visible.
It then opens Geographic analytics and waits for rendered taxi-zone polygons,
verifying that the packaged MapLibre worker loads under Electron's content
security policy.
It writes JSON and a screenshot, then closes the application. Check that no
`urbanflow-api.exe` process remains after exit. A successful smoke run on the
development machine does not replace a clean-machine installer test.

The portable ZIP avoids executing from a self-extracting launcher's temporary
directory. Some Windows temporary folders inherit AppContainer access rules
that prevent Electron's sandbox from reading its own runtime files. Extract
the ZIP into a normal user-owned folder; the renderer sandbox stays enabled.
The upstream diagnosis is documented in
[Electron's install-directory access fix](https://github.com/electron/electron/pull/54382).

These builds are unsigned. Code signing requires a publisher certificate and
is a separate release step; Windows may display an unknown-publisher prompt.
