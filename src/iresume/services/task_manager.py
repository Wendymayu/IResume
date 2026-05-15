from __future__ import annotations

import uuid
from datetime import datetime, timezone

from iresume.models.task import GenerationTask, TaskStatus


class TaskManager:
    """In-memory, thread-safe task registry."""

    def __init__(self) -> None:
        self._tasks: dict[str, GenerationTask] = {}
        self._lock = None  # lazy import to avoid asyncio at import time

    @property
    def _lock_impl(self):
        if self._lock is None:
            import asyncio
            self._lock = asyncio.Lock()
        return self._lock

    async def create_task(self) -> str:
        task_id = uuid.uuid4().hex
        task = GenerationTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress="正在初始化...",
            progress_pct=0,
            created_at=datetime.now(timezone.utc),
        )
        async with self._lock_impl:
            self._tasks[task_id] = task
        return task_id

    async def get_task(self, task_id: str) -> GenerationTask | None:
        async with self._lock_impl:
            return self._tasks.get(task_id)

    async def update_task(self, task_id: str, **updates) -> None:
        async with self._lock_impl:
            task = self._tasks.get(task_id)
            if task is None:
                return
            for key, value in updates.items():
                setattr(task, key, value)


task_manager = TaskManager()
