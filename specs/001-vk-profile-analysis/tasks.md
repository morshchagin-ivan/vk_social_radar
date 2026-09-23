> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](../../docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](../../docs/certification/ARCHITECTURE_STATUS.md).

# Tasks: VK Social Radar

**Input**: Design documents from `/specs/001-vk-profile-analysis/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/local-api.md, quickstart.md

**Tests**: No separate test-first tasks are generated because the feature request does not explicitly require TDD. Validation is captured through independent test criteria and final quickstart execution.

**Organization**: Tasks are grouped by independently testable user story increments derived from the current spec's functional requirements and user flows.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the existing local Python/FastAPI application for snapshot-centered feature work.

- [ ] T001 Review existing API routes and align endpoint naming gaps with specs/001-vk-profile-analysis/contracts/local-api.md
- [ ] T002 [P] Document local environment prerequisites and Playwright setup updates in README.md
- [ ] T003 [P] Add feature validation notes from specs/001-vk-profile-analysis/quickstart.md to tests/07_ACCEPTANCE_CHECKLIST.md
- [ ] T004 Add application version and feature scope constants for VK Social Radar in app/main.py
- [ ] T005 Verify local data, import, backup, collector preview, and collector log directories are initialized in app/db.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core persistence, error, and privacy foundations that must exist before user-story work.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Extend SQLite schema for collector_runs, snapshots, snapshot_items, diffs, change_events, timeline_entries, relationship_insights, graph_models, rag_indexes, ai_reports, ai_chat_sessions, personal_crm_items, and export_packages in app/db.py
- [ ] T007 Add schema migration safety and idempotent upgrade checks for new tables in app/db.py
- [ ] T008 Create shared serialization helpers for JSON fields, timestamps, and integrity status values in app/services.py
- [ ] T009 Create shared user-facing error response helpers for authorization, unavailable VK data, network failure, DOM change, and local storage errors in app/main.py
- [ ] T010 Add local-only privacy guard helpers that reject cloud URLs and external data transfer settings in app/services.py
- [ ] T011 Add collector run persistence helpers for start, completion, warning, failure, diagnostic artifacts, and collected counts in app/services.py
- [ ] T012 Add local API route aliases under /api/v1 for health and settings while preserving existing /api routes in app/main.py

**Checkpoint**: Foundation ready; user story implementation can now begin.

---

## Phase 3: User Story 1 - Collect VK Data and Create Snapshot (Priority: P1) MVP

**Goal**: User can validate VK authorization, collect supported VK entities, and save an immutable local snapshot with run logs and diagnostics.

**Independent Test**: Start the local app, check authorization, collect friends/followers/dialogs through the collector, save the result, and confirm a complete snapshot appears in the local snapshot list with source run, entity counts, timestamp, and diagnostics.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Extend CollectorState with run_id, requested_entities, collected_counts, warning_count, diagnostic_artifacts, and failure_reason fields in app/collector.py
- [ ] T014 [US1] Persist collector run start and status transitions from collector.start, collector.check_auth, and collector.collect in app/collector.py
- [ ] T015 [US1] Expand collector collection orchestration to support friends, followers, subscriptions, dialogs, communities, channels, profiles, statuses, pinned messages, and unread message metadata placeholders in app/collector.py
- [ ] T016 [US1] Normalize collector preview items into snapshot item records with entity_type, vk_identifier, attributes, visibility_status, and collected_at in app/services.py
- [ ] T017 [US1] Implement immutable snapshot creation from successful collector runs with source_run_id, schema_version, entity_counts, collection_stats, and technical_metadata in app/services.py
- [ ] T018 [US1] Reject snapshot creation for unauthorized, empty, failed, or partial collector runs with clear user-facing messages in app/services.py
- [ ] T019 [US1] Add snapshot list and snapshot detail service functions returning metadata and supported entity views in app/services.py
- [ ] T020 [US1] Add /api/v1/collector/run, /api/v1/collector/status, /api/v1/snapshots, and /api/v1/snapshots/{snapshot_id} routes in app/main.py
- [ ] T021 [US1] Update the collector controls and snapshot list UI in static/app.js
- [ ] T022 [US1] Add snapshot and collector status sections to static/index.html
- [ ] T023 [US1] Ensure collector diagnostics and preview files are linked from collector run results without exposing non-local paths in app/collector.py

**Checkpoint**: User Story 1 is fully functional and independently testable as the MVP.

---

## Phase 4: User Story 2 - Compare Snapshots and View Dashboard Analytics (Priority: P2)

**Goal**: User can compare snapshots, view changes, timeline events, dashboard metrics, relationship insights, and a derived social graph without live VK access.

**Independent Test**: With two complete snapshots present, create a diff, verify added/removed/attribute/activity changes, disconnect VK, and confirm dashboard, timeline, relationship, and graph views load from local snapshot-derived data only.

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement snapshot comparison helpers for added, removed, attribute_changed, and activity_changed records in app/services.py
- [ ] T025 [US2] Persist diff records and change_events for selected snapshots or latest-versus-previous snapshots in app/services.py
- [ ] T026 [US2] Generate timeline_entries from snapshots and change_events for contact appearance, communication start, activity peaks, inactivity periods, and profile changes in app/services.py
- [ ] T027 [US2] Generate relationship_insights with score_version, explanation, and evidence_refs after diff processing in app/services.py
- [ ] T028 [US2] Generate graph_models with nodes, edges, centrality, clusters, communities, and bridges derived from the latest snapshot in app/services.py
- [ ] T029 [US2] Refactor dashboard service to read only the latest successful snapshot and derived local records in app/services.py
- [ ] T030 [US2] Add /api/v1/diffs, /api/v1/timeline, /api/v1/dashboard, /api/v1/relationships, and /api/v1/graph routes in app/main.py
- [ ] T031 [US2] Update dashboard, changes, timeline, relationships, and graph rendering in static/app.js
- [ ] T032 [US2] Add dashboard analytics, timeline, relationship, and graph containers to static/index.html

**Checkpoint**: User Story 2 works independently after foundational data and at least two snapshots exist.

---

## Phase 5: User Story 3 - Run Local AI Reports and AI Chat (Priority: P3)

**Goal**: User can generate local AI reports and ask AI Chat questions over local Snapshot, Diff, Timeline, and AI Report knowledge, while non-AI features continue when the local LLM is unavailable.

**Independent Test**: With a completed snapshot and diff, generate an AI report when LM Studio is available, ask a chat question, then stop LM Studio and confirm collector, snapshots, diff, and dashboard still work while AI returns unavailable status.

### Implementation for User Story 3

- [ ] T033 [P] [US3] Add RAG index metadata creation, stale marking, and source_scope tracking for snapshots and diffs in app/services.py
- [ ] T034 [US3] Build local report context from Snapshot, Diff, Timeline, and Relationship Insight records without internet sources in app/services.py
- [ ] T035 [US3] Extend local LLM report generation to persist ai_reports with status, content, limitations, and evidence_refs in app/lmstudio.py
- [ ] T036 [US3] Implement AI unavailable fallback that records unavailable status without blocking non-AI workflows in app/lmstudio.py
- [ ] T037 [US3] Implement AI Chat sessions and messages using only local RAG index and AI reports in app/services.py
- [ ] T038 [US3] Add /api/v1/ai/reports GET, /api/v1/ai/reports POST, and /api/v1/ai/chat POST routes in app/main.py
- [ ] T039 [US3] Update AI report and AI Chat UI flows in static/app.js
- [ ] T040 [US3] Add AI report list, report generation, and AI Chat containers to static/index.html

**Checkpoint**: User Story 3 works independently with local data and degrades gracefully without local LLM availability.

---

## Phase 6: User Story 4 - Manage Personal CRM and OSINT Boundary (Priority: P4)

**Goal**: User can manage VIP contacts, reminders, inactive contacts, relationship history, and public-data-only OSINT analysis without collecting private third-party data.

**Independent Test**: Mark a contact as VIP, create a reminder, view inactive contacts and relationship history, run OSINT mode against public data, and confirm private or unavailable third-party data is reported as unavailable rather than inferred.

### Implementation for User Story 4

- [ ] T041 [P] [US4] Implement personal_crm_items service functions for VIP status, reminders, notes, inactive_since, and status in app/services.py
- [ ] T042 [US4] Add inactive contact detection derived from timeline_entries, dialogs, and relationship_insights in app/services.py
- [ ] T043 [US4] Implement OSINT input validation and public-data-only visibility checks in app/collector.py
- [ ] T044 [US4] Add OSINT result persistence as snapshot_items with visibility_status and limitation notes in app/services.py
- [ ] T045 [US4] Add /api/v1/crm, /api/v1/crm/{person_id}, and /api/v1/osint/profile routes in app/main.py
- [ ] T046 [US4] Update Personal CRM and OSINT UI flows in static/app.js
- [ ] T047 [US4] Add Personal CRM, reminders, inactive contacts, and OSINT containers to static/index.html

**Checkpoint**: User Story 4 works independently after people, timeline, and snapshot data are available.

---

## Phase 7: User Story 5 - Export, Import, and Delete Local Data (Priority: P5)

**Goal**: User can export snapshots and reports, import local packages, delete snapshots, and verify all operations remain local.

**Independent Test**: Export a completed snapshot, import the package, reopen imported metadata, delete a snapshot, and confirm no cloud transfer or external destination is used.

### Implementation for User Story 5

- [ ] T048 [P] [US5] Implement export_package creation with included_snapshot_ids, included_report_ids, format, file_reference, and integrity_status in app/services.py
- [ ] T049 [US5] Extend import_uploaded_file to import snapshot packages and preserve imported metadata in app/importers.py
- [ ] T050 [US5] Implement snapshot deletion that removes local snapshot-derived records or marks them deleted consistently in app/services.py
- [ ] T051 [US5] Enforce local-only file destinations for export and import operations in app/services.py
- [ ] T052 [US5] Add /api/v1/snapshots/{snapshot_id}/export, /api/v1/snapshots/import, and DELETE /api/v1/snapshots/{snapshot_id} routes in app/main.py
- [ ] T053 [US5] Update export, import, and delete interactions in static/app.js
- [ ] T054 [US5] Add export/import/delete controls and status messages to static/index.html

**Checkpoint**: User Story 5 works independently with existing local snapshots and reports.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T055 [P] Update 11_OPENAPI.yaml with all /api/v1 routes from specs/001-vk-profile-analysis/contracts/local-api.md
- [ ] T056 [P] Update 12_API_GUIDE.md with local-only privacy and AI fallback behavior
- [ ] T057 [P] Update 17_IMPLEMENTATION_PLAN.md with completed story increments and remaining deferred open issues
- [ ] T058 Add user-facing limitation text for deferred Relationship Score formula, Social Health Index formula, graph model type, RAG architecture, performance SLA, and snapshot versioning in static/app.js
- [ ] T059 Review all endpoints to ensure Dashboard, Timeline, Graph, AI, CRM, export, and import never call VK directly in app/main.py
- [ ] T060 Run quickstart validation scenarios from specs/001-vk-profile-analysis/quickstart.md
- [ ] T061 Run the existing automated test suite with run_tests.bat
- [ ] T062 Record validation results and known limitations in specs/001-vk-profile-analysis/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion.
- **Polish (Final Phase)**: Depends on the selected user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; MVP and required for all snapshot-derived stories.
- **US2 (P2)**: Depends on US1 data, but is independently testable with any two complete snapshots.
- **US3 (P3)**: Depends on US1 local data and benefits from US2 diffs/timeline; non-AI features must remain independent.
- **US4 (P4)**: Depends on US1 people/snapshot data and benefits from US2 timeline/relationship records.
- **US5 (P5)**: Depends on US1 snapshots and optionally US3 reports.

### Within Each User Story

- Data model and persistence helpers before services.
- Services before API routes.
- API routes before UI wiring.
- Core story validation before moving to the next priority.

### Parallel Opportunities

- Setup documentation tasks T002 and T003 can run in parallel.
- US1 state/data normalization tasks T013 and T016 can run in parallel after foundational tasks.
- US2 comparison task T024 can start while UI tasks wait for API routes.
- US3 RAG metadata task T033 can run in parallel with AI context design once local persistence exists.
- US4 CRM task T041 can run in parallel with OSINT validation task T043.
- US5 export task T048 can run in parallel with import extension task T049.
- Polish documentation tasks T055, T056, and T057 can run in parallel.

---

## Parallel Example: User Story 1

```text
Task: "T013 [P] [US1] Extend CollectorState with run_id, requested_entities, collected_counts, warning_count, diagnostic_artifacts, and failure_reason fields in app/collector.py"
Task: "T016 [US1] Normalize collector preview items into snapshot item records with entity_type, vk_identifier, attributes, visibility_status, and collected_at in app/services.py"
```

## Parallel Example: User Story 2

```text
Task: "T024 [P] [US2] Implement snapshot comparison helpers for added, removed, attribute_changed, and activity_changed records in app/services.py"
Task: "T032 [US2] Add dashboard analytics, timeline, relationship, and graph containers to static/index.html"
```

## Parallel Example: User Story 3

```text
Task: "T033 [P] [US3] Add RAG index metadata creation, stale marking, and source_scope tracking for snapshots and diffs in app/services.py"
Task: "T040 [US3] Add AI report list, report generation, and AI Chat containers to static/index.html"
```

## Parallel Example: User Story 4

```text
Task: "T041 [P] [US4] Implement personal_crm_items service functions for VIP status, reminders, notes, inactive_since, and status in app/services.py"
Task: "T043 [US4] Implement OSINT input validation and public-data-only visibility checks in app/collector.py"
```

## Parallel Example: User Story 5

```text
Task: "T048 [P] [US5] Implement export_package creation with included_snapshot_ids, included_report_ids, format, file_reference, and integrity_status in app/services.py"
Task: "T049 [US5] Extend import_uploaded_file to import snapshot packages and preserve imported metadata in app/importers.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate collector authorization, collection, snapshot creation, snapshot immutability, and snapshot listing.
5. Demo the local collector-to-snapshot workflow before adding analytics or AI.

### Incremental Delivery

1. Deliver US1 for local collection and immutable snapshots.
2. Deliver US2 for diff, timeline, dashboard, relationships, and graph from local data.
3. Deliver US3 for optional local AI report/chat with graceful fallback.
4. Deliver US4 for Personal CRM and OSINT boundary handling.
5. Deliver US5 for export, import, and deletion.

### Notes

- [P] tasks touch different files or can be started without waiting for incomplete same-file changes.
- [US] labels map tasks to independently testable story increments.
- Preserve existing endpoints while adding /api/v1 route aliases required by the feature contract.
- Do not add cloud synchronization, external analytics, VK write actions, or privacy-bypassing behavior.
