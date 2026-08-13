import asyncio
import json
from pathlib import Path

from agent0_ipo_dispatcher.plugin import (
    TapeDispatchChannel,
    fetch_new_events,
    load_subscriptions,
    matches_any,
)
from bub.tape import InMemoryTapeStore, TapeEntry


def write_skill(workspace: Path, name: str, subscribes: str) -> None:
    skill_dir = workspace / ".agents" / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {name}
description: test skill for dispatcher unit tests
metadata:
  subscribes: "{subscribes}"
---

body
""",
        encoding="utf-8",
    )


class FakeFramework:
    def __init__(self, workspace: Path, store: InMemoryTapeStore):
        self.workspace = workspace
        self._store = store

    def get_tape_store(self):
        return self._store


class TestMatchesAny:
    def test_exact_match(self):
        assert matches_any("redteam.target.registered", {"redteam.target.registered"})

    def test_wildcard_match(self):
        assert matches_any("redteam.target.registered", {"redteam.*"})

    def test_no_match(self):
        assert not matches_any("ingest.source.collected", {"redteam.*"})

    def test_empty_patterns_no_match(self):
        assert not matches_any("redteam.target.registered", set())


class TestLoadSubscriptions:
    def test_reads_comma_separated_metadata(self, tmp_path: Path):
        write_skill(tmp_path, "probe-builder", "redteam.target.registered, redteam.intel.ingested")
        patterns = load_subscriptions(tmp_path)
        assert {"redteam.target.registered", "redteam.intel.ingested"} <= patterns

    def test_no_skills_no_patterns_from_project(self, tmp_path: Path):
        patterns = load_subscriptions(tmp_path)
        assert "redteam.target.registered" not in patterns


class TestFetchNewEvents:
    def test_filters_kind_and_after_id(self):
        store = InMemoryTapeStore()
        store.append("main", TapeEntry.message({"role": "user", "content": "hi"}))
        store.append("main", TapeEntry.event("redteam.target.registered", {"target": "t1"}))
        store.append("main", TapeEntry.event("ingest.source.collected", {"source": "s1"}))

        all_events = asyncio.run(fetch_new_events(store, "main", after_id=0))
        assert [e.payload["name"] for e in all_events] == [
            "redteam.target.registered",
            "ingest.source.collected",
        ]

        newer_only = asyncio.run(fetch_new_events(store, "main", after_id=all_events[0].id))
        assert [e.payload["name"] for e in newer_only] == ["ingest.source.collected"]


class TestTapeDispatchChannelTick:
    def test_matching_event_triggers_turn_once(self, tmp_path: Path):
        write_skill(tmp_path, "probe-builder", "redteam.*")
        store = InMemoryTapeStore()
        store.append("main", TapeEntry.event("redteam.target.registered", {"target": "t1"}))
        store.append("main", TapeEntry.event("ingest.source.collected", {"source": "s1"}))

        framework = FakeFramework(tmp_path, store)
        received = []

        async def on_receive(message):
            received.append(message)

        channel = TapeDispatchChannel(framework, on_receive)

        asyncio.run(channel._tick())
        assert len(received) == 1
        payload = json.loads(received[0].content)
        assert payload["event"] == "redteam.target.registered"
        assert payload["data"] == {"target": "t1"}

        # a second tick with no new tape entries must not re-trigger
        asyncio.run(channel._tick())
        assert len(received) == 1

    def test_no_subscriptions_means_no_dispatch(self, tmp_path: Path):
        store = InMemoryTapeStore()
        store.append("main", TapeEntry.event("redteam.target.registered", {"target": "t1"}))
        framework = FakeFramework(tmp_path, store)
        received = []

        async def on_receive(message):
            received.append(message)

        channel = TapeDispatchChannel(framework, on_receive)
        asyncio.run(channel._tick())
        assert received == []

    def test_no_tape_store_is_noop(self, tmp_path: Path):
        write_skill(tmp_path, "probe-builder", "redteam.*")

        class NoStoreFramework:
            workspace = tmp_path

            def get_tape_store(self):
                return None

        received = []

        async def on_receive(message):
            received.append(message)

        channel = TapeDispatchChannel(NoStoreFramework(), on_receive)
        asyncio.run(channel._tick())
        assert received == []
