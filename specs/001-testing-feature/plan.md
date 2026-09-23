# Implementation Plan: Testing Feature

**Branch**: Not created by this command | **Date**: 2026-07-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-testing-feature/spec.md`

## Summary

The testing feature adds a local, user-facing capability for authorized product team users to define validation tests, run them, record passed/failed/inconclusive outcomes, and review historical results. The implementation should extend the existing local web application with persistent test definitions, run history, summary views, and clear validation/error feedback while preserving local-only storage and role-appropriate access boundaries.

## Technical Context

**Language/Version**: Python 3.x and browser-based JavaScript, aligned with the existing application.

**Primary Dependencies**: Existing FastAPI application, SQLite persistence, static HTML/CSS/JavaScript UI, and current Python test tooling.

**Storage**: Local SQLite database managed through `app/db.py`.

**Testing**: Existing Python tests under `tests/`, run through `run_tests.bat` or pytest-compatible commands.

**Target Platform**: Local desktop web application environment already used by VK Social Radar.

**Project Type**: Single local web application with HTTP API, static UI assets, services, and local persistence.

**Performance Goals**: Users can create a test in under 2 minutes, see completed run status within 10 seconds, and identify latest outcomes in under 15 seconds.

**Constraints**: Keep all test definitions and run history local; do not introduce cloud synchronization; preserve existing app structure; do not require live VK access for managing validation tests.

**Scale/Scope**: Single-user or small-team local usage with test definitions, run records, latest status summaries, and historical run views.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No `.specify/memory/constitution.md` file exists in this workspace, so there are no configured constitution principles to validate. The plan still preserves the existing product direction visible in prior specs and application copy: local-first storage, privacy-conscious operation, and no unnecessary external data transfer.

**Pre-Design Gate Status**: PASS. No constitution file or enforceable gates found.

**Post-Design Gate Status**: PASS. Phase 1 artifacts keep the feature local, model persistent test evidence, and avoid external service dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-feature/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── local-api.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
app/
├── main.py          # local HTTP API and web application entrypoint
├── db.py            # local SQLite schema and connections
├── services.py      # application service functions and persistence operations
└── ...              # existing collector, importer, seed, and AI modules

static/
├── index.html       # browser UI structure
├── app.js           # browser UI behavior and API calls
└── styles.css       # visual styling

tests/               # unit, integration, smoke, and acceptance tests
```

**Structure Decision**: Use the existing single-app layout. Add test-management persistence in `app/db.py`, service behavior in `app/services.py` or a small focused service module if the file becomes hard to maintain, local API routes in `app/main.py`, UI additions under `static/`, and regression tests under `tests/`.

## Phase 0: Research

Research outcomes are captured in [research.md](./research.md).

Key decisions:

- Model tests and test runs as separate persistent entities so changing a test does not erase prior evidence.
- Support manual outcome recording rather than assuming full automation.
- Treat inconclusive as a first-class result distinct from failed.
- Provide latest-outcome summaries plus full history for each test.
- Keep access boundaries simple and local, matching the existing app context.

## Phase 1: Design

Design artifacts:

- Data model: [data-model.md](./data-model.md)
- Local API contract: [contracts/local-api.md](./contracts/local-api.md)
- Validation quickstart: [quickstart.md](./quickstart.md)

Design result:

- Add `TestDefinition` records for reusable validation scenarios.
- Add `TestRun` records for each execution and outcome.
- Add a latest-status list view and detail history view.
- Preserve historical runs when a definition changes.
- Enforce required fields and status values at both service and persistence boundaries.

## Phase 2: Task Planning Approach

The `/specify.tasks` phase should generate tasks in this order:

1. Persistence schema for test definitions and test runs.
2. Service functions for create, update, run/record outcome, list latest statuses, and list history.
3. Local API routes and validation responses.
4. Static UI navigation, forms, summary list, detail/history view, and result messaging.
5. Tests covering validation failures, status handling, history preservation, and latest outcome summaries.
6. Quickstart/manual validation pass.

## Complexity Tracking

No constitution violations or exceptional complexity justifications are required.
