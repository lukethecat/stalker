"""Authorization gate: redteam.* attack activity must not start without a
matching, unexpired `redteam.target.registered` event.

House rule (CLAUDE.md): "`redteam.target.registered` 必带授权范围，无授权不启动"。
This enforces that at runtime rather than only modeling it in the C2 schema,
so a caller can't accidentally skip the check by forgetting to look.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


class NotAuthorized(Exception):
    def __init__(self, target_id: str, reason: str):
        super().__init__(f"target '{target_id}' not authorized: {reason}")
        self.target_id = target_id
        self.reason = reason


@dataclass(frozen=True)
class Authorization:
    target_id: str
    scope: list[str]
    authorized_by: str
    expires_at: str | None


def _is_expired(expires_at: str | None) -> bool:
    if expires_at is None:
        return False
    expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    return expires < datetime.now(UTC)


def find_authorization(events: list[dict[str, Any]], target_id: str) -> Authorization | None:
    """Scan C2 event envelopes (oldest to newest) for `target_id`'s most
    recent `redteam.target.registered` registration; return it unless it has
    expired. A later registration for the same target_id supersedes an
    earlier one (re-registration -- distinct from C1's tape-level
    `supersedes`, which this function doesn't need to know about)."""
    found: Authorization | None = None
    for event in events:
        if event.get("event") != "redteam.target.registered":
            continue
        payload = event.get("payload", {})
        if payload.get("target", {}).get("id") != target_id:
            continue
        auth = payload.get("authorization", {})
        found = Authorization(
            target_id=target_id,
            scope=list(auth.get("scope", [])),
            authorized_by=auth.get("authorized_by", ""),
            expires_at=auth.get("expires_at"),
        )
    if found is not None and _is_expired(found.expires_at):
        return None
    return found


def require_authorization(events: list[dict[str, Any]], target_id: str) -> Authorization:
    auth = find_authorization(events, target_id)
    if auth is None:
        raise NotAuthorized(target_id, "no unexpired redteam.target.registered event found")
    if not auth.scope:
        raise NotAuthorized(target_id, "authorization scope is empty")
    return auth
