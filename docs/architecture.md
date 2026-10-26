# UrbanFlow architecture

UrbanFlow is a modular monolith with an independent batch pipeline:

`TLC → ingestion → raw Parquet on Drive → Colab Spark/Spark SQL → aggregate Parquet → MongoDB → FastAPI → React → Electron`

Dashboard requests do not invoke Spark. Colab is temporary compute; Drive and MongoDB retain
the outputs. Notebooks orchestrate reusable modules from `pipelines/`; React calls FastAPI.

## Repository boundaries

- `apps/api`: serving API, validation, repositories, business logic and response models.
- `apps/web`: feature-based React client, generated API types, charts and maps.
- `apps/desktop`: future Electron shell and Windows packaging.
- `pipelines`: separately installable ingestion, Spark analytics and publishing package.
- `notebooks`: orchestration and demonstrations, without embedded transformation logic.
- `contracts`: generated FastAPI OpenAPI and shared contract documentation.
- `configs`: source periods and processing parameters, without credentials.
- `scripts`: local tooling, fallback download and artifact preparation.
- `docs`: architecture, metrics, operational instructions and project evidence.

## Development environment

The preferred canonical development checkout is inside WSL's Linux filesystem. The initial
checkout is in the provided Windows workspace. WSL access was initially restricted and is
now verified through `wsl -d Ubuntu`. Windows Python tooling is installed under ignored
`.tools/`, with its virtual environment in `.venv/`. No shell-profile changes are required.

Google Drive is connected. Its connector can upload artifacts but cannot start Colab runtimes.
The installed Colab CLI runs inside Ubuntu at
`/home/rikin_parekh/.venvs/colab-cli/bin/colab`. Authentication is verified and a named CPU
runtime has executed the reusable ingestion package. A browser notebook in Drive remains
available as an alternative. Drive mounting requires its own Google consent; CLI runtime
authentication alone does not provide a mounted Drive filesystem.

## Publication protocol (next milestone)

Every aggregate has `run_id` plus its deterministic dimension key. Build a new immutable
version, validate all expected collections, then atomically change one publication-pointer
document. API requests resolve that pointer once and filter all queries by that version.
The client can pin a version across charts. Retain the preceding version for rollback;
do not clean versions still needed by active or pinned requests.

## Scope of the initial commit

Implemented: source download configuration, progress/checksum manifests, source-container
validation, reusable Python ingestion, a Node fallback downloader, Colab bootstrap, FastAPI
liveness and explicit unpublished-data status, and meaningful ingestion/API tests.

Pending: Spark transformations, MongoDB publication and querying, analytical endpoints,
generated frontend client, dashboard, benchmarks and Electron. No mock trip analytics are
presented as real results.

Sources:
- https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- https://github.com/googlecolab/google-colab-cli
- https://www.mongodb.com/docs/manual/core/write-operations-atomicity/
