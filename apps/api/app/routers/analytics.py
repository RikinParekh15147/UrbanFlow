from typing import Annotated, Literal

from app.models.contracts import (
    BenchmarksResponse,
    DatasetStatus,
    FaresResponse,
    GeographyResponse,
    OverviewResponse,
    RoutesResponse,
    SeriesResponse,
    ZonesResponse,
)
from app.repositories.analytics import repository
from app.services.analytics import Context, context, group, metrics, ratio, sum_rows
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="/api/v1")
Ctx = Annotated[Context, Depends(context)]


@router.get("/datasets/status", response_model=DatasetStatus)
def dataset_status(store=Depends(repository)):
    manifest = store.manifest()
    return {
        "status": "published" if manifest else "not_published",
        "run_id": manifest["run_id"] if manifest else None,
        "source": store.source,
        "manifest": manifest,
    }


@router.get("/overview", response_model=OverviewResponse)
def overview(ctx: Ctx):
    rows = ctx.rows("demand_daily")
    return {
        "meta": ctx.meta,
        "metrics": metrics(sum_rows(rows)),
        "daily": sorted(group(rows, ["date"]), key=lambda r: r["date"]),
        "busiest_zones": sorted(
            group(rows, ["zone_id"], ctx.zones()), key=lambda r: -r["trip_count"]
        )[:10],
        "boroughs": sorted(group(rows, ["borough"]), key=lambda r: -r["trip_count"]),
    }


@router.get("/demand/daily", response_model=SeriesResponse)
def daily(ctx: Ctx):
    rows = sorted(group(ctx.rows("demand_daily"), ["date"]), key=lambda r: r["date"])
    return {"meta": ctx.meta, "data": rows, "total": len(rows), "limit": 366}


@router.get("/demand/hourly", response_model=SeriesResponse)
def hourly(ctx: Ctx, group_by: Literal["hour", "date_hour"] = "hour"):
    keys = ["date", "hour"] if group_by == "date_hour" else ["hour"]
    rows = sorted(
        group(ctx.rows("demand_hourly", keys), keys), key=lambda r: tuple(r[k] for k in keys)
    )
    return {"meta": ctx.meta, "data": rows, "total": len(rows), "limit": len(rows)}


@router.get("/zones", response_model=ZonesResponse)
def zones(
    store=Depends(repository),
    borough: str | None = None,
    run_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=265)] = 265,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    manifest = store.manifest(run_id)
    if not manifest:
        raise HTTPException(404 if run_id else 503, "No published dataset available")
    rows = store.rows("zones", manifest["run_id"], {"borough": borough} if borough else {})
    rows.sort(key=lambda r: r["name"])
    return {"run_id": manifest["run_id"], "data": rows[offset : offset + limit], "total": len(rows)}


@router.get("/zones/{id}/metrics", response_model=OverviewResponse)
def zone_metrics(id: int, ctx: Ctx):
    if id not in ctx.zones():
        raise HTTPException(404, "Unknown taxi zone")
    if ctx.meta.zone_id and ctx.meta.zone_id != id:
        raise HTTPException(422, "Path zone and zone_id filter must agree")
    ctx.filters["zone_id"] = id
    ctx.meta.zone_id = id
    return overview(ctx)


@router.get("/geography/heatmap", response_model=GeographyResponse)
def geography(ctx: Ctx):
    values = {r["zone_id"]: r for r in group(ctx.rows("demand_daily"), ["zone_id"])}
    features = []
    for zone in ctx.zones().values():
        if not zone.get("geometry"):
            continue
        if ctx.meta.borough and zone["borough"] != ctx.meta.borough:
            continue
        features.append(
            {
                "type": "Feature",
                "id": zone["zone_id"],
                "geometry": zone["geometry"],
                "properties": {
                    **{k: v for k, v in zone.items() if k not in {"geometry", "_id", "run_id"}},
                    **values.get(zone["zone_id"], {"trip_count": 0}),
                    "in_selection": ctx.meta.zone_id is None or zone["zone_id"] == ctx.meta.zone_id,
                },
            }
        )
    return {"meta": ctx.meta, "type": "FeatureCollection", "features": features}


@router.get("/routes/top", response_model=RoutesResponse)
def routes(
    ctx: Ctx,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filters = dict(ctx.filters)
    if "zone_id" in filters:
        filters["pickup_zone"] = filters.pop("zone_id")
    raw = ctx.store.rows("route_flows", ctx.meta.run_id, filters)
    values = {}
    for row in raw:
        key = (row["pickup_zone"], row["dropoff_zone"])
        values[key] = values.get(key, 0) + row["trip_count"]
    metadata = ctx.zones()
    ranked = sorted(values.items(), key=lambda r: (-r[1], r[0]))
    data = [
        {
            "pickup_zone": k[0],
            "dropoff_zone": k[1],
            "trip_count": n,
            "pickup_name": metadata.get(k[0], {}).get("name", "Unknown"),
            "dropoff_name": metadata.get(k[1], {}).get("name", "Unknown"),
        }
        for k, n in ranked[offset : offset + limit]
    ]
    return {
        "meta": ctx.meta,
        "data": data,
        "total": len(ranked),
        "coverage": ctx.manifest["route_coverage"],
    }


@router.get("/trips/efficiency", response_model=SeriesResponse)
def efficiency(
    ctx: Ctx,
    group_by: Literal["zone", "hour"] = "zone",
    limit: Annotated[int, Query(ge=1, le=265)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    keys = ["zone_id"] if group_by == "zone" else ["hour"]
    data = group(ctx.rows("trip_efficiency", keys), keys, ctx.zones())
    data.sort(key=(lambda r: -r["trip_count"]) if group_by == "zone" else lambda r: r["hour"])
    return {
        "meta": ctx.meta,
        "data": data[offset : offset + limit],
        "total": len(data),
        "offset": offset,
        "limit": limit,
    }


@router.get("/fares/summary", response_model=FaresResponse)
def fares(ctx: Ctx):
    rows = ctx.rows("fare_analytics")
    sums = sum_rows(rows)
    bins = [
        ("0_10", "$0–10"),
        ("10_20", "$10–20"),
        ("20_30", "$20–30"),
        ("30_50", "$30–50"),
        ("50_100", "$50–100"),
        ("100_plus", "$100+"),
    ]
    return {
        "meta": ctx.meta,
        "metrics": metrics(sums),
        "fare_per_mile": ratio(
            sums.get("fare_distance_amount", 0), sums.get("fare_distance_miles", 0)
        ),
        "total_tips": sums.get("tip_sum", 0),
        "congestion_fees": sums.get("congestion_fee_sum", 0),
        "distribution": [
            {"label": label, "trip_count": int(sums.get("bin_" + key, 0))} for key, label in bins
        ],
        "payment_types": [
            {
                "label": label.replace("_", " ").title(),
                "trip_count": int(sums.get("pay_" + label, 0)),
            }
            for label in ["card", "cash", "no_charge", "dispute", "unknown", "voided", "other"]
        ],
        "zones": sorted(group(rows, ["zone_id"], ctx.zones()), key=lambda r: -r["trip_count"])[:20],
    }


@router.get("/benchmarks", response_model=BenchmarksResponse)
def benchmarks(store=Depends(repository), run_id: str | None = None):
    manifest = store.manifest(run_id)
    if not manifest:
        raise HTTPException(404 if run_id else 503, "No published dataset available")
    return {
        "run_id": manifest["run_id"],
        "data": store.rows("benchmarks", manifest["run_id"]),
        "quality": manifest["quality"],
        "machine": manifest["machine"],
        "notes": [
            "Benchmark task: identical pickup-zone counts, verified across engines.",
            "Timings include reading Parquet and exclude Spark session startup.",
            "Quality exclusion flags overlap; do not add them as distinct excluded rows.",
        ],
    }
