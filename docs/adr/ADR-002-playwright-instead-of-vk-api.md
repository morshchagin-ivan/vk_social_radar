# ADR-002 — Playwright instead of VK API

**Status:** ACCEPTED. **Implementation:** IMPLEMENTED. **Date:** 2026-09-23.
**Decision owners:** владелец VK Social Radar и architecture maintainer (роли).
**Related backlog:** [U10 parsers, U06 privacy, U13 validation](../certification/05_UPGRADE_BACKLOG.md).

## Context

[Spec FR-1 / Chromium Profile / Constraints](../../spec.md) предполагают работу с доступным пользователю VK web interface. Реальный collector уже использует Playwright и отдельную persistent session; direct VK API client в аудированной копии не найден.

## Decision

Сохранить browser collection через отдельный Chromium profile и Playwright; собирать доступное пользовательской сессии содержимое в пределах поддерживаемых surfaces. Не обходить авторизацию/visibility limits. Явный preview отделять от persistence. Public organization scan не доказывает employment/личные отношения.

## Current implementation status

[SafeVKCollector.start](../../app/collector.py) создаёт persistent context; `collect` поддерживает friends/followers/dialogs; `collect_public_organization_source` — public member collection. API wiring находится в [main.py](../../app/main.py). IMPLEMENTED означает code/wiring; live VK correctness и полнота DOM extraction этим baseline не проверялись.

## Alternatives considered

Direct VK API integration с отдельной проверкой доступных endpoints/permissions; только импорт файлов; live scraping в пользовательском основном browser profile. API не выбран для данного baseline, но ADR не утверждает, что VK API вообще непригоден или недоступен. Импорт уже существует как дополнительный источник, не замена всем flows.

## Consequences

- Positive: единая browser session и соответствие выбранной модели доступа; preview перед save.
- Negative: DOM fragility, virtual scrolling и зависимость от browser lifecycle.
- Risks: partial scans, auth/captcha states, selectors changing; существующие marker tests не доказывают extraction.

## Security/Privacy impact

Separate profile — реальная граница хранения session, но содержит чувствительные данные. Whitelist существует с fail-open exception branch; raw DOM diagnostics требуют U06. Организационный membership не следует трактовать как employment.

## Validation/Evidence

[Audit components](../certification/01_ARCHITECTURE_INVENTORY.md); [test_v03.py](../../tests/test_v03.py) profile path/preview save; [v043 tests](../../tests/test_v043_organization_source.py) classification + source assertions. DOM fixture substitution/fullness tests — future U10/U07.

## Evolution path

Выделить replaceable parsers U10 и completeness/normalization U13, сохранив browser adapter и UI orchestration. Новые API-based collectors возможны позже только при обоснованном изменении требований.
