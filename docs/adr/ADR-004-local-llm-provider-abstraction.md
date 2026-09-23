# ADR-004 — Local LLM + Provider Abstraction

**Status:** ACCEPTED / IMPLEMENTATION PLANNED. **Implementation:** PLANNED abstraction; concrete LM Studio integration exists. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U05 provider, U06 privacy, U07 tests, U09 resilience](../certification/05_UPGRADE_BACKLOG.md).

## Context

AI optional для core local functionality, но [main.py](../../app/main.py) прямо импортирует [lmstudio.py](../../app/lmstudio.py). Один модуль содержит prompt, HTTP, settings и persistence. Интерфейса provider, factory/selection и Ollama adapter нет.

## Decision

Ввести минимальный vendor-neutral provider port для AI use cases: typed request/result/error, selection в composition/configuration boundary, concrete LM Studio adapter. Prompt/context/persistence responsibilities отделить от HTTP. Сохранить local-first policy. Второй adapter не обещается без test evidence; Ollama — возможное расширение принятого port, не AS-IS.

## Current implementation status

PLANNED abstraction; IMPLEMENTED concrete HTTP integration: GET `/models`, POST `/chat/completions`, configurable model/temperature/base_url; API/UI call sites есть. Нет inference/adapter contract tests и live verification. Endpoint compatibility не равна provider abstraction.

## Alternatives considered

Оставить direct LM functions; generic URL-only configuration; крупный multi-provider framework. Первые два не дают бизнес-уровню независимого контракта. Framework пока не обоснован числом providers/use cases; небольшой port достаточен.

## Consequences

- Positive: deterministic fake provider, testable use cases, vendor substitution без переписывания prompts.
- Negative: новый контракт/error mapping, проверка совместимости JSON output.
- Risks: переобобщённый port, различия schema enforcement/model capabilities; результат нужно валидировать локально.

## Security/Privacy impact

Provider selection не должен разрешать скрытый remote fallback; U06 проверяет endpoint locality. Передавать только нужные поля и source context. Credential policy для будущего provider требует отдельной конфигурации, не hardcoding.

## Validation/Evidence

[LLM verdict](../certification/02_PATTERN_INVENTORY.md): no Protocol/ABC/selection, timeouts 8/120 s, no retry/breaker. Target U05 tests: fake provider + LM adapter contract, malformed response, invalid fields, unavailable dependency, business layer без concrete imports.

## Evolution path

U05 port/adapter/output validation → U08 retrieval use case → U09 bounded retry/breaker после U11 NFR. Принятие ADR не реализует ни port, ни resilience.
