from __future__ import annotations

import copy
import dataclasses
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    canonical_json_bytes,
    load_json_strict,
    sha256_bytes,
    validate_phase_c_policy,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-003-phase-c0-policy.json"
)


def build_policy_leaf_mutations(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    mutations: list[tuple[str, dict[str, Any]]] = []
    for path in _leaf_paths(payload):
        original = _value_at_path(payload, path)
        mutated = copy.deepcopy(payload)
        _replace_at_path(mutated, path, _mutate_leaf(original))
        mutations.append((".".join(str(part) for part in path), mutated))
    return mutations


def _leaf_paths(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
    if type(value) is dict:
        paths: list[tuple[str | int, ...]] = []
        for key in sorted(value):
            paths.extend(_leaf_paths(value[key], (*path, key)))
        return paths
    if type(value) is list:
        paths = []
        for index, item in enumerate(value):
            paths.extend(_leaf_paths(item, (*path, index)))
        return paths
    return [path]


def _value_at_path(payload: dict[str, Any], path: tuple[str | int, ...]) -> Any:
    value: Any = payload
    for part in path:
        value = value[part]
    return value


def _replace_at_path(payload: dict[str, Any], path: tuple[str | int, ...], value: Any) -> None:
    target: Any = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def _mutate_leaf(value: Any) -> Any:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return f"{value}-mutated"
    raise TypeError(f"unsupported policy leaf type: {type(value).__name__}")


class PhaseCPolicyContractTests(unittest.TestCase):
    def test_frozen_policy_is_exact_and_canonical(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        validated = validate_phase_c_policy(payload)
        self.assertEqual(validated["policy_id"], "emotion-state-phase-c0-synthetic-v1")
        self.assertEqual(validated["evidence_policy_version"], "emotion-state-evidence-v2")
        self.assertEqual(validated["base_support_units"]["unsolicited_explicit_statement"], 700)
        self.assertEqual(validated["contradiction_cap"], 350)
        self.assertEqual(validated["acoustic_only_cap"], 400)
        canonical = canonical_json_bytes(validated)
        self.assertEqual(
            json.loads(canonical.decode("utf-8")),
            json.loads(POLICY_PATH.read_text(encoding="utf-8")),
        )
        self.assertRegex(sha256_bytes(canonical), r"^[0-9A-F]{64}$")

    def test_every_top_level_policy_mutation_fails_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for key in tuple(payload):
            mutated = copy.deepcopy(payload)
            mutated.pop(key)
            with self.subTest(missing=key):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)
        extra = copy.deepcopy(payload)
        extra["future"] = True
        with self.assertRaises(PhaseCContractError):
            validate_phase_c_policy(extra)

    def test_every_policy_leaf_mutation_fails_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for name, mutated in build_policy_leaf_mutations(payload):
            with self.subTest(mutation=name):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)

    def test_nonfinite_and_bool_numeric_values_fail_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for invalid in (True, float("nan"), float("inf"), -1):
            mutated = copy.deepcopy(payload)
            mutated["entry_threshold"] = invalid
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)

    def test_exact_output_eol_attributes_are_narrow(self) -> None:
        self.assertEqual(
            (ROOT / ".gitattributes").read_text(
                encoding="utf-8",
            ).splitlines(),
            [
                "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json text eol=lf",
                "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md text eol=lf",
            ],
        )
