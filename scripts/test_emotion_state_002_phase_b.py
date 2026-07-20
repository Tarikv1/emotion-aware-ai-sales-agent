from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
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
            [sys.executable, str(validator)],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertEqual(
            passed.stdout,
            "EMOTION-STATE-002 Phase B frozen contract validation passed.\n",
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
                [sys.executable, str(temporary_validator)],
                cwd=temporary_root,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(failed.stdout, "")
            self.assertIn("frozen contract validation failed", failed.stderr)

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
        for actor_index in range(actor_count):
            actor_id = f"{1001 + actor_index:04d}"
            for sentence_index, sentence_id in enumerate(cls.SENTENCES):
                label = cls.LABELS[(actor_index + sentence_index) % len(cls.LABELS)]
                records.append(CremaLabelRecord(
                    clip_stem=f"synthetic-{actor_id}-{sentence_id}",
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
                            f"synthetic-extra-{actor_id}-{extra_index:02d}"
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
            [str(EVALUATION_PYTHON), str(validator)],
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(fixed.returncode, 0, fixed.stderr)
        self.assertEqual(
            fixed.stdout,
            "EMOTION-STATE-002 Phase B frozen contract validation passed.\n",
        )
        self.assertEqual(fixed.stderr, "")

        system_python = Path(sys.base_prefix) / "python.exe"
        self.assertTrue(system_python.is_file())
        self.assertNotEqual(system_python.resolve(), EVALUATION_PYTHON.resolve())
        refused = subprocess.run(
            [str(system_python), str(validator)],
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


if __name__ == "__main__":
    unittest.main()
