> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](docs/certification/ARCHITECTURE_STATUS.md).

# 09_C4_MODEL.md

# C4 Model

**Project:** VK Social Radar

---

# Level 1 — System Context

```mermaid
flowchart LR

    User["👤 User"]

    VK["VK Web Interface"]

    LLM["Local LLM
LM Studio / Ollama"]

    System["VK Social Radar"]

    User -->|Uses| System

    System -->|Reads data| VK

    System -->|Inference| LLM
```

---

# Level 2 — Container Diagram

```mermaid
flowchart LR

subgraph VKSocialRadar

UI["Frontend
React"]

API["Backend API
FastAPI"]

Collector["Collector
Playwright"]

Scheduler["Scheduler"]

Storage["Snapshot Storage
SQLite"]

Analytics["Analytics Engine"]

RAG["RAG Index"]

AI["AI Engine"]

Logs["Logging"]

end

VK["VK Web"]

LLM["Local LLM"]

UI --> API

API --> Storage

API --> Analytics

API --> AI

API --> Logs

Scheduler --> Collector

Collector --> VK

Collector --> Storage

Storage --> Analytics

Analytics --> RAG

RAG --> AI

AI --> LLM
```

---

# Level 3 — Collector Components

```mermaid
flowchart LR

Collector["Collector"]

Session["Session Validator"]

Browser["Chromium Manager"]

Driver["Playwright Driver"]

Parser["VK Parser"]

Normalizer["Normalizer"]

Snapshot["Snapshot Builder"]

Logger["Collector Logger"]

Collector --> Session

Session --> Browser

Browser --> Driver

Driver --> Parser

Parser --> Normalizer

Normalizer --> Snapshot

Snapshot --> Logger
```

---

# Level 3 — Analytics Components

```mermaid
flowchart LR

Snapshots["Snapshots"]

Diff["Diff Engine"]

Timeline["Timeline Builder"]

Relationship["Relationship Engine"]

Graph["Social Graph Builder"]

Dashboard["Dashboard Model"]

Snapshots --> Diff

Diff --> Timeline

Diff --> Relationship

Relationship --> Graph

Timeline --> Dashboard

Relationship --> Dashboard

Graph --> Dashboard
```

---

# Level 3 — AI Components

```mermaid
flowchart LR

Snapshots["Snapshots"]

Indexer["Indexer"]

Vector["RAG Index"]

Retriever["Retriever"]

Prompt["Prompt Builder"]

LLM["Local LLM"]

Reports["AI Reports"]

Chat["AI Chat"]

Snapshots --> Indexer

Indexer --> Vector

Chat --> Retriever

Retriever --> Vector

Retriever --> Prompt

Prompt --> LLM

LLM --> Reports

LLM --> Chat
```

---

# Level 3 — Storage Components

```mermaid
flowchart LR

SQLite["SQLite"]

Snapshots["Snapshots"]

Metadata["Metadata"]

Logs["Logs"]

Exports["Export Files"]

SQLite --> Snapshots

SQLite --> Metadata

SQLite --> Logs

Snapshots --> Exports
```

---

# Level 3 — Runtime Data Flow

```mermaid
flowchart LR

VK["VK"]

Collector["Collector"]

Snapshot["Snapshot"]

Diff["Diff"]

Timeline["Timeline"]

Relationship["Relationship"]

Graph["Graph"]

Dashboard["Dashboard"]

Indexer["Indexer"]

RAG["RAG"]

AI["AI"]

UI["Frontend"]

VK --> Collector

Collector --> Snapshot

Snapshot --> Diff

Diff --> Timeline

Diff --> Relationship

Relationship --> Graph

Graph --> Dashboard

Snapshot --> Indexer

Indexer --> RAG

RAG --> AI

Dashboard --> UI

AI --> UI
```

---

# Level 4 — Backend API Components

```mermaid
flowchart LR

API["FastAPI"]

SnapshotAPI["Snapshot API"]

CollectorAPI["Collector API"]

AnalyticsAPI["Analytics API"]

AIAPI["AI API"]

SettingsAPI["Settings API"]

API --> SnapshotAPI

API --> CollectorAPI

API --> AnalyticsAPI

API --> AIAPI

API --> SettingsAPI
```

---

# Level 4 — Frontend Components

```mermaid
flowchart LR

App["App"]

Dashboard["Dashboard"]

Timeline["Timeline"]

Graph["Social Graph"]

Snapshots["Snapshot Browser"]

Reports["AI Reports"]

Chat["AI Chat"]

Settings["Settings"]

App --> Dashboard

App --> Timeline

App --> Graph

App --> Snapshots

App --> Reports

App --> Chat

App --> Settings
```