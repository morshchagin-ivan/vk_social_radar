# Certification Baseline Checklist

Baseline 1.0 · 2026-09-23. Галочка означает проверенный documentary deliverable, не выполнение target capability. Источник результатов — [Baseline upgrade report](BASELINE_UPGRADE_REPORT.md). Pending items не отмечаются по факту генерации файла.

- [ ] Git revision known
- [x] README current/target distinction — reviewed against frozen audit
- [x] Current C4 — actual modules and flows only
- [x] Target C4 — planned boundaries labelled
- [x] ADR 001–006 — all template fields and separate implementation statuses checked
- [x] Architecture status — allowed vocabulary and Uxx links checked
- [x] Traceability — existing FR IDs and actual/target API distinguished
- [x] Technical debt — defects separated from roadmap gaps
- [x] NFR baseline — code settings distinguished from proposed/TBD metrics
- [x] API status — mismatch retained; YAML comments only
- [x] Data model status — eight tables and known P0 drift documented
- [x] Privacy status — Git/local-policy limitations retained
- [x] Tests evidence — prior 18 + 8 audit results, no new execution claimed
- [x] Defense guide — 20 evidence-based questions and static demo path reviewed
- [x] All relative links valid — static target-existence validation
- [x] Mermaid blocks parse or syntax checked — syntax review/basic screening only; parser unavailable
- [x] No target capability called implemented without evidence — semantic review against audit

Git revision остаётся открытой, пока не предоставлен настоящий checkout. Test evidence — результаты прежнего audit, а не новый test run. API status — прозрачное описание mismatch, не исправленный contract. NFR baseline — измеримые предложения/TBD, не выполненные SLA. Mermaid parser при отсутствии не подменяется утверждением о render success.
