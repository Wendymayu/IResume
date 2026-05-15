import logging
from pathlib import Path

from iresume.agent.state import ResumeState
from iresume.storage.profile_repository import ProfileRepository

logger = logging.getLogger(__name__)


def run(state: ResumeState) -> dict:
    logger.info("[profile_loader] 开始加载用户档案")
    try:
        profile_path = state.get("profile_path", "")
        logger.info(f"[profile_loader] profile_path: {profile_path}")

        if not profile_path:
            logger.error("[profile_loader] profile_path 为空")
            return {"profile": {"raw_text": ""}}

        repo = ProfileRepository(Path(profile_path))
        logger.info(f"[profile_loader] ProfileRepository 初始化完成")

        raw_text = repo.load_raw()
        logger.info(f"[profile_loader] 加载完成，文本长度: {len(raw_text)}")
        logger.debug(f"[profile_loader] 原始文本预览: {raw_text[:200]}...")

        return {"profile": {"raw_text": raw_text}}
    except Exception as e:
        logger.exception(f"[profile_loader] 加载档案异常: {type(e).__name__}: {str(e)}")
        raise
