"""Run in Colab or a Java/PySpark development environment."""

import pytest

pyspark = pytest.importorskip("pyspark")

from urbanflow_etl.analytics.job import METRICS, prepare  # noqa: E402


def test_metric_populations_and_month_boundaries():
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.master("local[2]").appName("UrbanFlow-correctness").getOrCreate()
    try:
        raw = spark.sql("""SELECT * FROM VALUES
          (TIMESTAMP '2025-01-01 00:01:00', TIMESTAMP '2025-01-01 00:11:00',1,2,2.0,10.0),
          (TIMESTAMP '2025-01-01 00:02:00', TIMESTAMP '2025-01-01 00:02:00',1,2,0.0,-5.0),
          (TIMESTAMP '2024-12-31 23:59:00', TIMESTAMP '2025-01-01 00:10:00',1,2,2.0,8.0),
          (TIMESTAMP '2025-01-01 00:03:00', TIMESTAMP '2025-01-01 00:13:00',999,2,1.0,3.0)
          AS t(tpep_pickup_datetime,tpep_dropoff_datetime,PULocationID,DOLocationID,
               trip_distance,fare_amount)""")
        zones = spark.sql("SELECT 1 AS LocationID,'Manhattan' AS Borough")
        for name in ("tip_amount", "total_amount", "congestion_surcharge", "cbd_congestion_fee"):
            from pyspark.sql.functions import lit

            raw = raw.withColumn(name, lit(0.0))
        clean = prepare(spark, raw, zones, "2025-01-01", "2025-01-31")
        assert clean.count() == 3
        clean.filter("borough IS NOT NULL").createOrReplaceTempView("fixture")
        totals = spark.sql(f"SELECT {METRICS} FROM fixture").first().asDict()
        assert totals["trip_count"] == 2
        assert totals["efficiency_count"] == 1
        assert totals["fare_count"] == 1
        assert totals["fare_sum"] == 10
        assert totals["duration_sum"] == 10
        assert totals["efficiency_distance_sum"] == 2
    finally:
        spark.stop()
