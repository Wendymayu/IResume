import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from iresume.agent.prompts.resume_generator_prompt import (
    RESUME_GENERATOR_HUMAN,
    RESUME_GENERATOR_SYSTEM,
)
from iresume.agent.state import ResumeState
from iresume.utils.llm import create_llm

logger = logging.getLogger(__name__)


def run(state: ResumeState) -> dict:
    logger.info("[resume_generator] 开始生成简历")
    try:
        jd_parsed = state.get("jd_parsed", {})
        profile = state.get("profile", {})
        skill_matches = state.get("skill_matches", [])
        gap_report = state.get("gap_report", {})
        logger.info(f"[resume_generator] 输入状态 - JD键: {list(jd_parsed.keys())}, 技能数: {len(skill_matches)}, 缺口报告键: {list(gap_report.keys())}")

        llm = create_llm(temperature=0.4)
        logger.info(f"[resume_generator] LLM创建完成，模型: {llm.model_name}")

        prompt = RESUME_GENERATOR_HUMAN.format(
            jd_parsed=json.dumps(jd_parsed, ensure_ascii=False, indent=2),
            profile=_get_profile_text(profile),
            skill_matches=json.dumps(skill_matches, ensure_ascii=False, indent=2),
            gap_report=json.dumps(gap_report, ensure_ascii=False, indent=2),
        )
        logger.debug(f"[resume_generator] 提示词长度: {len(prompt)}")

        response = llm.invoke([
            SystemMessage(content=RESUME_GENERATOR_SYSTEM),
            HumanMessage(content=prompt),
        ])
        logger.info(f"[resume_generator] LLM响应长度: {len(response.content)}")
        logger.debug(f"[resume_generator] 响应预览: {response.content[:300]}...")

        try:
            resume_content = json.loads(response.content)
            logger.info(f"[resume_generator] JSON解析成功，键: {list(resume_content.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"[resume_generator] JSON解析失败: {str(e)}")
            resume_content = _extract_json(response.content)
            logger.info(f"[resume_generator] 尝试提取JSON成功，键: {list(resume_content.keys())}")

        logger.info(f"[resume_generator] 简历内容生成完成")
        return {"resume_content": resume_content}
    except Exception as e:
        logger.exception(f"[resume_generator] 生成简历异常: {type(e).__name__}: {str(e)}")
        raise


def _extract_json(text: str) -> dict:
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {}


def _get_profile_text(profile: dict) -> str:
    if "raw_text" in profile:
        return profile["raw_text"]
    return json.dumps(profile, ensure_ascii=False, indent=2)
