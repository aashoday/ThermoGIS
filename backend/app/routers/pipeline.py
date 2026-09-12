"""
Manual pipeline trigger endpoint — lets a demo show the "Monitor" loop
running live on-demand, rather than waiting for the 30-minute scheduled
interval. Runs synchronously and returns once done, which is fine at
our current data scale (53 hotspots, sub-second per step).
"""
from fastapi import APIRouter

from app.services.run_pipeline import run_full_pipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/run")
def trigger_pipeline_run():
    run_full_pipeline()
    return {"status": "completed"}