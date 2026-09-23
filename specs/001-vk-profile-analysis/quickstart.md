> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](../../docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](../../docs/certification/ARCHITECTURE_STATUS.md).

# Quickstart: VK Social Radar Validation

## Prerequisites

- Windows local development environment.
- Python environment with dependencies installed from `requirements.txt`.
- Playwright browser dependencies installed for local Chromium automation.
- A Chromium profile with a user-controlled VK session for collector validation.
- Optional local LLM service available only for AI report and AI Chat scenarios.

## Setup

1. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Start the local application:

   ```powershell
   .\start.bat
   ```

3. Open the local UI and verify that the service health endpoint is available.

## Validation Scenarios

### Scenario 1: Authorization Check

1. Start a collector run with a valid Chromium VK session.
2. Expected outcome: collector status moves from running to completed or completed_with_warnings.
3. Repeat without an authorized session.
4. Expected outcome: collector stops with a clear authorization message and does not create a snapshot.

### Scenario 2: Snapshot Creation and Immutability

1. Complete a successful collector run.
2. Open the snapshot list.
3. Expected outcome: a new snapshot appears with creation time, entity counts, source run, and integrity status.
4. Reopen the snapshot after restarting the application.
5. Expected outcome: snapshot content remains available and unchanged.

### Scenario 3: Diff and Dashboard Source Isolation

1. Ensure at least two complete snapshots exist.
2. Create a diff or open the default latest-versus-previous diff view.
3. Expected outcome: added, removed, attribute_changed, and activity_changed records are distinguishable.
4. Open the dashboard while VK is unavailable or disconnected.
5. Expected outcome: dashboard still displays the latest successful snapshot and does not require live VK access.

### Scenario 4: AI Fallback

1. Disable or stop the local LLM service.
2. Run collector, snapshot list, diff, and dashboard flows.
3. Expected outcome: non-AI functions continue to work.
4. Attempt AI report or AI Chat.
5. Expected outcome: AI surfaces unavailable status and clear explanation.

### Scenario 5: Export, Import, and Deletion

1. Export a completed snapshot to a local package.
2. Import the package into the local application.
3. Expected outcome: imported snapshot is listed with valid metadata and integrity status.
4. Delete a snapshot by user action.
5. Expected outcome: the snapshot is removed from local views and no cloud transfer occurs.

### Scenario 6: OSINT Boundary

1. Run OSINT mode against a public VK profile.
2. Expected outcome: only public data is analyzed.
3. Attempt to analyze unavailable or private data.
4. Expected outcome: the system reports unavailable data and does not infer private attributes.

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

- Collector failures are logged and visible to the user.
- Successful collector runs create immutable snapshots.
- Diff, Timeline, Dashboard, Relationship Intelligence, Graph, and AI features derive from local snapshots or local derived records.
- AI features degrade gracefully when local LLM is unavailable.
- No feature requires cloud synchronization or third-party data transfer.
