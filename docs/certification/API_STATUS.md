# API Status

Baseline 1.0 · 2026-09-23. **Runtime unchanged. Contract consistency remains FAIL.**

| Aspect | CURRENT | TARGET proposal |
|---|---|---|
| Base | `http://127.0.0.1:8765/api` | `/api/v1`; legacy YAML also names port 8000/HTTPS |
| Version | app 0.4.2 | YAML API 1.0.0 |
| Operations | 29 `/api/*` operations | 18 YAML operations |
| Contract source | [main.py](../../app/main.py) decorators and FastAPI generated schema | [11_OPENAPI.yaml](../../11_OPENAPI.yaml), marked TARGET CONTRACT |
| Security | no bearer validation | global BearerAuth in YAML; policy requires U04/U06 decision |
| Schemas | generic dict/list annotations, limited validation | largely empty object schemas; not a finished contract |

Prior audit generated OpenAPI 3.1.0 without startup. Exact prefix agreement: none; after normalization only GET health, GET/PUT settings, GET collector/status coincide. There are 25 normalized runtime-only operations and 14 missing target operations. Root `/`/framework documentation/static routes are excluded from the 29 count.

Current examples: `/api/people`, `/api/changes`, `/api/dashboard`, `/api/import/file`, `/api/collector/collect/{kind}`, `/api/people/{person_id}/insight`. Target examples without current implementation: snapshots resource, `/ai/chat`, `/graph`, export. Person insight is not snapshot AI Report. `/collector/start` opens the browser, not a full `/collector/run` snapshot workflow.

Mismatches include `/persons` vs `/people`, integer vs UUID IDs, pagination/filtering, 200 vs 202 job status, `{detail}` vs documented error envelope, missing auth, ignored settings fields, absent report/chat/search/export routes. API Guide and feature local-api also disagree with YAML. Full inventory: [audit report 01](01_ARCHITECTURE_INVENTORY.md).

**U04 resolution (PLANNED):** select canonical certification surface/versioning/compatibility policy; typed request/response models; consistent error/status/security; align runtime/generated schema/canonical YAML; contract gate U07. Merely adding comments or successfully parsing YAML does not execute this work. Root YAML content below comments is intentionally preserved, including known structural and schema weaknesses.

[Data status](DATA_MODEL_STATUS.md) · [ADR-004](../adr/ADR-004-local-llm-provider-abstraction.md) · [backlog](05_UPGRADE_BACKLOG.md).
