> **U04 current evidence:** [test_api_contract.py](test_api_contract.py) implements 23 offline runtime/contract tests; [report](../docs/certification/U04_API_CONTRACT_REPORT.md). [Canonical API](../11_OPENAPI.yaml) and [guide](../12_API_GUIDE.md) supersede incompatible API examples below. Remaining scenarios are target specifications, not executed live checks.

> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 04_INTEGRATION_TESTS.md

# Integration Test Specification

Project: VK Social Radar

Version: 1.0

Status: Approved

---

# 1. Purpose

Настоящий документ описывает интеграционные тесты системы VK Social Radar.

Интеграционные тесты проверяют взаимодействие компонентов системы, а не отдельные функции.

Каждый тест основан на:

- System Architecture
- C4 Model
- Sequence Diagrams
- Class Diagram
- Acceptance Criteria

---

# 2. Integration Strategy

Каждый тест проверяет завершённый бизнес-сценарий.

Не допускается тестирование отдельных методов.

Минимальная единица тестирования — взаимодействие двух и более компонентов.

---

# 3. Components

Интеграционные тесты покрывают взаимодействие следующих компонентов.

- Frontend
- Backend API
- Collector
- Snapshot Engine
- Timeline Engine
- Analytics Engine
- Graph Engine
- AI Worker
- RAG Service
- SQLite
- Export Service

---

# 4. Integration Environment

Backend

FastAPI

---

Frontend

React

---

Database

SQLite

---

Collector

Playwright

Chromium

---

AI

LM Studio

или

Ollama

---

# 5. Collector Pipeline

## INT-COL-001

Название

Полный цикл запуска Collector.

Проверяемые компоненты

Frontend

↓

Backend

↓

Collector

↓

Playwright

↓

Snapshot Builder

↓

SQLite

Предусловия

Backend запущен.

Frontend открыт.

Шаги

1.

Запустить Collector.

2.

Дождаться окончания.

Ожидаемый результат

Collector завершён.

Создан Snapshot.

Запись сохранена в БД.

Связанные диаграммы

15_SEQUENCE_DIAGRAMS

Collector

---

## INT-COL-002

Collector корректно завершает работу после ошибки браузера.

---

## INT-COL-003

Collector корректно восстанавливает соединение.

---

# 6. Snapshot Pipeline

## INT-SNP-001

Snapshot сохраняется в Repository.

Поток

Collector

↓

Snapshot Builder

↓

Repository

↓

SQLite

Проверяется

- Snapshot существует

- идентификатор уникален

- все связанные сущности сохранены

---

## INT-SNP-002

Повторный Snapshot не повреждает историю.

---

## INT-SNP-003

Удаление Snapshot обновляет Repository.

---

# 7. Timeline Pipeline

## INT-TML-001

Построение Timeline.

Поток

Snapshot

↓

Timeline Service

↓

Repository

↓

Frontend

Проверяется

Timeline содержит изменения.

---

## INT-TML-002

Timeline корректно работает при отсутствии изменений.

---

## INT-TML-003

Timeline корректно строится для большого Snapshot.

---

# 8. Social Graph Pipeline

## INT-GRP-001

Построение графа.

Поток

Snapshot

↓

Graph Engine

↓

Backend

↓

Frontend

Проверяется

Все вершины отображаются.

---

## INT-GRP-002

Количество связей совпадает.

---

## INT-GRP-003

Изолированные вершины отображаются.

---

# 9. Analytics Pipeline

## INT-ANA-001

Полный расчёт аналитики.

Поток

Snapshot

↓

Analytics Engine

↓

Backend

↓

Dashboard

Проверяется

Все показатели рассчитаны.

---

## INT-ANA-002

Статистика обновляется после нового Snapshot.

---

# 10. AI Report Pipeline

## INT-AIR-001

Создание AI Report.

Поток

Frontend

↓

Backend

↓

AI Worker

↓

RAG

↓

SQLite

↓

LLM

↓

AI Report

Проверяется

Report сформирован.

---

## INT-AIR-002

Используется актуальный Snapshot.

---

## INT-AIR-003

Используется контекст RAG.

---

## INT-AIR-004

Report сохраняется.

---

# 11. AI Chat Pipeline

## INT-CHAT-001

Полный цикл AI Chat.

Поток

Frontend

↓

Backend

↓

RAG

↓

LLM

↓

Response

↓

Frontend

Проверяется

Ответ сформирован.

---

## INT-CHAT-002

История сообщений сохраняется.

---

## INT-CHAT-003

Контекст соответствует Snapshot.

---

# 12. Export Pipeline

## INT-EXP-001

Экспорт JSON.

Поток

Snapshot

↓

Export Service

↓

JSON

Проверяется

Файл создан.

---

## INT-EXP-002

Экспорт CSV.

---

## INT-EXP-003

Большой Snapshot экспортируется.

---

# 13. Search Pipeline

## INT-SRC-001

Полный поиск.

Поток

Frontend

↓

Backend

↓

Repository

↓

SQLite

↓

Frontend

Проверяется

Результаты соответствуют запросу.

---

## INT-SRC-002

Поиск по сообщениям.

---

## INT-SRC-003

Поиск по друзьям.

---

# 14. Settings Pipeline

## INT-SET-001

Изменение настроек.

Поток

Frontend

↓

Backend

↓

Repository

↓

SQLite

↓

Frontend

Проверяется

Настройки сохранены.

---

## INT-SET-002

Настройки восстанавливаются после перезапуска.

---

# 15. Error Recovery

## INT-ERR-001

Collector недоступен.

Frontend отображает ошибку.

---

## INT-ERR-002

SQLite повреждена.

Backend возвращает ошибку.

---

## INT-ERR-003

AI Worker недоступен.

Backend корректно сообщает об ошибке.

---

## INT-ERR-004

RAG возвращает пустой результат.

AI продолжает работу.

---

## INT-ERR-005

Frontend корректно отображает ошибки Backend.

---

# 16. End-to-End Business Scenarios

## E2E-001

Первый запуск приложения.

Шаги

1.

Backend запускается.

2.

Frontend запускается.

3.

Collector запускается.

4.

Создаётся Snapshot.

5.

Строится Timeline.

6.

Строится Graph.

7.

Считается Analytics.

8.

Создаётся AI Report.

9.

Экспортируется JSON.

Ожидаемый результат

Полный цикл завершается без ошибок.

---

## E2E-002

Повторный Snapshot.

Проверяется

Timeline показывает изменения.

---

## E2E-003

AI анализирует историю нескольких Snapshot.

---

## E2E-004

Полный пользовательский сценарий поиска.

---

# 17. Performance Integration

Проверяется время выполнения цепочек.

Collector

<60 сек

---

AI Report

<30 сек

---

Export JSON

<5 сек

---

Timeline

<2 сек

---

Analytics

<5 сек

---

# 18. Traceability Matrix

| Sequence Diagram | Integration Test |
|------------------|------------------|
| Collector Pipeline | INT-COL-001 |
| Snapshot Pipeline | INT-SNP-001 |
| Timeline Pipeline | INT-TML-001 |
| Graph Pipeline | INT-GRP-001 |
| Analytics Pipeline | INT-ANA-001 |
| AI Report Pipeline | INT-AIR-001 |
| AI Chat Pipeline | INT-CHAT-001 |
| Export Pipeline | INT-EXP-001 |
| Search Pipeline | INT-SRC-001 |
| Settings Pipeline | INT-SET-001 |
| Full Business Flow | E2E-001 |

---

# 19. Definition of Done

Каждый интеграционный тест считается успешным только если:

✓ Все компоненты успешно взаимодействуют.

✓ Все данные проходят через полный pipeline.

✓ Нет потери данных.

✓ Нет нарушения архитектурных зависимостей.

✓ Все Sequence Diagrams подтверждены фактическим поведением системы.

✓ Все Acceptance Criteria выполнены.

---

# 20. Architectural Rule

Каждый новый бизнес-сценарий проекта обязан сопровождаться:

- обновлением Sequence Diagram;

- добавлением нового Integration Test;

- обновлением Traceability Matrix.

Ни один архитектурный сценарий не считается реализованным без соответствующего Integration Test.