from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import ComputeJob
from app.schemas.compute import ComputeJobStatus, ComputeJobTriggerResponse
from app.services.compute_service import ComputeService


logger = logging.getLogger(__name__)
settings = get_settings()


class ComputeJobService:
    def __init__(self) -> None:
        self.compute_service = ComputeService()
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._active_job_id: int | None = None

    def trigger(self, db: Session) -> ComputeJobTriggerResponse:
        active_job = self._get_active_job(db)
        if active_job is not None:
            return ComputeJobTriggerResponse(
                success=True,
                message="Existing compute job is already running",
                job=self.to_schema(active_job),
            )

        job = self._get_resumable_job(db)
        if job is None:
            job = ComputeJob(
                status="pending",
                stage="queued",
                message="Job queued",
                heartbeat_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            message = "Compute job created"
        else:
            if job.status == "failed":
                job.status = "pending"
                job.stage = "queued"
                job.error_message = None
                job.message = "Job resumed from checkpoint"
                job.finished_at = None
                job.heartbeat_at = datetime.utcnow()
                db.commit()
                db.refresh(job)
            message = "Existing compute job resumed"

        self._ensure_worker(job.id, "full")
        return ComputeJobTriggerResponse(success=True, message=message, job=self.to_schema(job))

    def trigger_daily_refresh(self, db: Session) -> ComputeJobTriggerResponse:
        active_job = self._get_active_job(db)
        if active_job is not None:
            return ComputeJobTriggerResponse(
                success=True,
                message="Existing compute job is already running",
                job=self.to_schema(active_job),
            )

        job = ComputeJob(
            status="pending",
            stage="queued",
            message="Daily quote refresh queued",
            heartbeat_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        self._ensure_worker(job.id, "daily")
        return ComputeJobTriggerResponse(success=True, message="Daily refresh job created", job=self.to_schema(job))

    def resume_incomplete_jobs(self) -> None:
        db = SessionLocal()
        try:
            job = self._get_resumable_job(db, include_failed=False)
            if job is not None:
                mode = "daily" if (job.message or "").lower().startswith("daily") else "full"
                self._ensure_worker(job.id, mode)
        finally:
            db.close()

    def get_latest_job(self, db: Session) -> ComputeJob | None:
        return db.scalar(select(ComputeJob).order_by(desc(ComputeJob.id)))

    def list_jobs(self, db: Session, limit: int = 20) -> list[ComputeJob]:
        safe_limit = max(1, min(limit, 100))
        return list(db.scalars(select(ComputeJob).order_by(desc(ComputeJob.id)).limit(safe_limit)))

    def get_job(self, db: Session, job_id: int) -> ComputeJob | None:
        return db.get(ComputeJob, job_id)

    def to_schema(self, job: ComputeJob) -> ComputeJobStatus:
        return ComputeJobStatus(
            id=job.id,
            status=job.status,
            stage=job.stage,
            current_theme_type=job.current_theme_type,
            current_theme_index=job.current_theme_index,
            total_theme_count=job.total_theme_count,
            processed_theme_count=job.processed_theme_count,
            synced_theme_count=job.synced_theme_count,
            score_count=job.score_count,
            last_theme_name=job.last_theme_name,
            message=job.message,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            heartbeat_at=job.heartbeat_at,
            finished_at=job.finished_at,
        )

    def _get_resumable_job(self, db: Session, include_failed: bool = True) -> ComputeJob | None:
        statuses = ["pending", "running"]
        if include_failed:
            statuses.append("failed")
        return db.scalar(
            select(ComputeJob)
            .where(ComputeJob.status.in_(statuses))
            .order_by(desc(ComputeJob.id))
        )

    def _get_active_job(self, db: Session) -> ComputeJob | None:
        return db.scalar(
            select(ComputeJob)
            .where(ComputeJob.status.in_(["pending", "running"]))
            .order_by(desc(ComputeJob.id))
        )

    def _ensure_worker(self, job_id: int, mode: str) -> None:
        with self._lock:
            if self._worker and self._worker.is_alive() and self._active_job_id == job_id:
                return
            self._active_job_id = job_id
            target = self._run_daily_job if mode == "daily" else self._run_job
            self._worker = threading.Thread(target=target, args=(job_id,), daemon=True)
            self._worker.start()

    def _run_job(self, job_id: int) -> None:
        fetched_quotes_by_symbol: set[str] = set()
        db = SessionLocal()
        try:
            job = db.get(ComputeJob, job_id)
            if job is None:
                return

            if job.status == "pending":
                job.status = "running"
                job.stage = "syncing"
                job.started_at = datetime.utcnow()
                job.message = "Sync started"
                job.error_message = None
                job.heartbeat_at = datetime.utcnow()
                db.commit()

            catalog = self.compute_service.build_theme_catalog()
            if not catalog:
                catalog = self.compute_service.build_theme_catalog_from_db(db)
                job.message = "Live theme catalog unavailable, resuming from stored themes"
                job.heartbeat_at = datetime.utcnow()
                db.commit()
            job.total_theme_count = len(catalog)
            if job.current_theme_type is None and catalog:
                job.current_theme_type = catalog[0].theme_type
                job.current_theme_index = catalog[0].index
            job.heartbeat_at = datetime.utcnow()
            db.commit()

            start_position = self.compute_service.get_resume_start_position(db, job, catalog)
            for batch_start in range(start_position, len(catalog), settings.compute_batch_size):
                batch_end = min(batch_start + settings.compute_batch_size, len(catalog))
                for position in range(batch_start, batch_end):
                    item = catalog[position]
                    synced = self.compute_service.sync_single_theme(db, item, fetched_quotes_by_symbol)
                    job = db.get(ComputeJob, job_id)
                    if job is None:
                        return
                    job.status = "running"
                    job.stage = "syncing"
                    job.current_theme_type = item.theme_type
                    job.current_theme_index = item.index + 1
                    job.processed_theme_count = min(position + 1, len(catalog))
                    if synced:
                        job.synced_theme_count += 1
                    job.last_theme_name = item.name
                    job.message = f"Synced {item.theme_type}/{item.name}"
                    job.error_message = None
                    job.heartbeat_at = datetime.utcnow()
                    db.commit()
                time.sleep(settings.compute_batch_pause_seconds)

            job = db.get(ComputeJob, job_id)
            if job is None:
                return
            job.stage = "scoring"
            job.message = "Computing scores"
            job.heartbeat_at = datetime.utcnow()
            db.commit()

            score_count = self.compute_service.compute_scores_only(db)

            job = db.get(ComputeJob, job_id)
            if job is None:
                return
            job.status = "completed"
            job.stage = "completed"
            job.score_count = score_count
            job.current_theme_type = None
            job.message = "Job completed"
            job.error_message = None
            job.finished_at = datetime.utcnow()
            job.heartbeat_at = datetime.utcnow()
            db.commit()
        except Exception as exc:
            logger.exception("compute job %s failed", job_id)
            db.rollback()
            failed_job = db.get(ComputeJob, job_id)
            if failed_job is not None:
                failed_job.status = "failed"
                failed_job.stage = "failed"
                failed_job.error_message = str(exc)
                failed_job.message = "Job failed"
                failed_job.finished_at = datetime.utcnow()
                failed_job.heartbeat_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None
                self._worker = None

    def _run_daily_job(self, job_id: int) -> None:
        fetched_quotes_by_symbol: set[str] = set()
        db = SessionLocal()
        try:
            job = db.get(ComputeJob, job_id)
            if job is None:
                return

            job.status = "running"
            job.stage = "quotes"
            job.started_at = job.started_at or datetime.utcnow()
            job.message = "Refreshing existing stock quotes"
            job.error_message = None
            job.heartbeat_at = datetime.utcnow()
            db.commit()

            refreshed_count = self.compute_service.refresh_existing_stock_quotes(db, fetched_quotes_by_symbol)

            job = db.get(ComputeJob, job_id)
            if job is None:
                return
            job.stage = "scoring"
            job.processed_theme_count = refreshed_count
            job.synced_theme_count = refreshed_count
            job.message = f"Refreshed quotes for {refreshed_count} stocks"
            job.heartbeat_at = datetime.utcnow()
            db.commit()

            score_count = self.compute_service.compute_scores_only(db)

            job = db.get(ComputeJob, job_id)
            if job is None:
                return
            job.status = "completed"
            job.stage = "completed"
            job.score_count = score_count
            job.message = "Daily refresh completed"
            job.error_message = None
            job.finished_at = datetime.utcnow()
            job.heartbeat_at = datetime.utcnow()
            db.commit()
        except Exception as exc:
            logger.exception("daily compute job %s failed", job_id)
            db.rollback()
            failed_job = db.get(ComputeJob, job_id)
            if failed_job is not None:
                failed_job.status = "failed"
                failed_job.stage = "failed"
                failed_job.error_message = str(exc)
                failed_job.message = "Daily refresh failed"
                failed_job.finished_at = datetime.utcnow()
                failed_job.heartbeat_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None
                self._worker = None


compute_job_service = ComputeJobService()
