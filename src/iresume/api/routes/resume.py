from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from iresume.agent.graph import build_resume_graph
from iresume.api.deps import get_history_repo
from iresume.config import settings
from iresume.services.resume_runner import run_resume_generation
from iresume.services.task_manager import task_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    jd_text: str
    template: str = "professional"


class TaskResponse(BaseModel):
    task_id: str


@router.post("/generate")
async def generate_resume(request: GenerateRequest):
    logger.info(f"[API] 开始生成简历（异步），JD长度: {len(request.jd_text)}, 模板: {request.template}")
    task_id = await task_manager.create_task()
    # 立即创建历史记录，状态为 running
    history_repo = get_history_repo()
    history_repo.add_record(
        task_id=task_id,
        jd_text=request.jd_text,
        status="running",
        template=request.template,
    )
    asyncio.create_task(
        run_resume_generation(
            task_id=task_id,
            jd_text=request.jd_text,
            profile_path=str(settings.profile_dir),
            template_name=request.template,
        )
    )
    logger.info(f"[API] 任务已创建: {task_id}")
    return TaskResponse(task_id=task_id)


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = await task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump()


# --- Streaming endpoint (kept for future use) ---


@router.post("/generate/stream")
async def generate_resume_stream(request: GenerateRequest):
    graph = build_resume_graph()

    async def event_stream():
        async for event in graph.astream_events(
            {
                "jd_raw": request.jd_text,
                "profile_path": str(settings.profile_dir),
                "template_name": request.template,
            },
            version="v2",
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- History endpoints ---


@router.get("/history/list")
async def list_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    repo = get_history_repo()
    records = repo.list_records(limit=limit, offset=offset)
    total = repo.count()
    return {"records": records, "total": total}


@router.get("/history/{task_id}")
async def get_history_detail(task_id: str):
    repo = get_history_repo()
    record = repo.get_record(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/history/{task_id}")
async def delete_history_record(task_id: str):
    repo = get_history_repo()
    deleted = repo.delete_record(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"ok": True}


# --- Resume lookup & download ---


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    filepath = settings.resumes_dir / f"{resume_id}.md"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    content = filepath.read_text(encoding="utf-8")
    return {"resume_id": resume_id, "markdown": content}


@router.get("/{resume_id}/download")
async def download_resume(resume_id: str):
    filepath = settings.resumes_dir / f"{resume_id}.md"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(
        filepath,
        media_type="text/markdown",
        filename=f"{resume_id}.md",
    )
