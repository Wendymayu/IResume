import logging
import uuid
from datetime import datetime
from pathlib import Path

from iresume.agent.state import ResumeState
from iresume.config import settings
from iresume.exporter.markdown_renderer import render_markdown

logger = logging.getLogger(__name__)


def run(state: ResumeState) -> dict:
    logger.info("[markdown_exporter] 开始导出Markdown")
    try:
        content = state.get("resume_content", {})
        logger.info(f"[markdown_exporter] 简历内容键: {list(content.keys())}")

        if not content:
            logger.error("[markdown_exporter] 简历内容为空")
            return {"errors": ["No resume content to export"]}

        markdown_text = render_markdown(content)
        logger.info(f"[markdown_exporter] Markdown渲染完成，长度: {len(markdown_text)}")
        logger.debug(f"[markdown_exporter] Markdown预览: {markdown_text[:200]}...")

        # Save to file
        resumes_dir = settings.resumes_dir
        resumes_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[markdown_exporter] 简历目录: {resumes_dir}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:8]
        filename = f"resume_{timestamp}_{short_id}.md"
        filepath = resumes_dir / filename
        logger.info(f"[markdown_exporter] 保存文件: {filepath}")

        filepath.write_text(markdown_text, encoding="utf-8")
        logger.info(f"[markdown_exporter] 文件保存成功")

        return {
            "resume_markdown": markdown_text,
            "resume_path": str(filepath),
        }
    except Exception as e:
        logger.exception(f"[markdown_exporter] 导出异常: {type(e).__name__}: {str(e)}")
        raise
