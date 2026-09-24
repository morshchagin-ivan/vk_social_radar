"""The only production binding from the provider port to LM Studio."""
from threading import Lock

from .provider import LLMProvider
from .providers.lmstudio import LMStudioProvider
from .resilience import ResilientLLMProvider
from .service import AIInsightService
from .settings import get_settings
from ..privacy import local_llm_url

_binding_lock = Lock()
_active_provider: tuple[str, ResilientLLMProvider] | None = None


def get_provider() -> LLMProvider:
    global _active_provider
    settings = get_settings()
    base_url = local_llm_url(settings.get("lmstudio_base_url", "http://127.0.0.1:1234/v1"))
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


def get_rag_service():
    """Explicit local service entry point; rebuild current persisted evidence read-only."""
    import sqlite3
    from contextlib import closing
    from .. import db
    from ..rag.corpus import build_corpus
    from ..rag.models import RAGValidationError
    from ..rag.retrieval import LexicalIndex
    from ..rag.service import RAGService

    try:
        with closing(sqlite3.connect(db.DB_PATH.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
            documents = build_corpus(conn)
    except sqlite3.Error:
        raise RAGValidationError('RAG corpus database unavailable') from None
    settings = get_settings()
    # Reuse the U05/U09/U06 composition boundary, including shared circuit state.
    return RAGService(LexicalIndex(documents), get_provider(), model=settings.get('lmstudio_model', ''))
