# Data and API contracts

## Provenance and grain

Source: [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), Yellow Taxi January–March 2025, official zone lookup and shapefile. `docs/q1-run.json` records source URLs, sizes and SHA-256 values computed by UrbanFlow, not checksums supplied by TLC. Raw files remain unchanged. Equal rows are not deduplicated because they do not establish trip identity.

The analytics input requires pickup/drop-off timestamps, pickup/drop-off IDs, distance, fare amount and payment type. Missing optional tip, total-amount and congestion-fee columns become null. Curated Parquet preserves derived flags; demand uses in-period trips whose pickup ID joins the lookup.

| Collection | Grain |
|---|---|
| `demand_daily`, `fare_analytics` | run × pickup date × pickup zone |
| `demand_hourly`, `trip_efficiency` | run × pickup date × wall-clock hour × pickup zone |
| `route_flows` | run × date × origin × destination; top 100 routes each day |
| `zones` | run × zone ID; geometry stored once per version |
| `benchmarks` | run × experiment ID |

Dates use NYC pickup wall-clock values and inclusive bounds. Spark uses `America/New_York`. Hour groups do not encode an offset or distinguish repeated autumn hours. Duration comes from timestamp differences in that session; DST-boundary trips need caution because source wall-clock timestamps do not provide a unique UTC offset.

## Metrics

| Metric/population | Rule or formula |
|---|---|
| Demand | In-period trips with a known pickup lookup ID, independent of fare/efficiency validity |
| Valid distance | 0–100 miles inclusive |
| Efficiency eligible | Distance >0 and ≤100 miles; duration 1–240 minutes; inferred speed ≤100 mph |
| Fare eligible | Base fare 0–1000 USD; negative/refund rows remain in demand |
| Average distance | Valid distance sum / valid distance count |
| Average duration | Efficiency-eligible duration sum / eligible count |
| Speed | Eligible miles × 60 / eligible minutes; ratio of totals |
| Average fare | Eligible base-fare sum / fare-eligible count |
| Total fare | Eligible base-fare sum; not total passenger charges or net revenue |
| Fare per mile | Fare sum / distance sum among jointly eligible trips with distance >0 |
| Fare distribution | [0,10), [10,20), [20,30), [30,50), [50,100), [100,1000] USD |
| Tips/fees | Nonnegative recorded tips or congestion-surcharge + CBD fee, on fare-eligible trips; missing amounts contribute zero |
| Payment categories | All demand-eligible trips by TLC code, independent of fare eligibility |

Zero denominators return null. Additive sums and counts produce weighted selected-period metrics. Quality flags overlap and cannot be added as distinct rejected trips. Cash tips are incompletely observed. Speeds describe taxi trips, not observed road congestion. Plausibility bounds are project rules, not official TLC guarantees.

## API

`contracts/openapi.json` is generated from FastAPI. Export with `uv run python scripts/export-openapi.py`, then run `npm run generate:api`.

| GET route | Result/additional parameters |
|---|---|
| `/health` | Process liveness only |
| `/api/v1/datasets/status` | Active version, source and manifest; no analytical filters |
| `/api/v1/overview` | KPIs, daily demand, top zones and boroughs |
| `/api/v1/demand/daily` | Daily series |
| `/api/v1/demand/hourly` | `group_by=hour` (default) or `date_hour` |
| `/api/v1/zones` | Metadata; optional borough/run_id, limit 1–265, offset ≥0 |
| `/api/v1/zones/{id}/metrics` | Overview restricted to path pickup zone |
| `/api/v1/geography/heatmap` | GeoJSON, metrics and `in_selection` |
| `/api/v1/routes/top` | Retained-route rankings; limit 1–100, offset ≥0 |
| `/api/v1/trips/efficiency` | `group_by=zone` or `hour`; limit 1–265, offset ≥0 |
| `/api/v1/fares/summary` | Fares, bins, payment counts and top 20 zones |
| `/api/v1/benchmarks` | Whole-run experiments, quality and machine data; optional run_id |

Analytical routes take `start_date`, `end_date`, `borough`, `zone_id` and `run_id` unless specified otherwise. Omitted dates use the publication's full period. Maximum range is 366 inclusive days, entirely inside the available period. Borough names match the lookup; zone IDs range 1–265. Zone filters mean **pickup** zone. Path and query zone IDs must agree; borough and zone filters intersect. Benchmark results describe the whole run and do not change with analytical filters.

The heatmap keeps surrounding polygons for context and marks zones outside a selected zone. Lookup entries without geometry have no polygon. Route filtering uses retained global daily top-100 routes, so it cannot recover discarded routes or guarantee true top routes for a selected origin/borough or combined period.

Metadata carries run ID, selected/available dates, source, timezone and filters; metric names and these contracts define units. CSV exports retain selection/version context. Valid empty selections return empty data or zero/null summaries. No publication returns 503; an unavailable explicit run returns 404; invalid filters return 422. Errors use `{"error":{"code":...,"message":...}}`.
