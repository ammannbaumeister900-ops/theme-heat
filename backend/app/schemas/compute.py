from datetime import datetime

from pydantic import BaseModel


class ComputeResponse(BaseModel):
    success: bool
    message: str
    computed_at: datetime
    theme_count: int
    score_count: int


class ComputeJobStatus(BaseModel):
    id: int
    status: str
    stage: str
    current_theme_type: str | None
    current_theme_index: int
    total_theme_count: int
    processed_theme_count: int
    synced_theme_count: int
    score_count: int
    last_theme_name: str | None
    message: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    heartbeat_at: datetime | None
    finished_at: datetime | None


class ComputeJobTriggerResponse(BaseModel):
    success: bool
    message: str
    job: ComputeJobStatus
