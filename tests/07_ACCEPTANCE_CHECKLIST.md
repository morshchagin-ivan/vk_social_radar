> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 07_ACCEPTANCE_CHECKLIST.md

# Acceptance Checklist

Project: VK Social Radar

Version: 1.0

Status: Approved

---

# 1. Purpose

Настоящий документ определяет критерии приёмки проекта VK Social Radar.

Acceptance Checklist используется:

- Product Owner;
- Архитектором;
- QA Lead;
- Заказчиком.

Проект считается принятым только после выполнения всех обязательных пунктов настоящего документа.

---

# 2. Acceptance Rules

Каждый пункт имеет один из статусов.

| Статус | Значение |
|----------|----------|
| PASS | Проверка успешно пройдена |
| FAIL | Проверка не пройдена |
| N/A | Не применяется к текущему релизу |

Любой пункт со статусом FAIL блокирует приёмку соответствующего функционала.

---

# 3. Documentation

## DOC-001

Спецификация актуальна.

□ PASS

□ FAIL

---

## DOC-002

Архитектурная документация актуальна.

□ PASS

□ FAIL

---

## DOC-003

OpenAPI соответствует реализации.

□ PASS

□ FAIL

---

## DOC-004

Sequence Diagram актуальны.

□ PASS

□ FAIL

---

## DOC-005

Class Diagram актуальна.

□ PASS

□ FAIL

---

## DOC-006

Roadmap обновлена.

□ PASS

□ FAIL

---

# 4. Infrastructure

## INF-001

Backend запускается.

□ PASS

□ FAIL

---

## INF-002

Frontend запускается.

□ PASS

□ FAIL

---

## INF-003

SQLite доступна.

□ PASS

□ FAIL

---

## INF-004

Collector запускается.

□ PASS

□ FAIL

---

## INF-005

LLM Provider доступен.

□ PASS

□ FAIL

---

# 5. Collector

## COL-001

Collector успешно запускается.

□ PASS

□ FAIL

---

## COL-002

Collector успешно завершается.

□ PASS

□ FAIL

---

## COL-003

Создаётся Snapshot.

□ PASS

□ FAIL

---

## COL-004

Ошибки Collector корректно отображаются.

□ PASS

□ FAIL

---

# 6. Snapshot

## SNP-001

Snapshot сохраняется.

□ PASS

□ FAIL

---

## SNP-002

Snapshot открывается.

□ PASS

□ FAIL

---

## SNP-003

Snapshot удаляется.

□ PASS

□ FAIL

---

## SNP-004

История Snapshot сохраняется.

□ PASS

□ FAIL

---

# 7. Timeline

## TML-001

Timeline строится.

□ PASS

□ FAIL

---

## TML-002

Изменения между Snapshot отображаются.

□ PASS

□ FAIL

---

## TML-003

Фильтрация работает.

□ PASS

□ FAIL

---

# 8. Social Graph

## GRP-001

Граф строится.

□ PASS

□ FAIL

---

## GRP-002

Связи отображаются корректно.

□ PASS

□ FAIL

---

# 9. Analytics

## ANA-001

Показатели рассчитываются.

□ PASS

□ FAIL

---

## ANA-002

Dashboard отображает статистику.

□ PASS

□ FAIL

---

# 10. AI

## AI-001

AI Report создаётся.

□ PASS

□ FAIL

---

## AI-002

AI Chat отвечает.

□ PASS

□ FAIL

---

## AI-003

Используется актуальный Snapshot.

□ PASS

□ FAIL

---

## AI-004

Используется RAG.

□ PASS

□ FAIL

---

# 11. Export

## EXP-001

Экспорт JSON.

□ PASS

□ FAIL

---

## EXP-002

Экспорт CSV.

□ PASS

□ FAIL

---

# 12. Search

## SRC-001

Поиск работает.

□ PASS

□ FAIL

---

## SRC-002

Поиск по сообщениям работает.

□ PASS

□ FAIL

---

# 13. Settings

## SET-001

Настройки сохраняются.

□ PASS

□ FAIL

---

## SET-002

Настройки восстанавливаются после перезапуска.

□ PASS

□ FAIL

---

# 14. UI

## UI-001

Dashboard открывается.

□ PASS

□ FAIL

---

## UI-002

Навигация работает.

□ PASS

□ FAIL

---

## UI-003

Отсутствуют критические ошибки интерфейса.

□ PASS

□ FAIL

---

# 15. API

## API-001

Все обязательные endpoints доступны.

□ PASS

□ FAIL

---

## API-002

OpenAPI соответствует реализации.

□ PASS

□ FAIL

---

## API-003

Все API Tests проходят.

□ PASS

□ FAIL

---

# 16. Integration

## INT-001

Все Integration Tests проходят.

□ PASS

□ FAIL

---

## INT-002

Архитектурные сценарии соответствуют Sequence Diagrams.

□ PASS

□ FAIL

---

# 17. Smoke

## SMK-001

Smoke Suite проходит полностью.

□ PASS

□ FAIL

---

## SMK-002

Release Gate имеет статус PASS.

□ PASS

□ FAIL

---

# 18. Security

## SEC-001

SQL Injection отсутствует.

□ PASS

□ FAIL

---

## SEC-002

XSS корректно обрабатывается.

□ PASS

□ FAIL

---

## SEC-003

Некорректный JSON не приводит к сбою.

□ PASS

□ FAIL

---

# 19. Performance

## PRF-001

Collector соответствует требованиям по времени выполнения.

□ PASS

□ FAIL

---

## PRF-002

AI Report соответствует требованиям.

□ PASS

□ FAIL

---

## PRF-003

Export соответствует требованиям.

□ PASS

□ FAIL

---

# 20. Regression

## REG-001

Regression Suite полностью проходит.

□ PASS

□ FAIL

---

## REG-002

Нет повторно открытых дефектов.

□ PASS

□ FAIL

---

# 21. Traceability Verification

Подтверждено соответствие:

□ Specification → Acceptance Criteria

□ Acceptance Criteria → Test Cases

□ Test Cases → API Tests

□ API Tests → Integration Tests

□ Integration Tests → Smoke Tests

□ Smoke Tests → Acceptance Checklist

Все связи должны быть актуальны.

---

# 22. Release Approval

## Technical Approval

Архитектор

Имя: _______________________

Дата: _______________________

Подпись: ___________________

---

## QA Approval

QA Lead

Имя: _______________________

Дата: _______________________

Подпись: ___________________

---

## Product Approval

Product Owner

Имя: _______________________

Дата: _______________________

Подпись: ___________________

---

## Customer Approval

Заказчик

Имя: _______________________

Дата: _______________________

Подпись: ___________________

---

# 23. Release Decision

| Критерий | Статус |
|----------|--------|
| Документация | □ PASS □ FAIL |
| Архитектура | □ PASS □ FAIL |
| API | □ PASS □ FAIL |
| Integration | □ PASS □ FAIL |
| Smoke | □ PASS □ FAIL |
| Regression | □ PASS □ FAIL |
| Performance | □ PASS □ FAIL |
| Security | □ PASS □ FAIL |

---

# 24. Final Acceptance Criteria

Релиз считается принятым только при выполнении всех условий:

✓ Все обязательные Acceptance Criteria имеют статус PASS.

✓ Все Critical Test Cases успешно выполнены.

✓ Все API Tests завершены успешно.

✓ Все Integration Tests завершены успешно.

✓ Smoke Suite имеет статус PASS.

✓ Regression Suite имеет статус PASS.

✓ Нет открытых дефектов уровней Critical и High.

✓ Архитектурная документация соответствует реализации.

✓ OpenAPI полностью соответствует реализации.

✓ Release Gate имеет статус PASS.

Только после выполнения всех перечисленных условий релиз может быть передан заказчику или опубликован в Production.