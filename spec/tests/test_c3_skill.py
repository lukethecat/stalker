import pytest
from jsonschema import ValidationError


def make_skill(**overrides):
    skill = {
        "schema_version": "1.0.0",
        "name": "agent0-ipo-dispatcher",
        "description": "Watches the tape for new entries, matches C2 subscriptions, triggers a turn.",
        "version": "0.1.0",
        "namespace": "shared",
        "license": "Apache-2.0",
        "layers": {
            "l1_body": "SKILL.md",
            "l2_references": ["reference/dispatch-rules.md"],
            "l3_resources": ["scripts/dispatch.py"],
        },
        "mount_points": ["pre_turn"],
        "subscribes": ["redteam.target.registered", "ingest.source.collected"],
        "emits": ["redteam.probe.built"],
        "requires_authorization": True,
    }
    skill.update(overrides)
    return skill


class TestSkillManifestShape:
    def test_valid_skill_passes(self, c3_validator):
        c3_validator.validate(make_skill())

    def test_minimal_skill_without_optional_fields_passes(self, c3_validator):
        skill = make_skill()
        for optional_field in ["license", "mount_points", "allowed_tools", "requires_authorization"]:
            skill.pop(optional_field, None)
        c3_validator.validate(skill)

    def test_missing_l1_body_fails(self, c3_validator):
        skill = make_skill()
        del skill["layers"]["l1_body"]
        with pytest.raises(ValidationError):
            c3_validator.validate(skill)

    def test_bad_name_case_fails(self, c3_validator):
        with pytest.raises(ValidationError):
            c3_validator.validate(make_skill(name="Agent0_Dispatcher"))

    def test_bad_namespace_fails(self, c3_validator):
        with pytest.raises(ValidationError):
            c3_validator.validate(make_skill(namespace="agent2"))

    def test_missing_subscribes_fails(self, c3_validator):
        skill = make_skill()
        del skill["subscribes"]
        with pytest.raises(ValidationError):
            c3_validator.validate(skill)

    def test_empty_subscribes_and_emits_is_valid(self, c3_validator):
        c3_validator.validate(make_skill(subscribes=[], emits=[]))

    def test_unknown_top_level_field_rejected(self, c3_validator):
        with pytest.raises(ValidationError):
            c3_validator.validate(make_skill(unexpected_field="nope"))


class TestSkillEventReferencesMatchC2Naming:
    def test_bad_subscribed_event_name_fails(self, c3_validator):
        with pytest.raises(ValidationError):
            c3_validator.validate(make_skill(subscribes=["not-an-event"]))

    def test_bad_emitted_event_name_fails(self, c3_validator):
        with pytest.raises(ValidationError):
            c3_validator.validate(make_skill(emits=["redteam"]))

    def test_subscribed_events_are_also_valid_c2_event_names(self, c3_validator, c2_validator):
        """Cross-contract check: every event name a skill declares must at least
        be shaped like a valid C2 event name (ingest.* open, redteam.* closed enum)."""
        skill = make_skill()
        redteam_enum = set(
            c2_validator.schema["$defs"]["redteam_event_name"]["enum"]
        )
        for name in skill["subscribes"] + skill["emits"]:
            if name.startswith("redteam."):
                assert name in redteam_enum
            else:
                assert name.startswith("ingest.")
