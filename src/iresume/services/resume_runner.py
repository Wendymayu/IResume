from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from iresume.agent.nodes import (
    gap_analyzer,
    jd_parser,
    markdown_exporter,
    profile_loader,
    resume_generator,
    skill_matcher,
)
from iresume.config import settings
from iresume.models.task import TaskStatus
from iresume.services.task_manager import task_manager
from iresume.storage.history_repository import HistoryRepository

logger = logging.getLogger(__name__)

_STEPS: list[tuple[str, int, str]] = [
    # (node_name, progress_pct, progress_text)
    ("jd_parser", 10, "正在解析职位描述..."),
    ("profile_loader", 25, "正在加载个人档案..."),
    ("skill_matcher", 40, "正在匹配技能..."),
    ("gap_analyzer", 55, "正在进行差距分析..."),
    ("resume_generator", 75, "正在生成简历内容..."),
    ("markdown_exporter", 90, "正在导出 Markdown..."),
]

_NODE_MAP = {
    "jd_parser": jd_parser.run,
    "profile_loader": profile_loader.run,
    "skill_matcher": skill_matcher.run,
    "gap_analyzer": gap_analyzer.run,
    "resume_generator": resume_generator.run,
    "markdown_exporter": markdown_exporter.run,
}


async def _update(task_id: str, status: TaskStatus, progress: str, pct: int, **extra):
    """Shortcut to update a task field."""
    await task_manager.update_task(task_id, status=status, progress=progress, progress_pct=pct, **extra)


async def run_resume_generation(
    task_id: str,
    jd_text: str,
    profile_path: str,
    template_name: str = "professional",
) -> None:
    logger.info(f"[runner] 开始后台执行 task={task_id}")
    start_time = time.perf_counter()
    history_repo = HistoryRepository(settings.history_db_path)
    try:
        await _update(task_id, TaskStatus.RUNNING, "正在初始化...", 0)

        state: dict = {
            "jd_raw": jd_text,
            "profile_path": profile_path,
            "template_name": template_name,
        }

        for node_name, pct, text in _STEPS:
            await _update(task_id, TaskStatus.RUNNING, text, pct)
            logger.info(f"[runner] 执行节点: {node_name}")
            fn = _NODE_MAP[node_name]
            result = await asyncio.to_thread(fn, state)
            state.update(result)
            logger.info(f"[runner] 节点完成: {node_name}")

        # Check gap analysis result
        gap_report = state.get("gap_report", {})
        recommendation = gap_report.get("recommendation", "proceed")
        logger.info(f"[runner] 缺口分析建议: {recommendation}")

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        if recommendation == "not_viable":
            logger.info("[runner] not_viable，提前结束")
            await _update(
                task_id,
                TaskStatus.COMPLETED,
                "技能匹配度过低",
                100,
                result={"gap_report": gap_report},
                completed_at=datetime.now(timezone.utc),
            )
            history_repo.add_record(
                task_id=task_id,
                jd_text=jd_text,
                status="not_viable",
                template=template_name,
                elapsed_ms=elapsed_ms,
                gap_report=gap_report,
            )
            return

        # Assemble result
        resume_path = state.get("resume_path", "")
        resume_id = Path(resume_path).stem if resume_path else ""
        result = {
            "resume_id": resume_id,
            "gap_report": gap_report,
            "skill_matches": state.get("skill_matches", []),
            "resume_markdown": state.get("resume_markdown", ""),
        }

        await _update(
            task_id,
            TaskStatus.COMPLETED,
            "简历生成完成",
            100,
            result=result,
            completed_at=datetime.now(timezone.utc),
        )
        logger.info(f"[runner] task={task_id} 完成, resume_id={resume_id}")

        history_repo.add_record(
            task_id=task_id,
            jd_text=jd_text,
            status="completed",
            template=template_name,
            elapsed_ms=elapsed_ms,
            resume_id=resume_id,
            gap_report=gap_report,
        )

    except Exception as e:
        logger.exception(f"[runner] task={task_id} 异常: {type(e).__name__}: {e}")
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        await _update(task_id, TaskStatus.FAILED, "生成失败", 0, error=str(e))
        history_repo.add_record(
            task_id=task_id,
            jd_text=jd_text,
            status="failed",
            template=template_name,
            elapsed_ms=elapsed_ms,
            error=str(e),
        )
