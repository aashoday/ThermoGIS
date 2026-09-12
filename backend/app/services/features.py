"""
Shared feature extraction — used by both training (train_classifier.py)
and live inference (the API layer in Step 7), so features are computed
identically in both places.
"""
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

FEATURES_SQL = text("""
    SELECT
        h.id,
        h.frp,
        h.distance_to_asset_m,
        h.cluster_id,
        cluster_stats.detection_count,
        cluster_stats.span_hours
    FROM hotspots h
    JOIN (
        SELECT
            cluster_id,
            count(*) AS detection_count,
            EXTRACT(EPOCH FROM (max(acquired_at) - min(acquired_at))) / 3600.0 AS span_hours
        FROM hotspots
        GROUP BY cluster_id
    ) cluster_stats ON h.cluster_id = cluster_stats.cluster_id
    WHERE h.distance_to_asset_m IS NOT NULL
      AND h.cluster_id IS NOT NULL
""")

FEATURE_COLUMNS = ["frp", "distance_to_asset_m", "detection_count", "span_hours"]


def load_feature_dataframe(db: Session) -> pd.DataFrame:
    rows = db.execute(FEATURES_SQL).fetchall()
    df = pd.DataFrame(rows, columns=[
        "id", "frp", "distance_to_asset_m", "cluster_id", "detection_count", "span_hours"
    ])
    df["frp"] = df["frp"].fillna(0.0)

    # Postgres numeric/EXTRACT results can arrive as Decimal (pandas dtype
    # 'object'), which LightGBM rejects outright. Force proper float/int
    # dtypes explicitly rather than relying on pandas to infer them.
    df["frp"] = df["frp"].astype(float)
    df["distance_to_asset_m"] = df["distance_to_asset_m"].astype(float)
    df["detection_count"] = df["detection_count"].astype(int)
    df["span_hours"] = df["span_hours"].astype(float)

    return df