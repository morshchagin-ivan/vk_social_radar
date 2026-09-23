from typing import Protocol

from .contracts import GenerationRequest, GenerationResult, ModelInfo


class LLMProvider(Protocol):
    """Only today's capabilities. Connection testing uses model discovery.

    Implementations return normalized values or raise ProviderError subclasses;
    they do not retry, persist insights or interpret the Person domain.
    """

    def list_models(self) -> list[ModelInfo]: ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...
