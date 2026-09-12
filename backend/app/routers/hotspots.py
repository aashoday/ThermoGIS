"""
Serves classified hotspots as a GeoJSON FeatureCollection, with the
nearest industrial asset's name/type joined in so the frontend doesn't
need a second request per point.

Supports optional filtering by predicted_class and a minimum
prediction_confidence, since a judge/demo will want to show "just show
me the high-confidence industrial ones" as a live filter.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.hotspot import (
    HotspotFeatureCollection,
    HotspotFeature,
    HotspotProperties,
    GeoJSONPointGeometry,
)

router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])

BASE_QUERY = """
    SELECT
        h.id,
        h.source,
        h.acquired_at,
        h.frp,
        h.confidence,
        h.distance_to_asset_m,
        h.nearest_asset_id,
        ia.name AS nearest_asset_name,
        ia.asset_type AS nearest_asset_type,
        h.cluster_id,
        h.predicted_class,
        h.prediction_confidence,
        ST_X(h.geom::geometry) AS lon,
        ST_Y(h.geom::geometry) AS lat
    FROM hotspots h
    LEFT JOIN industrial_assets ia ON h.nearest_asset_id = ia.id
    WHERE 1=1
"""


@router.get("", response_model=HotspotFeatureCollection)
def get_hotspots(
    predicted_class: Optional[str] = Query(
        None, description="Filter by predicted_class: industrial, non_industrial, uncertain"
    ),
    min_confidence: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum prediction_confidence to include"
    ),
    db: Session = Depends(get_db),
):
    query = BASE_QUERY
    params = {}

    if predicted_class:
        query += " AND h.predicted_class = :predicted_class"
        params["predicted_class"] = predicted_class

    if min_confidence is not None:
        query += " AND h.prediction_confidence >= :min_confidence"
        params["min_confidence"] = min_confidence

    query += " ORDER BY h.acquired_at DESC"

    rows = db.execute(text(query), params).fetchall()

    features = []
    for row in rows:
        features.append(
            HotspotFeature(
                geometry=GeoJSONPointGeometry(coordinates=[row.lon, row.lat]),
                properties=HotspotProperties(
                    id=str(row.id),
                    source=row.source,
                    acquired_at=row.acquired_at,
                    frp=row.frp,
                    confidence=row.confidence,
                    distance_to_asset_m=row.distance_to_asset_m,
                    nearest_asset_id=str(row.nearest_asset_id) if row.nearest_asset_id else None,
                    nearest_asset_name=row.nearest_asset_name,
                    nearest_asset_type=row.nearest_asset_type,
                    cluster_id=row.cluster_id,
                    predicted_class=row.predicted_class,
                    prediction_confidence=row.prediction_confidence,
                ),
            )
        )

    return HotspotFeatureCollection(features=features)