# VK Social Radar — Repository AS-IS

Дата аудита: 2026-09-23. Каталог: `C:\Developments\Javascript\VK`.
Branch / commit: **UNAVAILABLE**. `git status --short`, `git branch --show-current`, `git rev-parse HEAD` и `git ls-files --cached` возвращают `not a git repository`. Это аудит предоставленной рабочей копии, не подтверждённой ревизии Git.

## Метод и границы

Исследованы production-код, static UI, конфигурация, существующие Python-тесты, SDD в корне и `specs/`, архив `Artefacts.zip`. Рабочая SQLite открывалась только через `mode=ro`: прочитаны схема и число нарушений FK, без вывода пользовательских строк. Chromium, сбор VK, LLM inference, startup приложения, `start.bat` и `stop.bat` не запускались. Новые зависимости не установлены, исходники и тесты не исправлялись. Созданы только шесть Markdown-отчётов в этом каталоге; commit/push не выполнялись.

IMPLEMENTED означает наличие конкретного кода и wiring, но не автоматически успешную эксплуатационную проверку. PARTIAL означает реализованное подмножество или отсутствие существенной гарантии. DOCUMENTED_ONLY — описание без реализации; NOT_IMPLEMENTED — отсутствующий механизм; CONTRADICTED_BY_CODE — код нарушает заявленное свойство. Наличие Markdown test case не означает выполненный тест.

## Стек и entrypoints

| Область | Факт | Evidence |
|---|---|---|
| Runtime | Python 3.13.2 в существующей `.venv`; версия Python не закреплена в requirements | проверка `sys.version`; `requirements.txt` |
| HTTP | FastAPI 0.115.14, Uvicorn 0.34.3; версия приложения 0.4.2 | `requirements.txt:1`, `app/main.py:27` |
| HTTP client | httpx 0.28.1, синхронный клиент LM Studio | `requirements.txt:3`, `app/lmstudio.py:40,57` |
| Browser | Playwright 1.53.0, persistent Chromium context, visible/headless=False | `requirements.txt:5`, `app/collector.py:186` |
| Persistence | stdlib sqlite3, raw SQL, 8 прикладных таблиц; ORM нет | `app/db.py:21,33` |
| Frontend | HTML + CSS + vanilla JavaScript; FastAPI StaticFiles | `static/index.html`, `static/app.js:15`, `app/main.py:28,37` |
| Запуск | `python run_server.py`, слушает 127.0.0.1:8765 | `run_server.py:6` |
| Установка/запуск | `start.bat` создаёт venv, обновляет pip, устанавливает requirements и Chromium, запускает сервер | `start.bat` |
| Тестовый runner | `run_tests.bat` → `.venv\Scripts\python.exe -m unittest discover -s tests -v` | `run_tests.bat` |
| CI/CD | CI pipeline, build/release gates и deployment manifests не найдены | инвентаризация скрытых и обычных файлов вне `.venv`, runtime data |

React, npm frontend, отдельный AI worker, vector DB, scheduler framework и provider SDK в runtime не обнаружены. `.specify/workflows/speckit/workflow.yml` — workflow подготовки спецификаций, не CI приложения.

## Каталоги

| Каталог/файл | Назначение |
|---|---|
| `app/main.py` | 29 операций `/api/*`, root UI, startup init + demo seed |
| `app/services.py` | SQL queries, импорты relations/message aggregates, diff sets, сохранение previews |
| `app/db.py` | пути, connection context manager, CREATE TABLE IF NOT EXISTS, defaults |
| `app/collector.py` | монолитный SafeVKCollector, DOM JS extraction, навигация, jobs, диагностика |
| `app/importers.py` | JSON/CSV/TSV/HTML/ZIP → нормализация → services |
| `app/lmstudio.py` | settings + HTTP + prompt + сохранение AI-вывода в одном модуле |
| `app/seed.py` | синтетические demo relations и message_stats, если people пуста |
| `static/` | dashboard, people, changes, messages, dialogs, AI insight, import, settings, collector controls |
| `tests/` | 8 Python-файлов; 7 Markdown-спецификаций тестирования |
| `data/` | рабочая SQLite, imports, backups, collector_previews, Chromium profile |
| `logs/collector/` | HTML, PNG и JSON diagnostics |
| `specs/001-vk-profile-analysis/` | продуктовая спецификация, планы, контракты, дубли SDD, архив |
| `specs/001-testing-feature/` | запланированная функция ведения ручных тестов; runtime `/api/tests` отсутствует |
| `.specify/`, `.opencode/` | tooling/specification artifacts; не прикладные сервисы |

## Хранение и конфигурация

`app/db.py:8` фиксирует `data/social_radar.db`, `data/imports`, `data/backups`. `get_connection()` включает foreign_keys, коммитит при нормальном выходе и закрывает соединение. Миграционного механизма и schema version нет. Создание каталога backups не является резервным копированием.

**Рабочая БД отличается от схемы создания новой БД.** В существующей `collector_dialogs` только `id, dialog_key, peer_id, full_name, dialog_url, collected_at`. В коде DDL и INSERT дополнительно используются `preview, date_label, unread, unread_count, outgoing, avatar_url, verified` (`app/db.py:98`, `app/services.py:307`). `CREATE TABLE IF NOT EXISTS` не добавляет эти поля. Сохранение dialog preview на этой БД не совместимо с текущим SQL; в UI отсутствуют соответствующие значения. Read-only `PRAGMA foreign_key_check` обнаружил 0 нарушений; это не проверка семантики snapshots и не доказательство совместимости схем.

Настройки хранятся строками в `app_settings`: `lmstudio_base_url`, `lmstudio_model`, `lmstudio_temperature` (`app/lmstudio.py:17`). Default endpoint `http://127.0.0.1:1234/v1`, model пустая строка → первая модель из `/models`, temperature 0.2 (`app/db.py:127`). Проверки локальности адреса и выбора provider нет. Переменная `VK_COLLECTOR_PROFILE_DIR` переопределяет путь профиля (`app/collector.py:19`). API не проверяет Bearer Token.

Startup (`app/main.py:31`) вызывает `init_db()` и `seed_demo_data()`. Пустая пользовательская БД автоматически получает demo-данные. Аудит startup не выполнял.

## Фактический runtime flow

1. Browser UI → `fetch('/api/...')` → FastAPI → функции services или конкретный LM Studio module/collector singleton.
2. Collector → VK DOM → extractor/очистка/dedup → preview в памяти и JSON. Пользователь отдельно нажимает save-preview → relation rows либо collector_dialogs.
3. JSON/CSV/HTML/ZIP upload сохраняется локально → парсинг → dict normalization → relation import/message_stats upsert → import_jobs.
4. Relations import вычисляет разности множеств с предыдущей датой и записывает relation_events. Dashboard читает relations, message_stats и imports напрямую из SQLite.
5. AI insight → person_detail → последние агрегаты + до 10 событий → prompt → `/chat/completions` → json.loads → ai_insights. Нет retrieval/index/chat.
6. Organization source API имеет asyncio jobs, status/result/cancel. Jobs живут в словаре `SafeVKCollector.operations`, results дополнительно пишутся в preview JSON; scheduler и durable job storage отсутствуют. Организационный preview не поддерживается `save_collector_preview()`.

## Проверки, выполненные при аудите

| Проверка | Результат / ограничение |
|---|---|
| Существующий unittest suite | **18 passed, 0 failures, 0 errors**, 1.158 s; временные DB_PATH/DATA_DIR/IMPORT_DIR/BACKUP_DIR, включая импортированный `app.importers.IMPORT_DIR`; `-B` запрещает pyc writes |
| 8 функций `test_v043_organization_source.py` | **8 passed** при прямом вызове существующих `test_*`; pytest не установлен, зависимости не добавлялись. unittest их не обнаруживает |
| Generated OpenAPI | `app.openapi()` без startup: 3.1.0, app 0.4.2, 29 API operations + root `/` |
| Read-only ASGI smoke | `/api/health` → 200 + status/version; `/api/v1/health` → 404. Без startup и реального сервера |
| Синтетический same-day import | payload содержит 1 человека, returned removed=1; dashboard продолжает показывать 2 |
| Повтор того же import | число событий возрастает 1 → 2 |
| Пустой snapshot | новая дата с [] не становится текущим состоянием; dashboard остаётся 2 |
| FK | 0 нарушений в рабочей read-only БД и в изолированной синтетической БД |
| Неизменность | при завершающих runtime/schema probes SHA-256 21 файла (production, tests, static, requirements, DB) не изменился; до/после создания отчётов дополнительно совпали hashes 26 файлов app/tests/static, включая test docs |

Первая audit ASGI-попытка была остановлена собственной блокировкой `socket.connect`: Windows asyncio создаёт loopback socketpair. Это ошибка изоляции audit harness, не падение product suite. Повторная ASGI-проверка завершилась успешно с блокировкой внешнего HTTP transport. Полный live collector/LLM/UI E2E не проверялся.

Команда проекта: `run_tests.bat` или `.venv\Scripts\python.exe -m unittest discover -s tests -v`. Для безопасного аудита эта команда исполнялась через `unittest.defaultTestLoader.discover('tests')` с временными path patches. Прямой запуск без patches может перезаписать `data/imports/friends.csv` (`tests/test_v02.py:test_csv_file_import`). Процент coverage не измерялся.

## Security / local-first AS-IS

| Проверка | Verdict | Evidence |
|---|---|---|
| Локальные storage и bind | PASS | `app/db.py:8`, `run_server.py:6` |
| Обязательная внешняя LLM | Не обнаружена | localhost default, AI вызывается отдельно; `app/lmstudio.py:36,57` |
| Гарантия local-only inference | FAIL | endpoint произвольно задаётся через settings; имя и метрики отправляются на этот адрес |
| Hardcoded secrets | В просмотренном прикладном коде не обнаружены | read-only review, дополнительный AST поиск secret/password/token literal assignments без значений; не forensic/Git-history scan |
| Cookies/session tracked Git | UNVERIFIABLE | .git отсутствует; ignore не доказывает untracked |
| Raw/test dumps tracked Git | UNVERIFIABLE | .git отсутствует; `FILE_MANIFEST.md` — не Git index |
| Ignore | PARTIAL | `.gitignore` покрывает DB, imports/backups/previews/profile/collector logs; не покрывает явно DB `-wal`, `-shm`, `-journal`, `.env`, нестандартные profile paths |
| Runtime sensitive artifacts | PRESENT | без чтения содержимого: 4206 файлов profile, 18 previews, 12 diagnostics, 1 import (без `.gitkeep`) |
| Безопасность логов | PARTIAL | trace URL sanitizer `app/collector.py:163`; но `_save_diagnostics:2650` пишет raw DOM, screenshot, page.url без общего scrubber; page errors и exception text проходят в ответы |
| Cookie dump в коде | Явный вызов cookies dump не найден | не доказывает отсутствие token/session данных в raw DOM/URL или profile |
| Browser request restrictions | PARTIAL | whitelist `_route_request:224`, но exception branch вызывает continue_ (fail-open) |
| Публикация экспорта наружу | Не обнаружена | пользовательского export service нет; preview/diagnostics пишутся локально |

Подробные inventories: [01](01_ARCHITECTURE_INVENTORY.md), [02](02_PATTERN_INVENTORY.md), [03](03_SDD_CODE_GAP_ANALYSIS.md), [04](04_CERTIFICATION_READINESS.md), [05](05_UPGRADE_BACKLOG.md).
