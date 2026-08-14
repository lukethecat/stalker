import pytest
from jsonschema.exceptions import ValidationError

from sentinel_spec import conformance as C

EVENTS = C.validator("c2_events")


def test_valid_target_registered():
    EVENTS.validate({
        "name": "redteam.target.registered",
        "schema_version": "0.1.0",
        "data": {"target_id": "t", "authorization": {"authorized": True, "scope": "staging", "authorized_by": "jaco"}},
    })


def test_target_registered_rejects_unauthorized():
    with pytest.raises(ValidationError):
        EVENTS.validate({
            "name": "redteam.target.registered",
            "schema_version": "0.1.0",
            "data": {"target_id": "t", "authorization": {"authorized": False, "scope": "staging"}},
        })


def test_target_registered_requires_authorization_block():
    with pytest.raises(ValidationError):
        EVENTS.validate({
            "name": "redteam.target.registered",
            "schema_version": "0.1.0",
            "data": {"target_id": "t"},
        })


def test_finding_requires_a_taxonomy_mapping():
    with pytest.raises(ValidationError):
        EVENTS.validate({
            "name": "redteam.finding.logged",
            "schema_version": "0.1.0",
            "data": {"finding_id": "F", "severity": "high", "taxonomy": {}, "reproduction": "x", "remediation": "y"},
        })


def test_unknown_namespace_rejected():
    with pytest.raises(ValidationError):
        EVENTS.validate({"name": "marketing.blast.sent", "schema_version": "0.1.0", "data": {}})


def test_metric_asr_out_of_range_rejected():
    with pytest.raises(ValidationError):
        EVENTS.validate({
            "name": "redteam.metric.updated",
            "schema_version": "0.1.0",
            "data": {"campaign_id": "c", "metrics": {"asr": 1.5}},
        })


def test_generic_redteam_event_passes_without_special_def():
    EVENTS.validate({
        "name": "redteam.strategy.adjusted",
        "schema_version": "0.1.0",
        "data": {"from": "crescendo", "to": "goat", "reason": "save queries"},
    })
