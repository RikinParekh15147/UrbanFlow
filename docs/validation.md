# Verification record

Verified on the development Windows machine on 26 October 2026:

- Python: 27 tests passed, including real local MongoDB publication and API checks.
  One Spark-only test module is skipped locally; its correctness fixture separately
  passed in Colab before processing the real Q1 data.
- Frontend: five unit tests, TypeScript checking and the production build passed.
- Python lint and formatting checks passed. Generated OpenAPI and TypeScript
  contracts were refreshed together.
- Production npm audit reported zero vulnerabilities.
- GitHub Actions passed in a fresh Linux checkout after the temporary-directory
  configuration fix: Python lint/format, 16 tests passed with 12 optional MongoDB/Spark
  skips, OpenAPI consistency, frontend types, five tests and production build.
- Browser checks covered all six routes, shared zone filtering, an empty selection,
  CSV download and mobile document overflow. Desktop and mobile captures of all six
  sections received an independent visual review with disposition **ship**.
  That screenshot review does not certify keyboard behavior or computed contrast.
- The Dataset & Model extension separately passed desktop/mobile visual review,
  provenance disclosure, dataset-wide filter scope, benchmark navigation and preserved
  trip selection checks.
- The packaged backend exercised twelve routes. The installed desktop application
  passed startup, rendered dashboard, API, renderer security and backend shutdown
  checks on this machine. Final artifact hashes are in `release/release-manifest.json`.
- Q1 raw inputs, curated and aggregate Parquet, serving files and executed source
  were copied to Drive and checksum verified; see [archive evidence](q1-drive-export.json).
  The Colab runtime was then stopped.

The new exploration, runner and benchmark notebooks have valid JSON and compilable
Python cells; they have not independently been executed end to end. The underlying
pipeline modules were executed on the reported Q1 data. Atlas connectivity and a
clean-machine Windows installation remain unverified. Executables are unsigned.

## Production map regression, 27 October 2026

The production build reproduced a missing MapLibre worker while development
rendering worked. Vite now bundles the MapLibre 6 worker explicitly with
`?worker&url` and supplies that URL before map creation, following the
[official bundler setup](https://maplibre.org/maplibre-gl-js/docs/#installation).
Map readiness requires rendered zone polygons, rather than only a canvas element.
Production browser and actual Electron installer/ZIP checks passed. Blocking the
worker produced the visible failure state; restoring it and reloading restored
rendered polygons. The five frontend tests, TypeScript check and build also passed.
