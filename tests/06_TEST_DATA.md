> **Verification status: TARGET TEST SPECIFICATION / PLANNED CHECKS.**
> PASS labels, quality thresholds and acceptance boxes below describe intended checks, not completed runtime evidence.
> Verified results: [Certification audit](../docs/certification/00_REPOSITORY_AS_IS.md). Current scope: [Architecture Status](../docs/certification/ARCHITECTURE_STATUS.md).

# 06_TEST_DATA.md

# Test Data Specification

Project: VK Social Radar

Version: 1.0

Status: Approved

---

# 1. Purpose

Настоящий документ определяет стандартные наборы данных, используемые при тестировании системы VK Social Radar.

Документ обеспечивает:

- воспроизводимость результатов;
- единое тестовое окружение;
- повторяемость ошибок;
- сопоставимость результатов между разработчиками и QA.

Все тесты проекта должны использовать только утверждённые тестовые наборы данных.

---

# 2. Test Data Principles

Каждый Dataset должен быть:

- воспроизводимым;
- независимым;
- документированным;
- неизменяемым;
- пригодным для автоматического создания.

Каждый Dataset имеет собственную версию.

---

# 3. Dataset Classification

| Dataset | Назначение |
|----------|------------|
| DATA-001 | Пустая база |
| DATA-002 | Минимальный Snapshot |
| DATA-003 | Типичный пользователь |
| DATA-004 | Большой Snapshot |
| DATA-005 | История Snapshot |
| DATA-006 | Unicode |
| DATA-007 | Emoji |
| DATA-008 | Повреждённые данные |
| DATA-009 | Большие сообщения |
| DATA-010 | AI Dataset |

---

# 4. DATA-001 Empty Database

Название

Empty Database

Назначение

Проверка первого запуска.

Содержимое

SQLite

0 Snapshot

0 Person

0 Dialog

0 Message

0 Community

Используется в

- Smoke Tests
- API Tests
- Installation Tests

---

# 5. DATA-002 Minimal Snapshot

Название

Minimal Snapshot

Назначение

Минимальный рабочий набор.

Содержимое

1 Snapshot

1 Person

1 Dialog

2 Message

1 Community

Используется

- API
- Integration
- Smoke

---

# 6. DATA-003 Typical User

Название

Typical User

Назначение

Основной набор для функционального тестирования.

Содержимое

1 Snapshot

250 друзей

60 диалогов

15 сообществ

2500 сообщений

Используется

- Functional Tests
- Integration Tests
- AI Tests

---

# 7. DATA-004 Large Snapshot

Название

Large Snapshot

Назначение

Проверка производительности.

Содержимое

1 Snapshot

5000 друзей

3000 диалогов

100000 сообщений

500 сообществ

Используется

- Performance Tests
- Export
- Search
- Analytics

---

# 8. DATA-005 Snapshot History

Название

Snapshot History

Назначение

Проверка Timeline.

Содержимое

10 последовательных Snapshot.

Каждый содержит изменения:

- новые друзья;
- удалённые друзья;
- новые сообщения;
- изменение активности.

Используется

- Timeline
- Analytics
- AI

---

# 9. DATA-006 Unicode Dataset

Назначение

Проверка Unicode.

Содержимое

Кириллица

Латиница

Deutsch

Français

Español

中文

日本語

한국어

العربية

עברית

Используется

- Export
- Search
- AI

---

# 10. DATA-007 Emoji Dataset

Назначение

Проверка Emoji.

Примеры

😀

😂

👍

❤️

🎉

🚀

🤖

📈

🔥

Используется

- Search
- Export
- AI

---

# 11. DATA-008 Corrupted Dataset

Назначение

Проверка обработки ошибок.

Содержимое

Повреждённый JSON

Неверный UUID

NULL

Повреждённые ссылки

Некорректная кодировка

Используется

Negative Tests

---

# 12. DATA-009 Long Messages

Назначение

Проверка больших сообщений.

Размеры

1 KB

10 KB

100 KB

1 MB

Используется

Search

Export

AI

---

# 13. DATA-010 AI Dataset

Назначение

Проверка AI.

Содержимое

История сообщений.

История активности.

Изменения между Snapshot.

Метаданные.

Используется

AI Report

AI Chat

RAG

---

# 14. Test Profiles

Используются следующие профили.

## PROFILE-001

Новый пользователь.

---

## PROFILE-002

Активный пользователь.

---

## PROFILE-003

Неактивный пользователь.

---

## PROFILE-004

Пользователь с большим количеством сообщений.

---

## PROFILE-005

Пользователь с большим количеством друзей.

---

# 15. Database States

Используются состояния БД.

STATE-001

Пустая.

---

STATE-002

После первого запуска.

---

STATE-003

После нескольких Snapshot.

---

STATE-004

После удаления Snapshot.

---

STATE-005

Повреждённая БД.

---

# 16. AI Test Data

Используются вопросы.

## AI-Q-001

Кто мой самый активный собеседник?

---

## AI-Q-002

Какие изменения произошли после последнего Snapshot?

---

## AI-Q-003

Какие сообщества наиболее активны?

---

## AI-Q-004

Какие новые друзья появились?

---

## AI-Q-005

Какие пользователи перестали быть активными?

---

# 17. Search Dataset

Используются строки.

ASCII

Unicode

Emoji

Большие строки

Пустая строка

Пробелы

Спецсимволы

---

# 18. Export Dataset

Проверяется экспорт.

Пустая база.

---

Минимальный Snapshot.

---

Большой Snapshot.

---

Unicode.

---

Emoji.

---

# 19. Performance Dataset

Используется.

100 сообщений

1000 сообщений

10000 сообщений

100000 сообщений

1000000 сообщений

---

# 20. Security Dataset

Используются строки.

SQL Injection

```
' OR 1=1 --
```

---

XSS

```
<script>alert(1)</script>
```

---

JSON Injection

```
{}
[]
null
```

---

Большие строки

100 KB

1 MB

10 MB

---

# 21. Dataset Versioning

Каждый Dataset обязан иметь:

идентификатор;

описание;

версию;

дату изменения;

контрольную сумму (Checksum);

формат хранения.

---

# 22. Storage Structure

```
testdata/

    empty/

    minimal/

    typical/

    large/

    history/

    unicode/

    emoji/

    corrupted/

    performance/

    ai/

    security/
```

---

# 23. Traceability Matrix

| Dataset | Используется |
|-----------|-------------|
| DATA-001 | Installation, Smoke |
| DATA-002 | API, Smoke |
| DATA-003 | Functional Tests |
| DATA-004 | Performance |
| DATA-005 | Timeline |
| DATA-006 | Export |
| DATA-007 | AI |
| DATA-008 | Negative Tests |
| DATA-009 | Search |
| DATA-010 | AI Validation |

---

# 24. Dataset Lifecycle

Создание

↓

Валидация

↓

Использование

↓

Обновление

↓

Версионирование

↓

Архивирование

Никакие изменения Dataset не допускаются без обновления версии.

---

# 25. Definition of Done

Новый Dataset считается готовым только если:

✓ имеет уникальный идентификатор;

✓ документирован;

✓ воспроизводим;

✓ имеет контрольную сумму;

✓ используется хотя бы одним тестом;

✓ связан с Test Cases;

✓ связан с Acceptance Criteria;

✓ включён в Traceability Matrix.