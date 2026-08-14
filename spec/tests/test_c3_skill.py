import json

import pytest
from jsonschema.exceptions import ValidationError

from sentinel_spec import conformance as C

EX = C.SPEC_ROOT / "examples"
SKILL = C.validator("c3_skill")


def _load(name):
    return json.loads((EX / name).read_text(encoding="utf-8"))


def test_public_recon_skill_valid():
    SKILL.validate(_load("skill_public_recon.json"))


def test_private_attack_manifest_valid():
    SKILL.validate(_load("skill_private_attack.json"))


def test_public_skill_with_payloads_is_rejected():
    skill = _load("skill_private_attack.json")
    skill["visibility"] = "public"  # ammo must stay private
    with pytest.raises(ValidationError):
        SKILL.validate(skill)


def test_payload_skill_must_require_authorization():
    skill = _load("skill_private_attack.json")
    skill["authorization_required"] = False
    with pytest.raises(ValidationError):
        SKILL.validate(skill)


def test_layers_require_l0():
    skill = _load("skill_public_recon.json")
    del skill["layers"]["l0"]
    with pytest.raises(ValidationError):
        SKILL.validate(skill)


def test_unknown_mount_point_rejected():
    skill = _load("skill_public_recon.json")
    skill["mount_points"] = ["not_a_real_hook"]
    with pytest.raises(ValidationError):
        SKILL.validate(skill)
