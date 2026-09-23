"""The only production binding from the provider port to LM Studio."""
from threading import Lock

from .provider import LLMProvider
from .providers.lmstudio import LMStudioProvider
from .resilience import ResilientLLMProvider
from .service import AIInsightService
from .settings import get_settings

_binding_lock = Lock()
_active_provider: tuple[str, ResilientLLMProvider] | None = None


def get_provider() -> LLMProvider:
    global _active_provider
    settings = get_settings()
    base_url = settings.get("lmstudio_base_url", "http://127.0.0.1:1234/v1").rstrip("/")
    # One active endpoint binding per process. Model/temperature edits do not
    # reset an outage; endpoint changes replace the binding without sharing state.
    with _binding_lock:
        if _active_provider is None or _active_provider[0] != base_url:
            _active_provider = (base_url, ResilientLLMProvider(LMStudioProvider(base_url)))
        return _active_provider[1]


def get_insight_service() -> AIInsightService:
    settings = get_settings()
    return AIInsightService(
        get_provider(), model=settings.get("lmstudio_model", ""),
        temperature=settings.get("lmstudio_temperature", "0.2"),
    )
