> **Current U07 automated evidence:** 191 discoverable tests PASS via `python scripts/run_quality_gates.py`; seven mandatory gates and twelve architecture fitness invariants PASS. [Quality reference](../docs/certification/QUALITY_GATE_REFERENCE.md), [U07 report](../docs/certification/U07_QUALITY_GATES_CI_REPORT.md).
> **AUTOMATED:** temporary SQLite/migration/snapshot, fake AI/resilience, in-process API/smoke, privacy/UI helpers, architecture and governance checks.
> **MANUAL / NOT RUN:** live VK login/Chromium/LM Studio and visual UI walkthroughs. **DOCUMENTED_ONLY:** target RAG/Graph/Export/Scheduler and remaining Markdown scenarios below.
> CI workflow is CONFIGURED LOCALLY; remote Actions NOT YET VERIFIED. Branch protection NOT CONFIGURED. The historical specification below is not a claim that every target acceptance box has been implemented.

> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 01_TEST_PLAN.md

# Test Plan

**Project:** VK Social Radar

**Version:** 1.0

**Document Status:** Approved

---

# 1. Purpose

Настоящий документ определяет стратегию тестирования системы VK Social Radar.

Документ описывает:

- цели тестирования;
- область покрытия;
- уровни тестирования;
- тестовое окружение;
- критерии начала и завершения тестирования;
- требования к качеству;
- артефакты тестирования.

Документ является основой для формирования:

- Test Cases;
- API Tests;
- Integration Tests;
- Smoke Tests;
- Regression Tests;
- Acceptance Tests.

---

# 2. Objectives

Цель тестирования — подтвердить соответствие системы требованиям спецификации, архитектуры и Acceptance Criteria.

Необходимо убедиться, что:

- система корректно собирает данные;
- данные сохраняются без потерь;
- аналитика воспроизводима;
- AI использует корректный контекст;
- пользовательский интерфейс соответствует API;
- экспорт формирует корректные данные.

---

# 3. Scope

## Входит в тестирование

### Collector

- запуск браузера
- использование профиля
- сбор друзей
- сбор диалогов
- сбор сообщений
- сбор сообществ

---

### Snapshot Engine

- создание Snapshot
- сохранение Snapshot
- восстановление Snapshot
- хранение истории

---

### Backend API

Все REST endpoints.

---

### Timeline

- вычисление изменений
- отображение изменений
- фильтрация

---

### Analytics

- агрегированные показатели
- вычисление статистики
- построение графов

---

### AI

- AI Report

- AI Chat

- Prompt Builder

- RAG

---

### Export

- JSON

- CSV

---

### Frontend

- страницы

- Dashboard

- Timeline

- AI

- Export

- Settings

---

# Не входит

Настоящий этап НЕ включает:

- нагрузочное тестирование миллионов объектов;
- penetration testing;
- хакинг VK;
- тестирование внешних сервисов.

Эти проверки относятся к отдельным планам тестирования.

---

# 4. Test Levels

## Unit Testing

Проверяются отдельные классы.

Пример:

- Repository
- Services
- DTO
- Builder
- Parser

---

## Component Testing

Проверяется отдельный компонент.

Например:

Collector.

или

Timeline Engine.

---

## API Testing

Проверяются REST endpoints.

Включает:

- позитивные сценарии

- негативные сценарии

- ошибки

- валидацию

---

## Integration Testing

Проверяется взаимодействие компонентов.

Например

Collector

↓

Snapshot

↓

Repository

↓

API

↓

Frontend

---

## Smoke Testing

Минимальный набор тестов после каждой сборки.

Должен выполняться автоматически.

---

## Acceptance Testing

Проверка соответствия Acceptance Criteria.

---

# 5. Test Types

## Functional

Проверка функций системы.

---

## Regression

Проверка отсутствия регрессии.

---

## API

Проверка REST.

---

## UI

Проверка интерфейса.

---

## Database

Проверка хранения данных.

---

## AI Validation

Проверка:

- генерации отчёта;

- использования RAG;

- воспроизводимости результатов.

---

## Security

Проверка:

- валидации;

- обработки ошибок;

- отсутствия утечки данных.

---

# 6. Test Environment

## Operating System

Windows 11

Linux

---

## Backend

Python

FastAPI

SQLite

---

## Collector

Playwright

Chromium

---

## AI

LM Studio

или

Ollama

---

## Frontend

React

---

# 7. Test Data

Используются следующие наборы данных.

## Dataset A

Пустая база.

---

## Dataset B

Минимальный Snapshot.

---

## Dataset C

Типичный пользователь.

---

## Dataset D

Большой Snapshot.

---

## Dataset E

Повреждённые данные.

---

## Dataset F

Unicode

Emoji

Кириллица

Латиница

---

# 8. Entry Criteria

Тестирование начинается только после выполнения условий.

✓ Backend собирается

✓ Frontend запускается

✓ Collector запускается

✓ OpenAPI актуальна

✓ Выполнены миграции

✓ Все зависимости установлены

---

# 9. Exit Criteria

Тестирование считается завершённым при выполнении условий.

✓ Все Acceptance Criteria подтверждены

✓ Все Smoke Tests успешны

✓ Нет Critical Defect

✓ Нет Blocker

✓ Не менее 95% API проходят проверки

✓ Regression успешен

---

# 10. Defect Severity

## Critical

Система неработоспособна.

---

## High

Невозможно использовать основную функцию.

---

## Medium

Работа возможна с ограничениями.

---

## Low

Косметический дефект.

---

# 11. Deliverables

По результатам тестирования должны быть подготовлены:

- Test Cases
- API Tests
- Integration Tests
- Smoke Tests
- Test Report
- Defect Report

---

# 12. Acceptance Criteria Coverage

Каждый Acceptance Criteria обязан иметь:

- минимум один Test Case;

- минимум один Integration Test (если применимо);

- минимум один API Test (если есть endpoint);

- проверку в Regression Suite.

Acceptance Criteria без тестов не допускаются.

---

# 13. Quality Gates

Перед выпуском релиза должны быть выполнены следующие условия.

| Проверка | Требование |
|----------|------------|
| Build | PASS |
| Smoke Tests | PASS |
| API Tests | PASS |
| Integration Tests | PASS |
| Acceptance Tests | PASS |
| Regression | PASS |
| Critical Bugs | 0 |
| High Bugs | 0 |
| OpenAPI соответствует реализации | Да |
| Архитектура актуальна | Да |
| Документация обновлена | Да |

---

# 14. Traceability

Каждый артефакт проекта должен быть связан с тестами.

Specification

↓

Acceptance Criteria

↓

Test Case

↓

API Test

↓

Integration Test

↓

Smoke Test

↓

Release Checklist

Это обеспечивает полную трассируемость требований на протяжении жизненного цикла разработки.

---

# 15. Test Strategy Summary

Тестирование строится по принципу Specification Driven Development.

```
Specification
      ↓
Acceptance Criteria
      ↓
Test Cases
      ↓
API Tests
      ↓
Integration Tests
      ↓
Smoke Tests
      ↓
Implementation
      ↓
Regression
      ↓
Release
```

Разработка считается завершённой только после успешного прохождения полного набора тестов и подтверждения всех Acceptance Criteria.