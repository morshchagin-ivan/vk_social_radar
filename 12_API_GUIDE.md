> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](docs/certification/ARCHITECTURE_STATUS.md).

# 12_API_GUIDE.md

# VK Social Radar API Guide

Version: 1.0

---

# Overview

VK Social Radar предоставляет REST API для управления процессом сбора данных, анализа социальной сети пользователя и взаимодействия с AI.

API построен по принципам REST.

Базовый URL:

```

http://localhost:8000/api/v1

```

Все запросы и ответы используют JSON.

---

# Authentication

Все методы, кроме `/health`, требуют авторизацию.

Используется Bearer Token.

```

Authorization: Bearer <token>

```

---

# Common Response Codes

| Code | Description |
|-------|-------------|
|200|Success|
|201|Created|
|202|Accepted|
|204|No Content|
|400|Bad Request|
|401|Unauthorized|
|403|Forbidden|
|404|Not Found|
|409|Conflict|
|422|Validation Error|
|500|Internal Error|

---

# Pagination

Все коллекции поддерживают пагинацию.

Параметры:

| Parameter | Default |
|------------|----------|
|page|1|
|size|50|
|sort|created_at desc|

Пример:

```

GET /persons?page=2&size=100

```

Ответ:

```json
{
  "page":2,
  "size":100,
  "total":835,
  "items":[]
}
```

---

# Filtering

Практически все методы поддерживают фильтрацию.

Пример:

```

GET /timeline?personId=UUID

```

```

GET /persons?city=Saint Petersburg

```

```

GET /relationships?minScore=0.75

```

---

# Error Format

Все ошибки имеют одинаковый формат.

```json
{
  "error":"NOT_FOUND",
  "message":"Snapshot not found",
  "details":{}
}
```

---

# Health

## GET /health

Возвращает состояние приложения.

### Response

```json
{
  "status":"ok",
  "version":"1.0.0",
  "database":"online",
  "collector":"idle",
  "ai":"ready"
}
```

---

# Settings

## GET /settings

Получить настройки приложения.

---

## PUT /settings

Обновить настройки.

### Request

```json
{
  "collector_interval":3600,
  "llm_provider":"lmstudio",
  "language":"ru"
}
```

### Response

```json
{
  "success":true
}
```

---

# Collector

## POST /collector/run

Запускает новый сбор данных.

### Request

```json
{}
```

### Response

```json
{
  "runId":"UUID",
  "status":"started"
}
```

---

## GET /collector/status

Возвращает текущий статус Collector.

### Response

```json
{
  "status":"running",
  "progress":48,
  "currentStep":"Loading dialogs"
}
```

---

# Snapshots

## GET /snapshots

Получить список Snapshot.

### Response

```json
{
  "items":[
    {
      "id":"UUID",
      "created_at":"2026-07-20T12:00:00Z"
    }
  ]
}
```

---

## GET /snapshots/{snapshotId}

Получить Snapshot.

---

## DELETE /snapshots/{snapshotId}

Удалить Snapshot.

---

# Persons

## GET /persons

Поиск пользователей.

Фильтры:

- query
- city
- country

Пример

```

GET /persons?query=Иван

```

---

## GET /persons/{personId}

Карточка пользователя.

Ответ

```json
{
  "id":"UUID",
  "vk_id":"123456",
  "name":"Иван",
  "city":"Санкт-Петербург"
}
```

---

# Dialogs

## GET /dialogs

Список диалогов.

Поддерживает:

- pagination
- sorting

---

## GET /dialogs/{dialogId}

Получить диалог.

---

# Messages

## GET /messages

Получить сообщения.

Фильтрация:

- dialogId
- senderId
- from
- to

---

# Communities

## GET /communities

Получить список групп.

---

## GET /communities/{communityId}

Информация о группе.

---

# Timeline

## GET /timeline

Получить историю изменений.

Фильтрация:

- personId
- eventType
- from
- to

Пример

```

GET /timeline?personId=UUID

```

Ответ

```json
{
  "items":[
    {
      "date":"2026-07-10",
      "type":"FriendRemoved"
    }
  ]
}
```

---

# Relationships

## GET /relationships

Получить рейтинг отношений.

Фильтрация:

- minScore
- maxScore

Ответ

```json
{
  "items":[
    {
      "person":"UUID",
      "score":0.93
    }
  ]
}
```

---

# Social Graph

## GET /graph

Получить граф связей.

Ответ

```json
{
  "nodes":[],
  "edges":[]
}
```

---

# Analytics

## GET /analytics/dashboard

Получить агрегированную аналитику.

Ответ

```json
{
  "friends":824,
  "dialogs":281,
  "communities":147
}
```

---

## GET /analytics/summary

Получить краткое описание текущего состояния.

---

# AI

## POST /ai/report/{snapshotId}

Создать AI Report.

Ответ

```json
{
  "status":"completed",
  "report":"..."
}
```

---

## POST /ai/chat

Задать вопрос AI.

Запрос

```json
{
  "question":"Кто стал менее активен за последний месяц?"
}
```

Ответ

```json
{
  "answer":"..."
}
```

---

# Search

## GET /search

Глобальный поиск.

Пример

```

GET /search?query=Алексей

```

Ответ

```json
{
  "persons":[],
  "dialogs":[],
  "communities":[]
}
```

---

# Export

## GET /export/json

Экспорт Snapshot в JSON.

---

## GET /export/csv

Экспорт таблиц в CSV.

---

## GET /export/report

Экспорт AI Report.

---

# Typical Scenarios

## Scenario 1

Первичная загрузка данных

```
POST /collector/run

↓

GET /collector/status

↓

GET /snapshots

↓

GET /snapshots/{id}
```

---

## Scenario 2

Просмотр изменений пользователя

```
GET /persons

↓

GET /persons/{id}

↓

GET /timeline?personId=id

↓

GET /relationships
```

---

## Scenario 3

Получение AI анализа

```
GET /snapshots

↓

POST /ai/report/{snapshotId}

↓

POST /ai/chat
```

---

## Scenario 4

Поиск пользователя

```
GET /search

↓

GET /persons/{id}

↓

GET /graph

↓

GET /timeline
```

---

# API Versioning

Текущая версия API:

```
/api/v1/
```

Новые несовместимые изменения публикуются как:

```
/api/v2/
```

---

# Design Principles

API разработан в соответствии с принципами:

- REST
- OpenAPI 3.1
- Stateless
- Resource-oriented
- JSON-first
- Predictable error handling
- Consistent pagination
- Uniform filtering
- Backward compatibility