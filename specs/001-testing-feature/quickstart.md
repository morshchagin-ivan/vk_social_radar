# Quickstart: Testing Feature Validation

## Prerequisites

- Local development environment for the existing application.
- Dependencies installed from `requirements.txt`.
- Application can be started with the existing project startup workflow.

## Setup

1. Install dependencies if needed:

   ```powershell
   pip install -r requirements.txt
   ```

2. Start the local application:

   ```powershell
   .\start.bat
   ```

3. Open the local UI and confirm the application health endpoint responds.

## Validation Scenarios

### Scenario 1: Create a Complete Test

1. Open the testing feature view.
2. Create a test with name, objective, input details, and expected result.
3. Expected outcome: the test is saved and appears in the active tests list with no run status yet.

### Scenario 2: Required Field Validation

1. Try to save a test without an expected result.
2. Expected outcome: the test is not saved and the user sees a clear message identifying the missing field.

### Scenario 3: Record Passed and Failed Runs

1. Open an existing test.
2. Record one passed run with observed result evidence.
3. Record one failed run with observed result evidence.
4. Expected outcome: both runs appear in history, and the latest test summary reflects the most recent run.

### Scenario 4: Record an Inconclusive Run

1. Open an existing test.
2. Record an inconclusive run with an explanation of why the result could not be determined.
3. Expected outcome: the run is clearly labeled inconclusive and not confused with a failed result.

### Scenario 5: Update Test Definition Without Losing History

1. Update a test's expected result or input details.
2. Reopen the run history.
3. Expected outcome: earlier runs remain visible with their original expected-result snapshot.

### Scenario 6: Latest Outcome Summary

1. Create or use several tests with different latest outcomes.
2. Open the tests list.
3. Expected outcome: the user can identify each latest outcome without opening every test detail view.

## Test Commands

Run the existing automated test suite:

```powershell
.\run_tests.bat
```

If using pytest directly:

```powershell
pytest tests
```

## Expected Completion Criteria

- Users can create complete test definitions and receive clear validation errors for incomplete ones.
- Users can record passed, failed, and inconclusive runs.
- Latest outcomes and run history are visible and consistent.
- Updating a test definition preserves prior run history.
- All test-management data remains local.
