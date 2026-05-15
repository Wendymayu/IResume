import logging

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from iresume.config import settings

logger = logging.getLogger(__name__)


def create_llm(
    model: str | None = None,
    temperature: float | None = None,
) -> BaseChatModel:
    model = model or settings.llm_model
    temperature = temperature if temperature is not None else settings.llm_temperature

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
