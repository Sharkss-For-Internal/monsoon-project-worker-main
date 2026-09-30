"""Worker entry point: `uv run python -m jobs.scheduler`

Starts APScheduler in the Asia/Kolkata timezone. Jobs are registered in `register_jobs()` as they are
built (PRD §19): daily pipeline, rapid check, officer summary, fallback check, pause auto-resume,
digest, maintenance.
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from jobs.config import get_worker_settings

log = logging.getLogger("worker")


def run_daily_pipeline() -> None:
    """PRD §11.1 — fetch rain, score blocks (ML or SRS fallback), queue + send alerts."""
    from app.core.db import SessionLocal
    from app.models.enums import RunType
    from app.services.pipeline import trigger_run

    db = SessionLocal()
    try:
        run = trigger_run(db, RunType.SCHEDULED, triggered_by="worker")
        log.info("Daily pipeline finished: id=%s status=%s", run.id, run.status)
    finally:
        db.close()


def run_rapid_check() -> None:
    """PRD §11.9 — every 3 hours: 72-h forecast -> heavy-rain rapid events -> urgent alerts."""
    from app.core.db import SessionLocal
    from app.services.rapid_check import trigger_rapid_check

    db = SessionLocal()
    try:
        run = trigger_rapid_check(db, triggered_by="worker")
        log.info("Rapid check finished: id=%s status=%s", run.id, run.status)
    finally:
        db.close()


def run_officer_summary() -> None:
    """PRD §14.7 — daily 07:15 summary to every active extension officer."""
    from app.core.db import SessionLocal
    from app.services.officer_summary import run_officer_summary as _run

    db = SessionLocal()
    try:
        count = _run(db, triggered_by="worker")
        log.info("Officer summary finished: %d messages queued", count)
    finally:
        db.close()


def register_jobs(scheduler: BlockingScheduler) -> None:
    settings = get_worker_settings()
    tz = settings.timezone
    scheduler.add_job(
        run_daily_pipeline,
        CronTrigger.from_crontab(settings.pipeline_cron, timezone=tz),
        id="daily_pipeline",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        run_rapid_check,
        CronTrigger.from_crontab(settings.rapid_check_cron, timezone=tz),
        id="rapid_check",
        replace_existing=True,
        misfire_grace_time=1800,
    )
    scheduler.add_job(
        run_officer_summary,
        CronTrigger.from_crontab(settings.officer_summary_cron, timezone=tz),
        id="officer_summary",
        replace_existing=True,
        misfire_grace_time=1800,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_worker_settings()
    if not settings.scheduler_enabled:
        log.info("SCHEDULER_ENABLED=false - worker is not scheduling anything. Set it to true in .env.")
        return

    scheduler = BlockingScheduler(timezone=settings.timezone)
    register_jobs(scheduler)
    log.info("Worker started (%s) with %d job(s).", settings.timezone, len(scheduler.get_jobs()))
    scheduler.start()


if __name__ == "__main__":
    main()
