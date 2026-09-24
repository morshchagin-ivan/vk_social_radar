"""Read-only tracked-artifact/obvious-secret guard. Prints file/category, never values."""
from __future__ import annotations
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def sensitive_name(name):
    path = PurePosixPath(name.replace('\\', '/').lower())
    if path.name == '.gitkeep': return False
    if path.parts and path.parts[0] in {'data', 'logs'}: return True
    return (path.name in {'cookies','cookies.txt','cookies.json','session.json','local state','login data'} or
            path.name == '.env' or path.name.startswith('.env.') and path.name != '.env.example' or
            any(path.name.endswith(s) for s in ('.db','.sqlite','.sqlite3','.db-wal','.db-shm','.db-journal','.sqlite-wal','.sqlite-shm')) or
            any(p in {'vk_browser_profile','collector_previews'} for p in path.parts))


def secret_categories(source):
    categories = set()
    if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', source): categories.add('private-key')
    if re.search(r'\b(?:sk-[A-Za-z0-9_-]{32,}|AKIA[A-Z0-9]{16}|ghp_[A-Za-z0-9]{36})\b', source): categories.add('token-literal')
    for match in re.finditer(r'''(?i)["']?(?:password|api_key|access_token|auth_token|secret_key)["']?\s*[:=]\s*["']([^"'\n]{8,})["']''', source):
        value=match[1].lower()
        if not any(x in value for x in ('synthetic','example','placeholder','dummy','test','not-for','your-')) and not any(x in value for x in ('{','[','\\','(','.get')):
            categories.add('credential-literal')
    return categories


def check(root=ROOT):
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=root).decode('utf-8').split('\0')
    findings=[]
    for name in filter(None,tracked):
        if sensitive_name(name): findings.append((name,'sensitive-runtime-artifact'))
        path=root/name
        if path.is_symlink() or path.is_junction():
            findings.append((name,'tracked-filesystem-link'))
            continue
        if not path.is_file(): continue
        if path.suffix.lower() in {'.py','.js','.html','.md','.yaml','.yml','.toml','.json','.bat','.ps1','.sh'}:
            # Fixture placeholders are synthetic, but real-format keys/tokens still fail.
            findings.extend((name,category) for category in secret_categories(path.read_text(encoding='utf-8',errors='replace')))
        if path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(path) as archive:
                    if any(sensitive_name(item.filename) for item in archive.infolist()):
                        findings.append((name,'archive-runtime-artifact'))
            except (OSError,zipfile.BadZipFile):
                findings.append((name,'archive-inventory-unavailable'))
    return sorted(set(findings))


if __name__ == '__main__':
    findings=check()
    for name,category in findings: print(f'{name}: {category}')
    print('Tracked privacy guard: ' + ('FAIL' if findings else 'PASS'))
    raise SystemExit(bool(findings))
