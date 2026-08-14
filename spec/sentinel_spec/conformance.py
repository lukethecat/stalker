"""Reference conformance helpers for the sentinel-agents contracts.

Small, dependency-light (jsonschema only) reference implementation of:
  - loading and validating the C1/C2/C3 schemas
  - reading/writing a tape (JSONL, append-only)
  - assembling a C1 view (with supersede handling)
  - a semver major-based compatibility check for cross-version reads

This is a *spec* artifact: it defines what "conformant" means and is exercised
by the tests in ../tests. The kernel and plugins are separate implementations of
the same contracts.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SPEC_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = SPEC_ROOT / "schema"
SPEC_VERSION = "0.1.0"

_SCHEMA_FILES = {
    "c1_tape": "c1_tape.schema.json",
    "c1_view": "c1_view.schema.json",
    "c2_events": "c2_events.schema.json",
    "c3_skill": "c3_skill.schema.json",
}

_cache: dict[str, Draft202012Validator] = {}


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / _SCHEMA_FILES[name]).read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    if name not in _cache:
        schema = load_schema(name)
        Draft202012Validator.check_schema(schema)  # the schema itself must be valid
        _cache[name] = Draft202012Validator(schema)
    return _cache[name]


def validate_entry(entry: dict[str, Any]) -> None:
    """Validate one C1 tape entry. Event entries are cross-checked against C2."""
    validator("c1_tape").validate(entry)
    if entry.get("kind") == "event":
        validator("c2_events").validate(entry["payload"])


def read_tape(path: str | Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def write_tape(path: str | Path, entries: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def is_compatible(entry_version: str, reader_version: str = SPEC_VERSION) -> bool:
    """A reader can read any entry sharing its major version (semver)."""
    return entry_version.split(".")[0] == reader_version.split(".")[0]


def assemble_view(entries: list[dict[str, Any]], view: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive a context window from a tape per a C1 view query."""
    result = list(entries)

    if not view.get("include_superseded", False):
        superseded = {e["supersedes"] for e in entries if e.get("supersedes")}
        result = [e for e in result if e["id"] not in superseded]

    if "since_anchor" in view:
        idx = next((i for i, e in enumerate(result) if e["id"] == view["since_anchor"]), None)
        if idx is not None:
            result = result[idx:]

    if "kinds" in view:
        allowed = set(view["kinds"])
        result = [e for e in result if e["kind"] in allowed]

    if "event_names" in view:
        patterns = view["event_names"]

        def _match(e: dict[str, Any]) -> bool:
            if e.get("kind") != "event":
                return False
            name = e["payload"]["name"]
            return any(fnmatch.fnmatch(name, p) for p in patterns)

        result = [e for e in result if _match(e)]

    if "limit" in view:
        result = result[-view["limit"]:]

    return result
