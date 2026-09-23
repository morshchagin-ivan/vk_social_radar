> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](../../docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](../../docs/certification/ARCHITECTURE_STATUS.md).

# Phase 0 Research: VK Social Radar

## Decision: Keep a local-only architecture

**Rationale**: The specification explicitly requires all user data to remain on the user's computer, with no cloud synchronization or third-party transfer. A local application with local persistence and local processing satisfies privacy, offline operation, and user-control goals.

**Alternatives considered**: Cloud-hosted analytics, remote worker collection, and hosted LLM processing were rejected because they conflict with Local First and Privacy First product principles.

## Decision: Use immutable snapshots as the source of analytical truth

**Rationale**: The spec defines Snapshot as an immutable state record and requires Dashboard, Diff, Timeline, Relationship Intelligence, Social Graph, and AI analysis to derive from snapshots rather than live VK reads. This gives repeatable analysis, export/import capability, and recoverability when VK changes.

**Alternatives considered**: Querying VK live for every dashboard view was rejected because it breaks offline behavior and makes reports non-repeatable. Mutable snapshot updates were rejected because they weaken auditability and historical comparison.

## Decision: Treat Collector output as auditable collection runs

**Rationale**: The collector must validate authorization, collect supported entities, log errors, and create execution journals. Persisting run status and diagnostics supports troubleshooting when VK DOM, authorization, or network behavior changes.

**Alternatives considered**: Silent background collection was rejected because users need clear failure states and because VK page structure changes are an explicit technical risk.

## Decision: Store AI outputs separately from snapshots

**Rationale**: The spec states Relationship Score, AI analysis, and graph are computed separately and are not stored inside Snapshot. This allows re-running analytical models without rewriting historical source data.

**Alternatives considered**: Embedding scores and reports inside snapshots was rejected because it would mix immutable source state with derived, version-sensitive analytics.

## Decision: Degrade gracefully when local LLM is unavailable

**Rationale**: Alternative flow AF-3 requires Collector and non-AI features to continue when LM Studio is unavailable. AI reports and chat should be marked unavailable while snapshots, diffs, dashboard, exports, and imports continue.

**Alternatives considered**: Blocking all workflows on LLM availability was rejected because AI is optional for core snapshot and dashboard value.

## Decision: Expose local HTTP contracts for app/UI interactions

**Rationale**: The repository already includes an OpenAPI document and FastAPI dependency. Documenting local API contracts makes the feature testable and keeps UI, tests, and services aligned.

**Alternatives considered**: UI-only behavior without contracts was rejected because task generation and validation need stable interfaces for collector, snapshot, diff, graph, AI, and export flows.

## Decision: Limit OSINT mode to public data only

**Rationale**: FR-11 states OSINT is separate and uses only open data. This avoids conflating a user's authorized account data with third-party private data and preserves the privacy boundary.

**Alternatives considered**: Broad third-party data aggregation was rejected because it conflicts with explicit privacy and scope boundaries.

## Decision: Use existing test assets and add scenario-oriented tests

**Rationale**: The repository already contains acceptance, integration, smoke, and service tests. New work should expand these around collector errors, snapshot immutability, diff correctness, dashboard source isolation, AI fallback, and deletion/export/import paths.

**Alternatives considered**: Replacing the test setup was rejected because existing tests already represent current behavior and regression risk.
