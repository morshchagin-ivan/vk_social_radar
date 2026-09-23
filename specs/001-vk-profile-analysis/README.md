# Historical target specification package

Этот каталог содержит TARGET / EVOLUTIONARY DESIGN и исходный task plan, а не свидетельство завершённой реализации. Canonical certification baseline: [landing](../../docs/certification/README.md), [CURRENT C4](../../docs/certification/C4_CURRENT.md), [status](../../docs/certification/ARCHITECTURE_STATUS.md), [ADR register](../../docs/adr/README.md).

Нумерованные SDD являются копиями корневых target documents. Новые banners используют относительные ссылки для своего каталога; исходный body сохранён. [Artefacts.zip](Artefacts.zip) оставлен неизменённым историческим архивом target SDD; внутри нет новых status banners, не следует воспринимать его как implementation evidence.

[spec.md](spec.md), [plan](plan.md), [research](research.md), [data model](data-model.md), [contract](contracts/local-api.md), [quickstart](quickstart.md) и [tasks](tasks.md) — планы. Ветка, указанная в plan, не подтверждает текущую Git revision. PASS в design gates и отметки [requirements checklist](checklists/requirements.md) относятся к разработке спецификации, не к runtime verification. Tasks не помечались выполненными в baseline.

При конфликте target требований приоритет baseline задают accepted ADR. Например, legacy T018 отвергает empty collection, а [ADR-003](../../docs/adr/ADR-003-immutable-snapshot-source-of-truth.md) различает confirmed-empty и failed/partial run. Reconciliation — U03; сам task body здесь не переписан.
