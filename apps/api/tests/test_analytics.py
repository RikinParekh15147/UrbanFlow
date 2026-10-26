import json
import os
from uuid import uuid4

import pytest
from app.main import app
from app.repositories.analytics import MongoRepository, SnapshotRepository, repository
from fastapi.testclient import TestClient


@pytest.fixture(params=["snapshot", "mongodb"])
def analytical_client(tmp_path, request):
    uri = os.environ.get("URBANFLOW_TEST_MONGODB_URI")
    if request.param == "mongodb" and not uri:
        pytest.skip("Set URBANFLOW_TEST_MONGODB_URI for real database integration")
    manifest = {
        "run_id": "fixture-v1",
        "status": "published",
        "start_date": "2025-01-01",
        "end_date": "2025-01-02",
        "quality": {},
        "machine": {},
        "route_coverage": "top_100_routes_per_day",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    rows = [
        {
            "date": "2025-01-01",
            "zone_id": 1,
            "borough": "Manhattan",
            "hour": 8,
            "trip_count": 2,
            "fare_sum": 20,
            "fare_count": 2,
            "duration_sum": 10,
            "efficiency_count": 1,
            "efficiency_distance_sum": 2,
            "distance_sum": 2,
            "distance_count": 2,
        },
        {
            "date": "2025-01-02",
            "zone_id": 1,
            "borough": "Manhattan",
            "hour": 9,
            "trip_count": 1,
            "fare_sum": 100,
            "fare_count": 1,
            "duration_sum": 20,
            "efficiency_count": 1,
            "efficiency_distance_sum": 10,
            "distance_sum": 10,
            "distance_count": 1,
        },
        {
            "date": "2025-01-01",
            "zone_id": 2,
            "borough": "Queens",
            "hour": 10,
            "trip_count": 4,
            "fare_sum": 40,
            "fare_count": 4,
            "duration_sum": 80,
            "efficiency_count": 4,
            "efficiency_distance_sum": 8,
            "distance_sum": 8,
            "distance_count": 4,
        },
    ]
    zones = [
        {
            "zone_id": 1,
            "name": "Fixture A",
            "borough": "Manhattan",
            "geometry": {"type": "Polygon", "coordinates": []},
        },
        {
            "zone_id": 2,
            "name": "Fixture B",
            "borough": "Queens",
            "geometry": {"type": "Polygon", "coordinates": []},
        },
    ]
    for name, documents in {
        "zones": zones,
        "demand_daily": rows,
        "demand_hourly": rows,
        "trip_efficiency": rows,
    }.items():
        (tmp_path / f"{name}.jsonl").write_text("\n".join(json.dumps(row) for row in documents))
    if request.param == "snapshot":
        store = SnapshotRepository(str(tmp_path))
    else:
        store = MongoRepository(uri, "urbanflow_api_test_" + uuid4().hex)
        store.db.dataset_runs.insert_one({"_id": manifest["run_id"], **manifest})
        store.db.dataset_publications.insert_one({"_id": "current", "run_id": manifest["run_id"]})
        for path in tmp_path.glob("*.jsonl"):
            documents = [
                {**json.loads(line), "run_id": manifest["run_id"]}
                for line in path.read_text().splitlines()
            ]
            store.db[path.stem].insert_many(documents)
    app.dependency_overrides[repository] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        if request.param == "mongodb":
            store.client.drop_database(store.db.name)
            store.client.close()


def test_weighted_metrics_use_eligible_counts(analytical_client):
    result = analytical_client.get("/api/v1/overview?zone_id=1").json()
    assert result["meta"]["run_id"] == "fixture-v1"
    assert result["metrics"]["trip_count"] == 3
    assert result["metrics"]["avg_fare"] == 40
    assert result["metrics"]["avg_duration_min"] == 15
    assert result["metrics"]["speed_mph"] == 24
    assert len(result["daily"]) == 2


def test_filters_and_empty_selection(analytical_client):
    result = analytical_client.get("/api/v1/overview?borough=Queens").json()
    assert result["metrics"]["trip_count"] == 4
    empty = analytical_client.get("/api/v1/overview?zone_id=3").json()
    assert empty["metrics"]["trip_count"] == 0
    assert empty["metrics"]["avg_fare"] is None
    assert empty["daily"] == []


@pytest.mark.parametrize(
    "query",
    [
        "start_date=2025-01-02&end_date=2025-01-01",
        "start_date=2024-12-31",
        "zone_id=999",
        "borough=Invalid",
    ],
)
def test_invalid_filters_are_rejected(analytical_client, query):
    result = analytical_client.get("/api/v1/overview?" + query)
    assert result.status_code == 422
    assert "error" in result.json()


def test_pinned_version_and_pagination(analytical_client):
    assert analytical_client.get("/api/v1/overview?run_id=unknown").status_code == 404
    zones = analytical_client.get("/api/v1/zones?limit=1&offset=1").json()
    assert zones["total"] == 2
    assert len(zones["data"]) == 1
    series = analytical_client.get("/api/v1/demand/hourly").json()
    assert sum(row["trip_count"] for row in series["data"]) == 7


def test_geography_marks_zone_selection_and_keeps_city_context(analytical_client):
    response = analytical_client.get("/api/v1/geography/heatmap?zone_id=1")
    assert response.status_code == 200
    features = response.json()["features"]
    assert [feature["id"] for feature in features] == [1, 2]
    assert features[0]["properties"]["trip_count"] == 3
    assert features[0]["properties"]["in_selection"] is True
    assert features[1]["properties"]["in_selection"] is False


def test_repository_rejects_unavailable_version(analytical_client):
    store = app.dependency_overrides[repository]()
    assert store.rows("zones", "missing-version") == []
    assert store.grouped("demand_hourly", "missing-version", {}, ["hour"]) == []


def test_grouped_and_ungrouped_metrics_reconcile(analytical_client):
    total = analytical_client.get("/api/v1/overview?zone_id=1").json()["metrics"]
    hourly = analytical_client.get("/api/v1/demand/hourly?zone_id=1").json()["data"]
    assert sum(row["trip_count"] for row in hourly) == total["trip_count"]
    assert sum(row["total_fare"] for row in hourly) == total["total_fare"]
    efficiency = analytical_client.get("/api/v1/trips/efficiency?zone_id=1").json()["data"]
    assert efficiency[0]["avg_duration_min"] == total["avg_duration_min"]
    assert efficiency[0]["speed_mph"] == total["speed_mph"]
