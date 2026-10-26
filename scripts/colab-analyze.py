"""Execute reusable Spark analysis on public source data, then archive small outputs."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

os.environ["PYSPARK_SUBMIT_ARGS"] = "--driver-memory 4g pyspark-shell"

bundle = Path("/content/urbanflow-analytics.zip")
if hashlib.sha256(bundle.read_bytes()).hexdigest() != os.environ["URBANFLOW_BUNDLE_SHA256"]:
    raise ValueError("Source archive checksum mismatch")
root = Path("/content/urbanflow-analytics").resolve()
root.mkdir(exist_ok=True)
with ZipFile(bundle) as archive:
    for item in archive.infolist():
        if not (root / item.filename).resolve().is_relative_to(root):
            raise ValueError("Unsafe source archive path")
    archive.extractall(root)
sys.path.insert(0, str(root / "pipelines" / "src"))
os.environ["PYTHONPATH"] = str(root / "pipelines" / "src")
subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        str(root / "pipelines" / "tests"),
        "--basetemp=/content/urbanflow-test-temp",
    ],
    check=True,
)

from pyspark.sql import SparkSession  # noqa: E402
from urbanflow_etl.analytics.job import run  # noqa: E402
from urbanflow_etl.benchmarking.job import run as benchmark  # noqa: E402
from urbanflow_etl.ingestion.download import download_dataset  # noqa: E402

raw = Path("/content/urbanflow-data/raw")
quarter = os.environ.get("URBANFLOW_PERIOD") == "q1"
config_name = "yellow-2025-q1.json" if quarter else "yellow-2025-01.json"
config = json.loads((root / "configs" / config_name).read_text())
download_dataset(config, raw)
spark = (
    SparkSession.builder.appName("UrbanFlow January 2025")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")
output = Path("/content/urbanflow-results")
try:
    inputs = [str(raw / f["name"]) for f in config["files"] if f["kind"] == "parquet"]
    manifest = run(
        spark,
        inputs,
        raw / "taxi_zone_lookup.csv",
        raw / "taxi_zones.zip",
        output,
        "2025-01-01",
        "2025-03-31" if quarter else "2025-01-31",
        "yellow-2025-q1-v1" if quarter else "yellow-2025-01-v2",
    )
    benchmark(spark, inputs, output / "serving")
    print("ANALYSIS_VALIDATED", json.dumps(manifest), flush=True)
finally:
    spark.stop()
shutil.make_archive("/content/urbanflow-serving", "zip", output / "serving")
print("READY /content/urbanflow-serving.zip", flush=True)
