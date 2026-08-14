import json

import pytest
from jsonschema.exceptions import ValidationError

from sentinel_spec import conformance as C

EX = C.SPEC_ROOT / "examples"


def test_all_sample_entries_validate():
    entries = C.read_tape(EX / "tape_sample.jsonl")
    assert len(entries) >= 6
    for entry in entries:
        C.validate_entry(entry)


def test_roundtrip_preserves_entries(tmp_path):
    entries = C.read_tape(EX / "tape_sample.jsonl")
    out = tmp_path / "roundtrip.jsonl"
    C.write_tape(out, entries)
    assert C.read_tape(out) == entries


def test_entry_ids_unique():
    entries = C.read_tape(EX / "tape_sample.jsonl")
    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids))


def test_supersede_refs_point_to_earlier_entries():
    entries = C.read_tape(EX / "tape_sample.jsonl")
    seen: set[str] = set()
    for entry in entries:
        if "supersedes" in entry:
            assert entry["supersedes"] in seen, entry["id"]
        seen.add(entry["id"])


def test_anchor_requires_state_contract():
    bad = {
        "id": "bad-anchor",
        "schema_version": "0.1.0",
        "ts": "2026-08-13T00:00:00Z",
        "kind": "anchor",
        "actor": {"type": "system", "id": "k"},
        "payload": {"phase": "p"},  # missing summary / next_steps / source_ids
    }
    with pytest.raises(ValidationError):
        C.validate_entry(bad)


def test_view_drops_superseded_and_filters_kind_and_name():
    entries = C.read_tape(EX / "tape_sample.jsonl")
    view = json.loads((EX / "view_sample.json").read_text(encoding="utf-8"))
    C.validator("c1_view").validate(view)

    result = C.assemble_view(entries, view)
    ids = {e["id"] for e in result}

    assert "01E" not in ids  # finding superseded by note 01G
    assert "01B" not in ids  # ingest.* filtered out by redteam.* pattern
    assert "01A" not in ids  # anchor filtered out by kinds=[event]
    assert ids == {"01C", "01D", "01F", "01H"}
    assert all(e["kind"] == "event" for e in result)
