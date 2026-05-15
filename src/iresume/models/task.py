from __future__ import annotations

import enum
from datetime import datetime

from pydantic import BaseModel


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationTask(BaseModel):
    task_id: str
    status: TaskStatus
    progress: str
    progress_pct: int
    created_at: datetime
    completed_at: datetime | None = None
    result: dict | None = None
    error: str | None = None
