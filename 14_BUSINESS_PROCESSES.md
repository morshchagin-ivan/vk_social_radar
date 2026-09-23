> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](docs/certification/ARCHITECTURE_STATUS.md).
>
> **U03 current scope (2026-09-24):** immutable friend/follower snapshots are implemented, with frozen membership/person fields and derived adjacent-pair events. Current physical lifecycle is CREATING → COMPLETE / INCOMPLETE / FAILED; only declared COMPLETE sets become current. Collector/HTML observations remain incomplete. The broader full-corpus models/flows below remain TARGET, not current code; message_stats/AI are not snapshot-reproducible, and no Event Sourcing, automatic AI or Repository framework was added. [U03 model/flow/evidence](docs/certification/U03_IMMUTABLE_SNAPSHOT_REPORT.md).

# 14_BUSINESS_PROCESSES.md

# Business Processes

Project: VK Social Radar

Version: 1.0

---

# Overview

Документ описывает основные бизнес-процессы системы.

Каждый процесс показывает взаимодействие пользователя, Collector, Backend, Analytics и AI.

---

# BP-01. Первичная настройка системы

## Назначение

Подготовка приложения к первому запуску.

```mermaid
flowchart TD

A[Start]

B[Launch Application]

C[Check Settings]

D{Configured?}

E[Open Settings]

F[Save Settings]

G[Validate Configuration]

H[Ready]

A-->B
B-->C
C-->D
D--No-->E
E-->F
F-->G
G-->H
D--Yes-->H
```

### Комментарий

Пользователь один раз указывает настройки Collector, локальной LLM и пути хранения данных. После успешной проверки система готова к работе.

---

# BP-02. Сбор данных VK

## Назначение

Получение актуального снимка данных из VK.

```mermaid
flowchart TD

A[User]

B[Run Collector]

C[Start Browser]

D[Authenticate]

E[Collect Friends]

F[Collect Dialogs]

G[Collect Communities]

H[Normalize Data]

I[Create Snapshot]

J[Save Snapshot]

K[Finish]

A-->B
B-->C
C-->D
D-->E
E-->F
F-->G
G-->H
H-->I
I-->J
J-->K
```

### Комментарий

Collector не изменяет существующие данные. Каждый запуск формирует новый Snapshot, содержащий полное состояние социальной сети на момент сбора.

---

# BP-03. Анализ изменений

## Назначение

Выявление изменений между двумя Snapshot.

```mermaid
flowchart TD

A[Select Snapshot]

B[Load Previous Snapshot]

C[Load Current Snapshot]

D[Compare Objects]

E[Detect Changes]

F[Build Timeline]

G[Store Events]

H[Display Timeline]

A-->B
A-->C
B-->D
C-->D
D-->E
E-->F
F-->G
G-->H
```

### Комментарий

Система сравнивает два состояния данных и строит историю изменений: новые друзья, удалённые контакты, изменения профилей, активности и подписок.

---

# BP-04. Построение социального графа

## Назначение

Формирование графа связей пользователя.

```mermaid
flowchart TD

A[Load Snapshot]

B[Load Persons]

C[Calculate Relations]

D[Calculate Edge Weight]

E[Build Graph]

F[Store Graph]

G[Render Graph]

A-->B
B-->C
C-->D
D-->E
E-->F
F-->G
```

### Комментарий

Граф отражает взаимосвязи между людьми и используется как основа для аналитики и визуализации.

---

# BP-05. Расчёт аналитики

## Назначение

Вычисление производных показателей.

```mermaid
flowchart TD

A[Snapshot]

B[Relationship Engine]

C[Timeline Engine]

D[Activity Engine]

E[Statistics Engine]

F[Dashboard Model]

A-->B
A-->C
A-->D
B-->F
C-->F
D-->E
E-->F
```

### Комментарий

На основе Snapshot вычисляются рейтинги отношений, активность пользователей, статистика общения и агрегированные показатели для Dashboard.

---

# BP-06. Генерация AI Report

## Назначение

Создание аналитического отчёта средствами LLM.

```mermaid
flowchart TD

A[User]

B[Select Snapshot]

C[Prepare Context]

D[Retrieve RAG]

E[Build Prompt]

F[Local LLM]

G[Generate Report]

H[Save Report]

I[Display Report]

A-->B
B-->C
C-->D
D-->E
E-->F
F-->G
G-->H
H-->I
```

### Комментарий

AI получает только подготовленный контекст. Прямой доступ к базе данных отсутствует. Для повышения качества ответов используется RAG.

---

# BP-07. AI Chat

## Назначение

Ответы AI на вопросы пользователя.

```mermaid
flowchart TD

A[Question]

B[Retrieve Context]

C[Search Embeddings]

D[Build Prompt]

E[LLM]

F[Answer]

A-->B
B-->C
C-->D
D-->E
E-->F
```

### Комментарий

Каждый вопрос проходит через Retrieval, после чего формируется промпт для локальной языковой модели.

---

# BP-08. Поиск

## Назначение

Глобальный поиск по данным проекта.

```mermaid
flowchart TD

A[Enter Query]

B[Search Persons]

C[Search Dialogs]

D[Search Communities]

E[Merge Results]

F[Rank Results]

G[Display]

A-->B
A-->C
A-->D
B-->E
C-->E
D-->E
E-->F
F-->G
```

### Комментарий

Поиск выполняется одновременно по нескольким источникам, после чего результаты объединяются и сортируются по релевантности.

---

# BP-09. Экспорт данных

## Назначение

Экспорт данных проекта.

```mermaid
flowchart TD

A[Choose Format]

B{JSON/CSV}

C[Read Snapshot]

D[Serialize]

E[Create File]

F[Download]

A-->B
B-->C
C-->D
D-->E
E-->F
```

### Комментарий

Пользователь может выгрузить как исходные данные Snapshot, так и результаты аналитики в стандартных форматах.

---

# BP-10. Полный жизненный цикл анализа

## Назначение

Сквозной сценарий работы системы.

```mermaid
flowchart TD

A[Launch]

B[Collector]

C[Snapshot]

D[Analytics]

E[Timeline]

F[Graph]

G[AI Report]

H[AI Chat]

I[Export]

A-->B
B-->C
C-->D
D-->E
D-->F
E-->G
F-->G
G-->H
H-->I
```

### Комментарий

Этот процесс объединяет все ключевые функции VK Social Radar: сбор данных, формирование Snapshot, анализ, построение графа, генерацию AI-отчётов и экспорт результатов.

---

# Business Process Principles

Все процессы построены в соответствии со следующими принципами:

- Snapshot является единственным источником истины.
- Collector не выполняет аналитические вычисления.
- Аналитика работает только с сохранёнными Snapshot.
- AI получает данные исключительно через слой RAG.
- Все процессы являются идемпотентными и могут быть повторно выполнены без нарушения целостности данных.