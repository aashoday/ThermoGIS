"""
Tags each hotspot with its landcover class from ESA WorldCover (10m,
2021), sampled directly from the public Cloud-Optimized GeoTIFF tiles
on S3 — no local download needed. This is the actual payoff of COGs:
we stream only the handful of pixels we need (one per hotspot) via
HTTP range requests, rather than pulling gigabytes of raster data.
"""
import os

# Must be set before any rasterio/GDAL operation — tells GDAL not to
# attempt AWS request-signing (we have no credentials, and the ESA
# WorldCover bucket is public/unsigned).
os.environ["AWS_NO_SIGN_REQUEST"] = "YES"
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".tif"

import math

import rasterio
from sqlalchemy import text

from app.database import SessionLocal

WORLDCOVER_BASE_URL = (
    "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com"
    "/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
)

# ESA WorldCover v200 class codes -> human-readable labels
LANDCOVER_CLASSES = {
    10: "Tree Cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare/Sparse Vegetation",
    70: "Snow and Ice",
    80: "Water Bodies",
    90: "Herbaceous Wetland",
    95: "Mangroves",
    100: "Moss and Lichen",
}

FETCH_HOTSPOTS_SQL = text("""
    SELECT id, ST_X(geom::geometry) AS lon, ST_Y(geom::geometry) AS lat
    FROM hotspots
    WHERE landcover_class IS NULL
""")

UPDATE_LANDCOVER_SQL = text("""
    UPDATE hotspots SET landcover_class = :landcover_class WHERE id = :hotspot_id
""")

# Cache opened remote datasets per tile within a single run — avoids
# re-opening the same remote COG (and re-paying connection overhead)
# for every hotspot that happens to fall in the same tile.
_dataset_cache = {}


def tile_name_for(lat: float, lon: float) -> str:
    lat_tile = int(math.floor(lat / 3.0)) * 3
    lon_tile = int(math.floor(lon / 3.0)) * 3
    lat_prefix = f"N{lat_tile:02d}" if lat_tile >= 0 else f"S{abs(lat_tile):02d}"
    lon_prefix = f"E{lon_tile:03d}" if lon_tile >= 0 else f"W{abs(lon_tile):03d}"
    return f"{lat_prefix}{lon_prefix}"


def get_dataset_for_tile(tile: str):
    if tile not in _dataset_cache:
        url = WORLDCOVER_BASE_URL.format(tile=tile)
        try:
            _dataset_cache[tile] = rasterio.open(url)
        except rasterio.errors.RasterioIOError:
            # Tile doesn't exist (e.g. falls over open ocean with no land
            # cover data) — cache the miss as None so we don't retry it.
            _dataset_cache[tile] = None
    return _dataset_cache[tile]


def sample_landcover(lat: float, lon: float) -> str | None:
    tile = tile_name_for(lat, lon)
    dataset = get_dataset_for_tile(tile)
    if dataset is None:
        return None

    try:
        sample = next(dataset.sample([(lon, lat)]))
        class_code = int(sample[0])
        return LANDCOVER_CLASSES.get(class_code, f"Unknown ({class_code})")
    except (StopIteration, IndexError, ValueError):
        return None


def run_landcover_tagging():
    db = SessionLocal()
    try:
        rows = db.execute(FETCH_HOTSPOTS_SQL).fetchall()
        if not rows:
            print("No hotspots need landcover tagging.")
            return

        print(f"Tagging landcover for {len(rows)} hotspots...")
        tagged = 0
        failed = 0

        for row in rows:
            landcover = sample_landcover(row.lat, row.lon)
            if landcover:
                db.execute(UPDATE_LANDCOVER_SQL, {
                    "landcover_class": landcover,
                    "hotspot_id": row.id,
                })
                tagged += 1
            else:
                failed += 1

        db.commit()
        print(f"Tagged {tagged} hotspots. {failed} could not be tagged (no tile coverage).")

    finally:
        db.close()
        for ds in _dataset_cache.values():
            if ds is not None:
                ds.close()


if __name__ == "__main__":
    run_landcover_tagging()