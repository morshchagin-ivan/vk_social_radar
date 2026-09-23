> **Architecture status: TARGET / EVOLUTIONARY DESIGN.**
> This document describes intended architecture and is not evidence that every component is implemented.
> Verified AS-IS: [docs/certification/C4_CURRENT.md](../../docs/certification/C4_CURRENT.md).
> Implementation status: [docs/certification/ARCHITECTURE_STATUS.md](../../docs/certification/ARCHITECTURE_STATUS.md).

# Data Model: VK Social Radar

## Entity: User Session

Represents the local user's VK authorization availability through the configured Chromium profile.

**Fields**: session_id, status, checked_at, failure_reason, chromium_profile_reference

**Relationships**: Enables Collector Run when authorized.

**Validation Rules**: A collector run cannot create a snapshot when authorization is absent or invalid. Failure must be visible to the user.

## Entity: Collector Run

Represents one attempt to collect VK data.

**Fields**: run_id, started_at, finished_at, status, requested_entities, collected_counts, error_count, warning_count, diagnostic_artifacts, log_reference

**Relationships**: May create one Snapshot on success; records Collection Error entries; feeds Dashboard update status.

**Validation Rules**: A run must record start time, final status, and errors. Partial or failed runs must not be presented as complete snapshots.

**States**: pending, running, completed, completed_with_warnings, failed, cancelled

## Entity: Snapshot

Represents an immutable point-in-time state of collected VK data.

**Fields**: snapshot_id, created_at, source_run_id, schema_version, entity_counts, collection_stats, technical_metadata, integrity_status

**Relationships**: Contains Snapshot Items for supported entity types; can be compared by Diff; can be exported, imported, viewed, deleted, and used by Dashboard.

**Validation Rules**: Once created, source content must not be mutated. Derived analytics such as relationship score, graph metrics, AI reports, and RAG indexes are stored separately.

**States**: creating, complete, imported, exported, deleted, invalid

## Entity: Snapshot Item

Represents a collected VK object within a snapshot.

**Fields**: item_id, snapshot_id, entity_type, vk_identifier, display_name, attributes, collected_at, visibility_status

**Relationships**: Belongs to Snapshot; may correspond to Person, Dialog, Message, Community, Channel, Profile, Status, Pinned Message, or Unread Marker views.

**Validation Rules**: Must preserve entity type and snapshot association. Missing or inaccessible attributes must be marked rather than guessed.

## Entity: Person

Represents a VK user profile visible to the collector or OSINT mode.

**Fields**: person_id, vk_identifier, display_name, profile_url, avatar_reference, profile_attributes, visibility_status

**Relationships**: Appears in snapshots as friend, follower, subscription target, dialog participant, or graph node.

**Validation Rules**: Private third-party data must not be inferred or collected in OSINT mode.

## Entity: Dialog

Represents a visible VK conversation summary.

**Fields**: dialog_id, vk_identifier, title, participant_refs, last_activity_at, unread_count, pinned_message_ref, attributes

**Relationships**: Belongs to Snapshot; contains or references Message summaries; contributes to Timeline and Relationship Intelligence.

**Validation Rules**: Unavailable message content must be distinguished from absence of messages.

## Entity: Message

Represents visible message metadata or content collected from dialogs when supported.

**Fields**: message_id, dialog_id, sender_ref, sent_at, content_excerpt_or_text, attachment_summary, visibility_status

**Relationships**: Belongs to Dialog and Snapshot; contributes to activity, timeline, search, RAG, and AI analysis.

**Validation Rules**: Stored content must remain local and must not be sent to cloud services.

## Entity: Community

Represents a VK group, channel, or community relation.

**Fields**: community_id, vk_identifier, title, community_type, membership_status, profile_url, attributes

**Relationships**: Belongs to Snapshot; contributes to social graph and dashboard summaries.

## Entity: Diff

Represents calculated changes between two snapshots.

**Fields**: diff_id, base_snapshot_id, target_snapshot_id, created_at, change_counts, summary

**Relationships**: Contains Change Events; feeds Timeline, AI Pipeline, Dashboard, and Relationship Intelligence.

**Validation Rules**: If no snapshots are explicitly selected, the latest and previous snapshots are used. Both snapshots must be complete and comparable.

## Entity: Change Event

Represents one detected change between snapshots.

**Fields**: change_id, diff_id, entity_type, entity_ref, change_type, previous_value, current_value, detected_at

**Relationships**: Belongs to Diff; contributes to Timeline and reports.

**Validation Rules**: Change types must distinguish added, removed, attribute_changed, and activity_changed.

## Entity: Timeline Entry

Represents historical activity or relationship events for a contact or entity.

**Fields**: timeline_entry_id, subject_ref, event_type, event_at, source_snapshot_id, source_diff_id, description

**Relationships**: Derived from Snapshots and Diffs; displayed in Timeline and Life Replay.

## Entity: Relationship Insight

Represents derived relationship analysis for a contact.

**Fields**: insight_id, person_ref, source_diff_id, score_value, score_version, explanation, evidence_refs, created_at

**Relationships**: Derived after Diff; shown in Relationship Intelligence and Personal CRM.

**Validation Rules**: Score formula is deferred to a later specification; insight must identify algorithm version and evidence.

## Entity: Graph Model

Represents a derived social graph for the latest snapshot.

**Fields**: graph_id, source_snapshot_id, graph_type, created_at, metrics_summary

**Relationships**: Contains Graph Nodes and Graph Edges; powers Social Graph views.

**Validation Rules**: Graph type is deferred to architecture specification and must be recorded when calculated.

## Entity: AI Report

Represents local AI-generated analysis.

**Fields**: report_id, source_snapshot_id, source_diff_id, report_type, prompt_context_summary, generated_at, status, content, limitations, evidence_refs

**Relationships**: Uses Snapshot, Diff, Timeline, and local RAG index; visible in reports and AI Chat knowledge sources.

**Validation Rules**: Must be generated only through local AI. If the local LLM is unavailable, status must reflect unavailable without blocking non-AI features.

## Entity: RAG Index

Represents a local retrieval index built from local data.

**Fields**: index_id, source_snapshot_ids, source_diff_ids, created_at, status, item_count

**Relationships**: Supports AI Chat and AI Report generation.

**Validation Rules**: Must not include external internet content. Must be rebuilt or marked stale after new snapshot/diff data.

## Entity: AI Chat Session

Represents a local chat over stored VK Social Radar knowledge.

**Fields**: chat_id, created_at, last_message_at, status, source_scope

**Relationships**: Contains AI Chat Messages; queries local RAG Index and AI Reports only.

**Validation Rules**: Internet queries are not allowed.

## Entity: Personal CRM Item

Represents a user-facing relationship management record.

**Fields**: crm_item_id, person_ref, vip_status, reminder_at, reminder_text, inactive_since, notes, status

**Relationships**: Derived from or linked to Person, Timeline Entry, Dialog, and Relationship Insight.

## Entity: Export Package

Represents a local export of snapshots or reports.

**Fields**: export_id, created_at, included_snapshot_ids, included_report_ids, format, file_reference, integrity_status

**Relationships**: Created from Snapshots and Reports; can be imported as Snapshot or historical package.

**Validation Rules**: Export must be local and must not trigger cloud transfer.
