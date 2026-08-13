"""bub plugin: tape --entry--> C2 event --match--> turn.

Bridges C1 (tape) and C2 (event taxonomy) onto bub's concrete runtime:
a TapeEntry of kind="event" whose payload["name"] matches a namespace
pattern (see ../../../spec/schema/c2_events.schema.json) is turned into
an inbound ChannelMessage, which bub's own turn pipeline then processes.

Subscriptions come from discovered skills' SKILL.md frontmatter. bub's
skill metadata is a flat dict[str, str] (see bub.skills._is_valid_metadata_field),
so a skill declares interest as a comma-separated string:

    ---
    name: some-skill
    description: ...
    metadata:
      subscribes: "redteam.target.registered,ingest.source.collected"
    ---

This is the C3 `subscribes` field's concrete encoding under bub, distinct
from the richer JSON list in spec/schema/c3_skill.schema.json (that schema
describes the portable manifest shape; this is the adapter for bub's
actual frontmatter constraint).
"""

from __future__ import annotations

import asyncio
import fnmatch
import inspect
import json
from typing import TYPE_CHECKING, Any

from bub.channels.base import Lifecycle
from bub.channels.contracts import MessageHandler
from bub.channels.message import ChannelMessage
from bub.hooks import hookimpl
from bub.skills import discover_skills
from bub.tape import TapeEntry, TapeQuery

if TYPE_CHECKING:
    from bub.framework import BubFramework

POLL_INTERVAL_SECONDS = 1.0
TAPE_NAME = "main"


def load_subscriptions(workspace: Any) -> set[str]:
    """Collect C2 event-name patterns any discovered skill has subscribed to.

    `SkillMetadata.metadata` is the whole flattened SKILL.md frontmatter
    (name/description/metadata/...); the skill-author-declared fields live
    one level deeper, under its own `metadata` key (a flat dict[str, str] --
    see bub.skills._is_valid_metadata_field).
    """
    patterns: set[str] = set()
    for skill in discover_skills(workspace):
        declared = skill.metadata.get("metadata", {})
        raw = str(declared.get("subscribes", "")) if isinstance(declared, dict) else ""
        patterns.update(p.strip() for p in raw.split(",") if p.strip())
    return patterns


def matches_any(event_name: str, patterns: set[str]) -> bool:
    return any(fnmatch.fnmatch(event_name, pattern) for pattern in patterns)


async def fetch_new_events(store: Any, tape: str, after_id: int) -> list[TapeEntry]:
    """Return event-kind tape entries with id > after_id, oldest first."""
    query = TapeQuery(tape=tape, store=store).kinds("event")
    result = query.all()
    if inspect.isawaitable(result):
        result = await result
    return [entry for entry in result if entry.id > after_id]


class TapeDispatchChannel(Lifecycle):
    """Background channel: poll the tape, turn matching events into turns."""

    name = "agent0-ipo-dispatcher"

    def __init__(self, framework: BubFramework, on_receive: MessageHandler) -> None:
        self._framework = framework
        self._on_receive = on_receive
        self._last_id = 0
        self._task: asyncio.Task[None] | None = None

    async def start(self, stop_event: asyncio.Event) -> None:
        self._task = asyncio.create_task(self._run(stop_event))

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

    async def _run(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await self._tick()
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _tick(self) -> None:
        store = self._framework.get_tape_store()
        if store is None:
            return
        patterns = load_subscriptions(self._framework.workspace)
        if not patterns:
            return
        for entry in await fetch_new_events(store, TAPE_NAME, self._last_id):
            self._last_id = max(self._last_id, entry.id)
            event_name = str(entry.payload.get("name", ""))
            if not matches_any(event_name, patterns):
                continue
            await self._on_receive(self._to_message(entry, event_name))

    def _to_message(self, entry: TapeEntry, event_name: str) -> ChannelMessage:
        content = json.dumps({"event": event_name, "data": entry.payload.get("data", {})})
        return ChannelMessage(
            session_id=f"agent0-ipo-dispatcher:{event_name}",
            channel=self.name,
            content=content,
            context={"tape_entry_id": entry.id, "event": event_name},
        )


class Plugin:
    """Registered under the `bub` entry-point group as `agent0_ipo_dispatcher`."""

    def __init__(self, framework: BubFramework) -> None:
        self._framework = framework

    @hookimpl
    def provide_channels(self, message_handler: MessageHandler) -> list[Lifecycle]:
        return [TapeDispatchChannel(self._framework, message_handler)]
