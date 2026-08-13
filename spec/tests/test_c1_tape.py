import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


def make_entry(**overrides):
    entry = {
        "schema_version": "1.0.0",
        "type": "entry",
        "id": "entry-001",
        "ts": "2026-08-13T10:00:00Z",
        "agent": "agent0",
        "run_id": "run-abc",
        "seq": 0,
        "kind": "ingest.source.collected",
        "data": {"source_id": "src-1", "uri": "https://example.com/doc"},
    }
    entry.update(overrides)
    return entry


def make_anchor(**overrides):
    anchor = {
        "schema_version": "1.0.0",
        "type": "anchor",
        "id": "anchor-001",
        "ts": "2026-08-13T10:00:01Z",
        "agent": "agent0",
        "run_id": "run-abc",
        "seq": 1,
        "phase": "Collect",
        "state": {"collected_count": 1},
        "prev_anchor": None,
    }
    anchor.update(overrides)
    return anchor


class TestEntryShape:
    def test_valid_entry_passes(self, c1_validator):
        c1_validator.validate(make_entry())

    def test_entry_with_rationale_and_supersedes_passes(self, c1_validator):
        c1_validator.validate(
            make_entry(
                id="entry-002",
                seq=2,
                rationale="corrected source uri after re-crawl",
                supersedes="entry-001",
                refs=["entry-001"],
            )
        )

    def test_missing_required_field_fails(self, c1_validator):
        entry = make_entry()
        del entry["kind"]
        with pytest.raises(ValidationError):
            c1_validator.validate(entry)

    def test_bad_kind_pattern_fails(self, c1_validator):
        with pytest.raises(ValidationError):
            c1_validator.validate(make_entry(kind="not-dotted"))

    def test_unknown_field_rejected(self, c1_validator):
        with pytest.raises(ValidationError):
            c1_validator.validate(make_entry(extra_field="nope"))


class TestAnchorShape:
    def test_valid_anchor_passes(self, c1_validator):
        c1_validator.validate(make_anchor())

    def test_anchor_missing_state_fails(self, c1_validator):
        anchor = make_anchor()
        del anchor["state"]
        with pytest.raises(ValidationError):
            c1_validator.validate(anchor)

    def test_anchor_type_mismatch_fails(self, c1_validator):
        with pytest.raises(ValidationError):
            c1_validator.validate(make_anchor(type="entry"))


class TestTapeRoundtrip:
    def test_jsonl_write_read_roundtrip(self, c1_validator, tmp_path: Path):
        lines = [
            make_entry(id="e1", seq=0),
            make_entry(id="e2", seq=1, kind="ingest.data.structured", data={"source_id": "src-1"}),
            make_anchor(id="a1", seq=2, prev_anchor=None),
        ]
        tape_file = tmp_path / "run-abc.jsonl"
        with open(tape_file, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(line) + "\n" for line in lines)

        read_back = []
        with open(tape_file, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                obj = json.loads(raw)
                c1_validator.validate(obj)
                read_back.append(obj)

        assert read_back == lines
        assert [line["seq"] for line in read_back] == [0, 1, 2]

    def test_supersede_never_deletes_only_appends(self, tmp_path: Path, c1_validator):
        original = make_entry(id="e1", seq=0, data={"value": "draft"})
        correction = make_entry(
            id="e2",
            seq=1,
            data={"value": "final"},
            supersedes="e1",
            rationale="fixed typo",
        )
        tape_file = tmp_path / "run-abc.jsonl"
        with open(tape_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(original) + "\n")
            f.write(json.dumps(correction) + "\n")

        with open(tape_file, "r", encoding="utf-8") as f:
            all_lines = [json.loads(l) for l in f if l.strip()]

        for line in all_lines:
            c1_validator.validate(line)

        # both the original and the correction remain on tape (append-only)
        assert len(all_lines) == 2
        ids = {line["id"] for line in all_lines}
        assert ids == {"e1", "e2"}

        # a view assembled over this range resolves supersede: only the
        # latest value for a given logical fact should be "live".
        superseded_ids = {line["supersedes"] for line in all_lines if "supersedes" in line}
        live_entries = [line for line in all_lines if line["id"] not in superseded_ids]
        assert [line["id"] for line in live_entries] == ["e2"]
        assert live_entries[0]["data"]["value"] == "final"


class TestView:
    def test_valid_view_passes(self, c1_validator):
        view = {
            "schema_version": "1.0.0",
            "run_id": "run-abc",
            "generated_at": "2026-08-13T10:05:00Z",
            "source_range": {"from_seq": 0, "to_seq": 2},
            "phase": "Collect",
            "entries": [make_entry()],
            "state": {"collected_count": 1},
        }
        view_validator = Draft202012Validator(
            {**c1_validator.schema, "$ref": "#/$defs/view"}
        )
        view_validator.validate(view)

    def test_view_missing_entries_fails(self, c1_validator):
        view_validator = Draft202012Validator(
            {**c1_validator.schema, "$ref": "#/$defs/view"}
        )
        view = {
            "schema_version": "1.0.0",
            "run_id": "run-abc",
            "generated_at": "2026-08-13T10:05:00Z",
            "source_range": {"from_seq": 0, "to_seq": 2},
            "state": {},
        }
        with pytest.raises(ValidationError):
            view_validator.validate(view)


class TestCrossVersionReading:
    @pytest.mark.parametrize("version", ["1.0.0", "1.1.0", "1.0.5"])
    def test_minor_patch_version_bumps_still_readable(self, c1_validator, version):
        """Same physical shape under a different schema_version (minor/patch bump)
        must still validate -- consumers should not need a schema swap for
        backward-compatible tape line versions."""
        c1_validator.validate(make_entry(schema_version=version))

    def test_malformed_version_string_fails(self, c1_validator):
        with pytest.raises(ValidationError):
            c1_validator.validate(make_entry(schema_version="v1"))
