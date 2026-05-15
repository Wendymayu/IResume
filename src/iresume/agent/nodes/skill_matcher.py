import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from iresume.agent.prompts.skill_matcher_prompt import (
    SKILL_MATCHER_HUMAN,
    SKILL_MATCHER_SYSTEM,
)
from iresume.agent.state import ResumeState
from iresume.utils.llm import create_llm

logger = logging.getLogger(__name__)


def run(state: ResumeState) -> dict:
    logger.info("[skill_matcher] 开始匹配技能")
    try:
        jd_parsed = state.get("jd_parsed", {})
        profile = state.get("profile", {})
        logger.info(f"[skill_matcher] JD键: {list(jd_parsed.keys())}, Profile键: {list(profile.keys())}")

        llm = create_llm()
        logger.info(f"[skill_matcher] LLM创建完成，模型: {llm.model_name}")

        prompt = SKILL_MATCHER_HUMAN.format(
            jd_parsed=json.dumps(jd_parsed, ensure_ascii=False, indent=2),
            profile=_get_profile_text(profile),
        )
        logger.debug(f"[skill_matcher] 提示词长度: {len(prompt)}")

        response = llm.invoke([
            SystemMessage(content=SKILL_MATCHER_SYSTEM),
            HumanMessage(content=prompt),
        ])
        logger.info(f"[skill_matcher] LLM响应长度: {len(response.content)}")
        logger.debug(f"[skill_matcher] 响应预览: {response.content[:300]}...")

        try:
            matches = json.loads(response.content)
            logger.info(f"[skill_matcher] JSON解析成功，匹配数: {len(matches) if isinstance(matches, list) else 'N/A'}")
        except json.JSONDecodeError as e:
            logger.error(f"[skill_matcher] JSON解析失败: {str(e)}")
            matches = _extract_json_list(response.content)
            logger.info(f"[skill_matcher] 尝试提取JSON成功，匹配数: {len(matches)}")

        result = {"skill_matches": matches if isinstance(matches, list) else []}
        logger.info(f"[skill_matcher] 返回结果，技能匹配数: {len(result['skill_matches'])}")
        return result
    except Exception as e:
        logger.exception(f"[skill_matcher] 匹配技能异常: {type(e).__name__}: {str(e)}")
        raise


def _get_profile_text(profile: dict) -> str:
    """Extract raw text from profile dict (supports both raw_text and structured formats)."""
    if "raw_text" in profile:
        return profile["raw_text"]
    return json.dumps(profile, ensure_ascii=False, indent=2)


def _extract_json_list(text: str) -> list[dict]:
    import re
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return []
