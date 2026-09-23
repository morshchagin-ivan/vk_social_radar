> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](../../docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](../../docs/certification/ARCHITECTURE_STATUS.md).

# Implementation Plan: VK Social Radar

**Branch**: `001-vk-profile-analysis` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-vk-profile-analysis/spec.md`

## Summary

VK Social Radar is a local-first application for collecting VK account data, creating immutable snapshots, calculating differences between snapshots, and presenting dashboards, timelines, social graph insights, personal CRM views, and local AI-assisted analysis. The implementation extends the existing Python web application using local storage, a Playwright-based collector, a local HTTP API, and optional local LLM integration while preserving the product constraints of offline operation, privacy, and no cloud synchronization.

## Technical Context

**Language/Version**: Python 3.x, aligned with the existing application and test environment

**Primary Dependencies**: FastAPI, Uvicorn, httpx, python-multipart, Playwright; optional local LLM service already represented by the LM Studio integration module

**Storage**: Local SQLite database and local filesystem artifacts for logs, exports, diagnostics, and imported samples

**Testing**: Existing Python test suite under `tests/`, run through pytest-compatible tests and existing `run_tests.bat`

**Target Platform**: Local desktop environment on Windows with Chromium profile access

**Project Type**: Local web application with HTTP API, browser-based UI, collector service, and local persistence

**Performance Goals**: Collector must remain recoverable when VK pages change or network access fails; user-facing dashboard and report views should load from local snapshots without contacting VK

**Constraints**: Local-only operation, no cloud synchronization, no third-party data transfer, no VK write actions, no privacy bypass, no direct VK access from dashboard views, optional AI must degrade gracefully when local LLM is unavailable

**Scale/Scope**: Single-user local application; stores repeated snapshots of friends, followers, subscriptions, dialogs, communities, channels, profiles, statuses, pinned messages, unread message metadata, collector logs, diffs, timeline records, AI reports, and graph summaries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file currently contains placeholder principle names and descriptions only. No enforceable MUST or SHOULD rules are defined, so there are no constitution gates to fail for this plan. The plan still preserves the explicit product principles in the feature spec: Local First, Privacy First, Snapshot First, Explainable AI, AI Native, Extensible Architecture, and Offline by Design.

**Pre-Design Gate Status**: PASS. No constitution violations identified.

**Post-Design Gate Status**: PASS. Phase 1 artifacts keep data local, model snapshots as immutable records, document explainability fields for AI/analytics outputs, and avoid cloud or third-party transfer assumptions.

## Project Structure

### Documentation (this feature)

```text
specs/001-vk-profile-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── local-api.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── main.py          # local HTTP API and web application entrypoint
├── collector.py     # VK/Chromium collection workflows
├── db.py            # local persistence
├── services.py      # snapshot, diff, timeline, graph, analytics services
├── importers.py     # snapshot/sample import flows
├── lmstudio.py      # optional local LLM integration
└── seed.py          # local seed/sample data helpers

static/              # browser UI assets
data/                # local database, snapshots, imports, exports
logs/                # collector diagnostics and run logs
tests/               # unit, integration, smoke, and acceptance tests
```

**Structure Decision**: Use the existing single local web application layout. Feature work should add or extend modules inside `app/`, UI assets under `static/`, local data fixtures under `sample_import/` or `data/` as needed, and tests under `tests/` without creating separate frontend/backend projects.

## Complexity Tracking

No constitution violations or exceptional complexity justifications are required.
