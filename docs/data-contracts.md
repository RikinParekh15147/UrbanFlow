# Initial data contracts

## Sources

January 2025 Yellow Taxi records and the official zone lookup/shapefile. Download URLs live
in `configs/yellow-2025-01.json`. Files are immutable inputs; output manifests record source
URL, byte count, locally calculated SHA-256 and elapsed download time. These checksums detect
later changes but are not checksums supplied by TLC.

Container validation checks Parquet magic/footer markers, zone CSV columns and unique IDs,
and ZIP integrity. It does not yet establish trip-level analytical validity. A schema-profile
report reads Parquet metadata; full quality checks are a separate pipeline stage.

## Planned analytical grain

Hourly pickup demand: `run_id × date × hour × pickup_zone_id`. Public `zone_id` filters mean
pickup zone unless an endpoint explicitly specifies drop-off. Dates are inclusive NYC-local
pickup dates; invalid date order is rejected. January avoids daylight-saving ambiguity;
before extending periods, define how repeated autumn hours are represented.

Required source fields for the initial slice:

- `tpep_pickup_datetime`, `tpep_dropoff_datetime`
- `PULocationID`, `DOLocationID`
- `trip_distance`, `fare_amount`

Preserve optional source fields, including `cbd_congestion_fee`, for future fare analysis.
Do not assume all months share identical physical types. Normalize and validate explicitly.

## Metric populations

- Demand: usable pickup timestamp within the configured month; track known/unknown zones.
- Efficiency: additionally usable distance and positive duration, with separately documented
  configurable plausibility bounds.
- Fares: report eligibility and treatment of refunds/negative values explicitly.

Keep source counts, eligible counts and exclusion reasons. Exclusion flags may overlap;
do not sum overlapping flags and label that sum as distinct excluded trips. No global
deduplication without a defensible identity rule: identical trip rows may be legitimate.

Store sums and corresponding non-null eligible counts so filtering uses weighted metrics.
`avg_speed_mph` must distinguish mean per-trip speeds from total miles / total hours; use the
latter for the initial efficiency KPI and label its population. Zero/missing denominator
returns null. Fares use USD; distance uses miles; duration uses minutes.

## API and versioning

- `/health`: process liveness only; does not imply database readiness.
- `/api/v1/datasets/status`: explicit unpublished state until serving integration exists.
- Planned first analytics endpoints: `/api/v1/zones` and `/api/v1/demand/hourly`.
- Analytical responses identify `run_id`, supported/selected periods, filters and units.
- Return empty data for a valid selection with no records; return a service-unavailable
  error when no published dataset exists. Never substitute fabricated analytics.
- Paginate zone/route rows; bound chart series by an explicit maximum date window.
- FastAPI OpenAPI is authoritative. Generate TypeScript contracts from it.
