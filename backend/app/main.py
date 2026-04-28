import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.db.migrations import run_startup_migrations
from app.db.session import Base, engine
from app.models import ComputeJob, DailyQuote, Stock, Theme, ThemeScore, ThemeStock
from app.services.compute_job_service import compute_job_service
from app.tasks.scheduler import start_scheduler, stop_scheduler


logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_startup_migrations(engine)
    compute_job_service.resume_incomplete_jobs()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok"}
