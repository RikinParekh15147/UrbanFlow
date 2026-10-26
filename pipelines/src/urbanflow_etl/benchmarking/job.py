import json
import os
import platform
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path


def run(spark, inputs: list[str], output: Path, sizes=(10_000, 100_000, 1_000_000), repeats=3):
    import pandas as pd
    import psutil
    from pyspark.sql import functions as F

    frame = spark.read.parquet(*inputs).select("PULocationID")
    total = frame.count()
    experiments = []
    machine = {
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / 1024**3, 2),
        "python": platform.python_version(),
        "spark": spark.version,
        "pandas": pd.__version__,
    }
    for size in sorted(set([min(n, total) for n in sizes] + [total])):
        sample = output.parent / "benchmark-input" / str(size)
        frame.limit(size).coalesce(1).write.mode("overwrite").parquet(str(sample))
        input_bytes = sum(p.stat().st_size for p in sample.glob("*.parquet"))
        timings = {"Pandas": [], "Spark SQL": []}
        expected = None
        for repetition in range(repeats):
            # Alternate the order to reduce a systematic page-cache advantage.
            engines = ["Pandas", "Spark SQL"] if repetition % 2 == 0 else ["Spark SQL", "Pandas"]
            for engine in engines:
                start = time.perf_counter()
                if engine == "Pandas":
                    data = pd.read_parquet(sample)
                    counts = data["PULocationID"].fillna(-1).astype(int).value_counts()
                    result = {int(k): int(v) for k, v in counts.items()}
                else:
                    data = spark.read.parquet(str(sample)).select(
                        F.coalesce(F.col("PULocationID"), F.lit(-1)).alias("zone")
                    )
                    data.createOrReplaceTempView("benchmark_trips")
                    result = {
                        int(r.zone): int(r.n)
                        for r in spark.sql(
                            "SELECT zone,COUNT(*) n FROM benchmark_trips GROUP BY zone"
                        ).collect()
                    }
                    # collect is bounded by 266 zone groups, not raw records.
                elapsed = (time.perf_counter() - start) * 1000
                if expected is None:
                    expected = result
                if result != expected or sum(result.values()) != size:
                    raise ValueError("Benchmark outputs differ between engines")
                timings[engine].append(elapsed)
        for engine, times in timings.items():
            experiments.append(
                {
                    "experiment_id": f"zone-count-{size}-{engine.replace(' ', '-').lower()}",
                    "engine": engine,
                    "task": "Parquet read and pickup-zone trip counts",
                    "input_rows": size,
                    "input_bytes": input_bytes,
                    "repetitions": repeats,
                    "elapsed_ms": round(statistics.median(times), 3),
                    "min_ms": round(min(times), 3),
                    "max_ms": round(max(times), 3),
                    "samples_ms": [round(t, 3) for t in times],
                    "correctness_verified": True,
                    "partitions": int(spark.conf.get("spark.sql.shuffle.partitions"))
                    if engine == "Spark SQL"
                    else 1,
                    "startup_included": False,
                    "machine": machine,
                    "measured_at": datetime.now(UTC).isoformat(),
                }
            )
        print(f"Benchmarked {size:,} rows, {repeats} repetitions per engine", flush=True)
    with (output / "benchmarks.jsonl").open("w", encoding="utf-8") as stream:
        for item in experiments:
            stream.write(json.dumps(item) + "\n")
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["collection_counts"]["benchmarks"] = len(experiments)
    manifest["machine"] = machine
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return experiments
