from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.akshare_service import AKShareService
from app.services.compute_job_service import compute_job_service


logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
ak_service = AKShareService()


def _run_scheduled_compute() -> None:
    schedule_date = datetime.now(ZoneInfo(settings.scheduler_timezone)).date()
    if settings.scheduler_skip_non_trading_days and not ak_service.is_trading_day(schedule_date):
        logger.info("daily theme refresh skipped for non-trading day: %s", schedule_date)
        return

    db = SessionLocal()
    try:
        compute_job_service.trigger_daily_refresh(db)
        logger.info("daily theme refresh scheduled for trading day: %s", schedule_date)
    except Exception:
        logger.exception("daily theme refresh failed")
    finally:
        db.close()


def _run_full_sync() -> None:
    schedule_date = datetime.now(ZoneInfo(settings.scheduler_timezone)).date()
    if settings.scheduler_skip_non_trading_days and not ak_service.is_trading_day(schedule_date):
        logger.info("full theme sync skipped for non-trading day: %s", schedule_date)
        return

    db = SessionLocal()
    try:
        compute_job_service.trigger(db)
        logger.info("full theme sync scheduled for trading day: %s", schedule_date)
    except Exception:
        logger.exception("full theme sync failed")
    finally:
        db.close()


def start_scheduler() -> None:
    if not settings.scheduler_enabled or scheduler.running:
        return
    scheduler.add_job(
        _run_scheduled_compute,
        trigger="cron",
        day_of_week=settings.scheduler_cron_day_of_week,
        hour=settings.scheduler_cron_hour,
        minute=settings.scheduler_cron_minute,
        id="scheduled-theme-compute",
        replace_existing=True,
    )
    if settings.full_sync_enabled:
        scheduler.add_job(
            _run_full_sync,
            trigger="cron",
            day_of_week=settings.full_sync_cron_day_of_week,
            hour=settings.full_sync_cron_hour,
            minute=settings.full_sync_cron_minute,
            id="weekly-full-theme-sync",
            replace_existing=True,
        )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
