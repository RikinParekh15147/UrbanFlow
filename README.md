# UrbanFlow

Urban mobility analytics for **11,198,026 real NYC Yellow Taxi records from January–March 2025**. Spark and Spark SQL prepare versioned aggregates; MongoDB serves them through FastAPI to a six-section React dashboard. Electron packages the application for Windows with an explicit offline snapshot mode. Dashboard requests never start Spark.

The app includes Overview, Demand Intelligence, Geographic Analytics, Trip Efficiency, Fare Analytics and Big Data Lab, shared date/borough/pickup-zone filters, official TLC polygons, and CSV exports carrying selection and dataset metadata. Results describe taxi demand and inferred travel efficiency, not observed road congestion or crashes.

## Run the browser application

Run from the repository root with Python 3.12/3.13, uv and Node.js 22+. Lockfiles define dependencies. Datasets and generated releases are ignored by Git; this completed workspace has the real Q1 serving files in `data/serving/`.

```powershell
uv sync --python 3.12
npm ci
$env:URBANFLOW_DATA_SOURCE = 'snapshot'
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal run `npm run dev` and open the URL Vite prints. Its `/api` proxy targets port 8000. API documentation is at `http://127.0.0.1:8000/docs`. On this Windows workspace, `.tools/uv/uv.exe` can replace `uv`.

Snapshot mode is deliberately selected above. The default configuration uses MongoDB and reports database unavailability rather than silently substituting files. To demonstrate the database path, follow the [runbook](docs/runbook.md#mongodb-serving).

## Windows desktop

The desktop build bundles the frontend, a PyInstaller FastAPI executable and the verified Q1 aggregate snapshot. It manages a backend on a temporary loopback port and needs neither WSL, Python, MongoDB nor Colab at runtime in snapshot mode.

```powershell
npm run build
npm run desktop
# Build frontend, backend, installer and portable ZIP:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1
```

Generated executables and SHA-256 sidecars go in `release/`. Builds are unsigned; Windows may show an unknown-publisher warning. See the release manifest and [desktop documentation](docs/desktop-release.md) for artifact details and validation status. A development-machine build does not establish clean-machine compatibility.

The portable ZIP contains the standalone application folder; extract it and open
`UrbanFlow.exe`. It uses the same bundled backend and real Q1 snapshot as the installer.

## Reproduce and inspect

- [Runbook](docs/runbook.md): ingestion, Spark/Colab, publication, checks and recovery.
- [Architecture](docs/architecture.md): boundaries and versioned serving.
- [Data and API contracts](docs/data-contracts.md): definitions, filters and endpoints.
- [Demonstration report](docs/project-report.md): Q1 results and benchmark limitations.
- [Q1 evidence](docs/q1-run.json): checksums, quality counts and configuration.
- [Verification record](docs/validation.md): checks passed and remaining validation limits.
- [Google Drive/Colab handoff](docs/colab-handoff.md): account locations and initial provenance.

```powershell
uv run pytest
uv run ruff check .
npm run check
npm test
npm run build
uv run python scripts/export-openapi.py
npm run generate:api
```

The Spark fixture requires Java and the pipeline's `spark` extra; it is skipped without Spark and has separately run in Colab. No credentials belong in Git, frontend code or the installer. Atlas connectivity is supported through the MongoDB URI, but no Atlas cluster/account has been provisioned. Local MongoDB is the verified database target. Q1 raw data, serving and reproducibility archives are checksum-verified in the personal Drive; see [persistence evidence](docs/q1-drive-export.json). No remote Git repository is configured unless added later.
