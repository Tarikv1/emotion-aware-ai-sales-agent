from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
from collections import Counter
from contextlib import ExitStack, contextmanager, redirect_stderr
from copy import deepcopy
from dataclasses import replace
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research/experiments/cases/emotion-state-002-phase-b-config.json"
FEATURE_SCHEMA = (
    ROOT
    / "research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json"
)
SPLIT_SCHEMA = (
    ROOT
    / "research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json"
)
ENVIRONMENT_LOCK = (
    ROOT / "research/environments/emotion-state-002/requirements.lock"
)
WHEELHOUSE = (
    ROOT / ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse"
)
EVALUATION_PYTHON = (
    ROOT / ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe"
)
RUNTIME_MANIFEST = ROOT / "runtime/runtime_manifest.json"
IMPLEMENTATION_PLAN = (
    ROOT
    / "docs/superpowers/plans/"
    "2026-07-19-emotion-state-phase-b-public-data-feasibility.md"
)
ENVIRONMENT_TEST_TEMP = (
    ROOT / ".tmp/emotion-state-002-phase-b/dependencies/test-temp"
)


class PhaseBContractTests(unittest.TestCase):
    def test_frozen_contracts_validate(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_config,
            validate_feature_schema,
            validate_split_schema,
        )

        config = validate_config(load_json_strict(CONFIG))
        feature = validate_feature_schema(load_json_strict(FEATURE_SCHEMA))
        split = validate_split_schema(load_json_strict(SPLIT_SCHEMA))
        self.assertEqual(
            config["checkpoint_id"],
            "EMOTION-STATE-002-phase-b-public-data-feasibility",
        )
        self.assertEqual(len(feature["ordered_features"]), 17)
        self.assertEqual(
            split["partition_actor_counts"],
            {
                "training_discovery": 35,
                "calibration": 13,
                "balanced_diagnostic": 13,
                "final_lockbox": 30,
            },
        )

    def test_contract_mutations_fail_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_config,
            validate_feature_schema,
        )

        feature = load_json_strict(FEATURE_SCHEMA)
        mutated = deepcopy(feature)
        mutated["ordered_features"].append("filename")
        with self.assertRaisesRegex(ValueError, "ordered acoustic features"):
            validate_feature_schema(mutated)

        config = load_json_strict(CONFIG)
        mutated = deepcopy(config)
        mutated["boundaries"]["runtime_influence_allowed"] = True
        with self.assertRaisesRegex(ValueError, "runtime influence"):
            validate_config(mutated)

    def test_every_frozen_value_and_object_shape_fails_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_config,
            validate_feature_schema,
            validate_split_schema,
        )

        contracts: tuple[tuple[dict[str, Any], Callable[[Any], dict[str, Any]]], ...] = (
            (load_json_strict(CONFIG), validate_config),
            (load_json_strict(FEATURE_SCHEMA), validate_feature_schema),
            (load_json_strict(SPLIT_SCHEMA), validate_split_schema),
        )
        for payload, validator in contracts:
            for path in self._scalar_paths(payload):
                mutated = deepcopy(payload)
                current = self._value_at(mutated, path)
                self._replace_at(mutated, path, self._different_value(current))
                with self.subTest(contract=validator.__name__, mutation=path):
                    with self.assertRaises(ValueError):
                        validator(mutated)

            for path in self._mapping_paths(payload):
                mapping = self._value_at(payload, path)
                for key in mapping:
                    mutated = deepcopy(payload)
                    del self._value_at(mutated, path)[key]
                    with self.subTest(contract=validator.__name__, missing=path + (key,)):
                        with self.assertRaises(ValueError):
                            validator(mutated)

                mutated = deepcopy(payload)
                self._value_at(mutated, path)["unexpected_field"] = True
                with self.subTest(contract=validator.__name__, unexpected=path):
                    with self.assertRaises(ValueError):
                        validator(mutated)

    def test_strict_loader_rejects_numeric_overflow(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import load_json_strict

        with tempfile.TemporaryDirectory() as temporary_directory:
            overflow = Path(temporary_directory) / "overflow.json"
            overflow.write_text('{"value": 1e9999}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite JSON number"):
                load_json_strict(overflow)

    def test_direct_cli_validates_canonical_and_malformed_artifacts(self) -> None:
        validator = ROOT / "scripts/validate_emotion_state_002_phase_b.py"
        passed = subprocess.run(
            [sys.executable, str(validator), "contracts"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertEqual(
            passed.stdout,
            "EMOTION-STATE-002 Phase B validation passed: contracts.\n",
        )
        self.assertEqual(passed.stderr, "")

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            temporary_validator = (
                temporary_root / "scripts/validate_emotion_state_002_phase_b.py"
            )
            temporary_validator.parent.mkdir(parents=True)
            shutil.copy2(validator, temporary_validator)

            for source, destination in (
                (FEATURE_SCHEMA, temporary_root / FEATURE_SCHEMA.relative_to(ROOT)),
                (SPLIT_SCHEMA, temporary_root / SPLIT_SCHEMA.relative_to(ROOT)),
                (
                    ENVIRONMENT_LOCK,
                    temporary_root / ENVIRONMENT_LOCK.relative_to(ROOT),
                ),
            ):
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

            malformed_config = json.loads(CONFIG.read_text(encoding="utf-8"))
            malformed_config["implementation_base_commit"] = "not-the-frozen-base"
            temporary_config = temporary_root / CONFIG.relative_to(ROOT)
            temporary_config.parent.mkdir(parents=True, exist_ok=True)
            temporary_config.write_text(
                json.dumps(malformed_config),
                encoding="utf-8",
            )

            failed = subprocess.run(
                [sys.executable, str(temporary_validator), "contracts"],
                cwd=temporary_root,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(failed.stdout, "")
            self.assertIn("Phase B validation failed: contracts", failed.stderr)

    def test_task_9_cli_requires_exactly_one_section_and_scopes_receipt(self) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self.assertTrue(
            hasattr(validator, "SECTIONS"),
            "Task 9 section contract is missing",
        )
        SECTIONS = validator.SECTIONS
        _parse_args = validator._parse_args

        self.assertEqual(
            SECTIONS,
            (
                "source",
                "contracts",
                "environment",
                "synthetic",
                "candidate",
                "checkpoint",
            ),
        )
        for section in SECTIONS:
            arguments = (
                [section, "--receipt", "synthetic-receipt.json"]
                if section == "candidate"
                else [section]
            )
            parsed = _parse_args(arguments)
            self.assertEqual(parsed.section, section)
            self.assertEqual(
                parsed.receipt,
                "synthetic-receipt.json" if section == "candidate" else None,
            )

        for invalid in (
            [],
            ["source", "contracts"],
            ["source", "--receipt", "unexpected.json"],
            ["checkpoint", "--receipt", "unexpected.json"],
            ["candidate"],
            ["candidate", "--receipt", "a.json", "--receipt", "b.json"],
            ["--synthetic-runner"],
        ):
            with self.subTest(invalid=invalid):
                with redirect_stderr(StringIO()):
                    with self.assertRaises(SystemExit):
                        _parse_args(invalid)

    def test_task_9_offline_sections_validate_without_material_access(self) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        section_functions = (
            "validate_source_section",
            "validate_contracts_section",
            "validate_environment_section",
            "validate_synthetic_section",
        )
        for function_name in section_functions:
            with self.subTest(function=function_name):
                self.assertTrue(
                    hasattr(validator, function_name),
                    f"Task 9 {function_name} is missing",
                )
                self.assertIsNone(getattr(validator, function_name)())

    def test_task_9_command_docs_freeze_offline_commands_and_explicit_gates(
        self,
    ) -> None:
        command_map = (ROOT / "docs/product/COMMANDS.md").read_text(
            encoding="utf-8-sig"
        )
        heading = "## EMOTION-STATE-002 Phase B Offline Validation And Gates"
        self.assertIn(heading, command_map)
        section = command_map.split(heading, 1)[1].split("\n## ", 1)[0]
        validator = (
            ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe "
            "scripts/validate_emotion_state_002_phase_b.py"
        )
        expected_validator_commands = (
            f"{validator} source",
            f"{validator} contracts",
            f"{validator} environment",
            f"{validator} synthetic",
            (
                f"{validator} candidate --receipt "
                ".tmp/emotion-state-002-phase-b/publication/receipt.json"
            ),
            f"{validator} checkpoint",
        )
        for command in expected_validator_commands:
            self.assertEqual(section.count(command), 1, command)
        for gate in (
            "Explicit gate: dependency acquisition",
            "Explicit gate: public-material evaluation",
            "Explicit gate: final lockbox",
            "Explicit gate: canonical acceptance",
            "Explicit gate: push",
            "Explicit gate: merge",
        ):
            self.assertEqual(section.count(gate), 1, gate)
        documented_commands = "\n".join(
            line.strip()
            for line in section.splitlines()
            if line.startswith((".tmp/", "py ", "git "))
        ).casefold()
        for forbidden in (
            "provider",
            "elevenlabs",
            "simulation",
            "data/private",
            "runtime/",
            "outbound",
        ):
            self.assertNotIn(forbidden, documented_commands)

    def test_task_9_command_docs_parse_every_fenced_command_and_block_operations(
        self,
    ) -> None:
        command_map = (ROOT / "docs/product/COMMANDS.md").read_text(
            encoding="utf-8-sig"
        )
        heading = "## EMOTION-STATE-002 Phase B Offline Validation And Gates"
        section = command_map.split(heading, 1)[1].split("\n## ", 1)[0]
        dependency_gate_heading = "### Explicit gate: dependency acquisition"
        dependency_gate = section.split(dependency_gate_heading, 1)[1].split(
            "\n### Explicit gate:", 1
        )[0]

        def fenced_lines(text: str) -> list[str]:
            commands: list[str] = []
            inside_fence = False
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if line.startswith("```"):
                    inside_fence = not inside_fence
                    continue
                if inside_fence and line:
                    commands.append(line)
            self.assertFalse(inside_fence, "Task 9 command fence is unclosed")
            return commands

        fenced_commands = fenced_lines(section)
        dependency_gate_commands = fenced_lines(dependency_gate)

        validator = (
            ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe "
            "scripts/validate_emotion_state_002_phase_b.py"
        )
        for command in (
            f"{validator} source",
            f"{validator} contracts",
            f"{validator} environment",
            f"{validator} synthetic",
            (
                f"{validator} candidate --receipt "
                ".tmp/emotion-state-002-phase-b/publication/receipt.json"
            ),
            f"{validator} checkpoint",
        ):
            self.assertEqual(fenced_commands.count(command), 1, command)

        expected_dependency_commands = (
            "py -3.11 -m venv .tmp/emotion-state-002-phase-b/resolver-venv",
            (
                ".tmp/emotion-state-002-phase-b/resolver-venv/Scripts/"
                "python.exe -m pip --version"
            ),
            (
                "py -3.11 -m venv --without-pip "
                ".tmp/emotion-state-002-phase-b/venv"
            ),
            (
                ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe "
                '-c "import sys; print(sys.version); print(sys.executable)"'
            ),
            (
                ".tmp/emotion-state-002-phase-b/resolver-venv/Scripts/"
                "python.exe -m pip download --only-binary=:all: --dest "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse "
                '"numpy>=2.4,<2.5" "scipy>=1.16,<1.18" '
                '"scikit-learn>=1.8,<1.9"'
            ),
            (
                "Get-ChildItem -LiteralPath "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse "
                "-File | Sort-Object Name | Get-FileHash -Algorithm SHA256"
            ),
            (
                ".tmp/emotion-state-002-phase-b/resolver-venv/Scripts/"
                "python.exe -m pip --python "
                ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe "
                "install --no-index --no-deps "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse/"
                "joblib-1.5.3-py3-none-any.whl "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse/"
                "numpy-2.4.6-cp311-cp311-win_amd64.whl "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse/"
                "scikit_learn-1.8.0-cp311-cp311-win_amd64.whl "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse/"
                "scipy-1.17.1-cp311-cp311-win_amd64.whl "
                ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse/"
                "threadpoolctl-3.6.0-py3-none-any.whl"
            ),
            (
                ".tmp/emotion-state-002-phase-b/resolver-venv/Scripts/"
                "python.exe -m pip --python "
                ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe check"
            ),
        )
        self.assertEqual(
            Counter(dependency_gate_commands),
            Counter(expected_dependency_commands),
            "dependency gate command multiset differs from the reviewed allowlist",
        )
        self.assertEqual(
            tuple(dependency_gate_commands),
            expected_dependency_commands,
            "dependency gate command sequence differs from the reviewed allowlist",
        )
        for command in expected_dependency_commands:
            self.assertEqual(fenced_commands.count(command), 1, command)

        forbidden_command_forms = {
            "provider": re.compile(
                r"\b(?:provider|elevenlabs|openai|cartesia)\b",
                re.IGNORECASE,
            ),
            "call": re.compile(
                r"\b(?:outbound|pstn|call|dial)\b",
                re.IGNORECASE,
            ),
            "simulation": re.compile(r"\bsimulat[a-z]*\b", re.IGNORECASE),
            "private-data": re.compile(
                r"(?:^|[\s/])data/private(?:/|$)|\bprivate[-_ ]data\b",
                re.IGNORECASE,
            ),
            "product-runtime": re.compile(
                r"(?:^|\s)(?:python(?:\.exe)?\s+)?"
                r"(?:runtime|apps|sales_agent)/",
                re.IGNORECASE,
            ),
        }
        dependency_command_form = re.compile(
                r"\b(?:curl|wget|invoke-webrequest|invoke-restmethod)\b|"
                r"\bpip\b|\bnpm\s+(?:install|ci)\b|\bgit\s+clone\b|"
                r"\bpy(?:\.exe)?\s+-3\.11\s+-m\s+venv\b|"
                r"\bget-childitem\b.*\bget-filehash\b",
            re.IGNORECASE,
        )
        for command in fenced_commands:
            normalized = command.replace("\\", "/")
            for operation, pattern in forbidden_command_forms.items():
                with self.subTest(operation=operation, command=command):
                    self.assertIsNone(pattern.search(normalized))
            if dependency_command_form.search(normalized):
                with self.subTest(dependency_gate_command=command):
                    self.assertIn(command, expected_dependency_commands)
                    self.assertIn(command, dependency_gate_commands)
        unsafe_examples = {
            "provider": "python arbitrary.py --provider elevenlabs",
            "call": "python arbitrary.py outbound-call",
            "simulation": "python arbitrary.py --run-simulation",
            "private-data-posix": "python arbitrary.py data/private/input.json",
            "private-data-windows": r"python.exe arbitrary.py data\private\input.json",
            "product-runtime-posix": "python runtime/launch.py",
            "product-runtime-windows": r"python.exe runtime\launch.py",
        }
        operation_for_example = {
            "private-data-posix": "private-data",
            "private-data-windows": "private-data",
            "product-runtime-posix": "product-runtime",
            "product-runtime-windows": "product-runtime",
        }
        for label, example in unsafe_examples.items():
            operation = operation_for_example.get(label, label)
            with self.subTest(unsafe_example=label):
                self.assertIsNotNone(
                    forbidden_command_forms[operation].search(
                        example.replace("\\", "/")
                    )
                )
        unauthorized_dependency_examples = (
            "Invoke-WebRequest synthetic:network-target",
            "python -m pip download synthetic-package",
            "python -m pip install synthetic-package",
            "npm install synthetic-package",
            "git clone synthetic:source-target",
            "py -3.11 -m venv .tmp/arbitrary-environment",
        )
        for example in unauthorized_dependency_examples:
            normalized = example.replace("\\", "/")
            with self.subTest(unauthorized_dependency_command=example):
                self.assertIsNotNone(dependency_command_form.search(normalized))
                self.assertNotIn(example, expected_dependency_commands)
                self.assertNotIn(example, dependency_gate_commands)
        exact_equality_alias_examples = (
            "iwr synthetic:extra-acquisition",
            "irm synthetic:extra-acquisition",
            "choco install synthetic-package",
            "winget install synthetic-package",
            "scoop install synthetic-package",
            "uv pip install synthetic-package",
            "pnpm add synthetic-package",
            "yarn add synthetic-package",
        )
        for example in exact_equality_alias_examples:
            mutated_gate = (*dependency_gate_commands, example)
            with self.subTest(exact_equality_alias=example):
                self.assertNotEqual(
                    Counter(mutated_gate),
                    Counter(expected_dependency_commands),
                )
                self.assertNotEqual(
                    mutated_gate,
                    expected_dependency_commands,
                )

    def test_task_9_docs_hold_review_pending_status(self) -> None:
        conservative_status = (
            "Task 9 is implemented; its independent review gate must pass "
            "before Task 10. Task 10/public-material evaluation, the final "
            "lockbox, canonical staging/acceptance, push, and merge remain blocked."
        )
        for relative_path in (
            "docs/thesis/ROADMAP.md",
            (
                "research/experiments/"
                "EMOTION-STATE-002-phase-b-public-data-feasibility.md"
            ),
        ):
            text = (ROOT / relative_path).read_text(encoding="utf-8-sig")
            with self.subTest(path=relative_path):
                self.assertIn(conservative_status, text)
                self.assertNotIn("independently approved", text)

    def test_task_9_docs_state_production_lockbox_is_unavailable(self) -> None:
        boundary = (
            "The production lockbox evaluator remains unavailable; "
            "authorization alone does not wire it."
        )
        command_map = (ROOT / "docs/product/COMMANDS.md").read_text(
            encoding="utf-8-sig"
        )
        heading = "### Explicit gate: final lockbox"
        lockbox_section = command_map.split(heading, 1)[1].split("\n### ", 1)[0]
        self.assertIn(boundary, lockbox_section)
        protocol = (
            ROOT
            / "research/experiments/"
            "EMOTION-STATE-002-phase-b-public-data-feasibility.md"
        ).read_text(encoding="utf-8-sig")
        self.assertIn(boundary, protocol)

    def test_task_9_production_publication_sections_fail_closed_without_state(
        self,
    ) -> None:
        validator = ROOT / "scripts/validate_emotion_state_002_phase_b.py"
        fixed_paths = (
            ROOT / ".tmp/emotion-state-002-phase-b/state.json",
            ROOT / ".tmp/emotion-state-002-phase-b/publication/transaction.json",
            ROOT / ".tmp/emotion-state-002-phase-b/publication/receipt.json",
            ROOT
            / "research/experiments/generated/"
            "EMOTION-STATE-002-phase-b-public-data-feasibility/result.json",
            ROOT
            / "research/experiments/generated/"
            "EMOTION-STATE-002-phase-b-public-data-feasibility/report.md",
        )
        before = tuple(os.path.lexists(path) for path in fixed_paths)
        self.assertEqual(before, (False,) * len(fixed_paths))
        commands = (
            (
                "candidate",
                "--receipt",
                ".tmp/emotion-state-002-phase-b/publication/receipt.json",
            ),
            ("checkpoint",),
        )
        for arguments in commands:
            completed = subprocess.run(
                [str(EVALUATION_PYTHON), str(validator), *arguments],
                cwd=ROOT,
                capture_output=True,
                check=False,
                text=True,
            )
            with self.subTest(section=arguments[0]):
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stdout, "")
                self.assertIn(
                    f"Phase B validation failed: {arguments[0]}",
                    completed.stderr,
                )
                self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(
            tuple(os.path.lexists(path) for path in fixed_paths),
            before,
        )

    def test_crema_label_ledger_validates_and_fails_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_config,
            validate_crema_label_ledger,
        )

        config = validate_config(load_json_strict(CONFIG))
        ledger: dict[str, Any] = {
            "eligible_concordant_unique_winner": 6570,
            "summary_voice_tie": 644,
            "raw_audio_vote_tie": 204,
            "unique_winner_disagreement": 23,
            "label_counts": {
                "A": 951,
                "D": 500,
                "F": 613,
                "H": 330,
                "N": 3834,
                "S": 342,
            },
            "included_wav_count": 7441,
            "eligible_actor_count": 91,
            "eligible_sentence_count": 12,
            "source_binding": {
                key: config["crema_label_contract"][key]
                for key in (
                    "finished_responses_sha256",
                    "summary_table_sha256",
                    "raw_join_field",
                    "raw_modality_field",
                    "raw_audio_modality",
                    "raw_label_field",
                    "summary_join_field",
                    "summary_label_field",
                )
            },
        }
        validate_crema_label_ledger(ledger, config)

        count_paths = [
            (key,) for key in (
                "eligible_concordant_unique_winner",
                "summary_voice_tie",
                "raw_audio_vote_tie",
                "unique_winner_disagreement",
                "included_wav_count",
                "eligible_actor_count",
                "eligible_sentence_count",
            )
        ] + [("label_counts", label) for label in ledger["label_counts"]]
        for path in count_paths:
            mutated = deepcopy(ledger)
            current = self._value_at(mutated, path)
            self._replace_at(mutated, path, current + 1)
            with self.subTest(count=path):
                with self.assertRaises(ValueError):
                    validate_crema_label_ledger(mutated, config)

        field_paths = [(), ("label_counts",), ("source_binding",)]
        for path in field_paths:
            for key in self._value_at(ledger, path):
                mutated = deepcopy(ledger)
                mapping = self._value_at(mutated, path)
                mapping[f"renamed_{key}"] = mapping.pop(key)
                with self.subTest(field=path + (key,)):
                    with self.assertRaises(ValueError):
                        validate_crema_label_ledger(mutated, config)

        mutated = deepcopy(ledger)
        mutated["label_counts"]["Z"] = mutated["label_counts"].pop("A")
        with self.assertRaises(ValueError):
            validate_crema_label_ledger(mutated, config)

        mutated_config = deepcopy(config)
        mutated_config["crema_label_contract"]["raw_audio_modality"] = "2"
        with self.assertRaises(ValueError):
            validate_config(mutated_config)

        with tempfile.TemporaryDirectory() as temporary_directory:
            duplicate_keys = Path(temporary_directory) / "duplicate-keys.json"
            duplicate_keys.write_text('{"same": 1, "same": 2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_json_strict(duplicate_keys)

    @staticmethod
    def _scalar_paths(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
        if isinstance(value, dict):
            return [
                nested_path
                for key, nested_value in value.items()
                for nested_path in PhaseBContractTests._scalar_paths(
                    nested_value,
                    path + (key,),
                )
            ]
        if isinstance(value, list):
            return [
                nested_path
                for index, nested_value in enumerate(value)
                for nested_path in PhaseBContractTests._scalar_paths(
                    nested_value,
                    path + (index,),
                )
            ]
        return [path]

    @staticmethod
    def _mapping_paths(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
        if isinstance(value, dict):
            return [path] + [
                nested_path
                for key, nested_value in value.items()
                for nested_path in PhaseBContractTests._mapping_paths(
                    nested_value,
                    path + (key,),
                )
            ]
        if isinstance(value, list):
            return [
                nested_path
                for index, nested_value in enumerate(value)
                for nested_path in PhaseBContractTests._mapping_paths(
                    nested_value,
                    path + (index,),
                )
            ]
        return []

    @staticmethod
    def _value_at(value: Any, path: tuple[str | int, ...]) -> Any:
        for key in path:
            value = value[key]
        return value

    @staticmethod
    def _replace_at(value: Any, path: tuple[str | int, ...], replacement: Any) -> None:
        parent = PhaseBContractTests._value_at(value, path[:-1])
        parent[path[-1]] = replacement

    @staticmethod
    def _different_value(value: Any) -> Any:
        if isinstance(value, bool):
            return not value
        if value is None:
            return "not-null"
        if isinstance(value, str):
            return "mutated"
        if isinstance(value, int):
            return value + 1
        if isinstance(value, float):
            return value + 1.0
        raise AssertionError(f"unexpected scalar type: {type(value)!r}")


class ActorSplitTests(unittest.TestCase):
    LABELS = ("A", "D", "F", "H", "N", "S")
    SENTENCES = tuple(f"S{index:02d}" for index in range(12))
    PARTITION_ORDER = (
        "training_discovery",
        "calibration",
        "balanced_diagnostic",
        "final_lockbox",
    )
    PARTITION_COUNTS = {
        "training_discovery": 35,
        "calibration": 13,
        "balanced_diagnostic": 13,
        "final_lockbox": 30,
    }
    SEED_DIGEST = hashlib.sha256(b"synthetic-phase-b-config").hexdigest()
    ALTERNATE_SEED_DIGEST = hashlib.sha256(
        b"synthetic-phase-b-config-alternate"
    ).hexdigest()
    EXPECTED_VARIED_DIGEST = (
        "cf6e5b6c5488d6094ae7d44e239bf62776c478ce43dae6220421ff52196843bd"
    )
    EXPECTED_VARIED_PARTITION_ACTORS = {
        "training_discovery": (
            "1002", "1007", "1008", "1012", "1017", "1020", "1022",
            "1024", "1027", "1032", "1033", "1035", "1037", "1039",
            "1043", "1047", "1048", "1052", "1053", "1057", "1058",
            "1062", "1067", "1070", "1072", "1073", "1077", "1078",
            "1082", "1083", "1085", "1087", "1088", "1089", "1090",
        ),
        "calibration": (
            "1003", "1015", "1018", "1025", "1034", "1038", "1040",
            "1054", "1059", "1068", "1069", "1079", "1080",
        ),
        "balanced_diagnostic": (
            "1004", "1009", "1010", "1023", "1026", "1042", "1049",
            "1050", "1051", "1060", "1065", "1074", "1075",
        ),
        "final_lockbox": (
            "1001", "1005", "1006", "1011", "1013", "1014", "1016",
            "1019", "1021", "1028", "1029", "1030", "1031", "1036",
            "1041", "1044", "1045", "1046", "1055", "1056", "1061",
            "1063", "1064", "1066", "1071", "1076", "1081", "1084",
            "1086", "1091",
        ),
    }

    @classmethod
    def _records(
        cls,
        actor_count: int = 91,
        *,
        varied_vectors: bool = False,
    ) -> tuple[Any, ...]:
        from scripts.emotion_state_phase_b_evaluation import CremaLabelRecord

        records = []
        filename_emotions = ("ANG", "DIS", "FEA", "HAP", "NEU", "SAD")
        for actor_index in range(actor_count):
            actor_id = f"{1001 + actor_index:04d}"
            for sentence_index, sentence_id in enumerate(cls.SENTENCES):
                label = cls.LABELS[(actor_index + sentence_index) % len(cls.LABELS)]
                records.append(CremaLabelRecord(
                    clip_stem=(
                        f"{actor_id}_{sentence_id}_"
                        f"{filename_emotions[cls.LABELS.index(label)]}_XX"
                    ),
                    actor_id=actor_id,
                    sentence_id=sentence_id,
                    label=label,
                    abstention_reason=None,
                    vote_distribution=((label, 1),),
                    vote_agreement=1.0,
                    vote_entropy=0.0,
                ))
            if varied_vectors:
                for extra_index in range(actor_index % 5):
                    sentence_id = cls.SENTENCES[
                        (actor_index * 3 + extra_index) % len(cls.SENTENCES)
                    ]
                    label = cls.LABELS[
                        (actor_index * 2 + extra_index) % len(cls.LABELS)
                    ]
                    records.append(CremaLabelRecord(
                        clip_stem=(
                            f"{actor_id}_{sentence_id}_"
                            f"{filename_emotions[cls.LABELS.index(label)]}_HI"
                        ),
                        actor_id=actor_id,
                        sentence_id=sentence_id,
                        label=label,
                        abstention_reason=None,
                        vote_distribution=((label, 1),),
                        vote_agreement=1.0,
                        vote_entropy=0.0,
                    ))
        return tuple(records)

    @classmethod
    def _fixed_expected_assignment(cls) -> dict[str, str]:
        return {
            actor_id: partition
            for partition, actor_ids in cls.EXPECTED_VARIED_PARTITION_ACTORS.items()
            for actor_id in actor_ids
        }

    def test_exact_actor_partition_contract_and_aggregate_only_summary(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_splits import (
            build_actor_split,
            validate_actor_split,
        )

        records = self._records()
        assignment = build_actor_split(records, self.SEED_DIGEST)
        actors = {record.actor_id for record in records}
        actors_by_partition = {
            partition: {
                actor_id
                for actor_id, assigned_partition in assignment.items()
                if assigned_partition == partition
            }
            for partition in self.PARTITION_ORDER
        }

        self.assertEqual(Counter(assignment.values()), self.PARTITION_COUNTS)
        self.assertEqual(set(assignment), actors)
        self.assertEqual(set().union(*actors_by_partition.values()), actors)
        for index, partition in enumerate(self.PARTITION_ORDER):
            self.assertEqual(
                len(actors_by_partition[partition]),
                self.PARTITION_COUNTS[partition],
            )
            for other_partition in self.PARTITION_ORDER[index + 1:]:
                self.assertTrue(
                    actors_by_partition[partition].isdisjoint(
                        actors_by_partition[other_partition]
                    )
                )
            partition_records = [
                record
                for record in records
                if assignment[record.actor_id] == partition
            ]
            self.assertEqual(
                {record.sentence_id for record in partition_records},
                set(self.SENTENCES),
            )
            self.assertEqual(
                {record.label for record in partition_records},
                set(self.LABELS),
            )

        summary = validate_actor_split(records, assignment)
        self.assertEqual(summary["partition_actor_counts"], self.PARTITION_COUNTS)
        self.assertEqual(
            summary["partition_sentence_presence_counts"],
            {partition: 12 for partition in self.PARTITION_ORDER},
        )
        self.assertEqual(
            summary["partition_label_presence_counts"],
            {partition: 6 for partition in self.PARTITION_ORDER},
        )
        serialized_summary = json.dumps(summary, sort_keys=True)
        self.assertFalse(any(actor_id in serialized_summary for actor_id in actors))
        self.assertNotIn("assignments", summary)
        self.assertNotIn("actors", summary)
        self.assertNotIn("actor_exclusivity_validated", summary)

    def test_frozen_vector_score_order_and_row_permutation_stability(self) -> None:
        from scripts.emotion_state_phase_b_splits import (
            PARTITION_ORDER,
            build_actor_split,
        )

        varied_records = self._records(varied_vectors=True)
        expected = self._fixed_expected_assignment()
        actor_record_counts = Counter(
            record.actor_id for record in varied_records
        )
        self.assertEqual(len(actor_record_counts), 91)
        self.assertGreater(
            len(set(actor_record_counts.values())),
            1,
        )
        self.assertEqual(
            build_actor_split(varied_records, self.SEED_DIGEST),
            expected,
        )
        self.assertEqual(
            build_actor_split(tuple(reversed(varied_records)), self.SEED_DIGEST),
            expected,
        )

        tied_records = self._records()
        tied_assignment = build_actor_split(tied_records, self.SEED_DIGEST)
        first_actor = min(
            {record.actor_id for record in tied_records},
            key=lambda actor_id: hashlib.sha256(
                f"{self.SEED_DIGEST}:{actor_id}".encode("utf-8")
            ).hexdigest(),
        )
        self.assertEqual(tuple(PARTITION_ORDER), self.PARTITION_ORDER)
        self.assertEqual(
            tied_assignment[first_actor],
            self.PARTITION_ORDER[0],
        )

    def test_digest_rejects_invalid_split_before_minting_commitment(self) -> None:
        from scripts.emotion_state_phase_b_splits import (
            build_actor_split,
            split_manifest_digest,
        )

        records = self._records()
        assignment = build_actor_split(records, self.SEED_DIGEST)
        invalid = dict(assignment)
        actor_id = sorted(invalid)[0]
        invalid[actor_id] = next(
            partition
            for partition in self.PARTITION_ORDER
            if partition != invalid[actor_id]
        )

        with self.assertRaisesRegex(ValueError, "partition actor capacities"):
            split_manifest_digest(records, invalid, self.SEED_DIGEST)

    def test_digest_binds_fixed_assignment_and_configuration_oracle(self) -> None:
        from scripts.emotion_state_phase_b_splits import (
            build_actor_split,
            split_manifest_digest,
        )

        records = self._records(varied_vectors=True)
        assignment = build_actor_split(records, self.SEED_DIGEST)
        digest = split_manifest_digest(
            records,
            assignment,
            self.SEED_DIGEST,
        )
        with self.assertRaises(TypeError):
            split_manifest_digest(records, assignment)
        self.assertEqual(digest, self.EXPECTED_VARIED_DIGEST)
        self.assertEqual(
            split_manifest_digest(
                tuple(reversed(records)),
                assignment,
                self.SEED_DIGEST,
            ),
            digest,
        )
        self.assertNotEqual(
            split_manifest_digest(
                records,
                assignment,
                self.ALTERNATE_SEED_DIGEST,
            ),
            digest,
        )
        with self.assertRaisesRegex(ValueError, "seed digest"):
            split_manifest_digest(records, assignment, "not-a-digest")

    def test_valid_capacity_preserving_actor_swap_changes_digest(self) -> None:
        from scripts.emotion_state_phase_b_splits import (
            build_actor_split,
            split_manifest_digest,
            validate_actor_split,
        )

        records = self._records(varied_vectors=True)
        assignment = build_actor_split(records, self.SEED_DIGEST)
        swapped = dict(assignment)
        training_actor = next(
            actor_id
            for actor_id in sorted(swapped)
            if swapped[actor_id] == "training_discovery"
        )
        calibration_actor = next(
            actor_id
            for actor_id in sorted(swapped)
            if swapped[actor_id] == "calibration"
        )
        swapped[training_actor], swapped[calibration_actor] = (
            swapped[calibration_actor],
            swapped[training_actor],
        )

        validate_actor_split(records, swapped)
        self.assertNotEqual(
            split_manifest_digest(records, swapped, self.SEED_DIGEST),
            split_manifest_digest(records, assignment, self.SEED_DIGEST),
        )

    def test_capacity_preserving_swaps_reject_missing_label_and_sentence(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_splits import (
            build_actor_split,
            split_manifest_digest,
            validate_actor_split,
        )

        base_records = self._records(varied_vectors=True)
        assignment = build_actor_split(base_records, self.SEED_DIGEST)
        training_actors = sorted(
            actor_id
            for actor_id, partition in assignment.items()
            if partition == "training_discovery"
        )
        calibration_actor = next(
            actor_id
            for actor_id in sorted(assignment)
            if assignment[actor_id] == "calibration"
        )
        keeper_actor = training_actors[0]
        stripped_actors = set(training_actors[1:]) | {calibration_actor}

        for field, missing_value, replacement_value, error_pattern in (
            ("label", "A", "N", "missing a required label"),
            ("sentence_id", "S11", "S10", "missing a required sentence"),
        ):
            with self.subTest(field=field):
                records = tuple(
                    replace(record, **{field: replacement_value})
                    if (
                        record.actor_id in stripped_actors
                        and getattr(record, field) == missing_value
                    )
                    else record
                    for record in base_records
                )
                validate_actor_split(records, assignment)
                swapped = dict(assignment)
                swapped[keeper_actor], swapped[calibration_actor] = (
                    swapped[calibration_actor],
                    swapped[keeper_actor],
                )
                self.assertEqual(
                    Counter(swapped.values()),
                    self.PARTITION_COUNTS,
                )
                with self.assertRaisesRegex(ValueError, error_pattern):
                    validate_actor_split(records, swapped)
                with self.assertRaisesRegex(ValueError, error_pattern):
                    split_manifest_digest(
                        records,
                        swapped,
                        self.SEED_DIGEST,
                    )

    def test_actor_count_90_and_92_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_splits import build_actor_split

        for actor_count in (90, 92):
            with self.subTest(actor_count=actor_count):
                with self.assertRaisesRegex(ValueError, "exactly 91 actors"):
                    build_actor_split(
                        self._records(actor_count),
                        self.SEED_DIGEST,
                    )

    def test_malformed_seed_and_record_inputs_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_splits import build_actor_split

        records = self._records()
        for malformed_seed in (
            "",
            "0" * 63,
            "g" * 64,
            0,
            None,
        ):
            with self.subTest(seed=malformed_seed):
                with self.assertRaisesRegex(ValueError, "seed digest"):
                    build_actor_split(records, malformed_seed)

        malformed_records = []
        malformed_records.append(
            records[:1] + (object(),) + records[2:]
        )
        malformed_records.append(
            (replace(records[0], label=None, abstention_reason="tie"),)
            + records[1:]
        )
        malformed_records.append(
            (replace(records[0], label="Z"),) + records[1:]
        )
        malformed_records.append(
            (replace(records[0], actor_id="actor"),) + records[1:]
        )
        malformed_records.append(
            (replace(records[0], sentence_id="sentence"),) + records[1:]
        )
        malformed_records.append(
            records[:1]
            + (replace(records[1], clip_stem=records[0].clip_stem),)
            + records[2:]
        )
        for index, malformed in enumerate(malformed_records):
            with self.subTest(record_mutation=index):
                with self.assertRaises(ValueError):
                    build_actor_split(malformed, self.SEED_DIGEST)

    def test_malformed_assignment_and_dependency_roles_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_splits import (
            DEPENDENCY_ROLES,
            build_actor_split,
            split_manifest_digest,
            validate_actor_split,
        )

        records = self._records()
        assignment = build_actor_split(records, self.SEED_DIGEST)
        missing = dict(assignment)
        del missing[next(iter(missing))]
        extra = dict(assignment)
        extra["9999"] = self.PARTITION_ORDER[0]
        invalid_partition = dict(assignment)
        invalid_partition[next(iter(invalid_partition))] = "test"
        for malformed in ([], missing, extra, invalid_partition):
            with self.subTest(assignment_type=type(malformed).__name__):
                with self.assertRaises(ValueError):
                    validate_actor_split(records, malformed)
                with self.assertRaises(ValueError):
                    split_manifest_digest(
                        records,
                        malformed,
                        self.SEED_DIGEST,
                    )

        mutated_roles = dict(DEPENDENCY_ROLES)
        mutated_roles["scripted_scenario"] = "exclusion_group"
        with patch(
            "scripts.emotion_state_phase_b_splits.DEPENDENCY_ROLES",
            mutated_roles,
        ):
            with self.assertRaisesRegex(ValueError, "dependency roles"):
                validate_actor_split(records, assignment)
            with self.assertRaisesRegex(ValueError, "dependency roles"):
                split_manifest_digest(
                    records,
                    assignment,
                    self.SEED_DIGEST,
                )

    def test_fabricated_summary_has_no_public_semantic_approval_path(self) -> None:
        import scripts.validate_emotion_state_002_phase_b as validator

        self.assertFalse(
            hasattr(validator, "validate_actor_split_summary"),
            "fabricated summaries must not have a public semantic approval API",
        )

    def test_filename_and_vote_metadata_do_not_influence_assignment(self) -> None:
        from scripts.emotion_state_phase_b_splits import build_actor_split

        records = self._records(varied_vectors=True)
        assignment = build_actor_split(records, self.SEED_DIGEST)
        misleading_metadata = tuple(
            replace(
                record,
                clip_stem=f"misleading-ANG-model-output-{index:04d}",
                vote_distribution=(("N", 999),),
                vote_agreement=0.123,
                vote_entropy=9.99,
            )
            for index, record in enumerate(records)
        )
        self.assertEqual(
            build_actor_split(misleading_metadata, self.SEED_DIGEST),
            assignment,
        )


class AcousticFeatureTests(unittest.TestCase):
    FEATURE_NAMES = (
        "duration_seconds",
        "silence_ratio",
        "voiced_fraction",
        "f0_median_hz",
        "f0_iqr_hz",
        "f0_range_hz",
        "rms_dbfs_mean",
        "rms_dbfs_std",
        "rms_dbfs_p90_minus_p10",
        "zero_crossing_rate_mean",
        "zero_crossing_rate_std",
        "spectral_centroid_hz_mean",
        "spectral_centroid_hz_std",
        "spectral_bandwidth_hz_mean",
        "spectral_bandwidth_hz_std",
        "spectral_rolloff_85_hz_mean",
        "spectral_rolloff_85_hz_std",
    )

    @staticmethod
    def _write_tone(
        path: Path, *, hz: float, seconds: float, amplitude: float
    ) -> None:
        import math
        import struct
        import wave

        sample_rate = 16000
        count = int(sample_rate * seconds)
        samples = [
            max(-32768, min(32767, round(
                amplitude * 32767 * math.sin(2 * math.pi * hz * index / sample_rate)
            )))
            for index in range(count)
        ]
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(struct.pack("<" + "h" * len(samples), *samples))

    @staticmethod
    def _write_pcm16(
        path: Path,
        samples: list[int],
        *,
        channels: int = 1,
        sample_rate: int = 16000,
    ) -> None:
        import struct
        import wave

        with wave.open(str(path), "wb") as output:
            output.setnchannels(channels)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(struct.pack("<" + "h" * len(samples), *samples))

    @staticmethod
    def _tone_frame(hz: float, amplitude: float = 0.5) -> Any:
        import numpy as np

        indexes = np.arange(400, dtype=np.float64)
        return amplitude * np.sin(2.0 * np.pi * hz * indexes / 16000.0)

    @staticmethod
    def _deterministic_noise(count: int) -> list[int]:
        state = 0x12345678
        samples: list[int] = []
        for _ in range(count):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            samples.append(((state >> 16) & 0xFFFF) - 32768)
        return samples

    def test_200_hz_tone_produces_finite_expected_f0_and_feature_order(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_features import (
            FEATURE_NAMES,
            extract_acoustic_features,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.wav"
            self._write_tone(path, hz=200.0, seconds=1.0, amplitude=0.5)
            features = extract_acoustic_features(path)

        self.assertEqual(FEATURE_NAMES, self.FEATURE_NAMES)
        self.assertEqual(tuple(features), self.FEATURE_NAMES)
        self.assertAlmostEqual(features["f0_median_hz"], 200.0, delta=2.0)
        self.assertTrue(
            all(
                isinstance(value, float) and math.isfinite(value)
                for value in features.values()
            )
        )

    def test_amplitude_scaling_preserves_duration_and_f0_but_changes_rms(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_features import extract_acoustic_features

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            quiet_path = root / "quiet.wav"
            loud_path = root / "loud.wav"
            self._write_tone(quiet_path, hz=200.0, seconds=1.0, amplitude=0.2)
            self._write_tone(loud_path, hz=200.0, seconds=1.0, amplitude=0.6)
            quiet = extract_acoustic_features(quiet_path)
            loud = extract_acoustic_features(loud_path)

        self.assertEqual(quiet["duration_seconds"], loud["duration_seconds"])
        self.assertAlmostEqual(
            quiet["f0_median_hz"],
            loud["f0_median_hz"],
            places=12,
        )
        self.assertGreater(loud["rms_dbfs_mean"], quiet["rms_dbfs_mean"])

    def test_duration_scaling_changes_duration_without_changing_f0(self) -> None:
        from scripts.emotion_state_phase_b_features import extract_acoustic_features

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            short_path = root / "short.wav"
            long_path = root / "long.wav"
            self._write_tone(short_path, hz=200.0, seconds=0.5, amplitude=0.5)
            self._write_tone(long_path, hz=200.0, seconds=1.0, amplitude=0.5)
            short = extract_acoustic_features(short_path)
            long = extract_acoustic_features(long_path)

        self.assertEqual(short["duration_seconds"], 0.5)
        self.assertEqual(long["duration_seconds"], 1.0)
        self.assertAlmostEqual(
            short["f0_median_hz"],
            long["f0_median_hz"],
            places=12,
        )

    def test_silence_near_silence_and_insufficient_voicing_reject(self) -> None:
        import struct
        import wave

        from scripts.emotion_state_phase_b_features import (
            FeatureExtractionError,
            extract_acoustic_features,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            silence = root / "silence.wav"
            near_silence = root / "near-silence.wav"
            two_frames = root / "two-frames.wav"
            self._write_pcm16(silence, [0] * 8000)
            self._write_pcm16(near_silence, [1, -1] * 4000)
            self._write_tone(
                two_frames,
                hz=200.0,
                seconds=0.035,
                amplitude=0.5,
            )

            with wave.open(str(near_silence), "rb") as source:
                payload = source.readframes(source.getnframes())
            near_silence_pcm = struct.unpack(
                "<" + "h" * (len(payload) // 2),
                payload,
            )
            self.assertTrue(any(sample != 0 for sample in near_silence_pcm))
            self.assertEqual(max(abs(sample) for sample in near_silence_pcm), 1)

            for path in (silence, near_silence, two_frames):
                with self.subTest(path=path.name):
                    with self.assertRaises(FeatureExtractionError):
                        extract_acoustic_features(path)

    def test_dc_and_deterministic_unvoiced_noise_reject(self) -> None:
        from scripts.emotion_state_phase_b_features import (
            FeatureExtractionError,
            extract_acoustic_features,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dc = root / "dc.wav"
            noise = root / "noise.wav"
            self._write_pcm16(dc, [1000] * 720)
            self._write_pcm16(noise, self._deterministic_noise(720))

            for path in (dc, noise):
                with self.subTest(path=path.name):
                    with self.assertRaisesRegex(
                        FeatureExtractionError,
                        "voiced",
                    ):
                        extract_acoustic_features(path)

    def test_dc_biased_low_amplitude_tone_is_mean_centered_for_f0(self) -> None:
        from scripts.emotion_state_phase_b_features import extract_acoustic_features

        sample_rate = 16000
        samples = [
            round(
                1000
                + 300
                * math.sin(2 * math.pi * 150.0 * index / sample_rate)
            )
            for index in range(sample_rate)
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dc-biased-tone.wav"
            self._write_pcm16(path, samples)
            features = extract_acoustic_features(path)

        self.assertAlmostEqual(features["f0_median_hz"], 150.0, delta=2.0)

    def test_mixed_frames_freeze_duration_silence_voiced_and_f0_summaries(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_features import _summarize

        noise = np.asarray(
            self._deterministic_noise(400),
            dtype=np.float64,
        ) / 65536.0
        frames = np.stack(
            [
                np.zeros(400, dtype=np.float64),
                np.tile(
                    np.asarray([1.0, -1.0], dtype=np.float64) / 32768.0,
                    200,
                ),
                self._tone_frame(100.0),
                self._tone_frame(100.0),
                self._tone_frame(200.0),
                self._tone_frame(200.0),
                self._tone_frame(400.0),
                noise,
            ]
        )
        features = _summarize(
            frames,
            sample_count=1520,
            sample_rate=16000,
        )

        self.assertEqual(features["duration_seconds"], 0.095)
        self.assertEqual(features["silence_ratio"], 0.25)
        self.assertEqual(features["voiced_fraction"], 0.625)
        self.assertAlmostEqual(features["f0_median_hz"], 200.0, places=12)
        self.assertAlmostEqual(features["f0_iqr_hz"], 100.0, places=12)
        self.assertAlmostEqual(features["f0_range_hz"], 300.0, places=12)

    def test_pcm16_silence_floor_and_population_rms_summaries(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_features import _summarize

        frames = np.stack(
            [
                np.zeros(400, dtype=np.float64),
                self._tone_frame(200.0, amplitude=0.25),
                self._tone_frame(200.0, amplitude=0.5),
                self._tone_frame(200.0, amplitude=0.75),
            ]
        )
        features = _summarize(
            frames,
            sample_count=880,
            sample_rate=16000,
        )

        # Analytical values for RMS dBFS sequence:
        # [20*log10(1/655360), 20*log10(0.25/sqrt(2)),
        #  20*log10(0.5/sqrt(2)), 20*log10(0.75/sqrt(2))].
        self.assertAlmostEqual(
            features["rms_dbfs_mean"],
            -36.48026823859957,
            places=10,
        )
        self.assertAlmostEqual(
            features["rms_dbfs_std"],
            46.227130379274016,
            places=10,
        )
        self.assertAlmostEqual(
            features["rms_dbfs_p90_minus_p10"],
            79.3805467205516,
            places=10,
        )

    def test_zcr_is_exact_and_uses_only_nonsilent_frames(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_features import _summarize

        square = np.tile(
            np.concatenate(
                (
                    np.full(40, 0.25, dtype=np.float64),
                    np.full(40, -0.25, dtype=np.float64),
                )
            ),
            5,
        )
        features = _summarize(
            np.stack(
                [
                    np.zeros(400, dtype=np.float64),
                    square,
                    square,
                    square,
                ]
            ),
            sample_count=880,
            sample_rate=16000,
        )

        self.assertAlmostEqual(
            features["zero_crossing_rate_mean"],
            9.0 / 399.0,
            places=15,
        )
        self.assertEqual(features["zero_crossing_rate_std"], 0.0)

    def test_hann_power_spectral_moments_and_rolloff_are_analytical(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_features import _summarize

        indexes = np.arange(400, dtype=np.float64)
        tone_200 = 0.2 * np.cos(
            2.0 * np.pi * 200.0 * indexes / 16000.0
        )
        tone_400 = 0.2 * np.cos(
            2.0 * np.pi * 400.0 * indexes / 16000.0
        )
        features = _summarize(
            np.stack([tone_200, tone_400, tone_200 + tone_400]),
            sample_count=720,
            sample_rate=16000,
        )

        # A bin-centered periodic-Hann tone has power ratio 1:4:1 across
        # adjacent:center:adjacent bins, so bandwidth is 40/sqrt(3) Hz.
        # The equal 200+400 Hz mixture has centroid 300 Hz and bandwidth
        # sqrt(100**2 + (40/sqrt(3))**2).
        self.assertAlmostEqual(
            features["spectral_centroid_hz_mean"],
            300.0,
            places=10,
        )
        self.assertAlmostEqual(
            features["spectral_centroid_hz_std"],
            81.64965809277261,
            places=10,
        )
        self.assertAlmostEqual(
            features["spectral_bandwidth_hz_mean"],
            49.60668344136925,
            places=10,
        )
        self.assertAlmostEqual(
            features["spectral_bandwidth_hz_std"],
            37.49458127002419,
            places=10,
        )
        self.assertAlmostEqual(
            features["spectral_rolloff_85_hz_mean"],
            360.0,
            places=10,
        )
        self.assertAlmostEqual(
            features["spectral_rolloff_85_hz_std"],
            86.40987597877147,
            places=10,
        )

    def test_autocorrelation_peak_ties_choose_lowest_lag(self) -> None:
        from scripts.emotion_state_phase_b_features import (
            _normalized_autocorrelation_f0,
        )

        f0_hz, peak = _normalized_autocorrelation_f0(
            self._tone_frame(400.0),
            sample_rate=16000,
            minimum_hz=75.0,
            maximum_hz=400.0,
        )
        self.assertEqual(f0_hz, 400.0)
        self.assertAlmostEqual(peak, 1.0, places=15)

    def test_unsupported_wav_formats_malformed_riff_and_clipping_reject(
        self,
    ) -> None:
        import struct
        import wave

        from scripts.emotion_state_phase_b_features import (
            FeatureExtractionError,
            extract_acoustic_features,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stereo = root / "stereo.wav"
            eight_bit = root / "eight-bit.wav"
            wrong_rate = root / "wrong-rate.wav"
            compressed = root / "compressed.wav"
            malformed = root / "malformed.wav"
            clipped_positive = root / "clipped-positive.wav"
            clipped_negative = root / "clipped-negative.wav"

            self._write_pcm16(stereo, [1000, -1000] * 400, channels=2)
            with wave.open(str(eight_bit), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(1)
                output.setframerate(16000)
                output.writeframes(bytes([128] * 800))
            self._write_pcm16(
                wrong_rate,
                [1000, -1000] * 400,
                sample_rate=44100,
            )

            compressed_data = bytes([0] * 800)
            compressed_fmt = struct.pack(
                "<HHIIHH",
                6,
                1,
                16000,
                16000,
                1,
                8,
            )
            compressed_body = (
                b"fmt "
                + struct.pack("<I", len(compressed_fmt))
                + compressed_fmt
                + b"data"
                + struct.pack("<I", len(compressed_data))
                + compressed_data
            )
            compressed.write_bytes(
                b"RIFF"
                + struct.pack("<I", 4 + len(compressed_body))
                + b"WAVE"
                + compressed_body
            )
            malformed.write_bytes(b"not-a-wave")
            self._write_pcm16(
                clipped_positive,
                [32767] + [1000, -1000] * 400,
            )
            self._write_pcm16(
                clipped_negative,
                [-32768] + [1000, -1000] * 400,
            )

            for path in (
                stereo,
                eight_bit,
                wrong_rate,
                compressed,
                malformed,
                clipped_positive,
                clipped_negative,
            ):
                with self.subTest(path=path.name):
                    with self.assertRaises(FeatureExtractionError):
                        extract_acoustic_features(path)

    def test_empty_and_incomplete_wavs_reject(self) -> None:
        from scripts.emotion_state_phase_b_features import (
            FeatureExtractionError,
            extract_acoustic_features,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = root / "empty.wav"
            incomplete = root / "incomplete.wav"
            self._write_pcm16(empty, [])
            self._write_pcm16(incomplete, [1000, -1000] * 199 + [1000])

            for path in (empty, incomplete):
                with self.subTest(path=path.name):
                    with self.assertRaises(FeatureExtractionError):
                        extract_acoustic_features(path)

    def test_repeated_extraction_is_canonical_json_byte_deterministic(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_features import extract_acoustic_features

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.wav"
            self._write_tone(path, hz=200.0, seconds=1.0, amplitude=0.5)
            first = extract_acoustic_features(path)
            second = extract_acoustic_features(path)

        def canonical_bytes(payload: dict[str, float]) -> bytes:
            return json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")

        self.assertEqual(canonical_bytes(first), canonical_bytes(second))

    def test_feature_vector_is_canonical_and_rejects_imputation_and_schema_drift(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_features import (
            FeatureExtractionError,
            feature_vector,
        )

        canonical = {
            name: float(index)
            for index, name in enumerate(self.FEATURE_NAMES)
        }
        reversed_row = dict(reversed(tuple(canonical.items())))
        self.assertEqual(
            feature_vector(reversed_row),
            tuple(canonical[name] for name in self.FEATURE_NAMES),
        )

        imputed = dict(canonical)
        imputed["f0_median_hz"] = float("nan")
        with self.assertRaisesRegex(FeatureExtractionError, "non-finite"):
            feature_vector(imputed)

        missing = dict(canonical)
        del missing["f0_median_hz"]
        with self.assertRaisesRegex(FeatureExtractionError, "fields"):
            feature_vector(missing)

        extra = dict(canonical)
        extra["filename"] = 1.0
        with self.assertRaisesRegex(FeatureExtractionError, "fields"):
            feature_vector(extra)

    def test_feature_order_mutation_and_non_finite_frames_reject(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_features import (
            FeatureExtractionError,
            _summarize,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_feature_schema,
        )

        feature_schema = load_json_strict(FEATURE_SCHEMA)
        mutated = deepcopy(feature_schema)
        mutated["ordered_features"][0], mutated["ordered_features"][1] = (
            mutated["ordered_features"][1],
            mutated["ordered_features"][0],
        )
        with self.assertRaisesRegex(ValueError, "ordered acoustic features"):
            validate_feature_schema(mutated)

        frames = np.zeros((3, 400), dtype=np.float64)
        frames[0, 0] = np.nan
        with self.assertRaisesRegex(FeatureExtractionError, "non-finite"):
            _summarize(frames, sample_count=720, sample_rate=16000)

    def test_feature_schema_freezes_every_new_numerical_semantic(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_feature_schema,
        )

        expected = {
            "f0_frame_input": "normalized_raw_frame",
            "f0_centering": "subtract_full_frame_mean",
            "f0_window": "none",
            "f0_zero_residual_energy": "unvoiced",
            "f0_autocorrelation_peak_tie_break": "lowest_lag_highest_f0",
            "zero_frame_rms_floor": "one_pcm16_lsb_over_full_frame_rms",
            "zero_frame_rms_floor_linear": 0.00000152587890625,
            "rms_summary_frame_scope": "all_complete_frames",
            "standard_deviation_ddof": 0,
            "f0_range_definition": "maximum_minus_minimum_voiced_f0",
            "voiced_fraction_denominator": "all_complete_frames",
            "zcr_spectral_frame_scope": "nonsilent_frames",
        }
        schema = load_json_strict(FEATURE_SCHEMA)
        self.assertEqual(
            {field: schema.get(field) for field in expected},
            expected,
        )
        validate_feature_schema(schema)

        for field, value in expected.items():
            missing = deepcopy(schema)
            del missing[field]
            with self.subTest(field=field, mutation="missing"):
                with self.assertRaises(ValueError):
                    validate_feature_schema(missing)

            mutated = deepcopy(schema)
            if isinstance(value, str):
                mutated[field] = f"mutated-{value}"
            elif isinstance(value, int):
                mutated[field] = value + 1
            else:
                mutated[field] = value * 2.0
            with self.subTest(field=field, mutation="value"):
                with self.assertRaises(ValueError):
                    validate_feature_schema(mutated)

        extra = deepcopy(schema)
        extra["unexpected_numerical_semantic"] = "not-frozen"
        with self.assertRaises(ValueError):
            validate_feature_schema(extra)

    def test_task_4_plan_freezes_expanded_contract_paths_and_definitions(
        self,
    ) -> None:
        plan = IMPLEMENTATION_PLAN.read_text(encoding="utf-8")
        task_4 = plan.split(
            "### Task 4: Implement deterministic acoustic feature extraction",
            1,
        )[1].split("### Task 5:", 1)[0]
        normalized_task_4 = " ".join(task_4.split())
        required_markers = (
            "research/sources/emotion_state/"
            "emotion_state_phase_b_feature_v1.schema.json",
            "scripts/validate_emotion_state_002_phase_b.py",
            "normalized raw frame with its full-frame mean subtracted",
            "no window is applied to F0",
            "zero centered residual energy is unvoiced",
            "lowest allowed lag (highest F0)",
            "1 / (32768 * sqrt(400))",
            "RMS summaries use all complete frames",
            "population standard deviation (`ddof=0`)",
            "`f0_range_hz` is maximum minus minimum voiced F0",
            "`voiced_fraction` is voiced frames divided by all complete frames",
            "ZCR and spectral summaries use nonsilent frames only",
        )
        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized_task_4)


class EnvironmentLockTests(unittest.TestCase):
    def test_canonical_lock_matches_wheels_and_exact_runtime_identity(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_environment_identity,
            validate_environment_lock,
        )

        lock = validate_environment_lock(load_json_strict(ENVIRONMENT_LOCK))
        report = validate_environment_identity(
            lock_path=ENVIRONMENT_LOCK,
            wheelhouse_path=WHEELHOUSE,
        )
        expected = {
            distribution["name"]: distribution["version"]
            for distribution in lock["distributions"]
        }
        expected_hashes = {
            distribution["wheel_filename"]: distribution["sha256"]
            for distribution in lock["distributions"]
        }
        self.assertEqual(report["installed_distributions"], expected)
        self.assertEqual(report["wheel_count"], len(expected))
        self.assertEqual(report["wheel_hashes"], expected_hashes)
        self.assertEqual(
            Path(report["python_executable"]).resolve(),
            EVALUATION_PYTHON.resolve(),
        )
        self.assertEqual(report["python_version"], "3.11")
        self.assertEqual(report["platform"], "win_amd64")

    def test_cli_accepts_only_fixed_evaluation_interpreter(self) -> None:
        validator = ROOT / "scripts/validate_emotion_state_002_phase_b.py"
        fixed = subprocess.run(
            [str(EVALUATION_PYTHON), str(validator), "environment"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(fixed.returncode, 0, fixed.stderr)
        self.assertEqual(
            fixed.stdout,
            "EMOTION-STATE-002 Phase B validation passed: environment.\n",
        )
        self.assertEqual(fixed.stderr, "")

        system_python = Path(sys.base_prefix) / "python.exe"
        self.assertTrue(system_python.is_file())
        self.assertNotEqual(system_python.resolve(), EVALUATION_PYTHON.resolve())
        refused = subprocess.run(
            [str(system_python), str(validator), "environment"],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual(refused.stdout, "")
        self.assertIn("evaluation Python", refused.stderr)

    def test_actual_interpreter_platform_mismatch_fails_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_environment_identity,
        )

        with patch("sysconfig.get_platform", return_value="linux-x86_64"):
            with self.assertRaisesRegex(ValueError, "platform"):
                validate_environment_identity(
                    lock_path=ENVIRONMENT_LOCK,
                    wheelhouse_path=WHEELHOUSE,
                )

    def test_direct_dependencies_are_exact_and_runtime_manifest_is_untouched(
        self,
    ) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_environment_lock,
        )

        lock = validate_environment_lock(load_json_strict(ENVIRONMENT_LOCK))
        self.assertEqual(
            lock["direct_requirements"],
            ["numpy", "scipy", "scikit-learn"],
        )
        direct = sorted(
            distribution["name"]
            for distribution in lock["distributions"]
            if distribution["direct"]
        )
        self.assertEqual(direct, ["numpy", "scikit-learn", "scipy"])
        self.assertFalse(lock["product_dependency_manifest_influence_allowed"])

        runtime_manifest_text = RUNTIME_MANIFEST.read_text(encoding="utf-8")
        forbidden = [
            lock["schema_id"],
            ENVIRONMENT_LOCK.relative_to(ROOT).as_posix(),
            *(
                distribution["wheel_filename"]
                for distribution in lock["distributions"]
            ),
        ]
        for marker in forbidden:
            with self.subTest(runtime_manifest_marker=marker):
                self.assertNotIn(marker, runtime_manifest_text)

    def test_empty_extra_version_and_hash_mutations_fail_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_environment_lock,
        )

        lock = load_json_strict(ENVIRONMENT_LOCK)

        empty = deepcopy(lock)
        empty["distributions"] = []
        with self.assertRaisesRegex(ValueError, "distributions"):
            validate_environment_lock(empty)

        extra = deepcopy(lock)
        extra["distributions"].append(
            {
                "name": "unexpected",
                "version": "1.0.0",
                "direct": False,
                "wheel_filename": "unexpected-1.0.0-py3-none-any.whl",
                "sha256": "A" * 64,
                "license": "BSD-3-Clause",
            }
        )
        with self.assertRaisesRegex(ValueError, "distribution"):
            validate_environment_lock(extra)

        for field, replacement in (
            ("version", "0.0.0"),
            ("sha256", "0" * 64),
            ("sha256", lock["distributions"][0]["sha256"].lower()),
        ):
            mutated = deepcopy(lock)
            mutated["distributions"][0][field] = replacement
            with self.subTest(field=field, replacement=replacement):
                with self.assertRaisesRegex(ValueError, field):
                    validate_environment_lock(mutated)

    def test_identity_refuses_missing_lock_extra_and_version_mismatch(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            _validate_installed_distributions,
            load_json_strict,
            validate_environment_identity,
            validate_environment_lock,
        )

        lock = validate_environment_lock(load_json_strict(ENVIRONMENT_LOCK))
        installed = {
            distribution["name"]: distribution["version"]
            for distribution in lock["distributions"]
        }

        ENVIRONMENT_TEST_TEMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ENVIRONMENT_TEST_TEMP) as directory:
            missing = Path(directory) / "missing.lock"
            with self.assertRaisesRegex(ValueError, "environment lock is missing"):
                validate_environment_identity(
                    lock_path=missing,
                    wheelhouse_path=WHEELHOUSE,
                )

        extra = dict(installed)
        extra["pip"] = "24.0"
        with self.assertRaisesRegex(ValueError, "installed distributions"):
            _validate_installed_distributions(lock, extra)

        mismatch = dict(installed)
        mismatch["numpy"] = "0.0.0"
        with self.assertRaisesRegex(ValueError, "installed distributions"):
            _validate_installed_distributions(lock, mismatch)

    def test_missing_extra_and_tampered_wheels_fail_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_environment_identity,
            validate_environment_lock,
        )

        lock = validate_environment_lock(load_json_strict(ENVIRONMENT_LOCK))
        ENVIRONMENT_TEST_TEMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ENVIRONMENT_TEST_TEMP) as directory:
            temporary_wheelhouse = Path(directory)
            for wheel in WHEELHOUSE.glob("*.whl"):
                shutil.copy2(wheel, temporary_wheelhouse / wheel.name)

            missing = temporary_wheelhouse / lock["distributions"][0][
                "wheel_filename"
            ]
            missing.unlink()
            with self.assertRaisesRegex(ValueError, "wheel set"):
                validate_environment_identity(
                    lock_path=ENVIRONMENT_LOCK,
                    wheelhouse_path=temporary_wheelhouse,
                )
            shutil.copy2(WHEELHOUSE / missing.name, missing)

            extra = temporary_wheelhouse / "unexpected-1.0-py3-none-any.whl"
            extra.write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError, "wheel set"):
                validate_environment_identity(
                    lock_path=ENVIRONMENT_LOCK,
                    wheelhouse_path=temporary_wheelhouse,
                )
            extra.unlink()

            first = temporary_wheelhouse / lock["distributions"][0][
                "wheel_filename"
            ]
            first.write_bytes(first.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "wheel hash"):
                validate_environment_identity(
                    lock_path=ENVIRONMENT_LOCK,
                    wheelhouse_path=temporary_wheelhouse,
                )

    def test_step_7_keeps_pip_out_of_evaluation_venv(self) -> None:
        plan = IMPLEMENTATION_PLAN.read_text(encoding="utf-8")
        task_3 = plan.split(
            "### Task 3: Review and lock the isolated research environment",
            1,
        )[1].split("### Task 4:", 1)[0]
        step_7 = task_3.split(
            "- [ ] **Step 7: Add lock and runtime-identity tests**",
            1,
        )[1].split("- [ ] **Step 8:", 1)[0]
        self.assertNotIn(
            ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m pip",
            step_7,
        )
        self.assertIn(
            ".tmp/emotion-state-002-phase-b/resolver-venv/Scripts/python.exe "
            "-m pip --python "
            ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe check",
            step_7,
        )


class CremaReferenceLabelTests(unittest.TestCase):
    def _write_sources(self, root: Path) -> tuple[Path, Path]:
        finished = root / "finishedResponses.csv"
        summary = root / "summaryTable.csv"
        finished.write_text(
            ",localid,pos,ans,ttr,queryType,numTries,clipNum,questNum,"
            "subType,clipName,sessionNums,respEmo,respLevel,dispEmo,"
            "dispVal,dispLevel\n"
            "1,r1,1,A_80,1,1,0,1,1,4,1001_DFA_ANG_XX,s1,A,80,A,50,X\n"
            "2,r2,1,A_70,1,1,0,1,1,4,1001_DFA_ANG_XX,s2,A,70,A,50,X\n"
            "3,r3,1,N_60,1,1,0,1,1,4,1001_DFA_ANG_XX,s3,N,60,A,50,X\n"
            "4,r1,1,A_80,1,1,0,2,1,4,1002_IEO_HAP_HI,s1,A,80,H,80,H\n"
            "5,r2,1,H_80,1,1,0,2,1,4,1002_IEO_HAP_HI,s2,H,80,H,80,H\n"
            "6,r1,1,S_80,1,1,0,3,1,4,1003_TAI_FEA_XX,s1,S,80,F,50,X\n",
            encoding="utf-8",
        )
        summary.write_text(
            ",FileName,VoiceVote,VoiceLevel,FaceVote,FaceLevel,"
            "MultiModalVote,MultiModalLevel\n"
            "1,1001_DFA_ANG_XX,A,75,A,75,A,75\n"
            "2,1002_IEO_HAP_HI,H,80,H,80,H,80\n"
            "3,1003_TAI_FEA_XX,F,80,F,80,F,80\n",
            encoding="utf-8",
        )
        return finished, summary

    def test_concordant_unique_winner_is_eligible(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        with tempfile.TemporaryDirectory() as directory:
            finished, summary = self._write_sources(Path(directory))
            rows, ledger = load_crema_reference_labels(
                finished, summary,
                {"1001_DFA_ANG_XX", "1002_IEO_HAP_HI", "1003_TAI_FEA_XX"},
            )
        by_stem = {row.clip_stem: row for row in rows}
        self.assertEqual(by_stem["1001_DFA_ANG_XX"].label, "A")
        self.assertEqual(
            by_stem["1002_IEO_HAP_HI"].abstention_reason,
            "raw_audio_vote_tie",
        )
        self.assertEqual(
            by_stem["1003_TAI_FEA_XX"].abstention_reason,
            "unique_winner_disagreement",
        )
        self.assertEqual(ledger["eligible_concordant_unique_winner"], 1)

    def test_released_tie_and_filename_intent_abstain(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        with tempfile.TemporaryDirectory() as directory:
            finished, summary = self._write_sources(Path(directory))
            text = summary.read_text(encoding="utf-8").replace(
                "1001_DFA_ANG_XX,A,75", "1001_DFA_ANG_XX,A:N,75"
            )
            summary.write_text(text, encoding="utf-8")
            rows, _ = load_crema_reference_labels(
                finished, summary, {"1001_DFA_ANG_XX"}
            )
        self.assertIsNone(rows[0].label)
        self.assertEqual(rows[0].abstention_reason, "summary_voice_tie")
        self.assertNotEqual(rows[0].label, "ANG")

    def test_source_binding_rejects_substituted_bytes_and_contract_mismatches(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_crema_source_binding,
        )

        with tempfile.TemporaryDirectory() as directory:
            finished, summary = self._write_sources(Path(directory))
            _, ledger = load_crema_reference_labels(
                finished, summary, {"1001_DFA_ANG_XX"}
            )
            contract = dict(ledger["source_binding"])
            validate_crema_source_binding(ledger["source_binding"], contract)

            finished.write_text(
                "\ufeff" + finished.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            _, substituted = load_crema_reference_labels(
                finished, summary, {"1001_DFA_ANG_XX"}
            )
            with self.assertRaisesRegex(ValueError, "source binding"):
                validate_crema_source_binding(substituted["source_binding"], contract)

        for field, value in contract.items():
            mutated = dict(contract)
            mutated[field] = f"mutated-{value}"
            with self.subTest(binding_field=field):
                with self.assertRaisesRegex(ValueError, "source binding"):
                    validate_crema_source_binding(contract, mutated)

    def test_duplicate_included_stems_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        with tempfile.TemporaryDirectory() as directory:
            finished, summary = self._write_sources(Path(directory))
            with self.assertRaisesRegex(
                ValueError,
                "duplicate included CREMA-D clip stem",
            ):
                load_crema_reference_labels(
                    finished,
                    summary,
                    ["1001_DFA_ANG_XX", "1001_DFA_ANG_XX"],
                )

    def test_malformed_csv_rows_raise_controlled_value_errors(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        def expect_failure(
            mutation: Callable[[Path], None],
            pattern: str,
        ) -> None:
            with tempfile.TemporaryDirectory() as directory:
                finished, summary = self._write_sources(Path(directory))
                mutation(finished)
                with self.assertRaisesRegex(ValueError, pattern):
                    load_crema_reference_labels(
                        finished,
                        summary,
                        {"1001_DFA_ANG_XX"},
                    )

        with self.subTest(row="surplus"):
            expect_failure(
                lambda finished: finished.write_text(
                    finished.read_text(encoding="utf-8").replace(
                        ",s1,A,80,A,50,X\n", ",s1,A,80,A,50,X,surplus\n", 1,
                    ),
                    encoding="utf-8",
                ),
                "unexpected CSV row",
            )
        with self.subTest(row="short"):
            expect_failure(
                lambda finished: finished.write_text(
                    finished.read_text(encoding="utf-8").replace(
                        ",s1,A,80,A,50,X\n", ",s1,A,80,A,50\n", 1,
                    ),
                    encoding="utf-8",
                ),
                "unexpected CSV row",
            )
        with self.subTest(row="malformed"):
            expect_failure(
                lambda finished: finished.write_text(
                    finished.read_text(encoding="utf-8").splitlines()[0]
                    + "\n1,\"unterminated",
                    encoding="utf-8",
                ),
                "malformed CSV row",
            )

    def test_real_schema_and_reference_join_mutations_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        def expect_failure(
            mutation: Callable[[Path, Path], None],
            pattern: str,
        ) -> None:
            with tempfile.TemporaryDirectory() as directory:
                finished, summary = self._write_sources(Path(directory))
                mutation(finished, summary)
                with self.assertRaisesRegex(ValueError, pattern):
                    load_crema_reference_labels(
                        finished, summary, {"1001_DFA_ANG_XX"}
                    )

        with self.subTest(mutation="finished_field_name"):
            expect_failure(
                lambda finished, summary: finished.write_text(
                    finished.read_text(encoding="utf-8").replace(
                        "respEmo", "responseEmotion",
                    ),
                    encoding="utf-8",
                ),
                "unexpected CSV schema",
            )
        with self.subTest(mutation="raw_audio_modality"):
            expect_failure(
                lambda finished, summary: finished.write_text(
                    finished.read_text(encoding="utf-8").replace(
                        ",1,1,0,", ",1,2,0,",
                    ),
                    encoding="utf-8",
                ),
                "missing CREMA-D reference-label join",
            )
        with self.subTest(mutation="duplicate_summary_clip"):
            expect_failure(
                lambda finished, summary: summary.write_text(
                    summary.read_text(encoding="utf-8")
                    + "4,1001_DFA_ANG_XX,A,75,A,75,A,75\n",
                    encoding="utf-8",
                ),
                "duplicate summary clip",
            )
        with self.subTest(mutation="invalid_raw_label"):
            expect_failure(
                lambda finished, summary: finished.write_text(
                    finished.read_text(encoding="utf-8").replace(
                        ",s1,A,80,A,50,X", ",s1,Z,80,A,50,X", 1,
                    ),
                    encoding="utf-8",
                ),
                "invalid raw audio-perception label",
            )
        with self.subTest(mutation="invalid_summary_label"):
            expect_failure(
                lambda finished, summary: summary.write_text(
                    summary.read_text(encoding="utf-8").replace(
                        "1001_DFA_ANG_XX,A,75", "1001_DFA_ANG_XX,Z,75",
                    ),
                    encoding="utf-8",
                ),
                "invalid released VoiceVote",
            )
        with self.subTest(mutation="missing_raw_join"):
            expect_failure(
                lambda finished, summary: finished.write_text(
                    finished.read_text(encoding="utf-8").replace(
                        "1001_DFA_ANG_XX", "9999_DFA_ANG_XX",
                    ),
                    encoding="utf-8",
                ),
                "missing CREMA-D reference-label join",
            )
        with self.subTest(mutation="missing_summary_join"):
            expect_failure(
                lambda finished, summary: summary.write_text(
                    summary.read_text(encoding="utf-8").replace(
                        "1,1001_DFA_ANG_XX,A,75,A,75,A,75\n", "",
                    ),
                    encoding="utf-8",
                ),
                "missing CREMA-D reference-label join",
            )


class AmiMechanicsTests(unittest.TestCase):
    FROZEN_VALUE_KEYS = (
        "turn_duration_ms_median",
        "turn_duration_ms_p90",
        "inter_turn_gap_ms_median",
        "inter_turn_gap_ms_p90",
        "overlap_ratio",
        "floor_changes_per_minute",
        "speaker_balance_normalized_entropy",
        "backchannels_per_100_turns",
    )
    FROZEN_BUCKET_KEYS = FROZEN_VALUE_KEYS[:4]
    FROZEN_SCALAR_KEYS = FROZEN_VALUE_KEYS[4:]
    OFFICIAL_DIALOGUE_ACTS = (
        "ami_da_1",
        "ami_da_2",
        "ami_da_3",
        "ami_da_4",
        "ami_da_5",
        "ami_da_6",
        "ami_da_7",
        "ami_da_8",
        "ami_da_9",
        "ami_da_11",
        "ami_da_12",
        "ami_da_13",
        "ami_da_14",
        "ami_da_15",
        "ami_da_16",
    )

    @staticmethod
    def _write_fixture(root: Path) -> dict[str, Any]:
        metadata = root / "meetings.xml"
        words_a = root / "M1.A.words.xml"
        words_b = root / "M1.B.words.xml"
        segments_a = root / "M1.A.segments.xml"
        segments_b = root / "M1.B.segments.xml"
        acts_a = root / "M1.A.dialog-act.xml"
        acts_b = root / "M1.B.dialog-act.xml"
        metadata.write_text(
            """
<ami:corpus xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/">
  <ami:meeting nite:id="M1">
    <ami:participant ami:code="A" ami:participant_id="P-A" />
    <ami:participant ami:code="B" ami:participant_id="P-B" />
  </ami:meeting>
</ami:corpus>
""".strip(),
            encoding="utf-8",
        )
        words_a.write_text(
            """
<ami:words xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/"
           ami:meeting_id="M1" ami:agent="A">
  <ami:w nite:id="a1" ami:starttime="0.000" ami:endtime="0.500">SECRET ALPHA</ami:w>
  <ami:w nite:id="a2" ami:starttime="0.500" ami:endtime="1.000">SECRET BETA</ami:w>
  <ami:w nite:id="a3" ami:starttime="2.600" ami:endtime="3.000">SECRET GAMMA</ami:w>
</ami:words>
""".strip(),
            encoding="utf-8",
        )
        words_b.write_text(
            """
<ami:words xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/"
           ami:meeting_id="M1" ami:agent="B">
  <ami:w nite:id="b1" ami:starttime="0.800" ami:endtime="1.200">SECRET DELTA</ami:w>
  <ami:w nite:id="b2" ami:starttime="1.500" ami:endtime="2.000">SECRET EPSILON</ami:w>
  <ami:w nite:id="b3" ami:starttime="2.000" ami:endtime="2.500">SECRET ZETA</ami:w>
</ami:words>
""".strip(),
            encoding="utf-8",
        )
        segments_a.write_text(
            """
<ami:segments xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/"
              ami:meeting_id="M1" ami:agent="A">
  <ami:segment nite:id="s1">
    <nite:child href="M1.A.words.xml#id(a1)..id(a2)" />
  </ami:segment>
  <ami:segment nite:id="s2">
    <nite:child href="M1.A.words.xml#id(a3)" />
  </ami:segment>
</ami:segments>
""".strip(),
            encoding="utf-8",
        )
        segments_b.write_text(
            """
<ami:segments xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/"
              ami:meeting_id="M1" ami:agent="B">
  <ami:segment nite:id="s3">
    <nite:child href="M1.B.words.xml#id(b1)" />
  </ami:segment>
  <ami:segment nite:id="s4">
    <nite:child href="M1.B.words.xml#id(b2)..id(b3)" />
  </ami:segment>
</ami:segments>
""".strip(),
            encoding="utf-8",
        )
        acts_a.write_text(
            """
<ami:dialogue-acts xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/"
                   ami:meeting_id="M1" ami:agent="A"
                   ami:synthetic_legacy_schema="phase_b_ami_mechanics_v1">
  <ami:dact nite:id="d1" ami:type="ami_da_2">
    <nite:child href="M1.A.segments.xml#id(s1)" />
  </ami:dact>
  <ami:dact nite:id="d4" ami:type="ami_da_3">
    <nite:child href="M1.A.segments.xml#id(s2)" />
  </ami:dact>
</ami:dialogue-acts>
""".strip(),
            encoding="utf-8",
        )
        acts_b.write_text(
            """
<ami:dialogue-acts xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/"
                   ami:meeting_id="M1" ami:agent="B"
                   ami:synthetic_legacy_schema="phase_b_ami_mechanics_v1">
  <ami:dact nite:id="d2" ami:niteType="ami_da_1">
    <nite:child href="M1.B.segments.xml#id(s3)" />
  </ami:dact>
  <ami:dact nite:id="d3" ami:type="ami_da_2">
    <nite:child href="M1.B.segments.xml#id(s4)" />
  </ami:dact>
</ami:dialogue-acts>
""".strip(),
            encoding="utf-8",
        )
        return {
            "metadata_path": metadata,
            "word_paths": (words_a, words_b),
            "timing_link_paths": (segments_a, segments_b),
            "dialogue_act_paths": (acts_a, acts_b),
            "known_meetings": ("M1",),
        }

    @classmethod
    def _write_real_schema_fixture(
        cls,
        root: Path,
        *,
        include_participants: bool = False,
    ) -> dict[str, Any]:
        fixture = cls._write_fixture(root)
        metadata = fixture["metadata_path"]
        metadata.write_text(
            """
<ami:corpus xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/">
  <ami:meeting nite:id="internal-meeting-1" ami:observation="M1">
    <ami:speaker ami:nxt_agent="A" ami:global_name="P-A" />
    <ami:speaker ami:nxt_agent="B" ami:global_name="P-B" />
  </ami:meeting>
</ami:corpus>
""".strip(),
            encoding="utf-8",
        )
        replacements = {
            '<ami:dact nite:id="d1" ami:type="ami_da_2">': (
                '<ami:dact nite:id="d1">\n'
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_2)" />'
            ),
            '<ami:dact nite:id="d4" ami:type="ami_da_3">': (
                '<ami:dact nite:id="d4">\n'
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_3)" />'
            ),
            '<ami:dact nite:id="d2" ami:niteType="ami_da_1">': (
                '<ami:dact nite:id="d2">\n'
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_1)" />'
            ),
            '<ami:dact nite:id="d3" ami:type="ami_da_2">': (
                '<ami:dact nite:id="d3">\n'
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_2)" />'
            ),
        }
        for path in fixture["dialogue_act_paths"]:
            source = path.read_text(encoding="utf-8")
            source = source.replace(
                '\n                   ami:synthetic_legacy_schema='
                '"phase_b_ami_mechanics_v1"',
                "",
            )
            for original, replacement in replacements.items():
                source = source.replace(original, replacement)
            path.write_text(source, encoding="utf-8")
        if include_participants:
            participants = root / "participants.xml"
            participants.write_text(
                """
<ami:participants xmlns:ami="urn:ami" xmlns:nite="http://nite.sourceforge.net/">
  <ami:participant nite:id="P-A" />
  <ami:participant nite:id="P-B" />
</ami:participants>
""".strip(),
                encoding="utf-8",
            )
            fixture["participant_metadata_path"] = participants
        return fixture

    @classmethod
    def _meeting(
        cls,
        meeting_id: str,
        participants: tuple[str, ...],
        value: float,
    ) -> Any:
        from scripts.emotion_state_phase_b_ami_mechanics import MeetingMechanics

        return MeetingMechanics(
            meeting_id=meeting_id,
            participants=participants,
            values=(
                ("turn_duration_ms_median", value),
                ("turn_duration_ms_p90", value),
                ("inter_turn_gap_ms_median", value),
                ("inter_turn_gap_ms_p90", value),
                ("overlap_ratio", 0.1),
                ("floor_changes_per_minute", value),
                ("speaker_balance_normalized_entropy", 0.5),
                ("backchannels_per_100_turns", 25.0),
            ),
            dialogue_act_distribution=(
                ("ami_da_1", 0.25),
                ("ami_da_2", 0.75),
            ),
        )

    def test_namespace_qualified_local_nxt_links_produce_exact_mechanics(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            compute_meeting_mechanics,
            load_ami_turns,
        )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_fixture(Path(directory))
            turns = load_ami_turns(**fixture)
        mechanics = compute_meeting_mechanics(turns)
        self.assertEqual(
            mechanics.participants,
            ("P-A", "P-B"),
        )
        values = dict(mechanics.values)
        expected = {
            "turn_duration_ms_median": 700.0,
            "turn_duration_ms_p90": 1000.0,
            "inter_turn_gap_ms_median": 200.0,
            "inter_turn_gap_ms_p90": 280.0,
            "overlap_ratio": 1.0 / 15.0,
            "floor_changes_per_minute": 40.0,
            "speaker_balance_normalized_entropy": 1.0,
            "backchannels_per_100_turns": 25.0,
        }
        self.assertEqual(tuple(values), self.FROZEN_VALUE_KEYS)
        for key, value in expected.items():
            self.assertAlmostEqual(values[key], value, places=12)
        self.assertEqual(
            mechanics.dialogue_act_distribution,
            (
                ("ami_da_1", 0.25),
                ("ami_da_2", 0.5),
                ("ami_da_3", 0.25),
            ),
        )
        retained = repr((turns, mechanics)).upper()
        self.assertNotIn("SECRET", retained)
        self.assertTrue(all(not hasattr(turn, "text") for turn in turns))

    def test_official_dialogue_act_vocabulary_is_exact(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            BACKCHANNEL_ACT,
            DIALOGUE_ACT_VOCABULARY,
            Turn,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            AMI_DIALOGUE_ACT_VOCABULARY,
        )

        self.assertEqual(DIALOGUE_ACT_VOCABULARY, self.OFFICIAL_DIALOGUE_ACTS)
        self.assertEqual(
            AMI_DIALOGUE_ACT_VOCABULARY,
            self.OFFICIAL_DIALOGUE_ACTS,
        )
        self.assertEqual(BACKCHANNEL_ACT, "ami_da_1")
        self.assertNotIn("ami_da_10", DIALOGUE_ACT_VOCABULARY)
        for label in ("backchannel", "inform", "question", "ami_da_10"):
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    ValueError,
                    "dialogue-act vocabulary",
                ):
                    Turn("M1", "P-A", 0, 100, label)

    def test_real_meeting_schema_prefers_observation_and_optional_enrichment(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(Path(directory))
            without_enrichment = load_ami_turns(**fixture)
        self.assertEqual(
            {turn.participant_id for turn in without_enrichment},
            {"P-A", "P-B"},
        )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(
                Path(directory),
                include_participants=True,
            )
            with_enrichment = load_ami_turns(**fixture)
        self.assertEqual(with_enrichment, without_enrichment)

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(
                Path(directory),
                include_participants=True,
            )
            participants = fixture["participant_metadata_path"]
            participants.write_text(
                participants.read_text(encoding="utf-8").replace(
                    'nite:id="P-A"',
                    'nite:id="P-X"',
                ),
                encoding="utf-8",
            )
            partially_enriched = load_ami_turns(**fixture)
        self.assertEqual(partially_enriched, without_enrichment)

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(
                Path(directory),
                include_participants=True,
            )
            participants = fixture["participant_metadata_path"]
            participants.write_text(
                participants.read_text(encoding="utf-8").replace(
                    'nite:id="P-A"',
                    'nite:id="P-B"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "participant enrichment",
            ):
                load_ami_turns(**fixture)

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(
                Path(directory),
                include_participants=True,
            )
            participants = fixture["participant_metadata_path"]
            participants.write_text(
                participants.read_text(encoding="utf-8").replace(
                    'nite:id="P-A"',
                    'nite:ID="P-A"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "participant enrichment",
            ):
                load_ami_turns(**fixture)

    def test_real_meeting_dependencies_reject_aliases_and_duplicates(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        cases = (
            (
                "agent_alias",
                'ami:nxt_agent="A"',
                'ami:code="A"',
            ),
            (
                "agent_case_alias",
                'ami:nxt_agent="A"',
                'ami:nxtAgent="A"',
            ),
            (
                "participant_alias",
                'ami:global_name="P-A"',
                'ami:participant_id="P-A"',
            ),
            (
                "participant_case_alias",
                'ami:global_name="P-A"',
                'ami:globalName="P-A"',
            ),
            (
                "element_alias",
                "<ami:speaker ",
                "<ami:participant ",
            ),
        )
        for name, original, replacement in cases:
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as directory:
                    fixture = self._write_real_schema_fixture(Path(directory))
                    metadata = fixture["metadata_path"]
                    source = metadata.read_text(encoding="utf-8")
                    self.assertIn(original, source)
                    metadata.write_text(
                        source.replace(original, replacement, 1),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(
                        ValueError,
                        "participant dependency",
                    ):
                        load_ami_turns(**fixture)

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(Path(directory))
            metadata = fixture["metadata_path"]
            source = metadata.read_text(encoding="utf-8")
            binding = (
                '    <ami:speaker ami:nxt_agent="A" '
                'ami:global_name="P-A" />'
            )
            self.assertIn(binding, source)
            metadata.write_text(
                source.replace(binding, f"{binding}\n{binding}", 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "participant dependency is conflicting",
            ):
                load_ami_turns(**fixture)

    def test_real_da_aspect_pointer_is_exact_and_local(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(Path(directory))
            turns = load_ami_turns(**fixture)
        self.assertEqual(
            tuple(turn.dialogue_act for turn in turns),
            ("ami_da_2", "ami_da_1", "ami_da_2", "ami_da_3"),
        )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(Path(directory))
            acts = fixture["dialogue_act_paths"][0]
            source = acts.read_text(encoding="utf-8")
            pointer_record = (
                '<ami:dact nite:id="d1">\n'
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_2)" />'
            )
            self.assertIn(pointer_record, source)
            acts.write_text(
                source.replace(
                    pointer_record,
                    '<ami:dact nite:id="d1" ami:type="ami_da_2">',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "da-aspect pointer"):
                load_ami_turns(**fixture)

    def test_real_da_aspect_pointer_rejects_nonexact_references(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        cases = (
            (
                "multiple_conflicting",
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_2)" />',
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_2)" />\n'
                '    <nite:pointer role="da-aspect" '
                'href="da-types.xml#id(ami_da_3)" />',
                "da-aspect pointer",
            ),
            (
                "unknown",
                "da-types.xml#id(ami_da_2)",
                "da-types.xml#id(ami_da_10)",
                "dialogue-act vocabulary",
            ),
            (
                "identifier_case",
                "da-types.xml#id(ami_da_2)",
                "da-types.xml#id(AMI_DA_2)",
                "da-aspect pointer",
            ),
            (
                "identifier_whitespace",
                "da-types.xml#id(ami_da_2)",
                "da-types.xml#id( ami_da_2 )",
                "da-aspect pointer",
            ),
            (
                "fragment_whitespace",
                "da-types.xml#id(ami_da_2)",
                "da-types.xml# id(ami_da_2)",
                "da-aspect pointer",
            ),
            (
                "target_whitespace",
                "da-types.xml#id(ami_da_2)",
                "da-types.xml #id(ami_da_2)",
                "da-aspect pointer",
            ),
            (
                "target_case",
                "da-types.xml#id(ami_da_2)",
                "DA-TYPES.xml#id(ami_da_2)",
                "da-aspect pointer",
            ),
            (
                "range",
                "da-types.xml#id(ami_da_2)",
                "da-types.xml#id(ami_da_2)..id(ami_da_3)",
                "da-aspect pointer",
            ),
            (
                "external",
                "da-types.xml#id(ami_da_2)",
                "https://example.invalid/da-types.xml#id(ami_da_2)",
                "external URI",
            ),
            (
                "wrong_local_target",
                "da-types.xml#id(ami_da_2)",
                "other-types.xml#id(ami_da_2)",
                "da-aspect target",
            ),
            (
                "direct_and_pointer",
                '<ami:dact nite:id="d1">',
                '<ami:dact nite:id="d1" ami:type="ami_da_2">',
                "da-aspect pointer",
            ),
        )
        for name, original, replacement, pattern in cases:
            with self.subTest(case=name):
                with tempfile.TemporaryDirectory() as directory:
                    fixture = self._write_real_schema_fixture(Path(directory))
                    acts = fixture["dialogue_act_paths"][0]
                    source = acts.read_text(encoding="utf-8")
                    self.assertIn(original, source)
                    acts.write_text(
                        source.replace(original, replacement, 1),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ValueError, pattern):
                        load_ami_turns(**fixture)

    def test_real_loader_requires_exact_expected_unlabeled_count(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        pointer = (
            '    <nite:pointer role="da-aspect" '
            'href="da-types.xml#id(ami_da_2)" />\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(Path(directory))
            acts = fixture["dialogue_act_paths"][0]
            source = acts.read_text(encoding="utf-8")
            self.assertIn(pointer, source)
            acts.write_text(
                source.replace(pointer, "", 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unlabeled count"):
                load_ami_turns(**fixture)
            turns = load_ami_turns(
                **fixture,
                expected_unlabeled_count=1,
            )
            self.assertEqual(len(turns), 3)
            with self.assertRaisesRegex(ValueError, "unlabeled count"):
                load_ami_turns(
                    **fixture,
                    expected_unlabeled_count=2,
                )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_real_schema_fixture(Path(directory))
            for invalid in (True, -1):
                with self.subTest(invalid_expected_count=invalid):
                    with self.assertRaisesRegex(
                        ValueError,
                        "expected unlabeled",
                    ):
                        load_ami_turns(
                            **fixture,
                            expected_unlabeled_count=invalid,
                        )

    def test_official_backchannel_is_excluded_from_floor_changes(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            Turn,
            compute_meeting_mechanics,
        )

        mechanics = compute_meeting_mechanics((
            Turn("M1", "P-A", 0, 100, "ami_da_2"),
            Turn("M1", "P-B", 100, 200, "ami_da_1"),
            Turn("M1", "P-A", 200, 300, "ami_da_3"),
            Turn("M1", "P-B", 300, 400, "ami_da_2"),
        ))
        values = dict(mechanics.values)
        self.assertEqual(values["floor_changes_per_minute"], 150.0)
        self.assertEqual(values["backchannels_per_100_turns"], 25.0)

    def test_exact_frozen_metric_schema_uses_an_independent_oracle(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            Turn,
            compute_meeting_mechanics,
            contribution_limited_aggregates,
        )

        mechanics = compute_meeting_mechanics((
            Turn("M1", "P-A", 0, 100, "ami_da_2"),
            Turn("M1", "P-B", 200, 300, "ami_da_3"),
        ))
        self.assertEqual(
            tuple(key for key, _ in mechanics.values),
            self.FROZEN_VALUE_KEYS,
        )
        self.assertTrue({
            "turn_duration_median_ms",
            "turn_duration_p90_ms",
            "inter_turn_gap_median_ms",
            "inter_turn_gap_p90_ms",
            "normalized_speaker_entropy",
        }.isdisjoint(dict(mechanics.values)))

        meetings = tuple(
            self._meeting(
                f"M{index}",
                (f"P{index * 2:02d}", f"P{index * 2 + 1:02d}"),
                float(index),
            )
            for index in range(5)
        )
        meeting_ids = tuple(meeting.meeting_id for meeting in meetings)
        membership = {
            partition: meeting_ids
            for partition in ("scenario_only", "full_corpus", "full_only")
        }
        aggregate = contribution_limited_aggregates(
            meetings,
            membership,
            meeting_ids,
        )
        for partition in aggregate.values():
            self.assertEqual(
                tuple(partition["buckets"]),
                self.FROZEN_BUCKET_KEYS,
            )
            self.assertEqual(
                tuple(partition["scalars"]),
                self.FROZEN_SCALAR_KEYS,
            )

    def test_public_identity_entry_points_use_one_canonical_representation(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            Turn,
            contribution_limited_aggregates,
            load_ami_turns,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_ami_mechanics_aggregates,
        )

        turn = Turn(" M1 ", " P0 ", 0, 100, "ami_da_2")
        self.assertEqual((turn.meeting_id, turn.participant_id), ("M1", "P0"))
        with self.assertRaisesRegex(ValueError, "identifier"):
            Turn("   ", "P0", 0, 100, "ami_da_2")
        with self.assertRaisesRegex(ValueError, "identifier"):
            Turn("M1", "\t", 0, 100, "ami_da_2")
        with self.assertRaisesRegex(ValueError, "identifier"):
            self._meeting("   ", ("P0", "P1"), 1.0)
        with self.assertRaisesRegex(ValueError, "identifier"):
            self._meeting("M1", ("P0", "   "), 1.0)

        aliases = (
            ("M0", ("P0", "P1")),
            ("M1", ("P0 ", "P2")),
            ("M2", ("P1 ", "P3")),
            ("M3", ("P2 ", "P4")),
            ("M4", ("P3 ", "P4 ")),
        )
        meetings = tuple(
            self._meeting(meeting_id, participants, float(index + 1))
            for index, (meeting_id, participants) in enumerate(aliases)
        )
        padded_ids = tuple(f" {meeting.meeting_id} " for meeting in meetings)
        membership = {
            partition: padded_ids
            for partition in ("scenario_only", "full_corpus", "full_only")
        }
        aggregate = contribution_limited_aggregates(
            meetings,
            membership,
            padded_ids,
        )
        for partition in aggregate.values():
            self.assertEqual(partition["meeting_count"], 2)
            self.assertEqual(partition["unique_participant_count"], 4)
            self.assertEqual(
                partition["suppression_counts"][
                    "repeated_participant_meetings"
                ],
                3,
            )
            self.assertTrue(all(
                cell["suppressed"]
                for group in ("scalars", "buckets", "dialogue_acts")
                for cell in partition[group].values()
            ))
        validate_ami_mechanics_aggregates(
            aggregate,
            meetings=meetings,
            partition_membership=membership,
            official_order=padded_ids,
        )

        inflated = deepcopy(aggregate)
        cell = inflated["scenario_only"]
        cell["meeting_count"] = 5
        cell["unique_participant_count"] = 10
        cell["suppression_counts"] = {
            "repeated_participant_meetings": 0,
            "scalar_cells": 0,
            "bucket_cells": 0,
            "dialogue_act_cells": 0,
        }
        for group in ("scalars", "buckets", "dialogue_acts"):
            for metric in cell[group].values():
                metric["unique_participant_count"] = 10
                metric["suppressed"] = False
                metric["value"] = 0.0
        cell["dialogue_acts"]["ami_da_1"]["value"] = 0.25
        cell["dialogue_acts"]["ami_da_2"]["value"] = 0.75
        with self.assertRaisesRegex(ValueError, "authoritative"):
            validate_ami_mechanics_aggregates(
                inflated,
                meetings=meetings,
                partition_membership=membership,
                official_order=padded_ids,
            )

        with tempfile.TemporaryDirectory() as directory:
            fixture = self._write_fixture(Path(directory))
            fixture["known_meetings"] = (" M1 ",)
            metadata = fixture["metadata_path"]
            metadata.write_text(
                metadata.read_text(encoding="utf-8").replace(
                    'ami:participant_id="P-A"',
                    'ami:participant_id=" P-A "',
                ),
                encoding="utf-8",
            )
            turns = load_ami_turns(**fixture)
        self.assertEqual(
            {(item.meeting_id, item.participant_id) for item in turns},
            {("M1", "P-A"), ("M1", "P-B")},
        )

    def test_speaking_time_entropy_oracle_differs_from_balanced_turn_counts(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            Turn,
            compute_meeting_mechanics,
        )

        mechanics = compute_meeting_mechanics((
            Turn("M1", "P-A", 0, 900, "ami_da_2"),
            Turn("M1", "P-B", 1000, 1100, "ami_da_3"),
            Turn("M1", "P-A", 1200, 2100, "ami_da_2"),
            Turn("M1", "P-B", 2200, 2300, "ami_da_3"),
        ))
        expected = -(
            0.9 * math.log(0.9) + 0.1 * math.log(0.1)
        ) / math.log(2.0)
        actual = dict(mechanics.values)[
            "speaker_balance_normalized_entropy"
        ]
        self.assertAlmostEqual(actual, expected, places=15)
        self.assertNotEqual(actual, 1.0)

    def test_overlap_oracle_excludes_same_speaker_self_overlap(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            Turn,
            compute_meeting_mechanics,
        )

        mechanics = compute_meeting_mechanics((
            Turn("M1", "P-A", 0, 1000, "ami_da_2"),
            Turn("M1", "P-A", 500, 1500, "ami_da_3"),
            Turn("M1", "P-B", 1200, 1700, "ami_da_2"),
        ))
        self.assertAlmostEqual(
            dict(mechanics.values)["overlap_ratio"],
            300.0 / 1700.0,
            places=15,
        )

    def test_records_reject_every_unknown_dialogue_label_class(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import Turn

        rejected = (
            "backchannel",
            "inform",
            "question",
            "SECRET transcript",
            "P0",
            "M1",
            "anger",
            "customer_state",
            "operational_escalation",
            "persuasion_close",
        )
        template = self._meeting("M0", ("P0", "P1"), 1.0)
        for label in rejected:
            with self.subTest(label=label, record="Turn"):
                with self.assertRaisesRegex(
                    ValueError,
                    "dialogue-act vocabulary",
                ):
                    Turn("M0", "P0", 0, 100, label)
            with self.subTest(label=label, record="MeetingMechanics"):
                with self.assertRaisesRegex(
                    ValueError,
                    "dialogue-act vocabulary",
                ):
                    replace(
                        template,
                        dialogue_act_distribution=((label, 1.0),),
                    )

    def test_xml_loader_rejects_every_unknown_dialogue_label_class(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        rejected = (
            "backchannel",
            "inform",
            "question",
            "SECRET transcript",
            "P0",
            "M1",
            "anger",
            "customer_state",
            "operational_escalation",
            "persuasion_close",
        )
        for label in rejected:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as directory:
                    fixture = self._write_fixture(Path(directory))
                    acts_a = fixture["dialogue_act_paths"][0]
                    acts_a.write_text(
                        acts_a.read_text(encoding="utf-8").replace(
                            'ami:type="ami_da_2"',
                            f'ami:type="{label}"',
                            1,
                        ),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(
                        ValueError,
                        "dialogue-act vocabulary",
                    ):
                        load_ami_turns(**fixture)

    def test_xml_reference_rejections_cover_every_resolution_layer(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        cases = (
            (
                "word",
                "malformed_fragment",
                "timing_link_paths",
                0,
                "M1.A.words.xml#id(a1)..id(a2)",
                "M1.A.words.xml#not-an-id",
                "fragment",
            ),
            (
                "word",
                "unresolved_local",
                "timing_link_paths",
                0,
                "M1.A.words.xml#id(a1)..id(a2)",
                "missing.words.xml#id(a1)",
                "unknown local",
            ),
            (
                "word",
                "reversed_range",
                "timing_link_paths",
                0,
                "M1.A.words.xml#id(a1)..id(a2)",
                "M1.A.words.xml#id(a2)..id(a1)",
                "reversed",
            ),
            (
                "word",
                "cross_source",
                "timing_link_paths",
                0,
                "M1.A.words.xml#id(a1)..id(a2)",
                "M1.B.words.xml#id(b1)",
                "crosses source identity",
            ),
            (
                "timing",
                "malformed_fragment",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "M1.A.segments.xml#not-an-id",
                "fragment",
            ),
            (
                "timing",
                "unresolved_local",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "missing.segments.xml#id(s1)",
                "unknown local",
            ),
            (
                "timing",
                "reversed_range",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "M1.A.segments.xml#id(s2)..id(s1)",
                "reversed",
            ),
            (
                "timing",
                "cross_source",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "M1.B.segments.xml#id(s3)",
                "crosses source identity",
            ),
            (
                "dialogue",
                "malformed_fragment",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "M1.A.words.xml#not-an-id",
                "fragment",
            ),
            (
                "dialogue",
                "unresolved_local",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "missing.words.xml#id(a1)",
                "unknown local",
            ),
            (
                "dialogue",
                "reversed_range",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "M1.A.words.xml#id(a2)..id(a1)",
                "reversed",
            ),
            (
                "dialogue",
                "cross_source",
                "dialogue_act_paths",
                0,
                "M1.A.segments.xml#id(s1)",
                "M1.B.words.xml#id(b1)",
                "crosses source identity",
            ),
        )

        for (
            layer,
            boundary,
            path_key,
            index,
            original,
            replacement,
            pattern,
        ) in cases:
            with self.subTest(layer=layer, boundary=boundary):
                with tempfile.TemporaryDirectory() as directory:
                    fixture = self._write_fixture(Path(directory))
                    path = fixture[path_key][index]
                    source = path.read_text(encoding="utf-8")
                    self.assertIn(original, source)
                    path.write_text(
                        source.replace(original, replacement, 1),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ValueError, pattern):
                        load_ami_turns(**fixture)

    def test_xml_boundaries_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import load_ami_turns

        with self.subTest(boundary="unresolved participant"):
            with tempfile.TemporaryDirectory() as directory:
                fixture = self._write_fixture(Path(directory))
                metadata = fixture["metadata_path"]
                metadata.write_text(
                    metadata.read_text(encoding="utf-8").replace(
                        '    <ami:participant ami:code="B" '
                        'ami:participant_id="P-B" />\n',
                        "",
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "unresolved participant"):
                    load_ami_turns(**fixture)

        with self.subTest(boundary="malformed time span"):
            with tempfile.TemporaryDirectory() as directory:
                fixture = self._write_fixture(Path(directory))
                words_a = fixture["word_paths"][0]
                words_a.write_text(
                    words_a.read_text(encoding="utf-8").replace(
                        'ami:starttime="0.500" ami:endtime="1.000"',
                        'ami:starttime="0.500" ami:endtime="0.500"',
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "time span"):
                    load_ami_turns(**fixture)

        with self.subTest(boundary="unknown meeting"):
            with tempfile.TemporaryDirectory() as directory:
                fixture = self._write_fixture(Path(directory))
                fixture["known_meetings"] = ("M2",)
                with self.assertRaisesRegex(ValueError, "unknown meeting"):
                    load_ami_turns(**fixture)

        with self.subTest(boundary="external URI"):
            with tempfile.TemporaryDirectory() as directory:
                fixture = self._write_fixture(Path(directory))
                acts_a = fixture["dialogue_act_paths"][0]
                acts_a.write_text(
                    acts_a.read_text(encoding="utf-8").replace(
                        "M1.A.segments.xml#id(s1)",
                        "synthetic:M1.A.segments.xml#id(s1)",
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "external URI"):
                    load_ami_turns(**fixture)

    def test_compute_rejects_invalid_or_unproven_turns(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            Turn,
            compute_meeting_mechanics,
        )

        one_participant = (
            Turn("M1", "P-A", 0, 100, "ami_da_2"),
            Turn("M1", "P-A", 200, 300, "ami_da_3"),
        )
        with self.assertRaisesRegex(ValueError, "two proven participants"):
            compute_meeting_mechanics(one_participant)

        malformed = (
            Turn("M1", "P-A", 0, 100, "ami_da_2"),
            Turn("M1", "P-B", 200, 200, "ami_da_3"),
        )
        with self.assertRaisesRegex(ValueError, "time span"):
            compute_meeting_mechanics(malformed)

        mixed = (
            Turn("M1", "P-A", 0, 100, "ami_da_2"),
            Turn("M2", "P-B", 200, 300, "ami_da_3"),
        )
        with self.assertRaisesRegex(ValueError, "one meeting"):
            compute_meeting_mechanics(mixed)

    def test_contribution_limited_aggregates_use_official_order_once_per_person(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            contribution_limited_aggregates,
        )

        meetings = [
            self._meeting("M1", ("P00", "P01"), 1.0),
            self._meeting("M2", ("P02", "P03"), 2.0),
            self._meeting("M3", ("P04", "P05"), 3.0),
            self._meeting("M4", ("P06", "P07"), 4.0),
            self._meeting("M5", ("P08", "P09"), 5.0),
            self._meeting("M6", ("P00", "P10"), 999.0),
        ]
        membership = {
            key: tuple(meeting.meeting_id for meeting in meetings)
            for key in ("scenario_only", "full_corpus", "full_only")
        }
        result = contribution_limited_aggregates(
            meetings,
            membership,
            ("M1", "M6", "M2", "M3", "M4", "M5"),
        )
        for partition in ("scenario_only", "full_corpus", "full_only"):
            cell = result[partition]
            self.assertEqual(cell["meeting_count"], 5)
            self.assertEqual(cell["unique_participant_count"], 10)
            self.assertEqual(
                cell["suppression_counts"]["repeated_participant_meetings"],
                1,
            )
            for group in ("scalars", "buckets", "dialogue_acts"):
                self.assertTrue(all(
                    not metric["suppressed"]
                    and metric["unique_participant_count"] == 10
                    for metric in cell[group].values()
                ))
            self.assertEqual(
                cell["buckets"]["turn_duration_ms_median"]["value"],
                3.0,
            )

        reversed_result = contribution_limited_aggregates(
            meetings,
            membership,
            ("M6", "M1", "M2", "M3", "M4", "M5"),
        )
        self.assertEqual(
            reversed_result["scenario_only"]["buckets"][
                "turn_duration_ms_median"
            ]["value"],
            202.6,
        )
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("P00", serialized)
        self.assertNotIn('"M1"', serialized)

    def test_cells_below_ten_participants_are_suppressed_not_zero(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            contribution_limited_aggregates,
        )

        meetings = (
            self._meeting("M1", ("P00", "P01"), 1.0),
            self._meeting("M2", ("P02", "P03"), 2.0),
        )
        membership = {
            key: ("M1", "M2")
            for key in ("scenario_only", "full_corpus", "full_only")
        }
        result = contribution_limited_aggregates(
            meetings,
            membership,
            ("M1", "M2"),
        )
        for partition in result.values():
            self.assertEqual(partition["unique_participant_count"], 4)
            self.assertEqual(
                partition["suppression_counts"],
                {
                    "repeated_participant_meetings": 0,
                    "scalar_cells": 4,
                    "bucket_cells": 4,
                    "dialogue_act_cells": 2,
                },
            )
            for group in ("scalars", "buckets", "dialogue_acts"):
                for cell in partition[group].values():
                    self.assertTrue(cell["suppressed"])
                    self.assertEqual(cell["unique_participant_count"], 4)
                    self.assertIsNone(cell["value"])

    def test_aggregation_and_validator_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            contribution_limited_aggregates,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_ami_mechanics_aggregates,
        )

        meetings = (
            self._meeting("M1", ("P00", "P01"), 1.0),
            self._meeting("M2", ("P02", "P03"), 2.0),
        )
        membership = {
            key: ("M1", "M2")
            for key in ("scenario_only", "full_corpus", "full_only")
        }
        official_order = ("M1", "M2")
        aggregate = contribution_limited_aggregates(
            meetings,
            membership,
            official_order,
        )
        validate_ami_mechanics_aggregates(
            aggregate,
            meetings=meetings,
            partition_membership=membership,
            official_order=official_order,
        )

        with self.assertRaisesRegex(ValueError, "unknown meeting"):
            contribution_limited_aggregates(
                meetings,
                {**membership, "scenario_only": ("UNKNOWN",)},
                ("M1", "M2"),
            )
        with self.assertRaisesRegex(ValueError, "duplicate meeting"):
            contribution_limited_aggregates(
                meetings + (meetings[0],),
                membership,
                ("M1", "M2"),
            )
        with self.assertRaisesRegex(ValueError, "at least 10"):
            contribution_limited_aggregates(
                meetings,
                membership,
                ("M1", "M2"),
                minimum_contributors=9,
            )

        leaked = deepcopy(aggregate)
        leaked["scenario_only"]["transcript_text"] = "SECRET"
        with self.assertRaisesRegex(ValueError, "fields"):
            validate_ami_mechanics_aggregates(
                leaked,
                meetings=meetings,
                partition_membership=membership,
                official_order=official_order,
            )

        unsuppressed = deepcopy(aggregate)
        unsuppressed["scenario_only"]["scalars"]["overlap_ratio"][
            "suppressed"
        ] = False
        unsuppressed["scenario_only"]["scalars"]["overlap_ratio"]["value"] = 0.0
        with self.assertRaisesRegex(ValueError, "authoritative"):
            validate_ami_mechanics_aggregates(
                unsuppressed,
                meetings=meetings,
                partition_membership=membership,
                official_order=official_order,
            )

    def test_validator_rejects_dialogue_act_distribution_drift(self) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            contribution_limited_aggregates,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_ami_mechanics_aggregates,
        )

        meetings = tuple(
            self._meeting(
                f"M{index}",
                (f"P{index * 2:02d}", f"P{index * 2 + 1:02d}"),
                float(index),
            )
            for index in range(1, 6)
        )
        meeting_ids = tuple(meeting.meeting_id for meeting in meetings)
        membership = {
            key: meeting_ids
            for key in ("scenario_only", "full_corpus", "full_only")
        }
        aggregate = contribution_limited_aggregates(
            meetings,
            membership,
            meeting_ids,
        )
        validate_ami_mechanics_aggregates(
            aggregate,
            meetings=meetings,
            partition_membership=membership,
            official_order=meeting_ids,
        )
        mutated = deepcopy(aggregate)
        mutated["scenario_only"]["dialogue_acts"]["ami_da_2"]["value"] = 0.5
        with self.assertRaisesRegex(ValueError, "authoritative|sum to one"):
            validate_ami_mechanics_aggregates(
                mutated,
                meetings=meetings,
                partition_membership=membership,
                official_order=meeting_ids,
            )

    def test_validator_rejects_every_unknown_dialogue_output_key(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            contribution_limited_aggregates,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_ami_mechanics_aggregates,
        )

        meetings = tuple(
            self._meeting(
                f"M{index}",
                (f"P{index * 2:02d}", f"P{index * 2 + 1:02d}"),
                float(index),
            )
            for index in range(5)
        )
        meeting_ids = tuple(meeting.meeting_id for meeting in meetings)
        membership = {
            partition: meeting_ids
            for partition in ("scenario_only", "full_corpus", "full_only")
        }
        aggregate = contribution_limited_aggregates(
            meetings,
            membership,
            meeting_ids,
        )
        rejected = (
            "backchannel",
            "inform",
            "question",
            "ami_da_10",
            "SECRET transcript",
            "P0",
            "M1",
            "anger",
            "customer_state",
            "operational_escalation",
            "persuasion_close",
        )
        for label in rejected:
            with self.subTest(label=label):
                mutated = deepcopy(aggregate)
                cells = mutated["scenario_only"]["dialogue_acts"]
                cells[label] = cells.pop("ami_da_2")
                with self.assertRaisesRegex(
                    ValueError,
                    "dialogue-act vocabulary",
                ):
                    validate_ami_mechanics_aggregates(
                        mutated,
                        meetings=meetings,
                        partition_membership=membership,
                        official_order=meeting_ids,
                    )

    def test_validator_recomputes_the_entire_authoritative_aggregate(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            contribution_limited_aggregates,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_ami_mechanics_aggregates,
        )

        meetings = (
            self._meeting("M1", ("P00", "P01"), 1.0),
            self._meeting("M2", ("P02", "P03"), 2.0),
            self._meeting("M3", ("P04", "P05"), 3.0),
            self._meeting("M4", ("P06", "P07"), 4.0),
            self._meeting("M5", ("P08", "P09"), 5.0),
            self._meeting("M6", ("P00", "P10"), 999.0),
        )
        meeting_ids = tuple(meeting.meeting_id for meeting in meetings)
        membership = {
            partition: meeting_ids
            for partition in ("scenario_only", "full_corpus", "full_only")
        }
        official_order = ("M1", "M6", "M2", "M3", "M4", "M5")
        aggregate = contribution_limited_aggregates(
            meetings,
            membership,
            official_order,
        )
        validate_ami_mechanics_aggregates(
            aggregate,
            meetings=meetings,
            partition_membership=membership,
            official_order=official_order,
        )

        def all_cells(partition: dict[str, Any]) -> list[dict[str, Any]]:
            return [
                cell
                for group in ("scalars", "buckets", "dialogue_acts")
                for cell in partition[group].values()
            ]

        mutations: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
            (
                "meeting_count",
                lambda payload: payload["scenario_only"].__setitem__(
                    "meeting_count",
                    4,
                ),
            ),
            (
                "participant_count",
                lambda payload: (
                    payload["scenario_only"].__setitem__(
                        "unique_participant_count",
                        11,
                    ),
                    [
                        cell.__setitem__("unique_participant_count", 11)
                        for cell in all_cells(payload["scenario_only"])
                    ],
                ),
            ),
            (
                "repeated_count",
                lambda payload: payload["scenario_only"][
                    "suppression_counts"
                ].__setitem__("repeated_participant_meetings", 999),
            ),
            (
                "scalar_value",
                lambda payload: payload["scenario_only"]["scalars"][
                    "overlap_ratio"
                ].__setitem__("value", 0.2),
            ),
            (
                "bucket_value",
                lambda payload: payload["scenario_only"]["buckets"][
                    "turn_duration_ms_median"
                ].__setitem__("value", 4.0),
            ),
            (
                "dialogue_values",
                lambda payload: (
                    payload["scenario_only"]["dialogue_acts"][
                        "ami_da_1"
                    ].__setitem__("value", 0.3),
                    payload["scenario_only"]["dialogue_acts"][
                        "ami_da_2"
                    ].__setitem__("value", 0.7),
                ),
            ),
        )
        for name, mutation in mutations:
            with self.subTest(payload_mutation=name):
                mutated = deepcopy(aggregate)
                mutation(mutated)
                with self.assertRaisesRegex(ValueError, "authoritative"):
                    validate_ami_mechanics_aggregates(
                        mutated,
                        meetings=meetings,
                        partition_membership=membership,
                        official_order=official_order,
                    )

        omitted = {
            **membership,
            "scenario_only": tuple(
                meeting_id
                for meeting_id in membership["scenario_only"]
                if meeting_id != "M6"
            ),
        }
        with self.assertRaisesRegex(ValueError, "authoritative"):
            validate_ami_mechanics_aggregates(
                aggregate,
                meetings=meetings,
                partition_membership=omitted,
                official_order=official_order,
            )
        unknown = {
            **membership,
            "scenario_only": membership["scenario_only"] + ("UNKNOWN",),
        }
        with self.assertRaisesRegex(ValueError, "unknown meeting"):
            validate_ami_mechanics_aggregates(
                aggregate,
                meetings=meetings,
                partition_membership=unknown,
                official_order=official_order,
            )
        with self.assertRaisesRegex(ValueError, "authoritative"):
            validate_ami_mechanics_aggregates(
                aggregate,
                meetings=meetings,
                partition_membership=membership,
                official_order=("M6", "M1", "M2", "M3", "M4", "M5"),
            )

        mutated_meeting = replace(
            meetings[0],
            values=tuple(
                (
                    key,
                    value + 1.0
                    if key == "turn_duration_ms_median"
                    else value,
                )
                for key, value in meetings[0].values
            ),
        )
        with self.assertRaisesRegex(ValueError, "authoritative"):
            validate_ami_mechanics_aggregates(
                aggregate,
                meetings=(mutated_meeting,) + meetings[1:],
                partition_membership=membership,
                official_order=official_order,
            )

        sparse_meetings = meetings[:2]
        sparse_ids = tuple(meeting.meeting_id for meeting in sparse_meetings)
        sparse_membership = {
            partition: sparse_ids
            for partition in ("scenario_only", "full_corpus", "full_only")
        }
        sparse = contribution_limited_aggregates(
            sparse_meetings,
            sparse_membership,
            sparse_ids,
        )
        for count_key in (
            "scalar_cells",
            "bucket_cells",
            "dialogue_act_cells",
        ):
            with self.subTest(suppression_count=count_key):
                mutated = deepcopy(sparse)
                mutated["scenario_only"]["suppression_counts"][count_key] += 1
                with self.assertRaisesRegex(ValueError, "authoritative"):
                    validate_ami_mechanics_aggregates(
                        mutated,
                        meetings=sparse_meetings,
                        partition_membership=sparse_membership,
                        official_order=sparse_ids,
                    )


class SecurePublicMaterialByteTests(unittest.TestCase):
    _OPEN_AUDIT_STATE: Any = None
    _OPEN_AUDIT_HOOK_INSTALLED = False

    @staticmethod
    def _runner_paths(root: Path) -> tuple[Any, Path]:
        from scripts import run_emotion_state_002_phase_b as runner

        input_root = root / "inputs"
        state_root = root / "state"
        canonical_root = root / "canonical"
        public_root = input_root / "public-material"
        for directory in (
            input_root,
            state_root,
            canonical_root,
            public_root,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        paths = runner.RunnerPaths.for_testing(
            project_root=root,
            input_root=input_root,
            state_root=state_root,
            canonical_root=canonical_root,
            config_path=input_root / "config.json",
            environment_lock_path=input_root / "requirements.lock",
            feature_schema_path=input_root / "feature.schema.json",
            split_schema_path=input_root / "split.schema.json",
            split_manifest_path=input_root / "split-manifest.json",
            input_ledger_path=input_root / "input-ledger.json",
            non_lockbox_packet_path=state_root / "non-lockbox.json",
            lockbox_result_path=state_root / "lockbox.json",
            public_material_root=public_root,
        )
        return paths, public_root

    @staticmethod
    def _ami_byte_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
        from scripts.emotion_state_phase_b_ami_mechanics import AmiXmlBytes

        def source(path: Path) -> Any:
            return AmiXmlBytes(path.name, path.read_bytes())

        return {
            "metadata": source(fixture["metadata_path"]),
            "word_sources": tuple(source(path) for path in fixture["word_paths"]),
            "timing_link_sources": tuple(
                source(path) for path in fixture["timing_link_paths"]
            ),
            "dialogue_act_sources": tuple(
                source(path) for path in fixture["dialogue_act_paths"]
            ),
            "known_meetings": fixture["known_meetings"],
            "participant_metadata": (
                None
                if "participant_metadata_path" not in fixture
                else source(fixture["participant_metadata_path"])
            ),
        }

    @staticmethod
    def _read_verified_fixture(
        runner: Any,
        paths: Any,
        path: Path,
        content: bytes,
    ) -> Any:
        return runner._read_verified_public_bytes(
            paths,
            path,
            expected_sha256=hashlib.sha256(content).hexdigest().upper(),
            expected_size_bytes=len(content),
            maximum_bytes=len(content),
        )

    @staticmethod
    def _tone_wav_bytes() -> bytes:
        import io
        import struct
        import wave

        sample_rate = 16000
        samples = [
            round(
                0.5
                * 32767
                * math.sin(2 * math.pi * 200.0 * index / sample_rate)
            )
            for index in range(sample_rate)
        ]
        output = io.BytesIO()
        with wave.open(output, "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(sample_rate)
            target.writeframes(
                struct.pack("<" + "h" * len(samples), *samples)
            )
        return output.getvalue()

    @classmethod
    def _ensure_open_audit_hook(cls) -> None:
        import contextvars
        import sys

        if cls._OPEN_AUDIT_STATE is None:
            cls._OPEN_AUDIT_STATE = contextvars.ContextVar(
                "phase_b_parser_open_audit_state",
                default=None,
            )
        if cls._OPEN_AUDIT_HOOK_INSTALLED:
            return
        state_variable = cls._OPEN_AUDIT_STATE

        def reject_active_open(event: str, arguments: tuple[Any, ...]) -> None:
            active_events = state_variable.get()
            if event == "open" and active_events is not None:
                active_events.append(arguments)
                raise AssertionError("blocked filesystem open audit event")

        sys.addaudithook(reject_active_open)
        cls._OPEN_AUDIT_HOOK_INSTALLED = True

    @contextmanager
    def _post_verified_no_open_events(
        self,
        *,
        wave_module: Any | None = None,
        xml_module: Any | None = None,
    ) -> Any:
        self._ensure_open_audit_hook()
        open_events: list[tuple[Any, ...]] = []
        token = self._OPEN_AUDIT_STATE.set(open_events)
        try:
            with ExitStack() as stack:
                if wave_module is not None:
                    real_wave_open = wave_module.wave.open

                    def guarded_wave_open(
                        source: Any,
                        *args: Any,
                        **kwargs: Any,
                    ) -> Any:
                        if isinstance(source, (str, os.PathLike)):
                            raise AssertionError(
                                "blocked path-like wave.open"
                            )
                        return real_wave_open(source, *args, **kwargs)

                    stack.enter_context(
                        patch.object(
                            wave_module.wave,
                            "open",
                            side_effect=guarded_wave_open,
                        )
                    )
                if xml_module is not None:
                    stack.enter_context(
                        patch.object(
                            xml_module.ET,
                            "parse",
                            side_effect=AssertionError(
                                "blocked ElementTree.parse"
                            ),
                        )
                    )
                yield open_events
        finally:
            self._OPEN_AUDIT_STATE.reset(token)

    def _exercise_open_audit_guard(
        self,
        runner: Any,
        source_path: Path,
        open_events: list[tuple[Any, ...]],
        prebound_io_open: Callable[..., Any],
        *,
        wave_module: Any | None = None,
        xml_module: Any | None = None,
    ) -> None:
        import builtins
        import io

        probes: dict[str, Callable[[], Any]] = {
            "pre-bound io.open": lambda: prebound_io_open(source_path, "rb"),
            "dynamic io.open": lambda: io.open(source_path, "rb"),
            "builtins.open": lambda: builtins.open(source_path, "rb"),
            "Path.open": lambda: source_path.open("rb"),
            "Path.read_bytes": source_path.read_bytes,
            "os.open": lambda: os.open(source_path, os.O_RDONLY),
            "_read_file_nofollow": lambda: runner._read_file_nofollow(
                source_path
            ),
        }
        for label, probe in probes.items():
            with self.subTest(open_audit_probe=label):
                event_count = len(open_events)
                with self.assertRaisesRegex(
                    AssertionError,
                    "blocked filesystem open audit event",
                ):
                    probe()
                self.assertEqual(len(open_events), event_count + 1)
        if wave_module is not None:
            with self.assertRaisesRegex(
                AssertionError,
                "blocked path-like wave.open",
            ):
                wave_module.wave.open(str(source_path), "rb")
        if xml_module is not None:
            with self.assertRaisesRegex(
                AssertionError,
                "blocked ElementTree.parse",
            ):
                xml_module.ET.parse(source_path)

    def test_verified_crema_content_composes_without_reopen(self) -> None:
        import codecs
        import io

        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts import run_emotion_state_002_phase_b as runner

        prebound_io_open = io.open
        codecs.lookup("utf-8-sig")
        finished_bytes = (
            b",localid,pos,ans,ttr,queryType,numTries,clipNum,questNum,"
            b"subType,clipName,sessionNums,respEmo,respLevel,dispEmo,"
            b"dispVal,dispLevel\n"
            b"1,r1,1,A_80,1,1,0,1,1,4,1001_DFA_ANG_XX,s1,A,80,A,50,X\n"
            b"2,r2,1,A_70,1,1,0,1,1,4,1001_DFA_ANG_XX,s2,A,70,A,50,X\n"
        )
        summary_bytes = (
            b",FileName,VoiceVote,VoiceLevel,FaceVote,FaceLevel,"
            b"MultiModalVote,MultiModalLevel\n"
            b"1,1001_DFA_ANG_XX,A,75,A,75,A,75\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            paths, public_root = self._runner_paths(Path(directory).resolve())
            finished_path = public_root / "finishedResponses.csv"
            summary_path = public_root / "summaryTable.csv"
            finished_path.write_bytes(finished_bytes)
            summary_path.write_bytes(summary_bytes)
            finished = self._read_verified_fixture(
                runner,
                paths,
                finished_path,
                finished_bytes,
            )
            summary = self._read_verified_fixture(
                runner,
                paths,
                summary_path,
                summary_bytes,
            )

            with self._post_verified_no_open_events() as open_events:
                first = evaluation.load_crema_reference_labels_bytes(
                    finished.content,
                    summary.content,
                    ("1001_DFA_ANG_XX",),
                )
                second = evaluation.load_crema_reference_labels_bytes(
                    finished.content,
                    summary.content,
                    ("1001_DFA_ANG_XX",),
                )
                self.assertEqual(open_events, [])
                self.assertEqual(first, second)
                records, ledger = first
                self.assertEqual(len(records), 1)
                self.assertEqual(
                    (
                        records[0].clip_stem,
                        records[0].actor_id,
                        records[0].sentence_id,
                        records[0].label,
                        records[0].vote_distribution,
                    ),
                    (
                        "1001_DFA_ANG_XX",
                        "1001",
                        "DFA",
                        "A",
                        (("A", 2),),
                    ),
                )
                self.assertEqual(
                    ledger["source_binding"][
                        "finished_responses_sha256"
                    ],
                    finished.sha256,
                )
                self.assertEqual(
                    ledger["source_binding"]["summary_table_sha256"],
                    summary.sha256,
                )
                self._exercise_open_audit_guard(
                    runner,
                    finished_path,
                    open_events,
                    prebound_io_open,
                )
            self.assertIsNone(self._OPEN_AUDIT_STATE.get())
            with prebound_io_open(finished_path, "rb") as reopened:
                self.assertEqual(reopened.read(1), finished_bytes[:1])

    def test_verified_wav_content_composes_without_reopen(self) -> None:
        import io

        from scripts import emotion_state_phase_b_features as features
        from scripts import run_emotion_state_002_phase_b as runner

        prebound_io_open = io.open
        wav_bytes = self._tone_wav_bytes()
        with tempfile.TemporaryDirectory() as directory:
            paths, public_root = self._runner_paths(Path(directory).resolve())
            wav_path = public_root / "tone.wav"
            wav_path.write_bytes(wav_bytes)
            verified = self._read_verified_fixture(
                runner,
                paths,
                wav_path,
                wav_bytes,
            )

            with self._post_verified_no_open_events(
                wave_module=features,
            ) as open_events:
                first = features.extract_acoustic_features_bytes(
                    verified.content
                )
                second = features.extract_acoustic_features_bytes(
                    verified.content
                )
                self.assertEqual(open_events, [])
                self.assertEqual(first, second)
                self.assertEqual(tuple(first), features.FEATURE_NAMES)
                self.assertEqual(first["duration_seconds"], 1.0)
                self.assertAlmostEqual(
                    first["f0_median_hz"],
                    200.0,
                    delta=2.0,
                )
                self._exercise_open_audit_guard(
                    runner,
                    wav_path,
                    open_events,
                    prebound_io_open,
                    wave_module=features,
                )
            self.assertIsNone(self._OPEN_AUDIT_STATE.get())

    def test_verified_ami_content_composes_without_reopen(self) -> None:
        import io

        from scripts import emotion_state_phase_b_ami_mechanics as ami
        from scripts import run_emotion_state_002_phase_b as runner

        prebound_io_open = io.open
        contents = {
            "meetings.xml": (
                b"<corpus><meeting id=\"M1\">"
                b"<participant code=\"A\" participant_id=\"P-A\" />"
                b"</meeting></corpus>"
            ),
            "M1.A.words.xml": (
                b"<words meeting_id=\"M1\" agent=\"A\">"
                b"<w id=\"w1\" starttime=\"0.000\" endtime=\"0.500\">"
                b"DISCARDED TRANSCRIPT</w></words>"
            ),
            "M1.A.segments.xml": (
                b"<segments meeting_id=\"M1\" agent=\"A\">"
                b"<segment id=\"s1\"><child "
                b"href=\"M1.A.words.xml#id(w1)\" /></segment></segments>"
            ),
            "M1.A.dialog-act.xml": (
                b"<dialogue-acts meeting_id=\"M1\" agent=\"A\" "
                b"synthetic_legacy_schema=\"phase_b_ami_mechanics_v1\">"
                b"<dact id=\"d1\" type=\"ami_da_2\"><child "
                b"href=\"M1.A.segments.xml#id(s1)\" /></dact>"
                b"</dialogue-acts>"
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            paths, public_root = self._runner_paths(Path(directory).resolve())
            verified: dict[str, Any] = {}
            source_paths: dict[str, Path] = {}
            for filename, content in contents.items():
                source_path = public_root / filename
                source_path.write_bytes(content)
                source_paths[filename] = source_path
                verified[filename] = self._read_verified_fixture(
                    runner,
                    paths,
                    source_path,
                    content,
                )

            with self._post_verified_no_open_events(
                xml_module=ami,
            ) as open_events:
                arguments = {
                    "metadata": ami.AmiXmlBytes(
                        verified["meetings.xml"].logical_name,
                        verified["meetings.xml"].content,
                    ),
                    "word_sources": (
                        ami.AmiXmlBytes(
                            verified["M1.A.words.xml"].logical_name,
                            verified["M1.A.words.xml"].content,
                        ),
                    ),
                    "timing_link_sources": (
                        ami.AmiXmlBytes(
                            verified["M1.A.segments.xml"].logical_name,
                            verified["M1.A.segments.xml"].content,
                        ),
                    ),
                    "dialogue_act_sources": (
                        ami.AmiXmlBytes(
                            verified[
                                "M1.A.dialog-act.xml"
                            ].logical_name,
                            verified["M1.A.dialog-act.xml"].content,
                        ),
                    ),
                    "known_meetings": ("M1",),
                }
                first = ami.load_ami_turns_from_bytes(**arguments)
                second = ami.load_ami_turns_from_bytes(**arguments)
                self.assertEqual(open_events, [])
                self.assertEqual(first, second)
                self.assertEqual(
                    first,
                    (ami.Turn("M1", "P-A", 0, 500, "ami_da_2"),),
                )
                self.assertNotIn("TRANSCRIPT", repr(first).upper())
                self._exercise_open_audit_guard(
                    runner,
                    source_paths["meetings.xml"],
                    open_events,
                    prebound_io_open,
                    xml_module=ami,
                )
            self.assertIsNone(self._OPEN_AUDIT_STATE.get())

    def test_verified_reader_binds_one_nofollow_read_and_rejects_violations(
        self,
    ) -> None:
        from scripts import run_emotion_state_002_phase_b as runner

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            paths, public_root = self._runner_paths(root)
            material = public_root / "nested" / "sample.bin"
            material.parent.mkdir()
            material.write_bytes(b"unused-on-disk-content")
            content = b"identity-bound-returned-content"
            digest = hashlib.sha256(content).hexdigest().upper()

            with patch.object(
                runner,
                "_read_file_nofollow",
                return_value=content,
            ) as read:
                verified = runner._read_verified_public_bytes(
                    paths,
                    material,
                    expected_sha256=digest,
                    expected_size_bytes=len(content),
                    maximum_bytes=len(content),
                )
            read.assert_called_once_with(
                material,
                maximum_bytes=len(content),
            )
            self.assertEqual(verified.logical_name, "nested/sample.bin")
            self.assertEqual(verified.content, content)
            self.assertEqual(verified.sha256, digest)
            self.assertEqual(verified.size_bytes, len(content))

            for field, value, pattern in (
                ("expected_sha256", digest.lower(), "uppercase SHA-256"),
                ("expected_sha256", "A" * 63, "uppercase SHA-256"),
                ("expected_size_bytes", True, "non-negative integer"),
                ("expected_size_bytes", 1.0, "non-negative integer"),
                ("expected_size_bytes", -1, "non-negative integer"),
                ("maximum_bytes", True, "non-negative integer"),
                ("maximum_bytes", 1.0, "non-negative integer"),
                ("maximum_bytes", -1, "non-negative integer"),
            ):
                arguments = {
                    "expected_sha256": digest,
                    "expected_size_bytes": len(content),
                    "maximum_bytes": len(content),
                }
                arguments[field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(runner.RunnerError, pattern):
                        runner._read_verified_public_bytes(
                            paths,
                            material,
                            **arguments,
                        )

            with patch.object(
                runner,
                "_read_file_nofollow",
                return_value=content,
            ) as read:
                with self.assertRaisesRegex(runner.RunnerError, "SHA-256"):
                    runner._read_verified_public_bytes(
                        paths,
                        material,
                        expected_sha256="0" * 64,
                        expected_size_bytes=len(content),
                        maximum_bytes=len(content),
                    )
                read.assert_called_once()
            with patch.object(
                runner,
                "_read_file_nofollow",
                return_value=content,
            ) as read:
                with self.assertRaisesRegex(runner.RunnerError, "byte count"):
                    runner._read_verified_public_bytes(
                        paths,
                        material,
                        expected_sha256=digest,
                        expected_size_bytes=len(content) + 1,
                        maximum_bytes=len(content) + 1,
                    )
                read.assert_called_once()
            with patch.object(
                runner,
                "_read_file_nofollow",
                return_value=content,
            ) as read:
                with self.assertRaisesRegex(runner.RunnerError, "allowed size"):
                    runner._read_verified_public_bytes(
                        paths,
                        material,
                        expected_sha256=digest,
                        expected_size_bytes=len(content),
                        maximum_bytes=len(content) - 1,
                    )
                read.assert_not_called()

            outside = root / "outside.bin"
            outside.write_bytes(content)
            private = public_root / "private" / "blocked.bin"
            private.parent.mkdir()
            private.write_bytes(content)
            missing = public_root / "missing.bin"
            directory_entry = public_root / "directory.bin"
            directory_entry.mkdir()
            for path, pattern in (
                (outside, "allowed root"),
                (private, "private path"),
                (missing, "missing"),
                (directory_entry, "regular file"),
            ):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(runner.RunnerError, pattern):
                        runner._read_verified_public_bytes(
                            paths,
                            path,
                            expected_sha256=digest,
                            expected_size_bytes=len(content),
                            maximum_bytes=len(content),
                        )

            real_link_check = runner._is_link_or_reparse

            def material_is_reparse(
                path: Path,
                status: os.stat_result | Any,
            ) -> bool:
                return (
                    Path(path) == material
                    or real_link_check(Path(path), status)
                )

            with patch.object(
                runner,
                "_is_link_or_reparse",
                side_effect=material_is_reparse,
            ):
                with self.assertRaisesRegex(runner.RunnerError, "reparse"):
                    runner._read_verified_public_bytes(
                        paths,
                        material,
                        expected_sha256=digest,
                        expected_size_bytes=len(content),
                        maximum_bytes=len(content),
                    )

    def test_crema_bytes_are_deterministic_without_filesystem_reopen(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
            load_crema_reference_labels_bytes,
        )

        stems = {
            "1001_DFA_ANG_XX",
            "1002_IEO_HAP_HI",
            "1003_TAI_FEA_XX",
        }
        with tempfile.TemporaryDirectory() as directory:
            finished, summary = CremaReferenceLabelTests()._write_sources(
                Path(directory)
            )
            finished_bytes = finished.read_bytes()
            summary_bytes = summary.read_bytes()
            compatibility = load_crema_reference_labels(
                finished,
                summary,
                stems,
            )
            with patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("byte loader reopened a path"),
            ):
                first = load_crema_reference_labels_bytes(
                    finished_bytes,
                    summary_bytes,
                    stems,
                )
                second = load_crema_reference_labels_bytes(
                    finished_bytes,
                    summary_bytes,
                    stems,
                )
        self.assertEqual(first, compatibility)
        self.assertEqual(second, first)
        self.assertEqual(
            first[1]["source_binding"]["finished_responses_sha256"],
            hashlib.sha256(finished_bytes).hexdigest().upper(),
        )
        self.assertEqual(
            first[1]["source_binding"]["summary_table_sha256"],
            hashlib.sha256(summary_bytes).hexdigest().upper(),
        )

    def test_wav_bytes_match_wrapper_without_path_wave_open(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_features as features

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tone.wav"
            AcousticFeatureTests._write_tone(
                path,
                hz=200.0,
                seconds=1.0,
                amplitude=0.5,
            )
            wav_bytes = path.read_bytes()
            compatibility = features.extract_acoustic_features(path)
            real_wave_open = features.wave.open

            def memory_wave_open(source: Any, mode: str) -> Any:
                if isinstance(source, (str, os.PathLike)):
                    raise AssertionError("byte extractor used path-based wave.open")
                return real_wave_open(source, mode)

            with (
                patch.object(
                    Path,
                    "read_bytes",
                    side_effect=AssertionError("byte extractor reopened a path"),
                ),
                patch.object(
                    features.wave,
                    "open",
                    side_effect=memory_wave_open,
                ),
            ):
                extracted = features.extract_acoustic_features_bytes(wav_bytes)
        self.assertEqual(extracted, compatibility)

    def test_ami_bytes_match_wrapper_without_parse_or_filesystem_reopen(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_ami_mechanics as ami

        with tempfile.TemporaryDirectory() as directory:
            fixture = AmiMechanicsTests._write_fixture(Path(directory))
            byte_fixture = self._ami_byte_fixture(fixture)
            compatibility = ami.load_ami_turns(**fixture)
            with (
                patch.object(
                    Path,
                    "read_bytes",
                    side_effect=AssertionError("AMI byte loader reopened a path"),
                ),
                patch.object(
                    ami.ET,
                    "parse",
                    side_effect=AssertionError("AMI byte loader used ET.parse"),
                ),
            ):
                turns = ami.load_ami_turns_from_bytes(**byte_fixture)
        self.assertEqual(turns, compatibility)
        self.assertNotIn("SECRET", repr(turns).upper())
        self.assertTrue(all(not hasattr(turn, "text") for turn in turns))

    def test_byte_apis_reject_nonbytes_and_malformed_bytes(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_ami_mechanics as ami
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts import emotion_state_phase_b_features as features

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            finished, summary = CremaReferenceLabelTests()._write_sources(root)
            finished_bytes = finished.read_bytes()
            summary_bytes = summary.read_bytes()
            tone = root / "tone.wav"
            AcousticFeatureTests._write_tone(
                tone,
                hz=200.0,
                seconds=1.0,
                amplitude=0.5,
            )
            wav_bytes = tone.read_bytes()
            ami_root = root / "ami"
            ami_root.mkdir()
            fixture = AmiMechanicsTests._write_fixture(ami_root)
            ami_bytes = self._ami_byte_fixture(fixture)

        for value in (
            bytearray(finished_bytes),
            memoryview(finished_bytes),
            "finishedResponses.csv",
            Path("finishedResponses.csv"),
        ):
            with self.subTest(api="crema", value_type=type(value).__name__):
                with self.assertRaisesRegex((TypeError, ValueError), "bytes"):
                    evaluation.load_crema_reference_labels_bytes(
                        value,
                        summary_bytes,
                        {"1001_DFA_ANG_XX"},
                    )
        for value in (
            bytearray(wav_bytes),
            memoryview(wav_bytes),
            "tone.wav",
            Path("tone.wav"),
        ):
            with self.subTest(api="wav", value_type=type(value).__name__):
                with self.assertRaisesRegex((TypeError, ValueError), "bytes"):
                    features.extract_acoustic_features_bytes(value)
        for value in (
            bytearray(b"<root />"),
            memoryview(b"<root />"),
            "<root />",
            Path("meetings.xml"),
        ):
            with self.subTest(api="ami", value_type=type(value).__name__):
                with self.assertRaisesRegex((TypeError, ValueError), "bytes"):
                    ami.AmiXmlBytes("meetings.xml", value)

        with self.assertRaisesRegex(ValueError, "CSV"):
            evaluation.load_crema_reference_labels_bytes(
                b"not,csv\n",
                summary_bytes,
                {"1001_DFA_ANG_XX"},
            )
        with self.assertRaisesRegex(
            features.FeatureExtractionError,
            "malformed",
        ):
            features.extract_acoustic_features_bytes(b"not a wav")
        malformed_ami = {
            **ami_bytes,
            "metadata": ami.AmiXmlBytes("meetings.xml", b"<broken"),
        }
        with self.assertRaisesRegex(ValueError, "AMI XML"):
            ami.load_ami_turns_from_bytes(**malformed_ami)

    def test_ami_bytes_reject_unsafe_duplicate_and_unresolved_local_names(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_ami_mechanics as ami

        with tempfile.TemporaryDirectory() as directory:
            fixture = AmiMechanicsTests._write_fixture(Path(directory))
            byte_fixture = self._ami_byte_fixture(fixture)

        with (
            patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("AMI validation touched a path"),
            ),
            patch.object(
                ami.ET,
                "parse",
                side_effect=AssertionError("AMI validation used ET.parse"),
            ),
        ):
            duplicate = {
                **byte_fixture,
                "word_sources": (
                    byte_fixture["word_sources"][0],
                    byte_fixture["word_sources"][0],
                ),
            }
            with self.assertRaisesRegex(ValueError, "duplicate AMI"):
                ami.load_ami_turns_from_bytes(**duplicate)

            for filename in (
                "../M1.A.words.xml",
                "nested/M1.A.words.xml",
                r"nested\M1.A.words.xml",
                "C:M1.A.words.xml",
                ".",
                "..",
            ):
                with self.subTest(filename=filename):
                    with self.assertRaisesRegex(ValueError, "filename"):
                        ami.AmiXmlBytes(
                            filename,
                            byte_fixture["word_sources"][0].content,
                        )

            unresolved_content = byte_fixture["timing_link_sources"][
                0
            ].content.replace(
                b"M1.A.words.xml",
                b"missing.words.xml",
            )
            unresolved = {
                **byte_fixture,
                "timing_link_sources": (
                    replace(
                        byte_fixture["timing_link_sources"][0],
                        content=unresolved_content,
                    ),
                    byte_fixture["timing_link_sources"][1],
                ),
            }
            with self.assertRaisesRegex(ValueError, "unknown local word file"):
                ami.load_ami_turns_from_bytes(**unresolved)


class EvaluationTests(unittest.TestCase):
    CLASS_ORDER = ("A", "D", "F", "H", "N", "S")
    MODEL_KEYS = ("class_prior", "sentence_id", "acoustic")
    MODEL_SEED = 71019

    @classmethod
    def setUpClass(cls) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            mint_validated_split_assignment,
        )
        from scripts.emotion_state_phase_b_splits import build_actor_split

        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        digest = hashlib.sha256(json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        records = ActorSplitTests._records(varied_vectors=True)
        assignment = build_actor_split(records, digest)
        cls.AUTHORITATIVE_RECORDS = tuple(records)
        cls.CONFIGURATION_DIGEST = digest
        cls.SPLIT_ASSIGNMENT = mint_validated_split_assignment(
            records,
            assignment,
            digest,
        )
        cls.ACTORS_BY_ROLE = {
            role: tuple(
                actor
                for actor, assigned_role in sorted(assignment.items())
                if assigned_role == role
            )
            for role in ActorSplitTests.PARTITION_ORDER
        }
        cls.RECORDS_BY_ROLE = {
            role: tuple(sorted(
                (
                    record
                    for record in records
                    if assignment[record.actor_id] == role
                ),
                key=lambda record: record.clip_stem,
            ))
            for role in ActorSplitTests.PARTITION_ORDER
        }
        cls._SEMANTIC_CACHE = {}

    def _actors_for_role(self, role: str, count: int) -> list[str]:
        actors = self.ACTORS_BY_ROLE[role]
        return [actors[index % len(actors)] for index in range(count)]

    def _authoritative_partition(
        self,
        role: str,
        *,
        feature_variant: int = 0,
        row_ids: Any = None,
        labels: Any = None,
    ) -> Any:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            frozen_model_identity,
            mint_partition_evidence,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            EXPECTED_CONFIG,
            EXPECTED_ENVIRONMENT_LOCK,
            EXPECTED_FEATURE_SCHEMA,
            EXPECTED_SPLIT_SCHEMA,
        )

        records = self.RECORDS_BY_ROLE[role]
        authoritative_rows = [record.clip_stem for record in records]
        actors = [record.actor_id for record in records]
        sentences = np.asarray(
            [record.sentence_id for record in records],
            dtype="<U3",
        )
        authoritative_labels = np.asarray(
            [record.label for record in records],
            dtype="<U1",
        )
        features = np.zeros((len(records), 17), dtype=np.float64)
        for index, record in enumerate(records):
            label_index = self.CLASS_ORDER.index(str(record.label))
            sentence_index = ActorSplitTests.SENTENCES.index(record.sentence_id)
            actor_number = int(record.actor_id) - 1000
            features[index, label_index] = 3.0
            features[index, 6] = actor_number / 100.0
            features[index, 7] = sentence_index / 11.0
            features[index, 8] = ((actor_number + sentence_index) % 7) / 7.0
            features[index, 9] = float(feature_variant) * (
                (label_index + 1) * ((actor_number % 5) - 2) / 10.0
            )
            features[index, 10] = float(index % 13) / 13.0
        upstream = hashlib.sha256(
            f"synthetic-upstream:{role}:{feature_variant}:".encode("ascii")
            + features.tobytes(order="C")
        ).hexdigest().upper()
        return mint_partition_evidence(
            partition_role=role,
            row_ids=authoritative_rows if row_ids is None else row_ids,
            actor_ids=actors,
            labels=authoritative_labels if labels is None else labels,
            sentences=sentences,
            features=features,
            upstream_acoustic_source_commitment_sha256=upstream,
            split_assignment=self.SPLIT_ASSIGNMENT,
            configuration=deepcopy(EXPECTED_CONFIG),
            environment_lock=deepcopy(EXPECTED_ENVIRONMENT_LOCK),
            feature_schema=deepcopy(EXPECTED_FEATURE_SCHEMA),
            split_schema=deepcopy(EXPECTED_SPLIT_SCHEMA),
            model_identity=frozen_model_identity(self.MODEL_SEED),
        )

    def _semantic_artifacts(self, variant: int = 0) -> dict[str, Any]:
        from scripts.emotion_state_phase_b_evaluation import (
            build_decision_evidence,
            calibrate_thresholds,
            evaluate_partition,
            fit_frozen_models,
            mint_slice_analysis,
            paired_actor_bootstrap,
            predict_probabilities,
        )

        cached = self._SEMANTIC_CACHE.get(variant)
        if cached is not None:
            return cached
        training = self._authoritative_partition(
            "training_discovery",
            feature_variant=variant,
        )
        fitted = fit_frozen_models(training, self.MODEL_SEED)
        calibration_partition = self._authoritative_partition("calibration")
        calibration_probabilities = predict_probabilities(
            fitted,
            calibration_partition,
        )
        calibration = calibrate_thresholds(
            calibration_probabilities,
            (1.0, 0.8, 0.6),
        )
        final_partition = self._authoritative_partition("final_lockbox")
        final_probabilities = predict_probabilities(fitted, final_partition)
        evaluation = evaluate_partition(final_probabilities, calibration)
        seed = int(self.CONFIGURATION_DIGEST[:16], 16)
        bootstrap = paired_actor_bootstrap(
            final_probabilities,
            2000,
            seed,
        )
        full_rows = [
            record.clip_stem
            for record in self.RECORDS_BY_ROLE["final_lockbox"]
        ]
        slice_analysis = mint_slice_analysis(
            final_probabilities,
            evaluation,
            {
                "all_eligible_a": full_rows,
                "all_eligible_b": list(reversed(full_rows)),
            },
        )
        decision = build_decision_evidence(
            evaluation,
            bootstrap,
            slice_analysis,
        )
        cached = {
            "training": training,
            "fitted": fitted,
            "calibration_partition": calibration_partition,
            "calibration_probabilities": calibration_probabilities,
            "calibration": calibration,
            "final_partition": final_partition,
            "final_probabilities": final_probabilities,
            "evaluation": evaluation,
            "bootstrap": bootstrap,
            "slice_analysis": slice_analysis,
            "decision": decision,
        }
        self._SEMANTIC_CACHE[variant] = cached
        return cached

    def _training_arrays(self) -> tuple[Any, Any, Any]:
        import numpy as np

        prevalence = {
            "A": 5,
            "D": 10,
            "F": 15,
            "H": 20,
            "N": 8,
            "S": 7,
        }
        labels = np.asarray([
            label
            for label in self.CLASS_ORDER
            for _ in range(prevalence[label])
        ], dtype="<U1")
        features = np.zeros((len(labels), 17), dtype=np.float64)
        for row, label in enumerate(labels):
            features[row, self.CLASS_ORDER.index(label)] = 3.0
            features[row, 6] = float(row % 5) / 10.0
        sentences = np.asarray(
            [f"S{row % 12:02d}" for row in range(len(labels))],
            dtype="<U3",
        )
        return features, sentences, labels

    def _partition_evidence(
        self,
        role: str,
        labels: Any,
        *,
        actor_ids: list[str] | None = None,
        features: Any = None,
        sentences: Any = None,
        probabilities: dict[str, Any] | None = None,
        assignment_role: str | None = None,
        seed: int | None = None,
    ) -> Any:
        from scripts.emotion_state_phase_b_evaluation import (
            frozen_model_identity,
            mint_partition_evidence,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            EXPECTED_CONFIG,
            EXPECTED_ENVIRONMENT_LOCK,
            EXPECTED_FEATURE_SCHEMA,
            EXPECTED_SPLIT_SCHEMA,
        )

        count = len(labels)
        actor_role = assignment_role or role
        actors = actor_ids or self._actors_for_role(actor_role, count)
        return mint_partition_evidence(
            partition_role=role,
            row_ids=[f"row-{index:04d}" for index in range(count)],
            actor_ids=actors,
            labels=labels,
            split_assignment=self.SPLIT_ASSIGNMENT,
            configuration=deepcopy(EXPECTED_CONFIG),
            environment_lock=deepcopy(EXPECTED_ENVIRONMENT_LOCK),
            feature_schema=deepcopy(EXPECTED_FEATURE_SCHEMA),
            split_schema=deepcopy(EXPECTED_SPLIT_SCHEMA),
            features=features,
            sentences=sentences,
            probabilities=probabilities,
            model_identity=frozen_model_identity(seed or self.MODEL_SEED),
        )

    def _metric_arrays(
        self,
        actor_count: int = 10,
        *,
        role: str = "final_lockbox",
    ) -> tuple[Any, dict[str, Any], list[str]]:
        import numpy as np

        patterns = np.asarray(
            [
                [0.70, 0.10, 0.05, 0.05, 0.05, 0.05],
                [0.30, 0.25, 0.20, 0.10, 0.10, 0.05],
                [0.10, 0.10, 0.40, 0.20, 0.10, 0.10],
                [0.10, 0.10, 0.10, 0.40, 0.20, 0.10],
                [0.10, 0.10, 0.10, 0.10, 0.30, 0.30],
                [0.20, 0.10, 0.10, 0.10, 0.10, 0.40],
            ],
            dtype=np.float64,
        )
        labels = np.asarray(self.CLASS_ORDER * actor_count, dtype="<U1")
        probabilities = np.tile(patterns, (actor_count, 1))
        selected_actors = self.ACTORS_BY_ROLE[role][:actor_count]
        actors = [
            actor
            for actor in selected_actors
            for _ in self.CLASS_ORDER
        ]
        return (
            labels,
            {key: probabilities.copy() for key in self.MODEL_KEYS},
            actors,
        )

    def _calibration_probabilities(self) -> dict[str, Any]:
        import numpy as np

        confidences = (0.20, 0.30, 0.40, 0.40, 0.40, 0.50)
        rows = np.asarray(
            [
                [confidence, *((1.0 - confidence) / 5.0 for _ in range(5))]
                for confidence in confidences
            ],
            dtype=np.float64,
        )
        return {key: rows.copy() for key in self.MODEL_KEYS}

    def _config_identity(self) -> tuple[str, int]:
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest().upper()
        return digest, int(digest[:16], 16)

    def _reseal_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload.pop("self_sha256", None)
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        payload["self_sha256"] = hashlib.sha256(canonical).hexdigest().upper()
        return payload

    def _perfect_probabilities(self, labels: Any) -> dict[str, Any]:
        import numpy as np

        count = len(labels)
        baseline = np.full((count, 6), 1.0 / 6.0, dtype=np.float64)
        acoustic = np.zeros((count, 6), dtype=np.float64)
        for row, label in enumerate(labels):
            acoustic[row, self.CLASS_ORDER.index(str(label))] = 1.0
        return {
            "class_prior": baseline.copy(),
            "sentence_id": baseline.copy(),
            "acoustic": acoustic,
        }

    def _clustered_bootstrap_arrays(
        self,
    ) -> tuple[Any, dict[str, Any], list[str]]:
        import numpy as np

        clusters = (
            (("A", "D"), ("A", "A"), ("A", "D")),
            (("F", "H", "S"), ("A", "A", "A"), ("F", "F", "S")),
            (("N", "N", "A", "D"), ("N", "N", "N", "N"),
             ("N", "A", "A", "D")),
            (("H",), ("A",), ("H",)),
            (("S", "F"), ("S", "S"), ("S", "F")),
            (("D", "D", "D"), ("A", "A", "A"), ("D", "A", "D")),
            (("A", "F", "H", "N", "S"), ("A", "A", "A", "A", "A"),
             ("A", "F", "A", "N", "S")),
            (("N", "S"), ("N", "N"), ("N", "N")),
            (("F", "F", "H"), ("F", "F", "F"), ("F", "H", "H")),
            (("A", "D", "N", "S"), ("A", "A", "A", "A"),
             ("A", "D", "N", "A")),
        )
        labels: list[str] = []
        actors: list[str] = []
        predictions = {key: [] for key in self.MODEL_KEYS}
        for actor_index, (truth, prior, sentence) in enumerate(clusters):
            labels.extend(truth)
            actors.extend(
                [self.ACTORS_BY_ROLE["final_lockbox"][actor_index]] * len(truth)
            )
            predictions["class_prior"].extend(prior)
            predictions["sentence_id"].extend(sentence)
            predictions["acoustic"].extend(truth)
        probabilities: dict[str, Any] = {}
        for model in self.MODEL_KEYS:
            matrix = np.zeros((len(labels), 6), dtype=np.float64)
            for row, prediction in enumerate(predictions[model]):
                matrix[row, self.CLASS_ORDER.index(prediction)] = 1.0
            probabilities[model] = matrix
        return np.asarray(labels, dtype="<U1"), probabilities, actors

    def _decision_from_probabilities(
        self,
        probabilities: dict[str, Any],
        *,
        sentence_driven_apparent_lift: bool = False,
        eligible_slice_reversal: bool = False,
        eligible_slice_instability: bool = False,
        confidence_abstention_improves: bool = True,
    ) -> tuple[Any, dict[str, bool]]:
        from scripts.emotion_state_phase_b_evaluation import (
            build_decision_evidence,
            calibrate_thresholds,
            evaluate_partition,
            paired_actor_bootstrap,
        )

        labels, _, actors = self._metric_arrays()
        calibration_evidence = self._partition_evidence(
            "calibration",
            labels,
            probabilities=probabilities,
        )
        thresholds = calibrate_thresholds(
            probabilities,
            (1.0, 0.8, 0.6),
            evidence=calibration_evidence,
        )
        final_evidence = self._partition_evidence(
            "final_lockbox",
            labels,
            actor_ids=actors,
            probabilities=probabilities,
        )
        evaluation = evaluate_partition(
            labels,
            probabilities,
            actors,
            thresholds,
            evidence=final_evidence,
        )
        _, seed = self._config_identity()
        bootstrap = paired_actor_bootstrap(
            labels,
            probabilities,
            actors,
            2000,
            seed,
            evidence=final_evidence,
        )
        evidence = build_decision_evidence(
            evaluation,
            bootstrap,
            evidence=final_evidence,
            sentence_driven_apparent_lift=sentence_driven_apparent_lift,
            eligible_slice_reversal=eligible_slice_reversal,
            eligible_slice_instability=eligible_slice_instability,
            confidence_abstention_improves=confidence_abstention_improves,
        )
        validity = {
            "material_valid": True,
            "environment_valid": True,
            "split_valid": True,
            "leakage_free": True,
            "deterministic": True,
            "lockbox_valid": True,
        }
        return evidence, validity

    def _decision_fixture(self) -> tuple[Any, dict[str, bool]]:
        labels, _, _ = self._metric_arrays()
        return self._decision_from_probabilities(
            self._perfect_probabilities(labels)
        )

    def _legacy_frozen_models_pin_exact_estimators_training_state_and_six_class_probabilities(
        self,
    ) -> None:
        import numpy as np
        from sklearn.dummy import DummyClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler

        from scripts.emotion_state_phase_b_evaluation import fit_frozen_models

        features, sentences, labels = self._training_arrays()
        evidence = self._partition_evidence(
            "training_discovery",
            labels,
            features=features,
            sentences=sentences,
            seed=self.MODEL_SEED,
        )
        with warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter("always")
            models = fit_frozen_models(
                features,
                sentences,
                labels,
                self.MODEL_SEED,
                evidence=evidence,
            )
        self.assertEqual(observed, [])
        self.assertEqual(tuple(models), self.MODEL_KEYS)

        prior = models["class_prior"]
        self.assertIs(type(prior), DummyClassifier)
        self.assertEqual(prior.strategy, "prior")
        np.testing.assert_array_equal(
            prior.class_prior_,
            np.asarray([5, 10, 15, 20, 8, 7], dtype=np.float64) / 65.0,
        )

        sentence = models["sentence_id"]
        self.assertIs(type(sentence), Pipeline)
        self.assertEqual(tuple(sentence.named_steps), ("one_hot", "classifier"))
        self.assertIs(type(sentence.named_steps["one_hot"]), OneHotEncoder)
        self.assertEqual(
            sentence.named_steps["one_hot"].handle_unknown,
            "ignore",
        )

        acoustic = models["acoustic"]
        self.assertIs(type(acoustic), Pipeline)
        self.assertEqual(
            tuple(acoustic.named_steps),
            ("standardize", "classifier"),
        )
        self.assertIs(type(acoustic.named_steps["standardize"]), StandardScaler)
        np.testing.assert_allclose(
            acoustic.named_steps["standardize"].mean_,
            features.mean(axis=0),
        )

        for pipeline in (sentence, acoustic):
            classifier = pipeline.named_steps["classifier"]
            self.assertIs(type(classifier), LogisticRegression)
            self.assertEqual(
                {
                    "C": classifier.C,
                    "class_weight": classifier.class_weight,
                    "solver": classifier.solver,
                    "max_iter": classifier.max_iter,
                    "random_state": classifier.random_state,
                    "l1_ratio": classifier.l1_ratio,
                },
                {
                    "C": 1.0,
                    "class_weight": None,
                    "solver": "lbfgs",
                    "max_iter": 10000,
                    "random_state": self.MODEL_SEED,
                    "l1_ratio": 0.0,
                },
            )
        for model in models.values():
            np.testing.assert_array_equal(model.classes_, self.CLASS_ORDER)

        prediction_inputs = features[:7] + 1000.0
        model_inputs = {
            "class_prior": prediction_inputs,
            "sentence_id": np.asarray(
                [["UNSEEN"] for _ in range(7)],
                dtype="<U6",
            ),
            "acoustic": prediction_inputs,
        }
        for key, model in models.items():
            probabilities = model.predict_proba(model_inputs[key])
            self.assertEqual(probabilities.shape, (7, 6))
            self.assertTrue(np.isfinite(probabilities).all())
            np.testing.assert_allclose(
                probabilities.sum(axis=1),
                np.ones(7),
                rtol=0.0,
                atol=1e-12,
            )
        np.testing.assert_allclose(
            prior.predict_proba(prediction_inputs)[0],
            np.asarray([5, 10, 15, 20, 8, 7], dtype=np.float64) / 65.0,
        )
        scores = acoustic.decision_function(features[:7])
        softmax = np.exp(scores - scores.max(axis=1, keepdims=True))
        softmax /= softmax.sum(axis=1, keepdims=True)
        np.testing.assert_allclose(
            acoustic.predict_proba(features[:7]),
            softmax,
            rtol=0.0,
            atol=1e-12,
        )

        deprecated_sentence = Pipeline([
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
            ("classifier", LogisticRegression(
                penalty="l2",
                C=1.0,
                class_weight=None,
                solver="lbfgs",
                max_iter=10000,
                random_state=self.MODEL_SEED,
            )),
        ])
        deprecated_acoustic = Pipeline([
            ("standardize", StandardScaler()),
            ("classifier", LogisticRegression(
                penalty="l2",
                C=1.0,
                class_weight=None,
                solver="lbfgs",
                max_iter=10000,
                random_state=self.MODEL_SEED,
            )),
        ])
        with warnings.catch_warnings(record=True) as deprecated_warnings:
            warnings.simplefilter("always")
            deprecated_sentence.fit(sentences.reshape(-1, 1), labels)
            deprecated_acoustic.fit(features, labels)
        self.assertEqual(len(deprecated_warnings), 2)
        for replacement, deprecated, inputs in (
            (sentence, deprecated_sentence, sentences.reshape(-1, 1)),
            (acoustic, deprecated_acoustic, features),
        ):
            np.testing.assert_array_equal(
                replacement.named_steps["classifier"].coef_,
                deprecated.named_steps["classifier"].coef_,
            )
            np.testing.assert_array_equal(
                replacement.predict_proba(inputs),
                deprecated.predict_proba(inputs),
            )

    def _legacy_fit_is_training_only_and_partition_roles_fail_closed(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            calibrate_thresholds,
            evaluate_partition,
            fit_frozen_models,
            paired_actor_bootstrap,
        )

        features, sentences, labels = self._training_arrays()
        wrong_fit_evidence = self._partition_evidence(
            "final_lockbox",
            labels,
            probabilities=self._perfect_probabilities(labels),
            seed=1,
        )
        with self.assertRaisesRegex(ValueError, "training_discovery"):
            fit_frozen_models(
                features,
                sentences,
                labels,
                1,
                evidence=wrong_fit_evidence,
            )
        with self.assertRaises(TypeError):
            fit_frozen_models(features, sentences, labels, 1)

        probabilities = self._calibration_probabilities()
        calibration_labels = np.asarray(self.CLASS_ORDER, dtype="<U1")
        wrong_calibration_evidence = self._partition_evidence(
            "final_lockbox",
            calibration_labels,
            probabilities=probabilities,
        )
        with self.assertRaisesRegex(ValueError, "calibration"):
            calibrate_thresholds(
                probabilities,
                (1.0, 0.8, 0.6),
                evidence=wrong_calibration_evidence,
            )
        labels_for_metrics, metric_probabilities, actors = self._metric_arrays(
            role="balanced_diagnostic",
        )
        calibration_evidence = self._partition_evidence(
            "calibration",
            labels_for_metrics,
            probabilities=metric_probabilities,
        )
        thresholds = calibrate_thresholds(
            metric_probabilities,
            (1.0, 0.8, 0.6),
            evidence=calibration_evidence,
        )
        wrong_evaluation_evidence = self._partition_evidence(
            "training_discovery",
            labels_for_metrics,
            features=np.zeros(
                (len(labels_for_metrics), 17),
                dtype=np.float64,
            ),
            sentences=np.asarray(
                [f"S{index % 12:02d}" for index in range(len(labels_for_metrics))],
                dtype="<U3",
            ),
        )
        with self.assertRaisesRegex(ValueError, "partition role"):
            evaluate_partition(
                labels_for_metrics,
                metric_probabilities,
                actors,
                thresholds,
                evidence=wrong_evaluation_evidence,
            )
        _, seed = self._config_identity()
        diagnostic_evidence = self._partition_evidence(
            "balanced_diagnostic",
            labels_for_metrics,
            actor_ids=actors,
            probabilities=metric_probabilities,
        )
        with self.assertRaisesRegex(ValueError, "final_lockbox"):
            paired_actor_bootstrap(
                labels_for_metrics,
                metric_probabilities,
                actors,
                2000,
                seed,
                evidence=diagnostic_evidence,
            )

    def _legacy_calibration_uses_only_calibration_confidences_and_retains_ties(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import calibrate_thresholds

        probabilities = self._calibration_probabilities()
        evidence = self._partition_evidence(
            "calibration",
            np.asarray(self.CLASS_ORDER, dtype="<U1"),
            probabilities=probabilities,
        )
        result = calibrate_thresholds(
            probabilities,
            (1.0, 0.8, 0.6),
            evidence=evidence,
        )
        self.assertEqual(result["partition_role"], "calibration")
        self.assertEqual(tuple(result["class_order"]), self.CLASS_ORDER)
        self.assertEqual(tuple(result["models"]), self.MODEL_KEYS)
        for model in self.MODEL_KEYS:
            cells = result["models"][model]
            self.assertEqual(tuple(cells), (1.0, 0.8, 0.6))
            self.assertEqual(cells[1.0], {
                "threshold": 0.2,
                "achieved_coverage": 1.0,
            })
            self.assertEqual(cells[0.8], {
                "threshold": 0.3,
                "achieved_coverage": 5.0 / 6.0,
            })
            self.assertEqual(cells[0.6], {
                "threshold": 0.4,
                "achieved_coverage": 4.0 / 6.0,
            })

    def _legacy_hand_calculated_metrics_ece_and_retained_coverage(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            calibrate_thresholds,
            evaluate_partition,
        )
        labels, probabilities, actors = self._metric_arrays(
            role="balanced_diagnostic",
        )
        calibration_evidence = self._partition_evidence(
            "calibration",
            labels,
            probabilities=probabilities,
        )
        thresholds = calibrate_thresholds(
            probabilities,
            (1.0, 0.8, 0.6),
            evidence=calibration_evidence,
        )
        diagnostic_evidence = self._partition_evidence(
            "balanced_diagnostic",
            labels,
            actor_ids=actors,
            probabilities=probabilities,
        )
        result = evaluate_partition(
            labels,
            probabilities,
            actors,
            thresholds,
            evidence=diagnostic_evidence,
        )
        self.assertFalse(result["final_decision_eligible"])
        model = result["models"]["acoustic"]
        self.assertFalse(model["suppressed"])
        self.assertEqual(model["unique_actor_count"], 10)
        self.assertEqual(model["case_count"], 60)
        self.assertAlmostEqual(model["macro_f1"], 7.0 / 9.0, places=15)
        self.assertAlmostEqual(
            model["balanced_accuracy"],
            5.0 / 6.0,
            places=15,
        )
        expected_recalls = {
            "A": 1.0,
            "D": 0.0,
            "F": 1.0,
            "H": 1.0,
            "N": 1.0,
            "S": 1.0,
        }
        for label, expected in expected_recalls.items():
            cell = model["per_class_recall"][label]
            self.assertFalse(cell["suppressed"])
            self.assertEqual(cell["unique_actor_count"], 10)
            self.assertEqual(cell["case_count"], 10)
            self.assertAlmostEqual(cell["recall"], expected, places=15)

        # Row-summed errors are .11, .715, .44, .44, .62, and .44.
        self.assertAlmostEqual(
            model["multiclass_brier"],
            2.765 / 6.0,
            places=15,
        )
        expected_log_loss = -sum(
            math.log(value)
            for value in (0.70, 0.25, 0.40, 0.40, 0.30, 0.40)
        ) / 6.0
        self.assertAlmostEqual(model["log_loss"], expected_log_loss, places=15)
        # ECE: 2/6*|.5-.3| + 3/6*|1-.4| + 1/6*|1-.7|.
        self.assertAlmostEqual(model["ece_10_bin"], 5.0 / 12.0, places=15)
        self.assertEqual(model["retained"][1.0]["coverage"], 1.0)
        self.assertEqual(model["retained"][0.8]["coverage"], 1.0)
        self.assertAlmostEqual(
            model["retained"][0.6]["coverage"],
            2.0 / 3.0,
            places=15,
        )
        self.assertAlmostEqual(
            model["retained"][0.6]["retained_macro_f1"],
            2.0 / 3.0,
            places=15,
        )

    def _legacy_sparse_cells_are_suppressed_not_zero(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            calibrate_thresholds,
            evaluate_partition,
        )
        labels, probabilities, actors = self._metric_arrays(
            actor_count=9,
            role="balanced_diagnostic",
        )
        calibration_evidence = self._partition_evidence(
            "calibration",
            labels,
            probabilities=probabilities,
        )
        thresholds = calibrate_thresholds(
            probabilities,
            (1.0, 0.8, 0.6),
            evidence=calibration_evidence,
        )
        diagnostic_evidence = self._partition_evidence(
            "balanced_diagnostic",
            labels,
            actor_ids=actors,
            probabilities=probabilities,
        )
        result = evaluate_partition(
            labels,
            probabilities,
            actors,
            thresholds,
            evidence=diagnostic_evidence,
        )
        for model in result["models"].values():
            self.assertTrue(model["suppressed"])
            self.assertIsNone(model["macro_f1"])
            self.assertIsNone(model["balanced_accuracy"])
            self.assertIsNone(model["multiclass_brier"])
            for cell in model["per_class_recall"].values():
                self.assertTrue(cell["suppressed"])
                self.assertIsNone(cell["recall"])
            for cell in model["retained"].values():
                self.assertTrue(cell["suppressed"])
                self.assertIsNone(cell["retained_macro_f1"])

    def _legacy_probability_threshold_and_class_order_schemas_fail_closed(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            calibrate_thresholds,
            evaluate_partition,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_calibration_result,
        )

        probabilities = self._calibration_probabilities()
        mutations: list[tuple[str, Any]] = []
        missing = dict(probabilities)
        missing.pop("sentence_id")
        mutations.append(("model keys", missing))
        extra = dict(probabilities)
        extra["extra"] = extra["acoustic"]
        mutations.append(("model keys", extra))
        non_finite = {key: value.copy() for key, value in probabilities.items()}
        non_finite["acoustic"][0, 0] = np.nan
        mutations.append(("finite", non_finite))
        wrong_sum = {key: value.copy() for key, value in probabilities.items()}
        wrong_sum["acoustic"][0, 0] += 0.1
        mutations.append(("sum", wrong_sum))
        wrong_shape = {key: value.copy() for key, value in probabilities.items()}
        wrong_shape["acoustic"] = wrong_shape["acoustic"][:, :5]
        mutations.append(("shape", wrong_shape))
        calibration_labels = np.asarray(self.CLASS_ORDER, dtype="<U1")
        for pattern, mutated in mutations:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(ValueError, pattern):
                    evidence = self._partition_evidence(
                        "calibration",
                        calibration_labels,
                        probabilities=mutated,
                    )
                    calibrate_thresholds(
                        mutated,
                        (1.0, 0.8, 0.6),
                        evidence=evidence,
                    )
        valid_evidence = self._partition_evidence(
            "calibration",
            calibration_labels,
            probabilities=probabilities,
        )
        with self.assertRaisesRegex(ValueError, "targets"):
            calibrate_thresholds(
                probabilities,
                (1.0, 0.7, 0.6),
                evidence=valid_evidence,
            )

        labels, metric_probabilities, actors = self._metric_arrays(
            role="balanced_diagnostic",
        )
        metric_calibration_evidence = self._partition_evidence(
            "calibration",
            labels,
            probabilities=metric_probabilities,
        )
        thresholds = calibrate_thresholds(
            metric_probabilities,
            (1.0, 0.8, 0.6),
            evidence=metric_calibration_evidence,
        )
        diagnostic_evidence = self._partition_evidence(
            "balanced_diagnostic",
            labels,
            actor_ids=actors,
            probabilities=metric_probabilities,
        )
        malformed = thresholds.to_payload()
        malformed["models"]["acoustic"][0.8]["unexpected"] = 1.0
        self._reseal_payload(malformed)
        with self.assertRaisesRegex(ValueError, "threshold"):
            validate_calibration_result(malformed)
        with self.assertRaisesRegex(ValueError, "actor IDs"):
            evaluate_partition(
                labels,
                metric_probabilities,
                actors[:-1],
                thresholds,
                evidence=diagnostic_evidence,
            )
        invalid_actors = list(actors)
        invalid_actors[0] = ""
        with self.assertRaisesRegex(ValueError, "actor IDs"):
            evaluate_partition(
                labels,
                metric_probabilities,
                invalid_actors,
                thresholds,
                evidence=diagnostic_evidence,
            )

    def _legacy_partition_evidence_binds_assignment_contracts_and_exact_inputs(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            PartitionEvidence,
            ValidatedSplitAssignment,
            calibrate_thresholds,
            fit_frozen_models,
        )

        with self.assertRaisesRegex(TypeError, "minted"):
            ValidatedSplitAssignment()
        with self.assertRaisesRegex(TypeError, "minted"):
            PartitionEvidence()

        features, sentences, labels = self._training_arrays()
        training_evidence = self._partition_evidence(
            "training_discovery",
            labels,
            features=features,
            sentences=sentences,
        )
        changed_features = features.copy()
        changed_features[0, 0] += 0.001
        with self.assertRaisesRegex(ValueError, "commitment"):
            fit_frozen_models(
                changed_features,
                sentences,
                labels,
                self.MODEL_SEED,
                evidence=training_evidence,
            )
        with self.assertRaisesRegex(ValueError, "assignment membership"):
            self._partition_evidence(
                "training_discovery",
                labels,
                features=features,
                sentences=sentences,
                assignment_role="calibration",
            )

        probabilities = self._calibration_probabilities()
        calibration_labels = np.asarray(self.CLASS_ORDER, dtype="<U1")
        calibration_evidence = self._partition_evidence(
            "calibration",
            calibration_labels,
            probabilities=probabilities,
        )
        changed_probabilities = {
            key: value.copy() for key, value in probabilities.items()
        }
        changed_probabilities["acoustic"][0] = np.asarray(
            [0.25, 0.15, 0.15, 0.15, 0.15, 0.15],
            dtype=np.float64,
        )
        with self.assertRaisesRegex(ValueError, "probability commitment"):
            calibrate_thresholds(
                changed_probabilities,
                (1.0, 0.8, 0.6),
                evidence=calibration_evidence,
            )

    def _legacy_diagnostic_relabel_and_equal_count_cross_run_mix_fail_closed(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            build_decision_evidence,
            calibrate_thresholds,
            evaluate_partition,
            paired_actor_bootstrap,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_evaluation_result,
        )

        labels, _, final_actors = self._metric_arrays()
        _, _, diagnostic_actors = self._metric_arrays(
            role="balanced_diagnostic",
        )
        probabilities_a = self._perfect_probabilities(labels)
        probabilities_b = {
            key: value.copy() for key, value in probabilities_a.items()
        }
        probabilities_b["acoustic"][0] = np.asarray(
            [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            dtype=np.float64,
        )
        calibration_evidence = self._partition_evidence(
            "calibration",
            labels,
            probabilities=probabilities_a,
        )
        thresholds = calibrate_thresholds(
            probabilities_a,
            (1.0, 0.8, 0.6),
            evidence=calibration_evidence,
        )
        diagnostic_evidence = self._partition_evidence(
            "balanced_diagnostic",
            labels,
            actor_ids=diagnostic_actors,
            probabilities=probabilities_a,
        )
        diagnostic = evaluate_partition(
            labels,
            probabilities_a,
            diagnostic_actors,
            thresholds,
            evidence=diagnostic_evidence,
        )
        promoted = diagnostic.to_payload()
        promoted["partition_role"] = "final_lockbox"
        promoted["final_decision_eligible"] = True
        self._reseal_payload(promoted)
        with self.assertRaisesRegex(ValueError, "provenance"):
            validate_evaluation_result(promoted, expected_role="final_lockbox")

        final_evidence_a = self._partition_evidence(
            "final_lockbox",
            labels,
            actor_ids=final_actors,
            probabilities=probabilities_a,
        )
        final_evaluation_a = evaluate_partition(
            labels,
            probabilities_a,
            final_actors,
            thresholds,
            evidence=final_evidence_a,
        )
        final_evidence_b = self._partition_evidence(
            "final_lockbox",
            labels,
            actor_ids=final_actors,
            probabilities=probabilities_b,
        )
        _, seed = self._config_identity()
        bootstrap_b = paired_actor_bootstrap(
            labels,
            probabilities_b,
            final_actors,
            2000,
            seed,
            evidence=final_evidence_b,
        )
        with self.assertRaisesRegex(ValueError, "provenance commitments"):
            build_decision_evidence(
                final_evaluation_a,
                bootstrap_b,
                evidence=final_evidence_a,
                sentence_driven_apparent_lift=False,
                eligible_slice_reversal=False,
                eligible_slice_instability=False,
                confidence_abstention_improves=True,
            )

    def _legacy_metric_domains_count_relationships_and_skewed_percentile_are_strict(
        self,
    ) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_bootstrap_result,
            validate_decision_inputs,
            validate_evaluation_result,
        )

        decision, validity = self._decision_fixture()
        base = decision.to_payload()
        domain_mutations = (
            ("macro_f1", "models", "acoustic", "macro_f1", 1.01),
            ("balanced_accuracy", "models", "acoustic", "balanced_accuracy", -0.01),
            ("multiclass_brier", "models", "acoustic", "multiclass_brier", 2.01),
            ("log_loss", "models", "acoustic", "log_loss", -0.01),
            ("ece_10_bin", "models", "acoustic", "ece_10_bin", -0.01),
        )
        for pattern, root, model, key, value in domain_mutations:
            mutated = deepcopy(base)
            mutated[root][model][key] = value
            self._reseal_payload(mutated)
            with self.subTest(metric=key):
                with self.assertRaisesRegex(ValueError, pattern):
                    validate_decision_inputs(mutated, validity)

        count_mutation = deepcopy(base)
        count_mutation["models"]["acoustic"]["unique_actor_count"] = (
            count_mutation["models"]["acoustic"]["case_count"] + 1
        )
        self._reseal_payload(count_mutation)
        with self.assertRaisesRegex(ValueError, "actors.*cases"):
            validate_decision_inputs(count_mutation, validity)

        recall_mutation = deepcopy(base)
        recall_mutation["models"]["acoustic"]["per_class_recall"]["A"][
            "recall"
        ] = 1.01
        self._reseal_payload(recall_mutation)
        with self.assertRaisesRegex(ValueError, "per-class recall"):
            validate_decision_inputs(recall_mutation, validity)

        retained_mutation = deepcopy(base)
        retained_mutation["models"]["acoustic"]["retained"][0.8][
            "retained_macro_f1"
        ] = 1.01
        self._reseal_payload(retained_mutation)
        with self.assertRaisesRegex(ValueError, "retained macro-F1"):
            validate_decision_inputs(retained_mutation, validity)

        retained_count_mutation = deepcopy(base)
        retained_count_mutation["models"]["acoustic"]["retained"][0.8][
            "case_count"
        ] = base["models"]["acoustic"]["case_count"] + 1
        self._reseal_payload(retained_count_mutation)
        with self.assertRaisesRegex(ValueError, "retained.*total"):
            validate_decision_inputs(retained_count_mutation, validity)

        cross_model_count_mutation = deepcopy(base)
        cross_model_count_mutation["models"]["sentence_id"]["case_count"] += 1
        self._reseal_payload(cross_model_count_mutation)
        with self.assertRaisesRegex(ValueError, "cross-model"):
            validate_decision_inputs(cross_model_count_mutation, validity)

        lift_mutation = deepcopy(base)
        lift_mutation["paired_macro_f1_lift"]["class_prior"][
            "lower_95"
        ] = -1.01
        self._reseal_payload(lift_mutation)
        with self.assertRaisesRegex(ValueError, "lift"):
            validate_decision_inputs(lift_mutation, validity)

        zero_nested_counts = {
            "schema_id": "emotion-state-phase-b-evaluation-v1",
            "partition_role": "final_lockbox",
            "class_order": list(self.CLASS_ORDER),
            "models": deepcopy(base["models"]),
            "final_decision_eligible": True,
            "provenance": deepcopy(base["provenance"]),
        }
        recall_cell = zero_nested_counts["models"]["acoustic"][
            "per_class_recall"
        ]["A"]
        recall_cell.update({
            "suppressed": True,
            "unique_actor_count": 0,
            "case_count": 0,
            "recall": None,
        })
        retained_cell = zero_nested_counts["models"]["acoustic"]["retained"][0.6]
        retained_cell.update({
            "coverage": 0.0,
            "suppressed": True,
            "unique_actor_count": 0,
            "case_count": 0,
            "retained_macro_f1": None,
        })
        self._reseal_payload(zero_nested_counts)
        validate_evaluation_result(
            zero_nested_counts,
            expected_role="final_lockbox",
        )

        skewed_provenance = deepcopy(base["provenance"])
        skewed_provenance["case_count"] = 20
        skewed_provenance["unique_actor_count"] = 10
        self._reseal_payload(skewed_provenance)
        bootstrap = {
            "schema_id": "emotion-state-phase-b-bootstrap-v1",
            "partition_role": "final_lockbox",
            "class_order": list(self.CLASS_ORDER),
            "resamples": 2000,
            "seed": self._config_identity()[1],
            "configuration_sha256": self._config_identity()[0],
            "unique_actor_count": 10,
            "case_count": 20,
            "paired_macro_f1_lift": {
                "class_prior": {
                    "point_estimate": 0.9,
                    "lower_95": 0.1,
                    "upper_95": 0.8,
                },
                "sentence_id": {
                    "point_estimate": -0.9,
                    "lower_95": -0.8,
                    "upper_95": -0.1,
                },
            },
            "provenance": skewed_provenance,
        }
        self._reseal_payload(bootstrap)
        validate_bootstrap_result(bootstrap)

    def _legacy_bootstrap_is_exactly_2000_paired_actor_cluster_draws_and_aggregate_only(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_evaluation import paired_actor_bootstrap

        labels, probabilities, actors = self._clustered_bootstrap_arrays()
        _, seed = self._config_identity()
        evidence = self._partition_evidence(
            "final_lockbox",
            labels,
            actor_ids=actors,
            probabilities=probabilities,
        )
        first = paired_actor_bootstrap(
            labels,
            probabilities,
            actors,
            2000,
            seed,
            evidence=evidence,
        )
        second = paired_actor_bootstrap(
            labels,
            probabilities,
            actors,
            2000,
            seed,
            evidence=evidence,
        )
        canonical = lambda value: json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(
            canonical(first.to_payload()),
            canonical(second.to_payload()),
        )
        self.assertEqual(first["resamples"], 2000)
        self.assertEqual(first["partition_role"], "final_lockbox")
        self.assertEqual(
            first["paired_macro_f1_lift"]["class_prior"],
            {
                "point_estimate": 0.7326839826839826,
                "lower_95": 0.6396058006535947,
                "upper_95": 0.8981598822324628,
            },
        )
        self.assertEqual(
            first["paired_macro_f1_lift"]["sentence_id"],
            {
                "point_estimate": 0.2504689754689755,
                "lower_95": 0.1520461945461947,
                "upper_95": 0.37701141451141434,
            },
        )
        serialized_keys = set(first)
        self.assertNotIn("draws", serialized_keys)
        self.assertNotIn("indexes", serialized_keys)
        self.assertNotIn("actor_ids", serialized_keys)
        self.assertNotIn("samples", serialized_keys)
        with self.assertRaisesRegex(ValueError, "2,000"):
            paired_actor_bootstrap(
                labels,
                probabilities,
                actors,
                1999,
                seed,
                evidence=evidence,
            )
        with self.assertRaisesRegex(ValueError, "configuration"):
            paired_actor_bootstrap(
                labels,
                probabilities,
                actors,
                2000,
                seed + 1,
                evidence=evidence,
            )

    def _legacy_decision_precedence_and_every_clause_are_mutation_tested(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import decide_experiment

        evidence, validity = self._decision_fixture()
        self.assertEqual(
            decide_experiment(evidence, validity),
            "keep_for_research_only",
        )

        for key in validity:
            mutated = dict(validity)
            mutated[key] = False
            with self.subTest(discard_validity=key):
                self.assertEqual(
                    decide_experiment(evidence, mutated),
                    "discard",
                )

        labels, _, _ = self._metric_arrays()
        perfect = self._perfect_probabilities(labels)
        sentence_driven, _ = self._decision_from_probabilities(
            perfect,
            sentence_driven_apparent_lift=True,
        )
        self.assertEqual(
            decide_experiment(sentence_driven, validity),
            "discard",
        )

        uniform = perfect["class_prior"].copy()
        failed_baseline, _ = self._decision_from_probabilities({
            key: uniform.copy() for key in self.MODEL_KEYS
        })
        self.assertEqual(
            decide_experiment(failed_baseline, validity),
            "discard",
        )

        rare_lift = {key: uniform.copy() for key in self.MODEL_KEYS}
        for row, label in enumerate(labels[:6]):
            rare_lift["acoustic"][row] = 0.0
            rare_lift["acoustic"][
                row,
                self.CLASS_ORDER.index(str(label)),
            ] = 1.0
        interval_crossing, _ = self._decision_from_probabilities(rare_lift)
        self.assertEqual(
            decide_experiment(interval_crossing, validity),
            "revise",
        )

        worse_ece_probabilities = {
            "class_prior": uniform.copy(),
            "sentence_id": uniform.copy(),
            "acoustic": np.full((len(labels), 6), 0.02, dtype=np.float64),
        }
        for row, label in enumerate(labels):
            worse_ece_probabilities["acoustic"][
                row,
                self.CLASS_ORDER.index(str(label)),
            ] = 0.90
        worse_ece, _ = self._decision_from_probabilities(
            worse_ece_probabilities
        )
        self.assertEqual(decide_experiment(worse_ece, validity), "revise")

        zero_recall_probabilities = {
            key: value.copy() for key, value in perfect.items()
        }
        for row, label in enumerate(labels):
            if label == "D":
                zero_recall_probabilities["acoustic"][row] = 0.0
                zero_recall_probabilities["acoustic"][row, 0] = 1.0
        zero_recall, _ = self._decision_from_probabilities(
            zero_recall_probabilities
        )
        self.assertEqual(decide_experiment(zero_recall, validity), "revise")

        for key in (
            "eligible_slice_reversal",
            "eligible_slice_instability",
        ):
            mutated, _ = self._decision_from_probabilities(
                perfect,
                **{key: True},
            )
            with self.subTest(revise_slice=key):
                self.assertEqual(
                    decide_experiment(mutated, validity),
                    "revise",
                )

        ineffective, _ = self._decision_from_probabilities(
            perfect,
            confidence_abstention_improves=False,
        )
        self.assertEqual(decide_experiment(ineffective, validity), "revise")

    def _legacy_decision_rejects_diagnostic_fabricated_or_nonfinite_evidence(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import decide_experiment
        from scripts.validate_emotion_state_002_phase_b import (
            validate_decision_inputs,
        )

        evidence, validity = self._decision_fixture()
        payload = evidence.to_payload()
        with self.assertRaisesRegex(ValueError, "bound decision evidence"):
            decide_experiment(payload, validity)

        mutations: list[tuple[str, dict[str, Any], dict[str, bool]]] = []
        missing_metric = deepcopy(payload)
        missing_metric.pop("eligible_slice_instability")
        self._reseal_payload(missing_metric)
        mutations.append(("metric keys", missing_metric, validity))
        extra_metric = deepcopy(payload)
        extra_metric["runtime_recommendation"] = "deploy"
        self._reseal_payload(extra_metric)
        mutations.append(("metric keys", extra_metric, validity))
        nonfinite = deepcopy(payload)
        nonfinite["models"]["acoustic"]["macro_f1"] = np.nan
        nonfinite["self_sha256"] = "0" * 64
        mutations.append(("finite", nonfinite, validity))
        fabricated = deepcopy(payload)
        fabricated["models"]["acoustic"]["macro_f1"] -= 0.01
        self._reseal_payload(fabricated)
        mutations.append(("point estimate", fabricated, validity))
        missing_validity = dict(validity)
        missing_validity.pop("split_valid")
        mutations.append(("validity keys", payload, missing_validity))
        extra_validity = dict(validity)
        extra_validity["runtime_valid"] = True
        mutations.append(("validity keys", payload, extra_validity))
        for pattern, metric_input, validity_input in mutations:
            with self.subTest(pattern=pattern):
                with self.assertRaisesRegex(ValueError, pattern):
                    validate_decision_inputs(metric_input, validity_input)

    def test_rereview_cross_calibration_lineage_mixing_rejects(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import evaluate_partition

        run_a = self._semantic_artifacts(0)
        run_b = self._semantic_artifacts(1)
        with self.assertRaisesRegex(ValueError, "calibration lineage"):
            evaluate_partition(
                run_a["final_probabilities"],
                run_b["calibration"],
            )
        evaluation = run_a["evaluation"].to_payload()
        self.assertEqual(
            evaluation["calibration_evidence_mint_sha256"],
            run_a["calibration"].mint_sha256,
        )
        self.assertEqual(
            evaluation["calibration_evidence"]["provenance"],
            run_a["calibration_partition"].to_payload(),
        )
        self.assertEqual(
            run_a["decision"]["calibration_evidence_mint_sha256"],
            run_a["calibration"].mint_sha256,
        )

    def test_rereview_bound_payload_mutation_and_reseal_cannot_change_decision(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            BootstrapEvidence,
            CalibrationEvidence,
            DecisionEvidence,
            EvaluationEvidence,
            PartitionEvidence,
            SliceAnalysisEvidence,
            ValidatedSplitAssignment,
            decide_experiment,
        )

        decision = self._semantic_artifacts()["decision"]
        validity = {
            "material_valid": True,
            "environment_valid": True,
            "split_valid": True,
            "leakage_free": True,
            "deterministic": True,
            "lockbox_valid": True,
        }
        before = decide_experiment(decision, validity)
        detached = decision.to_payload()
        detached["confidence_abstention_improves"] = not detached[
            "confidence_abstention_improves"
        ]
        self._reseal_payload(detached)
        self.assertNotEqual(detached, decision.to_payload())
        self.assertEqual(decide_experiment(decision, validity), before)
        self.assertNotEqual(decision.mint_sha256, decision["self_sha256"])
        nested = decision["models"]
        nested["acoustic"]["macro_f1"] = 0.0
        self.assertNotEqual(nested, decision["models"])
        with self.assertRaises(AttributeError):
            _ = decision._payload
        with self.assertRaises(AttributeError):
            decision._payload = detached
        with self.assertRaises(AttributeError):
            decision._mint_digest = "0" * 64
        with self.assertRaisesRegex(TypeError, "minted"):
            DecisionEvidence()
        for evidence_type in (
            ValidatedSplitAssignment,
            PartitionEvidence,
            CalibrationEvidence,
            EvaluationEvidence,
            BootstrapEvidence,
            SliceAnalysisEvidence,
        ):
            with self.subTest(evidence_type=evidence_type.__name__):
                with self.assertRaisesRegex(TypeError, "minted"):
                    evidence_type()

    def test_rereview_class_and_retained_relationships_reject(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_evaluation_result,
        )

        base = self._semantic_artifacts()["evaluation"].to_payload()
        class_sum = deepcopy(base)
        class_sum["models"]["acoustic"]["per_class_recall"]["A"][
            "case_count"
        ] += 1
        self._reseal_payload(class_sum)
        with self.assertRaisesRegex(ValueError, "class cases"):
            validate_evaluation_result(class_sum, expected_role="final_lockbox")

        actor_overflow = deepcopy(base)
        actor_overflow["models"]["acoustic"]["per_class_recall"]["A"][
            "unique_actor_count"
        ] = actor_overflow["models"]["acoustic"]["unique_actor_count"] + 1
        self._reseal_payload(actor_overflow)
        with self.assertRaisesRegex(ValueError, "class actors"):
            validate_evaluation_result(
                actor_overflow,
                expected_role="final_lockbox",
            )

        coverage = deepcopy(base)
        coverage["models"]["acoustic"]["retained"]["0.8"]["coverage"] = 0.5
        self._reseal_payload(coverage)
        with self.assertRaisesRegex(ValueError, "coverage.*case"):
            validate_evaluation_result(coverage, expected_role="final_lockbox")

        zero = deepcopy(base)
        zero_cell = zero["models"]["acoustic"]["retained"]["0.6"]
        zero_cell.update({
            "coverage": 0.0,
            "suppressed": False,
            "unique_actor_count": 1,
            "case_count": 0,
            "retained_macro_f1": 0.5,
        })
        self._reseal_payload(zero)
        with self.assertRaisesRegex(ValueError, "zero retained"):
            validate_evaluation_result(zero, expected_role="final_lockbox")

        threshold = deepcopy(base)
        threshold_cell = threshold["models"]["acoustic"]["retained"]["0.8"]
        threshold_cell["threshold"] = (
            threshold_cell["threshold"] - 0.01
            if threshold_cell["threshold"] >= 0.01
            else threshold_cell["threshold"] + 0.01
        )
        self._reseal_payload(threshold)
        with self.assertRaisesRegex(ValueError, "bound calibration"):
            validate_evaluation_result(
                threshold,
                expected_role="final_lockbox",
            )

        achieved = deepcopy(base)
        achieved["models"]["acoustic"]["retained"]["0.8"][
            "calibration_achieved_coverage"
        ] = 0.5
        self._reseal_payload(achieved)
        with self.assertRaisesRegex(ValueError, "bound calibration"):
            validate_evaluation_result(
                achieved,
                expected_role="final_lockbox",
            )

    def test_rereview_non_authoritative_rows_and_probabilities_reject(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import calibrate_thresholds

        records = self.RECORDS_BY_ROLE["calibration"]
        labels = np.asarray([record.label for record in records], dtype="<U1")
        wrong_labels = labels.copy()
        wrong_labels[0] = next(
            label for label in self.CLASS_ORDER if label != wrong_labels[0]
        )
        probabilities = self._calibration_probabilities()
        with self.assertRaisesRegex(ValueError, "authoritative row"):
            self._authoritative_partition(
                "calibration",
                row_ids=[
                    f"fabricated-{index}"
                    for index in range(len(records))
                ],
            )
        with self.assertRaisesRegex(ValueError, "authoritative label"):
            self._authoritative_partition(
                "calibration",
                labels=wrong_labels,
            )
        with self.assertRaisesRegex(TypeError, "ProbabilityEvidence"):
            calibrate_thresholds(
                probabilities,
                (1.0, 0.8, 0.6),
            )

    def test_rereview_bare_string_row_ids_reject(self) -> None:
        with self.assertRaisesRegex(ValueError, "row IDs.*sequence"):
            self._authoritative_partition(
                "calibration",
                row_ids="x" * len(self.RECORDS_BY_ROLE["calibration"]),
            )

    def test_rereview_decision_flags_cannot_be_caller_asserted(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            build_decision_evidence,
            mint_slice_analysis,
        )

        artifacts = self._semantic_artifacts()
        with self.assertRaises(TypeError):
            build_decision_evidence(
                artifacts["evaluation"],
                artifacts["bootstrap"],
                artifacts["slice_analysis"],
                sentence_driven_apparent_lift=False,
                eligible_slice_reversal=False,
                eligible_slice_instability=False,
                confidence_abstention_improves=True,
            )
        with self.assertRaisesRegex(ValueError, "slice contributors"):
            mint_slice_analysis(
                artifacts["final_probabilities"],
                artifacts["evaluation"],
                {
                    "caller_flags": {
                        "eligible_slice_reversal": False,
                        "eligible_slice_instability": False,
                    },
                },
            )
        decision = artifacts["decision"].to_payload()
        models = decision["models"]
        lifts = decision["paired_macro_f1_lift"]
        self.assertEqual(
            decision["sentence_driven_apparent_lift"],
            (
                models["sentence_id"]["macro_f1"]
                > models["class_prior"]["macro_f1"]
                and lifts["sentence_id"]["point_estimate"] <= 0.0
            ),
        )
        acoustic = models["acoustic"]
        candidates = [
            acoustic["retained"][key]
            for key in ("0.8", "0.6")
            if (
                not acoustic["retained"][key]["suppressed"]
                and acoustic["retained"][key]["coverage"] < 1.0
            )
        ]
        expected_confidence = (
            bool(candidates)
            and any(
                cell["retained_macro_f1"] > acoustic["macro_f1"]
                for cell in candidates
            )
            and all(
                cell["retained_macro_f1"] >= acoustic["macro_f1"]
                for cell in candidates
            )
        )
        self.assertEqual(
            decision["confidence_abstention_improves"],
            expected_confidence,
        )
        self.assertEqual(
            decision["eligible_slice_reversal"],
            artifacts["slice_analysis"]["eligible_slice_reversal"],
        )
        self.assertEqual(
            decision["eligible_slice_instability"],
            artifacts["slice_analysis"]["eligible_slice_instability"],
        )

    def test_authoritative_fitted_and_probability_evidence_are_bound(
        self,
    ) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            FittedModelEvidence,
            ProbabilityEvidence,
            _artifact_links,
            build_models,
            predict_probabilities,
        )

        artifacts = self._semantic_artifacts()
        fitted = artifacts["fitted"]
        payload = fitted.to_payload()
        self.assertEqual(payload["training_class_counts"], {
            "A": 84,
            "D": 77,
            "F": 84,
            "H": 78,
            "N": 86,
            "S": 78,
        })
        self.assertEqual(payload["model_order"], list(self.MODEL_KEYS))
        self.assertEqual(payload["class_order"], list(self.CLASS_ORDER))
        self.assertEqual(
            payload["training_evidence_mint_sha256"],
            artifacts["training"].mint_sha256,
        )
        probability_payload = artifacts["final_probabilities"].to_payload()
        self.assertEqual(
            probability_payload["fitted_model_evidence_mint_sha256"],
            fitted.mint_sha256,
        )
        self.assertNotIn("probabilities", probability_payload)
        with self.assertRaisesRegex(TypeError, "minted"):
            FittedModelEvidence()
        with self.assertRaisesRegex(TypeError, "minted"):
            ProbabilityEvidence()
        with self.assertRaises(AttributeError):
            fitted._model_state_sha256 = "0" * 64

        mutation_artifacts = self._semantic_artifacts(2)
        mutable_state = _artifact_links(mutation_artifacts["fitted"])[0]
        acoustic_classifier = dict(mutable_state.models)["acoustic"].named_steps[
            "classifier"
        ]
        acoustic_classifier.set_params(C=2.0)
        try:
            with self.assertRaisesRegex(ValueError, "model state"):
                predict_probabilities(
                    mutation_artifacts["fitted"],
                    mutation_artifacts["final_partition"],
                )
        finally:
            acoustic_classifier.set_params(C=1.0)

        features, sentences, labels = self._training_arrays()
        replacement = build_models(self.MODEL_SEED)
        deprecated = build_models(self.MODEL_SEED)
        for key in ("sentence_id", "acoustic"):
            classifier = deprecated[key].named_steps["classifier"]
            classifier.set_params(penalty="l2", l1_ratio=0.0)
        inputs = {
            "class_prior": features,
            "sentence_id": sentences.reshape(-1, 1),
            "acoustic": features,
        }
        with warnings.catch_warnings(record=True) as replacement_warnings:
            warnings.simplefilter("always")
            for key in self.MODEL_KEYS:
                replacement[key].fit(inputs[key], labels)
        with warnings.catch_warnings(record=True) as deprecated_warnings:
            warnings.simplefilter("always")
            for key in self.MODEL_KEYS:
                deprecated[key].fit(inputs[key], labels)
        self.assertEqual(replacement_warnings, [])
        self.assertEqual(len(deprecated_warnings), 2)
        for key in ("sentence_id", "acoustic"):
            np.testing.assert_array_equal(
                replacement[key].named_steps["classifier"].coef_,
                deprecated[key].named_steps["classifier"].coef_,
            )
            np.testing.assert_array_equal(
                replacement[key].predict_proba(inputs[key]),
                deprecated[key].predict_proba(inputs[key]),
            )

    def test_pure_calibration_and_hand_calculated_metrics_remain_exact(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            _calibrate_probability_arrays,
            _evaluate_probability_arrays,
        )

        calibration_probabilities = self._calibration_probabilities()
        calibration = _calibrate_probability_arrays(
            calibration_probabilities,
            (1.0, 0.8, 0.6),
        )
        for model in self.MODEL_KEYS:
            self.assertEqual(calibration[model]["1.0"], {
                "threshold": 0.2,
                "achieved_coverage": 1.0,
            })
            self.assertEqual(calibration[model]["0.8"], {
                "threshold": 0.3,
                "achieved_coverage": 5.0 / 6.0,
            })
            self.assertEqual(calibration[model]["0.6"], {
                "threshold": 0.4,
                "achieved_coverage": 4.0 / 6.0,
            })

        labels, probabilities, actors = self._metric_arrays(
            role="balanced_diagnostic",
        )
        metric_calibration = _calibrate_probability_arrays(
            probabilities,
            (1.0, 0.8, 0.6),
        )
        models = _evaluate_probability_arrays(
            labels,
            probabilities,
            actors,
            metric_calibration,
        )
        acoustic = models["acoustic"]
        self.assertAlmostEqual(acoustic["macro_f1"], 7.0 / 9.0, places=15)
        self.assertAlmostEqual(
            acoustic["balanced_accuracy"],
            5.0 / 6.0,
            places=15,
        )
        self.assertAlmostEqual(
            acoustic["multiclass_brier"],
            2.765 / 6.0,
            places=15,
        )
        expected_log_loss = -sum(
            math.log(value)
            for value in (0.70, 0.25, 0.40, 0.40, 0.30, 0.40)
        ) / 6.0
        self.assertAlmostEqual(
            acoustic["log_loss"],
            expected_log_loss,
            places=15,
        )
        self.assertAlmostEqual(acoustic["ece_10_bin"], 5.0 / 12.0, places=15)
        self.assertAlmostEqual(
            acoustic["retained"]["0.6"]["coverage"],
            2.0 / 3.0,
            places=15,
        )
        self.assertAlmostEqual(
            acoustic["retained"]["0.6"]["retained_macro_f1"],
            2.0 / 3.0,
            places=15,
        )

    def test_sparse_suppression_and_probability_schemas_fail_closed(self) -> None:
        import numpy as np

        from scripts.emotion_state_phase_b_evaluation import (
            _calibrate_probability_arrays,
            _evaluate_probability_arrays,
        )
        from scripts.validate_emotion_state_002_phase_b import (
            validate_probability_inputs,
        )

        labels, probabilities, actors = self._metric_arrays(
            actor_count=9,
            role="balanced_diagnostic",
        )
        calibration = _calibrate_probability_arrays(
            probabilities,
            (1.0, 0.8, 0.6),
        )
        models = _evaluate_probability_arrays(
            labels,
            probabilities,
            actors,
            calibration,
        )
        for model in models.values():
            self.assertTrue(model["suppressed"])
            self.assertIsNone(model["macro_f1"])
            for cell in model["per_class_recall"].values():
                self.assertTrue(cell["suppressed"])
                self.assertIsNone(cell["recall"])

        malformed = {
            key: value.copy() for key, value in probabilities.items()
        }
        malformed["acoustic"][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            validate_probability_inputs(
                malformed,
                class_order=self.CLASS_ORDER,
            )

    def test_pure_bootstrap_matches_independent_actor_cluster_oracles(
        self,
    ) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            _paired_actor_bootstrap_arrays,
        )

        labels, probabilities, actors = self._clustered_bootstrap_arrays()
        _, seed = self._config_identity()
        first = _paired_actor_bootstrap_arrays(
            labels,
            probabilities,
            actors,
            2000,
            seed,
        )
        second = _paired_actor_bootstrap_arrays(
            labels,
            probabilities,
            actors,
            2000,
            seed,
        )
        self.assertEqual(first, second)
        expected = {
            "class_prior": {
                "point_estimate": 0.7326839826839826,
                "lower_95": 0.6396058006535947,
                "upper_95": 0.8981598822324628,
            },
            "sentence_id": {
                "point_estimate": 0.2504689754689755,
                "lower_95": 0.1520461945461947,
                "upper_95": 0.37701141451141434,
            },
        }
        for baseline, expected_cell in expected.items():
            for key, expected_value in expected_cell.items():
                self.assertAlmostEqual(
                    first[baseline][key],
                    expected_value,
                    places=15,
                )

    def test_diagnostic_and_cross_run_final_artifacts_fail_closed(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            build_decision_evidence,
            evaluate_partition,
            mint_slice_analysis,
            predict_probabilities,
        )

        run_a = self._semantic_artifacts(0)
        run_b = self._semantic_artifacts(1)
        diagnostic_partition = self._authoritative_partition(
            "balanced_diagnostic",
        )
        diagnostic_probabilities = predict_probabilities(
            run_a["fitted"],
            diagnostic_partition,
        )
        diagnostic = evaluate_partition(
            diagnostic_probabilities,
            run_a["calibration"],
        )
        self.assertFalse(diagnostic["final_decision_eligible"])
        diagnostic_rows = [
            record.clip_stem
            for record in self.RECORDS_BY_ROLE["balanced_diagnostic"]
        ]
        diagnostic_slice = mint_slice_analysis(
            diagnostic_probabilities,
            diagnostic,
            {"all_diagnostic": diagnostic_rows},
        )
        with self.assertRaisesRegex(ValueError, "final_lockbox"):
            build_decision_evidence(
                diagnostic,
                run_a["bootstrap"],
                diagnostic_slice,
            )
        with self.assertRaisesRegex(ValueError, "provenance commitments"):
            build_decision_evidence(
                run_a["evaluation"],
                run_b["bootstrap"],
                run_a["slice_analysis"],
            )

    def test_domains_and_skewed_percentile_validation_are_strict(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_bootstrap_result,
            validate_evaluation_result,
        )

        artifacts = self._semantic_artifacts()
        evaluation = artifacts["evaluation"].to_payload()
        for key, value in (
            ("macro_f1", 1.01),
            ("balanced_accuracy", -0.01),
            ("multiclass_brier", 2.01),
            ("log_loss", -0.01),
            ("ece_10_bin", -0.01),
        ):
            mutated = deepcopy(evaluation)
            mutated["models"]["acoustic"][key] = value
            self._reseal_payload(mutated)
            with self.subTest(metric=key):
                with self.assertRaises(ValueError):
                    validate_evaluation_result(
                        mutated,
                        expected_role="final_lockbox",
                    )

        bootstrap = artifacts["bootstrap"].to_payload()
        bootstrap["paired_macro_f1_lift"]["class_prior"].update({
            "point_estimate": 0.9,
            "lower_95": 0.1,
            "upper_95": 0.8,
        })
        bootstrap["paired_macro_f1_lift"]["sentence_id"].update({
            "point_estimate": -0.9,
            "lower_95": -0.8,
            "upper_95": -0.1,
        })
        self._reseal_payload(bootstrap)
        validate_bootstrap_result(bootstrap)

    def test_decision_rule_precedence_uses_only_derived_bound_facts(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            _decision_outcome,
            decide_experiment,
        )

        artifacts = self._semantic_artifacts()
        decision = artifacts["decision"]
        validity = {
            "material_valid": True,
            "environment_valid": True,
            "split_valid": True,
            "leakage_free": True,
            "deterministic": True,
            "lockbox_valid": True,
        }
        self.assertIn(
            decide_experiment(decision, validity),
            ("keep_for_research_only", "revise", "discard"),
        )
        for key in validity:
            invalid = dict(validity)
            invalid[key] = False
            self.assertEqual(decide_experiment(decision, invalid), "discard")

        fixture = {
            "models": {
                "class_prior": {
                    "macro_f1": 0.40,
                    "multiclass_brier": 1.0,
                    "ece_10_bin": 0.20,
                },
                "sentence_id": {"macro_f1": 0.45},
                "acoustic": {
                    "macro_f1": 0.60,
                    "multiclass_brier": 0.8,
                    "ece_10_bin": 0.20,
                    "per_class_recall": {
                        label: {"recall": 0.5}
                        for label in self.CLASS_ORDER
                    },
                },
            },
            "paired_macro_f1_lift": {
                "class_prior": {
                    "point_estimate": 0.20,
                    "lower_95": 0.05,
                    "upper_95": 0.30,
                },
                "sentence_id": {
                    "point_estimate": 0.15,
                    "lower_95": 0.02,
                    "upper_95": 0.25,
                },
            },
            "sentence_driven_apparent_lift": False,
            "eligible_slice_reversal": False,
            "eligible_slice_instability": False,
            "confidence_abstention_improves": True,
        }
        self.assertEqual(
            _decision_outcome(fixture, validity),
            "keep_for_research_only",
        )
        for key, expected in (
            ("sentence_driven_apparent_lift", "discard"),
            ("eligible_slice_reversal", "revise"),
            ("eligible_slice_instability", "revise"),
        ):
            mutated = deepcopy(fixture)
            mutated[key] = True
            self.assertEqual(_decision_outcome(mutated, validity), expected)
        ineffective = deepcopy(fixture)
        ineffective["confidence_abstention_improves"] = False
        self.assertEqual(_decision_outcome(ineffective, validity), "revise")
        crossing = deepcopy(fixture)
        crossing["paired_macro_f1_lift"]["class_prior"]["lower_95"] = -0.01
        self.assertEqual(_decision_outcome(crossing, validity), "revise")
        failed = deepcopy(fixture)
        failed["paired_macro_f1_lift"]["sentence_id"]["point_estimate"] = 0.0
        self.assertEqual(_decision_outcome(failed, validity), "discard")


class Task10ProductionPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        EvaluationTests.setUpClass()

    def test_production_paths_pin_only_verified_public_roots_and_ignored_outputs(
        self,
    ) -> None:
        from scripts import run_emotion_state_002_phase_b as runner

        paths = runner.RunnerPaths.production()
        public_root = ROOT / "data/public/emotion-state"
        crema_root = public_root / "crema-d-v1.0"
        ami_root = public_root / "ami-manual-annotations-v1.6.2"

        self.assertTrue(
            hasattr(paths, "public_material_root"),
            "production RunnerPaths must pin the public-material root",
        )
        self.assertEqual(paths.public_material_root, public_root)
        self.assertEqual(paths.crema_material_root, crema_root)
        self.assertEqual(
            paths.crema_audio_root,
            crema_root / "repository/AudioWAV",
        )
        self.assertEqual(
            paths.crema_finished_responses_path,
            crema_root / "repository/finishedResponses.csv",
        )
        self.assertEqual(
            paths.crema_summary_table_path,
            crema_root / "repository/processedResults/summaryTable.csv",
        )
        self.assertEqual(paths.ami_material_root, ami_root)
        self.assertEqual(
            paths.ami_archive_path,
            ami_root / "ami_manual_1.6.2.zip",
        )
        self.assertEqual(paths.ami_extracted_root, ami_root / "extracted")
        self.assertEqual(
            paths.ami_partition_source_path,
            ami_root / "official-partitions/datasets.shtml",
        )
        self.assertEqual(
            paths.dataset_evidence_root,
            ROOT / "research/sources/emotion_state/datasets",
        )
        for output in (
            paths.preflight_cache_root,
            paths.non_lockbox_cache_root,
            paths.non_lockbox_packet_path,
        ):
            self.assertTrue(output.is_relative_to(paths.state_root))
        self.assertTrue(
            paths.final_lockbox_cache_root.is_relative_to(paths.lockbox_root)
        )
        self.assertFalse(paths.canonical_root.is_relative_to(paths.state_root))

        altered = replace(
            paths,
            public_material_root=ROOT / "data/public/other",
        )
        with self.assertRaisesRegex(
            runner.RunnerError,
            "prescribed paths",
        ):
            runner._validate_layout(altered)

    def test_partition_cache_serialization_emits_only_three_nonfinal_roles(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation

        self.assertTrue(
            hasattr(evaluation, "serialize_partition_authority_caches"),
            "preflight must serialize partition-separated split authorities",
        )
        caches = evaluation.serialize_partition_authority_caches(
            EvaluationTests.SPLIT_ASSIGNMENT
        )
        self.assertEqual(
            set(caches),
            {
                "training_discovery",
                "calibration",
                "balanced_diagnostic",
            },
        )
        for role, cache in caches.items():
            self.assertEqual(cache["partition_role"], role)
            expected = EvaluationTests.RECORDS_BY_ROLE[role]
            self.assertEqual(len(cache["records"]), len(expected))
            self.assertEqual(
                {row["clip_stem"] for row in cache["records"]},
                {record.clip_stem for record in expected},
            )

        split_manifest = EvaluationTests.SPLIT_ASSIGNMENT.to_payload()
        self.assertEqual(
            split_manifest["final_lockbox_commitment"]["eligible_actor_count"],
            30,
        )
        self.assertEqual(
            split_manifest["final_lockbox_commitment"]["eligible_record_count"],
            len(EvaluationTests.RECORDS_BY_ROLE["final_lockbox"]),
        )
        self.assertRegex(
            split_manifest["final_lockbox_commitment"][
                "eligible_record_commitment_sha256"
            ],
            r"^[0-9A-F]{64}$",
        )

    def test_partition_authority_derivation_requires_private_split_lifecycle(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.validate_emotion_state_002_phase_b import (
            canonical_payload_sha256,
        )

        authority = evaluation.derive_validated_partition_authority(
            EvaluationTests.SPLIT_ASSIGNMENT,
            role="training_discovery",
        )
        self.assertEqual(
            authority.to_payload()["partition_role"],
            "training_discovery",
        )
        self.assertFalse(
            hasattr(evaluation, "mint_validated_partition_authority"),
            "caller mappings must not have a mapping-to-authority mint path",
        )

        caches = evaluation.serialize_partition_authority_caches(
            EvaluationTests.SPLIT_ASSIGNMENT
        )
        tampered_cache = deepcopy(caches["training_discovery"])
        tampered_cache["records"][0]["label"] = (
            "D"
            if tampered_cache["records"][0]["label"] != "D"
            else "A"
        )
        tampered_cache["self_sha256"] = canonical_payload_sha256(
            tampered_cache
        )
        with self.assertRaisesRegex(
            (TypeError, ValueError),
            "ValidatedSplitAssignment",
        ):
            evaluation.derive_validated_partition_authority(
                tampered_cache,
                role="training_discovery",
            )

    def test_partition_authority_cache_rejects_label_vote_disagreement(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.emotion_state_phase_b_splits import build_actor_split

        records = list(EvaluationTests.AUTHORITATIVE_RECORDS)
        original = records[0]
        replacement_label = next(
            label
            for label in EvaluationTests.CLASS_ORDER
            if label != original.label
        )
        records[0] = replace(original, label=replacement_label)
        assignment = build_actor_split(
            records,
            EvaluationTests.CONFIGURATION_DIGEST,
        )
        with self.assertRaisesRegex(ValueError, "vote"):
            evaluation.mint_validated_split_assignment(
                records,
                assignment,
                EvaluationTests.CONFIGURATION_DIGEST,
            )

    def test_split_mint_rejects_clip_identity_not_matching_record(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.emotion_state_phase_b_splits import build_actor_split

        records = list(EvaluationTests.AUTHORITATIVE_RECORDS)
        index = next(
            index
            for index, record in enumerate(records)
            if record.actor_id == "1002" and record.sentence_id == "S00"
        )
        original = records[index]
        for clip_stem in (
            "9999_ZZZ_ANG_XX",
            "9999_S00_ANG_XX",
            "1002_ZZZ_ANG_XX",
        ):
            with self.subTest(clip_stem=clip_stem):
                mutated = list(records)
                mutated[index] = replace(original, clip_stem=clip_stem)
                assignment = build_actor_split(
                    mutated,
                    EvaluationTests.CONFIGURATION_DIGEST,
                )
                with self.assertRaisesRegex(ValueError, "clip identity"):
                    evaluation.mint_validated_split_assignment(
                        mutated,
                        assignment,
                        EvaluationTests.CONFIGURATION_DIGEST,
                    )

    def test_split_mint_rejects_stems_outside_source_clip_contract(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.emotion_state_phase_b_splits import build_actor_split

        records = list(EvaluationTests.AUTHORITATIVE_RECORDS)
        original = records[0]
        malformed_stems = (
            f"{original.actor_id}_{original.sentence_id}_JOY_XX",
            f"{original.actor_id}_{original.sentence_id}_ANG_XY",
            f"{original.actor_id}_{original.sentence_id}_ANG",
            f"{original.actor_id}_{original.sentence_id}_ANG_XX.wav",
        )
        for clip_stem in malformed_stems:
            with self.subTest(clip_stem=clip_stem):
                mutated = list(records)
                mutated[0] = replace(original, clip_stem=clip_stem)
                assignment = build_actor_split(
                    mutated,
                    EvaluationTests.CONFIGURATION_DIGEST,
                )
                with self.assertRaisesRegex(ValueError, "clip identity"):
                    evaluation.mint_validated_split_assignment(
                        mutated,
                        assignment,
                        EvaluationTests.CONFIGURATION_DIGEST,
                    )

    def test_filename_emotion_remains_independent_from_perceived_label(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.emotion_state_phase_b_splits import build_actor_split

        records = list(EvaluationTests.AUTHORITATIVE_RECORDS)
        index = next(
            index
            for index, record in enumerate(records)
            if record.actor_id == "1002" and record.sentence_id == "S00"
        )
        original = records[index]
        filename_emotion = "ANG" if original.label != "A" else "DIS"
        records[index] = replace(
            original,
            clip_stem=(
                f"{original.actor_id}_{original.sentence_id}_"
                f"{filename_emotion}_HI"
            ),
        )
        assignment = build_actor_split(
            records,
            EvaluationTests.CONFIGURATION_DIGEST,
        )
        split = evaluation.mint_validated_split_assignment(
            records,
            assignment,
            EvaluationTests.CONFIGURATION_DIGEST,
        )
        self.assertEqual(
            evaluation.derive_validated_partition_authority(
                split,
                role=assignment[original.actor_id],
            ).to_payload()["partition_role"],
            assignment[original.actor_id],
        )

    def test_non_lockbox_partition_evidence_uses_partition_authority_only(
        self,
    ) -> None:
        import numpy as np

        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.validate_emotion_state_002_phase_b import (
            EXPECTED_CONFIG,
            EXPECTED_ENVIRONMENT_LOCK,
            EXPECTED_FEATURE_SCHEMA,
            EXPECTED_SPLIT_SCHEMA,
        )

        authority = evaluation.derive_validated_partition_authority(
            EvaluationTests.SPLIT_ASSIGNMENT,
            role="training_discovery",
        )
        records = EvaluationTests.RECORDS_BY_ROLE["training_discovery"]
        features = np.zeros((len(records), 17), dtype=np.float64)
        try:
            evidence = evaluation.mint_partition_evidence(
                partition_role="training_discovery",
                row_ids=[record.clip_stem for record in records],
                actor_ids=[record.actor_id for record in records],
                labels=np.asarray(
                    [record.label for record in records],
                    dtype="<U1",
                ),
                sentences=np.asarray(
                    [record.sentence_id for record in records],
                    dtype="<U3",
                ),
                features=features,
                upstream_acoustic_source_commitment_sha256="A" * 64,
                split_assignment=authority,
                configuration=deepcopy(EXPECTED_CONFIG),
                environment_lock=deepcopy(EXPECTED_ENVIRONMENT_LOCK),
                feature_schema=deepcopy(EXPECTED_FEATURE_SCHEMA),
                split_schema=deepcopy(EXPECTED_SPLIT_SCHEMA),
                model_identity=evaluation.frozen_model_identity(
                    EvaluationTests.MODEL_SEED
                ),
            )
        except (TypeError, ValueError) as error:
            self.fail(
                "partition-only authority must mint non-lockbox evidence: "
                f"{error}"
            )
        self.assertEqual(
            evidence.to_payload()["partition_role"],
            "training_discovery",
        )
        self.assertEqual(
            evidence.to_payload()["assignment_sha256"],
            EvaluationTests.SPLIT_ASSIGNMENT.to_payload()["assignment_sha256"],
        )

    def test_tracked_ami_dependency_quarantine_blocks_material_access(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_public_pipeline as pipeline

        evidence_root = ROOT / "research/sources/emotion_state/datasets"
        evidence = {
            name: (evidence_root / name).read_bytes()
            for name in pipeline.TRACKED_DATASET_EVIDENCE_FILENAMES
        }
        with self.assertRaisesRegex(
            pipeline.PublicMaterialPrerequisiteError,
            r"2069 .*participant identity",
        ):
            pipeline.validate_tracked_public_evidence(evidence)

    def test_production_prerequisite_reads_only_identity_bound_tracked_evidence(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_public_pipeline as pipeline
        from scripts import run_emotion_state_002_phase_b as runner

        self.assertTrue(
            hasattr(runner, "_assert_production_material_prerequisites"),
            "production preflight must gate on tracked evidence first",
        )
        paths = runner.RunnerPaths.production()
        observed: list[Path] = []
        real_read = runner._read_file_nofollow

        def observed_read(path: Path, **kwargs: Any) -> bytes:
            observed.append(Path(path))
            return real_read(path, **kwargs)

        with patch.object(
            runner,
            "_read_file_nofollow",
            side_effect=observed_read,
        ):
            with self.assertRaisesRegex(
                runner.RunnerError,
                r"2069 .*participant identity",
            ):
                runner._assert_production_material_prerequisites(paths)
        self.assertEqual(
            set(observed),
            {
                paths.dataset_evidence_root / name
                for name in pipeline.TRACKED_DATASET_EVIDENCE_FILENAMES
            },
        )
        self.assertFalse(
            any(
                path.is_relative_to(paths.public_material_root)
                for path in observed
            )
        )

    @staticmethod
    def _non_lockbox_review_aggregates() -> tuple[dict[str, Any], dict[str, Any]]:
        from scripts.emotion_state_phase_b_evaluation import (
            evaluate_partition,
            predict_probabilities,
        )

        case = EvaluationTests(
            "test_diagnostic_and_cross_run_final_artifacts_fail_closed"
        )
        artifacts = case._semantic_artifacts()
        diagnostic_partition = case._authoritative_partition(
            "balanced_diagnostic"
        )
        diagnostic_probabilities = predict_probabilities(
            artifacts["fitted"],
            diagnostic_partition,
        )
        diagnostic = evaluate_partition(
            diagnostic_probabilities,
            artifacts["calibration"],
        ).to_payload()
        RunnerStateTests.setUpClass()
        return diagnostic, deepcopy(RunnerStateTests.AMI_AGGREGATE)

    @staticmethod
    def _rewrite_and_reseal_identity(
        value: Any,
        *,
        field: str,
        replacement: str,
    ) -> Any:
        from scripts.validate_emotion_state_002_phase_b import (
            canonical_payload_sha256,
        )

        if isinstance(value, list):
            return [
                Task10ProductionPipelineTests._rewrite_and_reseal_identity(
                    item,
                    field=field,
                    replacement=replacement,
                )
                for item in value
            ]
        if not isinstance(value, dict):
            return value
        rewritten = {
            key: (
                replacement
                if key == field
                else Task10ProductionPipelineTests._rewrite_and_reseal_identity(
                    item,
                    field=field,
                    replacement=replacement,
                )
            )
            for key, item in value.items()
        }
        if "self_sha256" in rewritten:
            rewritten["self_sha256"] = canonical_payload_sha256(rewritten)
        return rewritten

    def test_non_lockbox_packet_builder_cross_binds_diagnostic_identities(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_public_pipeline as pipeline

        diagnostic, ami = self._non_lockbox_review_aggregates()
        split_identity = diagnostic["provenance"]["split_manifest_sha256"]
        conflicting_split = (
            "A" * 64 if split_identity != "A" * 64 else "B" * 64
        )
        with self.assertRaisesRegex(
            pipeline.PublicMaterialPrerequisiteError,
            "split manifest identity does not match diagnostic provenance",
        ):
            pipeline.build_non_lockbox_review_packet(
                diagnostic_aggregate=diagnostic,
                ami_aggregate=ami,
                split_manifest_sha256=conflicting_split,
            )

        altered_configuration = self._rewrite_and_reseal_identity(
            diagnostic,
            field="configuration_sha256",
            replacement="B" * 64,
        )
        with self.assertRaisesRegex(
            pipeline.PublicMaterialPrerequisiteError,
            "configuration identity does not match diagnostic provenance",
        ):
            pipeline.build_non_lockbox_review_packet(
                diagnostic_aggregate=altered_configuration,
                ami_aggregate=ami,
                split_manifest_sha256=altered_configuration[
                    "provenance"
                ]["split_manifest_sha256"],
            )

    def test_non_lockbox_packet_validator_and_runner_bind_exact_split_identity(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_public_pipeline as pipeline
        from scripts import run_emotion_state_002_phase_b as runner

        diagnostic, ami = self._non_lockbox_review_aggregates()
        split_identity = diagnostic["provenance"]["split_manifest_sha256"]
        packet = pipeline.build_non_lockbox_review_packet(
            diagnostic_aggregate=diagnostic,
            ami_aggregate=ami,
            split_manifest_sha256=split_identity,
        )
        conflicting_split = (
            "A" * 64 if split_identity != "A" * 64 else "B" * 64
        )
        mutated = deepcopy(packet)
        mutated["split_manifest_sha256"] = conflicting_split
        mutated.pop("review_sha256")
        mutated["review_sha256"] = pipeline._canonical_digest(mutated)
        with self.assertRaisesRegex(
            pipeline.PublicMaterialPrerequisiteError,
            "split manifest identity does not match diagnostic provenance",
        ):
            pipeline.validate_non_lockbox_review_packet(mutated)

        self.assertEqual(
            runner._validate_non_lockbox_packet_for_authority(
                runner.RunnerPaths.production(),
                packet,
                expected_split_manifest_sha256=split_identity,
            ),
            packet,
        )
        with self.assertRaisesRegex(
            runner.RunnerError,
            "split manifest identity does not match preflight state",
        ):
            runner._validate_non_lockbox_packet_for_authority(
                runner.RunnerPaths.production(),
                packet,
                expected_split_manifest_sha256=conflicting_split,
            )

    def test_non_lockbox_review_packet_binds_aggregates_and_zero_lockbox_reads(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_public_pipeline as pipeline
        diagnostic, ami = self._non_lockbox_review_aggregates()
        split_identity = diagnostic["provenance"]["split_manifest_sha256"]
        packet = pipeline.build_non_lockbox_review_packet(
            diagnostic_aggregate=diagnostic,
            ami_aggregate=ami,
            split_manifest_sha256=split_identity,
        )
        validated = pipeline.validate_non_lockbox_review_packet(packet)
        self.assertEqual(validated, packet)
        from scripts import run_emotion_state_002_phase_b as runner
        from scripts.validate_emotion_state_002_phase_b import (
            expected_non_lockbox_packet,
        )

        self.assertTrue(
            hasattr(runner, "_validate_non_lockbox_packet_for_authority"),
            "production non-lockbox must require the aggregate-bound packet",
        )
        self.assertEqual(
            runner._validate_non_lockbox_packet_for_authority(
                runner.RunnerPaths.production(),
                packet,
                expected_split_manifest_sha256=split_identity,
            ),
            packet,
        )
        with self.assertRaisesRegex(
            runner.RunnerError,
            "production non-lockbox packet",
        ):
            runner._validate_non_lockbox_packet_for_authority(
                runner.RunnerPaths.production(),
                expected_non_lockbox_packet("A" * 64),
                expected_split_manifest_sha256=split_identity,
            )
        self.assertEqual(
            packet["lockbox_access"],
            {
                "open_count": 0,
                "label_reads": 0,
                "feature_reads": 0,
                "audio_reads": 0,
            },
        )
        self.assertFalse(packet["final_decision_eligible"])
        self.assertRegex(packet["diagnostic_aggregate_sha256"], r"^[0-9A-F]{64}$")
        self.assertRegex(packet["ami_aggregate_sha256"], r"^[0-9A-F]{64}$")
        self.assertRegex(packet["review_sha256"], r"^[0-9A-F]{64}$")
        serialized = json.dumps(packet, sort_keys=True).casefold()
        for forbidden in (
            '"row_ids"',
            '"actor_ids"',
            '"participant_ids"',
            '"meeting_ids"',
            '"probabilities"',
            '"clip_stem"',
            ".wav",
        ):
            self.assertNotIn(forbidden, serialized)

        mutated = deepcopy(packet)
        mutated["model_settings"]["C"] = 2.0
        with self.assertRaisesRegex(
            pipeline.PublicMaterialPrerequisiteError,
            "model settings",
        ):
            pipeline.validate_non_lockbox_review_packet(mutated)
        with self.assertRaisesRegex(
            pipeline.PublicMaterialPrerequisiteError,
            "private identifier",
        ):
            pipeline.validate_aggregate_privacy(
                {
                    "safe_cell": {
                        "unique_actor_count": 10,
                        "value": 0.5,
                    },
                    "row_ids": ["synthetic-row"],
                }
            )


class RunnerStateTests(unittest.TestCase):
    DIGESTS = tuple(character * 64 for character in "ABCDEF0123456789")

    @classmethod
    def setUpClass(cls) -> None:
        from scripts.emotion_state_phase_b_ami_mechanics import (
            MeetingMechanics,
            contribution_limited_aggregates,
        )

        EvaluationTests.setUpClass()
        evaluation_case = EvaluationTests(
            "test_rereview_decision_flags_cannot_be_caller_asserted"
        )
        cls.DECISION_ARTIFACT = evaluation_case._semantic_artifacts()["decision"]
        cls.DECISION_EVIDENCE = deepcopy(cls.DECISION_ARTIFACT.to_payload())
        cls.SPLIT_MANIFEST = deepcopy(
            EvaluationTests.SPLIT_ASSIGNMENT.to_payload()
        )
        meetings = tuple(
            MeetingMechanics(
                meeting_id=f"M{index}",
                participants=(f"P{index * 2:02d}", f"P{index * 2 + 1:02d}"),
                values=(
                    ("turn_duration_ms_median", float(index)),
                    ("turn_duration_ms_p90", float(index + 1)),
                    ("inter_turn_gap_ms_median", float(index + 2)),
                    ("inter_turn_gap_ms_p90", float(index + 3)),
                    ("overlap_ratio", 0.1),
                    ("floor_changes_per_minute", float(index + 4)),
                    ("speaker_balance_normalized_entropy", 0.5),
                    ("backchannels_per_100_turns", 25.0),
                ),
                dialogue_act_distribution=(
                    ("ami_da_1", 0.25),
                    ("ami_da_2", 0.5),
                    ("ami_da_3", 0.25),
                    ("ami_da_4", 0.0),
                    ("ami_da_5", 0.0),
                    ("ami_da_6", 0.0),
                    ("ami_da_7", 0.0),
                    ("ami_da_8", 0.0),
                    ("ami_da_9", 0.0),
                    ("ami_da_11", 0.0),
                    ("ami_da_12", 0.0),
                    ("ami_da_13", 0.0),
                    ("ami_da_14", 0.0),
                    ("ami_da_15", 0.0),
                    ("ami_da_16", 0.0),
                ),
            )
            for index in range(5)
        )
        official_order = tuple(meeting.meeting_id for meeting in meetings)
        membership = {
            partition: official_order
            for partition in ("scenario_only", "full_corpus", "full_only")
        }
        cls.AMI_AGGREGATE = contribution_limited_aggregates(
            meetings,
            membership,
            official_order,
        )
        cls.AMI_AUTHORITY = {
            "meetings": [
                {
                    "meeting_id": meeting.meeting_id,
                    "participants": list(meeting.participants),
                    "values": dict(meeting.values),
                    "dialogue_act_distribution": dict(
                        meeting.dialogue_act_distribution
                    ),
                }
                for meeting in meetings
            ],
            "partition_membership": {
                key: list(value) for key, value in membership.items()
            },
            "official_order": list(official_order),
        }

    def setUp(self) -> None:
        from scripts import run_emotion_state_002_phase_b as runner
        from scripts.validate_emotion_state_002_phase_b import (
            _canonical_digest,
            expected_non_lockbox_packet,
            expected_phase_b_input_ledger,
        )

        self.runner = runner
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name).resolve()
        self.input_root = self.root / "public-inputs"
        self.state_root = self.root / "ignored-state"
        self.canonical_root = self.root / "canonical"
        self.non_lockbox_root = self.state_root / "non-lockbox"
        self.lockbox_root = self.state_root / "lockbox"
        self.input_root.mkdir(parents=True)
        self.non_lockbox_root.mkdir(parents=True)
        self.lockbox_root.mkdir(parents=True)
        self.canonical_root.mkdir(parents=True)

        self.config_path = self.input_root / "config.json"
        self.environment_lock_path = self.input_root / "requirements.lock"
        self.feature_schema_path = self.input_root / "feature.schema.json"
        self.split_schema_path = self.input_root / "split.schema.json"
        self.split_manifest_path = self.input_root / "split-manifest.json"
        self.input_ledger_path = self.input_root / "input-ledger.json"
        self.non_lockbox_packet_path = (
            self.non_lockbox_root / "non-lockbox-packet.json"
        )
        self.lockbox_result_path = self.lockbox_root / "lockbox-result.json"
        shutil.copy2(CONFIG, self.config_path)
        shutil.copy2(ENVIRONMENT_LOCK, self.environment_lock_path)
        shutil.copy2(FEATURE_SCHEMA, self.feature_schema_path)
        shutil.copy2(SPLIT_SCHEMA, self.split_schema_path)
        self._write_json(self.split_manifest_path, self.SPLIT_MANIFEST)

        self.input_ledger = expected_phase_b_input_ledger()
        self.non_lockbox_packet = expected_non_lockbox_packet(self.DIGESTS[8])
        self.lockbox_result = {
            "schema_version": 1,
            "decision_evidence": deepcopy(self.DECISION_EVIDENCE),
            "ami": {
                "aggregate": deepcopy(self.AMI_AGGREGATE),
                "authority": deepcopy(self.AMI_AUTHORITY),
                "authority_sha256": _canonical_digest(self.AMI_AUTHORITY),
            },
        }
        self.lockbox_ami_input = {
            "schema_version": 1,
            "ami": deepcopy(self.lockbox_result["ami"]),
        }
        self._write_json(self.input_ledger_path, self.input_ledger)
        self._write_json(self.non_lockbox_packet_path, self.non_lockbox_packet)
        self._write_json(self.lockbox_result_path, self.lockbox_ami_input)
        self.paths = self._paths()

        clean_environment = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        }
        self.environment_patcher = patch.dict(
            os.environ,
            clean_environment,
            clear=True,
        )
        self.environment_patcher.start()
        self.addCleanup(self.environment_patcher.stop)

    def _paths(self, **changes: Path) -> Any:
        values = {
            "project_root": self.root,
            "input_root": self.input_root,
            "state_root": self.state_root,
            "canonical_root": self.canonical_root,
            "config_path": self.config_path,
            "environment_lock_path": self.environment_lock_path,
            "feature_schema_path": self.feature_schema_path,
            "split_schema_path": self.split_schema_path,
            "split_manifest_path": self.split_manifest_path,
            "input_ledger_path": self.input_ledger_path,
            "non_lockbox_packet_path": self.non_lockbox_packet_path,
            "lockbox_result_path": self.lockbox_result_path,
        }
        values.update(changes)
        return self.runner.RunnerPaths.for_testing(**values)

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            (
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
        )

    def _state_bytes(self) -> bytes | None:
        if not self.paths.state_path.exists():
            return None
        return self.paths.state_path.read_bytes()

    def _canonical_bytes(self) -> tuple[bytes | None, bytes | None]:
        return tuple(
            path.read_bytes() if path.exists() else None
            for path in (self.paths.result_path, self.paths.report_path)
        )

    def _test_oracle_report_bytes(self, result: dict[str, Any]) -> bytes:
        result_bytes = self.runner.canonical_json_bytes(result)
        result_sha256 = hashlib.sha256(result_bytes).hexdigest().upper()
        canonical_payload = result_bytes.decode("utf-8").rstrip("\n")
        return (
            "# EMOTION-STATE-002 Phase B public-data feasibility\n\n"
            f"- Result SHA-256: `{result_sha256}`\n"
            f"- Decision: `{result['decision']}`\n"
            "- Final lockbox open count: `1`\n"
            "- Boundary: aggregate public/synthetic evidence only; no private data, "
            "provider operations, network evaluation, source adaptation, runtime "
            "influence, or customer-state output.\n\n"
            "## Canonical aggregate\n\n"
            "```json\n"
            f"{canonical_payload}\n"
            "```\n"
        ).encode("utf-8")

    def _write_mutually_consistent_candidate_assertions(
        self,
        paths: Any,
        result: dict[str, Any],
    ) -> tuple[bytes, bytes]:
        result_bytes = self.runner.canonical_json_bytes(result)
        report_bytes = self._test_oracle_report_bytes(result)
        paths.result_path.write_bytes(result_bytes)
        paths.report_path.write_bytes(report_bytes)
        transaction = json.loads(paths.journal_path.read_text(encoding="utf-8"))
        transaction["candidate_pair"] = {
            "result_sha256": hashlib.sha256(result_bytes).hexdigest().upper(),
            "report_sha256": hashlib.sha256(report_bytes).hexdigest().upper(),
        }
        self._write_json(paths.journal_path, transaction)
        receipt = self.runner._receipt_from_transaction(transaction)
        self._write_json(
            paths.receipt_path(transaction["receipt_name"]),
            receipt,
        )
        return result_bytes, report_bytes

    @staticmethod
    def _snapshot_publication_bytes(paths: Any) -> dict[str, bytes]:
        roots = (Path(paths.state_root), Path(paths.canonical_root))
        return {
            str(path.relative_to(paths.project_root)): path.read_bytes()
            for root in roots
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def _lockbox_subprocess(
        self,
        mode: str,
        marker: Path,
    ) -> subprocess.Popen[str]:
        path_fields = (
            "project_root",
            "input_root",
            "state_root",
            "canonical_root",
            "config_path",
            "environment_lock_path",
            "feature_schema_path",
            "split_schema_path",
            "split_manifest_path",
            "input_ledger_path",
            "non_lockbox_packet_path",
            "lockbox_result_path",
        )
        payload = {
            field: str(getattr(self.paths, field)) for field in path_fields
        }
        code = f"""
import os
from pathlib import Path
from scripts import run_emotion_state_002_phase_b as runner
from scripts.test_emotion_state_002_phase_b import EvaluationTests

values = {payload!r}
paths = runner.RunnerPaths.for_testing(
    **{{key: Path(value) for key, value in values.items()}}
)
EvaluationTests.setUpClass()
decision_evidence = EvaluationTests(
    "test_rereview_decision_flags_cannot_be_caller_asserted"
)._semantic_artifacts()["decision"]
mode = {mode!r}
marker = Path({str(marker)!r})

if mode == "crash_before_reservation":
    original_replace = runner._replace_bytes_durably
    def crash_before(path, content):
        if Path(path) == paths.lockbox_reservation_path:
            os._exit(72)
        return original_replace(path, content)
    runner._replace_bytes_durably = crash_before
elif mode == "crash_after_reservation":
    original_load = runner._load_json_object
    def crash_after(path, label):
        if Path(path) == paths.lockbox_result_path:
            with marker.open("ab", buffering=0) as handle:
                handle.write(b"entered\\n")
            os._exit(73)
        return original_load(path, label)
    runner._load_json_object = crash_after
else:
    original_load = runner._load_json_object
    marked = False
    def observed_load(path, label):
        global marked
        if Path(path) == paths.lockbox_result_path and not marked:
            with marker.open("ab", buffering=0) as handle:
                handle.write(b"entered\\n")
            marked = True
        return original_load(path, label)
    runner._load_json_object = observed_load

try:
    runner._run_lockbox_with_private_evidence_for_testing(
        paths,
        decision_evidence,
    )
except runner.RunnerError:
    raise SystemExit(2)
"""
        clean_environment = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "PYTHONPATH": str(ROOT),
        }
        return subprocess.Popen(
            [str(EVALUATION_PYTHON), "-c", code],
            cwd=ROOT,
            env=clean_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _clone_paths(self, clone_root: Path) -> Any:
        shutil.copytree(self.root, clone_root, dirs_exist_ok=True)
        values = {}
        for field in (
            "project_root",
            "input_root",
            "state_root",
            "canonical_root",
            "config_path",
            "environment_lock_path",
            "feature_schema_path",
            "split_schema_path",
            "split_manifest_path",
            "input_ledger_path",
            "non_lockbox_packet_path",
            "lockbox_result_path",
        ):
            original = Path(getattr(self.paths, field))
            values[field] = (
                clone_root
                if field == "project_root"
                else clone_root / original.relative_to(self.root)
            )
        return self.runner.RunnerPaths.for_testing(**values)

    def _stage_crash_subprocess(
        self,
        paths: Any,
        target: str,
        timing: str,
    ) -> subprocess.CompletedProcess[str]:
        values = {
            field: str(getattr(paths, field))
            for field in (
                "project_root",
                "input_root",
                "state_root",
                "canonical_root",
                "config_path",
                "environment_lock_path",
                "feature_schema_path",
                "split_schema_path",
                "split_manifest_path",
                "input_ledger_path",
                "non_lockbox_packet_path",
                "lockbox_result_path",
            )
        }
        code = f"""
import os
from pathlib import Path
from scripts import run_emotion_state_002_phase_b as runner

values = {values!r}
paths = runner.RunnerPaths.for_testing(
    **{{key: Path(value) for key, value in values.items()}}
)
target = {target!r}
timing = {timing!r}
original_write = runner._write_new_fsynced
original_replace = runner._replace_entry_durably

def classify_write(path):
    name = Path(path).name
    if name.endswith(".result.stage"):
        return "candidate_result"
    if name.endswith(".report.stage"):
        return "candidate_report"
    if name.endswith(".result.backup"):
        return "backup_result"
    if name.endswith(".report.backup"):
        return "backup_report"
    if name == runner.JOURNAL_NAME:
        return "journal"
    if name == "crash.json":
        return "receipt"
    return ""

def observed_write(path, content):
    label = classify_write(path)
    if label == target and timing == "before":
        os._exit(86)
    result = original_write(path, content)
    if label == target and timing == "after":
        os._exit(86)
    return result

def classify_replace(destination):
    path = Path(destination)
    if path == paths.result_path:
        return "canonical_result"
    if path == paths.report_path:
        return "canonical_report"
    if path == paths.state_path:
        return "awaiting_state"
    return ""

def observed_replace(source, destination):
    label = classify_replace(destination)
    if label == target and timing == "before":
        os._exit(86)
    result = original_replace(source, destination)
    if label == target and timing == "after":
        os._exit(86)
    return result

runner._write_new_fsynced = observed_write
runner._replace_entry_durably = observed_replace
runner.stage_candidate(paths, "crash.json")
"""
        return subprocess.run(
            [str(EVALUATION_PYTHON), "-c", code],
            cwd=ROOT,
            env={
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PYTHONPATH": str(ROOT),
            },
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def _accept_crash_subprocess(
        self,
        paths: Any,
        target: str,
        timing: str,
    ) -> subprocess.CompletedProcess[str]:
        values = {
            field: str(getattr(paths, field))
            for field in (
                "project_root",
                "input_root",
                "state_root",
                "canonical_root",
                "config_path",
                "environment_lock_path",
                "feature_schema_path",
                "split_schema_path",
                "split_manifest_path",
                "input_ledger_path",
                "non_lockbox_packet_path",
                "lockbox_result_path",
            )
        }
        code = f"""
import os
from pathlib import Path
from scripts import run_emotion_state_002_phase_b as runner

values = {values!r}
paths = runner.RunnerPaths.for_testing(
    **{{key: Path(value) for key, value in values.items()}}
)
target = {target!r}
timing = {timing!r}
original_replace = runner._replace_entry_durably
original_unlink = runner._durable_unlink

def classify_replace(destination):
    path = Path(destination)
    if path == paths.journal_path:
        return "accepted_journal"
    if path == paths.state_path:
        return "accepted_state"
    return ""

def observed_replace(source, destination):
    label = classify_replace(destination)
    if label == target and timing == "before":
        os._exit(87)
    result = original_replace(source, destination)
    if label == target and timing == "after":
        os._exit(87)
    return result

def classify_unlink(path):
    name = Path(path).name
    if name.endswith(".result.backup"):
        return "cleanup_result_backup"
    if name.endswith(".report.backup"):
        return "cleanup_report_backup"
    if name == "accept.json":
        return "cleanup_receipt"
    if name == runner.JOURNAL_NAME:
        return "cleanup_journal"
    return ""

def observed_unlink(path, *args, **kwargs):
    label = classify_unlink(path)
    if label == target and timing == "before":
        os._exit(87)
    result = original_unlink(path, *args, **kwargs)
    if label == target and timing == "after":
        os._exit(87)
    return result

runner._replace_entry_durably = observed_replace
runner._durable_unlink = observed_unlink
runner.accept_receipt(paths, paths.receipt_path("accept.json"))
"""
        return subprocess.run(
            [str(EVALUATION_PYTHON), "-c", code],
            cwd=ROOT,
            env={
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PYTHONPATH": str(ROOT),
            },
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def _advance_to_lockbox(self) -> None:
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)
        self.runner._run_lockbox_with_private_evidence_for_testing(
            self.paths,
            self.DECISION_ARTIFACT,
        )

    def _install_previous_pair(self) -> tuple[bytes, bytes]:
        result = b'{"previous":true}\n'
        report = b"# Previous report\n"
        self.paths.result_path.write_bytes(result)
        self.paths.report_path.write_bytes(report)
        return result, report

    def test_invalid_phase_order_and_stale_state_leave_state_bytes_unchanged(
        self,
    ) -> None:
        self.runner.initialize_state(self.paths)
        before = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "transition"):
            self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

        stale = json.loads(before.decode("utf-8"))
        stale["unexpected"] = True
        self._write_json(self.paths.state_path, stale)
        stale_bytes = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "state"):
            self.runner.run_preflight(self.paths)
        self.assertEqual(self._state_bytes(), stale_bytes)

    def test_preflight_binds_inputs_and_mutation_fails_without_state_change(
        self,
    ) -> None:
        state = self.runner.run_preflight(self.paths)
        self.assertEqual(state["phase"], "preflight_complete")
        for field in (
            "configuration_sha256",
            "environment_lock_sha256",
            "input_ledger_sha256",
            "split_manifest_sha256",
        ):
            self.assertRegex(state[field], r"^[0-9A-F]{64}$")

        before = self._state_bytes()
        self.config_path.write_bytes(self.config_path.read_bytes() + b" ")
        with self.assertRaisesRegex(self.runner.RunnerError, "configuration"):
            self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

        shutil.copy2(CONFIG, self.config_path)
        self.environment_lock_path.write_bytes(
            self.environment_lock_path.read_bytes() + b" "
        )
        with self.assertRaisesRegex(self.runner.RunnerError, "environment"):
            self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

    def test_state_bound_manifest_reader_returns_payload_identity_not_file_digest(
        self,
    ) -> None:
        state = self.runner.run_preflight(self.paths)
        semantic_identity = self.SPLIT_MANIFEST["split_manifest_sha256"]
        self.assertNotEqual(
            semantic_identity,
            state["split_manifest_sha256"],
            "state must separately bind the exact split-manifest file bytes",
        )
        self.assertEqual(
            self.runner._validated_split_manifest_identity(
                self.paths,
                state,
            ),
            semantic_identity,
        )

    def test_production_packet_readback_uses_state_bound_manifest_payload_identity(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_public_pipeline as pipeline

        state = self.runner.run_preflight(self.paths)
        diagnostic, ami = (
            Task10ProductionPipelineTests._non_lockbox_review_aggregates()
        )
        semantic_identity = self.SPLIT_MANIFEST["split_manifest_sha256"]
        packet = pipeline.build_non_lockbox_review_packet(
            diagnostic_aggregate=diagnostic,
            ami_aggregate=ami,
            split_manifest_sha256=semantic_identity,
        )
        self._write_json(self.non_lockbox_packet_path, packet)
        production_readback_paths = replace(
            self.paths,
            authority="production",
        )
        validated, _digest = self.runner._validated_packet(
            production_readback_paths,
            state,
            require_bound=False,
        )
        self.assertEqual(validated, packet)

        conflicting_identity = (
            "A" * 64 if semantic_identity != "A" * 64 else "B" * 64
        )
        conflicting_diagnostic = (
            Task10ProductionPipelineTests._rewrite_and_reseal_identity(
                diagnostic,
                field="split_manifest_sha256",
                replacement=conflicting_identity,
            )
        )
        conflicting_packet = pipeline.build_non_lockbox_review_packet(
            diagnostic_aggregate=conflicting_diagnostic,
            ami_aggregate=ami,
            split_manifest_sha256=conflicting_identity,
        )
        self._write_json(self.non_lockbox_packet_path, conflicting_packet)
        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "split manifest identity does not match preflight state",
        ):
            self.runner._validated_packet(
                production_readback_paths,
                state,
                require_bound=False,
            )

    def test_preflight_cannot_promote_preexisting_rehashed_cache_and_manifest(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation
        from scripts.validate_emotion_state_002_phase_b import (
            canonical_payload_sha256,
        )

        self.assertTrue(
            hasattr(self.runner, "_load_bound_partition_authority"),
            "non-lockbox must load cache authority through preflight state",
        )
        caches = evaluation.serialize_partition_authority_caches(
            EvaluationTests.SPLIT_ASSIGNMENT
        )
        cache_path = (
            self.paths.preflight_cache_root / "training_discovery.json"
        )
        tampered_cache = deepcopy(caches["training_discovery"])
        tampered_cache["records"][0]["label"] = (
            "D"
            if tampered_cache["records"][0]["label"] != "D"
            else "A"
        )
        tampered_cache["self_sha256"] = canonical_payload_sha256(
            tampered_cache
        )
        tampered_manifest = deepcopy(self.SPLIT_MANIFEST)
        tampered_manifest["partition_authority_sha256"][
            "training_discovery"
        ] = tampered_cache["self_sha256"]
        tampered_manifest["self_sha256"] = canonical_payload_sha256(
            tampered_manifest
        )
        self._write_json(cache_path, tampered_cache)
        self._write_json(self.split_manifest_path, tampered_manifest)
        state = self.runner.run_preflight(self.paths)

        state_before = self._state_bytes()
        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "runner-owned partition authority persistence is unavailable",
        ):
            self.runner._load_bound_partition_authority(
                self.paths,
                role="training_discovery",
                expected_split_manifest_sha256=state[
                    "split_manifest_sha256"
                ],
            )
        self.assertEqual(self._state_bytes(), state_before)

    def test_partition_authority_loader_is_unavailable_without_runner_owned_persistence(
        self,
    ) -> None:
        from scripts import emotion_state_phase_b_evaluation as evaluation

        caches = evaluation.serialize_partition_authority_caches(
            EvaluationTests.SPLIT_ASSIGNMENT
        )
        for role, payload in caches.items():
            self._write_json(
                self.paths.preflight_cache_root / f"{role}.json",
                payload,
            )
        state = self.runner.run_preflight(self.paths)
        with patch.object(
            self.runner.os,
            "stat",
            wraps=self.runner.os.stat,
        ) as stat_read, patch.object(
            self.runner,
            "_read_file_nofollow",
            wraps=self.runner._read_file_nofollow,
        ) as file_read:
            with self.assertRaisesRegex(
                self.runner.RunnerError,
                "runner-owned partition authority persistence is unavailable",
            ):
                self.runner._load_bound_partition_authority(
                    self.paths,
                    role="training_discovery",
                    expected_split_manifest_sha256=state[
                        "split_manifest_sha256"
                    ],
                )
        stat_read.assert_not_called()
        file_read.assert_not_called()

    def test_phase_specific_state_placeholders_fail_closed(self) -> None:
        self.runner.run_preflight(self.paths)
        state = self.runner.load_state(self.paths)
        state["non_lockbox_packet_sha256"] = self.DIGESTS[0]
        self._write_json(self.paths.state_path, state)
        before = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "preflight"):
            self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

    def test_paths_escape_private_components_and_mocked_reparse_fail_closed(
        self,
    ) -> None:
        outside = self.root.parent / f"{self.root.name}-outside-config.json"
        shutil.copy2(CONFIG, outside)
        self.addCleanup(outside.unlink, missing_ok=True)
        escaped_paths = self._paths(config_path=outside)
        with self.assertRaisesRegex(self.runner.RunnerError, "allowed root"):
            self.runner.run_preflight(escaped_paths)
        self.assertFalse(escaped_paths.state_path.exists())

        private_ledger = self.root / "data" / "private" / "input-ledger.json"
        self._write_json(private_ledger, self.input_ledger)
        private_paths = self._paths(
            input_root=self.root,
            input_ledger_path=private_ledger,
        )
        with self.assertRaisesRegex(self.runner.RunnerError, "private"):
            self.runner.run_preflight(private_paths)
        self.assertFalse(private_paths.state_path.exists())

        real_lstat = os.lstat

        def fake_lstat(path: os.PathLike[str] | str) -> Any:
            status = real_lstat(path)
            if Path(path) == self.input_root:
                return SimpleNamespace(
                    st_mode=status.st_mode,
                    st_file_attributes=getattr(
                        stat,
                        "FILE_ATTRIBUTE_REPARSE_POINT",
                        0x400,
                    ),
                )
            return status

        with patch.object(self.runner.os, "lstat", side_effect=fake_lstat):
            with self.assertRaisesRegex(self.runner.RunnerError, "reparse"):
                self.runner.run_preflight(self.paths)
        self.assertFalse(self.paths.state_path.exists())

    def test_non_lockbox_rejects_lockbox_paths_credentials_runtime_and_network(
        self,
    ) -> None:
        self.runner.run_preflight(self.paths)
        before = self._state_bytes()
        stolen = self.lockbox_root / "stolen-packet.json"
        self._write_json(stolen, self.non_lockbox_packet)
        stolen_paths = self._paths(non_lockbox_packet_path=stolen)
        with self.assertRaisesRegex(self.runner.RunnerError, "non-lockbox"):
            self.runner.run_non_lockbox(stolen_paths)
        self.assertEqual(self._state_bytes(), before)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-secret"}):
            with self.assertRaisesRegex(self.runner.RunnerError, "credential"):
                self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

        with patch.dict(sys.modules, {"runtime.synthetic": object()}):
            with self.assertRaisesRegex(self.runner.RunnerError, "runtime"):
                self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

        with patch.dict(os.environ, {"SYNTHETIC_PASSWORD": "credential"}):
            with self.assertRaisesRegex(self.runner.RunnerError, "credential"):
                self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

    def test_non_lockbox_model_settings_must_match_frozen_configuration(
        self,
    ) -> None:
        self.runner.run_preflight(self.paths)
        mutated = deepcopy(self.non_lockbox_packet)
        mutated["model_settings"]["C"] = 2.0
        self._write_json(self.non_lockbox_packet_path, mutated)
        before = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "model settings"):
            self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), before)

    def test_no_production_operation_callback_can_activate_boundaries(self) -> None:
        self.assertNotIn(
            "operation",
            inspect.signature(self.runner.run_non_lockbox).parameters,
        )
        self.assertNotIn(
            "operation",
            inspect.signature(self.runner.run_lockbox).parameters,
        )

    def test_lockbox_is_one_use_and_exactly_bound(self) -> None:
        self._advance_to_lockbox()
        state = self.runner.load_state(self.paths)
        self.assertEqual(state["phase"], "lockbox_complete")
        self.assertEqual(state["lockbox_open_count"], 1)
        self.assertRegex(state["lockbox_result_sha256"], r"^[0-9A-F]{64}$")
        before = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "lockbox"):
            self.runner._run_lockbox_with_private_evidence_for_testing(
                self.paths,
                self.DECISION_ARTIFACT,
            )
        self.assertEqual(self._state_bytes(), before)

    def test_result_and_report_are_deterministic_and_bind_every_required_group(
        self,
    ) -> None:
        self._advance_to_lockbox()
        first = self.runner.build_aggregate_result(self.paths)
        second = self.runner.build_aggregate_result(self.paths)
        self.assertEqual(
            self.runner.canonical_json_bytes(first),
            self.runner.canonical_json_bytes(second),
        )
        required = {
            "phase_a",
            "dataset_evidence",
            "raw_csv_sha256",
            "configuration_sha256",
            "environment_lock_sha256",
            "feature_schema_sha256",
            "split_manifest_sha256",
            "crema_label_ledger",
            "model_settings",
            "metric_definitions",
            "non_lockbox_review_sha256",
            "lockbox",
            "decision",
            "closed_boundaries",
        }
        self.assertTrue(required.issubset(first))
        self.assertEqual(first["lockbox"]["open_count"], 1)
        self.assertEqual(
            set(first["closed_boundaries"]),
            {
                "private_data_allowed",
                "provider_operations_allowed",
                "network_during_evaluation_allowed",
                "source_adaptation_allowed",
                "runtime_influence_allowed",
                "customer_state_output_allowed",
            },
        )
        self.assertTrue(
            all(value is False for value in first["closed_boundaries"].values())
        )
        digest = hashlib.sha256(
            self.runner.canonical_json_bytes(first)
        ).hexdigest().upper()
        report_a = self.runner.render_report(first, digest)
        report_b = self.runner.render_report(deepcopy(first), digest)
        self.assertEqual(report_a, report_b)
        self.assertTrue(report_a.endswith("\n"))
        self.assertNotIn("\r", report_a)

    def test_stage_and_accept_publish_validated_pair_once(self) -> None:
        self._advance_to_lockbox()
        receipt = self.runner.stage_candidate(self.paths, "accept.json")
        self.assertEqual(
            self.runner.load_state(self.paths)["phase"],
            "awaiting_acceptance",
        )
        result_bytes, report_bytes = self._canonical_bytes()
        self.assertEqual(
            hashlib.sha256(result_bytes).hexdigest().upper(),
            receipt["result_sha256"],
        )
        self.assertEqual(
            hashlib.sha256(report_bytes).hexdigest().upper(),
            receipt["report_sha256"],
        )
        self.runner.accept_receipt(self.paths, self.paths.receipt_path("accept.json"))
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "accepted")
        self.assertEqual(self._canonical_bytes(), (result_bytes, report_bytes))
        self.assertFalse(self.paths.journal_path.exists())
        self.assertFalse(self.paths.receipt_path("accept.json").exists())

    def test_reject_restores_exact_previous_pair(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "reject.json")
        self.assertNotEqual(self._canonical_bytes(), previous)
        self.runner.reject_receipt(self.paths, self.paths.receipt_path("reject.json"))
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertFalse(self.paths.journal_path.exists())

    def test_reject_receipt_identity_tamper_retains_all_evidence(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "reject-tamper.json")
        candidate = self._canonical_bytes()
        receipt_path = self.paths.receipt_path("reject-tamper.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["report_sha256"] = self.DIGESTS[0]
        self._write_json(receipt_path, receipt)
        with self.assertRaisesRegex(self.runner.RunnerError, "receipt"):
            self.runner.reject_receipt(self.paths, receipt_path)
        self.assertNotEqual(candidate, previous)
        self.assertEqual(self._canonical_bytes(), candidate)
        self.assertEqual(
            self.runner.load_state(self.paths)["phase"],
            "awaiting_acceptance",
        )
        self.assertTrue(self.paths.journal_path.exists())
        self.assertTrue(receipt_path.exists())

    def test_recovery_finishes_interrupted_rejected_cleanup(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "cleanup-crash.json")
        original_cleanup = self.runner._cleanup_transaction
        failed_once = False

        def fail_cleanup_once(*args: Any, **kwargs: Any) -> None:
            nonlocal failed_once
            if not failed_once:
                failed_once = True
                raise OSError("synthetic cleanup crash")
            original_cleanup(*args, **kwargs)

        with patch.object(
            self.runner,
            "_cleanup_transaction",
            side_effect=fail_cleanup_once,
        ):
            with self.assertRaises(OSError):
                self.runner.reject_receipt(
                    self.paths,
                    self.paths.receipt_path("cleanup-crash.json"),
                )
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")
        self.assertTrue(self.paths.journal_path.exists())
        self.assertEqual(self.runner.recover_publication(self.paths), "restored")
        self.assertFalse(self.paths.journal_path.exists())

    def test_partial_previous_pair_fails_without_state_or_canonical_mutation(
        self,
    ) -> None:
        self.paths.result_path.write_bytes(b"partial\n")
        self._advance_to_lockbox()
        state_before = self._state_bytes()
        canonical_before = self._canonical_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "partial"):
            self.runner.stage_candidate(self.paths, "partial.json")
        self.assertEqual(self._state_bytes(), state_before)
        self.assertEqual(self._canonical_bytes(), canonical_before)
        self.assertFalse(self.paths.journal_path.exists())

    def test_extra_canonical_entry_fails_without_publication_mutation(self) -> None:
        self._advance_to_lockbox()
        extra = self.canonical_root / "unexpected.txt"
        extra.write_text("unexpected", encoding="utf-8")
        state_before = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "exactly"):
            self.runner.stage_candidate(self.paths, "extra.json")
        self.assertEqual(self._state_bytes(), state_before)
        self.assertEqual(extra.read_text(encoding="utf-8"), "unexpected")
        self.assertEqual(self._canonical_bytes(), (None, None))

    def test_accept_tampering_restores_previous_pair_and_rejects(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "tampered.json")
        self.paths.result_path.write_bytes(b'{"tampered":true}\n')
        with self.assertRaisesRegex(self.runner.RunnerError, "candidate"):
            self.runner.accept_receipt(
                self.paths,
                self.paths.receipt_path("tampered.json"),
            )
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")

    def test_accept_config_drift_restores_previous_pair(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "drift.json")
        self.config_path.write_bytes(self.config_path.read_bytes() + b" ")
        with self.assertRaisesRegex(self.runner.RunnerError, "configuration"):
            self.runner.accept_receipt(
                self.paths,
                self.paths.receipt_path("drift.json"),
            )
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")

    def test_accept_revalidates_config_semantics_and_restores_previous_pair(
        self,
    ) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "semantic.json")
        with patch.object(
            self.runner,
            "validate_config",
            side_effect=ValueError("synthetic semantic rejection"),
        ):
            with self.assertRaisesRegex(self.runner.RunnerError, "preflight"):
                self.runner.accept_receipt(
                    self.paths,
                    self.paths.receipt_path("semantic.json"),
                )
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")

    def test_accept_receipt_identity_tamper_retains_all_evidence(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "receipt-tamper.json")
        candidate = self._canonical_bytes()
        receipt_path = self.paths.receipt_path("receipt-tamper.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["result_sha256"] = self.DIGESTS[0]
        self._write_json(receipt_path, receipt)
        with self.assertRaisesRegex(self.runner.RunnerError, "receipt"):
            self.runner.accept_receipt(self.paths, receipt_path)
        self.assertNotEqual(candidate, previous)
        self.assertEqual(self._canonical_bytes(), candidate)
        self.assertEqual(
            self.runner.load_state(self.paths)["phase"],
            "awaiting_acceptance",
        )
        self.assertTrue(self.paths.journal_path.exists())
        self.assertTrue(receipt_path.exists())

    def test_accept_partial_candidate_restores_previous_pair(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "partial-candidate.json")
        self.paths.report_path.unlink()
        with self.assertRaisesRegex(self.runner.RunnerError, "partial"):
            self.runner.accept_receipt(
                self.paths,
                self.paths.receipt_path("partial-candidate.json"),
            )
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")

    def test_second_replace_fault_restores_exact_previous_pair(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        real_replace = self.runner._replace_entry_durably
        failed_once = False

        def fail_report_replace(
            source: os.PathLike[str] | str,
            destination: os.PathLike[str] | str,
        ) -> None:
            nonlocal failed_once
            if Path(destination) == self.paths.report_path and not failed_once:
                failed_once = True
                raise OSError("synthetic second replace crash")
            real_replace(Path(source), Path(destination))

        state_before = self._state_bytes()
        with patch.object(
            self.runner,
            "_replace_entry_durably",
            side_effect=fail_report_replace,
        ):
            with self.assertRaisesRegex(self.runner.RunnerError, "restored"):
                self.runner.stage_candidate(self.paths, "crash.json")
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self._state_bytes(), state_before)
        self.assertFalse(self.paths.journal_path.exists())

    def test_recovery_of_awaiting_transaction_restores_previous_pair(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "recovery.json")
        outcome = self.runner.recover_publication(self.paths)
        self.assertEqual(outcome, "restored")
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")
        self.assertFalse(self.paths.journal_path.exists())

    def test_malformed_journal_uses_receipt_for_rollback_only_recovery(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "journal.json")
        self.paths.journal_path.write_bytes(b'{"tampered":true}\n')
        self.assertEqual(self.runner.recover_publication(self.paths), "restored")
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")
        self.assertFalse(self.paths.journal_path.exists())

    def test_missing_journal_reconstructs_rollback_for_recovery(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "missing.json")
        self.paths.journal_path.unlink()
        self.assertEqual(self.runner.recover_publication(self.paths), "restored")
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")

    def test_missing_journal_reconstructs_rollback_for_reject(self) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "missing.json")
        self.paths.journal_path.unlink()
        self.runner.reject_receipt(
            self.paths,
            self.paths.receipt_path("missing.json"),
        )
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")

    def test_missing_journal_accept_and_identity_conflicts_retain_evidence(
        self,
    ) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "conflict.json")
        candidate = self._canonical_bytes()
        self.paths.journal_path.unlink()
        state_before = self._state_bytes()
        with self.assertRaises(self.runner.RunnerError):
            self.runner.accept_receipt(
                self.paths,
                self.paths.receipt_path("conflict.json"),
            )
        self.assertNotEqual(candidate, previous)
        self.assertEqual(self._canonical_bytes(), candidate)
        self.assertEqual(self._state_bytes(), state_before)
        self.assertTrue(self.paths.receipt_path("conflict.json").exists())

    def test_recovery_rejects_journal_state_identity_mismatch(self) -> None:
        self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "identity.json")
        candidate = self._canonical_bytes()
        state = self.runner.load_state(self.paths)
        state["candidate_transaction_id"] = "f" * 32
        self._write_json(self.paths.state_path, state)
        state_before = self._state_bytes()
        with self.assertRaisesRegex(self.runner.RunnerError, "identity"):
            self.runner.recover_publication(self.paths)
        self.assertEqual(self._canonical_bytes(), candidate)
        self.assertEqual(self._state_bytes(), state_before)
        self.assertTrue(self.paths.journal_path.exists())

    def test_output_roots_and_publication_lock_fail_closed(self) -> None:
        outside_canonical = self.root.parent / f"{self.root.name}-canonical"
        outside_canonical.mkdir()
        self.addCleanup(outside_canonical.rmdir)
        escaped_paths = self._paths(canonical_root=outside_canonical)
        self._advance_to_lockbox()
        with self.assertRaisesRegex(self.runner.RunnerError, "canonical root"):
            self.runner.stage_candidate(escaped_paths, "escape.json")

        state_before = self._state_bytes()
        canonical_before = self._canonical_bytes()
        with self.runner.publication_lock(self.paths):
            with self.assertRaisesRegex(self.runner.RunnerError, "lock"):
                self.runner.stage_candidate(self.paths, "locked.json")
        self.assertEqual(self._state_bytes(), state_before)
        self.assertEqual(self._canonical_bytes(), canonical_before)

    def test_publication_lock_rejects_mocked_reparse_entry(self) -> None:
        self._advance_to_lockbox()
        self.paths.recovery_root.mkdir(parents=True, exist_ok=True)
        self.paths.recovery_root.joinpath(self.runner.LOCK_NAME).write_bytes(b"\0")
        real_lstat = os.lstat

        def fake_lstat(path: os.PathLike[str] | str) -> Any:
            status = real_lstat(path)
            if Path(path) == self.paths.recovery_root / self.runner.LOCK_NAME:
                return SimpleNamespace(
                    st_mode=status.st_mode,
                    st_file_attributes=getattr(
                        stat,
                        "FILE_ATTRIBUTE_REPARSE_POINT",
                        0x400,
                    ),
                    st_dev=status.st_dev,
                    st_ino=status.st_ino,
                )
            return status

        state_before = self._state_bytes()
        with patch.object(self.runner.os, "lstat", side_effect=fake_lstat):
            with self.assertRaisesRegex(self.runner.RunnerError, "reparse"):
                self.runner.stage_candidate(self.paths, "reparse-lock.json")
        self.assertEqual(self._state_bytes(), state_before)
        self.assertEqual(self._canonical_bytes(), (None, None))

    def test_review_critical_callbacks_are_not_a_production_interface(self) -> None:
        self.assertNotIn(
            "operation",
            inspect.signature(self.runner.run_non_lockbox).parameters,
        )
        self.assertNotIn(
            "operation",
            inspect.signature(self.runner.run_lockbox).parameters,
        )

    def test_review_critical_input_ledger_binds_exact_accepted_evidence(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_phase_b_input_ledger,
        )

        mutated = deepcopy(self.input_ledger)
        mutated["phase_a"]["commit"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "Phase A"):
            validate_phase_b_input_ledger(mutated)

    def test_review_critical_every_runner_contract_leaf_and_shape_is_bound(
        self,
    ) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_lockbox_result,
            validate_non_lockbox_packet,
            validate_phase_b_input_ledger,
        )

        contracts = (
            (self.input_ledger, validate_phase_b_input_ledger),
            (self.non_lockbox_packet, validate_non_lockbox_packet),
            (self.lockbox_result, validate_lockbox_result),
        )
        for payload, validator in contracts:
            validator(deepcopy(payload))
            for path in PhaseBContractTests._scalar_paths(payload):
                mutated = deepcopy(payload)
                current = PhaseBContractTests._value_at(mutated, path)
                PhaseBContractTests._replace_at(
                    mutated,
                    path,
                    PhaseBContractTests._different_value(current),
                )
                with self.subTest(validator=validator.__name__, leaf=path):
                    with self.assertRaises((TypeError, ValueError)):
                        validator(mutated)
            for path in PhaseBContractTests._mapping_paths(payload):
                mapping = PhaseBContractTests._value_at(payload, path)
                mutated = deepcopy(payload)
                PhaseBContractTests._value_at(mutated, path)[
                    "unexpected_field"
                ] = True
                with self.subTest(validator=validator.__name__, unknown=path):
                    with self.assertRaises((TypeError, ValueError)):
                        validator(mutated)
                for key in mapping:
                    mutated = deepcopy(payload)
                    del PhaseBContractTests._value_at(mutated, path)[key]
                    with self.subTest(
                        validator=validator.__name__,
                        missing=path + (key,),
                    ):
                        with self.assertRaises((TypeError, ValueError)):
                            validator(mutated)

    def test_review_critical_canonical_mutations_and_free_decision_reject(
        self,
    ) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            validate_phase_b_result,
        )

        self._advance_to_lockbox()
        result = self.runner.build_aggregate_result(self.paths)
        validate_phase_b_result(deepcopy(result))
        for path in PhaseBContractTests._scalar_paths(result):
            mutated = deepcopy(result)
            current = PhaseBContractTests._value_at(mutated, path)
            PhaseBContractTests._replace_at(
                mutated,
                path,
                PhaseBContractTests._different_value(current),
            )
            with self.subTest(leaf=path):
                with self.assertRaises((TypeError, ValueError)):
                    validate_phase_b_result(mutated)
        for forbidden in (
            "row_records",
            "actor_id",
            "participant_id",
            "meeting_id",
            "filename",
            "local_path",
            "transcript_text",
            "probability_rows",
            "fitted_model",
        ):
            mutated = deepcopy(result)
            mutated["lockbox"][forbidden] = [{"value": "forbidden"}]
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(ValueError):
                    validate_phase_b_result(mutated)
        mutated = deepcopy(result)
        alternatives = {
            "keep_for_research_only",
            "revise",
            "discard",
        } - {result["decision"]}
        mutated["decision"] = sorted(alternatives)[0]
        with self.assertRaisesRegex(ValueError, "decision"):
            validate_phase_b_result(mutated)

    def test_task_9_every_result_shape_leaf_and_renderer_line_fails_closed(
        self,
    ) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self.assertTrue(
            hasattr(validator, "validate_publication_pair_bytes"),
            "Task 9 publication-pair validator is missing",
        )
        validate_publication_pair_bytes = validator.validate_publication_pair_bytes

        self._advance_to_lockbox()
        receipt = self.runner.stage_candidate(self.paths, "shape-review.json")
        result_bytes, report_bytes = self._canonical_bytes()
        self.assertIsNotNone(result_bytes)
        self.assertIsNotNone(report_bytes)
        assert result_bytes is not None
        assert report_bytes is not None
        result = json.loads(result_bytes.decode("utf-8"))
        self.assertEqual(
            validate_publication_pair_bytes(result_bytes, report_bytes),
            result,
        )

        for path in PhaseBContractTests._scalar_paths(result):
            mutated = deepcopy(result)
            current = PhaseBContractTests._value_at(mutated, path)
            PhaseBContractTests._replace_at(
                mutated,
                path,
                PhaseBContractTests._different_value(current),
            )
            with self.subTest(leaf=path):
                with self.assertRaises((TypeError, ValueError)):
                    validate_publication_pair_bytes(
                        self.runner.canonical_json_bytes(mutated),
                        report_bytes,
                    )

        for path in PhaseBContractTests._mapping_paths(result):
            mapping = PhaseBContractTests._value_at(result, path)
            for key in mapping:
                mutated = deepcopy(result)
                del PhaseBContractTests._value_at(mutated, path)[key]
                with self.subTest(missing=path + (key,)):
                    with self.assertRaises((TypeError, ValueError)):
                        validate_publication_pair_bytes(
                            self.runner.canonical_json_bytes(mutated),
                            report_bytes,
                        )
            mutated = deepcopy(result)
            PhaseBContractTests._value_at(mutated, path)["unexpected_field"] = True
            with self.subTest(unexpected=path):
                with self.assertRaises((TypeError, ValueError)):
                    validate_publication_pair_bytes(
                        self.runner.canonical_json_bytes(mutated),
                        report_bytes,
                    )

        report_lines = report_bytes.decode("utf-8").splitlines(keepends=True)
        json_start = report_lines.index("```json\n")
        renderer_lines = [
            index
            for index, line in enumerate(report_lines[:json_start])
            if line.strip()
        ]
        self.assertEqual(len(renderer_lines), 6)
        for index in renderer_lines:
            mutated_lines = list(report_lines)
            mutated_lines[index] = (
                mutated_lines[index].rstrip("\n") + " mutated\n"
            )
            with self.subTest(renderer_line=report_lines[index].strip()):
                with self.assertRaisesRegex(ValueError, "report"):
                    validate_publication_pair_bytes(
                        result_bytes,
                        "".join(mutated_lines).encode("utf-8"),
                    )

        self.assertRegex(receipt["result_sha256"], r"^[0-9A-F]{64}$")
        self.assertRegex(receipt["report_sha256"], r"^[0-9A-F]{64}$")

    def test_task_9_candidate_receipt_hashes_fail_closed(self) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self.assertTrue(
            hasattr(validator, "validate_candidate_readback"),
            "Task 9 candidate validator is missing",
        )
        validate_candidate_readback = validator.validate_candidate_readback

        self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "hash-review.json")
        receipt_path = self.paths.receipt_path("hash-review.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_candidate_readback(self.paths, receipt_path)
        hash_fields = tuple(
            field for field, value in receipt.items()
            if field.endswith("_sha256") and isinstance(value, str)
        )
        self.assertEqual(
            set(hash_fields),
            {
                "configuration_sha256",
                "result_sha256",
                "report_sha256",
                "previous_result_sha256",
                "previous_report_sha256",
            },
        )
        for field in hash_fields:
            mutated = deepcopy(receipt)
            mutated[field] = (
                "B" * 64 if mutated[field] == "A" * 64 else "A" * 64
            )
            self._write_json(receipt_path, mutated)
            with self.subTest(hash_field=field):
                with self.assertRaises((RuntimeError, ValueError)):
                    validate_candidate_readback(self.paths, receipt_path)
            self._write_json(receipt_path, receipt)
        validate_candidate_readback(self.paths, receipt_path)

    def test_task_9_candidate_rebuilds_every_state_bound_digest_and_report(
        self,
    ) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "state-bound-review.json")
        receipt_path = self.paths.receipt_path("state-bound-review.json")
        result = json.loads(self.paths.result_path.read_text(encoding="utf-8"))
        baseline = {
            "result": self.paths.result_path.read_bytes(),
            "report": self.paths.report_path.read_bytes(),
            "journal": self.paths.journal_path.read_bytes(),
            "receipt": receipt_path.read_bytes(),
        }
        digest_paths = tuple(
            path
            for path in PhaseBContractTests._scalar_paths(result)
            if (
                isinstance(PhaseBContractTests._value_at(result, path), str)
                and re.fullmatch(
                    r"[0-9A-F]{64}",
                    PhaseBContractTests._value_at(result, path),
                )
                and any(
                    isinstance(component, str)
                    and component.endswith("_sha256")
                    for component in path
                )
            )
        )
        required_state_bound_paths = {
            ("split_manifest_sha256",),
            ("non_lockbox_review_sha256",),
            ("lockbox", "reservation_sha256"),
            ("lockbox", "result_sha256"),
            ("lockbox", "decision_evidence_sha256"),
            ("lockbox", "decision_evidence_mint_sha256"),
            ("lockbox", "ami", "source_commitment_sha256"),
        }
        self.assertTrue(required_state_bound_paths.issubset(set(digest_paths)))

        for path in digest_paths:
            mutated = deepcopy(result)
            current = PhaseBContractTests._value_at(mutated, path)
            alternative = "B" * 64 if current != "B" * 64 else "A" * 64
            PhaseBContractTests._replace_at(mutated, path, alternative)
            _result_bytes, report_bytes = (
                self._write_mutually_consistent_candidate_assertions(
                    self.paths,
                    mutated,
                )
            )
            with self.subTest(state_bound_digest=path):
                with patch.object(
                    self.runner,
                    "render_report",
                    return_value=report_bytes.decode("utf-8"),
                ):
                    with self.assertRaises((RuntimeError, ValueError)):
                        validator.validate_candidate_readback(
                            self.paths,
                            receipt_path,
                        )
            self.paths.result_path.write_bytes(baseline["result"])
            self.paths.report_path.write_bytes(baseline["report"])
            self.paths.journal_path.write_bytes(baseline["journal"])
            receipt_path.write_bytes(baseline["receipt"])

        forged_report = baseline["report"].replace(
            b"- Final lockbox open count: `1`\n",
            b"- Final lockbox open count: `01`\n",
        )
        self.paths.report_path.write_bytes(forged_report)
        transaction = json.loads(
            self.paths.journal_path.read_text(encoding="utf-8")
        )
        transaction["candidate_pair"]["report_sha256"] = (
            hashlib.sha256(forged_report).hexdigest().upper()
        )
        self._write_json(self.paths.journal_path, transaction)
        self._write_json(
            receipt_path,
            self.runner._receipt_from_transaction(transaction),
        )
        with patch.object(
            self.runner,
            "render_report",
            return_value=forged_report.decode("utf-8"),
        ):
            with self.assertRaisesRegex(ValueError, "report"):
                validator.validate_candidate_readback(self.paths, receipt_path)

    def test_task_9_candidate_authority_blocks_lifecycle_interleavings(
        self,
    ) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "interleaving-review.json")
        original_validator = validator.validate_publication_pair_bytes
        for operation in ("accept", "reject", "cleanup"):
            with tempfile.TemporaryDirectory() as directory:
                clone_paths = self._clone_paths(
                    Path(directory).resolve() / "clone"
                )
                receipt_path = clone_paths.receipt_path(
                    "interleaving-review.json"
                )
                observation: list[str] = []

                def interleave(
                    result_bytes: bytes,
                    report_bytes: bytes,
                ) -> dict[str, Any]:
                    if operation == "accept":
                        try:
                            self.runner.accept_receipt(
                                clone_paths,
                                receipt_path,
                            )
                        except self.runner.RunnerError:
                            observation.append("blocked")
                        else:
                            observation.append("accepted")
                    elif operation == "reject":
                        try:
                            self.runner.reject_receipt(
                                clone_paths,
                                receipt_path,
                            )
                        except self.runner.RunnerError:
                            observation.append("blocked")
                        else:
                            observation.append("rejected")
                    else:
                        clone_paths.journal_path.unlink()
                        receipt_path.unlink()
                        observation.append("cleaned")
                    return original_validator(result_bytes, report_bytes)

                before = self._snapshot_publication_bytes(clone_paths)
                with patch.object(
                    validator,
                    "validate_publication_pair_bytes",
                    side_effect=interleave,
                ):
                    if operation == "cleanup":
                        with self.subTest(operation=operation):
                            with self.assertRaises(
                                (RuntimeError, ValueError)
                            ):
                                validator.validate_candidate_readback(
                                    clone_paths,
                                    receipt_path,
                                )
                    else:
                        with self.subTest(operation=operation):
                            validator.validate_candidate_readback(
                                clone_paths,
                                receipt_path,
                            )
                            self.assertEqual(observation, ["blocked"])
                            self.assertEqual(
                                self.runner.load_state(clone_paths)["phase"],
                                "awaiting_acceptance",
                            )
                            self.assertTrue(clone_paths.journal_path.is_file())
                            self.assertTrue(receipt_path.is_file())
                            self.assertEqual(
                                self._snapshot_publication_bytes(clone_paths),
                                before,
                            )

        with tempfile.TemporaryDirectory() as directory:
            empty_lock_paths = self._clone_paths(
                Path(directory).resolve() / "empty-lock-clone"
            )
            lock_path = (
                empty_lock_paths.recovery_root / self.runner.LOCK_NAME
            )
            lock_path.write_bytes(b"")
            try:
                validator.validate_candidate_readback(
                    empty_lock_paths,
                    empty_lock_paths.receipt_path("interleaving-review.json"),
                )
            except self.runner.RunnerError:
                pass
            self.assertEqual(
                lock_path.read_bytes(),
                b"",
                "read-only candidate validation initialized the lock file",
            )

    def test_task_9_output_projection_and_nested_scanner_are_fail_closed(
        self,
    ) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "projection-review.json")
        result_bytes, report_bytes = self._canonical_bytes()
        assert result_bytes is not None
        assert report_bytes is not None
        result = json.loads(result_bytes.decode("utf-8"))
        self.assertEqual(
            result["raw_csv_sha256"],
            {
                "finished_response_votes": (
                    self.input_ledger["raw_csv_sha256"][
                        "finishedResponses.csv"
                    ]
                ),
                "summary_voice_votes": (
                    self.input_ledger["raw_csv_sha256"][
                        "processedResults/summaryTable.csv"
                    ]
                ),
            },
        )
        self.assertEqual(
            set(self.input_ledger["raw_csv_sha256"]),
            {
                "finishedResponses.csv",
                "processedResults/summaryTable.csv",
            },
        )
        combined = result_bytes + b"\n" + report_bytes
        self.assertNotIn(b".csv", combined.lower())
        validator.validate_candidate_output_bytes(combined)

        forbidden_payloads = {
            "posix-path": {"value": "/etc/passwd"},
            "posix-root-path": {"value": "/secret"},
            "windows-path": {"value": r"C:\Users\private\artifact"},
            "unc-path": {"value": r"\\server\share\artifact"},
            "broad-filename": {"value": "private.parquet"},
            "speaker-container": {"metadata": {"speaker": "S01"}},
            "participant-container": {
                "metadata": {"participantIdentifiers": ["P01"]}
            },
            "meeting-container": {"meeting": {"id": "M01"}},
            "row-container": {"payload": {"items": [{"row_id": 1}]}},
            "row-array": {"rows": [{"value": 1}]},
            "transcript": {
                "metadata": {"transcript_lines": ["private words"]}
            },
            "audio-encoding": {"metadata": {"audio_base64": "UklGRg=="}},
            "audio-marker": {"value": "RIFF-WAVE"},
            "model-state": {"metadata": {"model_state": "opaque"}},
            "model-serialization": {
                "metadata": {"serialized_estimator": "opaque"}
            },
            "probability": {"metadata": {"class_probability": 0.9}},
            "probabilities": {
                "metadata": {"class_probabilities": [0.1, 0.9]}
            },
            "credential": {"metadata": {"client_secret": "secret-value"}},
            "credential-token": {
                "metadata": {"refresh_token": "secret-value"}
            },
        }
        for output_class, payload in forbidden_payloads.items():
            with self.subTest(output_class=output_class):
                with self.assertRaisesRegex(ValueError, "forbidden output"):
                    validator.validate_candidate_output_bytes(
                        self.runner.canonical_json_bytes(payload)
                    )
        for output_class, encoded_payload in {
            "decoded-posix-path": b'{"value":"\\u002fetc\\u002fpasswd"}',
            "decoded-filename": b'{"value":"private\\u002eparquet"}',
        }.items():
            with self.subTest(output_class=output_class):
                with self.assertRaisesRegex(ValueError, "forbidden output"):
                    validator.validate_candidate_output_bytes(encoded_payload)

        for signal in (
            "hesitation",
            "frustration",
            "confusion",
            "interest",
            "disengagement",
        ):
            with self.subTest(signal=signal):
                with self.assertRaisesRegex(ValueError, "forbidden output"):
                    validator.validate_candidate_output_bytes(
                        self.runner.canonical_json_bytes({"value": signal})
                    )

        safe_near_misses = {
            "speaker_balance_normalized_entropy": 0.5,
            "unique_actor_count": 10,
            "meeting_count": 5,
            "row_commitment_sha256": "A" * 64,
            "model_settings": {"regularization": "l2"},
            "probabilistic_metric": "multiclass_brier",
            "audio_feature_count": 17,
            "interesting_result": False,
        }
        validator.validate_candidate_output_bytes(
            self.runner.canonical_json_bytes(safe_near_misses)
        )

    def test_task_9_synthetic_candidate_bytes_exclude_every_forbidden_class(
        self,
    ) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self.assertTrue(
            hasattr(validator, "validate_candidate_output_bytes"),
            "Task 9 output-leakage validator is missing",
        )
        validate_candidate_output_bytes = validator.validate_candidate_output_bytes

        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "leakage-review.json")
        result_bytes, report_bytes = self._canonical_bytes()
        self.assertIsNotNone(result_bytes)
        self.assertIsNotNone(report_bytes)
        assert result_bytes is not None
        assert report_bytes is not None
        candidate_bytes = result_bytes + b"\n" + report_bytes
        validate_candidate_output_bytes(candidate_bytes)

        forbidden_markers = {
            "absolute_paths": (
                str(self.root).encode("utf-8"),
                str(ROOT).encode("utf-8"),
                b"C:\\Users\\synthetic\\private\\clip.wav",
            ),
            "timestamps": (b"2030-01-02T03:04:05Z",),
            "filenames": (b"synthetic_clip_0001.wav",),
            "stems": (b"1001_DFA_ANG_XX",),
            "actor_speaker_participant_ids": (
                b'"actor_id":"A01"',
                b'"speaker_id":"S01"',
                b'"participant_id":"P01"',
            ),
            "row_arrays": (b'"row_records":[{"row_id":1}]',),
            "transcripts": (b'"transcript_text":"private words"',),
            "audio_markers": (b'"audio_bytes":"RIFF-WAVE"',),
            "model_serialization": (b'"fitted_model":"pickle"',),
            "probabilities": (b'"probabilities":[0.1,0.9]',),
            "credentials": (b'"api_key":"synthetic-secret"',),
            "operational_signals": (
                b"hesitation",
                b"frustration",
                b"confusion",
                b"interest",
                b"disengagement",
            ),
        }
        lowered_candidate = candidate_bytes.lower()
        for output_class, markers in forbidden_markers.items():
            for marker in markers:
                with self.subTest(output_class=output_class, marker=marker):
                    self.assertNotIn(marker.lower(), lowered_candidate)
                    with self.assertRaisesRegex(ValueError, "forbidden output"):
                        validate_candidate_output_bytes(
                            candidate_bytes + b"\n" + marker
                        )

    def test_task_9_candidate_and_checkpoint_lifecycle_is_injected_and_read_only(
        self,
    ) -> None:
        from scripts import validate_emotion_state_002_phase_b as validator

        self.assertTrue(
            hasattr(validator, "validate_candidate_readback")
            and hasattr(validator, "validate_checkpoint_readback"),
            "Task 9 candidate/checkpoint lifecycle validators are missing",
        )
        validate_candidate_readback = validator.validate_candidate_readback
        validate_checkpoint_readback = validator.validate_checkpoint_readback

        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "lifecycle.json")
        receipt_path = self.paths.receipt_path("lifecycle.json")
        before_candidate = (
            self._state_bytes(),
            self._canonical_bytes(),
            self.paths.journal_path.read_bytes(),
            receipt_path.read_bytes(),
        )
        validate_candidate_readback(self.paths, receipt_path)
        self.assertEqual(
            (
                self._state_bytes(),
                self._canonical_bytes(),
                self.paths.journal_path.read_bytes(),
                receipt_path.read_bytes(),
            ),
            before_candidate,
        )
        with self.assertRaisesRegex(ValueError, "accepted"):
            validate_checkpoint_readback(self.paths)

        self.runner.accept_receipt(self.paths, receipt_path)
        before_checkpoint = (self._state_bytes(), self._canonical_bytes())
        validate_checkpoint_readback(self.paths)
        self.assertEqual(
            (self._state_bytes(), self._canonical_bytes()),
            before_checkpoint,
        )
        with self.assertRaisesRegex(ValueError, "awaiting_acceptance"):
            validate_candidate_readback(self.paths, receipt_path)

        residual_receipt = self.paths.recovery_root / "residual-receipt.json"
        residual_receipt.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "residual"):
            validate_checkpoint_readback(self.paths)

    def test_review_critical_independent_process_lockbox_concurrency(self) -> None:
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)
        marker = self.root / "lockbox-entries.txt"
        processes = [
            self._lockbox_subprocess("normal", marker),
            self._lockbox_subprocess("normal", marker),
        ]
        results = [process.communicate(timeout=60) for process in processes]
        return_codes = [process.returncode for process in processes]
        self.assertEqual(sorted(return_codes), [0, 2], results)
        self.assertEqual(marker.read_text(encoding="utf-8"), "entered\n")
        self.assertEqual(
            self.runner.load_state(self.paths)["lockbox_open_count"],
            1,
        )

    def test_review_critical_lockbox_reentry_cannot_enter_twice(self) -> None:
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)
        original = self.runner.validate_lockbox_ami_input
        attempted_reentry = False
        logical_entries = 0

        def attempt_reentry(payload: Any) -> Any:
            nonlocal attempted_reentry, logical_entries
            if not attempted_reentry:
                attempted_reentry = True
                logical_entries += 1
                with self.assertRaisesRegex(self.runner.RunnerError, "lockbox"):
                    self.runner._run_lockbox_with_private_evidence_for_testing(
                        self.paths,
                        self.DECISION_ARTIFACT,
                    )
            return original(payload)

        with patch.object(
            self.runner,
            "validate_lockbox_ami_input",
            side_effect=attempt_reentry,
        ):
            self.runner._run_lockbox_with_private_evidence_for_testing(
                self.paths,
                self.DECISION_ARTIFACT,
            )
        self.assertTrue(attempted_reentry)
        self.assertEqual(logical_entries, 1)
        self.assertEqual(
            self.runner.load_state(self.paths)["lockbox_open_count"],
            1,
        )

    def test_review_critical_crash_before_and_after_reservation_fail_closed(
        self,
    ) -> None:
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)
        marker = self.root / "lockbox-crash-entries.txt"
        before = self._lockbox_subprocess(
            "crash_before_reservation",
            marker,
        )
        before.communicate(timeout=60)
        self.assertEqual(before.returncode, 72)
        self.assertFalse(self.paths.lockbox_reservation_path.exists())

        after = self._lockbox_subprocess("crash_after_reservation", marker)
        after.communicate(timeout=60)
        self.assertEqual(after.returncode, 73)
        reservation = json.loads(
            self.paths.lockbox_reservation_path.read_text(encoding="utf-8")
        )
        self.assertEqual(reservation["status"], "reserved")
        self.assertEqual(marker.read_text(encoding="utf-8"), "entered\n")
        refused = self._lockbox_subprocess("normal", marker)
        refused.communicate(timeout=60)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(marker.read_text(encoding="utf-8"), "entered\n")
        self.assertEqual(
            self.runner.load_state(self.paths)["phase"],
            "non_lockbox_complete",
        )

    def test_review_important_anchor_is_revalidated_before_transition(self) -> None:
        self.runner.run_preflight(self.paths)
        state_before = self._state_bytes()
        original_validator = self.runner.validate_non_lockbox_packet

        def mutate_anchor(payload: Any) -> Any:
            validated = original_validator(payload)
            self.config_path.write_bytes(self.config_path.read_bytes() + b" ")
            return validated

        with patch.object(
            self.runner,
            "validate_non_lockbox_packet",
            side_effect=mutate_anchor,
        ):
            with self.assertRaisesRegex(self.runner.RunnerError, "configuration"):
                self.runner.run_non_lockbox(self.paths)
        self.assertEqual(self._state_bytes(), state_before)

    def test_review_important_every_non_lockbox_anchor_is_revalidated(self) -> None:
        anchors = (
            self.config_path,
            self.environment_lock_path,
            self.feature_schema_path,
            self.split_schema_path,
            self.split_manifest_path,
            self.input_ledger_path,
            self.non_lockbox_packet_path,
        )
        for index, anchor in enumerate(anchors):
            if index:
                self._write_json(
                    self.paths.state_path,
                    self.runner._initial_state(),
                )
            self.runner.run_preflight(self.paths)
            state_before = self._state_bytes()
            original = anchor.read_bytes()
            original_validator = self.runner.validate_non_lockbox_packet
            mutated = False

            def mutate_anchor(payload: Any) -> Any:
                nonlocal mutated
                validated = original_validator(payload)
                if not mutated:
                    anchor.write_bytes(original + b" ")
                    mutated = True
                return validated

            try:
                with patch.object(
                    self.runner,
                    "validate_non_lockbox_packet",
                    side_effect=mutate_anchor,
                ):
                    with self.subTest(anchor=anchor.name):
                        with self.assertRaises(self.runner.RunnerError):
                            self.runner.run_non_lockbox(self.paths)
                self.assertEqual(self._state_bytes(), state_before)
            finally:
                anchor.write_bytes(original)

    def test_review_important_lockbox_result_change_before_binding_invalidates(
        self,
    ) -> None:
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)
        state_before = self._state_bytes()
        original = self.runner._replace_bytes_durably
        mutated = False

        def mutate_result(path: Path, content: bytes) -> None:
            nonlocal mutated
            original(path, content)
            if Path(path) == self.lockbox_result_path and not mutated:
                self.lockbox_result_path.write_bytes(content + b" ")
                mutated = True

        with patch.object(
            self.runner,
            "_replace_bytes_durably",
            side_effect=mutate_result,
        ):
            with self.assertRaisesRegex(self.runner.RunnerError, "changed"):
                self.runner._run_lockbox_with_private_evidence_for_testing(
                    self.paths,
                    self.DECISION_ARTIFACT,
                )
        self.assertEqual(self._state_bytes(), state_before)
        reservation = json.loads(
            self.paths.lockbox_reservation_path.read_text(encoding="utf-8")
        )
        self.assertEqual(reservation["status"], "reserved")

    def test_review_important_post_awaiting_fault_is_terminally_recoverable(
        self,
    ) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        original_write_state = self.runner._write_state
        failed_once = False

        def fail_after_awaiting(
            paths: Any,
            state: dict[str, Any],
        ) -> dict[str, Any]:
            nonlocal failed_once
            written = original_write_state(paths, state)
            if state["phase"] == "awaiting_acceptance" and not failed_once:
                failed_once = True
                raise OSError("synthetic post-awaiting durability fault")
            return written

        with patch.object(
            self.runner,
            "_write_state",
            side_effect=fail_after_awaiting,
        ):
            with self.assertRaisesRegex(self.runner.RunnerError, "restored"):
                self.runner.stage_candidate(self.paths, "post-awaiting.json")
        self.assertEqual(self._canonical_bytes(), previous)
        self.assertEqual(self.runner.load_state(self.paths)["phase"], "rejected")
        self.assertEqual(self.runner.recover_publication(self.paths), "none")

    def test_review_important_real_process_crash_at_stage_durable_boundaries(
        self,
    ) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        targets = (
            "candidate_result",
            "candidate_report",
            "backup_result",
            "backup_report",
            "journal",
            "canonical_result",
            "canonical_report",
            "receipt",
            "awaiting_state",
        )
        for target in targets:
            for timing in ("before", "after"):
                with tempfile.TemporaryDirectory() as directory:
                    clone_root = Path(directory).resolve() / "clone"
                    paths = self._clone_paths(clone_root)
                    crashed = self._stage_crash_subprocess(
                        paths,
                        target,
                        timing,
                    )
                    with self.subTest(target=target, timing=timing):
                        self.assertEqual(crashed.returncode, 86, crashed.stderr)
                        recovery = self.runner.recover_publication(paths)
                        self.assertIn(
                            recovery,
                            {
                                "discarded_unjournaled",
                                "restored",
                                "none",
                            },
                        )
                        self.assertEqual(
                            (
                                paths.result_path.read_bytes(),
                                paths.report_path.read_bytes(),
                            ),
                            previous,
                        )
                        expected_phase = (
                            "rejected"
                            if target == "awaiting_state" and timing == "after"
                            else "lockbox_complete"
                        )
                        self.assertEqual(
                            self.runner.load_state(paths)["phase"],
                            expected_phase,
                        )
                        self.assertFalse(paths.journal_path.exists())
                        residual = {
                            entry.name
                            for entry in paths.recovery_root.iterdir()
                            if entry.name != self.runner.LOCK_NAME
                        }
                        self.assertEqual(residual, set())

    def test_review_important_real_process_crash_at_accept_and_cleanup_boundaries(
        self,
    ) -> None:
        previous = self._install_previous_pair()
        self._advance_to_lockbox()
        self.runner.stage_candidate(self.paths, "accept.json")
        candidate = self._canonical_bytes()
        targets = (
            "accepted_journal",
            "accepted_state",
            "cleanup_result_backup",
            "cleanup_report_backup",
            "cleanup_receipt",
            "cleanup_journal",
        )
        for target in targets:
            for timing in ("before", "after"):
                with tempfile.TemporaryDirectory() as directory:
                    clone_root = Path(directory).resolve() / "clone"
                    paths = self._clone_paths(clone_root)
                    crashed = self._accept_crash_subprocess(
                        paths,
                        target,
                        timing,
                    )
                    with self.subTest(target=target, timing=timing):
                        self.assertEqual(crashed.returncode, 87, crashed.stderr)
                        recovery = self.runner.recover_publication(paths)
                        expected_rejected = (
                            target == "accepted_journal" and timing == "before"
                        )
                        self.assertIn(
                            recovery,
                            {"accepted", "restored", "none"},
                        )
                        expected_pair = previous if expected_rejected else candidate
                        self.assertEqual(
                            (
                                paths.result_path.read_bytes(),
                                paths.report_path.read_bytes(),
                            ),
                            expected_pair,
                        )
                        self.assertEqual(
                            self.runner.load_state(paths)["phase"],
                            "rejected" if expected_rejected else "accepted",
                        )
                        residual = {
                            entry.name
                            for entry in paths.recovery_root.iterdir()
                            if entry.name != self.runner.LOCK_NAME
                        }
                        self.assertEqual(residual, set())

    def test_review_important_receipt_binds_previous_pair(self) -> None:
        self._install_previous_pair()
        self._advance_to_lockbox()
        receipt = self.runner.stage_candidate(self.paths, "previous.json")
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "transaction_id",
                "configuration_sha256",
                "result_sha256",
                "report_sha256",
                "previous_pair_present",
                "previous_result_sha256",
                "previous_report_sha256",
            },
        )
        self.assertIs(receipt["previous_pair_present"], True)
        self.assertRegex(receipt["previous_result_sha256"], r"^[0-9A-F]{64}$")
        self.assertRegex(receipt["previous_report_sha256"], r"^[0-9A-F]{64}$")

    def test_review_important_durability_has_directory_barrier(self) -> None:
        self.assertTrue(callable(self.runner._sync_directory))
        self.assertTrue(callable(self.runner._durable_unlink))

    def test_review_important_cli_rejects_root_authority_overrides(self) -> None:
        with self.assertRaises(SystemExit):
            self.runner.parse_args(
                ["preflight", "--state-root", str(self.state_root)]
            )
        production = self.runner._paths_from_args(
            self.runner.parse_args(["preflight"])
        )
        self.assertEqual(production, self.runner.RunnerPaths.production())
        metadata_paths = self._paths(state_root=self.root / ".git")
        with self.assertRaisesRegex(self.runner.RunnerError, "metadata"):
            self.runner.run_preflight(metadata_paths)

    def test_second_review_lockbox_authority_requires_private_mint(
        self,
    ) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            canonical_payload_sha256,
            derive_phase_b_decision,
        )

        original_decision = derive_phase_b_decision(self.DECISION_EVIDENCE)
        forged = deepcopy(self.lockbox_result)
        evidence = forged["decision_evidence"]
        evidence["models"]["sentence_id"]["macro_f1"] = evidence["models"][
            "acoustic"
        ]["macro_f1"]
        evidence["paired_macro_f1_lift"]["sentence_id"][
            "point_estimate"
        ] = 0.0
        evidence["sentence_driven_apparent_lift"] = (
            evidence["models"]["sentence_id"]["macro_f1"]
            > evidence["models"]["class_prior"]["macro_f1"]
        )
        evidence["self_sha256"] = canonical_payload_sha256(evidence)
        self.assertNotEqual(
            derive_phase_b_decision(forged["decision_evidence"]),
            original_decision,
        )
        self._write_json(self.lockbox_result_path, forged)
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)

        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "private.*mint|evaluator.*not wired",
        ):
            self.runner.run_lockbox(self.paths)
        self.assertFalse(self.paths.lockbox_reservation_path.exists())
        self.assertEqual(
            self.runner.load_state(self.paths)["phase"],
            "non_lockbox_complete",
        )

    def test_second_review_private_synthetic_mint_is_bound_into_state(
        self,
    ) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            _canonical_digest,
            derive_phase_b_decision,
        )

        self.assertTrue(
            callable(
                getattr(
                    self.runner,
                    "_run_lockbox_with_private_evidence_for_testing",
                    None,
                )
            )
        )
        self._write_json(
            self.lockbox_result_path,
            {
                "schema_version": 1,
                "ami": deepcopy(self.lockbox_result["ami"]),
            },
        )
        self.runner.run_preflight(self.paths)
        self.runner.run_non_lockbox(self.paths)
        state = self.runner._run_lockbox_with_private_evidence_for_testing(
            self.paths,
            self.DECISION_ARTIFACT,
        )
        expected_evidence_sha256 = _canonical_digest(self.DECISION_EVIDENCE)
        self.assertEqual(
            state["lockbox_decision_evidence_sha256"],
            expected_evidence_sha256,
        )
        self.assertEqual(
            state["lockbox_decision_evidence_mint_sha256"],
            self.DECISION_ARTIFACT.mint_sha256,
        )
        reservation = json.loads(
            self.paths.lockbox_reservation_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            reservation["lockbox_decision_evidence_sha256"],
            expected_evidence_sha256,
        )
        self.assertEqual(
            reservation["lockbox_decision_evidence_mint_sha256"],
            self.DECISION_ARTIFACT.mint_sha256,
        )
        minted = json.loads(
            self.lockbox_result_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            minted["decision_evidence"],
            self.DECISION_EVIDENCE,
        )
        self.assertEqual(
            derive_phase_b_decision(minted["decision_evidence"]),
            derive_phase_b_decision(self.DECISION_EVIDENCE),
        )

        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "private DecisionEvidence mint",
        ):
            self.runner._validated_private_decision_evidence(
                deepcopy(self.DECISION_EVIDENCE)
            )
        direct = object.__new__(type(self.DECISION_ARTIFACT))
        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "private DecisionEvidence mint",
        ):
            self.runner._run_lockbox_with_private_evidence_for_testing(
                self.paths,
                direct,
            )

    def test_second_review_mutations_require_cached_parent_identity(
        self,
    ) -> None:
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside")

        authority_root = self.root / "authority-project"
        authority_parent = authority_root / "state"
        authority_parent.mkdir(parents=True)
        authority_target = authority_parent / "root-bound.json"
        self.runner._safe_path(
            authority_target,
            allowed_root=authority_parent,
            project_root=authority_root,
        )
        moved_authority_root = self.root / "authority-project-original"
        authority_root.rename(moved_authority_root)
        authority_parent.mkdir(parents=True)
        with self.assertRaisesRegex(self.runner.RunnerError, "identity|trusted"):
            self.runner._write_new_fsynced(authority_target, b"candidate")
        self.assertFalse(authority_target.exists())
        self.assertFalse(
            (
                moved_authority_root
                / authority_target.relative_to(authority_root)
            ).exists()
        )

        create_parent = self.root / "create-parent"
        create_parent.mkdir()
        create_target = create_parent / "new.json"
        self.runner._safe_path(
            create_target,
            allowed_root=create_parent,
            project_root=self.root,
        )
        moved_create_parent = self.root / "create-parent-original"
        create_parent.rename(moved_create_parent)
        create_parent.mkdir()
        with self.assertRaisesRegex(self.runner.RunnerError, "identity|trusted"):
            self.runner._write_new_fsynced(create_target, b"candidate")
        self.assertFalse(create_target.exists())
        self.assertFalse((moved_create_parent / create_target.name).exists())

        remove_parent = self.root / "remove-parent"
        remove_parent.mkdir()
        remove_target = remove_parent / "remove.json"
        remove_target.write_bytes(b"original")
        self.runner._safe_path(
            remove_target,
            allowed_root=remove_parent,
            project_root=self.root,
            final_kind="file",
            require_final=True,
        )
        attacker = self.root / "remove-attacker.json"
        attacker.write_bytes(b"attacker")
        os.replace(attacker, remove_target)
        with self.assertRaisesRegex(self.runner.RunnerError, "identity|trusted"):
            self.runner._durable_unlink(remove_target)
        self.assertEqual(remove_target.read_bytes(), b"attacker")
        self.assertEqual(outside.read_bytes(), b"outside")

    def test_second_review_lock_and_replace_bind_both_path_authorities(
        self,
    ) -> None:
        outside = self.root / "outside.bin"
        outside.write_bytes(b"outside")
        outside_lock = self.root / "outside-lock.bin"
        outside_lock.write_bytes(b"")
        hardlink_parent = self.root / "hardlink-parent"
        hardlink_parent.mkdir()
        hardlink_path = hardlink_parent / "identity.lock"
        os.link(outside_lock, hardlink_path)
        self.runner._safe_path(
            hardlink_path,
            allowed_root=hardlink_parent,
            project_root=self.root,
            final_kind="file",
            require_final=True,
        )
        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "hard link|single-link",
        ):
            self.runner._open_lock_handle(hardlink_path)
        self.assertEqual(outside_lock.read_bytes(), b"")

        lock_parent = self.root / "lock-parent"
        lock_parent.mkdir()
        lock_path = lock_parent / "identity.lock"
        self.runner._safe_path(
            lock_path,
            allowed_root=lock_parent,
            project_root=self.root,
        )
        moved_lock_parent = self.root / "lock-parent-original"
        lock_parent.rename(moved_lock_parent)
        lock_parent.mkdir()
        with self.assertRaisesRegex(self.runner.RunnerError, "identity|trusted"):
            self.runner._open_lock_handle(lock_path)
        self.assertFalse(lock_path.exists())
        self.assertFalse((moved_lock_parent / lock_path.name).exists())

        for changed_side in ("source", "destination"):
            with self.subTest(changed_side=changed_side):
                pair_root = self.root / f"replace-{changed_side}"
                pair_root.mkdir()
                source = pair_root / "source.stage"
                destination = pair_root / "destination.json"
                source.write_bytes(b"source")
                destination.write_bytes(b"destination")
                for candidate in (source, destination):
                    self.runner._safe_path(
                        candidate,
                        allowed_root=pair_root,
                        project_root=self.root,
                        final_kind="file",
                        require_final=True,
                    )
                changed = source if changed_side == "source" else destination
                attacker = self.root / f"{changed_side}-attacker.bin"
                attacker.write_bytes(f"{changed_side}-attacker".encode("ascii"))
                os.replace(attacker, changed)
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "identity|trusted",
                ):
                    self.runner._replace_entry_durably(source, destination)
                self.assertEqual(outside.read_bytes(), b"outside")
                self.assertTrue(source.exists())
                self.assertTrue(destination.exists())

    @unittest.skipUnless(os.name == "nt", "Windows namespace authority test")
    def test_final_review_existing_destination_is_held_through_replace(
        self,
    ) -> None:
        pair_root = self.root / "held-destination"
        pair_root.mkdir()
        source = pair_root / "source.stage"
        destination = pair_root / "destination.json"
        source.write_bytes(b"new-candidate")
        destination.write_bytes(b"exact-prior")
        for path in (source, destination):
            self.runner._safe_path(
                path,
                allowed_root=pair_root,
                project_root=self.root,
                final_kind="file",
                require_final=True,
            )
        attacker = self.root / "destination-attacker.json"
        attacker.write_bytes(b"attacker")
        unrelated = self.root / "destination-unrelated.json"
        unrelated.write_bytes(b"unrelated")
        original_replace = self.runner._windows_replace_by_handle
        race_attempted = False
        race_blocked = False
        observed_prior: list[bytes] = []

        def timed_replace(
            source_path: Path,
            destination_path: Path,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            nonlocal race_attempted, race_blocked
            destination_descriptor = kwargs.get("destination_descriptor")
            if destination_descriptor is not None:
                position = os.lseek(destination_descriptor, 0, os.SEEK_CUR)
                os.lseek(destination_descriptor, 0, os.SEEK_SET)
                observed_prior.append(os.read(destination_descriptor, 4096))
                os.lseek(destination_descriptor, position, os.SEEK_SET)
            race_attempted = True
            try:
                os.replace(attacker, destination_path)
            except OSError:
                race_blocked = True
            original_replace(
                source_path,
                destination_path,
                *args,
                **kwargs,
            )
            if destination_descriptor is not None:
                position = os.lseek(destination_descriptor, 0, os.SEEK_CUR)
                os.lseek(destination_descriptor, 0, os.SEEK_SET)
                observed_prior.append(os.read(destination_descriptor, 4096))
                os.lseek(destination_descriptor, position, os.SEEK_SET)

        with patch.object(
            self.runner,
            "_windows_replace_by_handle",
            side_effect=timed_replace,
        ):
            self.runner._replace_entry_durably(source, destination)
        self.assertTrue(race_attempted)
        self.assertTrue(race_blocked)
        self.assertEqual(observed_prior, [b"exact-prior", b"exact-prior"])
        self.assertEqual(destination.read_bytes(), b"new-candidate")
        self.assertEqual(attacker.read_bytes(), b"attacker")
        self.assertEqual(unrelated.read_bytes(), b"unrelated")

    def test_final_review_posix_existing_destination_replace_fails_closed(
        self,
    ) -> None:
        pair_root = self.root / "posix-unqualified"
        pair_root.mkdir()
        source = pair_root / "source.stage"
        destination = pair_root / "destination.json"
        source.write_bytes(b"source")
        destination.write_bytes(b"prior")
        for path in (source, destination):
            self.runner._safe_path(
                path,
                allowed_root=pair_root,
                project_root=self.root,
                final_kind="file",
                require_final=True,
            )
        outcome = ""
        with patch.object(self.runner.os, "name", "posix"):
            try:
                self.runner._replace_entry_durably(source, destination)
            except self.runner.RunnerError as error:
                outcome = str(error)
            except Exception as error:  # the old branch raises a platform error
                outcome = f"unexpected {type(error).__name__}: {error}"
        self.assertRegex(
            outcome,
            "POSIX existing-destination replacement is not qualified",
        )
        self.assertEqual(source.read_bytes(), b"source")
        self.assertEqual(destination.read_bytes(), b"prior")

    @unittest.skipUnless(os.name == "nt", "Windows durability authority test")
    def test_final_review_mutation_barriers_keep_the_same_parent_authority(
        self,
    ) -> None:
        unrelated = self.root / "barrier-unrelated.bin"
        unrelated.write_bytes(b"unrelated")

        def exercise(
            label: str,
            parents: tuple[Path, ...],
            operation: Callable[[], None],
        ) -> None:
            original_sync = self.runner._sync_directory
            attempted: set[Path] = set()
            blocked: set[Path] = set()
            authorities: dict[Path, bool] = {}

            def timed_sync(
                path: Path,
                *args: Any,
                **kwargs: Any,
            ) -> None:
                directory = Path(path)
                authority = kwargs.get("authority")
                if directory in parents and directory not in attempted:
                    attempted.add(directory)
                    authorities[directory] = authority is not None
                    moved = directory.parent / f"{directory.name}-{label}-moved"
                    try:
                        directory.rename(moved)
                    except OSError:
                        blocked.add(directory)
                    else:
                        directory.mkdir()
                original_sync(path, *args, **kwargs)

            with patch.object(
                self.runner,
                "_sync_directory",
                side_effect=timed_sync,
            ):
                operation()
            self.assertEqual(attempted, set(parents), label)
            self.assertEqual(blocked, set(parents), label)
            self.assertTrue(all(authorities.values()), label)
            self.assertEqual(unrelated.read_bytes(), b"unrelated")

        create_parent = self.root / "barrier-create"
        create_parent.mkdir()
        create_path = create_parent / "created.json"
        self.runner._safe_path(
            create_path,
            allowed_root=create_parent,
            project_root=self.root,
        )
        exercise(
            "create",
            (create_parent,),
            lambda: self.runner._write_new_fsynced(create_path, b"created"),
        )

        source_parent = self.root / "barrier-replace-source"
        destination_parent = self.root / "barrier-replace-destination"
        source_parent.mkdir()
        destination_parent.mkdir()
        source = source_parent / "source.stage"
        destination = destination_parent / "destination.json"
        source.write_bytes(b"replacement")
        destination.write_bytes(b"prior")
        for path, parent in (
            (source, source_parent),
            (destination, destination_parent),
        ):
            self.runner._safe_path(
                path,
                allowed_root=parent,
                project_root=self.root,
                final_kind="file",
                require_final=True,
            )
        exercise(
            "replace",
            (source_parent, destination_parent),
            lambda: self.runner._replace_entry_durably(source, destination),
        )

        unlink_parent = self.root / "barrier-unlink"
        unlink_parent.mkdir()
        unlink_path = unlink_parent / "remove.json"
        unlink_path.write_bytes(b"remove")
        self.runner._safe_path(
            unlink_path,
            allowed_root=unlink_parent,
            project_root=self.root,
            final_kind="file",
            require_final=True,
        )
        exercise(
            "unlink",
            (unlink_parent,),
            lambda: self.runner._durable_unlink(unlink_path),
        )

        lock_parent = self.root / "barrier-lock"
        lock_parent.mkdir()
        lock_path = lock_parent / "create.lock"
        self.runner._safe_path(
            lock_path,
            allowed_root=lock_parent,
            project_root=self.root,
        )

        def create_lock() -> None:
            handle = self.runner._open_lock_handle(lock_path)
            handle.close()

        exercise("lock", (lock_parent,), create_lock)

    def test_final_review_all_transaction_entry_barriers_carry_authority(
        self,
    ) -> None:
        self.paths.recovery_root.mkdir(parents=True, exist_ok=True)
        self._install_previous_pair()
        expected_parents = {
            self.state_root,
            self.lockbox_root,
            self.paths.recovery_root,
            self.canonical_root,
        }
        observed: dict[Path, list[bool]] = {
            path: [] for path in expected_parents
        }
        original_sync = self.runner._sync_directory

        def observed_sync(
            path: Path,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            directory = Path(path)
            if directory in observed:
                observed[directory].append(
                    kwargs.get("authority") is not None
                )
            original_sync(path, *args, **kwargs)

        with patch.object(
            self.runner,
            "_sync_directory",
            side_effect=observed_sync,
        ):
            self._advance_to_lockbox()
            self.runner.stage_candidate(self.paths, "authority.json")
            self.runner.reject_receipt(
                self.paths,
                self.paths.receipt_path("authority.json"),
            )
        for parent, authority_flags in observed.items():
            with self.subTest(parent=parent):
                self.assertTrue(authority_flags)
                self.assertTrue(all(authority_flags))

    @unittest.skipUnless(os.name == "nt", "Windows recovery authority test")
    def test_final_rereview_not_started_holds_destination_through_cleanup(
        self,
    ) -> None:
        recovery_root = self.root / "recovery-not-started"
        recovery_root.mkdir()
        destination = recovery_root / "state.json"
        prior_bytes = b"exact-prior"
        source_bytes = b"future-source"
        destination.write_bytes(prior_bytes)
        self.runner._safe_path(
            destination,
            allowed_root=recovery_root,
            project_root=self.root,
            final_kind="file",
            require_final=True,
        )
        intent_path, prior_path = self.runner._replacement_control_paths(
            destination
        )
        intent_path.write_bytes(
            self.runner.canonical_json_bytes(
                {
                    "schema_version": 1,
                    "destination_name": destination.name,
                    "prior_name": prior_path.name,
                    "source_sha256": hashlib.sha256(
                        source_bytes
                    ).hexdigest().upper(),
                    "prior_sha256": hashlib.sha256(
                        prior_bytes
                    ).hexdigest().upper(),
                }
            )
        )
        attacker = self.root / "not-started-attacker.json"
        attacker.write_bytes(b"attacker")
        original_unlink = self.runner._durable_unlink
        change_attempted = False
        change_blocked = False

        def timed_unlink(
            path: Path,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            nonlocal change_attempted, change_blocked
            if Path(path) == intent_path and not change_attempted:
                change_attempted = True
                try:
                    os.replace(attacker, destination)
                except OSError:
                    change_blocked = True
            original_unlink(path, *args, **kwargs)

        with patch.object(
            self.runner,
            "_durable_unlink",
            side_effect=timed_unlink,
        ):
            outcome = self.runner._recover_windows_replacement(destination)
        self.assertEqual(outcome, "not_started")
        self.assertTrue(change_attempted)
        self.assertTrue(change_blocked)
        self.assertEqual(destination.read_bytes(), prior_bytes)
        self.assertFalse(intent_path.exists())
        self.assertFalse(prior_path.exists())
        self.assertEqual(attacker.read_bytes(), b"attacker")

    @unittest.skipUnless(os.name == "nt", "Windows recovery authority test")
    def test_final_rereview_committed_holds_destination_through_cleanup(
        self,
    ) -> None:
        recovery_root = self.root / "recovery-committed"
        recovery_root.mkdir()
        destination = recovery_root / "state.json"
        source_bytes = b"installed-source"
        prior_bytes = b"exact-prior"
        destination.write_bytes(source_bytes)
        self.runner._safe_path(
            destination,
            allowed_root=recovery_root,
            project_root=self.root,
            final_kind="file",
            require_final=True,
        )
        intent_path, prior_path = self.runner._replacement_control_paths(
            destination
        )
        prior_path.write_bytes(prior_bytes)
        intent_path.write_bytes(
            self.runner.canonical_json_bytes(
                {
                    "schema_version": 1,
                    "destination_name": destination.name,
                    "prior_name": prior_path.name,
                    "source_sha256": hashlib.sha256(
                        source_bytes
                    ).hexdigest().upper(),
                    "prior_sha256": hashlib.sha256(
                        prior_bytes
                    ).hexdigest().upper(),
                }
            )
        )
        attacker = self.root / "committed-attacker.json"
        attacker.write_bytes(b"attacker")
        original_unlink = self.runner._durable_unlink
        change_attempted = False
        change_blocked = False

        def timed_unlink(
            path: Path,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            nonlocal change_attempted, change_blocked
            if Path(path) == prior_path and not change_attempted:
                change_attempted = True
                try:
                    os.replace(attacker, destination)
                except OSError:
                    change_blocked = True
            original_unlink(path, *args, **kwargs)

        with patch.object(
            self.runner,
            "_durable_unlink",
            side_effect=timed_unlink,
        ):
            outcome = self.runner._recover_windows_replacement(destination)
        self.assertEqual(outcome, "committed")
        self.assertTrue(change_attempted)
        self.assertTrue(change_blocked)
        self.assertEqual(destination.read_bytes(), source_bytes)
        self.assertFalse(intent_path.exists())
        self.assertFalse(prior_path.exists())
        self.assertEqual(attacker.read_bytes(), b"attacker")

    def test_review_important_open_handles_block_root_parent_file_races(
        self,
    ) -> None:
        safe_config = self.runner._validate_input_path(
            self.paths,
            self.config_path,
        )
        original_config = self.config_path.read_bytes()
        attacker = self.root / "attacker-config.json"
        attacker.write_bytes(original_config + b" ")
        moved_root = self.root.parent / f"{self.root.name}-moved"
        moved_input = self.root / "public-inputs-moved"

        def restore_race_paths() -> None:
            if moved_root.exists() and not self.root.exists():
                moved_root.rename(self.root)
            if moved_input.exists() and not self.input_root.exists():
                moved_input.rename(self.input_root)

        self.addCleanup(restore_race_paths)
        real_open = self.runner.os.open
        attempts: list[str] = []
        blocked: list[str] = []
        triggered = False

        def racing_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            nonlocal triggered
            if Path(path) == self.config_path and not triggered:
                triggered = True
                for label, operation in (
                    (
                        "file",
                        lambda: os.replace(attacker, self.config_path),
                    ),
                    (
                        "parent",
                        lambda: self.input_root.rename(moved_input),
                    ),
                    (
                        "root",
                        lambda: self.root.rename(moved_root),
                    ),
                ):
                    attempts.append(label)
                    try:
                        operation()
                    except OSError:
                        blocked.append(label)
            return real_open(path, flags, *args, **kwargs)

        with patch.object(self.runner.os, "open", side_effect=racing_open):
            digest = self.runner._sha256_file(safe_config)
        self.assertRegex(digest, r"^[0-9A-F]{64}$")
        self.assertEqual(attempts, ["file", "parent", "root"])
        self.assertEqual(blocked, attempts)
        self.assertEqual(self.config_path.read_bytes(), original_config)
        self.assertTrue(attacker.exists())

    def test_review_important_lock_and_canonical_handle_races_are_blocked(
        self,
    ) -> None:
        with self.runner.publication_lock(self.paths):
            pass
        lock_path = self.paths.recovery_root / self.runner.LOCK_NAME
        attacker_lock = self.root / "attacker.lock"
        attacker_lock.write_bytes(b"attacker")
        real_open = self.runner.os.open
        lock_race_blocked = False

        def race_lock(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            nonlocal lock_race_blocked
            if Path(path) == lock_path and not lock_race_blocked:
                try:
                    os.replace(attacker_lock, lock_path)
                except OSError:
                    lock_race_blocked = True
            return real_open(path, flags, *args, **kwargs)

        with patch.object(self.runner.os, "open", side_effect=race_lock):
            with self.runner.publication_lock(self.paths):
                pass
        self.assertTrue(lock_race_blocked)
        self.assertTrue(attacker_lock.exists())

        self._advance_to_lockbox()
        moved_canonical = self.root / "canonical-moved"
        real_handles = self.runner._trusted_parent_handles
        canonical_race_attempted = False
        canonical_race_blocked = False

        @contextmanager
        def race_canonical(
            path: Path,
            *,
            include_target: bool = True,
            mutation: bool = False,
        ) -> Any:
            nonlocal canonical_race_attempted, canonical_race_blocked
            with real_handles(
                path,
                include_target=include_target,
                mutation=mutation,
            ) as authority:
                if (
                    Path(path) == self.paths.result_path
                    and not canonical_race_attempted
                ):
                    canonical_race_attempted = True
                    try:
                        self.canonical_root.rename(moved_canonical)
                    except OSError:
                        canonical_race_blocked = True
                    else:
                        self.canonical_root.mkdir()
                yield authority

        with patch.object(
            self.runner,
            "_trusted_parent_handles",
            side_effect=race_canonical,
        ):
            if os.name == "nt":
                self.runner.stage_candidate(self.paths, "race.json")
            else:
                with self.assertRaises(self.runner.RunnerError):
                    self.runner.stage_candidate(self.paths, "race.json")
        self.assertTrue(canonical_race_attempted)
        if canonical_race_blocked:
            self.assertFalse(moved_canonical.exists())
        else:
            self.assertEqual(tuple(self.canonical_root.iterdir()), ())


if __name__ == "__main__":
    unittest.main()
