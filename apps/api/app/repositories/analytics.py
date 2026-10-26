"""Serving repositories; neither adapter reads raw trips or starts a Spark job."""

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ADDITIVE = [
    "trip_count",
    "distance_sum",
    "distance_count",
    "duration_sum",
    "efficiency_distance_sum",
    "efficiency_count",
    "fare_sum",
    "fare_count",
    "fare_distance_amount",
    "fare_distance_miles",
    "tip_sum",
    "total_amount_sum",
    "congestion_fee_sum",
]


class MongoRepository:
    source = "mongodb"

    def __init__(self, uri: str, database: str):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[database]

    def manifest(self, run_id: str | None = None):
        try:
            if run_id is None:
                publication = self.db.dataset_publications.find_one({"_id": "current"})
                if not publication:
                    return None
                run_id = publication["run_id"]
            return self.db.dataset_runs.find_one({"_id": run_id, "status": "published"}, {"_id": 0})
        except PyMongoError as error:
            raise HTTPException(
                503, "MongoDB is unavailable. Start the database or check its URI."
            ) from error

    def rows(self, collection: str, run_id: str, filters: dict | None = None):
        try:
            return list(self.db[collection].find({"run_id": run_id, **(filters or {})}, {"_id": 0}))
        except PyMongoError as error:
            raise HTTPException(
                503, "The analytical database is unavailable. Retry shortly."
            ) from error

    def grouped(self, collection: str, run_id: str, filters: dict, keys: list[str]):
        try:
            sums = {field: {"$sum": "$" + field} for field in ADDITIVE}
            return list(
                self.db[collection].aggregate(
                    [
                        {"$match": {"run_id": run_id, **filters}},
                        {"$group": {"_id": {k: "$" + k for k in keys}, **sums}},
                        {
                            "$project": {
                                "_id": 0,
                                **{k: "$_id." + k for k in keys},
                                **{field: 1 for field in ADDITIVE},
                            }
                        },
                    ],
                    maxTimeMS=15000,
                )
            )
        except PyMongoError as error:
            raise HTTPException(503, "The analytical query failed. Retry shortly.") from error


class SnapshotRepository:
    """Explicit offline demo adapter for the same verified aggregates shipped with desktop."""

    source = "local_snapshot"

    def __init__(self, path: str):
        self.path = Path(path)

    def manifest(self, run_id: str | None = None):
        path = self.path / "manifest.json"
        if not path.is_file():
            return None
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if run_id and run_id != manifest["run_id"]:
            return None
        return manifest

    def iterate(self, collection: str, filters: dict | None = None):
        path = self.path / f"{collection}.jsonl"
        if not path.is_file():
            return
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                matches = True
                for key, value in (filters or {}).items():
                    if isinstance(value, dict):
                        actual = row.get(key, "")
                        matches &= "$gte" not in value or actual >= value["$gte"]
                        matches &= "$lte" not in value or actual <= value["$lte"]
                    else:
                        matches &= row.get(key) == value
                if matches:
                    yield row

    def rows(self, collection: str, run_id: str, filters: dict | None = None):
        if not self.manifest(run_id):
            return []
        return list(self.iterate(collection, filters))

    def grouped(self, collection: str, run_id: str, filters: dict, keys: list[str]):
        if not self.manifest(run_id):
            return []
        output = {}
        for row in self.iterate(collection, filters):
            dimensions = tuple(row.get(k) for k in keys)
            if dimensions not in output:
                output[dimensions] = {**dict(zip(keys, dimensions)), **dict.fromkeys(ADDITIVE, 0)}
            for field in ADDITIVE:
                output[dimensions][field] += row.get(field, 0)
        return list(output.values())


@lru_cache
def repository():
    if settings.data_source == "snapshot":
        return SnapshotRepository(settings.snapshot_dir)
    return MongoRepository(settings.mongodb_uri, settings.mongodb_database)
