import pytest

from sentinel_spec import conformance as C


@pytest.mark.parametrize("name", ["c1_tape", "c1_view", "c2_events", "c3_skill"])
def test_schema_is_itself_valid(name):
    # Draft202012Validator.check_schema (inside validator()) raises if the schema is malformed.
    C.validator(name)
