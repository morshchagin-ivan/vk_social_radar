> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 05_SMOKE_TESTS.md

# Smoke Test Specification

Project: VK Social Radar

Version: 1.0

Status: Approved

---

# 1. Purpose

Настоящий документ определяет минимальный набор проверок,
который должен успешно выполняться после каждой сборки проекта.

Smoke Tests предназначены для быстрого подтверждения того, что:

- система запускается;
- основные сервисы доступны;
- критический пользовательский сценарий работоспособен;
- сборка пригодна для дальнейшего тестирования либо выпуска.

Smoke Tests не заменяют Integration Tests и Regression Tests.

---

# 2. Goals

Smoke Tests должны подтвердить:

✓ приложение запускается

✓ Backend отвечает

✓ Frontend доступен

✓ база данных работает

✓ Collector запускается

✓ Snapshot создаётся

✓ Timeline строится

✓ Analytics работает

✓ AI отвечает

✓ Export работает

---

# 3. Execution Rules

Smoke Tests выполняются:

- после каждой сборки;
- перед публикацией релиза;
- после обновления зависимостей;
- после миграций базы данных;
- после изменения архитектуры.

---

# 4. Test Environment

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

# 5. Infrastructure Checks

## SMK-INF-001

Backend запускается.

Ожидаемый результат

HTTP сервер успешно стартует.

PASS

---

## SMK-INF-002

Frontend запускается.

PASS

---

## SMK-INF-003

SQLite открывается.

PASS

---

## SMK-INF-004

Playwright доступен.

PASS

---

## SMK-INF-005

LLM Provider доступен.

PASS

---

# 6. API Checks

## SMK-API-001

GET /health

Ожидается

HTTP 200

---

## SMK-API-002

GET /snapshots

HTTP 200

---

## SMK-API-003

GET /settings

HTTP 200

---

## SMK-API-004

GET /analytics

HTTP 200

---

# 7. Collector Checks

## SMK-COL-001

Collector запускается.

PASS

---

## SMK-COL-002

Collector завершается успешно.

PASS

---

## SMK-COL-003

Создан Snapshot.

PASS

---

# 8. Snapshot Checks

## SMK-SNP-001

Snapshot сохраняется.

---

## SMK-SNP-002

Snapshot читается.

---

## SMK-SNP-003

Snapshot содержит данные.

---

# 9. Timeline Checks

## SMK-TML-001

Timeline создаётся.

---

## SMK-TML-002

Timeline содержит изменения.

(если существует более одного Snapshot)

---

# 10. Graph Checks

## SMK-GRP-001

Graph строится.

---

## SMK-GRP-002

Количество узлов больше нуля.

---

# 11. Analytics Checks

## SMK-ANA-001

Статистика вычисляется.

---

## SMK-ANA-002

Dashboard отображает показатели.

---

# 12. AI Checks

## SMK-AI-001

AI Report создаётся.

---

## SMK-AI-002

AI Chat отвечает.

---

## SMK-AI-003

RAG возвращает контекст.

---

# 13. Export Checks

## SMK-EXP-001

JSON экспортируется.

---

## SMK-EXP-002

CSV экспортируется.

---

# 14. Search Checks

## SMK-SRC-001

Поиск возвращает результаты.

---

# 15. UI Checks

## SMK-UI-001

Dashboard открывается.

---

## SMK-UI-002

Навигация работает.

---

## SMK-UI-003

Ошибок JavaScript нет.

---

# 16. End-to-End Smoke

## SMK-E2E-001

Полный сценарий пользователя.

Последовательность

1.

Запустить Backend.

↓

2.

Запустить Frontend.

↓

3.

Открыть Dashboard.

↓

4.

Запустить Collector.

↓

5.

Создать Snapshot.

↓

6.

Открыть Timeline.

↓

7.

Открыть Analytics.

↓

8.

Создать AI Report.

↓

9.

Выполнить Export JSON.

Ожидаемый результат

Полный пользовательский сценарий выполняется без ошибок.

---

# 17. Failure Policy

Если не пройден хотя бы один тест уровня Critical,

релиз автоматически блокируется.

---

# 18. Smoke Priority

## Critical

Без прохождения выпуск невозможен.

- Backend
- Frontend
- SQLite
- Collector
- Snapshot
- AI
- Export

---

## High

Должны проходить до передачи QA.

- Timeline
- Graph
- Analytics
- Search

---

## Medium

Могут быть временно исключены по согласованию.

- Settings
- UI Improvements

---

# 19. CI/CD Requirements

Smoke Tests должны запускаться автоматически:

✓ после Build

✓ после Deploy в Test Environment

✓ перед Release

✓ после Rollback Recovery

---

# 20. Release Gate

Сборка считается пригодной к выпуску только при выполнении условий.

| Проверка | Статус |
|----------|--------|
| Build | PASS |
| Backend Start | PASS |
| Frontend Start | PASS |
| Database | PASS |
| Health API | PASS |
| Collector | PASS |
| Snapshot | PASS |
| Timeline | PASS |
| Graph | PASS |
| Analytics | PASS |
| AI Report | PASS |
| AI Chat | PASS |
| Export JSON | PASS |
| Export CSV | PASS |
| Search | PASS |
| Smoke Suite | PASS |

---

# 21. Traceability Matrix

| Smoke Test | Integration Test | API Test | Acceptance |
|-------------|------------------|----------|------------|
| SMK-INF-001 | INT-INF-001 | API-HLT-001 | AC-SYS-001 |
| SMK-COL-001 | INT-COL-001 | API-COL-001 | AC-COL-001 |
| SMK-SNP-001 | INT-SNP-001 | API-SNP-001 | AC-SNP-001 |
| SMK-TML-001 | INT-TML-001 | API-TML-001 | AC-TML-001 |
| SMK-GRP-001 | INT-GRP-001 | API-GRP-001 | AC-GRP-001 |
| SMK-ANA-001 | INT-ANA-001 | API-ANA-001 | AC-ANA-001 |
| SMK-AI-001 | INT-AIR-001 | API-AIR-001 | AC-AI-001 |
| SMK-EXP-001 | INT-EXP-001 | API-EXP-001 | AC-EXP-001 |

Каждый Smoke Test обязан иметь связь с:

- функциональным сценарием;
- Integration Test;
- API Test;
- Acceptance Criteria.

---

# 22. Definition of Done

Smoke Suite считается успешной только если:

✓ Все проверки уровня Critical имеют статус PASS.

✓ Нет блокирующих ошибок.

✓ Все обязательные сервисы доступны.

✓ Все API отвечают корректно.

✓ Полный пользовательский сценарий завершается успешно.

✓ Release Gate имеет статус PASS.

Только после выполнения этих условий сборка может быть передана в Regression Testing или опубликована как релиз.