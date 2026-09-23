# Data Model: Testing Feature

## Entity: Test Definition

Represents a reusable validation scenario created by a user.

**Fields**: test_id, name, objective, input_details, expected_result, access_level, created_by, created_at, updated_at, archived_at

**Relationships**: Has many Test Runs. Latest status is derived from the most recent Test Run.

**Validation Rules**: Name, objective, input details, and expected result are required. Archived tests remain visible in history but should not be shown as active by default.

**States**: active, archived

## Entity: Test Run

Represents one recorded execution of a Test Definition.

**Fields**: run_id, test_id, run_by, run_at, expected_result_snapshot, observed_result, status, blocked_reason

**Relationships**: Belongs to one Test Definition.

**Validation Rules**: Status must be passed, failed, or inconclusive. Observed result is required for passed and failed outcomes. Blocked or missing evidence should be recorded as inconclusive with an explanation.

**States**: passed, failed, inconclusive

## Entity: User

Represents the person creating, running, or reviewing tests within the local application context.

**Fields**: user_id, display_name, access_level

**Relationships**: May create Test Definitions and Test Runs.

**Validation Rules**: Access level must allow the requested create, run, update, or view action. If no explicit account system exists, the local default user represents the current operator.

## Derived View: Test Summary

Represents the list view used to quickly identify each test's latest outcome.

**Fields**: test_id, name, objective, latest_status, latest_run_at, latest_run_by, total_runs, failed_runs, inconclusive_runs

**Relationships**: Derived from Test Definition and Test Run.

**Validation Rules**: Latest status must reflect the most recent run by run time, with deterministic tie-breaking by run identifier.
