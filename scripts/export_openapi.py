"""Deterministic JSON-form YAML 1.2 export; no lifespan, DB or external calls.

Usage: python -B scripts/export_openapi.py [--check]
Authoring source: FastAPI route metadata and response models. Never edit output.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def render(schema):
    # JSON is a YAML 1.2 subset; stdlib parsing keeps the gate dependency-free.
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    from app.main import app
    expected = render(app.openapi())
    target = ROOT / "11_OPENAPI.yaml"
    if args.check:
        if target.read_text(encoding="utf-8") != expected:
            raise SystemExit("OpenAPI drift: regenerate 11_OPENAPI.yaml and review the diff")
        print("Canonical OpenAPI is current")
    else:
        target.write_text(expected, encoding="utf-8", newline="\n")
        print("Exported 11_OPENAPI.yaml (JSON-form YAML 1.2)")


if __name__ == "__main__":
    main()
