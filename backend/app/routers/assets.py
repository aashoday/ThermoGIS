"""
Serves industrial assets as GeoJSON. Note: industrial_assets.geom is
stored as generic GEOMETRY (points and polygons both possible from OSM
ways), but we use ST_Centroid so every asset renders as a single point
on the map regardless of its original shape — polygon rendering can be
added later if the demo needs it, but a point marker is enough for now.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas.industrial_asset import (
    AssetFeatureCollection,
    AssetFeature,
    AssetProperties,
    GeoJSONPointGeometry,
)

router = APIRouter(prefix="/api/assets", tags=["assets"])

QUERY = text("""
    SELECT
        id,
        name,
        asset_type,
        source,
        ST_X(ST_Centroid(geom)::geometry) AS lon,
        ST_Y(ST_Centroid(geom)::geometry) AS lat
    FROM industrial_assets
""")


@router.get("", response_model=AssetFeatureCollection)
def get_assets(db: Session = Depends(get_db)):
    rows = db.execute(QUERY).fetchall()

    features = [
        AssetFeature(
            geometry=GeoJSONPointGeometry(coordinates=[row.lon, row.lat]),
            properties=AssetProperties(
                id=str(row.id),
                name=row.name,
                asset_type=row.asset_type,
                source=row.source,
            ),
        )
        for row in rows
    ]

    return AssetFeatureCollection(features=features)