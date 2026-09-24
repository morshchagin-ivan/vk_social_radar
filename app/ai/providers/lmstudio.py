from __future__ import annotations

from dataclasses import asdict
from typing import Any

import httpx
from ...privacy import local_llm_url

from ..contracts import (
    GenerationRequest, GenerationResult, ModelInfo, ProviderProtocolError,
    ProviderResponseError, ProviderTimeoutError, ProviderUnavailableError,
)


class LMStudioProvider:
    def __init__(self, base_url: str, *, transport: httpx.BaseTransport | None = None):
        self.base_url = local_llm_url(base_url)
        self.transport = transport

    def _request(self, method: str, path: str, timeout: float, **kwargs: Any) -> dict[str, Any]:
        endpoint = local_llm_url(self.base_url)
        try:
            with httpx.Client(timeout=timeout, transport=self.transport, trust_env=False, follow_redirects=False) as client:
                response = client.request(method, f"{endpoint}{path}", **kwargs)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Provider request timed out") from None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {429, 500, 502, 503, 504}:
                raise ProviderUnavailableError("Provider is unavailable") from None
            raise ProviderProtocolError("Provider rejected the request") from None
        except (httpx.InvalidURL, httpx.UnsupportedProtocol, httpx.ProtocolError):
            raise ProviderProtocolError("Provider protocol or configuration is invalid") from None
        except httpx.DecodingError:
            raise ProviderResponseError("Provider returned invalid response encoding") from None
        except (httpx.NetworkError, httpx.ProxyError):
            raise ProviderUnavailableError("Provider is unavailable") from None
        except httpx.RequestError:
            raise ProviderProtocolError("Provider request could not be completed") from None
        except (ValueError, RecursionError):
            raise ProviderResponseError("Provider returned invalid JSON") from None
        if not isinstance(payload, dict):
            raise ProviderResponseError("Provider returned an invalid response envelope")
        return payload

    def list_models(self) -> list[ModelInfo]:
        payload = self._request("GET", "/models", 8.0)
        rows = payload.get("data")
        if not isinstance(rows, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip()
            for row in rows
        ):
            raise ProviderResponseError("Provider returned an invalid model list")
        return [ModelInfo(row["id"], {key: value for key, value in row.items() if key != "id"}) for row in rows]

    def generate(self, request: GenerationRequest) -> GenerationResult:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [asdict(message) for message in request.messages],
            "temperature": request.temperature,
            "stream": False,
        }
        if request.structured_output is not None:
            output = request.structured_output
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": output.name, "strict": True, "schema": output.schema},
            }
        raw = self._request("POST", "/chat/completions", 120.0, json=payload)
        try:
            choices = raw["choices"]
            if not isinstance(choices, list) or not choices:
                raise ValueError
            content = choices[0]["message"]["content"]
            model = raw.get("model", request.model)
            if not isinstance(content, str) or not isinstance(model, str) or not model.strip():
                raise ValueError
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderResponseError("Provider returned an invalid completion") from None
        return GenerationResult(content=content, model=model, provider="lmstudio")
