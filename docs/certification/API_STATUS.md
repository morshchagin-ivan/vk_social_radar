# API Status

**U04 IMPLEMENTED · Contract Governance IMPLEMENTED · API drift RESOLVED for the current runtime · 2026-09-24.** [Report](U04_API_CONTRACT_REPORT.md) and [pre-build/final inventory](U04_RUNTIME_API_INVENTORY.md).

| Aspect | Verified current contract |
|---|---|
| Canonical artifact | [root 11_OPENAPI.yaml](../../11_OPENAPI.yaml), generated from FastAPI metadata/models (strategy A) |
| Format/server | OpenAPI 3.1.0, JSON-form YAML 1.2; http://127.0.0.1:8765 with `/api` paths |
| Operations | 29 public API + 1 internal HTML shell = 30 canonical; 21 frontend call sites covered |
| IDs | 30 explicit stable unique operationIds |
| Schemas | 27 explicit response-model operations, two existing typed settings mappings, HTML shell; 32 components including framework validation/multipart schemas |
| Requests | preserved dict/service validation and coercion, multipart required fields, required path/query fields; limits documented as clamping |
| Errors | JSON detail for mapped errors; safe 422 detail array without input/ctx; Host 400/Origin 403; generic 500 plain text; startup can return JSON 500; provider/circuit 503 |
| Security | no API authentication; no Bearer requirement; U06 local Host/Origin checks and loopback-only LLM policy; trusted OS single-user boundary |
| Ownership | author route metadata/models, export root artifact; feature YAML archived/non-canonical |
| Drift gate | 23 new standard-discoverable tests; exact fresh app.openapi export + semantic route/param/schema/security/UI checks + mutation rejection |
| Validation | JSON/YAML parse, reference/structural checks and behavior fixtures PASS; formal OpenAPI validator unavailable; no client generation claim |

The former 18-operation `/api/v1` target is preserved only in the existing feature proposal. All 18 old URLs are non-runtime; after prefix normalization, 14 have no equivalent operation. Runtime retained `/api`, 200 job busy/pending semantics, integer person IDs and no auth. No target endpoints were implemented to match old documentation.

U03 appears through relation import/save, dashboard/people flags and changes; there is no snapshot resource route. Incomplete collector observations never replace current truth. Message_stats/AI are not snapshot-reproducible. U05/U09 appear through existing insight and model discovery/test routes; controlled 503 is retained. Auth, RAG, Graph, Export and Scheduler are not implemented.

Latest U06 gate evidence: **171 unittest PASS** (31 U06 + 23 U04 + 34 U03 + 25 U09 + 26 U05 + 14 U02 + 18 existing), **8 additional functions PASS**. No live VK/LM Studio/Chromium, network or user DB. [Guide](../../12_API_GUIDE.md) · [Backlog](05_UPGRADE_BACKLOG.md).
