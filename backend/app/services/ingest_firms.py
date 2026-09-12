"""
Pulls active fire hotspots from NASA FIRMS (VIIRS SNPP, last 7 days)
for the configured region bounding box, and loads them into the
hotspots table.

FIRMS API docs: https://firms.modaps.eosdis.nasa.gov/api/area/
"""
import csv
import io
import uuid
from datetime import datetime

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import SessionLocal
from app.models.hotspot import Hotspot
from app.config import settings

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SATELLITE = "VIIRS_SNPP_NRT"  # near-real-time VIIRS, 375m
DAY_RANGE = 5


def fetch_firms_csv() -> str:
    if not settings.firms_map_key:
        raise ValueError("FIRMS_MAP_KEY is not set in .env")

    url = f"{FIRMS_BASE_URL}/{settings.firms_map_key}/{SATELLITE}/{settings.region_bbox}/{DAY_RANGE}"
    print(f"Requesting: {url}")
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(f"FIRMS returned status {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        response.raise_for_status()

    if response.text.startswith("Invalid") or "error" in response.text[:100].lower():
        raise ValueError(f"FIRMS API returned an error: {response.text[:200]}")

    return response.text


def parse_and_load(csv_text: str, db: Session) -> int:
    reader = csv.DictReader(io.StringIO(csv_text))
    count = 0
    skipped = 0

    for row in reader:
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            frp = float(row["frp"]) if row.get("frp") else None
            confidence = row.get("confidence", "")
            acq_date = row.get("acq_date", "")
            acq_time = row.get("acq_time", "0000").zfill(4)

            acquired_at = datetime.strptime(
                f"{acq_date} {acq_time}", "%Y-%m-%d %H%M"
            )

            # FIRMS returns a rolling window on every call, so the same
            # detection reappears across scheduled runs. Dedupe on the
            # natural key (same satellite pass + same location, rounded
            # to VIIRS's ~375m pixel precision) before inserting, or the
            # table grows unbounded every 30 minutes.
            existing = db.execute(
                text("""
                    SELECT 1 FROM hotspots
                    WHERE acquired_at = :acquired_at
                      AND source = 'VIIRS'
                      AND ST_DWithin(
                          geom::geography,
                          ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                          50
                      )
                    LIMIT 1
                """),
                {"acquired_at": acquired_at, "lon": lon, "lat": lat},
            ).fetchone()

            if existing:
                skipped += 1
                continue

            point = Point(lon, lat)
            geom = from_shape(point, srid=4326)

            hotspot = Hotspot(
                id=uuid.uuid4(),
                source="VIIRS",
                acquired_at=acquired_at,
                frp=frp,
                confidence=confidence,
                geom=geom,
            )
            db.add(hotspot)
            count += 1
        except (KeyError, ValueError) as e:
            print(f"  skipping malformed row: {e}")
            continue

    db.commit()
    print(f"  ({skipped} duplicates skipped)")
    return count


def run_ingestion():
    print(f"Fetching FIRMS hotspots for bbox {settings.region_bbox} (last {DAY_RANGE} days)...")
    csv_text = fetch_firms_csv()

    db = SessionLocal()
    try:
        count = parse_and_load(csv_text, db)
        print(f"Loaded {count} hotspots into database.")
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()