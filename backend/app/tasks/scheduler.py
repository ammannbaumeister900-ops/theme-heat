from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.compute_job_service import compute_job_service


logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)


def _run_weekly_compute() -> None:
    db = SessionLocal()
    try:
        compute_job_service.trigger(db)
        logger.info("weekly compute scheduled")
    except Exception:
        logger.exception("weekly compute failed")
    finally:
        db.close()


def start_scheduler() -> None:
    if not settings.scheduler_enabled or scheduler.running:
        return
    scheduler.add_job(
        _run_weekly_compute,
        trigger="cron",
        day_of_week=settings.scheduler_cron_day_of_week,
        hour=settings.scheduler_cron_hour,
        minute=settings.scheduler_cron_minute,
        id="weekly-theme-compute",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
