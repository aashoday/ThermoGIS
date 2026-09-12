from typing import List, Literal, Optional

from pydantic import BaseModel


class AssetProperties(BaseModel):
    id: str
    name: Optional[str] = None
    asset_type: str
    source: str


class GeoJSONPointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]


class AssetFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONPointGeometry
    properties: AssetProperties


class AssetFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[AssetFeature]