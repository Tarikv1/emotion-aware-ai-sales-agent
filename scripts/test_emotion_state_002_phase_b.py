from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
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
            self._write_tone(
                near_silence,
                hz=200.0,
                seconds=0.5,
                amplitude=0.00001,
            )
            self._write_tone(
                two_frames,
                hz=200.0,
                seconds=0.035,
                amplitude=0.5,
            )

            for path in (silence, near_silence, two_frames):
                with self.subTest(path=path.name):
                    with self.assertRaises(FeatureExtractionError):
                        extract_acoustic_features(path)

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
            clipped = root / "clipped.wav"

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
            self._write_pcm16(clipped, [32767] + [1000, -1000] * 400)

            for path in (
                stereo,
                eight_bit,
                wrong_rate,
                compressed,
                malformed,
                clipped,
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
