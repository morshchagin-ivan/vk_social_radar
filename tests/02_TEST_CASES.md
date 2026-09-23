> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 02_TEST_CASES.md

# Functional Test Cases

Project: VK Social Radar

Version: 1.0

Status: Approved

---

# 1. Purpose

Настоящий документ содержит полный перечень функциональных тест-кейсов проекта VK Social Radar.

Каждый тест связан с:

- Specification
- Acceptance Criteria
- API
- Integration Tests
- Smoke Tests

---

# 2. Test Case Template

Каждый тест имеет структуру.

| Поле | Описание |
|------|----------|
| ID | Уникальный идентификатор |
| Requirement | Требование |
| Acceptance Criteria | Ссылка на критерий |
| Priority | Critical / High / Medium / Low |
| Preconditions | Предусловия |
| Steps | Последовательность действий |
| Expected Result | Ожидаемый результат |
| Related API | Endpoint |
| Related Module | Компонент |

---

# 3. Collector

## TC-COL-001

**Название**

Запуск Collector.

**Requirement**

Collector должен запускаться.

**Acceptance**

AC-COL-001

**Priority**

Critical

**Предусловия**

Backend работает.

Frontend открыт.

Playwright установлен.

**Шаги**

1. Открыть Dashboard.

2. Нажать Run Collector.

**Ожидаемый результат**

Collector запускается.

Отображается статус Running.

---

## TC-COL-002

Запуск Collector повторно.

Ожидается:

Повторный запуск невозможен либо корректно обработан.

---

## TC-COL-003

Collector завершает работу без ошибок.

---

## TC-COL-004

Collector корректно завершает работу после отмены.

---

## TC-COL-005

Collector восстанавливается после ошибки браузера.

---

# 4. Browser

## TC-BRW-001

Используется существующий профиль Chromium.

---

## TC-BRW-002

При отсутствии профиля выводится понятная ошибка.

---

## TC-BRW-003

Collector не уничтожает пользовательский профиль.

---

# 5. Friends

## TC-FRD-001

Получение списка друзей.

---

## TC-FRD-002

Друг без фотографии корректно импортируется.

---

## TC-FRD-003

Друг без имени корректно обрабатывается.

---

## TC-FRD-004

Большое количество друзей импортируется полностью.

---

## TC-FRD-005

Повторный импорт не создаёт дубликаты.

---

# 6. Dialogs

## TC-DLG-001

Получение списка диалогов.

---

## TC-DLG-002

Получение истории сообщений.

---

## TC-DLG-003

Пустой диалог импортируется.

---

## TC-DLG-004

Большой диалог импортируется.

---

## TC-DLG-005

Диалог с вложениями импортируется.

---

## TC-DLG-006

Unicode сохраняется.

---

## TC-DLG-007

Emoji сохраняются.

---

# 7. Communities

## TC-COM-001

Получение списка сообществ.

---

## TC-COM-002

Закрытое сообщество импортируется.

---

## TC-COM-003

Сообщество без описания импортируется.

---

# 8. Snapshot

## TC-SNP-001

Создание Snapshot.

---

## TC-SNP-002

Snapshot сохраняется.

---

## TC-SNP-003

Snapshot имеет уникальный идентификатор.

---

## TC-SNP-004

Snapshot можно открыть.

---

## TC-SNP-005

Snapshot можно удалить.

---

## TC-SNP-006

История Snapshot сохраняется.

---

# 9. Timeline

## TC-TML-001

Timeline строится после двух Snapshot.

---

## TC-TML-002

Отображаются новые друзья.

---

## TC-TML-003

Отображаются удалённые друзья.

---

## TC-TML-004

Отображаются изменения активности.

---

## TC-TML-005

Фильтрация Timeline работает.

---

# 10. Social Graph

## TC-GRP-001

Строится граф связей.

---

## TC-GRP-002

Вершины отображаются корректно.

---

## TC-GRP-003

Связи отображаются корректно.

---

## TC-GRP-004

Изолированные вершины отображаются.

---

# 11. Analytics

## TC-ANA-001

Вычисляется количество друзей.

---

## TC-ANA-002

Вычисляется количество сообщений.

---

## TC-ANA-003

Вычисляется активность.

---

## TC-ANA-004

Вычисляется статистика по периодам.

---

## TC-ANA-005

Dashboard отображает актуальные показатели.

---

# 12. AI Report

## TC-AI-001

AI Report создаётся.

---

## TC-AI-002

Используется последний Snapshot.

---

## TC-AI-003

Используется RAG.

---

## TC-AI-004

Report содержит разделы согласно Specification.

---

## TC-AI-005

Report можно пересоздать.

---

# 13. AI Chat

## TC-CHAT-001

AI отвечает на вопрос.

---

## TC-CHAT-002

Ответ использует RAG.

---

## TC-CHAT-003

Ответ связан с выбранным Snapshot.

---

## TC-CHAT-004

История сообщений сохраняется.

---

## TC-CHAT-005

Очистка истории работает.

---

# 14. Search

## TC-SRC-001

Поиск по имени пользователя.

---

## TC-SRC-002

Поиск по сообщению.

---

## TC-SRC-003

Поиск по сообществу.

---

## TC-SRC-004

Пустой результат отображается корректно.

---

# 15. Export

## TC-EXP-001

Экспорт JSON.

---

## TC-EXP-002

Экспорт CSV.

---

## TC-EXP-003

Большой Snapshot экспортируется.

---

## TC-EXP-004

Unicode экспортируется корректно.

---

# 16. Settings

## TC-SET-001

Настройки сохраняются.

---

## TC-SET-002

Настройки восстанавливаются.

---

## TC-SET-003

Изменение пути к Chromium применяется.

---

## TC-SET-004

Настройки AI применяются.

---

# 17. Error Handling

## TC-ERR-001

Backend недоступен.

---

## TC-ERR-002

SQLite повреждена.

---

## TC-ERR-003

Playwright отсутствует.

---

## TC-ERR-004

Collector завершился с ошибкой.

---

## TC-ERR-005

AI недоступен.

---

# 18. Security

## TC-SEC-001

Недопустимые параметры отклоняются.

---

## TC-SEC-002

SQL Injection невозможна.

---

## TC-SEC-003

Некорректный JSON обрабатывается.

---

## TC-SEC-004

Большой запрос не приводит к падению сервиса.

---

# 19. UI

## TC-UI-001

Dashboard открывается.

---

## TC-UI-002

Все страницы доступны.

---

## TC-UI-003

Навигация работает.

---

## TC-UI-004

Ошибки отображаются пользователю.

---

## TC-UI-005

Loader отображается при длительных операциях.

---

# 20. Regression Suite

Обязательные тесты перед каждым релизом.

- TC-COL-001
- TC-FRD-001
- TC-DLG-001
- TC-SNP-001
- TC-TML-001
- TC-GRP-001
- TC-ANA-001
- TC-AI-001
- TC-CHAT-001
- TC-EXP-001
- TC-SET-001
- TC-UI-001

---

# 21. Traceability Matrix

| Requirement | Acceptance | Test Case |
|------------|------------|-----------|
| Collector запускается | AC-COL-001 | TC-COL-001 |
| Snapshot создаётся | AC-SNP-001 | TC-SNP-001 |
| Timeline строится | AC-TML-001 | TC-TML-001 |
| AI Report создаётся | AC-AI-001 | TC-AI-001 |
| Export JSON работает | AC-EXP-001 | TC-EXP-001 |

Каждый Acceptance Criteria проекта должен иметь как минимум один соответствующий Test Case.