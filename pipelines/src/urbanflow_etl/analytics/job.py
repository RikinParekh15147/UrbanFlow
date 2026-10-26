"""Historical taxi analysis. Only bounded aggregates are brought to the driver."""

import argparse
import csv
import json
import platform
import time
from datetime import UTC, datetime
from pathlib import Path

VERSION = "1.0.0"

METRICS = """
COUNT(*) AS trip_count,
SUM(CASE WHEN distance_valid THEN trip_distance ELSE 0 END) AS distance_sum,
SUM(CASE WHEN distance_valid THEN 1 ELSE 0 END) AS distance_count,
SUM(CASE WHEN efficiency_valid THEN duration_min ELSE 0 END) AS duration_sum,
SUM(CASE WHEN efficiency_valid THEN trip_distance ELSE 0 END) AS efficiency_distance_sum,
SUM(CASE WHEN efficiency_valid THEN 1 ELSE 0 END) AS efficiency_count,
SUM(CASE WHEN fare_valid THEN fare_amount ELSE 0 END) AS fare_sum,
SUM(CASE WHEN fare_valid THEN 1 ELSE 0 END) AS fare_count,
SUM(CASE WHEN fare_valid AND distance_valid AND trip_distance > 0
    THEN fare_amount ELSE 0 END) AS fare_distance_amount,
SUM(CASE WHEN fare_valid AND distance_valid AND trip_distance > 0
    THEN trip_distance ELSE 0 END) AS fare_distance_miles,
SUM(CASE WHEN fare_valid THEN GREATEST(COALESCE(tip_amount,0),0) ELSE 0 END) AS tip_sum,
SUM(CASE WHEN fare_valid THEN GREATEST(COALESCE(total_amount,0),0) ELSE 0 END) AS total_amount_sum,
SUM(CASE WHEN fare_valid THEN GREATEST(COALESCE(congestion_surcharge,0),0)
    + GREATEST(COALESCE(cbd_congestion_fee,0),0) ELSE 0 END) AS congestion_fee_sum
"""


def prepare(spark, raw, zones, start: str, end: str):
    """Source timestamps are NYC local wall-clock values; never relabel them UTC."""
    raw.createOrReplaceTempView("source_trips")
    zones.createOrReplaceTempView("zone_lookup")
    # Dates below are supplied by datetime.date, not arbitrary user SQL.
    clean = spark.sql(f"""
      WITH base AS (
        SELECT *, CAST(tpep_pickup_datetime AS DATE) AS date,
          HOUR(tpep_pickup_datetime) AS hour,
          CAST(PULocationID AS INT) AS zone_id,
          CAST(DOLocationID AS INT) AS dropoff_zone,
          (unix_timestamp(tpep_dropoff_datetime)-unix_timestamp(tpep_pickup_datetime))/60.0
            AS duration_min
        FROM source_trips
      )
      SELECT b.*, z.Borough AS borough,
        COALESCE(trip_distance >= 0 AND trip_distance <= 100, FALSE) AS distance_valid,
        COALESCE(trip_distance > 0 AND trip_distance <= 100 AND duration_min >= 1
          AND duration_min <= 240 AND trip_distance / (duration_min/60) <= 100, FALSE)
          AS efficiency_valid,
        COALESCE(fare_amount >= 0 AND fare_amount <= 1000, FALSE) AS fare_valid
      FROM base b LEFT JOIN zone_lookup z ON b.zone_id = z.LocationID
      WHERE date >= DATE '{start}' AND date <= DATE '{end}'
    """)
    return clean


def zone_documents(csv_path: Path, geometry_zip: Path | None) -> list[dict]:
    with csv_path.open(encoding="utf-8-sig") as stream:
        documents = [
            {
                "zone_id": int(r["LocationID"]),
                "borough": r["Borough"],
                "name": r["Zone"],
                "service_zone": r["service_zone"],
                "geometry": None,
            }
            for r in csv.DictReader(stream)
        ]
    if geometry_zip:
        import tempfile
        import zipfile

        import shapefile
        from pyproj import CRS, Transformer

        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(geometry_zip) as archive:
                root = Path(directory).resolve()
                for member in archive.infolist():
                    if not (root / member.filename).resolve().is_relative_to(root):
                        raise ValueError("Unsafe geometry archive")
                archive.extractall(root)
            shp = next(root.rglob("*.shp"))
            transformer = Transformer.from_crs(
                CRS.from_wkt(shp.with_suffix(".prj").read_text()), 4326, always_xy=True
            )

            def convert(coordinates):
                if coordinates and isinstance(coordinates[0], (int, float)):
                    return list(transformer.transform(*coordinates[:2]))
                return [convert(c) for c in coordinates]

            by_id = {d["zone_id"]: d for d in documents}
            with shapefile.Reader(str(shp)) as reader:
                for record in reader.iterShapeRecords():
                    zone_id = int(record.record.as_dict()["LocationID"])
                    geometry = record.shape.__geo_interface__
                    geometry["coordinates"] = convert(geometry["coordinates"])
                    if zone_id in by_id:
                        by_id[zone_id]["geometry"] = geometry
    return documents


def run(
    spark,
    inputs: list[str],
    zone_csv: Path,
    geometry_zip: Path | None,
    output: Path,
    start: str,
    end: str,
    run_id: str,
) -> dict:
    from pyspark import StorageLevel
    from pyspark.sql import functions as F

    started = time.perf_counter()
    spark.conf.set("spark.sql.session.timeZone", "America/New_York")
    spark.conf.set("spark.sql.ansi.enabled", "false")
    raw = spark.read.parquet(*inputs)
    required = {
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "trip_distance",
        "fare_amount",
        "payment_type",
    }
    if missing := required - set(raw.columns):
        raise ValueError(f"Missing required source columns: {sorted(missing)}")
    for optional in ("tip_amount", "total_amount", "congestion_surcharge", "cbd_congestion_fee"):
        if optional not in raw.columns:
            raw = raw.withColumn(optional, F.lit(None).cast("double"))
    source_rows = raw.count()
    zones = spark.read.option("header", True).option("inferSchema", True).csv(str(zone_csv))
    raw = raw.select(
        *sorted(
            required | {"tip_amount", "total_amount", "congestion_surcharge", "cbd_congestion_fee"}
        )
    )
    clean = prepare(spark, raw, zones, start, end).persist(StorageLevel.DISK_ONLY)
    clean.createOrReplaceTempView("trips")
    quality = (
        spark.sql("""SELECT COUNT(*) AS in_period_rows,
      SUM(CASE WHEN borough IS NULL THEN 1 ELSE 0 END) AS unknown_pickup_zone,
      SUM(CASE WHEN NOT distance_valid THEN 1 ELSE 0 END) AS invalid_distance,
      SUM(CASE WHEN NOT efficiency_valid THEN 1 ELSE 0 END) AS efficiency_excluded,
      SUM(CASE WHEN NOT fare_valid THEN 1 ELSE 0 END) AS fare_excluded
      FROM trips""")
        .first()
        .asDict()
    )
    quality = {k: int(v or 0) for k, v in quality.items()}
    quality.update(
        source_rows=source_rows, outside_period_rows=source_rows - quality["in_period_rows"]
    )
    # Preserve valid demand even when the same row is ineligible for another metric.
    valid = clean.filter("borough IS NOT NULL")
    valid.createOrReplaceTempView("eligible_trips")
    output.mkdir(parents=True, exist_ok=True)
    export = output / "serving"
    export.mkdir(exist_ok=True)
    counts = {}

    def save(name, frame):
        # All exported frames have explicit low-cardinality bounds, never raw trips.
        frame = frame.persist(StorageLevel.MEMORY_AND_DISK)
        count = frame.count()
        if count > 2_000_000:
            raise ValueError(f"Serving output too large: {name} ({count})")
        frame.write.mode("overwrite").parquet(str(output / "parquet" / name))
        with (export / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for row in frame.toJSON().toLocalIterator():
                stream.write(row + "\n")
        counts[name] = count
        frame.unpersist()
        print(f"Saved {name}: {count:,} aggregate documents", flush=True)

    daily = spark.sql(
        f"SELECT date,zone_id,borough,{METRICS} FROM eligible_trips GROUP BY date,zone_id,borough"
    )
    hourly = spark.sql(
        f"SELECT date,hour,zone_id,borough,{METRICS} FROM eligible_trips "
        "GROUP BY date,hour,zone_id,borough"
    )
    save("demand_daily", daily)
    save("demand_hourly", hourly)
    save(
        "trip_efficiency",
        hourly.select(
            "date",
            "hour",
            "zone_id",
            "borough",
            "trip_count",
            "efficiency_count",
            "duration_sum",
            "efficiency_distance_sum",
            "distance_sum",
            "distance_count",
        ),
    )
    fare_columns = []
    for low, high, label in [
        (0, 10, "0_10"),
        (10, 20, "10_20"),
        (20, 30, "20_30"),
        (30, 50, "30_50"),
        (50, 100, "50_100"),
        (100, 1001, "100_plus"),
    ]:
        fare_columns.append(
            f"SUM(CASE WHEN fare_valid AND fare_amount >= {low} "
            f"AND fare_amount < {high} THEN 1 ELSE 0 END) AS bin_{label}"
        )
    for code, label in [
        (1, "card"),
        (2, "cash"),
        (3, "no_charge"),
        (4, "dispute"),
        (5, "unknown"),
        (6, "voided"),
    ]:
        fare_columns.append(f"SUM(CASE WHEN payment_type={code} THEN 1 ELSE 0 END) AS pay_{label}")
    fare_columns.append(
        "SUM(CASE WHEN payment_type IS NULL OR payment_type NOT IN "
        "(1,2,3,4,5,6) THEN 1 ELSE 0 END) AS pay_other"
    )
    save(
        "fare_analytics",
        spark.sql(
            "SELECT date,zone_id,borough,"
            + METRICS
            + ","
            + ",".join(fare_columns)
            + " FROM eligible_trips GROUP BY date,zone_id,borough"
        ),
    )
    save(
        "route_flows",
        spark.sql("""WITH routes AS (
      SELECT date,zone_id AS pickup_zone,dropoff_zone,borough,COUNT(*) AS trip_count
      FROM eligible_trips WHERE dropoff_zone IN (SELECT LocationID FROM zone_lookup)
      GROUP BY date,zone_id,dropoff_zone,borough
    ), ranked AS (
      SELECT *,ROW_NUMBER() OVER(
        PARTITION BY date ORDER BY trip_count DESC,pickup_zone,dropoff_zone)
        AS rank FROM routes
    ) SELECT * FROM ranked WHERE rank <= 100"""),
    )
    documents = zone_documents(zone_csv, geometry_zip)
    with (export / "zones.jsonl").open("w", encoding="utf-8") as stream:
        for document in documents:
            stream.write(json.dumps(document, separators=(",", ":")) + "\n")
    counts["zones"] = len(documents)
    reconciliation = daily.agg(F.sum("trip_count")).first()[0] or 0
    expected = quality["in_period_rows"] - quality["unknown_pickup_zone"]
    if reconciliation != expected:
        raise ValueError(f"Demand reconciliation failed: {reconciliation} != {expected}")
    manifest = {
        "run_id": run_id,
        "etl_version": VERSION,
        "status": "validated",
        "start_date": start,
        "end_date": end,
        "source_rows": source_rows,
        "eligible_demand_rows": int(reconciliation),
        "quality": quality,
        "collection_counts": counts,
        "route_coverage": "top_100_routes_per_day",
        "created_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": time.perf_counter() - started,
        "engine": "Apache Spark SQL",
        "spark_version": spark.version,
        "partitions": int(spark.conf.get("spark.sql.shuffle.partitions")),
        "machine": {"platform": platform.platform(), "python": platform.python_version()},
        "eligibility": {
            "distance_miles": "0–100",
            "efficiency": "distance >0 and <=100 mi; duration 1–240 min; speed <=100 mph",
            "fare_usd": "0–1000; negative/refund rows excluded from fare metrics only",
        },
    }
    (export / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    clean.unpersist()
    return manifest


def main():
    from pyspark.sql import SparkSession

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--zones", type=Path, required=True)
    parser.add_argument("--geometry", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=lambda x: datetime.fromisoformat(x).date(), required=True)
    parser.add_argument("--end", type=lambda x: datetime.fromisoformat(x).date(), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--partitions", type=int, default=8)
    args = parser.parse_args()
    if args.start > args.end or not 1 <= args.partitions <= 200:
        parser.error("Invalid period or partition count")
    spark = (
        SparkSession.builder.appName("UrbanFlow")
        .config("spark.sql.shuffle.partitions", str(args.partitions))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        print(
            json.dumps(
                run(
                    spark,
                    args.input,
                    args.zones,
                    args.geometry,
                    args.output,
                    str(args.start),
                    str(args.end),
                    args.run_id,
                ),
                indent=2,
            )
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
