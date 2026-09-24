"""Offline checks for the repository's Markdown subset, not a Markdown/Mermaid parser."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
# These exact legacy audit lines record their original environment, not usable links.
HISTORICAL_PATH_LINES = {
    'docs/certification/00_REPOSITORY_AS_IS.md': {3},
    'docs/certification/01_ARCHITECTURE_INVENTORY.md': {3},
    'docs/certification/04_CERTIFICATION_READINESS.md': {3},
    'docs/certification/BASELINE_UPGRADE_REPORT.md': {3},
}


def check_document(path: Path, root: Path = ROOT) -> list[str]:
    text = path.read_text(encoding='utf-8-sig')
    name = path.relative_to(root).as_posix()
    issues = []
    fence = None
    language = ''
    body = []
    for number, line in enumerate(text.splitlines(), 1):
        if re.search(r'\b[A-Za-z]:[\\/]', line) and number not in HISTORICAL_PATH_LINES.get(name, set()):
            issues.append(f'{name}:{number}: absolute developer path')
        marker = re.match(r'^\s*(`{3,}|~{3,})(\w*)\s*$', line)
        if marker:
            if fence is None:
                fence, language, body = marker[1], marker[2], []
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2]:
                if language == 'mermaid':
                    nonempty = [part.strip() for part in body if part.strip() and not part.strip().startswith('%%')]
                    if not nonempty or not re.match(r'^(flowchart|graph|sequenceDiagram|stateDiagram-v2|classDiagram|erDiagram|C4Context|C4Container)\b', nonempty[0]):
                        issues.append(f'{name}:{number}: unsupported/empty Mermaid declaration')
                    if sum(part.startswith('subgraph ') for part in nonempty) != sum(part == 'end' for part in nonempty):
                        issues.append(f'{name}:{number}: unbalanced Mermaid subgraph')
                fence = None
            else:
                issues.append(f'{name}:{number}: malformed fence')
            continue
        if fence:
            body.append(line)
            continue
        # Inline links and reference definitions used in the maintained docs.
        targets = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', line)
        definition = re.match(r'^\s*\[[^\]]+\]:\s*(\S+)', line)
        if definition:
            targets.append(definition[1])
        for target in targets:
            target = target.strip().strip('<>')
            target = re.split(r'\s+[\"\']', target, maxsplit=1)[0]
            if target.startswith('#'):
                continue  # Local anchor semantics need a full Markdown parser.
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                if parsed.scheme not in {'http', 'https', 'mailto'}:
                    issues.append(f'{name}:{number}: non-portable link')
                continue  # No network/link checking of external sites.
            # Existing audit evidence uses repository-relative file.py:line links.
            relative_path = re.sub(r':\d+$', '', unquote(parsed.path))
            destination = (path.parent / relative_path).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                issues.append(f'{name}:{number}: missing/outside relative target')
    if fence:
        issues.append(f'{name}: unclosed fence')
    return issues


def documents(root: Path = ROOT) -> list[Path]:
    return sorted({root/'README.md', root/'12_API_GUIDE.md',
                   *root.glob('docs/certification/**/*.md'), *root.glob('docs/adr/**/*.md'),
                   *root.glob('tests/*.md')})


def check(root: Path = ROOT) -> list[str]:
    return [issue for path in documents(root) for issue in check_document(path, root)]


if __name__ == '__main__':
    findings = check()
    print('\n'.join(findings) if findings else 'Documentation links/fences: PASS')
    print('Mermaid formal validation: NOT AVAILABLE (structural sanity only)')
    raise SystemExit(bool(findings))
