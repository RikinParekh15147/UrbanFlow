"""Persist full curated trips and aggregate Parquet for reproducibility."""

import json
import shutil
from pathlib import Path

from pyspark.sql import SparkSession
from urbanflow_etl.analytics.job import prepare

root = Path("/content/urbanflow-results")
raw = Path("/content/urbanflow-data/raw")
spark = (
    SparkSession.builder.appName("UrbanFlow curated archive")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)
spark.conf.set("spark.sql.session.timeZone", "America/New_York")
spark.conf.set("spark.sql.ansi.enabled", "false")
spark.sparkContext.setLogLevel("ERROR")
manifest_path = root / "serving/manifest.json"
manifest = json.loads(manifest_path.read_text())
try:
    files = sorted(raw.glob("yellow_tripdata_2025-0[123].parquet"))
    frame = spark.read.parquet(*map(str, files))
    zones = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(str(raw / "taxi_zone_lookup.csv"))
    )
    clean = prepare(spark, frame, zones, manifest["start_date"], manifest["end_date"])
    clean.write.mode("overwrite").partitionBy("date").parquet(str(root / "curated"))
    rows = spark.read.parquet(str(root / "curated")).count()
    if rows != manifest["quality"]["in_period_rows"]:
        raise ValueError("Curated archive count does not reconcile")
    manifest["curated"] = {
        "rows": rows,
        "format": "Parquet",
        "partition_by": "date",
        "files": len(list((root / "curated").rglob("*.parquet"))),
    }
    source_manifest = json.loads((raw / "2025-q1-manifest.json").read_text())
    manifest["sources"] = source_manifest["files"]
    manifest["driver_memory"] = spark.sparkContext.getConf().get("spark.driver.memory")
    manifest["cache_policy"] = "DISK_ONLY for cleaned trip rows"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
finally:
    spark.stop()
shutil.make_archive("/content/urbanflow-serving", "zip", root / "serving")
shutil.make_archive("/content/urbanflow-reproducibility", "zip", root, base_dir="curated")
print("CURATED_ARCHIVE_VALIDATED", json.dumps(manifest["curated"]), flush=True)
