"""
Background scheduler for periodic pipeline runs. Uses APScheduler's
BackgroundScheduler (thread-based) rather than Celery/Redis — appropriate
for our 4-day hackathon scope; a single-process in-app scheduler is
enough to prove the "unattended monitoring" claim without adding
infra we don't have time to properly operate.
"""
from apscheduler.schedulers.background import BackgroundScheduler

from app.services.run_pipeline import run_full_pipeline

# VIIRS NRT passes are roughly every few hours; refreshing every 30 min
# is frequent enough to feel "live" in a demo without hammering FIRMS
# or Overpass rate limits.
PIPELINE_INTERVAL_MINUTES = 30

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        run_full_pipeline,
        trigger="interval",
        minutes=PIPELINE_INTERVAL_MINUTES,
        id="thermogis_pipeline",
        next_run_time=None,  # don't fire immediately on startup — data already loaded at setup
        replace_existing=True,
    )
    scheduler.start()
    print(f"[Scheduler] Started — pipeline will run every {PIPELINE_INTERVAL_MINUTES} minutes.")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    print("[Scheduler] Stopped.")