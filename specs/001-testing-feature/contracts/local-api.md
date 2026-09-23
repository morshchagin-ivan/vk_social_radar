# Local Interface Contracts: Testing Feature

These contracts describe local application interfaces for managing validation tests and test runs.

## Tests

### GET `/api/tests`

Lists active test definitions with latest outcome summaries.

**Success**: Returns test id, name, objective, latest status, latest run time, total run count, failed run count, and inconclusive run count.

### POST `/api/tests`

Creates a new test definition.

**Required input**: name, objective, input details, expected result.

**Success**: Returns the created test definition.

**Failure**: Returns a user-facing validation message for missing or invalid required fields.

### GET `/api/tests/{test_id}`

Returns one test definition with recent run history.

**Success**: Returns definition fields and test runs in reverse chronological order.

**Failure**: Returns not found when the test does not exist or is not visible to the current user.

### PUT `/api/tests/{test_id}`

Updates editable test definition fields while preserving all existing run history.

**Editable input**: name, objective, input details, expected result, archive state.

**Success**: Returns the updated test definition.

**Failure**: Returns a user-facing validation message for missing required fields or invalid access.

## Test Runs

### POST `/api/tests/{test_id}/runs`

Records a test execution outcome.

**Required input**: status and observed result or inconclusive explanation.

**Allowed status values**: passed, failed, inconclusive.

**Success**: Returns the created test run and updated latest test summary.

**Failure**: Returns a user-facing validation message when status is invalid, required evidence is missing, or the test is not runnable.

### GET `/api/tests/{test_id}/runs`

Lists historical runs for a test in reverse chronological order.

**Success**: Returns run id, run time, runner, expected result snapshot, observed result, status, and blocked reason.

## Privacy and Locality Contract

All test definitions, inputs, expected results, observed results, and run history remain local to the application storage. Managing validation tests must not require cloud synchronization or external services.
