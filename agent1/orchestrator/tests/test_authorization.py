from datetime import UTC, datetime, timedelta

import pytest
from agent1_orchestrator.authorization import (
    NotAuthorized,
    find_authorization,
    require_authorization,
)


def registration_event(target_id, scope, authorized_by="lead@example.com", expires_at=None):
    return {
        "event": "redteam.target.registered",
        "payload": {
            "target": {"id": target_id},
            "authorization": {"scope": scope, "authorized_by": authorized_by, "expires_at": expires_at},
        },
    }


class TestFindAuthorization:
    def test_finds_matching_registration(self):
        events = [registration_event("t1", ["POST /chat"])]
        auth = find_authorization(events, "t1")
        assert auth is not None
        assert auth.scope == ["POST /chat"]

    def test_no_registration_returns_none(self):
        assert find_authorization([], "t1") is None

    def test_wrong_target_id_returns_none(self):
        events = [registration_event("other-target", ["POST /chat"])]
        assert find_authorization(events, "t1") is None

    def test_later_registration_supersedes_earlier(self):
        events = [
            registration_event("t1", ["POST /old"]),
            registration_event("t1", ["POST /new"]),
        ]
        auth = find_authorization(events, "t1")
        assert auth.scope == ["POST /new"]

    def test_expired_registration_returns_none(self):
        past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        events = [registration_event("t1", ["POST /chat"], expires_at=past)]
        assert find_authorization(events, "t1") is None

    def test_future_expiry_is_valid(self):
        future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
        events = [registration_event("t1", ["POST /chat"], expires_at=future)]
        assert find_authorization(events, "t1") is not None

    def test_no_expiry_is_valid(self):
        events = [registration_event("t1", ["POST /chat"], expires_at=None)]
        assert find_authorization(events, "t1") is not None


class TestRequireAuthorization:
    def test_raises_when_missing(self):
        with pytest.raises(NotAuthorized):
            require_authorization([], "t1")

    def test_raises_when_scope_empty(self):
        events = [registration_event("t1", [])]
        with pytest.raises(NotAuthorized):
            require_authorization(events, "t1")

    def test_returns_authorization_when_valid(self):
        events = [registration_event("t1", ["POST /chat"])]
        auth = require_authorization(events, "t1")
        assert auth.target_id == "t1"
