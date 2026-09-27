"""Worker entry point: `uv run python -m jobs.scheduler`

Starts APScheduler in the Asia/Kolkata timezone. Jobs are registered in `register_jobs()` as they are
built (PRD §19): daily pipeline, rapid check, officer summary, fallback check, pause auto-resume,
digest, maintenance.
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from jobs.config import get_worker_settings

log = logging.getLogger("worker")


def register_jobs(scheduler: BlockingScheduler) -> None:
    """Add jobs here, e.g.:
        scheduler.add_job(run_daily_pipeline, CronTrigger.from_crontab(settings.pipeline_cron, timezone=tz))
    """


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
