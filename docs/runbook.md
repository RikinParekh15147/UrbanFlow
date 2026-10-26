# Reproducible runbook

Run commands from the repository root. Use `uv sync --python 3.12` and `npm ci` first. This workspace also has `.tools/uv/uv.exe`. For WSL shell equivalents, replace PowerShell `$env:NAME='value'` with `export NAME=value`. Python and Node environments should belong to the environment running the commands.

## Browser and offline demonstration

```powershell
$env:URBANFLOW_DATA_SOURCE = 'snapshot'
$env:URBANFLOW_SNAPSHOT_DIR = 'data/serving'
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal:
npm run dev
```

The serving directory must contain `manifest.json` and the seven JSONL collection files. These large generated outputs are ignored by Git. A new checkout needs the verified serving archive or a regenerated pipeline run. There is no fabricated fallback. `/health` only verifies process liveness; `/api/v1/datasets/status` verifies publication availability and reports its source.

For a production browser build, run `npm run build`, then use FastAPI on port 8000; it serves `apps/web/dist` with SPA fallback. The Vite server is unnecessary in this mode.

## MongoDB serving

Use an installed MongoDB instance bound to loopback, or an Atlas URI with appropriate permissions and network access. No Atlas account was provisioned. The supplied WSL helper is specific to this workspace: `scripts/start-mongo.sh` requires the downloaded `.tools/mongodb.tgz` and keeps state under `$HOME/.local/share/urbanflow`; a fresh clone must supply that archive or install MongoDB independently.

```powershell
wsl -d Ubuntu -- bash scripts/start-mongo.sh
$env:URBANFLOW_MONGODB_URI = 'mongodb://127.0.0.1:27017'
$env:URBANFLOW_MONGODB_DATABASE = 'urbanflow'
uv run python -m urbanflow_etl.publishing.mongo --input data/serving
$env:URBANFLOW_DATA_SOURCE = 'mongodb'
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Do not leave `URBANFLOW_MONGODB_URI` blank in `.env`; either omit it to use the default or set a real URI. Set data source explicitly to avoid inheriting snapshot mode from an earlier terminal. MongoDB unavailability returns 503. Secrets belong in local environment/configuration only.

The publisher accepts validated manifests, binds run identity to payload hashes, validates counts and demand totals, and switches the current pointer after staging. Repeating an already published identical run is a no-op. Changed inputs require a new run ID. Keep the earlier version until rollback is unnecessary; cleanup is manual. Inspect failed/staging runs before intervention, especially after a killed publisher.

## Ingest and run Spark

The no-Google January fallback is `node scripts/download-data.mjs`. For Q1 or other configurations, use the reusable ingestion command:

```powershell
uv run python -m urbanflow_etl.ingestion.download --config configs/yellow-2025-q1.json --output data/raw
uv run python -m urbanflow_etl.analytics.job --help
```

A Java-compatible PySpark environment is required for analytics. The following is a Linux/Colab shell example after installing the pipeline Spark extra and PyArrow, Pandas, psutil, pyshp and pyproj:

```bash
export PYSPARK_SUBMIT_ARGS='--driver-memory 4g pyspark-shell'
python -m urbanflow_etl.analytics.job \
  --input data/raw/yellow_tripdata_2025-01.parquet data/raw/yellow_tripdata_2025-02.parquet data/raw/yellow_tripdata_2025-03.parquet \
  --zones data/raw/taxi_zone_lookup.csv --geometry data/raw/taxi_zones.zip \
  --output data/results --start 2025-01-01 --end 2025-03-31 \
  --run-id yellow-2025-q1-reproduction --partitions 8
```

This produces aggregate Parquet and `data/results/serving`. Run benchmarks using `urbanflow_etl.benchmarking.job.run(spark, inputs, Path('data/results/serving'))` with the same Spark session or see the complete orchestration in `scripts/colab-analyze.py`. Benchmarking updates the serving manifest with eight experiment rows.

## Colab and persistence

The installed CLI is `/home/rikin_parekh/.venvs/colab-cli/bin/colab` in Ubuntu. Existing OAuth/session state is local and must not be committed. Check installed CLI help with:

```powershell
wsl -d Ubuntu -- /home/rikin_parekh/.venvs/colab-cli/bin/colab --help
```

`notebooks/00_ingestion_colab.ipynb` and `scripts/colab-ingest.py` cover ingestion; `scripts/colab-analyze.py` imports the same reusable Spark modules, runs fixture checks, analyses and benchmarks. It expects the uploaded archive at `/content/urbanflow-analytics.zip`, its SHA-256 in `URBANFLOW_BUNDLE_SHA256`, and `URBANFLOW_PERIOD=q1` for the quarter. Rebuild with `uv run python scripts/package-colab.py --output artifacts/urbanflow-analytics.zip` and compute SHA-256 with `Get-FileHash`; upload under the expected name. Install runtime dependencies first. Source scripts reference `/content` intentionally and are not ordinary Windows commands.

`scripts/colab-curated.py` separately writes and validates date-partitioned full curated Parquet and creates a reproducibility archive. Do not count temporary VM archives as persisted Drive outputs. Mount Drive with Google consent, copy archives/manifests, verify SHA-256 after copying, then stop the runtime. Full Q1 raw and run output persistence is verified in [q1-drive-export.json](q1-drive-export.json), completed 2026-10-26T11:03:13Z. The personal Drive holds five raw files (190,500,974 bytes), serving.zip (27,572,731 bytes), curated-and-aggregate-parquet.zip (322,015,163 bytes), executed-source.zip (13,547 bytes), manifest and benchmarks under the documented paths. A new runtime may still require its own Drive consent. The CLI personal Google account and connected university Drive are separate.

## Checks and release

```powershell
uv run pytest
uv run ruff check .
npm run check
npm test
npm run build
uv run python scripts/export-openapi.py
npm run generate:api
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-release.ps1
```

The Spark fixture is skipped without Spark and must be executed in a real Spark environment. `scripts/smoke-backend.ps1` checks the packaged backend against the snapshot. Release builds require Windows, the real serving files, installed workspace dependencies and PyInstaller. Keep generated `.exe` files out of Git. Inspect `release/release-manifest.json` and hash sidecars. Releases are unsigned; separate clean-machine installer testing remains required unless recorded as completed in release evidence.

For startup failures, inspect the Electron user-data `backend.log`. A stale backend, missing snapshot or missing build is not repaired by launching Spark. Stop/restart the service after changing environment settings because API configuration is read at import time.


## Orchestration notebooks

The pinned initial `00_ingestion_colab.ipynb` is unchanged. New notebooks use the exact checksum-verified `executed-source.zip` from the completed Q1 Drive run, install its runtime dependencies, and import reusable pipeline functions:

- `01_exploration.ipynb`: source schemas, Parquet metadata and original manifest.
- `02_pipeline_runner.ipynb`: Q1 Spark aggregation, benchmarks and verified serving-archive persistence under a fresh run ID.
- `03_benchmarks.ipynb`: independent equivalent-engine experiments and verified experiment-evidence persistence.

Open them in the personal Drive account in a CPU runtime. They contain orchestration, not duplicate cleaning or metric logic. Notebook JSON and Python cell syntax have been checked; the new notebooks have not themselves been executed end to end. Existing pipeline modules and the original run provide the execution evidence. Fresh source installs can use `pip install -e 'pipelines[spark,geometry,benchmark,publish]'`; archived source predates the new geometry/benchmark extras, so notebooks install those dependencies explicitly.
