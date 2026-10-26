"""Real MongoDB publication checks, opt-in with URBANFLOW_TEST_MONGODB_URI."""

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from pymongo import MongoClient
from urbanflow_etl.publishing.mongo import publish


def test_idempotent_publication_and_failed_version_isolation(tmp_path, monkeypatch):
    uri = os.environ.get("URBANFLOW_TEST_MONGODB_URI")
    if not uri:
        pytest.skip("Set URBANFLOW_TEST_MONGODB_URI for real database integration")
    database = "urbanflow_test_" + uuid.uuid4().hex
    client = MongoClient(uri)
    manifest = {
        "run_id": "fixture-v1",
        "etl_version": "test",
        "status": "validated",
        "start_date": "2025-01-01",
        "end_date": "2025-01-01",
        "source_rows": 2,
        "eligible_demand_rows": 2,
        "quality": {},
        "collection_counts": {"demand_daily": 1},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "demand_daily.jsonl").write_text(
        json.dumps({"date": "2025-01-01", "zone_id": 1, "trip_count": 2}) + "\n"
    )
    try:
        from pymongo.synchronous.collection import Collection

        original_insert = Collection.insert_one
        barrier = Barrier(2)

        def synchronized_insert(collection, document, *args, **kwargs):
            if collection.name == "dataset_runs":
                barrier.wait(timeout=10)
            return original_insert(collection, document, *args, **kwargs)

        def attempt():
            try:
                return publish(tmp_path, uri, database)["status"]
            except ValueError as error:
                assert "already in progress" in str(error)
                return "in_progress"

        with monkeypatch.context() as patch:
            patch.setattr(Collection, "insert_one", synchronized_insert)
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(lambda _: attempt(), range(2)))
        assert outcomes.count("published") == 1
        assert set(outcomes) <= {"published", "already_published", "in_progress"}
        assert publish(tmp_path, uri, database)["status"] == "already_published"
        assert client[database].demand_daily.count_documents({}) == 1
        # A changed value with identical manifest counts still violates immutability.
        payload = tmp_path / "demand_daily.jsonl"
        original = payload.read_text()
        payload.write_text(original.replace('"trip_count": 2', '"trip_count": 9'))
        with pytest.raises(ValueError, match="immutable"):
            publish(tmp_path, uri, database)
        payload.write_text(original)
        manifest["run_id"] = "fixture-v2"
        manifest["eligible_demand_rows"] = 999
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))
        with pytest.raises(ValueError, match="reconciliation"):
            publish(tmp_path, uri, database)
        failed = client[database].dataset_runs.find_one({"_id": "fixture-v2"})
        assert failed["status"] == "failed"
        # The same failed version may retry without accumulating duplicate documents.
        with pytest.raises(ValueError, match="reconciliation"):
            publish(tmp_path, uri, database)
        assert client[database].demand_daily.count_documents({"run_id": "fixture-v2"}) == 1
        assert (
            client[database].dataset_publications.find_one({"_id": "current"})["run_id"]
            == "fixture-v1"
        )
    finally:
        client.drop_database(database)
        client.close()
