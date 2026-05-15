import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from iresume.agent.prompts.gap_analyzer_prompt import (
    GAP_ANALYZER_HUMAN,
    GAP_ANALYZER_SYSTEM,
)
from iresume.agent.state import ResumeState
from iresume.utils.llm import create_llm

logger = logging.getLogger(__name__)


def run(state: ResumeState) -> dict:
    logger.info("[gap_analyzer] 开始分析缺口")
    try:
        jd_parsed = state.get("jd_parsed", {})
        skill_matches = state.get("skill_matches", [])
        profile = state.get("profile", {})
        logger.info(f"[gap_analyzer] JD键: {list(jd_parsed.keys())}, 技能匹配数: {len(skill_matches)}")

        llm = create_llm()
        logger.info(f"[gap_analyzer] LLM创建完成，模型: {llm.model_name}")

        prompt = GAP_ANALYZER_HUMAN.format(
            jd_parsed=json.dumps(jd_parsed, ensure_ascii=False, indent=2),
            skill_matches=json.dumps(skill_matches, ensure_ascii=False, indent=2),
            profile=_get_profile_text(profile),
        )
        logger.debug(f"[gap_analyzer] 提示词长度: {len(prompt)}")

        response = llm.invoke([
            SystemMessage(content=GAP_ANALYZER_SYSTEM),
            HumanMessage(content=prompt),
        ])
        logger.info(f"[gap_analyzer] LLM响应长度: {len(response.content)}")
        logger.debug(f"[gap_analyzer] 响应预览: {response.content[:300]}...")

        try:
            gap_report = json.loads(response.content)
            logger.info(f"[gap_analyzer] JSON解析成功，键: {list(gap_report.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"[gap_analyzer] JSON解析失败: {str(e)}")
            gap_report = _extract_json(response.content)
            logger.info(f"[gap_analyzer] 尝试提取JSON成功，键: {list(gap_report.keys())}")

        # Validate recommendation
        valid = {"proceed", "proceed_with_caveats", "not_viable"}
        recommendation = gap_report.get("recommendation")
        logger.info(f"[gap_analyzer] 原始建议: {recommendation}, 可行性评分: {gap_report.get('viability_score')}")

        if recommendation not in valid:
            score = gap_report.get("viability_score", 0)
            if score >= 0.5:
                gap_report["recommendation"] = "proceed"
            elif score >= 0.3:
                gap_report["recommendation"] = "proceed_with_caveats"
            else:
                gap_report["recommendation"] = "not_viable"
            logger.info(f"[gap_analyzer] 调整建议为: {gap_report['recommendation']}")

        logger.info(f"[gap_analyzer] 最终建议: {gap_report.get('recommendation')}")
        return {"gap_report": gap_report}
    except Exception as e:
        logger.exception(f"[gap_analyzer] 分析缺口异常: {type(e).__name__}: {str(e)}")
        raise


def _extract_json(text: str) -> dict:
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {"recommendation": "proceed", "viability_score": 0.5, "missing_skills": [], "weak_skills": []}


def _get_profile_text(profile: dict) -> str:
    if "raw_text" in profile:
        return profile["raw_text"]
    return json.dumps(profile, ensure_ascii=False, indent=2)
