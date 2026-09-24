"""OpenAPI metadata, not a second router or alternate validation layer."""
from .api_models import APIError


def errors(*codes):
    result = {400: {"model": APIError, "description": "Local Host rejected or invalid domain input."},
              403: {"model": APIError, "description": "Origin or Fetch Metadata violates the local same-origin policy."},
              500: {"description": "Unhandled server failure (safe plain text; raw exceptions suppressed).",
                    "content": {"text/plain": {"schema": {"type": "string"}}}}}
    for code in codes:
        result[code] = {"model": APIError, "description": {
            400: "Local Host rejected, domain/import/collector input or operation failure (safe detail).",
            404: "Person, preview or collector operation not found.",
            500: "Chromium startup failure (JSON); unhandled failures remain plain text.",
            503: "Provider unavailable, invalid insight/configuration or generation circuit open.",
        }[code]}
        if code == 500:
            result[code]["content"] = {"text/plain": {"schema": {"type": "string"}}}
    return result


SNAPSHOT_BODY = {
    "description": "Complete replacement declaration by default, including people: []. Domain validation returns 400, not 422. Extra fields ignored. Explicit ID replay requires identical metadata/content. UNKNOWN/PARTIAL cannot replace current truth. No snapshot read/list API is exposed.",
    "required": ["relation_type", "people"],
    "properties": {
        "relation_type": {"type": "string", "enum": ["friend", "follower"]},
        "people": {"type": "array", "items": {
            "type": "object", "required": ["full_name"], "additionalProperties": True,
            "description": "Unique numeric vk_id 1..9223372036854775807 (integer or canonical integer string), or screen_name when vk_id absent/null. Name must contain non-whitespace. Identity duplicates rejected with 400.",
            "properties": {"vk_id": {"type": ["integer", "string", "null"]},
                           "screen_name": {"description": "Coerced to string, stripped/casefolded; ASCII letters/digits/._ only."},
                           "full_name": {"type": "string", "minLength": 1},
                           "profile_url": {"description": "String when truthy; absent/falsy uses generated VK URL."},
                           "avatar_url": {"description": "String when truthy; absent/falsy becomes empty string."}}}},
        "snapshot_id": {"description": "UUID string expected; absent/falsy creates a new identity. Malformed non-string values can reach the existing unhandled 500 path."},
        "captured_at": {"description": "ISO date/time when truthy, taking precedence over snapshot_date. Naive timestamp uses application local time; precise timestamps normalize UTC."},
        "snapshot_date": {"description": "Fallback ISO capture date/time; absent/null on replay reuses existing capture, otherwise ingestion time."},
        "completeness": {"type": "string", "enum": ["DECLARED_COMPLETE", "UNKNOWN", "PARTIAL"], "default": "DECLARED_COMPLETE"},
        "status": {"description": "CREATING/COMPLETE/INCOMPLETE/FAILED when truthy. Absent/falsy selects COMPLETE for DECLARED_COMPLETE, otherwise INCOMPLETE. COMPLETE with unknown/partial is 400."},
        "source": {"type": "string", "minLength": 1, "default": "manual_import"},
        "source_reference": {"type": ["string", "null"]},
    },
}

SETTINGS_BODY = {
    "description": "Accepts a JSON object. Only three lmstudio keys are saved; unknown keys ignored. Base URL must be a parsed HTTP(S) loopback string with no userinfo/query/fragment; remote/LAN rejected 400, localhost normalized to 127.0.0.1. Model/temperature retain string conversion and no temperature bounds. No remote opt-in or retry/provider selector.",
    "properties": {"lmstudio_base_url": {"type": "string"}, "lmstudio_model": {}, "lmstudio_temperature": {}},
}

ORGANIZATION_BODY = {
    "description": "source_url is string-coerced and stripped; absent/falsy/blank is 400. options is passed through only if an object; otherwise treated as {}. Collector restrictions are business errors, not framework enums.",
    "required": ["source_url"],
    "properties": {"source_url": {}, "options": {
        "description": "Only objects are used. Synchronous collection int-coerces and clamps: max_member_index or max_profiles (default 7000, 1..20000), max_pages or max_scrolls (800, 1..2000), max_candidate_profile_enrichment (30, 0..200), max_ambiguous_profile_enrichment (10, 0..100), timeout_ms (30000, 5000..60000). Falsy values select defaults; malformed values yield 400 synchronously or job failure asynchronously. Unknown keys ignored. These are coercion rules, not framework request bounds."}},
}
