# Tasks: Testing Feature

**Input**: Design documents from `/specs/001-testing-feature/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/local-api.md`, `quickstart.md`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and has no dependency on incomplete tasks in the same phase
- **[Story]**: User story label for story phases only
- Every task includes an exact file path

## Phase 1: Setup

**Purpose**: Prepare the existing local web app for test-management work.

- [ ] T001 Review existing database schema patterns in `app/db.py`
- [ ] T002 Review existing service validation and result-shaping patterns in `app/services.py`
- [ ] T003 [P] Review existing route error handling patterns in `app/main.py`
- [ ] T004 [P] Review existing static UI navigation and view patterns in `static/index.html`
- [ ] T005 [P] Review existing browser API and rendering helpers in `static/app.js`

## Phase 2: Foundational

**Purpose**: Add shared persistence and service primitives required by all user stories.

**Critical**: No user story can be completed until these tasks are done.

- [ ] T006 Add `test_definitions` and `test_runs` SQLite tables with constraints in `app/db.py`
- [ ] T007 Create test-management validation constants and helper functions in `app/services.py`
- [ ] T008 Implement local default user and access-level helper behavior in `app/services.py`
- [ ] T009 Add shared row-to-dictionary conversion helpers for test definitions and runs in `app/services.py`

## Phase 3: User Story 1 - Create a Test Definition (Priority: P1)

**Goal**: A user can create a complete validation test with name, objective, input details, and expected result.

**Independent Test Criteria**: From the UI or local API, create a test with all required fields and confirm it appears in the active tests list with no run status yet; attempt creation with a missing expected result and confirm a clear validation message is returned.

- [ ] T010 [US1] Implement `create_test_definition` service behavior with required-field validation in `app/services.py`
- [ ] T011 [US1] Implement `list_test_summaries` service behavior for active tests with empty latest status support in `app/services.py`
- [ ] T012 [US1] Add `GET /api/tests` route using `list_test_summaries` in `app/main.py`
- [ ] T013 [US1] Add `POST /api/tests` route using `create_test_definition` with validation error responses in `app/main.py`
- [ ] T014 [US1] Add Testing navigation button and testing view container in `static/index.html`
- [ ] T015 [US1] Add test creation form markup with name, objective, input details, and expected result fields in `static/index.html`
- [ ] T016 [US1] Add `loadTests` and `createTestDefinition` browser functions in `static/app.js`
- [ ] T017 [US1] Render active test summaries and creation validation messages in `static/app.js`
- [ ] T018 [US1] Add styles for the testing view, test form, and summary cards in `static/styles.css`

## Phase 4: User Story 2 - Record Test Run Outcomes (Priority: P2)

**Goal**: A user can run a saved test by recording a passed, failed, or inconclusive outcome with observed evidence or explanation.

**Independent Test Criteria**: Open an existing test, record passed, failed, and inconclusive runs, and confirm each run stores status, runner, timestamp, expected-result snapshot, and observed result or blocked reason.

- [ ] T019 [US2] Implement `record_test_run` service behavior with allowed status validation in `app/services.py`
- [ ] T020 [US2] Store expected-result snapshots when creating test runs in `app/services.py`
- [ ] T021 [US2] Add `POST /api/tests/{test_id}/runs` route using `record_test_run` in `app/main.py`
- [ ] T022 [US2] Add run outcome controls for passed, failed, and inconclusive statuses in `static/index.html`
- [ ] T023 [US2] Add `recordTestRun` browser function and form validation handling in `static/app.js`
- [ ] T024 [US2] Refresh latest test summaries after recording a run in `static/app.js`
- [ ] T025 [US2] Add visual status styles for passed, failed, and inconclusive outcomes in `static/styles.css`

## Phase 5: User Story 3 - Review Latest Outcomes and History (Priority: P3)

**Goal**: A user can quickly identify each test's latest outcome and inspect historical runs in reverse chronological order.

**Independent Test Criteria**: Create multiple tests with different latest outcomes, open the testing view, confirm latest outcomes are visible without opening details, then open one test and confirm historical runs are sorted newest first.

- [ ] T026 [US3] Implement `get_test_definition` service behavior with recent run history in `app/services.py`
- [ ] T027 [US3] Implement `list_test_runs` service behavior sorted by run time and run id descending in `app/services.py`
- [ ] T028 [US3] Update `list_test_summaries` to include total, failed, and inconclusive run counts in `app/services.py`
- [ ] T029 [US3] Add `GET /api/tests/{test_id}` route using `get_test_definition` in `app/main.py`
- [ ] T030 [US3] Add `GET /api/tests/{test_id}/runs` route using `list_test_runs` in `app/main.py`
- [ ] T031 [US3] Add test detail dialog or panel markup for run history in `static/index.html`
- [ ] T032 [US3] Add `openTestDetail` and `renderTestRuns` browser functions in `static/app.js`
- [ ] T033 [US3] Render latest status, run counts, and reverse chronological history in `static/app.js`
- [ ] T034 [US3] Add styles for test history rows and latest-outcome summaries in `static/styles.css`

## Phase 6: User Story 4 - Update Tests While Preserving History (Priority: P4)

**Goal**: A user can update a test's expected result or input details without losing earlier run history.

**Independent Test Criteria**: Record a run, update the test definition, reopen history, and confirm the earlier run still displays the original expected-result snapshot while the active definition displays the new expected result.

- [ ] T035 [US4] Implement `update_test_definition` service behavior that preserves existing runs in `app/services.py`
- [ ] T036 [US4] Add archive-state handling for test definitions in `app/services.py`
- [ ] T037 [US4] Add `PUT /api/tests/{test_id}` route using `update_test_definition` in `app/main.py`
- [ ] T038 [US4] Add edit and archive controls for test definitions in `static/index.html`
- [ ] T039 [US4] Add `updateTestDefinition` browser function and validation handling in `static/app.js`
- [ ] T040 [US4] Update detail rendering to show active expected result and historical expected-result snapshots in `static/app.js`
- [ ] T041 [US4] Add styles for archived tests and edit states in `static/styles.css`

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Finish consistency, documentation, and manual validation.

- [ ] T042 Verify all testing feature routes return user-facing validation errors consistently in `app/main.py`
- [ ] T043 Verify all test-management data remains local and does not introduce external calls in `app/services.py`
- [ ] T044 Update manual validation notes after implementation in `specs/001-testing-feature/quickstart.md`
- [ ] T045 Run the existing project validation command documented in `specs/001-testing-feature/quickstart.md`
- [ ] T046 Fix any styling regressions in the testing view on desktop and narrow screens in `static/styles.css`

## Dependencies

- Phase 1 must complete before Phase 2.
- Phase 2 must complete before any user story phase.
- User Story 1 is the MVP and must complete before User Story 2 because runs require saved tests.
- User Story 2 must complete before User Story 3 can show meaningful run history, though summary display work can be prepared after Phase 2.
- User Story 4 depends on User Story 1 for editable definitions and User Story 2 for history preservation validation.
- Final Phase depends on all selected user stories.

## Parallel Execution Examples

### User Story 1

```text
Task A: T010 in app/services.py
Task B: T014 and T015 in static/index.html
Task C: T018 in static/styles.css
```

### User Story 2

```text
Task A: T019 and T020 in app/services.py
Task B: T022 in static/index.html
Task C: T025 in static/styles.css
```

### User Story 3

```text
Task A: T026, T027, and T028 in app/services.py
Task B: T031 in static/index.html
Task C: T034 in static/styles.css
```

### User Story 4

```text
Task A: T035 and T036 in app/services.py
Task B: T038 in static/index.html
Task C: T041 in static/styles.css
```

## Implementation Strategy

### MVP First

Complete Phase 1, Phase 2, and User Story 1. This produces the smallest useful increment: users can create complete test definitions and see them listed.

### Incremental Delivery

1. Add User Story 2 to record outcomes and make the feature useful for validation evidence.
2. Add User Story 3 to make latest status and run history review efficient.
3. Add User Story 4 to support ongoing test maintenance without losing evidence.
4. Complete polish tasks and quickstart validation.

### Validation Notes

- Automated test tasks were not generated because the feature request did not explicitly require TDD or automated tests.
- Manual independent test criteria are provided for each user story.
- Existing project validation should still be run after implementation using the command documented in `quickstart.md`.
