"""Small local trust-boundary policies; no network/DNS or application data access."""
from __future__ import annotations

import ipaddress
import re
import stat
import time
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit, urlunsplit

MAX_IMPORT_BYTES = 100 * 1024 * 1024
DIAGNOSTIC_MAX_AGE_SECONDS = 30 * 24 * 60 * 60


class PrivacyPolicyError(ValueError):
    pass


def local_llm_url(value: str) -> str:
    """Deny remote/LAN endpoints, ambiguous URL syntax and embedded secrets offline."""
    error = PrivacyPolicyError("LLM endpoint must be an HTTP(S) loopback URL without credentials, query or fragment")
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value:
        raise error
    try:
        url = urlsplit(value)
        host = url.hostname
        port = url.port
        if (url.scheme not in {'http', 'https'} or not host or url.username is not None or
                url.password is not None or '@' in url.netloc or '%' in url.netloc or
                '?' in value or '#' in value or not url.netloc or url.netloc.endswith(':') or port == 0):
            raise error
        if host.lower() == 'localhost':
            host = '127.0.0.1'  # no DNS dependency/rebinding for the alias
        else:
            address = ipaddress.ip_address(host)
            if not address.is_loopback or getattr(address, 'ipv4_mapped', None) is not None:
                raise error
            host = address.compressed
        if not re.fullmatch(r'(?:/[A-Za-z0-9._~-]+)*/?', url.path):
            raise error
        authority = f'[{host}]' if ':' in host else host
        if port is not None:
            authority += f':{port}'
        return urlunsplit((url.scheme, authority, url.path.rstrip('/'), '', ''))
    except (ValueError, TypeError):
        raise error from None


def safe_url_display(value: str) -> str:
    """Status/diagnostic URLs carry no credentials, query, fragment or profile path."""
    try:
        url = urlsplit(value)
        if url.scheme not in {'http', 'https'} or not url.hostname:
            return ''
        host = url.hostname
        if ':' in host: host = f'[{host}]'
        return f'{url.scheme}://{host}'
    except (ValueError, TypeError):
        return ''


def safe_directory(root: Path) -> Path:
    """Refuse symlinks and Windows reparse points, including any existing ancestor."""
    root = root.absolute()
    for path in (root, *root.parents):
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode) or
                getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise PrivacyPolicyError("Unsafe local storage path")
    if root.exists() and not root.is_dir():
        raise PrivacyPolicyError("Unsafe local storage path")
    return root


def upload_name(value: str) -> str:
    if (not isinstance(value, str) or not value or len(value) > 180 or value in {'.','..'} or
            any(c in value for c in '/\\:') or any(ord(c) < 32 for c in value) or
            Path(value).is_absolute() or PureWindowsPath(value).is_absolute()):
        raise PrivacyPolicyError("Invalid upload filename")
    stem = value.split('.')[0].upper()
    if stem in {'CON','PRN','AUX','NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}:
        raise PrivacyPolicyError("Invalid upload filename")
    if Path(value).suffix.lower() not in {'.json','.csv','.tsv','.html','.htm','.zip'}:
        raise PrivacyPolicyError("Unsupported import format")
    return re.sub(r'[^A-Za-zА-Яа-я0-9._-]+', '_', value)[:180]


def archive_member_name(value: str) -> None:
    path = PurePosixPath(value.replace('\\', '/'))
    if path.is_absolute() or PureWindowsPath(value).drive or '..' in path.parts or ':' in value:
        raise PrivacyPolicyError("Invalid archive member path")
    upload_name(path.name)  # Safe relative subdirectories are never extracted.


def prune_diagnostics(root: Path, *, now: float | None = None) -> int:
    """Only recognized direct diagnostic files; never recurse or touch symlink targets."""
    removed = 0
    try:
        root = safe_directory(root)
        if not root.exists(): return 0
        cutoff = (time.time() if now is None else now) - DIAGNOSTIC_MAX_AGE_SECONDS
        for path in root.iterdir():
            if not re.fullmatch(r'[a-z_]+_\d{8}_\d{6}(?:_[0-9a-f]+)?\.(?:json|html|png)', path.name):
                continue
            try:
                info = path.lstat()
                if (not stat.S_ISREG(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    continue
                if info.st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
    except (OSError, PrivacyPolicyError):
        return removed
    return removed


def diagnostic_summary(kind: str, report: dict) -> dict:
    allowed = {'items_found','profiles_found','scroll_rounds','duplicates_removed','raw_seen',
               'valid_count','invalid_count','rows_found','members_discovered','members_deduped'}
    return {'kind': kind if kind in {'friends','followers','dialogs','dialogs_success'} else 'collector',
            'counts': {key: value for key, value in report.items() if key in allowed and type(value) is int and value >= 0}}
