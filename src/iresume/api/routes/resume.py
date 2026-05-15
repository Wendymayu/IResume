import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from iresume.agent.graph import build_resume_graph
from iresume.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    jd_text: str
    template: str = "professional"


class GenerateResponse(BaseModel):
    resume_id: str
    gap_report: dict | None = None
    skill_matches: list | None = None
    resume_markdown: str | None = None


@router.post("/generate", response_model=GenerateResponse)
async def generate_resume(request: GenerateRequest):
    logger.info(f"[API] 开始生成简历，JD长度: {len(request.jd_text)}, 模板: {request.template}")
    try:
        graph = build_resume_graph()
        logger.info(f"[API] 图构建完成，profile_dir: {settings.profile_dir}")

        input_state = {
            "jd_raw": request.jd_text,
            "profile_path": str(settings.profile_dir),
            "template_name": request.template,
        }
        logger.info(f"[API] 开始执行图，输入状态: {list(input_state.keys())}")

        result = graph.invoke(input_state)
        logger.info(f"[API] 图执行完成，结果键: {list(result.keys())}")
        logger.debug(f"[API] 完整结果: {result}")

        if result.get("gap_report", {}).get("recommendation") == "not_viable":
            logger.warning(f"[API] 技能匹配度过低: {result['gap_report']}")
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "技能匹配度过低，建议调整目标职位",
                    "gap_report": result["gap_report"],
                },
            )

        # Extract resume_id from path
        resume_path = result.get("resume_path", "")
        resume_id = Path(resume_path).stem if resume_path else ""
        logger.info(f"[API] 简历生成成功，ID: {resume_id}")

        return GenerateResponse(
            resume_id=resume_id,
            gap_report=result.get("gap_report"),
            skill_matches=result.get("skill_matches"),
            resume_markdown=result.get("resume_markdown"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[API] 生成简历异常: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成简历失败: {str(e)}")


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
