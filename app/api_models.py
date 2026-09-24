"""Public response shapes; keep extension fields and existing JSON representations."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Response(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)


class APIError(Response):
    detail: str


class Health(Response):
    status: Literal["ok"]
    version: str


class RelationCounts(Response):
    current: int
    added: int
    removed: int


class Change(Response):
    id: str
    person_id: int
    event_type: str
    event_date: str
    details: str | None
    full_name: str
    profile_url: str | None
    from_snapshot_id: str | None
    to_snapshot_id: str | None
    provenance: Literal["snapshot", "legacy_unknown"]


class Person(Response):
    id: int
    vk_id: int | None
    full_name: str
    profile_url: str | None
    avatar_url: str | None
    is_deactivated: int


class PersonListItem(Person):
    incoming_count: int
    outgoing_count: int
    active_days: int
    median_reply_minutes: float | None
    is_friend: bool
    is_follower: bool
    total_messages: int


class StoredPerson(Person):
    created_at: str
    snapshot_key: str | None


class MessageStats(Response):
    id: int
    person_id: int
    period_start: str
    period_end: str
    incoming_count: int
    outgoing_count: int
    active_days: int
    initiated_by_person: int
    initiated_by_me: int
    median_reply_minutes: float | None


class LeaderboardItem(MessageStats):
    full_name: str
    profile_url: str | None
    total_messages: int
    person_initiative_pct: float


class StoredInsight(Response):
    id: int
    created_at: str
    model: str
    status: str
    confidence: float
    summary: str
    evidence_json: str
    cautions_json: str


class PersonDetail(Response):
    person: StoredPerson
    message_stats: list[MessageStats]
    events: list[Change]
    insights: list[StoredInsight]


class TopPerson(Response):
    id: int
    full_name: str
    profile_url: str | None
    incoming_count: int
    outgoing_count: int
    active_days: int
    median_reply_minutes: float | None
    total_messages: int


class ImportJob(Response):
    id: int
    filename: str
    import_type: str
    status: str
    imported_rows: int
    error_text: str | None
    created_at: str


class Dashboard(Response):
    friends: RelationCounts
    followers: RelationCounts
    message_total: int
    changes: list[Change]
    top_people: list[TopPerson]
    recent_imports: list[ImportJob]


class SnapshotResult(Response):
    snapshot_id: str
    snapshot_date: str
    captured_at: str
    relation_type: Literal["friend", "follower"]
    status: Literal["CREATING", "COMPLETE", "INCOMPLETE", "FAILED"]
    completeness: Literal["DECLARED_COMPLETE", "UNKNOWN", "PARTIAL"]
    count: int
    added: int
    removed: int


class DialogSave(Response):
    kind: Literal["dialogs"]
    saved: int
    collected_at: str


class SnapshotFileResult(SnapshotResult):
    job_id: int
    stored_as: str


class CountFileResult(Response):
    job_id: int
    stored_as: str
    imported: int
    processed_files: list[str] = Field(default_factory=list)


class ModelInfo(Response):
    id: str


class ModelTest(Response):
    ok: bool
    models_count: int
    models: list[str]


class Insight(Response):
    id: int
    model: str
    status: Literal["strengthening", "stable", "weakening", "insufficient_data"]
    confidence: float = Field(ge=0, le=1)
    summary: str
    evidence: list[str]
    cautions: list[str]


class CollectorStatus(Response):
    status: str
    authenticated: bool
    current_url: str
    last_error: str | None
    last_action: str | None
    has_preview: bool
    blocked_hosts: list[str]
    profile_dir: str
    operation_id: str
    operation_state: str
    collection_surface: str
    members_discovered: int
    members_deduped: int
    progress: dict[str, Any]
    result_available: bool


class ProfileDeleted(Response):
    ok: bool
    deleted: str


class Preview(Response):
    kind: str
    collected_at: str
    count: int
    items: list[dict[str, Any]]
    report: dict[str, Any]


class OrganizationResult(Response):
    source: str
    source_url: str
    profiles: list[dict[str, Any]]
    diagnostics: dict[str, Any]


class SourceClassification(Response):
    source_type: str
    source_url: str
    normalized_url: str
    eligible_for_collection: bool


class CollectorOperation(Response):
    """Stable job envelope; progress counters and diagnostic fields remain extensible."""
    operation_id: str
    state: str


class CollectorBusy(Response):
    status: Literal["COLLECTOR_BUSY"]
    state: Literal["COLLECTOR_BUSY"]
    operation_id: str
    current_operation: CollectorOperation


class CollectorJobResult(Response):
    operation: CollectorOperation
    result_available: bool
    result: dict[str, Any] = Field(default_factory=dict)


class Dialog(Response):
    id: int
    dialog_key: str
    peer_id: int | None
    full_name: str
    dialog_url: str | None
    preview: str | None
    date_label: str | None
    unread: int
    unread_count: int | None
    outgoing: int
    avatar_url: str | None
    verified: int
    collected_at: str
