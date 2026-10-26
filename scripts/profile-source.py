"""Inspect actual source metadata without loading the entire month into memory."""

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, default=Path("data/raw/yellow_tripdata_2025-01.parquet"))
parser.add_argument("--output", type=Path, default=Path("data/reports/january-schema.json"))
args = parser.parse_args()
source = pq.ParquetFile(args.input)
required = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
}
missing = sorted(required - set(source.schema_arrow.names))
report = {
    "source_file": args.input.name,
    "rows": source.metadata.num_rows,
    "row_groups": source.metadata.num_row_groups,
    "bytes": args.input.stat().st_size,
    "columns": [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in source.schema_arrow
    ],
    "missing_required_columns": missing,
    "validation_scope": "Parquet metadata and required column presence; not trip-level quality",
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
if missing:
    raise SystemExit("Source schema is missing required columns")
