# Initial Drive handoff

This page records the initial January ingestion and account locations. For the completed Q1 application, see [the current runbook](runbook.md), [Q1 evidence](q1-run.json) and [project report](project-report.md). Full Q1 raw data and run archives have since been checksum-verified in the personal Drive; see [Q1 persistence evidence](q1-drive-export.json). This historical section records the January handoff.


Uploaded and verified through Google Drive on 2026-10-26:

- Notebook: https://colab.research.google.com/drive/1xtu6zstgFAtdPfgpB-enIIPH_XTUGqyV
- Matching pipeline bundle: https://drive.google.com/file/d/1epvD-3-13ww0RJb-gq_ZtwpmXu4bj3zY/view
- Source configuration: https://drive.google.com/file/d/18AV3rmwZLt9sJ0JfWK7q40OOeqOicPEA/view

The notebook and bundle are in My Drive's root. Keep the bundle named
`urbanflow-pipeline.zip`. Open the notebook, select Runtime â†’ Run all, and approve the
Drive mount. The job uses a standard CPU runtime and writes progress/checksums/raw data
to `My Drive/UrbanFlow/data/raw/`. It needs no MongoDB credentials.

The notebook is available as a browser alternative. After workspace restrictions changed,
WSL and the existing Colab CLI were verified. A named CPU runtime, `urbanflow-ingestion`,
successfully ran `scripts/colab-ingest.py`, importing the same reusable package. The January
Parquet download took 0.744 seconds; all three source checksums matched the local fallback.
The files were first downloaded into temporary `/content/urbanflow-data/raw`. After the user
approved Google's Drive consent, `scripts/colab-persist.py` copied all three files to
`My Drive/UrbanFlow/data/raw` and verified each saved SHA-256. The persisted total is
60,193,143 bytes. `docs/colab-drive-status.json` records the completed persistence result.
The CPU runtime was then stopped successfully.

## Google account locations

The existing CLI is authenticated as `rikinparekh1415@gmail.com`; this account owns the
persisted raw data. The connected Google Drive plugin is authenticated as
`23bit044@sot.pdpu.ac.in`; this university account contains the earlier notebook and bundle
links above. These are separate Drives. Use the CLI for the current personal-account
workflow. To use the browser notebook in the personal account, copy/upload both the local
notebook and its matching bundle into that account's Drive first.

CLI session state is isolated at `/tmp/urbanflow-colab/sessions.json`. Never commit its
contents or OAuth credentials. The CLI executable is
`/home/rikin_parekh/.venvs/colab-cli/bin/colab` inside Ubuntu. Use the global options
`--auth oauth2 --config /tmp/urbanflow-colab/sessions.json` before each subcommand.

The local fallback already completed and was independently validated by the reusable Python
module. `docs/source-manifest-2025-01.json` records its sizes and checksums. The actual January
file has 3,475,226 rows, 20 columns and four row groups; see the source-profile JSON. Those
are source metadata counts, not cleaned or analytically eligible trip counts.

If using local files, upload these into `My Drive/UrbanFlow/data/raw/`:

- `data/raw/yellow_tripdata_2025-01.parquet`
- `data/raw/taxi_zone_lookup.csv`
- `data/raw/taxi_zones.zip`
- `data/raw/2025-01-manifest.json`

Rerunning the notebook validates the files and manifest before reuse. No manual upload is
necessary if the notebook's own download completes successfully.
