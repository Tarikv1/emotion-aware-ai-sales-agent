from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

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

        field_paths = [()] + [("label_counts",)]
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
