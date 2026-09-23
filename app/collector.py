from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from .db import BASE_DIR

PROFILE_DIR = Path(os.getenv("VK_COLLECTOR_PROFILE_DIR") or BASE_DIR / "data" / "vk_browser_profile")
DIAGNOSTICS_DIR = BASE_DIR / "logs" / "collector"
PREVIEW_DIR = BASE_DIR / "data" / "collector_previews"

ALLOWED_HOST_SUFFIXES = (
    "vk.com",
    "vk.ru",
    "vk.me",
    "vkuser.net",
    "vk-cdn.net",
    "vkuseraudio.net",
    "vkuserphoto.ru",
    "vkcdn.ru",
    "vkvideo.ru",
    "vkuservideo.net",
    "userapi.com",
    "localhost",
    "127.0.0.1",
)

RESERVED_PATHS = {
    "", "feed", "friends", "im", "groups", "albums", "photos", "video", "music",
    "apps", "settings", "support", "search", "login", "join", "away", "wall",
    "market", "clips", "stories", "bookmarks", "notifications", "docs",
}

VK_ORGANIZATION_SOURCE_TYPES = {"ORGANIZATION_COMMUNITY", "PUBLIC_COMMUNITY"}
VK_PUBLIC_HOSTS = {"vk.com", "www.vk.com", "vk.ru", "www.vk.ru"}
VK_MEDIA_PREFIXES = ("wall", "photo", "video", "clip", "doc", "album", "market")
SENSITIVE_LINK_HOSTS = {"login.vk.com", "login.vk.ru", "id.vk.com", "id.vk.ru"}
SENSITIVE_LINK_MARKERS = ("logout", "access_token", "remixsid", "cookie", "password", "hash=")


def classify_public_vk_source(source_url: str) -> dict[str, Any]:
    original = str(source_url or "").strip()
    if not original:
        return {"source_type": "UNKNOWN_VK_SOURCE", "source_url": "", "normalized_url": "", "eligible_for_collection": False}
    candidate = original if "://" in original else f"https://{original}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    path = parsed.path.strip("/")
    first = path.split("/", 1)[0].strip()
    normalized = f"https://vk.com/{first}" if host in VK_PUBLIC_HOSTS and first else ""
    if host not in VK_PUBLIC_HOSTS or not first:
        source_type = "UNKNOWN_VK_SOURCE"
    elif first.lower() in RESERVED_PATHS:
        source_type = "UNKNOWN_VK_SOURCE"
    elif first.lower().startswith(VK_MEDIA_PREFIXES):
        source_type = "POST" if first.lower().startswith("wall") else "MEDIA_DOCUMENT"
    elif re.fullmatch(r"id\d+", first, flags=re.I):
        source_type = "PERSON_PROFILE"
    elif re.fullmatch(r"(club|public)\d+", first, flags=re.I):
        source_type = "ORGANIZATION_COMMUNITY"
    elif re.fullmatch(r"event\d+", first, flags=re.I):
        source_type = "PUBLIC_COMMUNITY"
    elif re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", first):
        source_type = "PUBLIC_COMMUNITY"
    else:
        source_type = "UNKNOWN_VK_SOURCE"
    return {
        "source": "vk",
        "source_url": original,
        "normalized_url": normalized,
        "source_type": source_type,
        "eligible_for_collection": source_type in VK_ORGANIZATION_SOURCE_TYPES,
        "path": first,
        "host": host,
    }


def is_safe_public_link(url: str) -> bool:
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower()
    if not parsed.scheme.startswith("http") or not host:
        return False
    lowered = str(url or "").lower()
    if host in SENSITIVE_LINK_HOSTS:
        return False
    if any(marker in lowered for marker in SENSITIVE_LINK_MARKERS):
        return False
    return True


@dataclass
class CollectorState:
    status: str = "stopped"
    current_url: str = ""
    authenticated: bool = False
    last_error: str | None = None
    last_action: str | None = None
    preview: dict[str, Any] | None = None
    blocked_hosts: set[str] = field(default_factory=set)


TERMINAL_OPERATION_STATES = {"COMPLETED", "FAILED", "CANCELLED", "AUTH_REQUIRED", "BLOCKED", "PARSER_DEGRADED"}


@dataclass
class CollectorOperation:
    operation_id: str
    operation_type: str
    source_url: str
    collection_surface: str = "COMMUNITY_MEMBERS"
    state: str = "QUEUED"
    started_at: str = ""
    updated_at: str = ""
    finished_at: str = ""
    authenticated: bool = False
    members_discovered: int = 0
    members_deduped: int = 0
    current_offset: int = 0
    current_page: int = 0
    current_scroll: int = 0
    profiles_enriched: int = 0
    result_available: bool = False
    cancel_requested: bool = False
    last_error: str = ""
    safe_diagnostics: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "state": self.state,
            "source_url": self.source_url,
            "collection_surface": self.collection_surface,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "finished_at": self.finished_at,
            "authenticated": self.authenticated,
            "members_discovered": self.members_discovered,
            "members_deduped": self.members_deduped,
            "current_offset": self.current_offset,
            "current_page": self.current_page,
            "current_scroll": self.current_scroll,
            "profiles_enriched": self.profiles_enriched,
            "result_available": self.result_available,
            "cancel_requested": self.cancel_requested,
            "last_error": self.last_error,
            "safe_diagnostics": self.safe_diagnostics,
        }


def _sanitize_trace_url(value: str) -> str:
    parsed = urlparse(str(value or ""))
    if not parsed.scheme or not parsed.netloc:
        return str(value or "")[:220]
    allowed_query: list[str] = []
    query = parse_qs(parsed.query, keep_blank_values=True)
    for key in ("act", "section", "tab", "offset", "page"):
        if key in query and query[key]:
            allowed_query.append(f"{key}={query[key][0][:40]}")
    query_text = ("?" + "&".join(allowed_query)) if allowed_query else ""
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{query_text}"[:260]


class SafeVKCollector:
    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.lock = asyncio.Lock()
        self.state = CollectorState()
        self.operations: dict[str, CollectorOperation] = {}
        self.active_operation_id: str | None = None

    async def start(self) -> dict[str, Any]:
        async with self.lock:
            if self.context and self.page:
                return await self.get_status()

            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)
            PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

            self.playwright = await async_playwright().start()
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1440, "height": 940},
                locale="ru-RU",
                args=[
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-default-apps",
                    "--disable-sync",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )
            self.context.set_default_timeout(12_000)
            self.context.set_default_navigation_timeout(45_000)

            await self.context.route("**/*", self._route_request)
            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()
            self.page.on("pageerror", lambda exc: self._set_error(f"Page error: {exc}"))

            self.state.status = "running"
            self.state.last_error = None
            await self.page.goto("https://vk.com/", wait_until="domcontentloaded")
            await self._wait_soft()
            return await self.get_status()

    async def _route_request(self, route, request) -> None:
        try:
            host = (urlparse(request.url).hostname or "").lower()
            allowed = any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES)
            if allowed or request.url.startswith(("data:", "blob:", "about:")):
                await route.continue_()
            else:
                self.state.blocked_hosts.add(host or request.url[:80])
                await route.abort()
        except Exception:
            await route.continue_()

    def _set_error(self, message: str) -> None:
        self.state.last_error = message

    async def _wait_soft(self) -> None:
        await asyncio.sleep(1.2)

    async def close(self) -> dict[str, Any]:
        async with self.lock:
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
            self.context = None
            self.page = None
            self.playwright = None
            self.state.status = "stopped"
            self.state.current_url = ""
            self.state.authenticated = False
            return await self.get_status()

    async def delete_profile(self) -> dict[str, Any]:
        await self.close()
        if PROFILE_DIR.exists():
            shutil.rmtree(PROFILE_DIR)
        self.state.preview = None
        return {"ok": True, "deleted": str(PROFILE_DIR)}

    async def get_status(self) -> dict[str, Any]:
        if self.page:
            try:
                self.state.current_url = self.page.url
                self.state.authenticated = await self._detect_authenticated()
            except Exception as exc:
                self.state.last_error = str(exc)
        active = self.operations.get(self.active_operation_id or "")
        return {
            "status": self.state.status,
            "current_url": self.state.current_url,
            "authenticated": self.state.authenticated,
            "last_error": self.state.last_error,
            "last_action": self.state.last_action,
            "has_preview": bool(self.state.preview),
            "blocked_hosts": sorted(self.state.blocked_hosts),
            "profile_dir": str(PROFILE_DIR),
            "operation_id": active.operation_id if active else "",
            "operation_state": active.state if active else "",
            "collection_surface": active.collection_surface if active else "",
            "members_discovered": active.members_discovered if active else 0,
            "members_deduped": active.members_deduped if active else 0,
            "progress": active.to_safe_dict() if active else {},
            "result_available": active.result_available if active else False,
        }

    async def _detect_authenticated(self) -> bool:
        if not self.page:
            return False
        url = self.page.url.lower()
        if "login" in url or "join" in url:
            return False
        selectors = [
            'a[href="/feed"]',
            'a[href*="logout"]',
            '[data-testid*="profile"]',
            'a[href^="/id"]',
            'a[href^="https://vk.com/id"]',
        ]
        for selector in selectors:
            try:
                if await self.page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass
        return "/feed" in url or "/friends" in url or "/im" in url

    async def check_auth(self) -> dict[str, Any]:
        async with self.lock:
            self._ensure_running()
            self.state.authenticated = await self._detect_authenticated()
            self.state.last_action = "check_auth"
            return await self.get_status()

    def _ensure_running(self) -> None:
        if not self.page or not self.context:
            raise RuntimeError("Сборщик не запущен")

    def _active_busy_operation(self) -> CollectorOperation | None:
        operation = self.operations.get(self.active_operation_id or "")
        if operation and operation.state not in TERMINAL_OPERATION_STATES:
            return operation
        return None

    @staticmethod
    def _utc_now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    def _mark_operation_progress(
        self,
        operation: CollectorOperation | None,
        *,
        state: str | None = None,
        members_discovered: int | None = None,
        members_deduped: int | None = None,
        current_scroll: int | None = None,
        current_offset: int | None = None,
        current_page: int | None = None,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        if not operation:
            return
        if state:
            operation.state = state
        if members_discovered is not None:
            operation.members_discovered = members_discovered
        if members_deduped is not None:
            operation.members_deduped = members_deduped
        if current_scroll is not None:
            operation.current_scroll = current_scroll
            operation.current_page = current_scroll
        if current_offset is not None:
            operation.current_offset = current_offset
        if current_page is not None:
            operation.current_page = current_page
        if diagnostics:
            operation.safe_diagnostics.update(diagnostics)
        operation.updated_at = self._utc_now()

    def _append_navigation_trace(
        self,
        trace: list[dict[str, Any]],
        event: str,
        *,
        stage: str = "stage_a",
        operation: CollectorOperation | None = None,
        reason: str = "",
        url: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if len(trace) >= 240:
            return
        current_url = url or (self.page.url if self.page else "")
        row = {
            "event": event,
            "stage": stage,
            "operation_id": operation.operation_id if operation else "",
            "timestamp": self._utc_now(),
            "url": _sanitize_trace_url(current_url),
            "reason": reason,
        }
        if extra:
            row.update({key: value for key, value in extra.items() if key not in {"password", "cookie", "access_token", "remixsid"}})
        trace.append(row)

    def _append_url_transition_trace(
        self,
        trace: list[dict[str, Any]],
        *,
        cause: str,
        from_url: str,
        to_url: str,
        stage: str = "stage_a",
        operation: CollectorOperation | None = None,
        initiator: dict[str, Any] | None = None,
    ) -> None:
        if len(trace) >= 240:
            return
        trace.append({
            "event": "URL_CHANGE",
            "stage": stage,
            "operation_id": operation.operation_id if operation else "",
            "timestamp": self._utc_now(),
            "from_url": _sanitize_trace_url(from_url),
            "to_url": _sanitize_trace_url(to_url),
            "cause": cause,
            "initiator": initiator or {},
        })

    async def _detect_current_user_profile_paths(self) -> list[str]:
        assert self.page
        paths = await self.page.evaluate(
            """
            () => {
              const reserved = new Set(['','feed','friends','im','groups','photos','audios','videos','settings','support','login','join','away','edit']);
              const scopes = [...document.querySelectorAll(
                'header, nav, aside, [role="navigation"], [role="complementary"], [id*="side"], [class*="side"], [class*="LeftMenu"], [class*="Top"], [class*="Header"]'
              )];
              const result = [];
              for (const scope of scopes) {
                for (const a of scope.querySelectorAll('a[href]')) {
                  try {
                    const u = new URL(a.href, location.origin);
                    const p = u.pathname.replace(/^\\/+|\\/+$/g, '').toLowerCase();
                    if (!['vk.com','www.vk.com','vk.ru','www.vk.ru'].includes(u.hostname)) continue;
                    if (!p || reserved.has(p) || p.includes('/')) continue;
                    if (/^(wall|photo|video|clip|market|album|doc|club|public|event)/i.test(p)) continue;
                    if (/^id\\d+$/i.test(p) || /^[a-z0-9_.-]{3,64}$/i.test(p)) result.push(p);
                  } catch {}
                }
              }
              return [...new Set(result)].slice(0, 12);
            }
            """
        )
        return [str(path).lower() for path in paths if str(path).strip()]

    @staticmethod
    def _stage_url_status(
        url: str,
        classification: dict[str, Any],
        current_user_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        parsed = urlparse(str(url or ""))
        host = (parsed.hostname or "").lower()
        path = parsed.path.strip("/").lower()
        query = parse_qs(parsed.query)
        expected = str(classification.get("path") or "").lower()
        has_member_query = (
            query.get("act", [""])[0] == "members"
            or query.get("section", [""])[0] == "members"
            or query.get("tab", [""])[0] == "members"
        )
        current_users = {str(item or "").lower() for item in current_user_paths or []}
        status = "ALLOWED_ORGANIZATION" if path == expected and not has_member_query else "ALLOWED_MEMBER_SURFACE" if path == expected and has_member_query else "UNKNOWN_NAVIGATION"
        if host not in VK_PUBLIC_HOSTS:
            status = "UNEXPECTED_NAVIGATION"
        elif path in current_users:
            status = "OPERATOR_PROFILE_NAVIGATION"
        elif path in {"feed", "friends", "im", "groups"}:
            status = "FEED_NAVIGATION"
        elif re.fullmatch(r"id\d+", path, flags=re.I):
            status = "PERSON_PROFILE_NAVIGATION"
        elif path.startswith(VK_MEDIA_PREFIXES) or path.startswith("wall"):
            status = "WALL_FEED_DETECTED"
        elif expected and path and path != expected:
            status = "UNRELATED_COMMUNITY"
        return {
            "status": status,
            "path": path,
            "expected_path": expected,
            "has_member_query": has_member_query,
            "is_allowed": status in {"ALLOWED_ORGANIZATION", "ALLOWED_MEMBER_SURFACE"},
        }

    async def _goto_stage_a(
        self,
        url: str,
        *,
        cause: str,
        classification: dict[str, Any],
        current_user_paths: list[str],
        navigation_trace: list[dict[str, Any]],
        operation: CollectorOperation | None,
    ) -> dict[str, Any]:
        assert self.page
        from_url = self.page.url
        target_status = self._stage_url_status(url, classification, current_user_paths)
        if not target_status["is_allowed"]:
            self._append_url_transition_trace(
                navigation_trace,
                cause="UNEXPECTED_CLICK_NAVIGATION" if cause.endswith("CLICK") else cause,
                from_url=from_url,
                to_url=url,
                operation=operation,
                initiator={"target_status": target_status["status"], "blocked_before_goto": True},
            )
            return {"ok": False, **target_status}
        await self.page.goto(url, wait_until="domcontentloaded")
        await self._wait_soft()
        to_url = self.page.url
        self._stage_a_last_observed_url = to_url
        status = self._stage_url_status(to_url, classification, current_user_paths)
        self._append_url_transition_trace(
            navigation_trace,
            cause=cause,
            from_url=from_url,
            to_url=to_url,
            operation=operation,
            initiator={"target_status": status["status"]},
        )
        return {"ok": bool(status["is_allowed"]), **status}

    async def _check_stage_a_url_invariant(
        self,
        *,
        cause: str,
        before_url: str,
        classification: dict[str, Any],
        current_user_paths: list[str],
        navigation_trace: list[dict[str, Any]],
        operation: CollectorOperation | None,
        initiator: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assert self.page
        current = self.page.url
        if current != before_url:
            status = self._stage_url_status(current, classification, current_user_paths)
            self._append_url_transition_trace(
                navigation_trace,
                cause=cause if status["is_allowed"] else "UNKNOWN_NAVIGATION" if cause == "MEMBER_CONTAINER_SCROLL" else cause,
                from_url=before_url,
                to_url=current,
                operation=operation,
                initiator={**(initiator or {}), "target_status": status["status"]},
            )
            return {"ok": bool(status["is_allowed"]), **status}
        status = self._stage_url_status(current, classification, current_user_paths)
        if not status["is_allowed"]:
            self._append_url_transition_trace(
                navigation_trace,
                cause=cause,
                from_url=before_url,
                to_url=current,
                operation=operation,
                initiator={**(initiator or {}), "target_status": status["status"]},
            )
        return {"ok": bool(status["is_allowed"]), **status}

    def _arm_stage_a_navigation_observers(
        self,
        navigation_trace: list[dict[str, Any]],
        operation: CollectorOperation | None,
    ) -> None:
        if not self.page:
            return
        self._stage_a_navigation_trace = navigation_trace
        self._stage_a_navigation_operation = operation
        self._stage_a_last_observed_url = self.page.url
        if getattr(self, "_stage_a_navigation_observer_armed", False):
            return

        def on_frame_navigated(frame: Any) -> None:
            try:
                if not self.page or frame != self.page.main_frame:
                    return
                current = str(frame.url or "")
                previous = str(getattr(self, "_stage_a_last_observed_url", "") or "")
                if current and current != previous:
                    self._append_url_transition_trace(
                        getattr(self, "_stage_a_navigation_trace", []),
                        cause="BROWSER_REDIRECT",
                        from_url=previous,
                        to_url=current,
                        operation=getattr(self, "_stage_a_navigation_operation", None),
                        initiator={"event": "framenavigated"},
                    )
                    self._stage_a_last_observed_url = current
            except Exception:
                return

        def on_popup_opened(popup: Any) -> None:
            try:
                self._append_url_transition_trace(
                    getattr(self, "_stage_a_navigation_trace", []),
                    cause="POPUP_NAVIGATION",
                    from_url=self.page.url if self.page else "",
                    to_url=str(getattr(popup, "url", "") or ""),
                    operation=getattr(self, "_stage_a_navigation_operation", None),
                    initiator={"event": "popup"},
                )
            except Exception:
                return

        self.page.on("framenavigated", on_frame_navigated)
        self.page.on("popup", on_popup_opened)
        self._stage_a_navigation_observer_armed = True

    async def navigate(self, target: str) -> dict[str, Any]:
        async with self.lock:
            self._ensure_running()
            urls = {
                "home": "https://vk.com/",
                "friends": "https://vk.com/friends",
                "followers": "https://vk.com/friends?section=subscribers",
                "dialogs": "https://vk.com/im",
            }
            if target not in urls:
                raise ValueError("Неизвестная страница")
            await self.page.goto(urls[target], wait_until="domcontentloaded")
            await self._wait_soft()
            self.state.last_action = f"navigate:{target}"
            return await self.get_status()

    async def collect(self, kind: str) -> dict[str, Any]:
        busy = self._active_busy_operation()
        if busy:
            raise RuntimeError(f"COLLECTOR_BUSY:{busy.operation_id}:{busy.operation_type}")
        async with self.lock:
            self._ensure_running()
            if not await self._detect_authenticated():
                raise RuntimeError("В отдельном Chromium необходимо войти в VK")

            if kind == "friends":
                url = "https://vk.com/friends"
                await self.page.goto(url, wait_until="domcontentloaded")
                await self._wait_soft()
                items, report = await self._collect_profiles()
            elif kind == "followers":
                url = "https://vk.com/friends?section=subscribers"
                await self.page.goto(url, wait_until="domcontentloaded")
                await self._wait_soft()
                items, report = await self._collect_profiles()
            elif kind == "dialogs":
                url = "https://vk.com/im"
                await self.page.goto(url, wait_until="domcontentloaded")
                await self._wait_soft()
                items, report = await self._collect_dialogs()
            else:
                raise ValueError("kind должен быть friends, followers или dialogs")

            if not items:
                diagnostics = await self._save_diagnostics(kind, report)
                raise RuntimeError(
                    f"Найдено 0 валидных записей. Данные не сохранены. Диагностика: {diagnostics}"
                )

            preview = {
                "kind": kind,
                "collected_at": datetime.now().isoformat(timespec="seconds"),
                "source_url": self.page.url,
                "count": len(items),
                "items": items,
                "report": report,
            }
            self.state.preview = preview
            self.state.last_action = f"collect:{kind}"
            preview_path = PREVIEW_DIR / f"preview_{kind}_{datetime.now():%Y%m%d_%H%M%S}.json"
            preview_path.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
            return preview

    async def _find_scroll_target(self) -> dict[str, Any]:
        assert self.page
        return await self.page.evaluate(
            """
            () => {
              const all = [...document.querySelectorAll('main, section, [role="main"], [role="list"], div')];
              const candidates = [];
              for (const el of all) {
                if (!(el instanceof HTMLElement) || el.offsetParent === null) continue;
                const style = getComputedStyle(el);
                const scrollable = ['auto', 'scroll'].includes(style.overflowY)
                  && el.scrollHeight > el.clientHeight + 300;
                if (!scrollable) continue;
                const anchors = el.querySelectorAll('a[href]').length;
                const score = (el.scrollHeight - el.clientHeight) + anchors * 30;
                candidates.push({
                  score,
                  anchors,
                  scrollHeight: el.scrollHeight,
                  clientHeight: el.clientHeight,
                  tag: el.tagName,
                  id: el.id || '',
                  cls: String(el.className || '').slice(0, 160)
                });
              }
              candidates.sort((a,b) => b.score - a.score);
              const best = candidates[0] || null;
              if (best) {
                const match = all.find(el => {
                  if (!(el instanceof HTMLElement)) return false;
                  return el.scrollHeight === best.scrollHeight
                    && el.clientHeight === best.clientHeight
                    && el.querySelectorAll('a[href]').length === best.anchors;
                });
                if (match) {
                  match.dataset.socialRadarScrollTarget = '1';
                  return {kind:'element', ...best};
                }
              }
              return {
                kind:'window',
                anchors: document.querySelectorAll('a[href]').length,
                scrollHeight: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
                clientHeight: window.innerHeight,
                tag:'WINDOW', id:'', cls:''
              };
            }
            """
        )

    async def _extract_visible_profiles(self) -> list[dict[str, Any]]:
        assert self.page
        return await self.page.evaluate(
            """
            () => {
              const reserved = new Set([
                '', 'feed','friends','im','groups','albums','photos','video','music','apps',
                'settings','support','search','login','join','away','wall','market','clips',
                'stories','bookmarks','notifications','docs'
              ]);
              const scope = document.querySelector('[data-social-radar-scroll-target="1"]')
                || document.querySelector('main,[role="main"]')
                || document.body;
              const result = [];
              const anchors = [...scope.querySelectorAll('a[href]')];

              for (const a of anchors) {
                if (!(a instanceof HTMLElement) || a.offsetParent === null) continue;
                let url;
                try { url = new URL(a.href, location.origin); } catch { continue; }
                if (!['vk.com','www.vk.com','vk.ru','www.vk.ru'].includes(url.hostname)) continue;

                const path = url.pathname.replace(/^\\/+|\\/+$/g, '');
                if (!path || reserved.has(path.toLowerCase())) continue;
                if (path.includes('/') || /^(wall|photo|video|clip|market|album)/i.test(path)) continue;

                const isNumeric = /^id\\d+$/.test(path);
                const isSlug = /^[A-Za-z0-9_.]{3,64}$/.test(path);
                if (!isNumeric && !isSlug) continue;

                const card = a.closest(
                  '[data-testid*="friend"], [data-testid*="user"], [role="listitem"], li, article, .friends_user_row, .FriendsListItem'
                ) || a.parentElement?.parentElement;

                if (!card || !(card instanceof HTMLElement) || card.offsetParent === null) continue;

                const cardText = (card.innerText || '').replace(/\\s+/g,' ').trim();
                const hasPersonSignal =
                  card.querySelector('img') !== null ||
                  /написать сообщение|message|удалить из друзей|remove friend|общих друзей|mutual/i.test(cardText);
                if (!hasPersonSignal) continue;

                const candidates = [
                  a.getAttribute('aria-label'),
                  a.textContent,
                  card.querySelector('[data-testid*="name"]')?.textContent,
                  card.querySelector('h1,h2,h3,h4,strong')?.textContent
                ].filter(Boolean).map(v => v.replace(/\\s+/g,' ').trim());

                const name = candidates.find(v =>
                  v.length >= 2 &&
                  v.length <= 100 &&
                  !/^https?:/i.test(v) &&
                  !/^(друзья|подписчики|сообщения|написать|удалить|ещё|меню)$/i.test(v)
                ) || '';

                result.push({
                  path,
                  href: url.origin + url.pathname,
                  name,
                  is_numeric: isNumeric,
                  text_sample: cardText.slice(0,180)
                });
              }
              return result;
            }
            """
        )

    async def _click_load_more_if_present(self) -> bool:
        assert self.page
        selectors = [
            'button:has-text("Показать ещё")',
            'button:has-text("Показать еще")',
            'a:has-text("Показать ещё")',
            'a:has-text("Показать еще")',
            '[role="button"]:has-text("Показать ещё")',
            '[role="button"]:has-text("Показать еще")',
        ]
        for selector in selectors:
            try:
                locator = self.page.locator(selector)
                if await locator.count() > 0 and await locator.first.is_visible():
                    await locator.first.click()
                    await asyncio.sleep(0.8)
                    return True
            except Exception:
                continue
        return False

    async def _collect_profiles(
        self,
        *,
        max_rounds: int = 180,
        max_profiles: int | None = None,
        operation: CollectorOperation | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        assert self.page
        target = await self._find_scroll_target()
        accumulated: dict[str, dict[str, Any]] = {}
        raw_seen = 0
        stable_rounds = 0
        previous_unique = -1
        rounds = 0
        load_more_clicks = 0
        max_rounds = max(1, min(int(max_rounds or 180), 320))

        for rounds in range(1, max_rounds + 1):
            if operation and operation.cancel_requested:
                self._mark_operation_progress(operation, state="CANCELLED", current_scroll=rounds)
                break
            raw = await self._extract_visible_profiles()
            raw_seen += len(raw)

            for item in raw:
                path = item.get("path", "")
                name = self._clean_name(item.get("name") or item.get("text_sample") or "")
                if path.lower() in RESERVED_PATHS or not name:
                    continue
                numeric = re.fullmatch(r"id(\d+)", path)
                candidate = {
                    "vk_id": int(numeric.group(1)) if numeric else None,
                    "screen_name": None if numeric else path,
                    "full_name": name,
                    "profile_url": item["href"],
                }
                old = accumulated.get(path)
                if old is None or len(candidate["full_name"]) < len(old["full_name"]):
                    accumulated[path] = candidate
                if max_profiles and len(accumulated) >= max_profiles:
                    break

            if max_profiles and len(accumulated) >= max_profiles:
                break

            if len(accumulated) == previous_unique:
                stable_rounds += 1
            else:
                stable_rounds = 0
            previous_unique = len(accumulated)

            clicked = await self._click_load_more_if_present()
            if clicked:
                load_more_clicks += 1
                stable_rounds = 0

            self._mark_operation_progress(
                operation,
                members_discovered=len(accumulated),
                members_deduped=len(accumulated),
                current_scroll=rounds,
                current_offset=len(accumulated),
                diagnostics={"last_progress_at": self._utc_now()},
            )

            if target["kind"] == "element":
                await self.page.evaluate(
                    """
                    () => {
                      const el = document.querySelector('[data-social-radar-scroll-target="1"]');
                      if (el) el.scrollTop = Math.min(el.scrollHeight, el.scrollTop + Math.max(600, el.clientHeight * 0.82));
                    }
                    """
                )
            else:
                await self.page.evaluate(
                    "() => window.scrollBy(0, Math.max(700, window.innerHeight * 0.82))"
                )

            await asyncio.sleep(0.55)

            if stable_rounds >= 12:
                break

        for item in await self._extract_visible_profiles():
            path = item.get("path", "")
            name = self._clean_name(item.get("name") or item.get("text_sample") or "")
            if not path or not name:
                continue
            numeric = re.fullmatch(r"id(\d+)", path)
            accumulated[path] = {
                "vk_id": int(numeric.group(1)) if numeric else None,
                "screen_name": None if numeric else path,
                "full_name": name,
                "profile_url": item["href"],
            }

        items = sorted(accumulated.values(), key=lambda x: x["full_name"].lower())
        if operation:
            self._mark_operation_progress(
                operation,
                members_discovered=len(items),
                members_deduped=len(items),
                current_offset=len(items),
                diagnostics={"last_progress_at": self._utc_now()},
            )
        report = {
            "scroll_rounds": rounds,
            "scroll_target_kind": target["kind"],
            "scroll_target_tag": target.get("tag"),
            "scroll_target_class": target.get("cls"),
            "scroll_target_height": target.get("scrollHeight"),
            "scroll_target_client_height": target.get("clientHeight"),
            "load_more_clicks": load_more_clicks,
            "raw_candidates_seen": raw_seen,
            "unique_profiles": len(items),
            "numeric_ids": sum(1 for item in items if item["vk_id"] is not None),
            "screen_names": sum(1 for item in items if item["screen_name"]),
            "stopped_after_stable_rounds": stable_rounds,
            "extractor": "profile_virtualized_accumulator_v2",
        }
        return items, report

    async def _detect_captcha_or_block(self) -> dict[str, Any]:
        assert self.page
        return await self.page.evaluate(
            """
            () => {
              const text = (document.body?.innerText || '').replace(/\\s+/g, ' ').toLowerCase();
              const url = location.href.toLowerCase();
              return {
                captcha: /captcha|капч|подтвердите.*что вы не робот/.test(text) || url.includes('captcha'),
                auth_required: /login|join/.test(url) || /войдите|зарегистрируйтесь/.test(text),
                blocked: /доступ ограничен|access denied|temporarily blocked|слишком много запросов/.test(text),
                text_sample: text.slice(0, 220)
              };
            }
            """
        )

    async def _extract_public_source_identity(self) -> dict[str, Any]:
        assert self.page
        identity = await self.page.evaluate(
            """
            () => {
              const meta = name => document.querySelector(`meta[name="${name}"],meta[property="${name}"]`)?.content || '';
              const title = (document.querySelector('h1')?.textContent || document.title || '').replace(/\\s+/g,' ').trim();
              const description = (meta('description') || meta('og:description') || '').replace(/\\s+/g,' ').trim();
              const text = (document.body?.innerText || '').replace(/\\s+/g,' ').trim();
              const links = [...document.querySelectorAll('a[href]')].slice(0, 120).map(a => a.href || '').filter(Boolean);
              return {
                title: title.slice(0, 180),
                description: description.slice(0, 500),
                text_sample: text.slice(0, 900),
                public_links: links.slice(0, 40),
                verified: document.querySelector('[aria-label*="вериф"],[class*="Verified"],[class*="verified"]') !== null
              };
            }
            """
        )
        links = identity.get("public_links") if isinstance(identity, dict) else []
        if isinstance(links, list):
            identity["public_links"] = [link for link in links if is_safe_public_link(str(link))][:40]
        return identity

    async def _find_member_surface_navigation_target(self, classification: dict[str, Any]) -> dict[str, Any]:
        assert self.page
        expected_path = str((classification or {}).get("path") or "").lower()
        return await self.page.evaluate(
            """
            (expectedPath) => {
              const memberText = /(участник|участники|подписчик|подписчики|members|subscribers)/i;
              const reservedScopes = 'nav,header,aside,[role="navigation"],[role="complementary"],[id*="side"],[class*="side"]';
              const candidates = [...document.querySelectorAll('a[href]')].filter(a => {
                if (!(a instanceof HTMLElement) || a.offsetParent === null) return false;
                if (a.closest(reservedScopes)) return false;
                const text = (a.innerText || a.textContent || a.getAttribute('aria-label') || '').replace(/\\s+/g, ' ').trim();
                if (!memberText.test(text + ' ' + a.href)) return false;
                try {
                  const u = new URL(a.href, location.origin);
                  const p = u.pathname.replace(/^\\/+|\\/+$/g, '').toLowerCase();
                  if (!['vk.com','www.vk.com','vk.ru','www.vk.ru'].includes(u.hostname)) return false;
                  if (p !== String(expectedPath || '').toLowerCase()) return false;
                  const marker = `${u.search} ${u.hash}`.toLowerCase();
                  return /(act|section|tab)=members|subscribers|members|subscribers|участник|подписчик/.test(marker);
                } catch {
                  return false;
                }
              });
              const target = candidates[0];
              if (!target) {
                return {
                  status: 'MEMBER_INDEX_UNAVAILABLE',
                  reason: 'no_safe_explicit_member_surface_link',
                  url: '',
                  initiator: {strategy: 'explicit_member_surface_link_required', candidates: 0}
                };
              }
              return {
                status: 'MEMBER_SURFACE_LINK_FOUND',
                reason: 'safe_explicit_member_surface_link',
                url: target.href,
                initiator: {
                  tag: target.tagName,
                  role: target.getAttribute('role') || '',
                  text: (target.innerText || target.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80),
                  href: target.href
                }
              };
            }
            """,
            expected_path,
        )

    async def _audit_member_collection_surface(self) -> dict[str, Any]:
        assert self.page
        return await self._find_member_list_container({})

    async def _find_member_list_container(
        self,
        classification: dict[str, Any] | None = None,
        current_user_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        assert self.page
        expected_path = str((classification or {}).get("path") or "").lower()
        return await self.page.evaluate(
            """
            ({expectedPath, currentUserPaths}) => {
              const currentUsers = new Set((currentUserPaths || []).map(v => String(v || '').toLowerCase()).filter(Boolean));
              document.querySelectorAll('[data-social-radar-member-container="1"]')
                .forEach(el => el.removeAttribute('data-social-radar-member-container'));
              document.documentElement.removeAttribute('data-social-radar-member-surface-document');

              const text = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
              const lower = text.toLowerCase();
              const url = location.href;
              const parsed = new URL(location.href);
              const path = parsed.pathname.replace(/^\\/+|\\/+$/g, '').toLowerCase();
              const query = parsed.searchParams;
              const hasMemberQuery = query.get('act') === 'members'
                || query.get('section') === 'members'
                || query.get('tab') === 'members';
              const forbiddenPath = !path
                || /^id\\d+$/i.test(path)
                || ['feed','friends','im','groups','photos','audios','videos','settings','support','login','join','away','edit'].includes(path)
                || /^(wall|photo|video|clip|market|album|doc)/i.test(path);
              const unexpectedCommunity = Boolean(expectedPath && path && path !== expectedPath);
              const personProfileRoute = /^id\\d+$/i.test(path) || (!hasMemberQuery && !unexpectedCommunity && /^[a-z0-9_.-]{3,64}$/i.test(path) && path !== expectedPath);
              const memberTerms = /(участник|участники|подписчик|подписчики|members|subscribers)/i.test(text);
              const wallTerms = /(записи сообщества|новости сообщества|wall|публикации|предложить новость|комментарии|репост)/i.test(text);
              const postNodes = document.querySelectorAll('[id^="post-"],[data-post-id],article[class*="Post"],div[class*="post"]').length;
              const reserved = new Set([
                '', 'feed','friends','im','groups','albums','photos','video','music','apps',
                'settings','support','search','login','join','away','wall','market','clips',
                'stories','bookmarks','notifications','docs','edit'
              ]);
              const isProfileAnchor = (a) => {
                try {
                  const u = new URL(a.href, location.origin);
                  const p = u.pathname.replace(/^\\/+|\\/+$/g, '');
                  if (!['vk.com','www.vk.com','vk.ru','www.vk.ru'].includes(u.hostname)) return false;
                  if (!p || reserved.has(p.toLowerCase()) || p.includes('/')) return false;
                  if (/^(wall|photo|video|clip|market|album|doc)/i.test(p)) return false;
                  return /^id\\d+$/i.test(p) || /^[A-Za-z0-9_.]{3,64}$/i.test(p);
                } catch { return false; }
              };
              const anchorPath = (a) => {
                try { return new URL(a.href, location.origin).pathname.replace(/^\\/+|\\/+$/g, '').toLowerCase(); }
                catch { return ''; }
              };
              const containers = [...document.querySelectorAll(
                '[data-testid*="member"], [data-testid*="Member"], [data-testid*="subscriber"], [data-testid*="Subscriber"], ' +
                '[data-testid*="user"], [data-testid*="User"], [role="list"], section, ul, ol, div'
              )].filter(el => {
                if (!(el instanceof HTMLElement) || el.offsetParent === null) return false;
                if (['BODY','MAIN'].includes(el.tagName) || el.getAttribute('role') === 'main') return false;
                if (el.closest('nav,header,aside,[role="navigation"],[role="complementary"],[id*="side"],[class*="side"]')) return false;
                return true;
              });
              const scored = [];
              for (const el of containers) {
                const anchors = [...el.querySelectorAll('a[href]')].filter(isProfileAnchor).length;
                const currentUserAnchorCount = [...el.querySelectorAll('a[href]')].filter(a => currentUsers.has(anchorPath(a))).length;
                const cardLike = el.querySelectorAll('[role="listitem"], li, [data-testid*="member"], [data-testid*="user"], [class*="Member"], [class*="User"]').length;
                const t = (el.innerText || '').replace(/\\s+/g, ' ').slice(0, 600);
                const memberMarker = /(участник|участники|подписчик|подписчики|members|subscribers)/i.test(t);
                const wallMarker = /(записи сообщества|новости сообщества|предложить новость|комментарии|репост)/i.test(t);
                const operatorMenuMarker = /(профиль|лента|мессенджер|звонки|друзья|сообщества|музыка|видео|клипы|игры)/i.test(t);
                const style = getComputedStyle(el);
                const scrollable = ['auto','scroll','overlay'].includes(style.overflowY) && el.scrollHeight > el.clientHeight + 80;
                if (anchors < 1 || wallMarker) continue;
                if (operatorMenuMarker && !memberMarker) continue;
                if (currentUserAnchorCount > 0 && !memberMarker) continue;
                const score = anchors * 60 + cardLike * 12 + (memberMarker ? 80 : 0) + (scrollable ? 40 : 0);
                scored.push({
                  el,
                  score,
                  anchors,
                  cardLike,
                  currentUserAnchorCount,
                  memberMarker,
                  scrollable,
                  tag: el.tagName,
                  id: el.id || '',
                  cls: String(el.className || '').slice(0, 160),
                  scrollHeight: el.scrollHeight,
                  clientHeight: el.clientHeight
                });
              }
              scored.sort((a,b) => b.score - a.score);
              const best = scored[0] || null;
              const pageProfileAnchors = [...document.querySelectorAll('a[href]')].filter(isProfileAnchor).length;
              const surfaceDetected = Boolean(hasMemberQuery && !forbiddenPath && !unexpectedCommunity);
              const wallFeedDetected = Boolean((wallTerms || postNodes > 0) && !best);
              if (!surfaceDetected) {
                return {
                  url,
                  expected_path: expectedPath,
                  current_path: path,
                  collection_surface: 'WALL_OR_UNKNOWN',
                  surface_detected: false,
                  surface_verified: false,
                  surface_status: personProfileRoute ? 'UNEXPECTED_NAVIGATION' : unexpectedCommunity ? 'UNRELATED_COMMUNITY' : forbiddenPath ? 'UNEXPECTED_NAVIGATION' : 'MEMBER_INDEX_UNAVAILABLE',
                  member_terms_visible: memberTerms,
                  wall_terms_visible: wallTerms,
                  wall_feed_detected: wallFeedDetected || wallTerms || postNodes > 0,
                  profile_anchor_count: pageProfileAnchors,
                  member_container_found: false,
                  strict_container_selector: '',
                  scroll_target_scope: '',
                  wall_or_feed_rejected: true
                };
              }
              if (best) {
                best.el.dataset.socialRadarMemberContainer = '1';
                const surface = memberTerms || best.memberMarker ? 'COMMUNITY_MEMBERS' : 'COMMUNITY_SUBSCRIBERS';
                const verified = Boolean((memberTerms || best.memberMarker) && best.anchors >= 2);
                return {
                  url,
                  expected_path: expectedPath,
                  current_path: path,
                  collection_surface: surface,
                  surface_detected: true,
                  surface_verified: verified,
                  surface_status: verified ? 'SURFACE_VERIFIED' : 'MEMBER_CONTAINER_NOT_FOUND',
                  member_terms_visible: memberTerms,
                  wall_terms_visible: wallTerms,
                  wall_feed_detected: false,
                  profile_anchor_count: pageProfileAnchors,
                  list_item_count: best.cardLike,
                  member_container_found: true,
                  current_user_header_link_inside: best.currentUserAnchorCount > 0 && !best.memberMarker,
                  strict_container_selector: 'data-social-radar-member-container',
                  scroll_target_scope: best.scrollable ? 'MEMBER_CONTAINER' : 'MEMBER_CONTAINER_STATIC',
                  scroll_target_tag: best.tag,
                  scroll_target_id: best.id,
                  scroll_target_class: best.cls,
                  scrollHeight: best.scrollHeight,
                  clientHeight: best.clientHeight,
                  has_member_query: hasMemberQuery,
                  wall_or_feed_rejected: false
                };
              }
              const pageListItems = document.querySelectorAll('[role="listitem"], li, [data-testid*="member"], [data-testid*="user"]').length;
              if (hasMemberQuery && memberTerms && pageProfileAnchors > 0 && pageListItems > 0 && !wallTerms && postNodes === 0) {
                document.documentElement.dataset.socialRadarMemberSurfaceDocument = '1';
                return {
                  url,
                  expected_path: expectedPath,
                  current_path: path,
                  collection_surface: 'COMMUNITY_SUBSCRIBERS',
                  surface_detected: true,
                  surface_verified: true,
                  surface_status: 'SURFACE_VERIFIED_DOCUMENT',
                  member_terms_visible: memberTerms,
                  wall_terms_visible: wallTerms,
                  wall_feed_detected: false,
                  profile_anchor_count: pageProfileAnchors,
                  list_item_count: pageListItems,
                  member_container_found: true,
                  current_user_header_link_inside: false,
                  strict_container_selector: 'MEMBER_SURFACE_DOCUMENT',
                  scroll_target_scope: 'MEMBER_SURFACE_DOCUMENT',
                  scroll_target_tag: 'DOCUMENT',
                  scrollHeight: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
                  clientHeight: window.innerHeight,
                  has_member_query: hasMemberQuery,
                  wall_or_feed_rejected: false
                };
              }
              return {
                url,
                expected_path: expectedPath,
                current_path: path,
                collection_surface: 'WALL_OR_UNKNOWN',
                surface_detected: true,
                surface_verified: false,
                surface_status: wallFeedDetected ? 'WALL_FEED_DETECTED' : 'MEMBER_CONTAINER_NOT_FOUND',
                member_terms_visible: memberTerms,
                wall_terms_visible: wallTerms,
                wall_feed_detected: wallFeedDetected,
                profile_anchor_count: pageProfileAnchors,
                list_item_count: pageListItems,
                member_container_found: false,
                current_user_header_link_inside: false,
                strict_container_selector: '',
                scroll_target_scope: '',
                has_member_query: hasMemberQuery,
                wall_or_feed_rejected: true
              };
            }
            """,
            {"expectedPath": expected_path, "currentUserPaths": current_user_paths or []},
        )

    async def _wait_for_member_list_container(
        self,
        classification: dict[str, Any],
        *,
        current_user_paths: list[str],
        operation: CollectorOperation | None,
        navigation_trace: list[dict[str, Any]],
        attempts: int = 10,
    ) -> dict[str, Any]:
        last: dict[str, Any] = {}
        for attempt in range(1, max(1, attempts) + 1):
            last = await self._find_member_list_container(classification, current_user_paths)
            self._append_navigation_trace(
                navigation_trace,
                "SURFACE_CHECK",
                operation=operation,
                reason=f"member_container_readiness_attempt_{attempt}:{last.get('surface_status') or ''}",
                extra={
                    "collection_surface": last.get("collection_surface"),
                    "surface_detected": bool(last.get("surface_detected")),
                    "surface_verified": bool(last.get("surface_verified")),
                    "member_container_found": bool(last.get("member_container_found")),
                    "current_user_header_link_inside": bool(last.get("current_user_header_link_inside")),
                    "profile_anchor_count": int(last.get("profile_anchor_count") or 0),
                    "list_item_count": int(last.get("list_item_count") or 0),
                },
            )
            if last.get("surface_verified"):
                return last
            if last.get("surface_status") in {
                "UNEXPECTED_NAVIGATION",
                "UNRELATED_COMMUNITY",
                "OPERATOR_PROFILE_NAVIGATION",
                "PERSON_PROFILE_NAVIGATION",
                "FEED_NAVIGATION",
                "WALL_FEED_DETECTED",
                "MEMBER_CONTAINER_SCOPE_INVALID",
            }:
                return last
            await asyncio.sleep(0.8)
        return last

    async def _extract_member_cards_from_container(self, current_user_paths: list[str] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        assert self.page
        payload = await self.page.evaluate(
            """
            (currentUserPaths) => {
              const currentUsers = new Set((currentUserPaths || []).map(v => String(v || '').toLowerCase()).filter(Boolean));
              const reserved = new Set([
                '', 'feed','friends','im','groups','albums','photos','video','music','apps',
                'settings','support','search','login','join','away','wall','market','clips',
                'stories','bookmarks','notifications','docs','edit'
              ]);
              const container = document.querySelector('[data-social-radar-member-container="1"]');
              const documentSurface = document.documentElement.dataset.socialRadarMemberSurfaceDocument === '1';
              const scope = container || (documentSurface ? document : null);
              if (!scope) {
                return {items: [], raw_seen: 0, raw_valid_candidates: 0, invalid_card_rejected: 0, container_found: false};
              }
              const isProfileAnchor = (a) => {
                try {
                  const u = new URL(a.href, location.origin);
                  const p = u.pathname.replace(/^\\/+|\\/+$/g, '');
                  if (!['vk.com','www.vk.com','vk.ru','www.vk.ru'].includes(u.hostname)) return null;
                  if (!p || reserved.has(p.toLowerCase()) || p.includes('/')) return null;
                  if (/^(wall|photo|video|clip|market|album|doc)/i.test(p)) return null;
                  if (/^id\\d+$/i.test(p) || /^[A-Za-z0-9_.]{3,64}$/i.test(p)) return {url:u, path:p};
                  return null;
                } catch { return null; }
              };
              const isCurrentUserOutsideMemberCard = (path, card) => {
                if (!currentUsers.has(String(path || '').toLowerCase())) return false;
                const text = (card?.innerText || '').replace(/\\s+/g, ' ').toLowerCase();
                return !/(участник|участники|подписчик|подписчики|members|subscribers)/i.test(text)
                  && Boolean(card?.closest('header,nav,aside,[role="navigation"],[role="complementary"],[id*="side"],[class*="side"],[class*="LeftMenu"],[class*="Top"],[class*="Header"]'));
              };
              const anchors = [...scope.querySelectorAll('a[href]')];
              const items = [];
              let invalid = 0;
              for (const a of anchors) {
                if (!(a instanceof HTMLElement) || a.offsetParent === null) continue;
                if (a.closest('nav,header,aside,[role="navigation"],[role="complementary"],[id*="side"],[class*="side"]')) continue;
                const parsed = isProfileAnchor(a);
                if (!parsed) continue;
                const card = a.closest('[role="listitem"], li, [data-testid*="member"], [data-testid*="user"], [class*="Member"], [class*="User"], div');
                if (!card || !(card instanceof HTMLElement) || card.offsetParent === null) {
                  invalid++;
                  continue;
                }
                if (card.closest('article,[id^="post-"],[data-post-id],div[class*="post"],div[class*="Post"]')) {
                  invalid++;
                  continue;
                }
                if (isCurrentUserOutsideMemberCard(parsed.path, card)) {
                  invalid++;
                  continue;
                }
                const cardText = (card.innerText || '').replace(/\\s+/g,' ').trim();
                const candidates = [
                  a.getAttribute('aria-label'),
                  a.textContent,
                  card.querySelector('[data-testid*="name"], [class*="Name"], h1,h2,h3,h4,strong')?.textContent,
                  cardText
                ].filter(Boolean).map(v => v.replace(/\\s+/g,' ').trim());
                const name = candidates.find(v =>
                  v.length >= 2 &&
                  v.length <= 100 &&
                  !/^https?:/i.test(v) &&
                  !/^(друзья|подписчики|сообщения|написать|удалить|ещё|еще|меню|поиск)$/i.test(v)
                ) || '';
                if (!name) {
                  invalid++;
                  continue;
                }
                items.push({
                  path: parsed.path,
                  href: parsed.url.origin + parsed.url.pathname,
                  name,
                  is_numeric: /^id\\d+$/i.test(parsed.path),
                  text_sample: cardText.slice(0,180),
                  member_card_verified: true
                });
              }
              return {
                items,
                raw_seen: anchors.length,
                raw_valid_candidates: items.length,
                invalid_card_rejected: invalid,
                container_found: true
              };
            }
            """,
            current_user_paths or [],
        )
        return payload.get("items", []), {key: value for key, value in payload.items() if key != "items"}

    async def _click_member_load_more_if_present(self) -> dict[str, Any]:
        assert self.page
        return await self.page.evaluate(
            """
            () => {
              const container = document.querySelector('[data-social-radar-member-container="1"]');
              const documentSurface = document.documentElement.dataset.socialRadarMemberSurfaceDocument === '1';
              const scope = container || (documentSurface ? document : null);
              if (!scope) return {clicked:false, status:'MEMBER_CONTAINER_NOT_FOUND'};
              const controls = [...scope.querySelectorAll('button, a, [role="button"]')].filter(el => {
                if (!(el instanceof HTMLElement) || el.offsetParent === null) return false;
                if (el.closest('nav,header,aside,[role="navigation"],[role="complementary"],article,[id^="post-"],[data-post-id]')) return false;
                if (el.matches('a[href]')) {
                  try {
                    const u = new URL(el.href, location.origin);
                    const p = u.pathname.replace(/^\\/+|\\/+$/g, '');
                    if (/^id\\d+$/i.test(p) || /^[A-Za-z0-9_.]{3,64}$/i.test(p)) return false;
                  } catch {}
                }
                const text = (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                return /^(показать ещё|показать еще|ещё|еще|more|show more)$/.test(text);
              });
              const target = controls[0];
              if (!target) return {clicked:false, status:'NO_MEMBER_LOAD_MORE'};
              const meta = {
                tag: target.tagName,
                role: target.getAttribute('role') || '',
                text: (target.innerText || target.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80),
                href: target instanceof HTMLAnchorElement ? target.href : '',
                inside_member_container: Boolean(container && container.contains(target))
              };
              target.click();
              return {clicked:true, status:'MEMBER_LOAD_MORE_CLICK', initiator: meta};
            }
            """
        )

    async def _scroll_member_container_once(self, surface: dict[str, Any]) -> dict[str, Any]:
        assert self.page
        return await self.page.evaluate(
            """
            (scopeKind) => {
              const before = {
                y: window.scrollY,
                height: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
                url: location.href
              };
              const container = document.querySelector('[data-social-radar-member-container="1"]');
              let moved = false;
              if (container instanceof HTMLElement && scopeKind !== 'MEMBER_SURFACE_DOCUMENT') {
                const top = container.scrollTop;
                container.scrollTop = Math.min(container.scrollHeight, container.scrollTop + Math.max(520, container.clientHeight * 0.8));
                container.dispatchEvent(new Event('scroll', {bubbles:true}));
                moved = container.scrollTop !== top;
                return {
                  scope: 'MEMBER_CONTAINER',
                  moved,
                  before_top: top,
                  after_top: container.scrollTop,
                  height: container.scrollHeight,
                  client_height: container.clientHeight,
                  url: location.href
                };
              }
              if (scopeKind === 'MEMBER_SURFACE_DOCUMENT') {
                window.scrollBy(0, Math.max(700, window.innerHeight * 0.82));
                return {
                  scope: 'MEMBER_SURFACE_DOCUMENT',
                  moved: window.scrollY !== before.y,
                  before_top: before.y,
                  after_top: window.scrollY,
                  height: before.height,
                  client_height: window.innerHeight,
                  url: location.href
                };
              }
              return {scope: scopeKind || '', moved: false, before_top: 0, after_top: 0, height: 0, client_height: 0, url: location.href};
            }
            """,
            surface.get("scroll_target_scope") or "",
        )

    async def _collect_member_index_strict(
        self,
        classification: dict[str, Any],
        *,
        current_user_paths: list[str],
        max_rounds: int,
        max_profiles: int,
        operation: CollectorOperation | None,
        navigation_trace: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        assert self.page
        accumulated: dict[str, dict[str, Any]] = {}
        raw_seen = 0
        raw_valid_candidates = 0
        invalid_card_rejected = 0
        duplicates_removed = 0
        stable_rounds = 0
        previous_unique = -1
        rounds = 0
        load_more_clicks = 0
        member_scroll_rounds = 0
        wall_feed_scroll_rounds = 0
        profile_navigation_count = 0
        person_profile_navigation_count = 0
        operator_profile_navigation_count = 0
        unexpected_navigation_count = 0
        failure_status = ""
        navigation_initiator = ""
        max_rounds = max(1, min(int(max_rounds or 180), 2000))

        for rounds in range(1, max_rounds + 1):
            if operation and operation.cancel_requested:
                failure_status = "CANCELLED"
                self._mark_operation_progress(operation, state="CANCELLED", current_scroll=rounds)
                break

            before_surface_url = self.page.url
            surface = await self._find_member_list_container(classification, current_user_paths)
            surface_invariant = await self._check_stage_a_url_invariant(
                cause="DOM_ROUTER_NAVIGATION",
                before_url=before_surface_url,
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=navigation_trace,
                operation=operation,
                initiator={"phase": "before_extract_surface_check"},
            )
            if not surface_invariant.get("ok"):
                failure_status = str(surface_invariant.get("status") or "UNEXPECTED_NAVIGATION")
                navigation_initiator = "DOM_ROUTER_NAVIGATION"
                unexpected_navigation_count += 1
                if failure_status == "OPERATOR_PROFILE_NAVIGATION":
                    operator_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    person_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status == "WALL_FEED_DETECTED":
                    wall_feed_scroll_rounds += 1
                break
            self._append_navigation_trace(
                navigation_trace,
                "SURFACE_CHECK",
                operation=operation,
                reason=str(surface.get("surface_status") or ""),
                extra={
                    "collection_surface": surface.get("collection_surface"),
                    "surface_verified": bool(surface.get("surface_verified")),
                    "scroll_target_scope": surface.get("scroll_target_scope") or "",
                    "member_container_found": bool(surface.get("member_container_found")),
                },
            )
            if not surface.get("surface_verified"):
                failure_status = str(surface.get("surface_status") or "PARSER_DEGRADED")
                if failure_status in {"UNEXPECTED_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    unexpected_navigation_count += 1
                    profile_navigation_count += 1
                    person_profile_navigation_count += 1
                    navigation_initiator = "DOM_ROUTER_NAVIGATION"
                elif failure_status == "OPERATOR_PROFILE_NAVIGATION":
                    unexpected_navigation_count += 1
                    profile_navigation_count += 1
                    operator_profile_navigation_count += 1
                    navigation_initiator = "DOM_ROUTER_NAVIGATION"
                if surface.get("wall_feed_detected"):
                    wall_feed_scroll_rounds += 1
                break

            before_extract_url = self.page.url
            raw, extraction_report = await self._extract_member_cards_from_container(current_user_paths)
            extract_invariant = await self._check_stage_a_url_invariant(
                cause="DOM_ROUTER_NAVIGATION",
                before_url=before_extract_url,
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=navigation_trace,
                operation=operation,
                initiator={"phase": "after_extract"},
            )
            if not extract_invariant.get("ok"):
                failure_status = str(extract_invariant.get("status") or "UNEXPECTED_NAVIGATION")
                navigation_initiator = "DOM_ROUTER_NAVIGATION"
                unexpected_navigation_count += 1
                if failure_status == "OPERATOR_PROFILE_NAVIGATION":
                    operator_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    person_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status == "WALL_FEED_DETECTED":
                    wall_feed_scroll_rounds += 1
                break
            raw_seen += int(extraction_report.get("raw_seen") or len(raw))
            raw_valid_candidates += int(extraction_report.get("raw_valid_candidates") or len(raw))
            invalid_card_rejected += int(extraction_report.get("invalid_card_rejected") or 0)

            for item in raw:
                path = item.get("path", "")
                name = self._clean_name(item.get("name") or item.get("text_sample") or "")
                if path.lower() in RESERVED_PATHS or not name:
                    invalid_card_rejected += 1
                    continue
                numeric = re.fullmatch(r"id(\d+)", path, flags=re.I)
                candidate = {
                    "vk_id": int(numeric.group(1)) if numeric else None,
                    "screen_name": None if numeric else path,
                    "full_name": name,
                    "profile_url": item["href"],
                }
                old = accumulated.get(path)
                if old is not None:
                    duplicates_removed += 1
                if old is None or len(candidate["full_name"]) < len(old["full_name"]):
                    accumulated[path] = candidate
                if len(accumulated) >= max_profiles:
                    break

            self._mark_operation_progress(
                operation,
                members_discovered=len(accumulated),
                members_deduped=len(accumulated),
                current_scroll=rounds,
                current_offset=len(accumulated),
                diagnostics={
                    "last_progress_at": self._utc_now(),
                    "stage_a_profile_navigation_count": profile_navigation_count,
                    "stage_a_person_profile_navigation_count": person_profile_navigation_count,
                    "stage_a_operator_profile_navigation_count": operator_profile_navigation_count,
                    "stage_a_unexpected_navigation_count": unexpected_navigation_count,
                    "stage_a_wall_feed_scroll_rounds": wall_feed_scroll_rounds,
                    "stage_a_member_scroll_rounds": member_scroll_rounds,
                    "stage_a_profiles_deep_opened": 0,
                    "collection_surface": surface.get("collection_surface"),
                    "surface_status": surface.get("surface_status"),
                },
            )

            if len(accumulated) >= max_profiles:
                break

            if surface.get("scroll_target_scope") == "MEMBER_CONTAINER_STATIC":
                failure_status = "PARSER_DEGRADED"
                navigation_initiator = "STATIC_MEMBER_CONTAINER"
                break

            if len(accumulated) == previous_unique:
                stable_rounds += 1
            else:
                stable_rounds = 0
            previous_unique = len(accumulated)

            before_click_url = self.page.url
            click_report = await self._click_member_load_more_if_present()
            self._append_navigation_trace(
                navigation_trace,
                "CLICK_ATTEMPT",
                operation=operation,
                reason=str(click_report.get("status") or ""),
                extra={"initiator": click_report.get("initiator") or {}, "clicked": bool(click_report.get("clicked"))},
            )
            click_invariant = await self._check_stage_a_url_invariant(
                cause="MEMBER_LOAD_MORE_CLICK" if click_report.get("clicked") else "DOM_ROUTER_NAVIGATION",
                before_url=before_click_url,
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=navigation_trace,
                operation=operation,
                initiator=click_report.get("initiator") if isinstance(click_report.get("initiator"), dict) else {},
            )
            if not click_invariant.get("ok"):
                failure_status = str(click_invariant.get("status") or "UNEXPECTED_NAVIGATION")
                navigation_initiator = "MEMBER_LOAD_MORE_CLICK" if click_report.get("clicked") else "DOM_ROUTER_NAVIGATION"
                unexpected_navigation_count += 1
                if failure_status == "OPERATOR_PROFILE_NAVIGATION":
                    operator_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    person_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status == "WALL_FEED_DETECTED":
                    wall_feed_scroll_rounds += 1
                break
            if click_report.get("clicked"):
                load_more_clicks += 1
                stable_rounds = 0

            before_surface_scroll_url = self.page.url
            surface_before_scroll = await self._find_member_list_container(classification, current_user_paths)
            pre_scroll_invariant = await self._check_stage_a_url_invariant(
                cause="DOM_ROUTER_NAVIGATION",
                before_url=before_surface_scroll_url,
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=navigation_trace,
                operation=operation,
                initiator={"phase": "before_scroll_surface_check"},
            )
            if not pre_scroll_invariant.get("ok"):
                failure_status = str(pre_scroll_invariant.get("status") or "UNEXPECTED_NAVIGATION")
                navigation_initiator = "DOM_ROUTER_NAVIGATION"
                unexpected_navigation_count += 1
                if failure_status == "OPERATOR_PROFILE_NAVIGATION":
                    operator_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    person_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status == "WALL_FEED_DETECTED":
                    wall_feed_scroll_rounds += 1
                break
            self._append_navigation_trace(
                navigation_trace,
                "SURFACE_CHECK",
                operation=operation,
                reason="before_scroll",
                extra={
                    "collection_surface": surface_before_scroll.get("collection_surface"),
                    "surface_verified": bool(surface_before_scroll.get("surface_verified")),
                    "scroll_target_scope": surface_before_scroll.get("scroll_target_scope") or "",
                },
            )
            if not surface_before_scroll.get("surface_verified"):
                failure_status = str(surface_before_scroll.get("surface_status") or "MEMBER_SURFACE_LOST")
                if surface_before_scroll.get("wall_feed_detected"):
                    wall_feed_scroll_rounds += 1
                navigation_initiator = "DOM_ROUTER_NAVIGATION"
                break

            before_scroll_url = self.page.url
            scroll_result = await self._scroll_member_container_once(surface_before_scroll)
            if scroll_result.get("scope") in {"MEMBER_CONTAINER", "MEMBER_SURFACE_DOCUMENT"}:
                member_scroll_rounds += 1
            else:
                wall_feed_scroll_rounds += 1
                failure_status = "WALL_FEED_DETECTED"
                navigation_initiator = "MEMBER_CONTAINER_SCROLL"
                break
            self._append_navigation_trace(
                navigation_trace,
                "SCROLL_MEMBER_CONTAINER",
                operation=operation,
                reason=str(scroll_result.get("scope") or ""),
                extra={"moved": bool(scroll_result.get("moved")), "round": rounds},
            )
            await asyncio.sleep(0.55)
            scroll_invariant = await self._check_stage_a_url_invariant(
                cause="MEMBER_CONTAINER_SCROLL",
                before_url=before_scroll_url,
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=navigation_trace,
                operation=operation,
                initiator={"scope": scroll_result.get("scope"), "moved": bool(scroll_result.get("moved"))},
            )
            if not scroll_invariant.get("ok"):
                failure_status = str(scroll_invariant.get("status") or "UNEXPECTED_NAVIGATION")
                navigation_initiator = "MEMBER_CONTAINER_SCROLL"
                unexpected_navigation_count += 1
                if failure_status == "OPERATOR_PROFILE_NAVIGATION":
                    operator_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    person_profile_navigation_count += 1
                    profile_navigation_count += 1
                elif failure_status == "WALL_FEED_DETECTED":
                    wall_feed_scroll_rounds += 1
                break

            if stable_rounds >= 12:
                break

        items = sorted(accumulated.values(), key=lambda x: x["full_name"].lower())
        self._append_navigation_trace(
            navigation_trace,
            "STAGE_A_COMPLETE" if not failure_status else "STAGE_A_STOPPED",
            operation=operation,
            reason=failure_status or "strict_member_index_complete",
            extra={"profiles": len(items), "rounds": rounds},
        )
        report = {
            "scroll_rounds": rounds,
            "scroll_target_kind": "strict_member_surface",
            "scroll_target_scope": "MEMBER_CONTAINER_OR_MEMBER_SURFACE_DOCUMENT",
            "load_more_clicks": load_more_clicks,
            "raw_candidates_seen": raw_seen,
            "raw_seen": raw_seen,
            "raw_valid_candidates": raw_valid_candidates,
            "normalized": len(items),
            "deduped_normalized": len(items),
            "encoding_rejected": 0,
            "invalid_card_rejected": invalid_card_rejected,
            "duplicates_removed": duplicates_removed,
            "unique_profiles": len(items),
            "numeric_ids": sum(1 for item in items if item["vk_id"] is not None),
            "screen_names": sum(1 for item in items if item["screen_name"]),
            "stopped_after_stable_rounds": stable_rounds,
            "extractor": "strict_member_surface_accumulator_v1",
            "stage_a_profile_navigation_count": profile_navigation_count,
            "stage_a_person_profile_navigation_count": person_profile_navigation_count,
            "stage_a_operator_profile_navigation_count": operator_profile_navigation_count,
            "stage_a_unexpected_navigation_count": unexpected_navigation_count,
            "stage_a_wall_feed_scroll_rounds": wall_feed_scroll_rounds,
            "stage_a_member_scroll_rounds": member_scroll_rounds,
            "stage_a_profiles_deep_opened": 0,
            "stage_a_failure_status": failure_status,
            "stage_a_navigation_initiator": navigation_initiator or ("NONE" if not failure_status else "UNKNOWN_NAVIGATION"),
            "generic_main_body_fallback_used": False,
            "browser_stayed_on_member_surface": not failure_status,
            "operator_personal_profile_opened_during_stage_a": operator_profile_navigation_count > 0,
            "person_profile_opened_during_stage_a": person_profile_navigation_count > 0,
            "wall_or_feed_scrolled_during_stage_a": wall_feed_scroll_rounds > 0,
        }
        return items, report

    @staticmethod
    def _normalize_public_org_profile(
        item: dict[str, Any],
        *,
        source_url: str,
        source_type: str,
        observed_at: str,
        collection_surface: str,
    ) -> dict[str, Any]:
        return {
            "vk_user_id": item.get("vk_id"),
            "profile_url": item.get("profile_url"),
            "display_name": item.get("full_name") or "",
            "public_work": "",
            "public_position": "",
            "public_city": "",
            "public_contacts": [],
            "public_links": [],
            "public_bio": "",
            "observed_at": observed_at,
            "source_context": {
                "source": "vk",
                "source_url": source_url,
                "source_type": source_type,
                "relation": "public_community_member_index_entry",
                "collection_surface": collection_surface,
                "membership_is_employment_proof": False,
            },
        }

    async def collect_public_organization_source(
        self,
        source_url: str,
        options: dict[str, Any] | None = None,
        operation: CollectorOperation | None = None,
    ) -> dict[str, Any]:
        options = options or {}
        classification = classify_public_vk_source(source_url)
        max_profiles = max(1, min(int(options.get("max_member_index") or options.get("max_profiles") or 7000), 20_000))
        max_scrolls = max(1, min(int(options.get("max_pages") or options.get("max_scrolls") or 800), 2_000))
        max_candidate_profile_enrichment = max(0, min(int(options.get("max_candidate_profile_enrichment") or 30), 200))
        max_ambiguous_profile_enrichment = max(0, min(int(options.get("max_ambiguous_profile_enrichment") or 10), 100))
        timeout_ms = max(5_000, min(int(options.get("timeout_ms") or 30_000), 60_000))
        observed_at = datetime.now().isoformat(timespec="seconds")
        result = {
            "source": "vk",
            "source_url": classification.get("normalized_url") or source_url,
            "original_source_url": source_url,
            "source_type": classification.get("source_type"),
            "collection_surface": "COMMUNITY_MEMBERS",
            "collection_surface_verified": False,
            "source_identity": {},
            "source_validation_signals": [],
            "profiles": [],
            "member_index": {
                "strategy": "cheap_member_index_scan",
                "profiles": [],
                "requested_limit": max_profiles,
                "deep_profile_opened_for_all_members": False,
            },
            "candidate_enrichment": {
                "strategy": "bounded_candidate_only",
                "max_candidate_profile_enrichment": max_candidate_profile_enrichment,
                "max_ambiguous_profile_enrichment": max_ambiguous_profile_enrichment,
                "profiles_enriched": 0,
                "stage_b_profiles_requested": 0,
                "stage_b_profiles_opened": 0,
                "stage_b_profiles_completed": 0,
            },
            "pagination": {"max_profiles": max_profiles, "max_scrolls": max_scrolls, "timeout_ms": timeout_ms},
            "navigation_trace": [],
            "stage_a_counters": {
                "stage_a_profile_navigation_count": 0,
                "stage_a_person_profile_navigation_count": 0,
                "stage_a_operator_profile_navigation_count": 0,
                "stage_a_unexpected_navigation_count": 0,
                "stage_a_wall_feed_scroll_rounds": 0,
                "stage_a_member_scroll_rounds": 0,
                "stage_a_profiles_deep_opened": 0,
                "stage_a_navigation_initiator": "NONE",
            },
            "diagnostics": {
                "status": "QUEUED",
                "classifier": classification,
                "auth_state": "UNKNOWN",
                "captcha": False,
                "browser_required": True,
                "private_messages_excluded": True,
                "dialogs_excluded": True,
            },
        }
        if not classification.get("eligible_for_collection"):
            result["diagnostics"]["status"] = "REJECTED_SOURCE_TYPE"
            return result

        busy = self._active_busy_operation()
        if busy and busy is not operation:
            result["diagnostics"]["status"] = "COLLECTOR_BUSY"
            result["diagnostics"]["current_operation"] = {
                "operation_id": busy.operation_id,
                "operation_type": busy.operation_type,
                "state": busy.state,
            }
            return result

        async with self.lock:
            self._ensure_running()
            result["diagnostics"]["status"] = "CONNECTING"
            self._mark_operation_progress(operation, state="RUNNING", diagnostics={"status": "CONNECTING"})
            authenticated = await self._detect_authenticated()
            result["diagnostics"]["auth_state"] = "AUTHENTICATED" if authenticated else "AUTH_REQUIRED"
            if operation:
                operation.authenticated = authenticated
            if not authenticated:
                result["diagnostics"]["status"] = "AUTH_REQUIRED"
                self._mark_operation_progress(operation, state="AUTH_REQUIRED", diagnostics={"status": "AUTH_REQUIRED"})
                return result

            assert self.page
            self.page.set_default_navigation_timeout(timeout_ms)
            current_user_paths = await self._detect_current_user_profile_paths()
            self._arm_stage_a_navigation_observers(result["navigation_trace"], operation)
            self._append_navigation_trace(
                result["navigation_trace"],
                "STAGE_A_START",
                operation=operation,
                reason="strict_member_surface_collection_started",
                extra={"current_user_profile_paths_detected": len(current_user_paths)},
            )
            self._append_navigation_trace(result["navigation_trace"], "NAV", operation=operation, reason="organization_public_page")
            org_goto = await self._goto_stage_a(
                str(classification["normalized_url"]),
                cause="EXPLICIT_ORGANIZATION_GOTO",
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=result["navigation_trace"],
                operation=operation,
            )
            if not org_goto.get("ok"):
                result["diagnostics"]["status"] = str(org_goto.get("status") or "UNEXPECTED_NAVIGATION")
                result["stage_a_counters"]["stage_a_unexpected_navigation_count"] = 1
                result["stage_a_counters"]["stage_a_navigation_initiator"] = "EXPLICIT_ORGANIZATION_GOTO"
                if result["diagnostics"]["status"] == "OPERATOR_PROFILE_NAVIGATION":
                    result["stage_a_counters"]["stage_a_operator_profile_navigation_count"] = 1
                    result["stage_a_counters"]["stage_a_profile_navigation_count"] = 1
                elif result["diagnostics"]["status"] in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    result["stage_a_counters"]["stage_a_person_profile_navigation_count"] = 1
                    result["stage_a_counters"]["stage_a_profile_navigation_count"] = 1
                self._append_navigation_trace(
                    result["navigation_trace"],
                    "STAGE_A_STOPPED",
                    operation=operation,
                    reason=result["diagnostics"]["status"],
                    extra=result["stage_a_counters"],
                )
                self._mark_operation_progress(operation, state="PARSER_DEGRADED", diagnostics={"status": result["diagnostics"]["status"]})
                return result
            result["diagnostics"]["status"] = "DOWNLOADING"
            self._mark_operation_progress(operation, state="RUNNING", diagnostics={"status": "DOWNLOADING"})
            guard = await self._detect_captcha_or_block()
            result["diagnostics"].update({k: guard.get(k) for k in ("captcha", "auth_required", "blocked")})
            if guard.get("captcha"):
                result["diagnostics"]["status"] = "CAPTCHA_REQUIRED"
                self._mark_operation_progress(operation, state="BLOCKED", diagnostics={"status": "CAPTCHA_REQUIRED"})
                return result
            if guard.get("blocked"):
                result["diagnostics"]["status"] = "BLOCKED"
                self._mark_operation_progress(operation, state="BLOCKED", diagnostics={"status": "BLOCKED"})
                return result

            result["diagnostics"]["status"] = "PARSING"
            identity = await self._extract_public_source_identity()
            result["source_identity"] = identity
            member_target = await self._find_member_surface_navigation_target(classification)
            result["member_index"]["member_surface_navigation"] = {
                "status": member_target.get("status"),
                "reason": member_target.get("reason"),
                "explicit_link_required": True,
            }
            self._append_navigation_trace(
                result["navigation_trace"],
                "MEMBER_SURFACE_TARGET",
                operation=operation,
                reason=str(member_target.get("status") or ""),
                extra={"initiator": member_target.get("initiator") or {}},
            )
            member_url = str(member_target.get("url") or "")
            if not member_url:
                result["diagnostics"]["status"] = "MEMBER_INDEX_UNAVAILABLE"
                result["diagnostics"]["reason"] = str(member_target.get("reason") or "safe member surface link was not found")
                result["pagination"] = {
                    **result["pagination"],
                    "stage_a_failure_status": "MEMBER_INDEX_UNAVAILABLE",
                    "stage_a_navigation_initiator": "EXPLICIT_MEMBER_SURFACE_LINK_REQUIRED",
                    "generic_main_body_fallback_used": False,
                    "browser_stayed_on_member_surface": True,
                    "operator_personal_profile_opened_during_stage_a": False,
                    "person_profile_opened_during_stage_a": False,
                    "wall_or_feed_scrolled_during_stage_a": False,
                }
                result["stage_a_counters"]["stage_a_navigation_initiator"] = "EXPLICIT_MEMBER_SURFACE_LINK_REQUIRED"
                self._append_navigation_trace(
                    result["navigation_trace"],
                    "STAGE_A_STOPPED",
                    operation=operation,
                    reason="MEMBER_INDEX_UNAVAILABLE",
                    extra=result["stage_a_counters"],
                )
                self._mark_operation_progress(operation, state="PARSER_DEGRADED", diagnostics={"status": "MEMBER_INDEX_UNAVAILABLE"})
                return result
            self._append_navigation_trace(result["navigation_trace"], "NAV", operation=operation, reason="member_surface_route", url=member_url)
            member_goto = await self._goto_stage_a(
                member_url,
                cause="EXPLICIT_MEMBER_SURFACE_GOTO",
                classification=classification,
                current_user_paths=current_user_paths,
                navigation_trace=result["navigation_trace"],
                operation=operation,
            )
            if not member_goto.get("ok"):
                result["diagnostics"]["status"] = str(member_goto.get("status") or "UNEXPECTED_NAVIGATION")
                result["stage_a_counters"]["stage_a_unexpected_navigation_count"] = 1
                result["stage_a_counters"]["stage_a_navigation_initiator"] = "EXPLICIT_MEMBER_SURFACE_GOTO"
                if result["diagnostics"]["status"] == "OPERATOR_PROFILE_NAVIGATION":
                    result["stage_a_counters"]["stage_a_operator_profile_navigation_count"] = 1
                    result["stage_a_counters"]["stage_a_profile_navigation_count"] = 1
                elif result["diagnostics"]["status"] in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}:
                    result["stage_a_counters"]["stage_a_person_profile_navigation_count"] = 1
                    result["stage_a_counters"]["stage_a_profile_navigation_count"] = 1
                self._append_navigation_trace(
                    result["navigation_trace"],
                    "STAGE_A_STOPPED",
                    operation=operation,
                    reason=result["diagnostics"]["status"],
                    extra=result["stage_a_counters"],
                )
                self._mark_operation_progress(operation, state="PARSER_DEGRADED", diagnostics={"status": result["diagnostics"]["status"]})
                return result
            surface_audit = await self._wait_for_member_list_container(
                classification,
                current_user_paths=current_user_paths,
                operation=operation,
                navigation_trace=result["navigation_trace"],
            )
            self._append_navigation_trace(
                result["navigation_trace"],
                "SURFACE",
                operation=operation,
                reason=str(surface_audit.get("surface_status") or ""),
                extra={
                    "collection_surface": surface_audit.get("collection_surface"),
                    "surface_detected": bool(surface_audit.get("surface_detected")),
                    "surface_verified": bool(surface_audit.get("surface_verified")),
                    "member_container_found": bool(surface_audit.get("member_container_found")),
                    "scroll_target_scope": surface_audit.get("scroll_target_scope") or "",
                },
            )
            result["collection_surface"] = surface_audit["collection_surface"]
            result["collection_surface_verified"] = bool(surface_audit["surface_verified"])
            result["surface_audit"] = surface_audit
            result["member_index"]["collection_surface"] = surface_audit["collection_surface"]
            result["member_index"]["surface_verified"] = bool(surface_audit["surface_verified"])
            result["member_index"]["surface_status"] = surface_audit["surface_status"]
            result["diagnostics"]["collection_surface"] = surface_audit["collection_surface"]
            result["diagnostics"]["surface_status"] = surface_audit["surface_status"]
            self._mark_operation_progress(
                operation,
                state="RUNNING" if surface_audit["surface_verified"] else "PARSER_DEGRADED",
                diagnostics={
                    "status": "MEMBER_SURFACE_AUDITED",
                    "collection_surface": surface_audit["collection_surface"],
                    "surface_status": surface_audit["surface_status"],
                },
            )
            if not surface_audit["surface_verified"]:
                result["diagnostics"]["status"] = surface_audit.get("surface_status") or "MEMBER_INDEX_UNAVAILABLE"
                url_status = self._stage_url_status(self.page.url, classification, current_user_paths)
                operator_navigation = url_status.get("status") == "OPERATOR_PROFILE_NAVIGATION"
                person_navigation = url_status.get("status") in {"PERSON_PROFILE_NAVIGATION", "UNRELATED_COMMUNITY"}
                unexpected_navigation = result["diagnostics"]["status"] in {
                    "UNEXPECTED_NAVIGATION",
                    "UNRELATED_COMMUNITY",
                    "OPERATOR_PROFILE_NAVIGATION",
                    "PERSON_PROFILE_NAVIGATION",
                }
                wall_feed_detected = bool(surface_audit.get("wall_feed_detected")) or result["diagnostics"]["status"] == "WALL_FEED_DETECTED"
                result["stage_a_counters"] = {
                    "stage_a_profile_navigation_count": 1 if (operator_navigation or person_navigation) else 0,
                    "stage_a_person_profile_navigation_count": 1 if person_navigation else 0,
                    "stage_a_operator_profile_navigation_count": 1 if operator_navigation else 0,
                    "stage_a_unexpected_navigation_count": 1 if unexpected_navigation else 0,
                    "stage_a_wall_feed_scroll_rounds": 1 if wall_feed_detected else 0,
                    "stage_a_member_scroll_rounds": 0,
                    "stage_a_profiles_deep_opened": 0,
                    "stage_a_navigation_initiator": "DOM_ROUTER_NAVIGATION" if unexpected_navigation else "NONE",
                }
                result["pagination"] = {
                    **result["pagination"],
                    "stage_a_profile_navigation_count": result["stage_a_counters"]["stage_a_profile_navigation_count"],
                    "stage_a_person_profile_navigation_count": result["stage_a_counters"]["stage_a_person_profile_navigation_count"],
                    "stage_a_operator_profile_navigation_count": result["stage_a_counters"]["stage_a_operator_profile_navigation_count"],
                    "stage_a_unexpected_navigation_count": result["stage_a_counters"]["stage_a_unexpected_navigation_count"],
                    "stage_a_wall_feed_scroll_rounds": result["stage_a_counters"]["stage_a_wall_feed_scroll_rounds"],
                    "stage_a_member_scroll_rounds": 0,
                    "stage_a_profiles_deep_opened": 0,
                    "stage_a_failure_status": result["diagnostics"]["status"],
                    "generic_main_body_fallback_used": False,
                    "browser_stayed_on_member_surface": False,
                    "operator_personal_profile_opened_during_stage_a": operator_navigation,
                    "person_profile_opened_during_stage_a": person_navigation,
                    "stage_a_navigation_initiator": result["stage_a_counters"]["stage_a_navigation_initiator"],
                    "wall_or_feed_scrolled_during_stage_a": wall_feed_detected,
                }
                self._append_navigation_trace(
                    result["navigation_trace"],
                    "STAGE_A_STOPPED",
                    operation=operation,
                    reason=result["diagnostics"]["status"],
                    extra=result["stage_a_counters"],
                )
                self._mark_operation_progress(operation, state="PARSER_DEGRADED", diagnostics={"status": result["diagnostics"]["status"]})
                return result
            result["source_validation_signals"] = [
                "vk_public_url_classified",
                "browser_profile_owned_by_vk_radar",
                "public_page_loaded",
                "community_member_surface_verified",
            ]
            items, report = await self._collect_member_index_strict(
                classification,
                current_user_paths=current_user_paths,
                max_rounds=max_scrolls,
                max_profiles=max_profiles,
                operation=operation,
                navigation_trace=result["navigation_trace"],
            )
            result["diagnostics"]["status"] = "EXTRACTING"
            failure_status = str(report.get("stage_a_failure_status") or "")
            if failure_status and failure_status != "CANCELLED":
                result["diagnostics"]["status"] = failure_status
                result["collection_surface_verified"] = False
                result["member_index"]["surface_verified"] = False
                result["pagination"] = {**result["pagination"], **report}
                result["stage_a_counters"] = {
                    "stage_a_profile_navigation_count": report.get("stage_a_profile_navigation_count", 0),
                    "stage_a_person_profile_navigation_count": report.get("stage_a_person_profile_navigation_count", 0),
                    "stage_a_operator_profile_navigation_count": report.get("stage_a_operator_profile_navigation_count", 0),
                    "stage_a_unexpected_navigation_count": report.get("stage_a_unexpected_navigation_count", 0),
                    "stage_a_wall_feed_scroll_rounds": report.get("stage_a_wall_feed_scroll_rounds", 0),
                    "stage_a_member_scroll_rounds": report.get("stage_a_member_scroll_rounds", 0),
                    "stage_a_profiles_deep_opened": report.get("stage_a_profiles_deep_opened", 0),
                    "stage_a_navigation_initiator": report.get("stage_a_navigation_initiator") or "NONE",
                }
                self._mark_operation_progress(operation, state="PARSER_DEGRADED", diagnostics={"status": failure_status})
                return result
            result["profiles"] = [
                self._normalize_public_org_profile(
                    item,
                    source_url=str(classification["normalized_url"]),
                    source_type=str(classification["source_type"]),
                    observed_at=observed_at,
                    collection_surface=str(surface_audit["collection_surface"]),
                )
                for item in items[:max_profiles]
            ]
            result["member_index"]["profiles"] = result["profiles"]
            result["member_index"]["members_discovered"] = len(items)
            result["member_index"]["members_normalized"] = len(result["profiles"])
            result["member_index"]["members_deduped"] = len(result["profiles"])
            result["member_index"]["raw_seen"] = int(report.get("raw_seen") or report.get("raw_candidates_seen") or 0)
            result["member_index"]["raw_valid_candidates"] = int(report.get("raw_valid_candidates") or len(items))
            result["member_index"]["normalized"] = len(result["profiles"])
            result["member_index"]["deduped_normalized"] = len(result["profiles"])
            result["member_index"]["encoding_rejected"] = int(report.get("encoding_rejected") or 0)
            result["member_index"]["invalid_card_rejected"] = int(report.get("invalid_card_rejected") or 0)
            result["member_index"]["duplicates_removed"] = int(report.get("duplicates_removed") or 0)
            result["pagination"] = {**result["pagination"], **report}
            result["stage_a_counters"] = {
                "stage_a_profile_navigation_count": report.get("stage_a_profile_navigation_count", 0),
                "stage_a_person_profile_navigation_count": report.get("stage_a_person_profile_navigation_count", 0),
                "stage_a_operator_profile_navigation_count": report.get("stage_a_operator_profile_navigation_count", 0),
                "stage_a_unexpected_navigation_count": report.get("stage_a_unexpected_navigation_count", 0),
                "stage_a_wall_feed_scroll_rounds": report.get("stage_a_wall_feed_scroll_rounds", 0),
                "stage_a_member_scroll_rounds": report.get("stage_a_member_scroll_rounds", 0),
                "stage_a_profiles_deep_opened": report.get("stage_a_profiles_deep_opened", 0),
                "stage_a_navigation_initiator": report.get("stage_a_navigation_initiator") or "NONE",
            }
            if operation and operation.cancel_requested:
                result["diagnostics"]["status"] = "CANCELLED"
                self._mark_operation_progress(operation, state="CANCELLED")
                return result
            result["diagnostics"]["status"] = "EVIDENCE_CREATED" if result["profiles"] else "PARSER_DEGRADED"
            result["diagnostics"]["profiles_found"] = len(result["profiles"])
            self._mark_operation_progress(
                operation,
                state="RUNNING",
                members_discovered=len(items),
                members_deduped=len(result["profiles"]),
                current_offset=len(result["profiles"]),
                diagnostics={"status": result["diagnostics"]["status"]},
            )
            self.state.preview = result
            self.state.last_action = "collect_public_organization_source"
            preview_path = PREVIEW_DIR / f"preview_organization_source_{datetime.now():%Y%m%d_%H%M%S}.json"
            preview_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result

    async def start_organization_source_job(self, source_url: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        busy = self._active_busy_operation()
        if busy:
            return {
                "status": "COLLECTOR_BUSY",
                "state": "COLLECTOR_BUSY",
                "operation_id": "",
                "current_operation": {
                    "operation_id": busy.operation_id,
                    "operation_type": busy.operation_type,
                    "state": busy.state,
                },
            }
        operation_id = f"vk_org_members_{uuid4().hex[:16]}"
        now = self._utc_now()
        operation = CollectorOperation(
            operation_id=operation_id,
            operation_type="organization_source_member_index",
            source_url=source_url,
            collection_surface="COMMUNITY_MEMBERS",
            state="QUEUED",
            started_at=now,
            updated_at=now,
            safe_diagnostics={"status": "QUEUED", "profile_path_visible_to_client": False},
        )
        self.operations[operation_id] = operation
        self.active_operation_id = operation_id
        asyncio.create_task(self._run_organization_source_job(operation, options or {}))
        return operation.to_safe_dict()

    async def _run_organization_source_job(self, operation: CollectorOperation, options: dict[str, Any]) -> None:
        self._mark_operation_progress(operation, state="RUNNING", diagnostics={"status": "RUNNING"})
        try:
            if operation.cancel_requested:
                self._mark_operation_progress(operation, state="CANCELLED")
                return
            if not self.context or not self.page:
                self._mark_operation_progress(operation, diagnostics={"status": "STARTING_BROWSER"})
                await self.start()
            result = await self.collect_public_organization_source(operation.source_url, options, operation=operation)
            operation.result = result
            operation.result_available = True
            operation.collection_surface = str(result.get("collection_surface") or operation.collection_surface)
            operation.members_discovered = int((result.get("member_index") or {}).get("members_discovered") or 0)
            operation.members_deduped = int((result.get("member_index") or {}).get("members_deduped") or len(result.get("profiles") or []))
            operation.profiles_enriched = int((result.get("candidate_enrichment") or {}).get("profiles_enriched") or 0)
            status = str((result.get("diagnostics") or {}).get("status") or "")
            operation.authenticated = str((result.get("diagnostics") or {}).get("auth_state") or "") == "AUTHENTICATED"
            if operation.cancel_requested or status == "CANCELLED":
                state = "CANCELLED"
            elif status == "AUTH_REQUIRED":
                state = "AUTH_REQUIRED"
            elif status in {"CAPTCHA_REQUIRED", "BLOCKED"}:
                state = "BLOCKED"
            elif status in {
                "MEMBER_INDEX_UNAVAILABLE",
                "MEMBER_CONTAINER_NOT_FOUND",
                "MEMBER_CONTAINER_LOST",
                "MEMBER_SURFACE_LOST",
                "UNEXPECTED_NAVIGATION",
                "UNRELATED_COMMUNITY",
                "WALL_FEED_DETECTED",
                "PARSER_DEGRADED",
                "DOM_CHANGED",
                "OPERATOR_PROFILE_NAVIGATION",
                "PERSON_PROFILE_NAVIGATION",
                "FEED_NAVIGATION",
                "MEMBER_CONTAINER_SCOPE_INVALID",
                "MEMBER_LOAD_MORE_UNSAFE",
            }:
                state = "PARSER_DEGRADED"
            elif status == "EVIDENCE_CREATED":
                state = "COMPLETED"
            else:
                state = "FAILED"
            operation.safe_diagnostics.update({
                "status": status,
                "collection_surface": result.get("collection_surface"),
                "surface_status": (result.get("surface_audit") or {}).get("surface_status"),
                "profiles_found": len(result.get("profiles") or []),
            })
            self._mark_operation_progress(operation, state=state)
        except Exception as exc:
            operation.last_error = str(exc)
            operation.result = {
                "source": "vk",
                "source_url": operation.source_url,
                "profiles": [],
                "member_index": {"profiles": [], "members_discovered": operation.members_discovered, "members_deduped": operation.members_deduped},
                "diagnostics": {"status": "COLLECTION_FAILED", "reason": str(exc), "auth_state": "UNKNOWN"},
            }
            operation.result_available = True
            self._mark_operation_progress(operation, state="FAILED", diagnostics={"status": "COLLECTION_FAILED"})
        finally:
            operation.finished_at = self._utc_now()
            operation.updated_at = operation.finished_at
            if self.active_operation_id == operation.operation_id:
                self.active_operation_id = None

    async def get_organization_source_job(self, operation_id: str) -> dict[str, Any]:
        operation = self.operations.get(operation_id)
        if not operation:
            raise KeyError("operation_not_found")
        return operation.to_safe_dict()

    async def get_organization_source_job_result(self, operation_id: str) -> dict[str, Any]:
        operation = self.operations.get(operation_id)
        if not operation:
            raise KeyError("operation_not_found")
        if operation.state not in TERMINAL_OPERATION_STATES:
            return {"operation": operation.to_safe_dict(), "result_available": False}
        return {"operation": operation.to_safe_dict(), "result_available": operation.result_available, "result": operation.result or {}}

    async def cancel_organization_source_job(self, operation_id: str) -> dict[str, Any]:
        operation = self.operations.get(operation_id)
        if not operation:
            raise KeyError("operation_not_found")
        operation.cancel_requested = True
        operation.updated_at = self._utc_now()
        if operation.state == "QUEUED":
            operation.state = "CANCELLED"
            operation.finished_at = operation.updated_at
        return operation.to_safe_dict()

    @staticmethod
    def _clean_name(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"\b(online|был[аи]? в сети.*|написать сообщение|добавить в друзья)\b.*", "", value, flags=re.I).strip()
        if len(value) > 100:
            value = value[:100].strip()
        return value

    async def _find_dialog_scroll_target(self) -> dict[str, Any]:
        assert self.page
        return await self.page.evaluate(
            """
            () => {
              document.querySelectorAll('[data-social-radar-dialog-scroll="1"]')
                .forEach(el => el.removeAttribute('data-social-radar-dialog-scroll'));

              const row = document.querySelector(
                '[data-itemkey^="convo_"] button[role="listitem"], ' +
                '[data-itemkey^="convo_"], button[role="listitem"]'
              );

              if (!row) return {kind:'not_found', rows:0, scrollHeight:0, clientHeight:0, cls:'', ancestor_chain:[]};

              const chain = [];
              let el = row;
              let selected = null;

              while (el && el !== document.body && chain.length < 18) {
                if (el instanceof HTMLElement) {
                  const style = getComputedStyle(el);
                  const info = {
                    tag: el.tagName,
                    cls: String(el.className || '').slice(0,180),
                    id: el.id || '',
                    overflowY: style.overflowY,
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight,
                    scrollTop: el.scrollTop,
                    rows: el.querySelectorAll('[data-itemkey^="convo_"],button[role="listitem"]').length
                  };
                  chain.push(info);

                  if (!selected &&
                      ['auto','scroll','overlay'].includes(style.overflowY) &&
                      el.scrollHeight > el.clientHeight + 40) {
                    selected = el;
                  }
                }
                el = el.parentElement;
              }

              if (!selected) {
                el = row.parentElement;
                while (el && el !== document.body) {
                  if (el instanceof HTMLElement && el.scrollHeight > el.clientHeight + 120) {
                    selected = el;
                    break;
                  }
                  el = el.parentElement;
                }
              }

              if (!selected) selected = row.closest('.ConvoList,[class*="ConvoList"]');

              if (selected instanceof HTMLElement) {
                selected.dataset.socialRadarDialogScroll = '1';
                return {
                  kind:'element',
                  rows:selected.querySelectorAll('[data-itemkey^="convo_"],button[role="listitem"]').length,
                  scrollHeight:selected.scrollHeight,
                  clientHeight:selected.clientHeight,
                  scrollTop:selected.scrollTop,
                  cls:String(selected.className || '').slice(0,180),
                  tag:selected.tagName,
                  ancestor_chain:chain
                };
              }

              return {
                kind:'window',
                rows:document.querySelectorAll('[data-itemkey^="convo_"],button[role="listitem"]').length,
                scrollHeight:document.documentElement.scrollHeight,
                clientHeight:window.innerHeight,
                scrollTop:window.scrollY,
                cls:'',
                tag:'WINDOW',
                ancestor_chain:chain
              };
            }
            """
        )

    async def _extract_visible_dialogs(self) -> list[dict[str, Any]]:
        assert self.page
        return await self.page.evaluate("""
        () => {
          const scope=document.querySelector('[data-social-radar-dialog-scroll="1"]')||document.querySelector('.ConvoList')||document.body;
          let rows=[...scope.querySelectorAll('[data-itemkey^="convo_"]')];
          if(!rows.length) rows=[...scope.querySelectorAll('button[role="listitem"]')];
          return rows.map(w=>{
            const row=w.matches('button[role="listitem"]')?w:(w.querySelector('button[role="listitem"]')||w);
            const key=w.getAttribute('data-itemkey')||row.closest('[data-itemkey]')?.getAttribute('data-itemkey')||'';
            const m=key.match(/^convo_(-?\\d+)$/);
            const t=row.querySelector('.ConvoTitle__author,[title].ConvoTitle__author,h3[title]');
            const img=row.querySelector('img[alt]');
            const title=(t?.getAttribute('title')||t?.textContent||img?.getAttribute('alt')||'').replace(/\\s+/g,' ').trim();
            const mb=row.querySelector('.ConvoListItem__message');
            const preview=(row.querySelector('.MessagePreview')?.textContent||mb?.getAttribute('title')||mb?.textContent||'').replace(/\\s+/g,' ').trim();
            const date=(row.querySelector('.ConvoListItem__date')?.textContent||'').replace(/\\s+/g,' ').trim();
            const counter=row.querySelector('[class*="unread"],[class*="Unread"],[class*="counter"],[class*="Counter"]');
            const ct=(counter?.textContent||'').trim();
            return {item_key:key,peer_id:m?Number(m[1]):null,full_name:title,preview,date_label:date,
              unread:Boolean(counter)||row.className.includes('unread')||w.className.includes('unread'),
              unread_count:/^\\d+$/.test(ct)?Number(ct):null,
              outgoing:row.querySelector('.ConvoListItem__outStatusIcon')!==null||/^(Вы:|You:)/i.test(mb?.getAttribute('title')||preview),
              avatar_url:img?.getAttribute('src')||'',verified:row.querySelector('[class*="verified"],[aria-label*="вериф"]')!==null,
              aria_posinset:Number(row.getAttribute('aria-posinset')||0)||null,
              aria_setsize:Number(row.getAttribute('aria-setsize')||0)||null};
          });
        }""")

    async def _scroll_dialog_list_once(self, target: dict[str, Any]) -> dict[str, Any]:
        assert self.page

        before = await self.page.evaluate(
            """
            () => {
              const el = document.querySelector('[data-social-radar-dialog-scroll="1"]');
              const rows = [...document.querySelectorAll('[data-itemkey^="convo_"]')];
              return {
                top: el?.scrollTop ?? window.scrollY,
                height: el?.scrollHeight ?? document.documentElement.scrollHeight,
                client: el?.clientHeight ?? window.innerHeight,
                first_key: rows[0]?.getAttribute('data-itemkey') || null,
                last_key: rows[rows.length - 1]?.getAttribute('data-itemkey') || null,
                rendered_rows: rows.length
              };
            }
            """
        )

        moved = False
        wheel_steps = 0

        try:
            last_row = self.page.locator(
                '[data-itemkey^="convo_"] button[role="listitem"], [data-itemkey^="convo_"]'
            ).last
            box = await last_row.bounding_box()
            if box:
                await self.page.mouse.move(
                    box["x"] + min(box["width"] * 0.45, 240),
                    box["y"] + min(box["height"] * 0.55, 35),
                )
                for _ in range(8):
                    await self.page.mouse.wheel(0, 360)
                    wheel_steps += 1
                    await asyncio.sleep(0.16)
                moved = True
        except Exception:
            pass

        if target.get("kind") == "element":
            await self.page.evaluate(
                """
                () => {
                  const el = document.querySelector('[data-social-radar-dialog-scroll="1"]');
                  if (!el) return;
                  const next = Math.min(el.scrollHeight, el.scrollTop + Math.max(520, el.clientHeight * 0.78));
                  el.scrollTo({top: next, behavior:'instant'});
                  el.dispatchEvent(new WheelEvent('wheel', {deltaY:720,bubbles:true,cancelable:true}));
                  el.dispatchEvent(new Event('scroll', {bubbles:true}));
                }
                """
            )

        await asyncio.sleep(0.9)

        after = await self.page.evaluate(
            """
            () => {
              const el = document.querySelector('[data-social-radar-dialog-scroll="1"]');
              const rows = [...document.querySelectorAll('[data-itemkey^="convo_"]')];
              return {
                top: el?.scrollTop ?? window.scrollY,
                height: el?.scrollHeight ?? document.documentElement.scrollHeight,
                client: el?.clientHeight ?? window.innerHeight,
                first_key: rows[0]?.getAttribute('data-itemkey') || null,
                last_key: rows[rows.length - 1]?.getAttribute('data-itemkey') || null,
                rendered_rows: rows.length
              };
            }
            """
        )

        changed = (
            before.get("top") != after.get("top")
            or before.get("first_key") != after.get("first_key")
            or before.get("last_key") != after.get("last_key")
        )

        if not changed:
            try:
                last_button = self.page.locator('button[role="listitem"]').last
                await last_button.focus()
                for _ in range(6):
                    await self.page.keyboard.press("ArrowDown")
                    await asyncio.sleep(0.12)
                await self.page.keyboard.press("PageDown")
                await asyncio.sleep(0.8)

                after = await self.page.evaluate(
                    """
                    () => {
                      const el = document.querySelector('[data-social-radar-dialog-scroll="1"]');
                      const rows = [...document.querySelectorAll('[data-itemkey^="convo_"]')];
                      return {
                        top: el?.scrollTop ?? window.scrollY,
                        height: el?.scrollHeight ?? document.documentElement.scrollHeight,
                        client: el?.clientHeight ?? window.innerHeight,
                        first_key: rows[0]?.getAttribute('data-itemkey') || null,
                        last_key: rows[rows.length - 1]?.getAttribute('data-itemkey') || null,
                        rendered_rows: rows.length
                      };
                    }
                    """
                )
                changed = (
                    before.get("top") != after.get("top")
                    or before.get("first_key") != after.get("first_key")
                    or before.get("last_key") != after.get("last_key")
                )
            except Exception:
                pass

        return {"moved": moved, "changed": changed, "wheel_steps": wheel_steps, "before": before, "after": after}

    async def _collect_dialogs(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        assert self.page
        target = await self._find_dialog_scroll_target()
        accumulated: dict[str, dict[str, Any]] = {}
        raw_seen = 0
        stable_rounds = 0
        no_scroll_rounds = 0
        previous_unique = -1
        previous_signature = None
        rounds = 0
        expected_size = None
        scroll_attempts = []

        for rounds in range(1, 321):
            rows = await self._extract_visible_dialogs()
            raw_seen += len(rows)

            visible_keys = []
            for item in rows:
                key = item.get("item_key") or (
                    f"peer_{item['peer_id']}" if item.get("peer_id") is not None else ""
                )
                title = self._clean_dialog_title(item.get("full_name") or "")
                if not key or not title:
                    continue

                visible_keys.append(key)
                item["full_name"] = title
                item["dialog_key"] = key
                item["dialog_url"] = (
                    f"https://vk.com/im?sel={item['peer_id']}"
                    if item.get("peer_id") is not None
                    else "https://vk.com/im"
                )
                accumulated[key] = item

                if item.get("aria_setsize"):
                    expected_size = max(expected_size or 0, item["aria_setsize"])

            signature = tuple(visible_keys)
            if len(accumulated) == previous_unique and signature == previous_signature:
                stable_rounds += 1
            else:
                stable_rounds = 0

            previous_unique = len(accumulated)
            previous_signature = signature

            # Trust aria-setsize only when it exceeds the initially visible chunk.
            # Some VK builds set it to the current rendered window (often 15).
            if expected_size and expected_size > max(20, target.get("rows") or 0):
                if len(accumulated) >= expected_size:
                    break

            scroll_result = await self._scroll_dialog_list_once(target)
            scroll_attempts.append(scroll_result)

            before = scroll_result.get("before")
            after = scroll_result.get("after")
            if not scroll_result.get("changed"):
                no_scroll_rounds += 1
            else:
                no_scroll_rounds = 0

            # We need a much stronger stop condition than "15 rows stayed stable".
            if stable_rounds >= 24 and no_scroll_rounds >= 8:
                break

        items = list(accumulated.values())
        items.sort(
            key=lambda x: (
                x.get("aria_posinset") if x.get("aria_posinset") is not None else 10**9,
                x["full_name"].lower(),
            )
        )

        report = {
            "scroll_rounds": rounds,
            "scroll_target_kind": target["kind"],
            "scroll_target_class": target.get("cls"),
            "scroll_target_tag": target.get("tag"),
            "scroll_target_initial_top": target.get("scrollTop"),
            "scroll_target_height": target.get("scrollHeight"),
            "scroll_target_client_height": target.get("clientHeight"),
            "scroll_target_ancestor_chain": target.get("ancestor_chain"),
            "initial_visible_rows": target.get("rows"),
            "raw_candidates_seen": raw_seen,
            "unique_dialogs": len(items),
            "expected_size_from_aria": expected_size,
            "numeric_peer_ids": sum(1 for item in items if item.get("peer_id") is not None),
            "unread_dialogs": sum(1 for item in items if item.get("unread")),
            "outgoing_last_message": sum(1 for item in items if item.get("outgoing")),
            "stopped_after_stable_rounds": stable_rounds,
            "no_scroll_rounds": no_scroll_rounds,
            "last_scroll_before": scroll_attempts[-1]["before"] if scroll_attempts else None,
            "last_scroll_after": scroll_attempts[-1]["after"] if scroll_attempts else None,
            "extractor": "vk_reforged_exact_scroll_ancestor_v4",
        }

        # Save diagnostics on every dialog run, including successful partial runs.
        await self._save_diagnostics("dialogs_success", report)

        return items, report

    @staticmethod
    def _clean_dialog_title(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"\b\d{1,2}:\d{2}\b.*$", "", value).strip()
        value = re.sub(r"\b(вчера|сегодня|online|был[аи]? в сети)\b.*$", "", value, flags=re.I).strip()
        return value[:100]

    async def _save_diagnostics(self, kind: str, report: dict[str, Any]) -> str:
        assert self.page
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = DIAGNOSTICS_DIR / f"{kind}_{timestamp}"
        html_path = base.with_suffix(".html")
        png_path = base.with_suffix(".png")
        json_path = base.with_suffix(".json")

        html_path.write_text(await self.page.content(), encoding="utf-8")
        await self.page.screenshot(path=str(png_path), full_page=True)
        json_path.write_text(
            json.dumps(
                {
                    "url": self.page.url,
                    "title": await self.page.title(),
                    "report": report,
                    "blocked_hosts": sorted(self.state.blocked_hosts),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(base)


collector = SafeVKCollector()
