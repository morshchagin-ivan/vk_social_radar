"""The only production binding from the provider port to LM Studio."""
from .provider import LLMProvider
from .providers.lmstudio import LMStudioProvider
from .service import AIInsightService
from .settings import get_settings


def get_provider() -> LLMProvider:
    settings = get_settings()
    return LMStudioProvider(settings.get("lmstudio_base_url", "http://127.0.0.1:1234/v1"))


def get_insight_service() -> AIInsightService:
    settings = get_settings()
    return AIInsightService(
        get_provider(), model=settings.get("lmstudio_model", ""),
        temperature=settings.get("lmstudio_temperature", "0.2"),
    )
