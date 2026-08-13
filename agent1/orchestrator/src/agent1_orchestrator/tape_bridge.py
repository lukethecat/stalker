"""Bridge orchestrator results onto a tape as C2 events.

Only this module touches bub -- crescendo.py/budget.py/policies.py/report.py
stay framework-agnostic so agent1's method isn't nailed to one kernel
implementation (see docs/architecture.md's "operator equivalence"). `bub` is
imported lazily inside `append_event_to_tape` so importing this module
doesn't require bub to be installed.

Every event built here is validated against spec/schema/c2_events.schema.json
when that file can be located (i.e. when running inside this monorepo);
outside it, validation is skipped rather than failing, since a packaged
build of this adapter may not carry spec/ alongside it.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from agent1_orchestrator.crescendo import RoundResult

SCHEMA_VERSION = "1.0.0"


def _find_c2_schema() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "spec" / "schema" / "c2_events.schema.json"
        if candidate.is_file():
            return candidate
    return None


def _load_validator() -> Draft202012Validator | None:
    schema_path = _find_c2_schema()
    if schema_path is None:
        return None
    with open(schema_path, encoding="utf-8") as f:
        return Draft202012Validator(json.load(f))


_C2_VALIDATOR = _load_validator()


def _validate(event: dict[str, Any]) -> dict[str, Any]:
    if _C2_VALIDATOR is not None:
        _C2_VALIDATOR.validate(event)
    return event


def round_to_event(*, probe_id: str, result: RoundResult, run_id: str, agent: str = "agent1") -> dict[str, Any]:
    return _validate({
        "schema_version": SCHEMA_VERSION,
        "id": f"{probe_id}-round-{result.round_index}",
        "event": "redteam.attack.round.completed",
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent,
        "run_id": run_id,
        "payload": {
            "probe_ref": probe_id,
            "round_index": result.round_index,
            "verdict": result.verdict.verdict,
            "judge_score": result.verdict.score,
        },
    })


def finding_to_event(*, finding: dict[str, Any], run_id: str, agent: str = "agent1") -> dict[str, Any]:
    return _validate({
        "schema_version": SCHEMA_VERSION,
        "id": finding["finding_id"],
        "event": "redteam.finding.logged",
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent,
        "run_id": run_id,
        "payload": finding,
    })


def append_event_to_tape(store: Any, tape: str, event: dict[str, Any]) -> None:
    """Append one already-built C2 event envelope as a bub TapeEntry.event."""
    from bub.tape import TapeEntry

    store.append(
        tape,
        TapeEntry.event(
            event["event"],
            event["payload"],
            c2_schema_version=event["schema_version"],
            c2_event_id=event["id"],
            c2_run_id=event["run_id"],
            c2_agent=event["agent"],
        ),
    )
