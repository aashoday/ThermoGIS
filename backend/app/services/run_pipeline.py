"""
Runs the full ThermoGIS pipeline end-to-end:
  1. Ingest new FIRMS hotspots
  2. Spatial join (nearest industrial asset + distance)
  3. Landcover tagging (ESA WorldCover sample per hotspot)
  4. ST-DBSCAN clustering (persistence signal)
  5. LightGBM classification

OSM industrial assets are NOT re-ingested here on purpose — that data
changes rarely and Overpass is slow/rate-limited, so re-pulling it on
every scheduled run would be wasteful and risk failures. Assets are
ingested once at setup time (Step 3) and reused.

This is what the scheduler (Step 12b) calls periodically, and what
makes the system an actual "Monitor" rather than a manually-run script.
"""
import traceback
from datetime import datetime

from app.services.ingest_firms import run_ingestion as ingest_firms
from app.services.spatial_join import run_spatial_join
from app.services.ingest_landcover import run_landcover_tagging
from app.services.cluster_hotspots import run_clustering
from app.services.train_classifier import train_and_predict


def run_full_pipeline():
    started_at = datetime.utcnow()
    print(f"\n{'='*60}")
    print(f"[Pipeline] Starting run at {started_at.isoformat()}")
    print(f"{'='*60}")

    steps = [
        ("Ingest FIRMS hotspots", ingest_firms),
        ("Spatial join", run_spatial_join),
        ("Landcover tagging", run_landcover_tagging),
        ("Clustering", run_clustering),
        ("Classify", train_and_predict),
    ]

    for step_name, step_fn in steps:
        try:
            print(f"\n[Pipeline] Step: {step_name}")
            step_fn()
        except Exception as e:
            # One step failing (e.g. FIRMS API temporarily down) shouldn't
            # crash the whole scheduled job or take down the API process —
            # log it and continue, so the system stays resilient/unattended.
            print(f"[Pipeline] ERROR in step '{step_name}': {e}")
            print(traceback.format_exc())

    finished_at = datetime.utcnow()
    duration = (finished_at - started_at).total_seconds()
    print(f"\n[Pipeline] Run finished in {duration:.1f}s\n{'='*60}\n")


if __name__ == "__main__":
    run_full_pipeline()