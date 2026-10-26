# Implementation checkpoints

1. Foundation and ingestion: Git, package boundaries, environment template, source downloads,
   checksums, schema inspection, API liveness, notebook handoff and tests.
2. First Spark job: normalize January, flag eligibility, Spark SQL hourly zone aggregates,
   reconciliation tests, curated/aggregate Parquet and reproducible run manifest.
3. Serving: versioned MongoDB publisher, compound indexes, publication pointer, readiness,
   zone and hourly demand endpoints, generated OpenAPI client.
4. First UI: React/Vite, API proxy, demand chart and date/zone filters, real-data loading,
   empty/error states. Confirm it works after Colab disconnects.
5. Expand: overview, demand comparisons, geography, efficiency, fares; extend to Q1 after
   measuring collection/index sizes and handling schema/time-boundary differences.
6. Big Data Lab: equivalent Pandas/Spark tasks, repeated measured benchmarks, quality reports.
7. Desktop: Electron shell, managed Windows backend executable, installer and clean-machine QA.

The first complete vertical slice is checkpoint 4. Checkpoint 1 alone does not claim the
end-to-end analytics application is ready.
