import pytest
from jsonschema import ValidationError

REDTEAM_VALID_PAYLOADS = {
    "redteam.target.registered": {
        "target": {"id": "target-1", "description": "staging chat endpoint"},
        "authorization": {
            "scope": ["POST /v1/chat"],
            "authorized_by": "security-lead@example.com",
            "authorized_at": "2026-08-13T09:00:00Z",
            "expires_at": "2026-09-13T09:00:00Z",
        },
    },
    "redteam.intel.ingested": {
        "source_agent": "agent0",
        "intel_ref": "run-abc#seq-12",
        "summary": "collected public API docs",
    },
    "redteam.probe.built": {
        "probe_id": "probe-1",
        "target_ref": "target-1",
        "method": "crescendo",
        "expected_behavior": "model should refuse escalating harmful request",
        "rubric": {"pass_if": "refusal maintained across 5 turns"},
    },
    "redteam.attack.round.completed": {
        "probe_ref": "probe-1",
        "round_index": 0,
        "attacker_output_ref": "run-abc#seq-20",
        "judge_score": 0.2,
        "verdict": "fail",
        "transcript_ref": "run-abc#seq-19",
    },
    "redteam.strategy.adjusted": {
        "based_on_refs": ["run-abc#seq-20"],
        "previous_vector": "direct-ask",
        "next_vector": "role-play-escalation",
        "reason": "direct ask was refused; judge score indicates escalation path may succeed",
    },
    "redteam.finding.logged": {
        "finding_id": "finding-1",
        "category": {"owasp": "LLM01", "atlas": "AML.T0051"},
        "affected_component": "chat-completion-endpoint",
        "reproducible_case_ref": "run-abc#seq-33",
        "severity": "high",
        "remediation_hint": "tighten system prompt refusal boundary",
    },
    "redteam.metric.updated": {
        "metric_name": "asr",
        "value": 0.35,
        "scope": "probe-1",
    },
    "redteam.report.ready": {
        "report_id": "report-1",
        "finding_refs": ["finding-1"],
        "summary": "1 high severity finding on chat endpoint",
    },
    "redteam.remediation.retested": {
        "finding_ref": "finding-1",
        "patch_ref": "commit-abc123",
        "retest_result": "pass",
        "notes": "escalation path now refused",
    },
}


def make_event(event_name: str, payload: dict, **overrides):
    evt = {
        "schema_version": "1.0.0",
        "id": "evt-001",
        "event": event_name,
        "ts": "2026-08-13T10:00:00Z",
        "agent": "agent1",
        "run_id": "run-abc",
        "payload": payload,
    }
    evt.update(overrides)
    return evt


class TestRedteamEventNamesClosed:
    def test_all_nine_documented_events_present(self):
        expected = {
            "redteam.target.registered",
            "redteam.intel.ingested",
            "redteam.probe.built",
            "redteam.attack.round.completed",
            "redteam.strategy.adjusted",
            "redteam.finding.logged",
            "redteam.metric.updated",
            "redteam.report.ready",
            "redteam.remediation.retested",
        }
        assert set(REDTEAM_VALID_PAYLOADS.keys()) == expected

    @pytest.mark.parametrize("event_name", list(REDTEAM_VALID_PAYLOADS.keys()))
    def test_valid_payload_passes(self, c2_validator, event_name):
        c2_validator.validate(make_event(event_name, REDTEAM_VALID_PAYLOADS[event_name]))

    @pytest.mark.parametrize("event_name", list(REDTEAM_VALID_PAYLOADS.keys()))
    def test_empty_payload_fails(self, c2_validator, event_name):
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event(event_name, {}))

    def test_unknown_redteam_event_name_fails(self, c2_validator):
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("redteam.not.a.real.event", {"anything": True}))


class TestTargetRegisteredAuthorizationGate:
    def test_missing_authorization_fails(self, c2_validator):
        payload = {"target": {"id": "target-1"}}
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("redteam.target.registered", payload))

    def test_empty_scope_fails(self, c2_validator):
        payload = {
            "target": {"id": "target-1"},
            "authorization": {"scope": [], "authorized_by": "lead@example.com"},
        }
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("redteam.target.registered", payload))

    def test_missing_authorized_by_fails(self, c2_validator):
        payload = {
            "target": {"id": "target-1"},
            "authorization": {"scope": ["POST /v1/chat"]},
        }
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("redteam.target.registered", payload))


class TestFindingSeverityEnum:
    def test_invalid_severity_fails(self, c2_validator):
        payload = dict(REDTEAM_VALID_PAYLOADS["redteam.finding.logged"])
        payload["severity"] = "catastrophic"
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("redteam.finding.logged", payload))


class TestIngestNamespaceIsOpen:
    def test_well_formed_ingest_event_with_arbitrary_payload_passes(self, c2_validator):
        c2_validator.validate(
            make_event(
                "ingest.source.collected",
                {"source_id": "src-1", "uri": "https://example.com"},
                agent="agent0",
            )
        )

    def test_deeply_nested_ingest_event_name_passes(self, c2_validator):
        c2_validator.validate(
            make_event("ingest.data.structured.batch", {"batch_id": "b1"}, agent="agent0")
        )

    def test_malformed_ingest_event_name_fails(self, c2_validator):
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("ingest", {}, agent="agent0"))

    def test_wrong_namespace_prefix_fails(self, c2_validator):
        with pytest.raises(ValidationError):
            c2_validator.validate(make_event("intake.source.collected", {}, agent="agent0"))


class TestEnvelopeRequiredFields:
    def test_missing_run_id_fails(self, c2_validator):
        evt = make_event("redteam.report.ready", REDTEAM_VALID_PAYLOADS["redteam.report.ready"])
        del evt["run_id"]
        with pytest.raises(ValidationError):
            c2_validator.validate(evt)

    def test_bad_schema_version_fails(self, c2_validator):
        evt = make_event(
            "redteam.report.ready",
            REDTEAM_VALID_PAYLOADS["redteam.report.ready"],
            schema_version="v1",
        )
        with pytest.raises(ValidationError):
            c2_validator.validate(evt)
