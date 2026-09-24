> **U04 current evidence:** [test_api_contract.py](test_api_contract.py) implements 23 offline runtime/contract tests; [report](../docs/certification/U04_API_CONTRACT_REPORT.md). [Canonical API](../11_OPENAPI.yaml) and [guide](../12_API_GUIDE.md) supersede incompatible API examples below. Remaining scenarios are target specifications, not executed live checks.

> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 03_API_TESTS.md

# API Test Specification

Project: VK Social Radar

Version: 1.0

Status: Approved

---

# 1. Purpose

Настоящий документ определяет проверки REST API проекта VK Social Radar.

Каждый endpoint должен быть протестирован:

- позитивными сценариями;
- негативными сценариями;
- проверкой схемы OpenAPI;
- проверкой бизнес-правил;
- проверкой обработки ошибок.

Документ связан с:

- OpenAPI.yaml
- API_GUIDE.md
- Acceptance Criteria
- Test Cases
- Integration Tests

---

# 2. Test Strategy

Для каждого endpoint выполняются проверки:

✓ HTTP Status

✓ Response Body

✓ JSON Schema

✓ Headers

✓ Validation

✓ Error Handling

✓ Idempotency (где применимо)

✓ Performance

✓ Traceability

---

# 3. Response Validation

Проверяется:

- соответствие OpenAPI Schema;
- отсутствие лишних полей;
- обязательные поля присутствуют;
- типы данных корректны;
- nullable соблюдается;
- enum соответствует Specification.

---

# 4. HTTP Codes

Все endpoints обязаны корректно использовать статусы.

| Код | Назначение |
|------|------------|
|200|Успех|
|201|Создано|
|202|Принято|
|204|Нет содержимого|
|400|Ошибка запроса|
|404|Не найдено|
|409|Конфликт|
|422|Ошибка валидации|
|429|Слишком много запросов|
|500|Внутренняя ошибка|

---

# 5. Health API

## API-HLT-001

Endpoint

GET /health

Цель

Проверка доступности сервиса.

Проверки

- HTTP 200
- application/json
- status = "ok"
- version присутствует
- timestamp присутствует

---

## API-HLT-002

Backend отвечает менее чем за 500 мс.

---

# 6. Collector API

## API-COL-001

POST /collector/run

Позитивный сценарий

Ожидается

- HTTP 202
- collectorId присутствует
- status = queued/running

---

## API-COL-002

Повторный запуск Collector.

Проверяется корректная обработка.

---

## API-COL-003

Некорректный JSON.

Ожидается

422.

---

## API-COL-004

Обязательные поля отсутствуют.

Ожидается

422.

---

## API-COL-005

Ошибка браузера.

Ожидается

500.

---

# 7. Snapshot API

## API-SNP-001

GET /snapshots

Ожидается

200.

Возвращается массив Snapshot.

---

## API-SNP-002

Пустая база.

Возвращается пустой массив.

---

## API-SNP-003

GET /snapshots/{id}

Корректный id.

Возвращается Snapshot.

---

## API-SNP-004

Несуществующий id.

404.

---

## API-SNP-005

Некорректный UUID.

422.

---

## API-SNP-006

DELETE /snapshots/{id}

Snapshot удалён.

204.

---

# 8. Timeline API

## API-TML-001

GET /timeline

Возвращается Timeline.

---

## API-TML-002

Фильтрация по периоду.

---

## API-TML-003

Пустой Timeline.

---

## API-TML-004

Некорректный диапазон дат.

422.

---

# 9. Graph API

## API-GRP-001

GET /graph

Возвращается граф.

---

## API-GRP-002

Количество узлов соответствует Snapshot.

---

## API-GRP-003

Количество связей корректно.

---

# 10. Analytics API

## API-ANA-001

GET /analytics

Возвращаются показатели.

---

## API-ANA-002

Проверка обязательных полей.

---

## API-ANA-003

Типы данных соответствуют OpenAPI.

---

# 11. AI Report API

## API-AIR-001

POST /ai/report

Создание отчёта.

HTTP 202.

---

## API-AIR-002

Некорректный Snapshot.

404.

---

## API-AIR-003

AI недоступен.

503.

---

## API-AIR-004

Повторная генерация.

Обрабатывается корректно.

---

# 12. AI Chat API

## API-CHAT-001

POST /ai/chat

Успешный ответ.

---

## API-CHAT-002

Пустой вопрос.

422.

---

## API-CHAT-003

Большой вопрос.

Корректная обработка.

---

## API-CHAT-004

Отсутствует Snapshot.

404.

---

## API-CHAT-005

Ответ соответствует схеме.

---

# 13. Search API

## API-SRC-001

GET /search

Поиск по имени.

---

## API-SRC-002

Поиск по сообщению.

---

## API-SRC-003

Пустой результат.

200.

---

## API-SRC-004

Некорректные параметры.

422.

---

# 14. Export API

## API-EXP-001

GET /export/json

JSON создаётся.

---

## API-EXP-002

GET /export/csv

CSV создаётся.

---

## API-EXP-003

Пустая база.

Возвращается пустой экспорт.

---

# 15. Settings API

## API-SET-001

GET /settings

Настройки возвращаются.

---

## API-SET-002

PUT /settings

Настройки сохраняются.

---

## API-SET-003

Некорректные параметры.

422.

---

# 16. Common Validation

Для каждого endpoint дополнительно выполняются проверки.

## VAL-001

Content-Type корректный.

---

## VAL-002

UTF-8.

---

## VAL-003

JSON валиден.

---

## VAL-004

OpenAPI Schema совпадает.

---

## VAL-005

Нет неожиданных полей.

---

## VAL-006

Enum соответствует Specification.

---

## VAL-007

Все обязательные поля присутствуют.

---

# 17. Negative Testing

Каждый endpoint проверяется:

✓ пустой запрос

✓ отсутствующее обязательное поле

✓ неизвестное поле

✓ слишком длинная строка

✓ отрицательные числа

✓ слишком большие числа

✓ неправильный UUID

✓ неверный JSON

✓ SQL Injection строка

✓ XSS строка

✓ Unicode

✓ Emoji

✓ null

✓ массив вместо объекта

✓ объект вместо массива

---

# 18. Performance Requirements

Health

<500 ms

---

GET endpoints

<1000 ms

---

POST endpoints

<3000 ms

---

Export

<5000 ms

---

# 19. OpenAPI Compliance

Все endpoints обязаны соответствовать:

- пути;
- HTTP-методу;
- параметрам;
- Request Body;
- Response Body;
- Error Response;
- JSON Schema.

Любое расхождение считается дефектом.

---

# 20. Traceability Matrix

| Endpoint | Test Cases | Acceptance |
|-----------|------------|------------|
|GET /health|API-HLT-001|AC-SYS-001|
|POST /collector/run|API-COL-001|AC-COL-001|
|GET /snapshots|API-SNP-001|AC-SNP-001|
|GET /timeline|API-TML-001|AC-TML-001|
|GET /graph|API-GRP-001|AC-GRP-001|
|GET /analytics|API-ANA-001|AC-ANA-001|
|POST /ai/report|API-AIR-001|AC-AI-001|
|POST /ai/chat|API-CHAT-001|AC-CHAT-001|
|GET /search|API-SRC-001|AC-SRC-001|
|GET /export/json|API-EXP-001|AC-EXP-001|

Каждый endpoint обязан иметь минимум:

- 1 позитивный тест;
- 3 негативных теста;
- проверку схемы OpenAPI;
- проверку производительности;
- связь с Acceptance Criteria.

---

# 21. Definition of Done

API считается реализованным только если:

✓ OpenAPI соответствует реализации

✓ Все API Tests проходят

✓ Все негативные сценарии проходят

✓ JSON Schema полностью совпадает

✓ Нет Critical и High дефектов

✓ Endpoint включён в Regression Suite

✓ Endpoint включён в Smoke Tests (если критичен)