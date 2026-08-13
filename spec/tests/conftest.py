import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def _load(name: str) -> dict:
    with open(SCHEMA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def c1_schema() -> dict:
    return _load("c1_tape.schema.json")


@pytest.fixture(scope="session")
def c2_schema() -> dict:
    return _load("c2_events.schema.json")


@pytest.fixture(scope="session")
def c3_schema() -> dict:
    return _load("c3_skill.schema.json")


@pytest.fixture(scope="session")
def c1_validator(c1_schema) -> Draft202012Validator:
    Draft202012Validator.check_schema(c1_schema)
    return Draft202012Validator(c1_schema)


@pytest.fixture(scope="session")
def c2_validator(c2_schema) -> Draft202012Validator:
    Draft202012Validator.check_schema(c2_schema)
    return Draft202012Validator(c2_schema)


@pytest.fixture(scope="session")
def c3_validator(c3_schema) -> Draft202012Validator:
    Draft202012Validator.check_schema(c3_schema)
    return Draft202012Validator(c3_schema)
