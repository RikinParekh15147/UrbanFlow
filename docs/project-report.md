# UrbanFlow demonstration report

## Objective and implementation

UrbanFlow demonstrates a reproducible big-data analytics path: official TLC source files → PySpark cleaning and Spark SQL → versioned MongoDB aggregates → FastAPI → React dashboard, with an Electron Windows release. Six modules expose demand, geography, travel efficiency, fares and processing evidence. The offline desktop snapshot uses the same real aggregates and identifies its source explicitly; it does not demonstrate a live MongoDB query.

## Q1 processing result

Run `yellow-2025-q1-v1`, ETL 1.0.0, covers January 1–March 31, 2025. Evidence is in [q1-run.json](q1-run.json).

| Observation | Count |
|---|---:|
| Source rows | 11,198,026 |
| In-period / demand-eligible rows | 11,198,001 |
| Outside-period rows | 25 |
| Unknown pickup lookup IDs | 0 |
| Invalid distance flags | 548 |
| Efficiency exclusion flags | 364,942 |
| Fare exclusion flags | 535,511 |
| Daily demand documents | 21,549 |
| Hourly demand documents | 321,933 |
| Efficiency documents | 321,933 |
| Fare documents | 21,549 |
| Retained route documents | 9,000 |
| Zone metadata documents | 265 |
| Benchmark experiment documents | 8 |

Exclusion flags overlap. Trips can count toward demand while being excluded from another metric. Curated Parquet reconciled to 11,198,001 rows in 94 date-partitioned files. The recorded analytics job took 259.35 seconds; this is not end-to-end acquisition, benchmark and persistence time.

The first Q1 attempt exhausted Java heap. A 4 GiB Spark driver with cleaned rows persisted using `DISK_ONLY` completed successfully. The recorded environment had 2 CPU cores, 12.67 GiB RAM, Spark 3.5.9, Python 3.13.16, Pandas 2.2.3 and 8 shuffle partitions. This is a single Colab VM, not a multi-machine Spark cluster.

Q1 was published to local MongoDB. At that point, including the retained January version, database statistics recorded 908,213 documents, 343.08 MiB BSON data, 73.91 MiB storage, 33.73 MiB indexes and 107.65 MiB total physical storage. These are different measurements; physical compression does not establish compliance with a hosted tier's logical storage limit. Atlas storage and networking must be checked on an actual provisioned cluster.

## Benchmark experiment

The task reads a **single-column** Parquet input and counts records by pickup-zone ID. Spark materializes identical bounded samples for both engines. Each engine runs three repetitions, alternating order, and exact result equality and total counts are checked. Table entries are median milliseconds from the saved experiment records.

| Input rows | Pandas | Spark SQL |
|---:|---:|---:|
| 10,000 | 9.127 | 315.074 |
| 100,000 | 23.947 | 670.087 |
| 1,000,000 | 32.859 | 389.201 |
| 11,198,026 | 313.479 | 1,113.450 |

Pandas was faster for this small-width, in-memory-compatible count task on this VM. Spark session startup is excluded; Parquet read and result materialization are included. Sample creation is outside timings, OS caches are not cleared, samples use `limit` rather than random sampling, and all inputs are coalesced to one file. The largest input is only 12,337,418 compressed bytes because it contains one column. These results do not establish a universal engine ranking, full-ETL speedup, a distributed scaling curve or a partition-tuning experiment. The early small Pandas run also shows warm-up variation; min/max and all three samples are retained in the evidence.

## Suggested demonstration

1. Show `/api/v1/datasets/status`: run ID, quarter, serving source and quality manifest.
2. Open Overview and explain demand versus metric-specific eligible counts.
3. Select a month, borough and pickup zone; show the version stays pinned across pages.
4. Open Demand for hour-of-day patterns and Geographic Analytics for official TLC polygons.
5. Explain that outside-selection zones remain map context and not zero-demand observations.
6. Show Trip Efficiency and its ratio-of-totals speed definition.
7. Show Fare Analytics; distinguish base fare from passenger total and explain excluded refunds.
8. Export CSV and inspect date, zone and dataset context.
9. Open Big Data Lab; show quality flags, source provenance and the honest benchmark outcome.
10. Demonstrate desktop startup with Colab stopped. State explicitly whether it uses MongoDB or the offline snapshot.

## Validation and remaining boundaries

The implementation has API/publisher tests, frontend unit tests, a real Spark correctness fixture executed in Colab, and packaged-backend route smoke checks. Consult the latest command output and release evidence for final test counts and artifact validation. A local Spark skip is not a Spark pass. The Windows backend smoke exercised twelve routes; that alone does not verify an installer on a clean Windows machine.

Source provenance is the [official TLC dataset](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), with exact fetched URLs and computed checksums in the run manifest. Maps use TLC shapefile geometry transformed to WGS84; metadata-only lookup IDs may lack polygons. Daily routes are truncated to the globally top 100, so filtered route rankings are partial. Wall-clock timestamps carry DST ambiguity. Data describes taxi activity, not all city travel, road occupancy, crash rates or causal congestion. No predictive model is claimed.

Full Q1 persistence completed at 2026-10-26T11:03:13Z in the personal Drive. Five raw files total 190,500,974 bytes in `My Drive/UrbanFlow/data/raw`. `My Drive/UrbanFlow/runs/yellow-2025-q1-v1` contains checksum-verified `serving.zip` (27,572,731 bytes), `curated-and-aggregate-parquet.zip` (322,015,163 bytes), `executed-source.zip` (13,547 bytes), manifest and benchmark JSON. See [persistence evidence](q1-drive-export.json). The personal CLI Google account and university connected Drive are separate. Atlas has not been provisioned. Windows executables are unsigned; clean-machine testing and code signing are release follow-ups unless later evidence records them completed.
