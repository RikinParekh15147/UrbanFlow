"""Filter-aware, weighted summaries from small serving aggregates."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Annotated

from app.models.contracts import Meta
from app.repositories.analytics import repository
from fastapi import Depends, HTTPException, Query


@dataclass
class Context:
    store: object
    manifest: dict
    meta: Meta
    filters: dict

    def rows(self, name: str, group_keys: list[str] | None = None):
        if group_keys:
            return self.store.grouped(name, self.meta.run_id, self.filters, group_keys)
        return self.store.rows(name, self.meta.run_id, self.filters)

    def zones(self):
        return {r["zone_id"]: r for r in self.store.rows("zones", self.meta.run_id)}


def context(
    start_date: date | None = None,
    end_date: date | None = None,
    borough: Annotated[str | None, Query(max_length=60)] = None,
    zone_id: Annotated[int | None, Query(ge=1, le=265)] = None,
    run_id: Annotated[str | None, Query(max_length=100, pattern=r"^[\w.-]+$")] = None,
    store=Depends(repository),
) -> Context:
    manifest = store.manifest(run_id)
    if not manifest:
        raise HTTPException(
            404 if run_id else 503,
            "Requested dataset version is unavailable"
            if run_id
            else "No validated dataset is published. Run the publishing job first.",
        )
    start = start_date or date.fromisoformat(manifest["start_date"])
    end = end_date or date.fromisoformat(manifest["end_date"])
    if start > end:
        raise HTTPException(422, "start_date must be on or before end_date")
    if (end - start).days > 365:
        raise HTTPException(422, "Select a date range of at most 366 days")
    if str(start) < manifest["start_date"] or str(end) > manifest["end_date"]:
        raise HTTPException(
            422, f"Available dates: {manifest['start_date']} to {manifest['end_date']}"
        )
    filters = {"date": {"$gte": str(start), "$lte": str(end)}}
    if borough:
        allowed = {r["borough"] for r in store.rows("zones", manifest["run_id"])}
        if borough not in allowed:
            raise HTTPException(422, "Unknown borough")
        filters["borough"] = borough
    if zone_id:
        filters["zone_id"] = zone_id
    meta = Meta(
        run_id=manifest["run_id"],
        start_date=str(start),
        end_date=str(end),
        available_start=manifest["start_date"],
        available_end=manifest["end_date"],
        source=store.source,
        zone_id=zone_id,
        borough=borough,
    )
    return Context(store, manifest, meta, filters)


def sum_rows(rows):
    totals = defaultdict(float)
    for row in rows:
        for key, value in row.items():
            if isinstance(value, (float, int)) and key not in {"zone_id", "hour", "rank"}:
                totals[key] += value
    return dict(totals)


def ratio(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else None


def metrics(totals):
    return {
        "trip_count": int(totals.get("trip_count", 0)),
        "avg_distance_miles": ratio(totals.get("distance_sum", 0), totals.get("distance_count", 0)),
        "avg_duration_min": ratio(totals.get("duration_sum", 0), totals.get("efficiency_count", 0)),
        "avg_fare": ratio(totals.get("fare_sum", 0), totals.get("fare_count", 0)),
        "speed_mph": ratio(
            totals.get("efficiency_distance_sum", 0) * 60, totals.get("duration_sum", 0)
        ),
        "total_fare": round(totals.get("fare_sum", 0), 2),
        "efficiency_count": int(totals.get("efficiency_count", 0)),
        "fare_count": int(totals.get("fare_count", 0)),
    }


def group(rows, keys: list[str], zones=None):
    buckets = defaultdict(list)
    for row in rows:
        buckets[tuple(row.get(k) for k in keys)].append(row)
    result = []
    for dimensions, values in buckets.items():
        item = {**dict(zip(keys, dimensions)), **metrics(sum_rows(values))}
        if zones and "zone_id" in item:
            zone = zones.get(item["zone_id"], {})
            item.update(name=zone.get("name", "Unknown zone"), borough=zone.get("borough"))
        result.append(item)
    return result
