# UrbanFlow

NYC taxi mobility analytics using independent Spark/Spark SQL batch processing, MongoDB
serving, FastAPI and a future React/Electron interface.

Git is initialized on `main`. No remote repository has been configured or pushed.

## Current milestone

Repository foundation and source ingestion. January 2025 download configuration, checksum
manifests, source-container validation, Colab bootstrap and API foundation are implemented.
Spark analytics, MongoDB integration, the dashboard and desktop packaging are subsequent
milestones. See [the roadmap](docs/roadmap.md) and [data contracts](docs/data-contracts.md).

## Download source data locally

Requires Node.js 22 or newer. No Python or Google credentials are needed:

```powershell
node scripts/download-data.mjs
```

Outputs: `data/raw/yellow_tripdata_2025-01.parquet`, `taxi_zone_lookup.csv`, `taxi_zones.zip`,
`2025-01-manifest.json` and `download-progress.json`. Re-running verifies existing hashes.
Raw data, tools, environment files and generated artifacts are ignored by Git.

The [initial Colab handoff](docs/colab-handoff.md) contains the verified Drive notebook and
bundle links, plus instructions for the already-downloaded local fallback.

## Run in Colab

1. Put `artifacts/urbanflow-pipeline.zip` at the root of My Drive.
2. Open `notebooks/00_ingestion_colab.ipynb` in Colab with a standard CPU runtime.
3. Run all cells and approve the Google Drive mount prompt.
4. Inspect progress in the cell output or `My Drive/UrbanFlow/data/raw/download-progress.json`.

The notebook verifies its companion bundle's SHA-256, imports the reusable Python package
and downloads into persistent Drive storage. No paid runtime or MongoDB permission is needed.
If using the local fallback, upload the three source files and manifest from `data/raw/`
into that same Drive directory; the Python downloader validates and reuses them.

To rebuild the companion artifacts on Windows:

```powershell
uv run python scripts/package-colab.py
node scripts/build-colab.mjs
```

## Python setup and API

With [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```text
uv sync --python 3.12
uv run pytest
uv run ruff check .
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
uv run python scripts/export-openapi.py
```

Run commands from the repository root. The root uv workspace installs both local packages.
`GET /health` reports process liveness. `GET /api/v1/datasets/status` honestly reports that
no analytical version is published yet. API documentation is available at `/docs`.

For the Windows checkout, uv and Python are installed inside ignored `.tools/`; use
`.tools/uv/uv.exe` in place of `uv`. If needed set `UV_CACHE_DIR` to `.cache/uv` and
`UV_PYTHON_INSTALL_DIR` to `.tools/python` using absolute paths. No secrets belong in Git.

## Architecture

See [architecture](docs/architecture.md). The preferred development checkout is in WSL's
Linux filesystem. This initial checkout uses the supplied Windows workspace; WSL access
and the installed Colab CLI have now been verified. The project root itself is the monorepo; an additional
nested `urbanflow/` directory is unnecessary.
