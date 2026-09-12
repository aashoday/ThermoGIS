"""
Pydantic response models for the hotspot API. Shaped as GeoJSON
Feature/FeatureCollection so the frontend (MapLibreGL) can consume
the response directly as a map source with zero transformation.
"""
from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel


class HotspotProperties(BaseModel):
    id: str
    source: str
    acquired_at: datetime
    frp: Optional[float] = None
    confidence: Optional[str] = None
    distance_to_asset_m: Optional[float] = None
    nearest_asset_id: Optional[str] = None
    nearest_asset_name: Optional[str] = None
    nearest_asset_type: Optional[str] = None
    cluster_id: Optional[int] = None
    predicted_class: Optional[str] = None
    prediction_confidence: Optional[float] = None


class GeoJSONPointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [lon, lat]


class HotspotFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONPointGeometry
    properties: HotspotProperties


class HotspotFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[HotspotFeature]