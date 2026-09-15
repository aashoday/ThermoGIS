"""
Full database snapshot/restore for demo safety. Dumps the entire
current hotspots + industrial_assets state (including ML predictions)
to a JSON file, and can restore it instantly — giving a guaranteed,
network-independent "known good" demo state regardless of whether
FIRMS/Overpass are reachable or rate-limited on demo day.

Usage:
    python -m app.services.snapshot save    # capture current state
    python -m app.services.snapshot restore # wipe + reload from snapshot
"""
import json
import os
import sys
import uuid
from datetime import datetime

from sqlalchemy import text

from app.database import SessionLocal

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data_cache")
SNAPSHOT_PATH = os.path.join(SNAPSHOT_DIR, "demo_snapshot.json")

DUMP_HOTSPOTS_SQL = text("""
    SELECT id, source, acquired_at, frp, confidence,
           ST_X(geom::geometry) AS lon, ST_Y(geom::geometry) AS lat,
           nearest_asset_id, distance_to_asset_m, landcover_class,
           cluster_id, predicted_class, prediction_confidence
    FROM hotspots
""")

DUMP_ASSETS_SQL = text("""
    SELECT id, name, asset_type, source,
           ST_X(ST_Centroid(geom)::geometry) AS lon,
           ST_Y(ST_Centroid(geom)::geometry) AS lat
    FROM industrial_assets
""")

INSERT_ASSET_SQL = text("""
    INSERT INTO industrial_assets (id, name, asset_type, source, geom)
    VALUES (:id, :name, :asset_type, :source, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
""")

INSERT_HOTSPOT_SQL = text("""
    INSERT INTO hotspots (
        id, source, acquired_at, frp, confidence, geom,
        nearest_asset_id, distance_to_asset_m, landcover_class,
        cluster_id, predicted_class, prediction_confidence
    )
    VALUES (
        :id, :source, :acquired_at, :frp, :confidence,
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
        :nearest_asset_id, :distance_to_asset_m, :landcover_class,
        :cluster_id, :predicted_class, :prediction_confidence
    )
""")


def save_snapshot():
    db = SessionLocal()
    try:
        hotspots = [dict(row._mapping) for row in db.execute(DUMP_HOTSPOTS_SQL).fetchall()]
        assets = [dict(row._mapping) for row in db.execute(DUMP_ASSETS_SQL).fetchall()]

        # UUID and datetime objects aren't JSON-serializable by default.
        def serialize(obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        for row in hotspots + assets:
            for k, v in row.items():
                row[k] = serialize(v)

        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        with open(SNAPSHOT_PATH, "w") as f:
            json.dump({"hotspots": hotspots, "assets": assets}, f, indent=2)

        print(f"Snapshot saved: {len(hotspots)} hotspots, {len(assets)} assets -> {SNAPSHOT_PATH}")
    finally:
        db.close()


def restore_snapshot():
    if not os.path.exists(SNAPSHOT_PATH):
        print(f"No snapshot found at {SNAPSHOT_PATH}. Run 'save' first.")
        return

    with open(SNAPSHOT_PATH, "r") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        db.execute(text("TRUNCATE hotspots, industrial_assets CASCADE"))

        for asset in data["assets"]:
            db.execute(INSERT_ASSET_SQL, asset)

        for hotspot in data["hotspots"]:
            db.execute(INSERT_HOTSPOT_SQL, hotspot)

        db.commit()
        print(f"Restored {len(data['hotspots'])} hotspots, {len(data['assets'])} assets from snapshot.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("save", "restore"):
        print("Usage: python -m app.services.snapshot [save|restore]")
        sys.exit(1)

    if sys.argv[1] == "save":
        save_snapshot()
    else:
        restore_snapshot()