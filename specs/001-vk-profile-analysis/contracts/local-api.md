> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](../../../docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](../../../docs/certification/ARCHITECTURE_STATUS.md).

# Local Interface Contracts: VK Social Radar

The repository already contains a broader OpenAPI reference in `11_OPENAPI.yaml`. This contract summarizes the feature-level local interfaces that tasks should preserve or extend.

## Health and Settings

### GET `/api/v1/health`

Returns local service health.

**Success**: Service status and current timestamp are returned.

### GET `/api/v1/settings`

Returns local application settings relevant to collector, storage, and optional AI.

### PUT `/api/v1/settings`

Updates local settings without transmitting data externally.

## Collector

### POST `/api/v1/collector/run`

Starts a collector run against the configured local Chromium profile.

**Preconditions**: User has a valid local VK session.

**Success**: Returns accepted status and a collector run identifier.

**Failure**: Returns a user-facing authorization, network, DOM, or local environment error.

### GET `/api/v1/collector/status`

Returns current collector run state, counts, warnings, errors, and diagnostic references.

## Snapshots

### GET `/api/v1/snapshots`

Lists local snapshots with creation time, source run, entity counts, and integrity status.

### GET `/api/v1/snapshots/{snapshot_id}`

Returns snapshot metadata and supported local views of collected entities.

### DELETE `/api/v1/snapshots/{snapshot_id}`

Deletes a local snapshot according to user action.

### POST `/api/v1/snapshots/import`

Imports a local snapshot package.

### POST `/api/v1/snapshots/{snapshot_id}/export`

Creates a local export package for a snapshot.

## Diff and Timeline

### POST `/api/v1/diffs`

Creates or retrieves a diff between two snapshots. If snapshot IDs are omitted, compares the latest complete snapshot with the previous complete snapshot.

### GET `/api/v1/timeline`

Returns timeline entries derived from local snapshots and diffs.

## Dashboard and Analytics

### GET `/api/v1/dashboard`

Returns dashboard data derived only from the latest successful snapshot and local derived analytics.

### GET `/api/v1/relationships`

Returns relationship intelligence records and explanations derived after diff processing.

### GET `/api/v1/graph`

Returns social graph nodes, edges, and metrics for the latest snapshot-derived graph.

## AI

### POST `/api/v1/ai/reports`

Generates a local AI report from selected local sources when local LLM is available.

**Failure**: If local LLM is unavailable, returns unavailable status without affecting collector, snapshots, diff, or dashboard.

### GET `/api/v1/ai/reports`

Lists local AI reports.

### POST `/api/v1/ai/chat`

Answers a user question using only Snapshot, Diff, Timeline, and AI Report knowledge stored locally.

## Privacy Contract

All endpoints are local interfaces. Contract implementations must not send VK tokens, collected VK data, chat content, snapshots, diffs, reports, or graph data to cloud services or third parties.
