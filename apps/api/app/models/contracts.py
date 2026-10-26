from typing import Any, Literal

from pydantic import BaseModel, Field


class Meta(BaseModel):
    run_id: str
    start_date: str
    end_date: str
    available_start: str
    available_end: str
    source: str
    zone_id: int | None = None
    borough: str | None = None
    timezone: str = "America/New_York"


class Metrics(BaseModel):
    trip_count: int = 0
    avg_distance_miles: float | None = None
    avg_duration_min: float | None = None
    avg_fare: float | None = None
    speed_mph: float | None = None
    total_fare: float = 0
    efficiency_count: int = 0
    fare_count: int = 0


class Point(Metrics):
    date: str | None = None
    hour: int | None = None
    zone_id: int | None = None
    name: str | None = None
    borough: str | None = None


class SeriesResponse(BaseModel):
    meta: Meta
    data: list[Point]
    total: int = 0
    offset: int = 0
    limit: int = 100


class OverviewResponse(BaseModel):
    meta: Meta
    metrics: Metrics
    daily: list[Point]
    busiest_zones: list[Point]
    boroughs: list[Point]


class Zone(BaseModel):
    zone_id: int
    borough: str
    name: str
    service_zone: str | None = None


class ZonesResponse(BaseModel):
    run_id: str
    data: list[Zone]
    total: int


class GeoProperties(Zone, Metrics):
    in_selection: bool = True


class GeoFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: int
    geometry: dict[str, Any]
    properties: GeoProperties


class GeographyResponse(BaseModel):
    meta: Meta
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoFeature]


class Route(BaseModel):
    pickup_zone: int
    dropoff_zone: int
    pickup_name: str
    dropoff_name: str
    trip_count: int


class RoutesResponse(BaseModel):
    meta: Meta
    coverage: str
    data: list[Route]
    total: int


class Category(BaseModel):
    label: str
    trip_count: int


class FaresResponse(BaseModel):
    meta: Meta
    metrics: Metrics
    fare_per_mile: float | None
    total_tips: float
    congestion_fees: float
    distribution: list[Category]
    payment_types: list[Category]
    zones: list[Point]


class DatasetStatus(BaseModel):
    status: str
    run_id: str | None = None
    source: str
    manifest: dict[str, Any] | None = None


class BenchmarksResponse(BaseModel):
    run_id: str
    data: list[dict[str, Any]]
    quality: dict[str, int]
    machine: dict[str, Any]
    notes: list[str] = Field(default_factory=list)
