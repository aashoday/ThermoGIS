"""
Pulls industrial infrastructure (refineries, plants, mines, factories)
from OpenStreetMap via Overpass API for the configured region, and
loads them into the industrial_assets table.
"""
import time
import uuid
import json
import os

import requests
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import SessionLocal
from app.models.industrial_asset import IndustrialAsset
from app.config import settings

# Verified reachable public Overpass mirrors (as of testing).
# overpass.kumi.systems dropped — unreachable at network level in some environments.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

HEADERS = {
    "User-Agent": "ThermoGIS-Hackathon/1.0 (research/demo use)",
}

# OSM tags that map to "industrial asset" for our purposes
INDUSTRIAL_TAGS = [
    ("landuse", "industrial"),
    ("man_made", "works"),
    ("industrial", "refinery"),
    ("man_made", "petroleum_well"),
    ("landuse", "quarry"),
]

REQUEST_TIMEOUT = 180       # seconds, client-side (must exceed server-side query timeout below)
QUERY_SERVER_TIMEOUT = 150  # seconds, told to the Overpass server itself
MAX_RETRIES_PER_MIRROR = 2
RETRY_BACKOFF_SECONDS = 5

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data_cache")
OSM_CACHE_PATH = os.path.join(CACHE_DIR, "osm_last_success.json")



def build_overpass_query(bbox: str) -> str:
    min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
    # Overpass wants south,west,north,east
    bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"

    filters = "\n".join(
        f'  node["{k}"="{v}"]({bbox_str});\n  way["{k}"="{v}"]({bbox_str});'
        for k, v in INDUSTRIAL_TAGS
    )

    return f"""
    [out:json][timeout:{QUERY_SERVER_TIMEOUT}];
    (
    {filters}
    );
    out center tags;
    """


def fetch_osm_assets() -> list:
    query = build_overpass_query(settings.region_bbox)
    last_error = None

    for url in OVERPASS_URLS:
        for attempt in range(1, MAX_RETRIES_PER_MIRROR + 1):
            try:
                print(f"Trying {url} (attempt {attempt}/{MAX_RETRIES_PER_MIRROR})...")
                response = requests.post(
                    url,
                    data={"data": query},
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code == 200:
                    elements = response.json().get("elements", [])
                    # Success — cache it for future fallback.
                    os.makedirs(CACHE_DIR, exist_ok=True)
                    with open(OSM_CACHE_PATH, "w") as f:
                        json.dump(elements, f)
                    return elements

                print(f"  status {response.status_code}: {response.text[:300]}")
                last_error = requests.exceptions.HTTPError(f"{response.status_code} from {url}")
                if response.status_code in (504, 429, 503):
                    time.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                else:
                    break

            except requests.exceptions.RequestException as e:
                print(f"  failed: {e}")
                last_error = e
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue

    print(f"All Overpass mirrors failed. Last error: {last_error}")
    if os.path.exists(OSM_CACHE_PATH):
        print(f"Falling back to cached response: {OSM_CACHE_PATH}")
        with open(OSM_CACHE_PATH, "r") as f:
            return json.load(f)

    raise RuntimeError(f"All Overpass mirrors failed and no cache available. Last error: {last_error}")


def classify_asset_type(tags: dict) -> str:
    if tags.get("industrial") == "refinery":
        return "refinery"
    if tags.get("man_made") == "petroleum_well":
        return "oil_well"
    if tags.get("landuse") == "quarry":
        return "mine_quarry"
    if tags.get("man_made") == "works":
        return "plant_works"
    if tags.get("landuse") == "industrial":
        return "industrial_zone"
    return "industrial_other"


def parse_and_load(elements: list, db: Session) -> int:
    count = 0
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")

        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:  # way - use computed center
            center = el.get("center")
            if not center:
                continue
            lat, lon = center.get("lat"), center.get("lon")

        if lat is None or lon is None:
            continue

        point = Point(lon, lat)
        geom = from_shape(point, srid=4326)

        asset = IndustrialAsset(
            id=uuid.uuid4(),
            name=name,
            asset_type=classify_asset_type(tags),
            source="OSM",
            geom=geom,
        )
        db.add(asset)
        count += 1

    db.commit()
    return count


def run_ingestion():
    print(f"Fetching OSM industrial assets for bbox {settings.region_bbox}...")
    elements = fetch_osm_assets()
    print(f"  Overpass returned {len(elements)} raw elements.")

    db = SessionLocal()
    try:
        count = parse_and_load(elements, db)
        print(f"Loaded {count} industrial assets into database.")
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()