"""
For every hotspot, finds the nearest industrial asset and the distance
to it (in meters), and writes both back onto the hotspot row.

Uses PostGIS's KNN <-> operator (index-accelerated nearest-neighbor
search via the GiST index on industrial_assets.geom) instead of a
brute-force ST_Distance over every asset — critical at 3,700+ assets.

Distance is computed via geography cast so the result is in real-world
meters rather than raw degree units (which distort badly at this
latitude range).
"""
from sqlalchemy import text
from app.database import SessionLocal

# LIMIT 1 after the <-> ORDER BY is what makes this a fast KNN lookup
# instead of a full sort of all 3,722 assets for every hotspot.
NEAREST_ASSET_SQL = text("""
    UPDATE hotspots h
    SET
        nearest_asset_id = nearest.id,
        distance_to_asset_m = nearest.distance_m
    FROM (
        SELECT
            ia.id,
            ST_Distance(
                h2.geom::geography,
                ia.geom::geography
            ) AS distance_m
        FROM hotspots h2
        CROSS JOIN LATERAL (
            SELECT id, geom
            FROM industrial_assets
            ORDER BY geom <-> h2.geom
            LIMIT 1
        ) ia
        WHERE h2.id = :hotspot_id
    ) AS nearest
    WHERE h.id = :hotspot_id
""")

COUNT_HOTSPOTS_SQL = text("SELECT id FROM hotspots")


def run_spatial_join():
    db = SessionLocal()
    try:
        hotspot_ids = [row[0] for row in db.execute(COUNT_HOTSPOTS_SQL).fetchall()]
        print(f"Running nearest-asset spatial join for {len(hotspot_ids)} hotspots...")

        for hotspot_id in hotspot_ids:
            db.execute(NEAREST_ASSET_SQL, {"hotspot_id": hotspot_id})

        db.commit()
        print(f"Updated {len(hotspot_ids)} hotspots with nearest_asset_id + distance_to_asset_m.")
    finally:
        db.close()


if __name__ == "__main__":
    run_spatial_join()