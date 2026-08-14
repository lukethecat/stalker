from sentinel_spec import conformance as C


def test_same_major_is_compatible():
    assert C.is_compatible("0.1.0")
    assert C.is_compatible("0.1.99")
    assert C.is_compatible("0.9.3")


def test_different_major_is_incompatible():
    assert not C.is_compatible("1.0.0")


def test_future_patch_entry_still_validates():
    entry = {
        "id": "z1",
        "schema_version": "0.1.7",
        "ts": "2026-08-13T00:00:00Z",
        "kind": "note",
        "actor": {"type": "agent", "id": "a"},
        "payload": {"note": "written by a newer patch version, still readable"},
    }
    C.validate_entry(entry)
    assert C.is_compatible(entry["schema_version"])
