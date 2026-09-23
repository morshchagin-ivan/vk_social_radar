# ADR-004 — Local LLM + Provider Abstraction

**Status:** ACCEPTED. **Implementation:** IMPLEMENTED provider port + LM Studio adapter (U05); DIP at AI boundary only. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U05 provider, U06 privacy, U07 tests, U09 resilience](../certification/05_UPGRADE_BACKLOG.md).

## Context

До U05 AI optional для core local functionality, но main прямо импортировал concrete lmstudio functions; один модуль содержал prompt, HTTP, settings и persistence. [Исторический audit](../certification/02_PATTERN_INVENTORY.md) зафиксировал отсутствие provider seam. U05 устраняет эту coupling, сохраняя person insight use case и actual API.

## Decision

Использовать минимальный vendor-neutral [LLMProvider Protocol](../../app/ai/provider.py) с list_models/generate. Protocol выбран для structural substitution: fake и будущий adapter не обязаны наследовать base class. Typed dataclasses задают messages/model/temperature/optional JSON schema и content/model/provider result; четыре ProviderError subclass нормализуют transport failures. Connection test использует model discovery, отдельный health method не нужен.

Единственная production binding — [composition](../../app/ai/composition.py): existing settings → LMStudioProvider и AIInsightService. Только один adapter, поэтому user-visible llm_provider не добавляется. Business prompt, local validation и persistence отделены от HTTP. Ollama NOT IMPLEMENTED; скрытый fallback отсутствует.

## Current implementation status

IMPLEMENTED: [AIInsightService](../../app/ai/service.py) → LLMProvider → [LMStudioProvider](../../app/ai/providers/lmstudio.py) → HTTP. Main импортирует composition/service/settings, не concrete compatibility module. Adapter владеет URL/paths/httpx, 8/120s timeouts, request mapping и response/error extraction; не знает Person/SQLite/FastAPI. Service не импортирует httpx/adapter. SQL остаётся прямым: это **не global DIP/Repository**.

Local validation требует ровно status/confidence/summary/evidence/cautions, проверяет enum, number 0…1 (не bool/NaN/Infinity), string и arrays of strings. Невалидный output не сохраняется. API paths/shapes и lmstudio_* settings сохранены, optional model descriptors проходят обратно через models API. Ошибки остаются HTTP 503/detail, текст теперь нормализован без raw response/prompt. Live inference не запускался.

## Alternatives considered

Оставить direct LM functions; generic URL-only configuration; крупный multi-provider framework. Первые два не дают бизнес-уровню независимого контракта. Framework пока не обоснован числом providers/use cases; небольшой port достаточен.

## Consequences

- Positive: deterministic fake provider, testable use cases, vendor substitution без переписывания prompts.
- Negative: новый контракт/error mapping, проверка совместимости JSON output.
- Risks: переобобщённый port, различия schema enforcement/model capabilities; результат нужно валидировать локально.

## Security/Privacy impact

Default остаётся loopback; arbitrary remote URL — открытый U06 debt. Состав fixed person context сохранён: name, latest metrics и первые десять events. Нет prompt/raw response logging, telemetry/cloud adapter или fallback. Credential policy для будущего provider требует отдельной конфигурации, не hardcoding.

## Validation/Evidence

[U05 report](../certification/U05_LLM_PROVIDER_REPORT.md), [26 tests](../../tests/test_ai_provider.py): reusable provider contract для fake и mocked LM adapter; mapping/error/timeout/no-retry; structured validation/persistence/API/settings; AST dependency fitness. Standard discovery 58 PASS (26 U05 + 14 U02 + 18 existing), additional 8 отдельно PASS. Tests block network; user DB unchanged. Исторический audit сохраняется без переписывания результатов.

## Evolution path

U05 завершена; рекомендуемый следующий increment — U03 source model. U08 retrieval и U09 resilience после принятых dependencies/NFR остаются PLANNED. Runtime RAG = NO_RAG; Retry/Backoff/Jitter/Circuit Breaker = NOT IMPLEMENTED. Нормализованные ошибки сами по себе не являются retry policy.
