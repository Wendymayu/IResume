import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from iresume.agent.prompts.jd_parser_prompt import JD_PARSER_HUMAN, JD_PARSER_SYSTEM
from iresume.agent.state import ResumeState
from iresume.utils.llm import create_llm

logger = logging.getLogger(__name__)


def run(state: ResumeState) -> dict:
    logger.info("[jd_parser] 开始解析JD")
    try:
        jd_raw = state.get("jd_raw", "")
        logger.info(f"[jd_parser] JD长度: {len(jd_raw)}")

        llm = create_llm()
        logger.info(f"[jd_parser] LLM创建完成，模型: {llm.model_name}")

        prompt = JD_PARSER_HUMAN.format(jd_text=jd_raw)
        logger.debug(f"[jd_parser] 提示词长度: {len(prompt)}")

        response = llm.invoke([
            SystemMessage(content=JD_PARSER_SYSTEM),
            HumanMessage(content=prompt),
        ])
        logger.info(f"[jd_parser] LLM响应长度: {len(response.content)}")
        logger.debug(f"[jd_parser] 响应预览: {response.content[:300]}...")

        try:
            jd_parsed = json.loads(response.content)
            logger.info(f"[jd_parser] JSON解析成功，键: {list(jd_parsed.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"[jd_parser] JSON解析失败: {str(e)}")
            jd_parsed = _extract_json(response.content)
            logger.info(f"[jd_parser] 尝试提取JSON成功，键: {list(jd_parsed.keys())}")

        return {"jd_parsed": jd_parsed}
    except Exception as e:
        logger.exception(f"[jd_parser] 解析JD异常: {type(e).__name__}: {str(e)}")
        raise


def _extract_json(text: str) -> dict:
    """Try to extract JSON from markdown code blocks or surrounding text."""
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {}
