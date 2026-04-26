from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.compute import ComputeJobStatus, ComputeJobTriggerResponse
from app.schemas.theme import ThemeDetail, ThemeRankingItem
from app.services.compute_job_service import compute_job_service
from app.services.theme_service import get_theme_detail, get_theme_rankings


router = APIRouter()


@router.get("/themes", response_model=list[ThemeRankingItem])
def list_themes(db: Session = Depends(get_db)):
    return get_theme_rankings(db)


@router.get("/themes/{theme_id}", response_model=ThemeDetail)
def get_theme(theme_id: int, db: Session = Depends(get_db)):
    theme = get_theme_detail(db, theme_id)
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.get("/rankings", response_model=list[ThemeRankingItem])
def get_rankings(db: Session = Depends(get_db)):
    return get_theme_rankings(db)


@router.post("/compute", response_model=ComputeJobTriggerResponse)
def trigger_compute(db: Session = Depends(get_db)):
    return compute_job_service.trigger(db)


@router.get("/compute", response_model=ComputeJobStatus)
def get_latest_compute_job(db: Session = Depends(get_db)):
    job = compute_job_service.get_latest_job(db)
    if job is None:
        raise HTTPException(status_code=404, detail="No compute job found")
    return compute_job_service.to_schema(job)


@router.get("/compute/{job_id}", response_model=ComputeJobStatus)
def get_compute_job(job_id: int, db: Session = Depends(get_db)):
    job = compute_job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Compute job not found")
    return compute_job_service.to_schema(job)
