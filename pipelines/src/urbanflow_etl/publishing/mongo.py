import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

KEYS = {
    "zones": ["zone_id"],
    "demand_daily": ["date", "zone_id"],
    "demand_hourly": ["date", "hour", "zone_id"],
    "trip_efficiency": ["date", "hour", "zone_id"],
    "fare_analytics": ["date", "zone_id"],
    "route_flows": ["date", "pickup_zone", "dropoff_zone"],
    "benchmarks": ["experiment_id"],
}


def publish(directory: Path, uri: str, database: str = "urbanflow") -> dict:
    from pymongo import MongoClient, ReplaceOne
    from pymongo.errors import DuplicateKeyError

    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("status") != "validated":
        raise ValueError("Only validated analytical outputs can be published")
    run_id = manifest["run_id"]
    # Include actual payload bytes: equal counts do not imply equal analytical values.
    file_hashes = {}
    for collection in manifest["collection_counts"]:
        if collection not in KEYS:
            raise ValueError(f"Unexpected collection: {collection}")
        path = directory / f"{collection}.jsonl"
        with path.open("rb") as stream:
            file_hashes[collection] = hashlib.file_digest(stream, "sha256").hexdigest()
    identity = {"manifest": manifest, "file_hashes": file_hashes}
    signature = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    claim_id = uuid4().hex
    claimed = False
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        db = client[database]
        run = {
            "_id": run_id,
            **manifest,
            "signature": signature,
            "status": "staging",
            "claim_id": claim_id,
        }
        try:
            # Unique _id makes the first writer the sole owner of this version.
            db.dataset_runs.insert_one(run)
            claimed = True
        except DuplicateKeyError:
            prior = db.dataset_runs.find_one({"_id": run_id})
            if not prior or prior.get("signature") != signature:
                raise ValueError(
                    "run_id is immutable: use a new version for changed outputs"
                ) from None
            if prior.get("status") == "published":
                return {"run_id": run_id, "status": "already_published"}
            # A failed attempt can be retried, but an active writer cannot be displaced.
            result = db.dataset_runs.replace_one(
                {"_id": run_id, "signature": signature, "status": "failed"}, run
            )
            if not result.modified_count:
                raise ValueError("Publication is already in progress for this run_id") from None
            claimed = True
        for collection, expected in manifest["collection_counts"].items():
            if collection not in KEYS:
                raise ValueError(f"Unexpected collection: {collection}")
            path = directory / f"{collection}.jsonl"
            batch = []
            seen = 0
            payload_hash = hashlib.sha256()
            with path.open("rb") as stream:
                for line in stream:
                    payload_hash.update(line)
                    doc = json.loads(line)
                    doc["run_id"] = run_id
                    dimensions = [doc[k] for k in KEYS[collection]]
                    doc["_id"] = f"{run_id}:{collection}:" + json.dumps(
                        dimensions, separators=(",", ":")
                    )
                    batch.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))
                    seen += 1
                    if len(batch) >= 1000:
                        db[collection].bulk_write(batch, ordered=False)
                        batch = []
                if batch:
                    db[collection].bulk_write(batch, ordered=False)
            if payload_hash.hexdigest() != file_hashes[collection]:
                raise ValueError(f"Payload changed during publication: {collection}")
            actual = db[collection].count_documents({"run_id": run_id})
            if actual != expected or seen != expected:
                raise ValueError(f"Count mismatch in {collection}: {actual}/{seen}/{expected}")
            db[collection].create_index([("run_id", 1), ("date", 1), ("zone_id", 1)])
            db[collection].create_index([("run_id", 1), ("borough", 1), ("date", 1)])
        demand_total = list(
            db.demand_daily.aggregate(
                [
                    {"$match": {"run_id": run_id}},
                    {"$group": {"_id": None, "n": {"$sum": "$trip_count"}}},
                ]
            )
        )
        actual_trips = demand_total[0]["n"] if demand_total else 0
        if actual_trips != manifest["eligible_demand_rows"]:
            raise ValueError("Published demand failed source reconciliation")
        published_at = datetime.now(UTC).isoformat()
        db.dataset_runs.update_one(
            {"_id": run_id, "claim_id": claim_id, "status": "staging"},
            {
                "$set": {
                    "status": "published",
                    "published_at": published_at,
                }
            },
        )
        # All collections validated first. A single atomic document switches the version.
        db.dataset_publications.replace_one(
            {"_id": "current"},
            {
                "_id": "current",
                "run_id": run_id,
                "published_at": published_at,
            },
            upsert=True,
        )
        return {
            "run_id": run_id,
            "status": "published",
            "published_at": published_at,
            "storage": db.command("dbStats", scale=1024 * 1024),
        }
    except Exception:
        if claimed:
            # Preserve the active version and permit an identical failed attempt to retry.
            db.dataset_runs.update_one(
                {"_id": run_id, "claim_id": claim_id, "status": "staging"},
                {"$set": {"status": "failed"}},
            )
        raise
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--uri", default=os.environ.get("URBANFLOW_MONGODB_URI"))
    parser.add_argument("--database", default="urbanflow")
    args = parser.parse_args()
    if not args.uri:
        parser.error("Set URBANFLOW_MONGODB_URI or provide --uri")
    print(json.dumps(publish(args.input, args.uri, args.database), default=str, indent=2))


if __name__ == "__main__":
    main()
