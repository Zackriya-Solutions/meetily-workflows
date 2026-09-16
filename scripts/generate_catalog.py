#!/usr/bin/env python3
"""Generate the community-workflows catalog table from the manifests.

Reads every community-workflows/<id>/manifest.yaml, validates it against
community-workflows/manifest.schema.json, and rewrites the table between the
<!-- BEGIN CATALOG --> / <!-- END CATALOG --> markers in both the root README
and community-workflows/README.md.

Usage:
  python scripts/generate_catalog.py           # validate + write the tables
  python scripts/generate_catalog.py --check    # validate + fail if a table is stale (CI)

Requires: pyyaml, jsonschema (CI installs them; not needed by the examples).
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import Draft7Validator
except ImportError:
    sys.exit("generate_catalog.py needs pyyaml and jsonschema: pip install pyyaml jsonschema")

ROOT = Path(__file__).resolve().parents[1]
CW = ROOT / "community-workflows"
SCHEMA_PATH = CW / "manifest.schema.json"
BEGIN, END = "<!-- BEGIN CATALOG -->", "<!-- END CATALOG -->"
TARGETS = [ROOT / "README.md", CW / "README.md"]


def md_escape(text: str) -> str:
    """Escape text that goes into a Markdown table cell (contributor-controlled)."""
    out = str(text).replace("\\", "\\\\").replace("|", "\\|")
    out = out.replace("<", "&lt;").replace(">", "&gt;")
    return " ".join(out.split())  # collapse newlines/whitespace


def load_and_validate() -> tuple[list[dict], list[str]]:
    import json
    validator = Draft7Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    manifests, errors = [], []
    for mf in sorted(CW.glob("*/manifest.yaml")):
        folder = mf.parent.name
        try:
            data = yaml.safe_load(mf.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{mf}: invalid YAML: {e}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{mf}: top-level must be a mapping")
            continue
        for err in sorted(validator.iter_errors(data), key=str):
            errors.append(f"{mf}: {err.message}")
        if data.get("id") != folder:
            errors.append(f"{mf}: id '{data.get('id')}' must equal folder name '{folder}'")
        manifests.append(data)
    return manifests, errors


def render_table(manifests: list[dict]) -> str:
    if not manifests:
        return "_No community workflows listed yet. Be the first -- see the contributing guide._"
    lines = [
        "| Workflow | Trigger | Language | Scopes | Author |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in sorted(manifests, key=lambda d: d.get("id", "")):
        name = md_escape(m.get("name", m.get("id", "")))
        url = m.get("homepage") or m.get("source_url", "")
        link = f"[{name}]({url})" if url.startswith(("http://", "https://")) else name
        scopes = ", ".join(md_escape(s) for s in m.get("scopes", [])) or "read"
        lines.append(
            f"| {link} | `{md_escape(m.get('trigger',''))}` | {md_escape(m.get('language',''))} "
            f"| {scopes} | {md_escape(m.get('author',''))} |"
        )
    lines.append("")
    lines.append(f"_{len(manifests)} community workflow(s). Generated from `community-workflows/*/manifest.yaml` "
                 "by `scripts/generate_catalog.py` -- do not edit this table by hand._")
    return "\n".join(lines)


def splice(path: Path, table: str) -> str | None:
    """Return the new file content with the catalog block replaced, or None if markers are missing."""
    text = path.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return None
    pre = text.split(BEGIN)[0]
    post = text.split(END, 1)[1]
    return f"{pre}{BEGIN}\n{table}\n{END}{post}"


def main() -> int:
    check = "--check" in sys.argv[1:]
    manifests, errors = load_and_validate()
    if errors:
        print("Manifest validation FAILED:")
        for e in errors:
            print("  -", e)
        return 1
    table = render_table(manifests)
    stale = []
    for path in TARGETS:
        if not path.exists():
            print(f"skip (missing): {path}")
            continue
        new = splice(path, table)
        if new is None:
            print(f"WARNING: no catalog markers in {path}; skipping")
            continue
        if new != path.read_text(encoding="utf-8"):
            if check:
                stale.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(new, encoding="utf-8")
                print(f"updated {path.relative_to(ROOT)}")
    if check and stale:
        print("Catalog index is STALE (run scripts/generate_catalog.py and commit):")
        for s in stale:
            print("  -", s)
        return 1
    print(f"OK: {len(manifests)} manifest(s) valid" + (", index fresh" if check else ", index written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
