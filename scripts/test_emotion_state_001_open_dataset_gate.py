from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
import wave
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON = (
    "self-hosting guard unit runs in the direct unit gate; rerunning it under "
    "an active guard would require authority outside the frozen focused-command "
    "mapping"
)


class SourceProvenanceTests(unittest.TestCase):
    def test_private_source_pin_is_exact_and_non_adapting(self) -> None:
        path = ROOT / "research/sources/creative_analysis_engine/source_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["source_repository_url"],
            "https://github.com/WisdomBreathes/creative-analysis-engine",
        )
        self.assertEqual(manifest["source_repository_url_status"], "verified_read_only")
        self.assertEqual(manifest["source_branch"], "dev")
        self.assertEqual(
            manifest["source_revision"],
            "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
        )
        self.assertEqual(manifest["source_revision_status"], "verified_read_only")
        self.assertEqual(manifest["observed_license_status"], "absent_in_reviewed_root")
        self.assertEqual(len(manifest["reviewed_files"]), 7)
        self.assertEqual(manifest["copied_material"], [])
        self.assertEqual(manifest["translated_material"], [])
        self.assertEqual(manifest["adapted_material"], [])
        self.assertEqual(manifest["independently_reimplemented_material"], [])
        self.assertFalse(manifest["adaptation_allowed"])
        self.assertFalse(manifest["phase_b_approval"]["approved"])
        self.assertFalse(manifest["runtime_dependency_added"])


class PublicDatasetContractTests(unittest.TestCase):
    @staticmethod
    def _manifest_fixture(dataset_id: str, completion_status: str) -> dict[str, object]:
        from scripts.emotion_state_public_dataset_contracts import dataset_profile

        profile = dataset_profile(dataset_id)
        hashes_path = f"research/sources/emotion_state/datasets/{dataset_id}.hashes.json"
        quality_path = f"research/sources/emotion_state/datasets/{dataset_id}.quality.json"
        pending = completion_status == "material_verification_pending"
        digest = None if pending else "A" * 64
        selected_file_count = None if pending else 1
        selected_byte_count = None if pending else 1
        included_file_count = None if pending else 1
        excluded_file_count = None if pending else 0
        return {
            "dataset_id": dataset_id,
            "canonical_source_url": profile["canonical_source_url"],
            "release_or_version": profile["release_or_version"],
            "accessed_on": None if pending else "2026-07-15",
            "terms_or_license": profile["terms_or_license"],
            "access_restrictions": profile["access_restrictions"],
            "local_file_hashes": {
                "algorithm": "SHA-256",
                "inventory_path": hashes_path,
                "inventory_sha256": digest,
                "selected_file_count": selected_file_count,
                "selected_byte_count": selected_byte_count,
            },
            "source_label": "public-only",
            "source_labels": profile["source_labels"],
            "project_label_mapping": {},
            "excluded_labels": profile["excluded_labels"],
            "language": profile["language"],
            "domain": profile["domain"],
            "domain_limitations": profile["domain_limitations"],
            "permitted_research_lanes": profile["permitted_research_lanes"],
            "redistribution_status": profile["redistribution_status"],
            "manifest_version": 2,
            "selected_artifacts": profile["selected_artifacts"],
            "source_revision": profile["source_revision"],
            "release_published_at": profile["release_published_at"],
            "dependency_keys": profile["dependency_keys"],
            "quality_rules": profile["quality_rules"],
            "known_issues": profile["known_issues"],
            "exclusion_inventory": {
                "schema_id": "emotion-state-dataset-quality-inventory-reference-v1",
                "schema_version": 1,
                "quality_inventory_path": quality_path,
                "quality_inventory_sha256": digest,
                "included_file_count": included_file_count,
                "excluded_file_count": excluded_file_count,
            },
            "hash_inventory": {
                "schema_id": "emotion-state-dataset-hash-inventory-v1",
                "schema_version": 1,
                "algorithm": "SHA-256",
                "inventory_path": hashes_path,
                "inventory_sha256": digest,
                "selected_file_count": selected_file_count,
                "selected_byte_count": selected_byte_count,
                "path_normalization": "project-relative-posix-nfc",
                "ordering": "ordinal-by-normalized-path",
            },
            "completion_status": completion_status,
            "runtime_influence_allowed": False,
        }

    def test_selected_dataset_order_and_pins_are_exact(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
            SELECTED_PUBLIC_DATASETS,
            dataset_profile,
        )

        self.assertEqual(SELECTED_PUBLIC_DATASETS, (CREMA_DATASET_ID, AMI_DATASET_ID))
        crema = dataset_profile(CREMA_DATASET_ID)
        self.assertEqual(crema["release_or_version"], "v1.0")
        self.assertEqual(
            crema["source_revision"],
            "f3b8611a309886568dfa957141775b2e05add04a",
        )
        self.assertEqual(
            crema["raw_source_label_map"],
            {
                "A": "anger",
                "D": "disgust",
                "F": "fear",
                "H": "happy",
                "N": "neutral",
                "S": "sad",
            },
        )
        self.assertEqual(crema["project_label_mapping"], {})
        ami = dataset_profile(AMI_DATASET_ID)
        self.assertEqual(ami["release_or_version"], "AMI manual annotations v1.6.2")
        self.assertEqual(ami["project_label_mapping"], {})
        self.assertEqual(ami["selected_artifacts"][0], "official-manual-annotation-archive")

    def test_public_profiles_never_claim_operational_labels(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            OPERATIONAL_SIGNALS,
            SELECTED_PUBLIC_DATASETS,
            dataset_profile,
        )

        for dataset_id in SELECTED_PUBLIC_DATASETS:
            serialized = json.dumps(dataset_profile(dataset_id), sort_keys=True)
            for signal in OPERATIONAL_SIGNALS:
                self.assertNotIn(f'"{signal}":', serialized)

    def test_dataset_profiles_freeze_complete_identity_and_selection_boundaries(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            AMI_PROFILE_IDENTITY,
            CREMA_DATASET_ID,
            CREMA_PROFILE_IDENTITY,
            CREMA_RAW_SOURCE_LABEL_MAP,
            dataset_profile,
        )

        crema = dataset_profile(CREMA_DATASET_ID)
        ami = dataset_profile(AMI_DATASET_ID)
        for field, value in CREMA_PROFILE_IDENTITY.items():
            self.assertEqual(crema[field], value)
        for field, value in AMI_PROFILE_IDENTITY.items():
            self.assertEqual(ami[field], value)
        self.assertIn("official_access_process_required", crema["access_restrictions"])
        self.assertIn("git_lfs_media_objects_required", crema["access_restrictions"])
        self.assertIn(
            "local_archive_sha256_is_local_retrieval_pin_not_publisher_signed_checksum",
            ami["known_issues"],
        )
        crema["selected_artifacts"].append("mutation")
        self.assertEqual(
            dataset_profile(CREMA_DATASET_ID)["selected_artifacts"],
            CREMA_PROFILE_IDENTITY["selected_artifacts"],
        )
        original_raw_map = dict(CREMA_RAW_SOURCE_LABEL_MAP)
        try:
            CREMA_RAW_SOURCE_LABEL_MAP["A"] = "mutated"
            self.assertEqual(
                dataset_profile(CREMA_DATASET_ID)["raw_source_label_map"],
                original_raw_map,
            )
        finally:
            CREMA_RAW_SOURCE_LABEL_MAP.clear()
            CREMA_RAW_SOURCE_LABEL_MAP.update(original_raw_map)
        with self.assertRaisesRegex(ValueError, "unknown public dataset"):
            dataset_profile("unknown-dataset")

    def test_canonical_profiles_are_recursively_immutable_and_public_reads_are_independent(self) -> None:
        import scripts.emotion_state_public_dataset_contracts as contracts

        canonical_profiles = contracts._DATASET_PROFILES
        canonical_crema = canonical_profiles[contracts.CREMA_DATASET_ID]
        original_artifacts = list(canonical_crema["selected_artifacts"])
        original_label_map = dict(canonical_crema["raw_source_label_map"])

        def replace_canonical_profile() -> None:
            canonical_profiles[contracts.CREMA_DATASET_ID] = {}

        def replace_canonical_field() -> None:
            canonical_crema["domain"] = "mutated"

        def append_canonical_artifact() -> None:
            canonical_crema["selected_artifacts"].append("mutation")

        def replace_canonical_label() -> None:
            canonical_crema["raw_source_label_map"]["A"] = "mutated"

        mutation_cases = (
            ("root_mapping", replace_canonical_profile, TypeError),
            ("nested_mapping", replace_canonical_field, TypeError),
            ("nested_sequence", append_canonical_artifact, AttributeError),
            ("nested_label_mapping", replace_canonical_label, TypeError),
        )
        for name, mutation, expected_error in mutation_cases:
            with self.subTest(name=name):
                try:
                    with self.assertRaises(expected_error):
                        mutation()
                finally:
                    if isinstance(canonical_profiles, dict):
                        canonical_profiles[contracts.CREMA_DATASET_ID] = canonical_crema
                    if isinstance(canonical_crema, dict):
                        canonical_crema["domain"] = contracts.CREMA_PROFILE_IDENTITY["domain"]
                        canonical_crema["selected_artifacts"] = deepcopy(original_artifacts)
                        canonical_crema["raw_source_label_map"] = deepcopy(original_label_map)

        public_profile = contracts.dataset_profile(contracts.CREMA_DATASET_ID)
        public_profile["domain"] = "mutated"
        public_profile["selected_artifacts"].append("mutation")
        public_profile["raw_source_label_map"]["A"] = "mutated"
        fresh_profile = contracts.dataset_profile(contracts.CREMA_DATASET_ID)
        self.assertEqual(fresh_profile["domain"], contracts.CREMA_PROFILE_IDENTITY["domain"])
        self.assertEqual(
            fresh_profile["selected_artifacts"],
            contracts.CREMA_PROFILE_IDENTITY["selected_artifacts"],
        )
        self.assertEqual(fresh_profile["raw_source_label_map"], contracts.CREMA_RAW_SOURCE_LABEL_MAP)

    def test_pending_and_verified_manifests_use_exact_evidence_reference_shapes(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            CREMA_DATASET_ID,
            validate_dataset_manifest,
        )

        pending = self._manifest_fixture(CREMA_DATASET_ID, "material_verification_pending")
        self.assertIs(validate_dataset_manifest(pending), pending)
        pending_claim = deepcopy(pending)
        pending_claim["hash_inventory"]["inventory_sha256"] = "A" * 64
        pending_claim["local_file_hashes"]["inventory_sha256"] = "A" * 64
        with self.assertRaisesRegex(ValueError, "pending manifests cannot claim"):
            validate_dataset_manifest(pending_claim)

        verified = self._manifest_fixture(CREMA_DATASET_ID, "verified")
        self.assertIs(validate_dataset_manifest(verified), verified)
        projection_mismatch = deepcopy(verified)
        projection_mismatch["local_file_hashes"]["selected_byte_count"] = 2
        with self.assertRaisesRegex(ValueError, "v1 hash projection"):
            validate_dataset_manifest(projection_mismatch)
        path_escape = deepcopy(verified)
        path_escape["hash_inventory"]["inventory_path"] = "../escape.hashes.json"
        path_escape["local_file_hashes"]["inventory_path"] = "../escape.hashes.json"
        with self.assertRaisesRegex(ValueError, "inventory_path"):
            validate_dataset_manifest(path_escape)
        extra_field = dict(verified, unexpected=True)
        with self.assertRaisesRegex(ValueError, "fields mismatch"):
            validate_dataset_manifest(extra_field)

    def test_integer_version_fields_reject_booleans_and_numeric_lookalikes(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            CREMA_DATASET_ID,
            validate_dataset_manifest,
            validate_hash_inventory,
        )

        manifest = self._manifest_fixture(CREMA_DATASET_ID, "material_verification_pending")
        invalid_manifests = {
            "manifest_version_boolean": dict(manifest, manifest_version=True),
            "manifest_version_float": dict(manifest, manifest_version=2.0),
            "hash_schema_version": deepcopy(manifest),
            "quality_schema_version": deepcopy(manifest),
        }
        invalid_manifests["hash_schema_version"]["hash_inventory"]["schema_version"] = True
        invalid_manifests["quality_schema_version"]["exclusion_inventory"]["schema_version"] = True
        for name, invalid_manifest in invalid_manifests.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "version"):
                    validate_dataset_manifest(invalid_manifest)

        with tempfile.TemporaryDirectory() as directory:
            inventory = {
                "inventory_version": True,
                "dataset_id": "synthetic-fixture",
                "algorithm": "SHA-256",
                "path_normalization": "project-relative-posix-nfc",
                "ordering": "ordinal-by-normalized-path",
                "selected_file_count": 0,
                "selected_byte_count": 0,
                "files": [],
            }
            with self.assertRaisesRegex(ValueError, "inventory_version"):
                validate_hash_inventory(inventory, Path(directory))

    def test_forbidden_project_mappings_are_rejected(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
            CREMA_PROHIBITED_PROJECT_MAPPINGS,
            validate_dataset_manifest,
        )

        for source_label, project_label in CREMA_PROHIBITED_PROJECT_MAPPINGS.items():
            manifest = self._manifest_fixture(CREMA_DATASET_ID, "material_verification_pending")
            manifest["project_label_mapping"] = {source_label: project_label}
            with self.subTest(source_label=source_label, project_label=project_label):
                with self.assertRaisesRegex(ValueError, "project_label_mapping"):
                    validate_dataset_manifest(manifest)
        ami = self._manifest_fixture(AMI_DATASET_ID, "material_verification_pending")
        ami["project_label_mapping"] = {"dialogue_act": "confusion"}
        with self.assertRaisesRegex(ValueError, "project_label_mapping"):
            validate_dataset_manifest(ami)

    def test_hash_inventory_is_byte_bound_and_rejects_digest_path_and_count_mismatch(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import validate_hash_inventory

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "selected.bin"
            selected.write_bytes(b"verified-fixture")
            digest = hashlib.sha256(selected.read_bytes()).hexdigest().upper()
            inventory = {
                "inventory_version": 1,
                "dataset_id": "synthetic-fixture",
                "algorithm": "SHA-256",
                "path_normalization": "project-relative-posix-nfc",
                "ordering": "ordinal-by-normalized-path",
                "selected_file_count": 1,
                "selected_byte_count": selected.stat().st_size,
                "files": [{
                    "path": "selected.bin",
                    "size_bytes": selected.stat().st_size,
                    "sha256": digest,
                }],
            }
            self.assertIs(validate_hash_inventory(inventory, root), inventory)
            invalid_cases = {
                "digest": dict(
                    inventory,
                    files=[dict(inventory["files"][0], sha256="B" * 64)],
                ),
                "path": dict(
                    inventory,
                    files=[dict(inventory["files"][0], path="../selected.bin")],
                ),
                "count": dict(inventory, selected_file_count=2),
            }
            for name, invalid in invalid_cases.items():
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):
                        validate_hash_inventory(invalid, root)

    def test_tracked_manifest_contract_is_v2_and_preserves_v1_fields(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            REQUIRED_V1_FIELDS,
            REQUIRED_V2_FIELDS,
            SELECTED_PUBLIC_DATASETS,
        )

        contract = json.loads(
            (ROOT / "research/sources/emotion_state/dataset_manifest_contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["schema_id"], "emotion-state-dataset-manifest-v2")
        self.assertIs(type(contract["schema_version"]), int)
        self.assertEqual(contract["schema_version"], 2)
        self.assertEqual(set(contract["required_v1_fields"]), REQUIRED_V1_FIELDS)
        self.assertEqual(set(contract["required_fields"]), REQUIRED_V2_FIELDS)
        self.assertEqual(contract["selected_public_datasets"], list(SELECTED_PUBLIC_DATASETS))
        self.assertFalse(contract["dataset_download_authorized"])
        self.assertFalse(contract["dataset_evaluation_started"])
        self.assertFalse(contract["runtime_influence_allowed"])

    def test_public_dataset_contract_self_check_passes(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import public_dataset_contract_self_check

        self.assertEqual(public_dataset_contract_self_check(), "pass")


class DatasetMaterialValidationTests(unittest.TestCase):
    @staticmethod
    def _write_pcm_wav(path: Path, *, frame_count: int = 160) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(
                struct.pack("<" + "h" * frame_count, *([100] * frame_count))
            )

    @classmethod
    def _crema_fixture(cls, root: Path) -> None:
        (root / "processedResults").mkdir(parents=True)
        (root / "processedResults" / "summaryTable.csv").write_text(
            "filename,issue\n"
            "1001_DFA_ANG_XX.mp3,official encoding mismatch\n"
            "1076_MTI_SAD_XX.wav,official no audio\n",
            encoding="utf-8",
        )
        (root / "finishedResponses.csv").write_text(
            "FileName,Modality,Response\n"
            "1001_DFA_ANG_XX.mp3,audio,S\n"
            "1002_IEO_HAP_HI.wav,audio,H\n"
            "1002_IEO_HAP_HI.wav,audio,S\n"
            "1003_TAI_FEA_XX.mp3,video,NOT_AN_AUDIO_LABEL\n",
            encoding="utf-8",
        )
        (root / "SentenceFilenames.csv").write_text(
            "sentence_code,text\nDFA,synthetic sentence\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text("synthetic CREMA fixture\n", encoding="utf-8")
        (root / "LICENSE.txt").write_text("synthetic fixture license\n", encoding="utf-8")
        for filename in (
            "1001_DFA_ANG_XX.wav",
            "1002_IEO_HAP_HI.wav",
            "1003_TAI_FEA_XX.wav",
        ):
            cls._write_pcm_wav(root / "AudioWAV" / filename)
        cls._write_pcm_wav(
            root / "AudioWAV" / "1076_MTI_SAD_XX.wav",
            frame_count=0,
        )
        (root / "VideoDemographics.csv").write_text(
            "ActorID,Age\n1001,30\n",
            encoding="utf-8",
        )

    @staticmethod
    def _synthetic_crema_lfs_oids(crema_root: Path) -> dict[Path, str]:
        return {
            path: hashlib.sha256(path.read_bytes()).hexdigest().upper()
            for path in sorted((crema_root / "AudioWAV").glob("*.wav"))
            if path.name != "1076_MTI_SAD_XX.wav"
        }

    @classmethod
    def _crema_lfs_tar(
        cls,
        crema_root: Path,
        *,
        omit: frozenset[str] = frozenset(),
        overrides: dict[str, bytes] | None = None,
        extra: dict[str, bytes] | None = None,
    ) -> bytes:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as output:
            for path in sorted((crema_root / "AudioWAV").glob("*.wav")):
                relative = path.relative_to(crema_root).as_posix()
                if relative in omit:
                    continue
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                pointer = (
                    "version https://git-lfs.github.com/spec/v1\n"
                    f"oid sha256:{digest}\n"
                    f"size {path.stat().st_size}\n"
                ).encode("utf-8")
                payload = (overrides or {}).get(relative, pointer)
                info = tarfile.TarInfo(relative)
                info.size = len(payload)
                output.addfile(info, io.BytesIO(payload))
            for relative, payload in sorted((extra or {}).items()):
                info = tarfile.TarInfo(relative)
                info.size = len(payload)
                output.addfile(info, io.BytesIO(payload))
        return buffer.getvalue()

    @staticmethod
    def _ami_archive(path: Path, *, include_missing_participant: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        word_attributes = "" if include_missing_participant else ' participant="P1"'
        with zipfile.ZipFile(path, "w") as output:
            output.writestr(
                "ami_public_manual_1.6.2/corpusResources/meetings.xml",
                '<meetings><meeting id="ES2002a" site="Edinburgh" '
                'scenario="design" series="ES2002"><participant id="P1" />'
                "</meeting></meetings>",
            )
            output.writestr(
                "ami_public_manual_1.6.2/words/ES2002a.A.words.xml",
                '<root><w meeting="ES2002a"'
                + word_attributes
                + ">PRIVATE SYNTHETIC TRANSCRIPT TEXT</w></root>",
            )
            output.writestr(
                "ami_public_manual_1.6.2/dialogueActs/ES2002a.A.dialogue-acts.xml",
                '<root><dialogue-act participant="P1" meeting="ES2002a" /></root>',
            )
            output.writestr(
                "ami_public_manual_1.6.2/segments/ES2002a.A.segments.xml",
                '<root><segment participant="P1" meeting="ES2002a" /></root>',
            )
            output.writestr(
                "ami_public_manual_1.6.2/partitions/scenario.txt",
                "ES2002a\n",
            )
            output.writestr(
                "ami_public_manual_1.6.2/partitions/full-corpus.txt",
                "ES2002b\nES2002a\n",
            )
            output.writestr(
                "ami_public_manual_1.6.2/audio/",
                b"",
            )
            output.writestr(
                "ami_public_manual_1.6.2/audio/ES2002a.wav",
                b"excluded audio",
            )
            output.writestr(
                "ami_public_manual_1.6.2/video/ES2002a.avi",
                b"excluded video",
            )
            output.writestr(
                "ami_public_manual_1.6.2/automatic/ES2002a.asr.xml",
                "<automatic />",
            )
            output.writestr(
                "ami_public_manual_1.6.2/DOME/ES2002a.dome.xml",
                "<dome />",
            )
            output.writestr(
                "ami_public_manual_1.6.2/socialRoles/ES2002a.roles.xml",
                "<roles />",
            )
            output.writestr(
                "ami_public_manual_1.6.2/emotions/ES2002a.emotions.xml",
                "<emotions />",
            )

    @classmethod
    def _material_fixture(
        cls,
        root: Path,
    ) -> tuple[dict[str, dict[str, object]], Path]:
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
            safe_extract_ami_archive,
            validate_ami_material,
            validate_crema_material,
        )

        public_root = root / "data" / "public" / "emotion-state"
        crema_root = public_root / "crema"
        cls._crema_fixture(crema_root)
        archive = public_root / "ami.zip"
        extract_root = public_root / "ami-extract"
        cls._ami_archive(archive)
        extraction = safe_extract_ami_archive(archive, extract_root)
        materials = {
            CREMA_DATASET_ID: validate_crema_material(
                crema_root,
                project_root=root,
                git_lfs_oids_by_path=cls._synthetic_crema_lfs_oids(crema_root),
            ),
            AMI_DATASET_ID: validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=extraction,
                project_root=root,
            ),
        }
        output_root = (
            root / "research" / "sources" / "emotion_state" / "datasets"
        )
        return materials, output_root

    @staticmethod
    def _independent_ami_partition_definition_copies(
        materials: dict[str, dict[str, object]],
        *,
        source_file_path: str,
    ) -> tuple[dict[str, object], dict[str, object]]:
        from scripts.emotion_state_public_dataset_contracts import AMI_DATASET_ID

        quality_inventory = materials[AMI_DATASET_ID]["quality_inventory"]
        quality_item = next(
            item
            for item in quality_inventory["items"]
            if (
                item["classification"] == "official_partition_metadata"
                and item["details"]["source_file_path"] == source_file_path
            )
        )
        quality_item["details"] = deepcopy(quality_item["details"])
        source_definition = next(
            definition
            for definition in quality_inventory["source_metadata"][
                "official_partition_definitions"
            ]
            if definition["source_file_path"] == source_file_path
        )
        return quality_item["details"], source_definition

    def test_crema_rejects_lfs_pointer_and_accepts_real_pcm_wav(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import validate_wav_file

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pointer = root / "pointer.wav"
            pointer.write_text(
                "version https://" + "git-lfs.github.com/spec/v1\n"
                "oid sha256:" + "A" * 64 + "\nsize 44\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Git LFS pointer"):
                validate_wav_file(pointer)
            valid = root / "valid.wav"
            with wave.open(str(valid), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(struct.pack("<" + "h" * 160, *([100] * 160)))
            metadata = validate_wav_file(valid)
            self.assertEqual(metadata["frame_count"], 160)
            self.assertEqual(metadata["sample_rate_hz"], 16000)

    def test_wav_rejects_empty_zero_duration_unreadable_and_invalid_metadata(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import validate_wav_file

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = root / "empty.wav"
            empty.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "RIFF/WAVE header"):
                validate_wav_file(empty)

            zero_duration = root / "zero.wav"
            self._write_pcm_wav(zero_duration, frame_count=0)
            with self.assertRaisesRegex(ValueError, "frame count|zero-duration"):
                validate_wav_file(zero_duration)

            unreadable = root / "unreadable.wav"
            self._write_pcm_wav(unreadable, frame_count=4)
            unreadable.write_bytes(unreadable.read_bytes()[:-2])
            with self.assertRaisesRegex(ValueError, "unreadable frames"):
                validate_wav_file(unreadable)

            invalid_metadata = root / "invalid-metadata.wav"
            self._write_pcm_wav(invalid_metadata, frame_count=4)
            invalid_bytes = bytearray(invalid_metadata.read_bytes())
            invalid_bytes[22:24] = b"\x00\x00"
            invalid_metadata.write_bytes(invalid_bytes)
            with self.assertRaisesRegex(ValueError, "metadata|channel"):
                validate_wav_file(invalid_metadata)

            floating_point = root / "floating-point.wav"
            pcm = io.BytesIO()
            with wave.open(pcm, "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(4)
                output.setframerate(16000)
                output.writeframes(struct.pack("<f", 0.25))
            floating_bytes = bytearray(pcm.getvalue())
            floating_bytes[20:22] = b"\x03\x00"
            floating_point.write_bytes(floating_bytes)
            with self.assertRaisesRegex(ValueError, "unsupported|PCM"):
                validate_wav_file(floating_point)

    def test_ami_extraction_rejects_traversal_symlink_and_case_collision(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import safe_extract_ami_archive

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../escape.xml", "blocked")
            with self.assertRaisesRegex(ValueError, "archive path escape"):
                safe_extract_ami_archive(archive, root / "extract")

            symlink_archive = root / "symlink.zip"
            with zipfile.ZipFile(symlink_archive, "w") as output:
                symlink = zipfile.ZipInfo("manual/link.xml")
                symlink.create_system = 3
                symlink.external_attr = 0o120777 << 16
                output.writestr(symlink, "target.xml")
            with self.assertRaisesRegex(ValueError, "symlink"):
                safe_extract_ami_archive(symlink_archive, root / "symlink-extract")

            collision_archive = root / "collision.zip"
            with zipfile.ZipFile(collision_archive, "w") as output:
                output.writestr("manual/File.xml", "<root />")
                output.writestr("manual/file.xml", "<root />")
            with self.assertRaisesRegex(ValueError, "case-fold"):
                safe_extract_ami_archive(collision_archive, root / "collision-extract")

    def test_ami_extraction_rejects_file_descendant_and_casefold_prefix_conflicts(
        self,
    ) -> None:
        from scripts.emotion_state_public_dataset_contracts import safe_extract_ami_archive

        conflicts = {
            "exact": (
                "metadata",
                "metadata/words/ES2002a.A.words.xml",
            ),
            "casefold": (
                "Metadata",
                "metadata/words/ES2002a.A.words.xml",
            ),
        }
        for name, (file_path, descendant_path) in conflicts.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive = root / "conflict.zip"
                extract_root = root / "extract"
                with zipfile.ZipFile(archive, "w") as output:
                    output.writestr(file_path, "blocking file")
                    output.writestr(descendant_path, "<root />")
                with self.assertRaisesRegex(ValueError, "file.*descendant|prefix"):
                    safe_extract_ami_archive(archive, extract_root)
                self.assertFalse(extract_root.exists())
                self.assertEqual(list(root.glob(".extract.staging.*")), [])

    def test_ami_extraction_rejects_interposed_casefold_ancestor_conflict(
        self,
    ) -> None:
        from scripts.emotion_state_public_dataset_contracts import safe_extract_ami_archive

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "conflict.zip"
            extract_root = root / "extract"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("Metadata", "blocking file")
                output.writestr("metadata-aux", "interposed sibling")
                output.writestr(
                    "metadata/words/ES2002a.A.words.xml",
                    '<root><w participant="P1" meeting="ES2002a" /></root>',
                )
            with self.assertRaisesRegex(ValueError, "case-fold|file.*descendant|prefix"):
                safe_extract_ami_archive(archive, extract_root)
            self.assertFalse(extract_root.exists())
            self.assertEqual(list(root.glob(".extract.staging.*")), [])

    def test_ami_extraction_rejects_preexisting_path_conflict_without_residue(
        self,
    ) -> None:
        from scripts.emotion_state_public_dataset_contracts import safe_extract_ami_archive

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive)
            blocker = extract_root / "ami_public_manual_1.6.2" / "words"
            blocker.parent.mkdir(parents=True)
            blocker.write_text("pre-existing blocker", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pre-existing extraction path conflict"):
                safe_extract_ami_archive(archive, extract_root)
            self.assertEqual(
                blocker.read_text(encoding="utf-8"),
                "pre-existing blocker",
            )
            self.assertEqual(list(root.glob(".extract.staging.*")), [])
            self.assertEqual(list(root.glob(".extract.backup.*")), [])

    def test_ami_extraction_failure_leaves_no_partial_root_or_staging_residue(
        self,
    ) -> None:
        from scripts.emotion_state_public_dataset_contracts import safe_extract_ami_archive

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "corrupt.zip"
            extract_root = root / "extract"
            corrupt_payload = b"CORRUPT_SELECTED_PAYLOAD"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as output:
                output.writestr(
                    "ami_public_manual_1.6.2/corpusResources/meetings.xml",
                    "<meetings />",
                )
                output.writestr(
                    "ami_public_manual_1.6.2/words/ES2002a.A.words.xml",
                    corrupt_payload,
                )
            archive_bytes = bytearray(archive.read_bytes())
            payload_index = archive_bytes.find(corrupt_payload)
            self.assertGreaterEqual(payload_index, 0)
            archive_bytes[payload_index] ^= 0x01
            archive.write_bytes(archive_bytes)
            with self.assertRaisesRegex(ValueError, "AMI archive|extraction"):
                safe_extract_ami_archive(archive, extract_root)
            self.assertFalse(extract_root.exists())
            self.assertEqual(list(root.glob(".extract.staging.*")), [])
            self.assertEqual(list(root.glob(".extract.backup.*")), [])

    def test_hash_inventory_is_path_sorted_and_byte_bound(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import build_hash_inventory

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "b.txt").write_bytes(b"b")
            (root / "a.txt").write_bytes(b"a")
            inventory = build_hash_inventory(
                dataset_id="synthetic-fixture",
                project_root=root,
                selected_paths=[root / "b.txt", root / "a.txt"],
            )
            self.assertEqual([item["path"] for item in inventory["files"]], ["a.txt", "b.txt"])
            self.assertEqual(inventory["selected_file_count"], 2)
            self.assertEqual(inventory["selected_byte_count"], 2)

    def test_hash_inventory_rejects_escape_missing_collisions_and_lfs_mismatch(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import build_hash_inventory

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "selected.bin"
            selected.write_bytes(b"selected")
            outside = root.parent / f"{root.name}-outside.bin"
            outside.write_bytes(b"outside")
            try:
                with self.assertRaisesRegex(ValueError, "escapes"):
                    build_hash_inventory(
                        dataset_id="synthetic-fixture",
                        project_root=root,
                        selected_paths=[outside],
                    )
                with self.assertRaisesRegex(ValueError, "missing"):
                    build_hash_inventory(
                        dataset_id="synthetic-fixture",
                        project_root=root,
                        selected_paths=[root / "missing.bin"],
                    )
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    build_hash_inventory(
                        dataset_id="synthetic-fixture",
                        project_root=root,
                        selected_paths=[selected, selected],
                    )
                upper = root / "Straße.bin"
                lower = root / "Strasse.bin"
                upper.write_bytes(b"upper")
                lower.write_bytes(b"lower")
                with self.assertRaisesRegex(ValueError, "case-fold"):
                    build_hash_inventory(
                        dataset_id="synthetic-fixture",
                        project_root=root,
                        selected_paths=[upper, lower],
                    )
                with self.assertRaisesRegex(ValueError, "Git LFS OID"):
                    build_hash_inventory(
                        dataset_id="synthetic-fixture",
                        project_root=root,
                        selected_paths=[selected],
                        git_lfs_oids_by_path={"selected.bin": "B" * 64},
                    )
            finally:
                outside.unlink(missing_ok=True)

    def test_crema_filename_parsing_keeps_intended_label_as_prompt_metadata(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import parse_crema_filename

        parsed = parse_crema_filename("1001_DFA_ANG_XX.wav")
        self.assertEqual(parsed["actor_id"], "1001")
        self.assertEqual(parsed["sentence_code"], "DFA")
        self.assertEqual(parsed["intended_emotion_code"], "ANG")
        self.assertEqual(parsed["intensity_code"], "XX")
        self.assertEqual(parsed["intended_label_role"], "prompt_metadata_only")
        with self.assertRaisesRegex(ValueError, "CREMA-D filename"):
            parse_crema_filename("not-a-crema-file.wav")

    def test_crema_material_separates_intended_and_perceived_labels(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import validate_crema_material

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._crema_fixture(root)
            result = validate_crema_material(root, project_root=root)
            items = {
                item["path"]: item
                for item in result["quality_inventory"]["items"]
            }
            anger_file = items["AudioWAV/1001_DFA_ANG_XX.wav"]["details"]
            self.assertEqual(
                anger_file["filename_metadata"]["intended_emotion_code"],
                "ANG",
            )
            self.assertEqual(
                anger_file["source_label_evidence"]["raw_source_label"],
                "S",
            )
            self.assertEqual(
                anger_file["source_label_evidence"]["normalized_source_label"],
                "sad",
            )
            self.assertEqual(
                anger_file["source_label_evidence"]["source_column"],
                "Response",
            )
            self.assertEqual(
                anger_file["source_label_evidence"]["source_file_path"],
                "finishedResponses.csv",
            )
            self.assertEqual(
                anger_file["dependency_keys"],
                {
                    "speaker": "1001",
                    "source_corpus": "crema-d-v1.0-audio-wav",
                    "scripted_scenario": "DFA",
                },
            )
            tie = items["AudioWAV/1002_IEO_HAP_HI.wav"]["details"][
                "source_label_evidence"
            ]
            self.assertTrue(tie["ambiguous"])
            self.assertTrue(tie["abstained"])
            self.assertIsNone(tie["raw_source_label"])
            self.assertEqual(tie["vote_distribution"], {"H": 1, "S": 1})
            missing = items["AudioWAV/1003_TAI_FEA_XX.wav"]["details"][
                "source_label_evidence"
            ]
            self.assertTrue(missing["ambiguous"])
            self.assertIsNone(missing["normalized_source_label"])
            self.assertNotEqual(
                missing["normalized_source_label"],
                items["AudioWAV/1003_TAI_FEA_XX.wav"]["details"][
                    "filename_metadata"
                ]["intended_emotion_code"],
            )
            known_issue = items["AudioWAV/1076_MTI_SAD_XX.wav"]
            self.assertEqual(known_issue["disposition"], "excluded")
            self.assertEqual(
                known_issue["reason"],
                "official_known_no_audio_issue",
            )
            self.assertTrue(
                known_issue["details"]["objective_failure_confirmed"]
            )
            self.assertEqual(
                known_issue["details"]["objective_failure"],
                "objective_wav_validation_failed",
            )
            self.assertNotIn(str(root), json.dumps(result))
            demographics = items["VideoDemographics.csv"]
            self.assertEqual(demographics["disposition"], "excluded")
            self.assertEqual(
                demographics["reason"],
                "excluded_demographic_metadata",
            )
            selected_paths = {
                entry["path"] for entry in result["hash_inventory"]["files"]
            }
            self.assertNotIn("VideoDemographics.csv", selected_paths)
            self.assertNotIn("AudioWAV/1076_MTI_SAD_XX.wav", selected_paths)
            self.assertNotIn("7442", json.dumps(result))
            self.assertIn(
                "raters_heard_audio_presentation_encodings_while_feature_verification_uses_corresponding_wav_files",
                result["quality_inventory"]["limitations"],
            )

    def test_crema_material_rejects_missing_and_extra_selected_files(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import validate_crema_material

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._crema_fixture(root)
            complete = validate_crema_material(root, project_root=root)
            selected_paths = [
                root.joinpath(*entry["path"].split("/"))
                for entry in complete["hash_inventory"]["files"]
            ]
            with self.assertRaisesRegex(ValueError, "missing selected file"):
                validate_crema_material(
                    root,
                    project_root=root,
                    selected_paths=selected_paths[1:],
                )
            with self.assertRaisesRegex(ValueError, "extra selected file"):
                validate_crema_material(
                    root,
                    project_root=root,
                    selected_paths=[*selected_paths, root / "VideoDemographics.csv"],
                )
            (root / "README.md").unlink()
            with self.assertRaisesRegex(ValueError, "missing selected file"):
                validate_crema_material(root, project_root=root)
            (root / "README.md").write_text(
                "synthetic CREMA fixture\n",
                encoding="utf-8",
            )
            (root / "AudioWAV" / "1076_MTI_SAD_XX.wav").unlink()
            with self.assertRaisesRegex(ValueError, "missing selected file"):
                validate_crema_material(root, project_root=root)

    def test_ami_selection_excludes_media_automatic_roles_and_emotions(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            safe_extract_ami_archive,
            validate_ami_material,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive)
            extraction = safe_extract_ami_archive(archive, extract_root)
            members = {item["path"]: item for item in extraction["members"]}
            excluded_expectations = {
                "ami_public_manual_1.6.2/audio/ES2002a.wav": "audio",
                "ami_public_manual_1.6.2/video/ES2002a.avi": "video",
                "ami_public_manual_1.6.2/automatic/ES2002a.asr.xml": (
                    "automatic_annotation"
                ),
                "ami_public_manual_1.6.2/DOME/ES2002a.dome.xml": "dome",
                "ami_public_manual_1.6.2/socialRoles/ES2002a.roles.xml": (
                    "social_role"
                ),
                "ami_public_manual_1.6.2/emotions/ES2002a.emotions.xml": (
                    "speculative_emotion"
                ),
            }
            for path, classification in excluded_expectations.items():
                with self.subTest(path=path):
                    self.assertEqual(members[path]["classification"], classification)
                    self.assertFalse(members[path]["selected"])
                    self.assertFalse(extract_root.joinpath(*path.split("/")).exists())
            material = validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=extraction,
                project_root=root,
            )
            self.assertEqual(
                material["quality_inventory"]["excluded_file_count"],
                6,
            )
            self.assertEqual(
                material["hash_inventory"]["files"][0]["path"],
                "ami.zip",
            )
            serialized = json.dumps(material, sort_keys=True)
            self.assertNotIn("PRIVATE SYNTHETIC TRANSCRIPT TEXT", serialized)
            self.assertIn(
                "some_tno_participant_metadata_was_not_gathered",
                material["quality_inventory"]["limitations"],
            )
            self.assertIn(
                "documented_synchronization_and_dropout_limitations_exist",
                material["quality_inventory"]["limitations"],
            )
            self.assertTrue(
                material["quality_inventory"]["source_metadata"][
                    "multi_party_applicability"
                ]
            )
            self.assertEqual(
                material["quality_inventory"]["source_metadata"][
                    "dependency_keys"
                ],
                {
                    "speaker": ["P1"],
                    "call_session": ["ES2002a"],
                    "dialogue_dyad": "not_applicable_multi_party_meeting",
                    "source_corpus": ["ami-manual-annotations-v1.6.2"],
                    "scripted_scenario": ["design"],
                    "meeting_series": ["ES2002"],
                    "recording_site": ["Edinburgh"],
                },
            )

    def test_ami_unclassified_candidate_fails_and_missing_participant_is_quarantined(
        self,
    ) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            safe_extract_ami_archive,
            validate_ami_material,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unclassified = root / "unclassified.zip"
            with zipfile.ZipFile(unclassified, "w") as output:
                output.writestr("manual/mystery.xml", "<root />")
            with self.assertRaisesRegex(ValueError, "unclassified AMI"):
                safe_extract_ami_archive(unclassified, root / "unclassified-extract")

            empty_archive = root / "empty.zip"
            with zipfile.ZipFile(empty_archive, "w"):
                pass
            empty_extract_root = root / "empty-extract"
            empty_extraction = safe_extract_ami_archive(
                empty_archive,
                empty_extract_root,
            )
            with self.assertRaisesRegex(ValueError, "missing selected AMI"):
                validate_ami_material(
                    empty_extract_root,
                    archive_path=empty_archive,
                    extraction=empty_extraction,
                    project_root=root,
                )

            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive, include_missing_participant=True)
            extraction = safe_extract_ami_archive(archive, extract_root)
            material = validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=extraction,
                project_root=root,
            )
            quarantined_paths = {
                item["path"]
                for item in material["quality_inventory"]["dependency_quarantine"]
            }
            self.assertIn(
                "extract/ami_public_manual_1.6.2/words/ES2002a.A.words.xml",
                quarantined_paths,
            )

    def test_ami_retains_source_only_partition_definitions_deterministically(
        self,
    ) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            canonical_inventory_bytes,
            safe_extract_ami_archive,
            validate_ami_material,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive)
            extraction = safe_extract_ami_archive(archive, extract_root)
            first = validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=extraction,
                project_root=root,
            )
            second = validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=extraction,
                project_root=root,
            )
            source_metadata = first["quality_inventory"]["source_metadata"]
            self.assertEqual(source_metadata["project_case_assignments"], [])
            self.assertEqual(source_metadata["official_partition_definitions"], [
                {
                    "partition_id": "full-corpus",
                    "partition_type": "full_corpus",
                    "source_file_path": (
                        "extract/ami_public_manual_1.6.2/partitions/full-corpus.txt"
                    ),
                    "meeting_ids": ["ES2002a", "ES2002b"],
                },
                {
                    "partition_id": "scenario",
                    "partition_type": "scenario",
                    "source_file_path": (
                        "extract/ami_public_manual_1.6.2/partitions/scenario.txt"
                    ),
                    "meeting_ids": ["ES2002a"],
                },
            ])
            self.assertEqual(
                canonical_inventory_bytes(first),
                canonical_inventory_bytes(second),
            )

    def test_ami_requires_scenario_and_full_corpus_partition_types_at_both_gates(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            safe_extract_ami_archive,
            validate_ami_material,
        )

        for missing_type, missing_name in (
            ("scenario", "scenario.txt"),
            ("full_corpus", "full-corpus.txt"),
        ):
            with self.subTest(
                gate="material",
                missing_type=missing_type,
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive = root / "ami.zip"
                extract_root = root / "extract"
                self._ami_archive(archive)
                with zipfile.ZipFile(archive, "r") as source:
                    retained = [
                        (info, source.read(info))
                        for info in source.infolist()
                        if not info.filename.endswith(f"/partitions/{missing_name}")
                    ]
                with zipfile.ZipFile(archive, "w") as output:
                    for info, payload in retained:
                        output.writestr(info, payload)
                extraction = safe_extract_ami_archive(archive, extract_root)
                with self.assertRaisesRegex(
                    ValueError,
                    "scenario.*full_corpus|full_corpus.*scenario|partition type",
                ):
                    validate_ami_material(
                        extract_root,
                        archive_path=archive,
                        extraction=extraction,
                        project_root=root,
                    )

            with self.subTest(
                gate="quality",
                missing_type=missing_type,
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materials, output_root = self._material_fixture(root)
                mutated = deepcopy(materials)
                metadata = mutated[AMI_DATASET_ID]["quality_inventory"][
                    "source_metadata"
                ]
                metadata["official_partition_definitions"] = [
                    definition
                    for definition in metadata["official_partition_definitions"]
                    if definition["partition_type"] != missing_type
                ]
                metadata["official_partition_paths"] = [
                    definition["source_file_path"]
                    for definition in metadata["official_partition_definitions"]
                ]
                with self.assertRaisesRegex(
                    ValueError,
                    "scenario.*full_corpus|full_corpus.*scenario|partition type",
                ):
                    write_dataset_evidence(
                        output_root=output_root,
                        accessed_on="2026-07-15",
                        materials=mutated,
                        project_root=root,
                    )
                self.assertFalse(output_root.exists())

        with self.subTest(gate="material", duplicate="partition_id"), (
            tempfile.TemporaryDirectory()
        ) as directory:
            root = Path(directory)
            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive)
            with zipfile.ZipFile(archive, "a") as output:
                output.writestr(
                    "ami_public_manual_1.6.2/alternate-partitions/scenario.txt",
                    "ES2002a\n",
                )
            extraction = safe_extract_ami_archive(archive, extract_root)
            with self.assertRaisesRegex(ValueError, "duplicate AMI partition"):
                validate_ami_material(
                    extract_root,
                    archive_path=archive,
                    extraction=extraction,
                    project_root=root,
                )

        with self.subTest(gate="material", duplicate="definition"), (
            tempfile.TemporaryDirectory()
        ) as directory:
            root = Path(directory)
            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive)
            extraction = safe_extract_ami_archive(archive, extract_root)
            duplicated = deepcopy(extraction)
            duplicated["members"].append(
                deepcopy(next(
                    member
                    for member in duplicated["members"]
                    if member["classification"] == "official_partition_metadata"
                ))
            )
            with self.assertRaisesRegex(ValueError, "duplicate AMI partition"):
                validate_ami_material(
                    extract_root,
                    archive_path=archive,
                    extraction=duplicated,
                    project_root=root,
                )

        for duplicate in ("definition", "partition_id", "source_path"):
            with self.subTest(
                gate="quality",
                duplicate=duplicate,
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materials, output_root = self._material_fixture(root)
                mutated = deepcopy(materials)
                definitions = mutated[AMI_DATASET_ID]["quality_inventory"][
                    "source_metadata"
                ]["official_partition_definitions"]
                duplicate_definition = deepcopy(definitions[-1])
                if duplicate == "partition_id":
                    duplicate_definition["source_file_path"] = (
                        "extract/ami_public_manual_1.6.2/partitions/"
                        "scenario-copy.txt"
                    )
                elif duplicate == "source_path":
                    duplicate_definition["partition_id"] = "scenario-copy"
                definitions.append(duplicate_definition)
                definitions.sort(
                    key=lambda definition: (
                        definition["partition_id"],
                        definition["source_file_path"],
                    )
                )
                with self.assertRaisesRegex(ValueError, "duplicate AMI partition"):
                    write_dataset_evidence(
                        output_root=output_root,
                        accessed_on="2026-07-15",
                        materials=mutated,
                        project_root=root,
                    )
                self.assertFalse(output_root.exists())

    def test_write_evidence_rejects_synchronized_ami_partition_meeting_ids_tamper_without_output(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials, output_root = self._material_fixture(root)
            quality_definition, source_definition = (
                self._independent_ami_partition_definition_copies(
                    materials,
                    source_file_path=(
                        "data/public/emotion-state/ami-extract/"
                        "ami_public_manual_1.6.2/partitions/scenario.txt"
                    ),
                )
            )
            quality_definition["meeting_ids"] = ["ES2002b"]
            source_definition["meeting_ids"] = ["ES2002b"]

            with self.assertRaises(ValueError):
                write_dataset_evidence(
                    output_root=output_root,
                    accessed_on="2026-07-15",
                    materials=materials,
                    project_root=root,
                )
            self.assertFalse(output_root.exists())

    def test_write_evidence_rejects_synchronized_ami_partition_id_tamper_without_output(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials, output_root = self._material_fixture(root)
            quality_definition, source_definition = (
                self._independent_ami_partition_definition_copies(
                    materials,
                    source_file_path=(
                        "data/public/emotion-state/ami-extract/"
                        "ami_public_manual_1.6.2/partitions/scenario.txt"
                    ),
                )
            )
            quality_definition["partition_id"] = "scenario-tampered"
            source_definition["partition_id"] = "scenario-tampered"

            with self.assertRaises(ValueError):
                write_dataset_evidence(
                    output_root=output_root,
                    accessed_on="2026-07-15",
                    materials=materials,
                    project_root=root,
                )
            self.assertFalse(output_root.exists())

    def test_write_evidence_rejects_synchronized_ami_partition_type_tamper_without_output(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials, output_root = self._material_fixture(root)
            for source_file_path, partition_type in (
                (
                    "data/public/emotion-state/ami-extract/"
                    "ami_public_manual_1.6.2/partitions/full-corpus.txt",
                    "scenario",
                ),
                (
                    "data/public/emotion-state/ami-extract/"
                    "ami_public_manual_1.6.2/partitions/scenario.txt",
                    "full_corpus",
                ),
            ):
                quality_definition, source_definition = (
                    self._independent_ami_partition_definition_copies(
                        materials,
                        source_file_path=source_file_path,
                    )
                )
                quality_definition["partition_type"] = partition_type
                source_definition["partition_type"] = partition_type

            with self.assertRaises(ValueError):
                write_dataset_evidence(
                    output_root=output_root,
                    accessed_on="2026-07-15",
                    materials=materials,
                    project_root=root,
                )
            self.assertFalse(output_root.exists())

    def test_archive_hashing_and_material_outputs_are_deterministic(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            canonical_inventory_bytes,
            safe_extract_ami_archive,
            sha256_file,
            validate_ami_material,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "ami.zip"
            extract_root = root / "extract"
            self._ami_archive(archive)
            first_extraction = safe_extract_ami_archive(archive, extract_root)
            first = validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=first_extraction,
                project_root=root,
            )
            second_extraction = safe_extract_ami_archive(archive, extract_root)
            second = validate_ami_material(
                extract_root,
                archive_path=archive,
                extraction=second_extraction,
                project_root=root,
            )
            self.assertEqual(first_extraction["archive_sha256"], sha256_file(archive))
            self.assertEqual(
                canonical_inventory_bytes(first),
                canonical_inventory_bytes(second),
            )

    def test_offline_cli_rejects_private_and_out_of_root_paths(self) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public_root = root / "data" / "public" / "emotion-state"
            public_root.mkdir(parents=True)
            self._crema_fixture(public_root / "crema")
            archive = public_root / "ami.zip"
            self._ami_archive(archive)
            extract_root = public_root / "ami-extract"
            output_root = root / "research" / "sources" / "emotion_state" / "datasets"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--ami-archive",
                        str(archive),
                        "--ami-extract-root",
                        str(extract_root),
                        "--mode",
                        "list-ami",
                    ],
                    project_root=root,
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(stdout.getvalue().splitlines(), [
                "ami_public_manual_1.6.2/DOME/ES2002a.dome.xml\tdome",
                "ami_public_manual_1.6.2/audio/\tdirectory",
                "ami_public_manual_1.6.2/audio/ES2002a.wav\taudio",
                (
                    "ami_public_manual_1.6.2/automatic/ES2002a.asr.xml"
                    "\tautomatic_annotation"
                ),
                (
                    "ami_public_manual_1.6.2/corpusResources/meetings.xml"
                    "\tmanual_nxt_metadata"
                ),
                (
                    "ami_public_manual_1.6.2/dialogueActs/"
                    "ES2002a.A.dialogue-acts.xml\tdialogue_act"
                ),
                (
                    "ami_public_manual_1.6.2/emotions/ES2002a.emotions.xml"
                    "\tspeculative_emotion"
                ),
                (
                    "ami_public_manual_1.6.2/partitions/full-corpus.txt"
                    "\tofficial_partition_metadata"
                ),
                (
                    "ami_public_manual_1.6.2/partitions/scenario.txt"
                    "\tofficial_partition_metadata"
                ),
                (
                    "ami_public_manual_1.6.2/segments/ES2002a.A.segments.xml"
                    "\ttiming_link"
                ),
                (
                    "ami_public_manual_1.6.2/socialRoles/ES2002a.roles.xml"
                    "\tsocial_role"
                ),
                "ami_public_manual_1.6.2/video/ES2002a.avi\tvideo",
                (
                    "ami_public_manual_1.6.2/words/ES2002a.A.words.xml"
                    "\tspeaker_aligned_orthographic_transcript"
                ),
            ])
            private_archive = root / "data" / "private" / "ami.zip"
            private_archive.parent.mkdir(parents=True)
            private_archive.write_bytes(archive.read_bytes())
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--ami-archive",
                        str(private_archive),
                        "--ami-extract-root",
                        str(extract_root),
                        "--mode",
                        "list-ami",
                    ],
                    project_root=root,
                )
            self.assertEqual(exit_code, 1)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                stderr.getvalue(),
                (
                    "offline dataset verifier failed: "
                    "ami-archive rejects private dataset paths\n"
                ),
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--crema-root",
                        str(public_root / "crema"),
                        "--ami-archive",
                        str(archive),
                        "--ami-extract-root",
                        str(extract_root),
                        "--accessed-on",
                        "2026-07-15",
                        "--output-root",
                        str(root / "outside"),
                        "--mode",
                        "write-evidence",
                    ],
                    project_root=root,
                )
            self.assertEqual(exit_code, 1)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(
                stderr.getvalue(),
                (
                    "offline dataset verifier failed: output root must be "
                    "research/sources/emotion_state/datasets/\n"
                ),
            )
            self.assertFalse(output_root.exists())

    def test_offline_cli_rejects_abbreviated_and_unknown_options_with_exit_2(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public_root = root / "data" / "public" / "emotion-state"
            public_root.mkdir(parents=True)
            archive = public_root / "ami.zip"
            self._ami_archive(archive)
            extract_root = public_root / "ami-extract"
            invalid_argv = {
                "abbreviated": [
                    "--ami-arch",
                    str(archive),
                    "--ami-extract-root",
                    str(extract_root),
                    "--mode",
                    "list-ami",
                ],
                "unknown": [
                    "--unknown-option",
                    "value",
                    "--mode",
                    "list-ami",
                ],
            }
            for name, argv in invalid_argv.items():
                with self.subTest(name=name):
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with (
                        redirect_stdout(stdout),
                        redirect_stderr(stderr),
                        self.assertRaises(SystemExit) as raised,
                    ):
                        main(argv, project_root=root)
                    self.assertEqual(raised.exception.code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn("unrecognized arguments:", stderr.getvalue())

    def test_write_dataset_evidence_is_deterministic_and_manifest_immutable(self) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
            canonical_inventory_bytes,
            validate_ami_material,
            validate_crema_material,
            safe_extract_ami_archive,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public_root = root / "data" / "public" / "emotion-state"
            crema_root = public_root / "crema"
            self._crema_fixture(crema_root)
            archive = public_root / "ami.zip"
            extract_root = public_root / "ami-extract"
            self._ami_archive(archive)
            extraction = safe_extract_ami_archive(archive, extract_root)
            materials = {
                CREMA_DATASET_ID: validate_crema_material(
                    crema_root,
                    project_root=root,
                    git_lfs_oids_by_path=self._synthetic_crema_lfs_oids(
                        crema_root
                    ),
                ),
                AMI_DATASET_ID: validate_ami_material(
                    extract_root,
                    archive_path=archive,
                    extraction=extraction,
                    project_root=root,
                ),
            }
            output_root = (
                root / "research" / "sources" / "emotion_state" / "datasets"
            )
            written = write_dataset_evidence(
                output_root=output_root,
                accessed_on="2026-07-15",
                materials=materials,
                project_root=root,
            )
            self.assertEqual(len(written), 6)
            first_bytes = {
                path.name: path.read_bytes()
                for path in written
            }
            repeated = write_dataset_evidence(
                output_root=output_root,
                accessed_on="2026-07-15",
                materials=materials,
                project_root=root,
            )
            self.assertEqual(
                first_bytes,
                {path.name: path.read_bytes() for path in repeated},
            )
            manifest_path = output_root / f"{CREMA_DATASET_ID}.manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["accessed_on"] = "2026-07-16"
            manifest_path.write_bytes(canonical_inventory_bytes(manifest))
            with self.assertRaisesRegex(
                ValueError,
                "verified_manifest_version_is_immutable",
            ):
                write_dataset_evidence(
                    output_root=output_root,
                    accessed_on="2026-07-15",
                    materials=materials,
                    project_root=root,
                )

    def test_crema_lfs_pointer_parser_and_local_git_command_boundary(self) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            discover_crema_lfs_oids,
            parse_git_lfs_pointer,
        )

        digest = "A" * 64
        self.assertEqual(
            parse_git_lfs_pointer(
                (
                    "version https://git-lfs.github.com/spec/v1\r\n"
                    f"oid sha256:{digest.lower()}\r\n"
                    "size 44\r\n"
                ).encode("utf-8"),
                path="AudioWAV/1001_DFA_ANG_XX.wav",
            ),
            digest,
        )
        for malformed in (
            b"not a pointer\n",
            (
                b"version https://git-lfs.github.com/spec/v1\n"
                b"oid sha256:BAD\nsize 44\n"
            ),
            (
                b"version https://git-lfs.github.com/spec/v1\n"
                + b"oid sha256:"
                + b"A" * 64
                + b"\n"
            ),
        ):
            with self.subTest(malformed=malformed[:20]):
                with self.assertRaisesRegex(ValueError, "Git LFS pointer"):
                    parse_git_lfs_pointer(
                        malformed,
                        path="AudioWAV/1001_DFA_ANG_XX.wav",
                    )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            crema_root = root / "crema"
            self._crema_fixture(crema_root)
            expected_revision = "A" * 40
            archive_bytes = self._crema_lfs_tar(crema_root)
            calls: list[tuple[tuple[str, ...], Path, float]] = []

            def fake_git(
                argv: list[str],
                *,
                cwd: Path,
                timeout_seconds: float,
            ) -> bytes:
                calls.append((tuple(argv), cwd, timeout_seconds))
                command = tuple(argv[3:])
                if command == ("rev-parse", "--show-toplevel"):
                    return (str(crema_root.resolve()) + "\n").encode("utf-8")
                if command == ("rev-parse", "HEAD"):
                    return (expected_revision + "\n").encode("ascii")
                if command == (
                    "archive",
                    "--format=tar",
                    "HEAD",
                    "--",
                    "AudioWAV",
                ):
                    return archive_bytes
                raise AssertionError(f"unexpected git argv: {argv}")

            mapping = discover_crema_lfs_oids(
                crema_root,
                project_root=root,
                expected_revision=expected_revision,
                git_command=fake_git,
            )
            self.assertEqual(mapping, self._synthetic_crema_lfs_oids(crema_root))
            self.assertEqual(len(calls), 3)
            for argv, cwd, timeout_seconds in calls:
                self.assertEqual(argv[:3], ("git", "-C", str(crema_root.resolve())))
                self.assertEqual(cwd, root.resolve())
                self.assertGreater(timeout_seconds, 0)
                self.assertLessEqual(timeout_seconds, 60)

    def test_crema_lfs_discovery_fails_closed_for_revision_pointer_and_binding_errors(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            discover_crema_lfs_oids,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            validate_crema_material,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            crema_root = root / "crema"
            self._crema_fixture(crema_root)
            expected_revision = "A" * 40
            selected_name = "AudioWAV/1001_DFA_ANG_XX.wav"

            def command_for(
                *,
                revision: str = expected_revision,
                archive_bytes: bytes,
            ):
                def fake_git(
                    argv: list[str],
                    *,
                    cwd: Path,
                    timeout_seconds: float,
                ) -> bytes:
                    command = tuple(argv[3:])
                    if command == ("rev-parse", "--show-toplevel"):
                        return (str(crema_root.resolve()) + "\n").encode("utf-8")
                    if command == ("rev-parse", "HEAD"):
                        return (revision + "\n").encode("ascii")
                    if command[0] == "archive":
                        return archive_bytes
                    raise AssertionError(argv)

                return fake_git

            with self.assertRaisesRegex(ValueError, "revision"):
                discover_crema_lfs_oids(
                    crema_root,
                    project_root=root,
                    expected_revision=expected_revision,
                    git_command=command_for(
                        revision="B" * 40,
                        archive_bytes=self._crema_lfs_tar(crema_root),
                    ),
                )
            with self.assertRaisesRegex(ValueError, "missing"):
                discover_crema_lfs_oids(
                    crema_root,
                    project_root=root,
                    expected_revision=expected_revision,
                    git_command=command_for(
                        archive_bytes=self._crema_lfs_tar(
                            crema_root,
                            omit=frozenset({selected_name}),
                        ),
                    ),
                )
            malformed_archive = self._crema_lfs_tar(
                crema_root,
                overrides={selected_name: b"malformed pointer"},
            )
            with self.assertRaisesRegex(ValueError, "Git LFS pointer"):
                discover_crema_lfs_oids(
                    crema_root,
                    project_root=root,
                    expected_revision=expected_revision,
                    git_command=command_for(archive_bytes=malformed_archive),
                )
            extra_pointer = (
                "version https://git-lfs.github.com/spec/v1\n"
                + "oid sha256:"
                + "C" * 64
                + "\nsize 44\n"
            ).encode("utf-8")
            with self.assertRaisesRegex(ValueError, "unbound"):
                discover_crema_lfs_oids(
                    crema_root,
                    project_root=root,
                    expected_revision=expected_revision,
                    git_command=command_for(
                        archive_bytes=self._crema_lfs_tar(
                            crema_root,
                            extra={
                                "AudioWAV/9999_DFA_ANG_XX.wav": extra_pointer,
                            },
                        ),
                    ),
                )
            mismatched = discover_crema_lfs_oids(
                crema_root,
                project_root=root,
                expected_revision=expected_revision,
                git_command=command_for(
                    archive_bytes=self._crema_lfs_tar(
                        crema_root,
                        overrides={
                            selected_name: (
                                "version https://git-lfs.github.com/spec/v1\n"
                                + "oid sha256:"
                                + "D" * 64
                                + "\nsize 44\n"
                            ).encode("utf-8"),
                        },
                    ),
                ),
            )
            with self.assertRaisesRegex(ValueError, "Git LFS OID"):
                validate_crema_material(
                    crema_root,
                    project_root=root,
                    git_lfs_oids_by_path=mismatched,
                )

    def test_write_evidence_cli_discovers_and_emits_complete_crema_lfs_oids(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import main
        from scripts.emotion_state_public_dataset_contracts import CREMA_DATASET_ID

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public_root = root / "data" / "public" / "emotion-state"
            crema_root = public_root / "crema"
            self._crema_fixture(crema_root)
            ami_archive = public_root / "ami.zip"
            ami_extract_root = public_root / "ami-extract"
            self._ami_archive(ami_archive)
            expected_revision = "A" * 40
            archive_bytes = self._crema_lfs_tar(crema_root)

            def fake_git(
                argv: list[str],
                *,
                cwd: Path,
                timeout_seconds: float,
            ) -> bytes:
                command = tuple(argv[3:])
                if command == ("rev-parse", "--show-toplevel"):
                    return (str(crema_root.resolve()) + "\n").encode("utf-8")
                if command == ("rev-parse", "HEAD"):
                    return (expected_revision + "\n").encode("ascii")
                if command[0] == "archive":
                    return archive_bytes
                raise AssertionError(argv)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--crema-root",
                        str(crema_root),
                        "--ami-archive",
                        str(ami_archive),
                        "--ami-extract-root",
                        str(ami_extract_root),
                        "--accessed-on",
                        "2026-07-15",
                        "--output-root",
                        "research/sources/emotion_state/datasets",
                        "--mode",
                        "write-evidence",
                    ],
                    project_root=root,
                    git_command=fake_git,
                    crema_expected_revision=expected_revision,
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "")
            hashes_path = (
                root
                / "research"
                / "sources"
                / "emotion_state"
                / "datasets"
                / f"{CREMA_DATASET_ID}.hashes.json"
            )
            inventory = json.loads(hashes_path.read_text(encoding="utf-8"))
            audio_entries = [
                entry
                for entry in inventory["files"]
                if "/AudioWAV/" in entry["path"]
            ]
            self.assertEqual(len(audio_entries), 3)
            for entry in audio_entries:
                self.assertEqual(entry["git_lfs_oid_sha256"], entry["sha256"])

    def test_write_evidence_rejects_nested_raw_text_and_unknown_fields_without_output(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )
        from scripts.emotion_state_public_dataset_contracts import CREMA_DATASET_ID

        injections = {
            "raw_transcript": ("raw_transcript", "synthetic raw transcript body"),
            "body": ("body", "synthetic body payload"),
            "unexpected": ("unexpected_nested_field", "blocked"),
        }
        for name, (field, value) in injections.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materials, output_root = self._material_fixture(root)
                mutated = deepcopy(materials)
                item = next(
                    item
                    for item in mutated[CREMA_DATASET_ID]["quality_inventory"]["items"]
                    if item["classification"] == "crema_pcm_wav"
                )
                item["details"][field] = value
                with self.assertRaisesRegex(ValueError, "quality inventory"):
                    write_dataset_evidence(
                        output_root=output_root,
                        accessed_on="2026-07-15",
                        materials=mutated,
                        project_root=root,
                    )
                self.assertFalse(output_root.exists())

    def test_write_evidence_rejects_raw_sentence_in_every_quality_path_surface(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
        )

        sentence = "zzzz synthetic raw transcript sentence"
        for surface in (
            "item_path",
            "ami_selected_item_path",
            "ami_archive_item_path",
            "crema_item_path",
            "selected_file_path",
            "crema_source_file_path",
            "crema_mismatch_path",
            "ami_partition_item_source_path",
            "ami_partition_paths",
            "ami_partition_definition_source_path",
            "ami_quarantine_path",
        ):
            with self.subTest(surface=surface), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materials, output_root = self._material_fixture(root)
                mutated = deepcopy(materials)
                if surface == "item_path":
                    item = next(
                        item
                        for item in mutated[AMI_DATASET_ID]["quality_inventory"]["items"]
                        if item["disposition"] == "excluded"
                    )
                    item["path"] = sentence
                    mutated[AMI_DATASET_ID]["quality_inventory"]["items"].sort(
                        key=lambda value: value["path"]
                    )
                elif surface == "ami_selected_item_path":
                    item = next(
                        item
                        for item in mutated[AMI_DATASET_ID]["quality_inventory"]["items"]
                        if item["classification"]
                        == "speaker_aligned_orthographic_transcript"
                    )
                    item["path"] = sentence
                    mutated[AMI_DATASET_ID]["quality_inventory"]["items"].sort(
                        key=lambda value: value["path"]
                    )
                elif surface == "ami_archive_item_path":
                    item = next(
                        item
                        for item in mutated[AMI_DATASET_ID]["quality_inventory"]["items"]
                        if item["classification"] == "downloaded_archive"
                    )
                    item["path"] = sentence
                    mutated[AMI_DATASET_ID]["quality_inventory"]["items"].sort(
                        key=lambda value: value["path"]
                    )
                elif surface == "crema_item_path":
                    item = next(
                        item
                        for item in mutated[CREMA_DATASET_ID]["quality_inventory"]["items"]
                        if item["classification"] == "crema_demographic_metadata"
                    )
                    item["path"] = sentence
                    mutated[CREMA_DATASET_ID]["quality_inventory"]["items"].sort(
                        key=lambda value: value["path"]
                    )
                elif surface == "selected_file_path":
                    item = next(
                        item
                        for item in mutated[AMI_DATASET_ID]["quality_inventory"]["items"]
                        if item["classification"]
                        == "speaker_aligned_orthographic_transcript"
                    )
                    item["selected_file_path"] = sentence
                elif surface == "crema_source_file_path":
                    item = next(
                        item
                        for item in mutated[CREMA_DATASET_ID]["quality_inventory"]["items"]
                        if item["classification"] == "crema_pcm_wav"
                    )
                    item["details"]["source_label_evidence"]["source_file_path"] = sentence
                elif surface == "crema_mismatch_path":
                    mutated[CREMA_DATASET_ID]["quality_inventory"]["source_metadata"][
                        "official_mismatch_wav_counterparts"
                    ] = [sentence]
                elif surface == "ami_partition_item_source_path":
                    item = next(
                        item
                        for item in mutated[AMI_DATASET_ID]["quality_inventory"]["items"]
                        if item["classification"] == "official_partition_metadata"
                    )
                    item["details"]["source_file_path"] = sentence
                elif surface == "ami_partition_paths":
                    mutated[AMI_DATASET_ID]["quality_inventory"]["source_metadata"][
                        "official_partition_paths"
                    ] = [sentence]
                elif surface == "ami_partition_definition_source_path":
                    metadata = mutated[AMI_DATASET_ID]["quality_inventory"][
                        "source_metadata"
                    ]
                    metadata["official_partition_definitions"][0][
                        "source_file_path"
                    ] = sentence
                    metadata["official_partition_paths"] = sorted(
                        definition["source_file_path"]
                        for definition in metadata["official_partition_definitions"]
                    )
                else:
                    mutated[AMI_DATASET_ID]["quality_inventory"][
                        "dependency_quarantine"
                    ] = [{
                        "path": sentence,
                        "reason": "required_participant_identity_missing",
                    }]
                with self.assertRaisesRegex(ValueError, "quality inventory"):
                    write_dataset_evidence(
                        output_root=output_root,
                        accessed_on="2026-07-15",
                        materials=mutated,
                        project_root=root,
                    )
                self.assertFalse(output_root.exists())

        invalid_paths = (
            "/absolute/member.xml",
            "C:/drive-qualified/member.xml",
            "archive\\member.xml",
            "archive/\x00member.xml",
            "archive/./member.xml",
            "archive/../member.xml",
            "archive//member.xml",
            "archive/cafe\u0301.xml",
            "archive/member\n.xml",
            "archive/bad:name.xml",
        )
        for invalid_path in invalid_paths:
            with self.subTest(
                surface="item_path_grammar",
                invalid_path=repr(invalid_path),
            ), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materials, output_root = self._material_fixture(root)
                mutated = deepcopy(materials)
                item = next(
                    item
                    for item in mutated[AMI_DATASET_ID]["quality_inventory"]["items"]
                    if item["disposition"] == "excluded"
                )
                item["path"] = invalid_path
                mutated[AMI_DATASET_ID]["quality_inventory"]["items"].sort(
                    key=lambda value: value["path"]
                )
                with self.assertRaisesRegex(ValueError, "quality inventory"):
                    write_dataset_evidence(
                        output_root=output_root,
                        accessed_on="2026-07-15",
                        materials=mutated,
                        project_root=root,
                    )
                self.assertFalse(output_root.exists())

    def test_write_evidence_rejects_deep_unknown_fields_and_raw_identifier_content(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
        )

        def mutate_known_filename(materials: dict[str, dict[str, object]]) -> None:
            item = next(
                item
                for item in materials[CREMA_DATASET_ID]["quality_inventory"]["items"]
                if item["classification"] == "crema_wav"
            )
            item["details"]["filename_metadata"]["unexpected"] = "blocked"

        def mutate_source_column(materials: dict[str, dict[str, object]]) -> None:
            item = next(
                item
                for item in materials[CREMA_DATASET_ID]["quality_inventory"]["items"]
                if item["classification"] == "crema_pcm_wav"
            )
            item["details"]["source_label_evidence"][
                "source_column"
            ] = "synthetic raw transcript sentence"

        def mutate_participant_id(materials: dict[str, dict[str, object]]) -> None:
            materials[AMI_DATASET_ID]["quality_inventory"]["source_metadata"][
                "participants"
            ] = ["synthetic raw transcript sentence"]

        def mutate_mismatch_path(materials: dict[str, dict[str, object]]) -> None:
            materials[CREMA_DATASET_ID]["quality_inventory"]["source_metadata"][
                "official_mismatch_wav_counterparts"
            ] = ["synthetic raw transcript sentence"]

        def mutate_recording_site(materials: dict[str, dict[str, object]]) -> None:
            materials[AMI_DATASET_ID]["quality_inventory"]["source_metadata"][
                "recording_sites"
            ] = ["synthetic raw transcript sentence"]

        for name, mutate in {
            "known_filename": mutate_known_filename,
            "source_column": mutate_source_column,
            "participant_id": mutate_participant_id,
            "mismatch_path": mutate_mismatch_path,
            "recording_site": mutate_recording_site,
        }.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                materials, output_root = self._material_fixture(root)
                mutated = deepcopy(materials)
                mutate(mutated)
                with self.assertRaisesRegex(ValueError, "quality inventory"):
                    write_dataset_evidence(
                        output_root=output_root,
                        accessed_on="2026-07-15",
                        materials=mutated,
                        project_root=root,
                    )
                self.assertFalse(output_root.exists())

    def test_write_evidence_rejects_cross_dataset_and_file_set_mismatch_without_output(
        self,
    ) -> None:
        from scripts.build_emotion_state_public_dataset_manifests import (
            write_dataset_evidence,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials, output_root = self._material_fixture(root)
            cross_dataset = deepcopy(materials)
            cross_dataset[CREMA_DATASET_ID]["hash_inventory"][
                "dataset_id"
            ] = AMI_DATASET_ID
            with self.assertRaisesRegex(ValueError, "hash inventory dataset_id"):
                write_dataset_evidence(
                    output_root=output_root,
                    accessed_on="2026-07-15",
                    materials=cross_dataset,
                    project_root=root,
                )
            self.assertFalse(output_root.exists())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materials, output_root = self._material_fixture(root)
            mismatch = deepcopy(materials)
            item = next(
                item
                for item in mismatch[CREMA_DATASET_ID]["quality_inventory"]["items"]
                if item["classification"] == "crema_pcm_wav"
            )
            item["selected_file_path"] = "different/selected.wav"
            with self.assertRaisesRegex(ValueError, "selected file set"):
                write_dataset_evidence(
                    output_root=output_root,
                    accessed_on="2026-07-15",
                    materials=mismatch,
                    project_root=root,
                )
            self.assertFalse(output_root.exists())


class SplitManifestV2Tests(unittest.TestCase):
    def test_v2_rejects_unhashable_manifest_requirement_value_with_value_error(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        manifest["dependency_requirement_by_key"]["speaker"] = []
        with self.assertRaisesRegex(
            ValueError,
            "dependency_requirement_by_key values must be strings",
        ):
            validate_split_manifest_v2(manifest, records)

    def test_v2_rejects_unhashable_manifest_status_value_with_value_error(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        manifest["dependency_status_by_key"]["speaker"] = {}
        with self.assertRaisesRegex(
            ValueError,
            "dependency_status_by_key values must be strings",
        ):
            validate_split_manifest_v2(manifest, records)

    def test_v2_rejects_unhashable_record_status_value_with_value_error(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        records[0]["dependency_status_by_key"]["speaker"] = []
        with self.assertRaisesRegex(
            ValueError,
            "case-training-a.dependency_status_by_key values must be strings",
        ):
            validate_split_manifest_v2(manifest, records)

    def test_v2_rejects_unknown_covered_partition_case_before_dereference(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        manifest["calibration"]["case_ids"] = ["case-missing"]
        with self.assertRaises(ValueError):
            validate_split_manifest_v2(manifest, records)

    def test_v2_profile_registry_is_exact_and_rejects_unsupported_profiles(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            DEPENDENCY_PROFILES_V2,
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        self.assertEqual(tuple(DEPENDENCY_PROFILES_V2), (
            "crema-d-session-nesting-verified",
            "crema-d-session-nesting-unverified",
            "ami-scenario-series",
            "ami-natural-standalone",
        ))
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        manifest["dependency_profile_id"] = "unsupported-profile"
        with self.assertRaisesRegex(ValueError, "unsupported dependency profile"):
            validate_split_manifest_v2(manifest, records)

    def test_v2_rejects_mixed_dataset_records(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import AMI_DATASET_ID
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        records[1]["dataset_manifest_id"] = AMI_DATASET_ID
        with self.assertRaisesRegex(ValueError, "one dataset manifest ID"):
            validate_split_manifest_v2(manifest, records)

    def test_v2_dependency_rules_fail_closed(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            DEPENDENCY_KEYS_V2,
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        self.assertEqual(DEPENDENCY_KEYS_V2, (
            "speaker", "call_session", "dialogue_dyad", "source_corpus",
            "scripted_scenario", "meeting_series", "recording_site",
        ))
        validate_split_manifest_v2(manifest, records)
        leaked = json.loads(json.dumps(manifest))
        leaked["calibration"]["dependency_groups"]["speaker"] = ["speaker-training"]
        with self.assertRaisesRegex(ValueError, "speaker leakage"):
            validate_split_manifest_v2(leaked, records)

    def test_required_unknown_is_quarantined_and_covering_key_is_proven(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2(include_required_unknown=True)
        manifest = fixture_split_manifest_v2(records)
        validated = validate_split_manifest_v2(manifest, records)
        self.assertEqual(validated["dependency_unknown_quarantine"]["case_ids"], ["case-unknown"])
        self.assertFalse(validated["dependency_unknown_quarantine"]["claims_allowed"])
        broken = json.loads(json.dumps(manifest))
        broken["dependency_covering_key_by_key"]["call_session"] = "missing-key"
        with self.assertRaisesRegex(ValueError, "covering key"):
            validate_split_manifest_v2(broken, records)


class CohortReleaseTests(unittest.TestCase):
    @staticmethod
    def _pattern_candidate() -> dict[str, object]:
        return {
            "candidate_id": "synthetic-candidate-1",
            "hypothesis": "synthetic relationship for structural validation only",
            "feature_definition": {
                "relationship": "synthetic structural relationship",
                "direction": "increase",
                "null_comparator": "no_association",
                "minimum_observed_effect": 0.0,
                "eligible_turn_definition": "synthetic_fixture_turns_only",
                "search_budget": 1,
                "tested_hypothesis_count": 1,
                "max_qualifying_turns_per_speaker": 2,
            },
            "target_operational_signal": "confusion",
            "discovery_dataset_version": "synthetic-fixture-v1",
            "unique_speaker_count": 5,
            "independent_turn_count": 10,
            "annotation_agreement": {
                "metric": "nominal_krippendorff_alpha",
                "point_estimate": None,
                "lower_95_ci": None,
                "upper_95_ci": None,
                "status": "not_evaluated_in_phase_a",
            },
            "status": "candidate_hypothesis_only",
            "runtime_influence_allowed": False,
        }

    def test_four_speakers_suppress_and_ten_speakers_pass(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        suppressed = build_cohort_release(fixture_records(12, 4), fixture_request())
        self.assertEqual(suppressed["release_status"], "suppressed")
        self.assertIn(
            "minimum_unique_speakers_not_met",
            suppressed["suppression_reason_codes"],
        )
        self.assertEqual(suppressed["aggregate_metrics"], {})
        released = build_cohort_release(fixture_records(10, 10), fixture_request())
        self.assertEqual(released["release_status"], "released")
        self.assertEqual(released["unique_speaker_count"], 10)
        self.assertNotIn("speaker_keys", released)
        self.assertFalse(released["contains_per_speaker_rows"])

    def test_five_speaker_twenty_turn_cohort_is_discovery_only(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            MAX_DISCOVERY_TURNS_PER_SPEAKER,
            MIN_DISCOVERY_SPEAKERS,
            MIN_DISCOVERY_TURNS,
            build_cohort_release,
            evaluate_discovery_gate,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(20, 5)
        speaker_counts: dict[tuple[str, str], int] = {}
        for record in records:
            key = (record["dataset_manifest_id"], record["source_speaker_id"])
            speaker_counts[key] = speaker_counts.get(key, 0) + 1
        capped_discovery_turns = sum(
            min(count, MAX_DISCOVERY_TURNS_PER_SPEAKER)
            for count in speaker_counts.values()
        )
        self.assertGreaterEqual(len(speaker_counts), MIN_DISCOVERY_SPEAKERS)
        self.assertGreaterEqual(capped_discovery_turns, MIN_DISCOVERY_TURNS)
        discovery = evaluate_discovery_gate(records)
        self.assertTrue(discovery["discovery_eligible"])
        self.assertEqual(discovery["unique_speaker_count"], 5)
        self.assertEqual(discovery["retained_turn_count"], 10)
        self.assertEqual(discovery, evaluate_discovery_gate(list(reversed(records))))
        release = build_cohort_release(records, fixture_request())
        self.assertEqual(release["release_status"], "suppressed")
        self.assertEqual(release["unique_speaker_count"], 5)

    def test_discovery_gate_rejects_missing_metric_membership_keys(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            canonical_record_digest,
            evaluate_discovery_gate,
            fixture_records,
        )

        records = fixture_records(20, 5)
        records[0]["metric_cell_memberships"] = {
            "eligible_call_count": ["__scalar__"],
        }
        records[0]["canonical_record_digest"] = canonical_record_digest(records[0])

        with self.assertRaisesRegex(
            ValueError,
            "metric_cell_memberships.*metric allowlist",
        ):
            evaluate_discovery_gate(records)

    def test_discovery_gate_rejects_identity_bearing_scalar_membership(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            canonical_record_digest,
            evaluate_discovery_gate,
            fixture_records,
        )

        records = fixture_records(20, 5)
        records[0]["metric_cell_memberships"]["eligible_call_count"] = [
            "person@example.test",
        ]
        records[0]["canonical_record_digest"] = canonical_record_digest(records[0])

        with self.assertRaisesRegex(
            ValueError,
            "metric_cell_memberships.eligible_call_count.*__scalar__",
        ):
            evaluate_discovery_gate(records)

    def test_discovery_gate_rejects_nested_membership_on_ineligible_record(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            canonical_record_digest,
            evaluate_discovery_gate,
            fixture_records,
        )

        records = fixture_records(20, 5)
        records[0]["eligible"] = False
        records[0]["metric_cell_memberships"]["audio_quality_bucket_counts"] = [
            {"email_address": "person@example.test"},
        ]
        records[0]["canonical_record_digest"] = canonical_record_digest(records[0])

        with self.assertRaisesRegex(
            ValueError,
            "metric_cell_memberships.audio_quality_bucket_counts.*unique string list",
        ):
            evaluate_discovery_gate(records)

    def test_discovery_gate_requires_both_minimum_thresholds(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            evaluate_discovery_gate,
            fixture_records,
        )

        cases = {
            "too_few_retained_turns": (
                fixture_records(9, 6),
                {
                    "discovery_eligible": False,
                    "unique_speaker_count": 6,
                    "retained_turn_count": 9,
                },
            ),
            "too_few_speakers": (
                fixture_records(20, 4),
                {
                    "discovery_eligible": False,
                    "unique_speaker_count": 4,
                    "retained_turn_count": 8,
                },
            ),
        }
        for name, (records, expected) in cases.items():
            with self.subTest(name=name):
                self.assertEqual(evaluate_discovery_gate(records), expected)

    def test_discovery_gate_rejects_mixed_dataset_input(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            evaluate_discovery_gate,
            fixture_cross_corpus_records,
        )

        with self.assertRaisesRegex(ValueError, "cross-corpus discovery"):
            evaluate_discovery_gate(fixture_cross_corpus_records())

    def test_discovery_gate_rejects_duplicate_canonical_records_before_filter_and_cap(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            canonical_record_digest,
            evaluate_discovery_gate,
            fixture_records,
        )

        five_unique_records = fixture_records(5, 5)
        duplicated_to_false_ten_turn_floor = (
            five_unique_records + deepcopy(five_unique_records)
        )

        duplicate_beyond_speaker_cap = fixture_records(10, 5)
        duplicate_beyond_speaker_cap.append(deepcopy(duplicate_beyond_speaker_cap[0]))

        ineligible_duplicate = fixture_records(5, 5)
        ineligible_duplicate[0]["eligible"] = False
        ineligible_duplicate[0]["canonical_record_digest"] = canonical_record_digest(
            ineligible_duplicate[0]
        )
        ineligible_duplicate.append(deepcopy(ineligible_duplicate[0]))

        invalid_inputs = {
            "five_unique_records_duplicated_to_ten": (
                duplicated_to_false_ten_turn_floor
            ),
            "duplicate_beyond_two_per_speaker_cap": duplicate_beyond_speaker_cap,
            "ineligible_duplicate_before_filter": ineligible_duplicate,
        }
        for name, records in invalid_inputs.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ValueError,
                    "duplicate canonical_record_digest",
                ):
                    evaluate_discovery_gate(records)

    def test_duplicate_actor_ids_deduplicate_and_contribution_is_deterministic(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )
        from scripts.emotion_state_public_dataset_contracts import CREMA_DATASET_ID

        records = fixture_records(
            12,
            10,
            dataset_manifest_id=CREMA_DATASET_ID,
        )
        request = fixture_request(
            source_label="public-only",
            unique_speaker_basis="public_dataset_actor_id",
        )
        ordered = build_cohort_release(records, request)
        reversed_release = build_cohort_release(list(reversed(records)), request)
        self.assertEqual(ordered["release_status"], "released")
        self.assertEqual(ordered["unique_speaker_count"], 10)
        self.assertEqual(ordered["eligible_record_count"], 10)
        self.assertEqual(ordered["max_contribution_per_speaker"], 1)
        self.assertEqual(
            ordered["dedup_evidence_digest"],
            reversed_release["dedup_evidence_digest"],
        )

    def test_release_records_bind_approved_dataset_basis_id_and_digest_provenance(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
        )

        private_records = fixture_records(
            10,
            10,
            dataset_manifest_id="private-customer-audio-v1",
        )
        email_actor_records = fixture_records(
            10,
            10,
            dataset_manifest_id=CREMA_DATASET_ID,
        )
        email_actor_records[0]["source_speaker_id"] = "actor@example.com"
        ami_meeting_id_records = fixture_records(
            10,
            10,
            dataset_manifest_id=AMI_DATASET_ID,
        )
        for index, record in enumerate(ami_meeting_id_records):
            record["source_speaker_id"] = f"ES{2000 + index:04d}a"
        uncontrolled_synthetic_records = fixture_records(
            10,
            10,
            dataset_manifest_id="synthetic-corpus-uncontrolled-v1",
        )
        forged_digest_records = fixture_records(10, 10)
        forged_digest_records[0]["canonical_record_digest"] = "A" * 64

        invalid_cases = {
            "private_dataset": (
                private_records,
                fixture_request(),
                "approved|dataset",
            ),
            "email_public_actor_id": (
                email_actor_records,
                fixture_request(
                    source_label="public-only",
                    unique_speaker_basis="public_dataset_actor_id",
                ),
                "actor|speaker.*ID|identifier",
            ),
            "crema_participant_basis": (
                fixture_records(10, 10, dataset_manifest_id=CREMA_DATASET_ID),
                fixture_request(
                    source_label="public-only",
                    unique_speaker_basis="public_dataset_participant_id",
                ),
                "basis|CREMA",
            ),
            "ami_actor_basis": (
                fixture_records(10, 10, dataset_manifest_id=AMI_DATASET_ID),
                fixture_request(
                    source_label="public-only",
                    unique_speaker_basis="public_dataset_actor_id",
                ),
                "basis|AMI",
            ),
            "ami_meeting_id_as_participant": (
                ami_meeting_id_records,
                fixture_request(
                    source_label="public-only",
                    unique_speaker_basis="public_dataset_participant_id",
                ),
                "participant|speaker.*ID|identifier",
            ),
            "uncontrolled_synthetic_namespace": (
                uncontrolled_synthetic_records,
                fixture_request(),
                "controlled synthetic|dataset",
            ),
            "forged_canonical_record_digest": (
                forged_digest_records,
                fixture_request(),
                "canonical record digest mismatch",
            ),
        }
        for name, (records, request, error_pattern) in invalid_cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, error_pattern):
                    build_cohort_release(records, request)

    def test_discovery_records_share_the_release_provenance_validator(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            evaluate_discovery_gate,
            fixture_records,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
        )

        private_records = fixture_records(
            10,
            10,
            dataset_manifest_id="private-customer-audio-v1",
        )
        email_actor_records = fixture_records(
            10,
            10,
            dataset_manifest_id=CREMA_DATASET_ID,
        )
        email_actor_records[0]["source_speaker_id"] = "actor@example.com"
        wrong_crema_id_records = fixture_records(
            10,
            10,
            dataset_manifest_id=CREMA_DATASET_ID,
        )
        for index, record in enumerate(wrong_crema_id_records):
            record["source_speaker_id"] = f"ES{2000 + index:04d}.A"
        ami_meeting_id_records = fixture_records(
            10,
            10,
            dataset_manifest_id=AMI_DATASET_ID,
        )
        for index, record in enumerate(ami_meeting_id_records):
            record["source_speaker_id"] = f"ES{2000 + index:04d}a"
        uncontrolled_synthetic_records = fixture_records(
            10,
            10,
            dataset_manifest_id="synthetic-corpus-uncontrolled-v1",
        )
        forged_digest_records = fixture_records(10, 10)
        forged_digest_records[0]["canonical_record_digest"] = "A" * 64

        invalid_cases = {
            "private_dataset": (private_records, "approved|dataset"),
            "email_public_actor_id": (
                email_actor_records,
                "actor|speaker.*ID|identifier",
            ),
            "wrong_public_dataset_id_syntax": (
                wrong_crema_id_records,
                "actor|speaker.*ID|identifier",
            ),
            "ami_meeting_id_as_participant": (
                ami_meeting_id_records,
                "participant|speaker.*ID|identifier",
            ),
            "uncontrolled_synthetic_namespace": (
                uncontrolled_synthetic_records,
                "controlled synthetic|dataset",
            ),
            "forged_canonical_record_digest": (
                forged_digest_records,
                "canonical record digest mismatch",
            ),
        }
        for name, (records, error_pattern) in invalid_cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, error_pattern):
                    evaluate_discovery_gate(records)

    def test_missing_or_nondeterministic_speaker_evidence_suppresses(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        cases: dict[str, tuple[list[dict[str, object]], dict[str, object], str]] = {
            "missing_basis": (
                fixture_records(10, 10),
                fixture_request(unique_speaker_basis=None),
                "speaker_basis_missing",
            ),
            "missing_timestamp": (
                fixture_records(10, 10),
                fixture_request(),
                "deterministic_contribution_evidence_missing",
            ),
            "missing_digest": (
                fixture_records(10, 10),
                fixture_request(),
                "deterministic_contribution_evidence_missing",
            ),
        }
        cases["missing_timestamp"][0][0].pop("source_timestamp")
        cases["missing_digest"][0][0].pop("canonical_record_digest")
        for name, (records, request, reason) in cases.items():
            with self.subTest(name=name):
                release = build_cohort_release(records, request)
                self.assertEqual(release["release_status"], "suppressed")
                self.assertIn(reason, release["suppression_reason_codes"])

    def test_record_missing_eligible_rejects_with_value_error(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        records[0].pop("eligible")
        with self.assertRaisesRegex(ValueError, "missing eligible"):
            build_cohort_release(records, fixture_request())

    def test_identifier_and_identity_prediction_speaker_bases_reject(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            RESERVED_DISABLED_SPEAKER_BASE,
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        forbidden = (
            "call_id",
            "session_id",
            "turn_id",
            "name",
            "phone_number",
            "email_address",
            "account_id",
            "crm_id",
            "undocumented_identifier_hash",
            "voiceprint",
            "speaker_embedding",
            "biometric_match",
            "provider_identity_prediction",
            "model_identity_prediction",
            "probabilistic_dedup_as_certain",
        )
        for basis in forbidden:
            with self.subTest(basis=basis):
                with self.assertRaisesRegex(ValueError, "speaker basis"):
                    build_cohort_release(
                        fixture_records(10, 10),
                        fixture_request(unique_speaker_basis=basis),
                    )
        with self.assertRaisesRegex(ValueError, "reserved.*disabled"):
            build_cohort_release(
                fixture_records(10, 10),
                fixture_request(unique_speaker_basis=RESERVED_DISABLED_SPEAKER_BASE),
            )

    def test_cross_corpus_identity_cannot_be_pooled(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_cross_corpus_records,
            fixture_request,
        )

        result = build_cohort_release(fixture_cross_corpus_records(), fixture_request())
        self.assertEqual(result["release_status"], "suppressed")
        self.assertIn(
            "cross_corpus_identity_not_proven",
            result["suppression_reason_codes"],
        )

    def test_non_null_cross_corpus_identity_digest_rejects_even_when_valid(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        with self.assertRaisesRegex(ValueError, "cross_corpus_identity_evidence_digest.*null"):
            build_cohort_release(
                fixture_records(10, 10),
                fixture_request(cross_corpus_identity_evidence_digest="A" * 64),
            )

    def test_sparse_output_cells_are_omitted_not_zeroed(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_record_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        request = fixture_request()
        request["operational_aggregate"]["audio_quality_bucket_counts"] = {
            "usable": 1,
            "unavailable": 9,
        }
        for index, record in enumerate(records):
            record["metric_cell_memberships"]["audio_quality_bucket_counts"] = [
                "usable" if index == 0 else "unavailable"
            ]
            record["canonical_record_digest"] = canonical_record_digest(record)
        release = build_cohort_release(records, request)
        self.assertEqual(release["release_status"], "released")
        self.assertNotIn("audio_quality_bucket_counts", release["aggregate_metrics"])
        self.assertNotIn(
            "audio_quality_bucket_counts",
            release["output_cell_unique_speaker_counts"],
        )
        self.assertNotIn('"usable":0', json.dumps(release, separators=(",", ":")))

        zero_cell_records = fixture_records(10, 10)
        zero_cell_request = fixture_request()
        zero_cell_request["operational_aggregate"]["audio_quality_bucket_counts"] = {
            "usable": 0,
            "unavailable": 10,
        }
        zero_cell_release = build_cohort_release(zero_cell_records, zero_cell_request)
        self.assertEqual(
            zero_cell_release["aggregate_metrics"]["audio_quality_bucket_counts"],
            {"unavailable": 10},
        )
        self.assertEqual(
            zero_cell_release["output_cell_unique_speaker_counts"][
                "audio_quality_bucket_counts"
            ],
            {"unavailable": 10},
        )

    def test_count_map_values_must_match_membership_derived_support(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_record_digest,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        invalid_builds: dict[str, tuple[list[dict[str, object]], dict[str, object]]] = {}

        single_membership_records = fixture_records(10, 10)
        single_membership_request = fixture_request()
        single_membership_request["operational_aggregate"][
            "audio_quality_bucket_counts"
        ] = {"unavailable": 5, "usable": 5}
        invalid_builds["five_five_single_membership"] = (
            single_membership_records,
            single_membership_request,
        )

        dual_membership_records = fixture_records(10, 10)
        for record in dual_membership_records:
            record["metric_cell_memberships"]["audio_quality_bucket_counts"] = [
                "unavailable",
                "usable",
            ]
            record["canonical_record_digest"] = canonical_record_digest(record)
        dual_membership_request = fixture_request()
        dual_membership_request["operational_aggregate"][
            "audio_quality_bucket_counts"
        ] = {"unavailable": 5, "usable": 5}
        invalid_builds["five_five_dual_membership"] = (
            dual_membership_records,
            dual_membership_request,
        )

        zero_count_records = fixture_records(10, 10)
        zero_count_request = fixture_request()
        zero_count_request["operational_aggregate"][
            "audio_quality_bucket_counts"
        ] = {"unavailable": 0, "usable": 10}
        invalid_builds["zero_count_nonzero_membership"] = (
            zero_count_records,
            zero_count_request,
        )

        for name, (records, request) in invalid_builds.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "count-map.*support"):
                    build_cohort_release(records, request)

        valid_release = build_cohort_release(
            fixture_records(10, 10),
            fixture_request(),
        )
        contradictory_release = deepcopy(valid_release)
        contradictory_release["aggregate_metrics"]["audio_quality_bucket_counts"][
            "unavailable"
        ] = 9
        with self.assertRaisesRegex(ValueError, "count-map.*support"):
            validate_cohort_release(contradictory_release)

    def test_each_selected_record_has_exactly_one_cell_per_count_map_metric(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_record_digest,
            fixture_records,
            fixture_request,
        )

        count_map_cases = {
            "audio_quality_bucket_counts": ("unavailable", "usable"),
            "evidence_policy_version_counts": (
                "emotion-state-evidence-v1",
                "emotion-state-evidence-v2",
            ),
        }
        for metric, cells in count_map_cases.items():
            with self.subTest(metric=metric):
                records = fixture_records(20, 20)
                request = fixture_request()
                request["operational_aggregate"]["eligible_call_count"] = 20
                request["operational_aggregate"][
                    "audio_quality_bucket_counts"
                ] = {"unavailable": 20}
                request["operational_aggregate"][
                    "evidence_policy_version_counts"
                ] = {"emotion-state-evidence-v1": 20}
                request["operational_aggregate"][metric] = {
                    cells[0]: 10,
                    cells[1]: 10,
                }
                for index, record in enumerate(records):
                    record["metric_cell_memberships"][metric] = (
                        list(cells) if index < 10 else []
                    )
                    record["canonical_record_digest"] = canonical_record_digest(record)

                with self.assertRaisesRegex(ValueError, "exactly one.*count-map"):
                    build_cohort_release(records, request)

    def test_released_scalar_support_equals_eligible_record_count_direct_and_history(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        request = fixture_request()
        request["operational_aggregate"]["eligible_call_count"] = 20
        request["operational_aggregate"]["audio_quality_bucket_counts"] = {
            "unavailable": 20,
        }
        request["operational_aggregate"]["evidence_policy_version_counts"] = {
            "emotion-state-evidence-v1": 20,
        }
        release = build_cohort_release(fixture_records(20, 20), request)

        def later_request(history: list[dict[str, object]]) -> dict[str, object]:
            later = fixture_request(
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
            )
            later["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-08-01",
                "window_end_date": "2026-08-14",
                "timezone": "UTC",
            }
            later["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
            return later

        for metric in (
            "eligible_call_count",
            "audio_analysis_availability_rate",
            "abstention_rate",
        ):
            invalid = deepcopy(release)
            invalid["output_cell_unique_speaker_counts"][metric] = 10
            with self.subTest(path="direct", metric=metric):
                with self.assertRaisesRegex(
                    ValueError,
                    "scalar metric.*support.*eligible_record_count",
                ):
                    validate_cohort_release(invalid)
            with self.subTest(path="history", metric=metric):
                history = [invalid]
                with self.assertRaisesRegex(
                    ValueError,
                    "scalar metric.*support.*eligible_record_count",
                ):
                    build_cohort_release(
                        fixture_records(10, 10),
                        later_request(history),
                    )

    def test_released_count_map_total_cannot_exceed_eligible_count_direct_and_history(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        release = build_cohort_release(fixture_records(10, 10), fixture_request())
        count_map_cases = {
            "audio_quality_bucket_counts": {
                "unavailable": 10,
                "usable": 10,
            },
            "evidence_policy_version_counts": {
                "emotion-state-evidence-v1": 10,
                "emotion-state-evidence-v2": 10,
            },
        }

        for metric, cells in count_map_cases.items():
            invalid = deepcopy(release)
            invalid["aggregate_metrics"][metric] = deepcopy(cells)
            invalid["output_cell_unique_speaker_counts"][metric] = deepcopy(cells)
            with self.subTest(path="direct", metric=metric):
                with self.assertRaisesRegex(
                    ValueError,
                    "count-map metric.*total.*eligible_record_count",
                ):
                    validate_cohort_release(invalid)

            history = [invalid]
            later = fixture_request(
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
            )
            later["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-08-01",
                "window_end_date": "2026-08-14",
                "timezone": "UTC",
            }
            later["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
            with self.subTest(path="history", metric=metric):
                with self.assertRaisesRegex(
                    ValueError,
                    "count-map metric.*total.*eligible_record_count",
                ):
                    build_cohort_release(fixture_records(10, 10), later)

    def test_request_cannot_assert_output_cell_support(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        request = fixture_request()
        self.assertNotIn("output_cell_unique_speaker_counts", request)
        request["output_cell_unique_speaker_counts"] = {
            metric: 10 for metric in (
                "eligible_call_count",
                "audio_analysis_availability_rate",
                "abstention_rate",
            )
        }
        with self.assertRaisesRegex(ValueError, "request.*fields mismatch"):
            build_cohort_release(fixture_records(10, 10), request)

    def test_ineligible_foreign_dataset_record_still_suppresses(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_record_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        foreign = deepcopy(records[0])
        foreign["dataset_manifest_id"] = "synthetic-fixture-dataset-b-v1"
        foreign["source_speaker_id"] = "fixture-speaker-999"
        foreign["eligible"] = False
        foreign["canonical_record_digest"] = canonical_record_digest(foreign)
        records.append(foreign)
        release = build_cohort_release(records, fixture_request())
        self.assertEqual(release["release_status"], "suppressed")
        self.assertIn(
            "cross_corpus_identity_not_proven",
            release["suppression_reason_codes"],
        )

    def test_non_fixed_filtered_sliced_and_reconstructive_windows_reject(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        invalid_requests = {
            "open_window": fixture_request(window_policy="fixed_open"),
            "rolling_window": fixture_request(window_policy="rolling_closed"),
            "overlapping_window": fixture_request(window_relationship="overlapping"),
            "nested_window": fixture_request(window_relationship="nested"),
            "repeated_window": fixture_request(window_relationship="repeated"),
            "filtered": fixture_request(ad_hoc_filters=["campaign_id"]),
            "demographic_slice": fixture_request(slice_dimensions=["demographic"]),
            "campaign_slice": fixture_request(slice_dimensions=["campaign"]),
            "state_slice": fixture_request(slice_dimensions=["state"]),
            "signal_slice": fixture_request(slice_dimensions=["signal"]),
            "complementary": fixture_request(complementary_query=True),
            "differencing": fixture_request(differencing_query=True),
        }
        for name, request in invalid_requests.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    build_cohort_release(fixture_records(10, 10), request)

    def test_replacement_binds_prior_digest_and_preserves_window_and_allowlist(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_digest,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        prior = build_cohort_release(records, fixture_request())
        prior_digest = canonical_release_digest(prior)
        history = [prior]
        replacement_request = fixture_request(
            window_relationship="replacement",
            authoritative_release_history=history,
            authoritative_release_history_digest=canonical_release_history_digest(history),
            previous_release_digest=prior_digest,
            release_replaces_digest=prior_digest,
            replacement_scope="entire_prior_release",
        )
        replacement = build_cohort_release(records, replacement_request)
        self.assertEqual(replacement["release_status"], "released")
        self.assertEqual(replacement["previous_release_digest"], prior_digest)
        self.assertEqual(replacement["release_replaces_digest"], prior_digest)
        self.assertEqual(replacement["aggregation_window"], prior["aggregation_window"])
        self.assertEqual(
            replacement["metric_allowlist_version"],
            prior["metric_allowlist_version"],
        )
        invalid_requests = {
            "wrong_digest": dict(replacement_request, release_replaces_digest="B" * 64),
            "partial": dict(replacement_request, replacement_scope="partial"),
            "changed_allowlist": dict(
                replacement_request,
                metric_allowlist_version="emotion-state-operational-aggregate-v2",
            ),
            "wrong_history_digest": dict(
                replacement_request,
                authoritative_release_history_digest="C" * 64,
            ),
            "changed_window": deepcopy(replacement_request),
        }
        invalid_requests["changed_window"]["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-07-02",
            "window_end_date": "2026-07-14",
            "timezone": "UTC",
        }
        for name, request in invalid_requests.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    build_cohort_release(records, request)

    def test_candidate_replacement_preserves_fixed_cohort_evidence(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_record_digest,
            canonical_release_digest,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )
        from scripts.emotion_state_public_dataset_contracts import CREMA_DATASET_ID

        records = fixture_records(10, 10)
        root = build_cohort_release(records, fixture_request())
        root_digest = canonical_release_digest(root)
        history = [root]

        def replacement_request(**overrides: object) -> dict[str, object]:
            request = fixture_request(
                window_relationship="replacement",
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
                previous_release_digest=root_digest,
                release_replaces_digest=root_digest,
                replacement_scope="entire_prior_release",
                **overrides,
            )
            return request

        aggregate_correction_request = replacement_request()
        aggregate_correction_request["operational_aggregate"][
            "audio_analysis_availability_rate"
        ] = 0.25
        aggregate_correction = build_cohort_release(
            records,
            aggregate_correction_request,
        )
        self.assertEqual(
            aggregate_correction["aggregate_metrics"][
                "audio_analysis_availability_rate"
            ],
            0.25,
        )
        for field in (
            "source_label",
            "unique_speaker_basis",
            "dedup_evidence_digest",
            "eligible_record_count",
            "unique_speaker_count",
        ):
            self.assertEqual(aggregate_correction[field], root[field], field)

        crema_records = fixture_records(
            10,
            10,
            dataset_manifest_id=CREMA_DATASET_ID,
        )
        speaker_swap_records = deepcopy(records)
        speaker_swap_records[-1]["source_speaker_id"] = "fixture-speaker-010"
        speaker_swap_records[-1]["canonical_record_digest"] = canonical_record_digest(
            speaker_swap_records[-1]
        )
        expanded_records = fixture_records(11, 11)
        expanded_request = replacement_request()
        expanded_request["operational_aggregate"]["eligible_call_count"] = 11
        expanded_request["operational_aggregate"]["audio_quality_bucket_counts"] = {
            "unavailable": 11,
        }
        expanded_request["operational_aggregate"]["evidence_policy_version_counts"] = {
            "emotion-state-evidence-v1": 11,
        }

        invalid_candidates = {
            "synthetic_to_crema_source_and_basis": (
                crema_records,
                replacement_request(
                    source_label="public-only",
                    unique_speaker_basis="public_dataset_actor_id",
                ),
            ),
            "nine_of_ten_speaker_swap_changes_dedup": (
                speaker_swap_records,
                replacement_request(),
            ),
            "changed_eligible_and_unique_counts": (
                expanded_records,
                expanded_request,
            ),
        }
        for name, (candidate_records, request) in invalid_candidates.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "replacement.*cohort|fixed cohort"):
                    build_cohort_release(candidate_records, request)

    def test_authoritative_history_successors_preserve_fixed_cohort_evidence(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_digest,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )
        from scripts.emotion_state_public_dataset_contracts import CREMA_DATASET_ID

        records = fixture_records(10, 10)
        root = build_cohort_release(records, fixture_request())
        root_digest = canonical_release_digest(root)
        root_history = [root]
        first_replacement = build_cohort_release(
            records,
            fixture_request(
                window_relationship="replacement",
                authoritative_release_history=root_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(root_history)
                ),
                previous_release_digest=root_digest,
                release_replaces_digest=root_digest,
                replacement_scope="entire_prior_release",
            ),
        )
        first_digest = canonical_release_digest(first_replacement)
        first_history = [root, first_replacement]
        second_replacement = build_cohort_release(
            records,
            fixture_request(
                window_relationship="replacement",
                authoritative_release_history=first_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(first_history)
                ),
                previous_release_digest=first_digest,
                release_replaces_digest=first_digest,
                replacement_scope="entire_prior_release",
            ),
        )

        def later_request(history: list[dict[str, object]]) -> dict[str, object]:
            request = fixture_request(
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
            )
            request["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-08-01",
                "window_end_date": "2026-08-14",
                "timezone": "UTC",
            }
            request["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
            return request

        source_basis_swap = deepcopy(first_replacement)
        source_basis_swap["source_label"] = "public-only"
        source_basis_swap["unique_speaker_basis"] = "public_dataset_actor_id"

        changed_dedup = deepcopy(first_replacement)
        changed_dedup["dedup_evidence_digest"] = "A" * 64

        changed_counts = deepcopy(first_replacement)
        changed_counts["input_record_count"] = 11
        changed_counts["eligible_record_count"] = 11
        changed_counts["unique_speaker_count"] = 11
        changed_counts["aggregate_metrics"]["eligible_call_count"] = 11
        for metric in (
            "eligible_call_count",
            "audio_analysis_availability_rate",
            "abstention_rate",
        ):
            changed_counts["output_cell_unique_speaker_counts"][metric] = 11
        for metric in (
            "audio_quality_bucket_counts",
            "evidence_policy_version_counts",
        ):
            cell = next(iter(changed_counts["aggregate_metrics"][metric]))
            changed_counts["aggregate_metrics"][metric][cell] = 11
            changed_counts["output_cell_unique_speaker_counts"][metric][cell] = 11

        transitive_dedup_swap = deepcopy(second_replacement)
        transitive_dedup_swap["dedup_evidence_digest"] = "B" * 64

        crema_records = fixture_records(
            10,
            10,
            dataset_manifest_id=CREMA_DATASET_ID,
        )
        crema_request = fixture_request(
            source_label="public-only",
            unique_speaker_basis="public_dataset_actor_id",
        )
        crema_root = build_cohort_release(crema_records, crema_request)
        crema_digest = canonical_release_digest(crema_root)
        crema_history = [crema_root]
        crema_replacement = build_cohort_release(
            crema_records,
            fixture_request(
                source_label="public-only",
                unique_speaker_basis="public_dataset_actor_id",
                window_relationship="replacement",
                authoritative_release_history=crema_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(crema_history)
                ),
                previous_release_digest=crema_digest,
                release_replaces_digest=crema_digest,
                replacement_scope="entire_prior_release",
            ),
        )
        public_basis_swap = deepcopy(crema_replacement)
        public_basis_swap["unique_speaker_basis"] = "public_dataset_participant_id"

        invalid_histories = {
            "synthetic_to_crema_source_and_basis": [root, source_basis_swap],
            "changed_dedup_same_counts": [root, changed_dedup],
            "changed_eligible_and_unique_counts": [root, changed_counts],
            "transitive_changed_dedup": [
                root,
                first_replacement,
                transitive_dedup_swap,
            ],
            "public_speaker_basis_swap": [crema_root, public_basis_swap],
        }
        for name, history in invalid_histories.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "replacement.*cohort|fixed cohort"):
                    build_cohort_release(records, later_request(history))

    def test_replacement_rejects_suppressed_or_null_dedup_active_head(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_digest,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        released_records = fixture_records(10, 10)
        suppressed_root = build_cohort_release(
            fixture_records(12, 4),
            fixture_request(),
        )
        null_dedup_root = build_cohort_release(
            released_records,
            fixture_request(unique_speaker_basis=None),
        )

        for name, (target, basis) in {
            "suppressed_target": (suppressed_root, "synthetic_fixture_speaker_id"),
            "null_dedup_target": (null_dedup_root, None),
        }.items():
            target_digest = canonical_release_digest(target)
            history = [target]
            request = fixture_request(
                unique_speaker_basis=basis,
                window_relationship="replacement",
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
                previous_release_digest=target_digest,
                release_replaces_digest=target_digest,
                replacement_scope="entire_prior_release",
            )
            with self.subTest(path="candidate", name=name):
                with self.assertRaisesRegex(ValueError, "released.*dedup|suppressed.*replacement"):
                    build_cohort_release(released_records, request)

            manual_successor = deepcopy(target)
            manual_successor["previous_release_digest"] = target_digest
            manual_successor["release_replaces_digest"] = target_digest
            invalid_history = [target, manual_successor]
            later = fixture_request(
                authoritative_release_history=invalid_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(invalid_history)
                ),
            )
            later["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-08-01",
                "window_end_date": "2026-08-14",
                "timezone": "UTC",
            }
            later["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
            with self.subTest(path="history", name=name):
                with self.assertRaisesRegex(ValueError, "released.*dedup|suppressed.*replacement"):
                    build_cohort_release(released_records, later)

    def test_authoritative_history_accepts_ordered_replacement_chain_and_later_release(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_digest,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        root = build_cohort_release(records, fixture_request())
        root_digest = canonical_release_digest(root)
        first_history = [root]
        first_replacement = build_cohort_release(
            records,
            fixture_request(
                window_relationship="replacement",
                authoritative_release_history=first_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(first_history)
                ),
                previous_release_digest=root_digest,
                release_replaces_digest=root_digest,
                replacement_scope="entire_prior_release",
            ),
        )
        first_replacement_digest = canonical_release_digest(first_replacement)
        second_history = [root, first_replacement]
        second_replacement = build_cohort_release(
            records,
            fixture_request(
                window_relationship="replacement",
                authoritative_release_history=second_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(second_history)
                ),
                previous_release_digest=first_replacement_digest,
                release_replaces_digest=first_replacement_digest,
                replacement_scope="entire_prior_release",
            ),
        )

        complete_history = [root, first_replacement, second_replacement]
        later_request = fixture_request(
            authoritative_release_history=complete_history,
            authoritative_release_history_digest=canonical_release_history_digest(
                complete_history
            ),
        )
        later_request["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-07-15",
            "window_end_date": "2026-07-28",
            "timezone": "UTC",
        }
        later_request["fixed_window_id"] = "utc-2026-07-15--2026-07-28"

        later_release = build_cohort_release(records, later_request)
        self.assertEqual(second_replacement["release_status"], "released")
        self.assertEqual(later_release["release_status"], "released")

    def test_authoritative_history_rejects_invalid_replacement_dependencies(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_digest,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        root = build_cohort_release(records, fixture_request())
        root_digest = canonical_release_digest(root)
        root_history = [root]
        replacement = build_cohort_release(
            records,
            fixture_request(
                window_relationship="replacement",
                authoritative_release_history=root_history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(root_history)
                ),
                previous_release_digest=root_digest,
                release_replaces_digest=root_digest,
                replacement_scope="entire_prior_release",
            ),
        )

        def later_request(history: list[dict[str, object]]) -> dict[str, object]:
            request = fixture_request(
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
            )
            request["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-08-01",
                "window_end_date": "2026-08-14",
                "timezone": "UTC",
            }
            request["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
            return request

        dangling = deepcopy(root)
        dangling["previous_release_digest"] = "A" * 64
        dangling["release_replaces_digest"] = "A" * 64

        stale_fork = deepcopy(replacement)
        stale_fork["aggregate_metrics"]["audio_analysis_availability_rate"] = 0.25

        changed_window = deepcopy(replacement)
        changed_window["aggregation_window"] = {
            "window_start_date": "2026-07-15",
            "window_end_date": "2026-07-28",
            "timezone": "UTC",
        }
        changed_window["fixed_window_id"] = "utc-2026-07-15--2026-07-28"

        invalid_histories = {
            "missing_predecessor": [replacement],
            "arbitrary_digest": [dangling],
            "successor_before_predecessor": [replacement, root],
            "stale_head_fork": [root, replacement, stale_fork],
            "changed_window_and_id": [root, changed_window],
        }
        for name, history in invalid_histories.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    build_cohort_release(records, later_request(history))

        active_history = [root, replacement]
        with self.assertRaisesRegex(ValueError, "active|head|stale"):
            build_cohort_release(
                records,
                fixture_request(
                    window_relationship="replacement",
                    authoritative_release_history=active_history,
                    authoritative_release_history_digest=(
                        canonical_release_history_digest(active_history)
                    ),
                    previous_release_digest=root_digest,
                    release_replaces_digest=root_digest,
                    replacement_scope="entire_prior_release",
                ),
            )

    def test_authoritative_history_rejects_overlapping_distinct_window_chains(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        root = build_cohort_release(records, fixture_request())
        overlap_request = fixture_request()
        overlap_request["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-07-10",
            "window_end_date": "2026-07-20",
            "timezone": "UTC",
        }
        overlap_request["fixed_window_id"] = "utc-2026-07-10--2026-07-20"
        overlapping_root = build_cohort_release(records, overlap_request)
        history = [root, overlapping_root]
        candidate_request = fixture_request(
            authoritative_release_history=history,
            authoritative_release_history_digest=canonical_release_history_digest(history),
        )
        candidate_request["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-08-01",
            "window_end_date": "2026-08-14",
            "timezone": "UTC",
        }
        candidate_request["fixed_window_id"] = "utc-2026-08-01--2026-08-14"

        with self.assertRaisesRegex(ValueError, "overlap"):
            build_cohort_release(records, candidate_request)

    def test_authoritative_history_is_required_digest_bound_and_canonical(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        omitted = fixture_request()
        omitted.pop("authoritative_release_history", None)
        omitted.pop("authoritative_release_history_digest", None)
        with self.assertRaisesRegex(ValueError, "request.*fields mismatch"):
            build_cohort_release(records, omitted)

        forged = fixture_request(authoritative_release_history_digest="A" * 64)
        with self.assertRaisesRegex(ValueError, "history digest"):
            build_cohort_release(records, forged)

        prior = build_cohort_release(records, fixture_request())
        duplicate_history = [prior, deepcopy(prior)]
        duplicate_request = fixture_request(
            authoritative_release_history=duplicate_history,
            authoritative_release_history_digest=canonical_release_history_digest(
                duplicate_history
            ),
        )
        with self.assertRaisesRegex(ValueError, "duplicate|overlap"):
            build_cohort_release(records, duplicate_request)

    def test_authoritative_history_resource_caps_are_exact_and_descriptor_bound(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES,
            MAX_AUTHORITATIVE_HISTORY_ENTRIES,
            cohort_release_fixture_descriptor,
            cohort_release_schema_descriptor,
        )

        self.assertEqual(MAX_AUTHORITATIVE_HISTORY_ENTRIES, 256)
        self.assertEqual(MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES, 4_194_304)
        schema = cohort_release_schema_descriptor()
        fixtures = cohort_release_fixture_descriptor()
        self.assertEqual(
            schema["authoritative_history_boundary"][
                "max_authoritative_history_entries"
            ],
            MAX_AUTHORITATIVE_HISTORY_ENTRIES,
        )
        self.assertEqual(
            schema["authoritative_history_boundary"][
                "max_authoritative_history_canonical_bytes"
            ],
            MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES,
        )
        self.assertEqual(
            fixtures["max_authoritative_history_entries"],
            MAX_AUTHORITATIVE_HISTORY_ENTRIES,
        )
        self.assertEqual(
            fixtures["max_authoritative_history_canonical_bytes"],
            MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES,
        )

    def test_authoritative_history_rejects_entry_count_overflow_before_chain_scan(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        root = build_cohort_release(fixture_records(10, 10), fixture_request())
        history = [deepcopy(root) for _ in range(257)]
        request = fixture_request(
            authoritative_release_history=history,
            authoritative_release_history_digest=canonical_release_history_digest(history),
        )
        request["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-08-01",
            "window_end_date": "2026-08-14",
            "timezone": "UTC",
        }
        request["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
        with self.assertRaisesRegex(
            ValueError,
            "MAX_AUTHORITATIVE_HISTORY_ENTRIES=256",
        ):
            build_cohort_release(fixture_records(10, 10), request)

    def test_authoritative_history_rejects_canonical_byte_overflow_before_entry_validation(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        history = [{"padding": "X" * 4_194_304}]
        request = fixture_request(
            authoritative_release_history=history,
            authoritative_release_history_digest=canonical_release_history_digest(history),
        )
        request["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-08-01",
            "window_end_date": "2026-08-14",
            "timezone": "UTC",
        }
        request["fixed_window_id"] = "utc-2026-08-01--2026-08-14"
        with self.assertRaisesRegex(
            ValueError,
            "MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES=4194304",
        ):
            build_cohort_release(fixture_records(10, 10), request)

    def test_new_release_compares_window_against_all_authoritative_history(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        prior = build_cohort_release(records, fixture_request())
        history = [prior]

        duplicate = fixture_request(
            authoritative_release_history=history,
            authoritative_release_history_digest=canonical_release_history_digest(history),
        )
        with self.assertRaisesRegex(ValueError, "overlap|duplicate"):
            build_cohort_release(records, duplicate)

        overlapping = deepcopy(duplicate)
        overlapping["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-07-10",
            "window_end_date": "2026-07-20",
            "timezone": "UTC",
        }
        overlapping["fixed_window_id"] = "utc-2026-07-10--2026-07-20"
        with self.assertRaisesRegex(ValueError, "overlap"):
            build_cohort_release(records, overlapping)

        nested = deepcopy(duplicate)
        nested["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-07-02",
            "window_end_date": "2026-07-05",
            "timezone": "UTC",
        }
        nested["fixed_window_id"] = "utc-2026-07-02--2026-07-05"
        with self.assertRaisesRegex(ValueError, "overlap"):
            build_cohort_release(records, nested)

        nonoverlapping = deepcopy(duplicate)
        nonoverlapping["operational_aggregate"]["aggregation_window"] = {
            "window_start_date": "2026-07-15",
            "window_end_date": "2026-07-28",
            "timezone": "UTC",
        }
        nonoverlapping["fixed_window_id"] = "utc-2026-07-15--2026-07-28"
        release = build_cohort_release(records, nonoverlapping)
        self.assertEqual(release["release_status"], "released")

    def test_released_sparse_metric_shapes_reject_rows_arrays_and_malformed_numbers(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        release = build_cohort_release(fixture_records(10, 10), fixture_request())
        invalid: dict[str, dict[str, object]] = {}

        invalid["scalar_array"] = deepcopy(release)
        invalid["scalar_array"]["aggregate_metrics"]["eligible_call_count"] = [
            {"source_speaker_id": "blocked"}
        ]

        invalid["boolean_rate"] = deepcopy(release)
        invalid["boolean_rate"]["aggregate_metrics"][
            "audio_analysis_availability_rate"
        ] = True

        invalid["identity_rows"] = deepcopy(release)
        invalid["identity_rows"]["aggregate_metrics"]["audio_quality_bucket_counts"] = {
            "identity_rows": [{"source_speaker_id": "blocked"}]
        }
        invalid["identity_rows"]["output_cell_unique_speaker_counts"][
            "audio_quality_bucket_counts"
        ] = {"identity_rows": 10}

        invalid["percentile_array"] = deepcopy(release)
        invalid["percentile_array"]["aggregate_metrics"][
            "processing_latency_percentiles"
        ]["p50"] = [0]

        invalid["policy_rows"] = deepcopy(release)
        invalid["policy_rows"]["aggregate_metrics"]["evidence_policy_version_counts"] = {
            "emotion-state-evidence-v1": {"rows": []}
        }

        invalid["nonfinite_rate"] = deepcopy(release)
        invalid["nonfinite_rate"]["aggregate_metrics"]["abstention_rate"] = float("inf")

        for name, payload in invalid.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_cohort_release(payload)

    def test_task_owned_integer_constants_reject_bool_and_float_lookalikes(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        release = build_cohort_release(fixture_records(10, 10), fixture_request())
        invalid = {
            "cap_bool": dict(release, max_contribution_per_speaker=True),
            "cap_float": dict(release, max_contribution_per_speaker=1.0),
            "minimum_bool": dict(release, minimum_unique_speakers=True),
            "minimum_float": dict(release, minimum_unique_speakers=10.0),
            "cell_minimum_bool": dict(
                release,
                minimum_unique_speakers_per_output_cell=True,
            ),
            "cell_minimum_float": dict(
                release,
                minimum_unique_speakers_per_output_cell=10.0,
            ),
        }
        for name, payload in invalid.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_cohort_release(payload)

    def test_standalone_release_rejects_source_basis_and_basis_null_contradictions(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        valid_release = build_cohort_release(
            fixture_records(10, 10),
            fixture_request(),
        )
        source_basis_contradiction = deepcopy(valid_release)
        source_basis_contradiction["source_label"] = "public-only"
        with self.assertRaisesRegex(
            ValueError,
            "synthetic fixture speaker basis.*synthetic-only",
        ):
            validate_cohort_release(source_basis_contradiction)

        basis_missing = build_cohort_release(
            fixture_records(10, 10),
            fixture_request(unique_speaker_basis=None),
        )
        basis_null_contradictions = {
            "selected_records": dict(basis_missing, eligible_record_count=1),
            "unique_speakers": dict(basis_missing, unique_speaker_count=1),
            "dedup_digest": dict(basis_missing, dedup_evidence_digest="A" * 64),
        }
        for name, payload in basis_null_contradictions.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "basis-null evidence"):
                    validate_cohort_release(payload)

    def test_standalone_suppressed_release_rejects_impossible_record_counts(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        suppressed = build_cohort_release(fixture_records(12, 4), fixture_request())
        dedup_null_with_selected = deepcopy(suppressed)
        dedup_null_with_selected["dedup_evidence_digest"] = None
        dedup_null_with_selected["suppression_reason_codes"] = [
            "minimum_unique_speakers_not_met",
            "deterministic_contribution_evidence_missing",
        ]
        unique_exceeds_input = deepcopy(suppressed)
        unique_exceeds_input.update({
            "input_record_count": 3,
            "eligible_record_count": 0,
            "unique_speaker_count": 4,
            "dedup_evidence_digest": None,
            "suppression_reason_codes": [
                "minimum_unique_speakers_not_met",
                "deterministic_contribution_evidence_missing",
            ],
        })
        invalid = {
            "eligible_exceeds_unique": dict(
                suppressed,
                eligible_record_count=5,
            ),
            "unique_exceeds_input": unique_exceeds_input,
            "nonnull_dedup_requires_equal_counts": dict(
                suppressed,
                eligible_record_count=3,
            ),
            "null_dedup_requires_zero_eligible": dedup_null_with_selected,
        }
        for name, payload in invalid.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ValueError,
                    "record counts|eligible.*unique|dedup",
                ):
                    validate_cohort_release(payload)

    def test_authoritative_history_rejects_impossible_suppressed_record_counts(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        suppressed = build_cohort_release(fixture_records(12, 4), fixture_request())
        invalid_entries = {
            "eligible_exceeds_unique": dict(
                suppressed,
                eligible_record_count=5,
            ),
            "nonnull_dedup_requires_equal_counts": dict(
                suppressed,
                eligible_record_count=3,
            ),
        }
        null_dedup_with_selected = deepcopy(suppressed)
        null_dedup_with_selected["dedup_evidence_digest"] = None
        null_dedup_with_selected["suppression_reason_codes"] = [
            "minimum_unique_speakers_not_met",
            "deterministic_contribution_evidence_missing",
        ]
        invalid_entries["null_dedup_requires_zero_eligible"] = null_dedup_with_selected

        for name, invalid_entry in invalid_entries.items():
            history = [invalid_entry]
            request = fixture_request(
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
            )
            request["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-07-15",
                "window_end_date": "2026-07-28",
                "timezone": "UTC",
            }
            request["fixed_window_id"] = "utc-2026-07-15--2026-07-28"
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ValueError,
                    "record counts|eligible.*unique|dedup",
                ):
                    build_cohort_release(records, request)

    def test_authoritative_history_rejects_invalid_source_basis_and_basis_null_entries(
        self,
    ) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            canonical_release_history_digest,
            fixture_records,
            fixture_request,
        )

        valid_release = build_cohort_release(
            fixture_records(10, 10),
            fixture_request(),
        )
        source_basis_contradiction = deepcopy(valid_release)
        source_basis_contradiction["source_label"] = "public-only"

        basis_null_contradiction = build_cohort_release(
            fixture_records(10, 10),
            fixture_request(unique_speaker_basis=None),
        )
        basis_null_contradiction["eligible_record_count"] = 1

        invalid_history_entries = {
            "source_basis": (
                source_basis_contradiction,
                "synthetic fixture speaker basis.*synthetic-only",
            ),
            "basis_null": (basis_null_contradiction, "basis-null evidence"),
        }
        for name, (invalid_entry, error_pattern) in invalid_history_entries.items():
            history = [invalid_entry]
            request = fixture_request(
                authoritative_release_history=history,
                authoritative_release_history_digest=(
                    canonical_release_history_digest(history)
                ),
            )
            request["operational_aggregate"]["aggregation_window"] = {
                "window_start_date": "2026-07-15",
                "window_end_date": "2026-07-28",
                "timezone": "UTC",
            }
            request["fixed_window_id"] = "utc-2026-07-15--2026-07-28"
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, error_pattern):
                    build_cohort_release(fixture_records(10, 10), request)

    def test_suppression_reason_codes_are_frozen_and_semantically_consistent(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        suppressed = build_cohort_release(fixture_records(12, 4), fixture_request())
        unknown = dict(suppressed, suppression_reason_codes=["invented_reason"])
        minimum_contradiction = dict(
            suppressed,
            suppression_reason_codes=["cross_corpus_identity_not_proven"],
        )
        basis_missing = build_cohort_release(
            fixture_records(10, 10),
            fixture_request(unique_speaker_basis=None),
        )
        basis_contradiction = dict(
            basis_missing,
            suppression_reason_codes=["minimum_unique_speakers_not_met"],
        )
        dedup_contradiction = dict(
            suppressed,
            suppression_reason_codes=[
                "minimum_unique_speakers_not_met",
                "deterministic_contribution_evidence_missing",
            ],
        )
        for name, payload in {
            "unknown": unknown,
            "minimum": minimum_contradiction,
            "basis": basis_contradiction,
            "dedup": dedup_contradiction,
        }.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_cohort_release(payload)

    def test_unhashable_request_and_membership_values_raise_value_error(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            evaluate_discovery_gate,
            fixture_records,
            fixture_request,
        )

        malformed_requests = {
            "source_label_list": fixture_request(source_label=[]),
            "source_label_object": fixture_request(source_label={}),
            "basis_list": fixture_request(unique_speaker_basis=[]),
            "basis_object": fixture_request(unique_speaker_basis={}),
            "relationship_list": fixture_request(window_relationship=[]),
            "relationship_object": fixture_request(window_relationship={}),
        }
        for name, request in malformed_requests.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    build_cohort_release(fixture_records(10, 10), request)

        for malformed in ([], {}, {"eligible_call_count": [["__scalar__"]]}):
            records = fixture_records(10, 10)
            records[0]["metric_cell_memberships"] = malformed
            with self.subTest(membership_type=type(malformed).__name__):
                with self.assertRaisesRegex(ValueError, "metric_cell_memberships"):
                    build_cohort_release(records, fixture_request())

        for malformed_dataset_id in ([], {}):
            records = fixture_records(10, 10)
            records[0]["dataset_manifest_id"] = malformed_dataset_id
            for path in ("release", "discovery"):
                with self.subTest(
                    dataset_id_type=type(malformed_dataset_id).__name__,
                    path=path,
                ):
                    with self.assertRaisesRegex(ValueError, "dataset_manifest_id"):
                        if path == "release":
                            build_cohort_release(records, fixture_request())
                        else:
                            evaluate_discovery_gate(records)

    def test_runtime_operational_aggregate_contract_is_unchanged(self) -> None:
        from runtime.contracts.emotion_state_contracts import (
            OPERATIONAL_AGGREGATE_FIELDS,
            EmotionStateContractError,
            contract_self_check,
            validate_operational_aggregate,
        )
        from scripts.emotion_state_cohort_release_contracts import fixture_request

        self.assertEqual(OPERATIONAL_AGGREGATE_FIELDS, frozenset({
            "aggregation_window",
            "eligible_call_count",
            "audio_analysis_availability_rate",
            "audio_quality_bucket_counts",
            "abstention_rate",
            "processing_latency_percentiles",
            "evidence_policy_version_counts",
            "contains_call_level_rows",
            "contains_raw_audio",
            "contains_raw_transcript",
            "contains_signal_labels",
        }))
        aggregate = fixture_request()["operational_aggregate"]
        validate_operational_aggregate(aggregate)
        with self.assertRaises(EmotionStateContractError):
            validate_operational_aggregate(dict(aggregate, unique_speaker_count=10))
        self.assertEqual(contract_self_check(), "pass")

    def test_output_contains_no_speaker_token_or_per_speaker_row_and_boundaries_are_false(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            BOOLEAN_BOUNDARY_FIELDS,
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        release = build_cohort_release(records, fixture_request())
        serialized = json.dumps(release, sort_keys=True)
        for record in records:
            self.assertNotIn(record["source_speaker_id"], serialized)
        self.assertNotIn("speaker_keys", release)
        self.assertNotIn("per_speaker_rows", release)
        self.assertEqual(len(BOOLEAN_BOUNDARY_FIELDS), 8)
        for field in BOOLEAN_BOUNDARY_FIELDS:
            self.assertIs(release[field], False, field)

    def test_confirmatory_floor_requires_thirty_by_class_for_every_promoted_label(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import validate_confirmatory_floor

        passing = {
            "overall_unique_speaker_count": 30,
            "promoted_labels": ["frustration", "confusion"],
            "per_promoted_label": {
                "frustration": {
                    "consensus_positive_turn_count": 30,
                    "consensus_negative_turn_count": 30,
                },
                "confusion": {
                    "consensus_positive_turn_count": 30,
                    "consensus_negative_turn_count": 30,
                },
            },
            "power_precision_requirement_passed": True,
        }
        underpowered = json.loads(json.dumps(passing))
        underpowered["per_promoted_label"]["confusion"][
            "consensus_positive_turn_count"
        ] = 29
        with self.assertRaisesRegex(ValueError, "consensus-positive"):
            validate_confirmatory_floor(underpowered)
        validate_confirmatory_floor(passing)

        malformed = {
            "empty_labels": dict(passing, promoted_labels=[]),
            "duplicate_labels": dict(
                passing,
                promoted_labels=["frustration", "frustration"],
            ),
            "label_key_mismatch": dict(passing, promoted_labels=["frustration"]),
            "too_few_speakers": dict(passing, overall_unique_speaker_count=29),
            "boolean_speaker_count": dict(passing, overall_unique_speaker_count=True),
            "power_not_passed": dict(passing, power_precision_requirement_passed=False),
        }
        for name, evidence in malformed.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_confirmatory_floor(evidence)

    def test_phase_a_public_dataset_gate_rejects_operational_pattern_candidates(self) -> None:
        from runtime.contracts.emotion_pattern_contracts import validate_pattern_candidate
        from scripts.emotion_state_cohort_release_contracts import (
            validate_phase_a_pattern_candidate,
        )
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
        )

        candidate = self._pattern_candidate()
        for dataset_id in (CREMA_DATASET_ID, AMI_DATASET_ID):
            public_candidate = dict(candidate, discovery_dataset_version=dataset_id)
            self.assertIs(validate_pattern_candidate(public_candidate), public_candidate)
            with self.subTest(dataset_id=dataset_id):
                with self.assertRaisesRegex(ValueError, "public dataset.*PatternCandidateV1"):
                    validate_phase_a_pattern_candidate(public_candidate)
        self.assertIs(validate_phase_a_pattern_candidate(candidate), candidate)

    def test_release_validator_is_strict_and_wraps_operational_aggregate(self) -> None:
        from runtime.contracts.emotion_state_contracts import EmotionStateContractError
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
            validate_cohort_release,
        )

        records = fixture_records(10, 10)
        request = fixture_request()
        release = build_cohort_release(records, request)
        self.assertIs(validate_cohort_release(release), release)
        noncanonical_window = deepcopy(release)
        noncanonical_window["aggregation_window"]["window_start_date"] = "20260701"
        noncanonical_window["fixed_window_id"] = "utc-20260701--2026-07-14"
        reversed_window = deepcopy(release)
        reversed_window["aggregation_window"] = {
            "window_start_date": "2026-07-15",
            "window_end_date": "2026-07-14",
            "timezone": "UTC",
        }
        reversed_window["fixed_window_id"] = "utc-2026-07-15--2026-07-14"
        invalid_releases = {
            "extra_field": dict(release, speaker_keys=[]),
            "boundary_true": dict(release, speaker_tokens_persisted=True),
            "wrong_minimum": dict(release, minimum_unique_speakers=9),
            "wrong_cell_minimum": dict(
                release,
                minimum_unique_speakers_per_output_cell=9,
            ),
            "wrong_cap": dict(release, max_contribution_per_speaker=2),
            "wrong_status": dict(release, release_status="anonymous"),
            "noncanonical_window": noncanonical_window,
            "reversed_window": reversed_window,
        }
        for name, invalid in invalid_releases.items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_cohort_release(invalid)
        bad_request = fixture_request()
        bad_request["operational_aggregate"]["eligible_call_count"] = 9
        with self.assertRaises(EmotionStateContractError):
            build_cohort_release(records, bad_request)

    def test_tracked_schema_and_named_scenario_parameters_match_contract(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            BOOLEAN_BOUNDARY_FIELDS,
            COHORT_RELEASE_FIELDS,
            METRIC_ALLOWLIST_V1,
        )

        schema = json.loads(
            (
                ROOT
                / "research/sources/emotion_state/cohort_release_evidence_v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(schema["schema_id"], "emotion-state-cohort-release-evidence-v1")
        self.assertEqual(set(schema["required_fields"]), COHORT_RELEASE_FIELDS)
        self.assertEqual(schema["false_constants"], {
            field: False for field in BOOLEAN_BOUNDARY_FIELDS
        })
        self.assertEqual(schema["metric_allowlist"], list(METRIC_ALLOWLIST_V1))
        self.assertEqual(schema["minimum_unique_speakers"], 10)
        self.assertEqual(schema["minimum_unique_speakers_per_output_cell"], 10)
        fixtures = json.loads(
            (
                ROOT
                / "research/experiments/cases/emotion-state-001-cohort-release-fixtures.json"
            ).read_text(encoding="utf-8")
        )
        expected_scenarios = {
            "twelve_calls_four_speakers",
            "ten_calls_ten_speakers",
            "twenty_turns_five_speakers",
            "duplicate_public_actor_ids",
            "cross_corpus_same_bare_id",
            "missing_speaker_basis",
            "call_id_as_speaker",
            "forbidden_identity_basis",
            "over_contribution",
            "sparse_output_cell",
            "overlapping_release",
            "valid_replacement",
        }
        self.assertEqual(set(fixtures["scenarios"]), expected_scenarios)
        for scenario in fixtures["scenarios"].values():
            self.assertIsInstance(scenario, dict)
            self.assertNotIn("records", scenario)
            self.assertNotIn("speaker_ids", scenario)
        tracked_text = json.dumps({"schema": schema, "fixtures": fixtures}).lower()
        self.assertIn("suppression-based, privacy-minimized contribution gate", tracked_text)
        for prohibited_claim in ("anonymous", "differential privacy", "proof against re-identification"):
            self.assertNotIn(prohibited_claim, tracked_text)

    def test_complete_schema_and_fixture_descriptor_parity_is_type_exact(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            cohort_release_fixture_descriptor,
            cohort_release_schema_descriptor,
        )

        def canonical(value: object) -> str:
            return json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )

        schema = json.loads(
            (
                ROOT
                / "research/sources/emotion_state/cohort_release_evidence_v1.schema.json"
            ).read_text(encoding="utf-8")
        )
        fixtures = json.loads(
            (
                ROOT
                / "research/experiments/cases/emotion-state-001-cohort-release-fixtures.json"
            ).read_text(encoding="utf-8")
        )
        expected_schema = cohort_release_schema_descriptor()
        expected_fixtures = cohort_release_fixture_descriptor()
        self.assertEqual(canonical(schema), canonical(expected_schema))
        self.assertEqual(canonical(fixtures), canonical(expected_fixtures))
        self.assertEqual(expected_schema["contract_name"], "CohortReleaseEvidenceV1")
        self.assertEqual(expected_schema["allowed_source_labels"], [
            "public-only",
            "synthetic-only",
        ])
        self.assertEqual(expected_schema["release_statuses"], [
            "released",
            "suppressed",
        ])
        self.assertIs(
            expected_fixtures["scenarios"]["twenty_turns_five_speakers"][
                "discovery_floor_met"
            ],
            True,
        )
        type_mutation = deepcopy(expected_fixtures)
        type_mutation["scenarios"]["twenty_turns_five_speakers"][
            "discovery_floor_met"
        ] = 1
        self.assertNotEqual(canonical(type_mutation), canonical(expected_fixtures))

    def test_cohort_release_contract_self_check_passes(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            cohort_release_contract_self_check,
        )

        self.assertEqual(cohort_release_contract_self_check(), "pass")

    def test_phase_a_builder_registers_cohort_release_self_check(self) -> None:
        from scripts.emotion_state_phase_a_contracts import build_phase_a_payload

        payload = build_phase_a_payload(
            ROOT / "research/experiments/cases/emotion-state-001-phase-a-contracts.json",
            root=ROOT,
        )
        self.assertEqual(
            payload["summary"]["contract_checks"][
                "emotion_state_cohort_release_contracts"
            ],
            "pass",
        )


class VerificationEvidenceLockPhaseTests(unittest.TestCase):
    POLICY_PATH = (
        ROOT
        / "research/sources/emotion_state/phase_a_verification_guard_policy.json"
    )

    def _phase_fixture(
        self,
        root: Path,
        baseline_commit: str,
        head_commit: str,
    ) -> tuple[bytes, dict[str, object], list[dict[str, object]]]:
        policy_path = (
            root
            / "research/sources/emotion_state/"
            "phase_a_verification_guard_policy.json"
        )
        policy_path.parent.mkdir(parents=True)
        policy_bytes = self.POLICY_PATH.read_bytes()
        policy_path.write_bytes(policy_bytes)
        policy = json.loads(policy_bytes.decode("utf-8"))
        ledger: list[dict[str, object]] = []
        for command in policy["allowed_commands"]:
            if command["command_id"] == "phase-a-materials-validator":
                continue
            ledger.append({
                "sequence_number": len(ledger) + 1,
                "command_id": command["command_id"],
                "argv": [
                    argument.format(
                        mode="material-pending",
                        baseline_commit=baseline_commit,
                        head_commit=head_commit,
                    )
                    for argument in command["argv_template"]
                ],
                "working_directory": ".",
                "exit_status": 0,
            })
        closure_inventory = [{
            "path": "scripts/fixture.py",
            "git_mode": "100644",
            "sha256": "A" * 64,
        }]
        closure_edges: list[dict[str, str]] = []
        closure_digest = hashlib.sha256(
            (
                json.dumps(
                    {
                        "edges": closure_edges,
                        "inventory": closure_inventory,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
        ).hexdigest().upper()
        snapshot: dict[str, object] = {
            "committed_change_inventory": [{
                "path": "scripts/fixture.py",
                "git_mode": "100644",
                "sha256": "A" * 64,
            }],
            "uncommitted_change_inventory": [{
                "path": "research/fixture.json",
                "git_state": "untracked",
                "git_mode": "100644",
                "sha256": "B" * 64,
            }],
            "executable_dependency_closure": {
                "inventory": closure_inventory,
                "edges": closure_edges,
                "digest": closure_digest,
            },
            "dataset_manifest_digests": {},
            "dataset_hash_inventory_digests": {},
        }
        return policy_bytes, snapshot, ledger

    def test_wrapper_and_caller_locked_phases_are_canonical_byte_identical(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-phase-parity-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                wrapped = verification.build_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                with verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    explicit = verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=capability,
                    )

            self.assertEqual(
                verification.canonical_json_bytes(wrapped),
                verification.canonical_json_bytes(explicit),
            )
            self.assertEqual(set(explicit), {
                "implementation_baseline_commit",
                "repository_head_commit",
                "committed_change_inventory",
                "uncommitted_change_inventory",
                "executable_dependency_closure_inventory",
                "executable_dependency_closure_edges",
                "dataset_manifest_digests",
                "dataset_hash_inventory_digests",
                "executed_command_ledger",
                "guard_policy_digest",
                "verification_input_path_inventory_digest",
                "executable_dependency_closure_digest",
                "executed_command_ledger_digest",
                "verification_input_tree_digest",
                "verification_run_id",
                "guarded_command_results",
                "repository_gate_statuses",
                "provider_environment_scrubbed",
                "private_path_guard_enabled",
                "network_guard_enabled",
            })
            for field in (
                "guard_policy_digest",
                "verification_input_path_inventory_digest",
                "executable_dependency_closure_digest",
                "executed_command_ledger_digest",
                "verification_input_tree_digest",
                "verification_run_id",
            ):
                self.assertEqual(explicit[field], wrapped[field])

    def test_prepared_state_is_opaque_module_origin_and_noncopyable(self) -> None:
        import copy

        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-prepared-state-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )

            self.assertEqual(
                repr(prepared),
                "<PreparedVerificationEvidence opaque>",
            )
            for field_name in (
                "baseline_commit",
                "head_commit",
                "mode",
                "initial_policy_bytes",
                "initial_snapshot_bytes",
                "executed_command_ledger_bytes",
                "root",
            ):
                self.assertFalse(hasattr(prepared, field_name), field_name)
            with self.assertRaisesRegex(TypeError, "cannot be copied"):
                copy.copy(prepared)
            with self.assertRaisesRegex(TypeError, "cannot be copied"):
                copy.deepcopy(prepared)
            with self.assertRaisesRegex(TypeError, "opaque"):
                verification.PreparedVerificationEvidence(
                    baseline_commit=baseline_commit,
                    head_commit=head_commit,
                    mode="material-pending",
                    initial_policy_bytes=self.POLICY_PATH.read_bytes(),
                    initial_snapshot_bytes=verification.canonical_json_bytes(
                        snapshot
                    ),
                    executed_command_ledger_bytes=(
                        verification.canonical_json_bytes(ledger)
                    ),
                )
            forged = object.__new__(
                verification.PreparedVerificationEvidence
            )
            with self.assertRaisesRegex(ValueError, "module-origin"):
                with verification.exclusive_verification_lock(
                    forged,
                    root=root,
                    recovery_dir=(
                        root / ".tmp/emotion-state-001-phase-a-publication"
                    ),
                ):
                    self.fail("forged prepared state acquired a lock")

            class EqualPrepared(
                verification.PreparedVerificationEvidence
            ):
                __slots__ = ()

                def __hash__(self) -> int:
                    return hash(prepared)

                def __eq__(self, other: object) -> bool:
                    return other is prepared

            equal_forged = object.__new__(EqualPrepared)
            with self.assertRaisesRegex(ValueError, "module-origin"):
                with verification.exclusive_verification_lock(
                    equal_forged,
                    root=root,
                    recovery_dir=(
                        root / ".tmp/emotion-state-001-phase-a-publication"
                    ),
                ):
                    self.fail(
                        "equality-forged prepared state acquired a lock"
                    )

    def test_finalize_rejects_capability_misuse_without_consuming_state(
        self,
    ) -> None:
        import copy

        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-capability-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                other_prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                forgery_prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "active verification lock capability",
                ):
                    verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=None,
                    )
                with self.assertRaisesRegex(TypeError, "opaque"):
                    verification.VerificationLockCapability()
                forged_capability = object.__new__(
                    verification.VerificationLockCapability
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "active verification lock capability",
                ):
                    verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=forged_capability,
                    )
                with self.assertRaisesRegex(
                    ValueError,
                    "verification recovery directory",
                ):
                    with verification.exclusive_verification_lock(
                        prepared,
                        root=root,
                        recovery_dir=root / ".tmp/wrong-recovery-directory",
                    ):
                        self.fail(
                            "capability acquired through the wrong lock path"
                        )

                with verification.exclusive_verification_lock(
                    forgery_prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    class EqualCapability(
                        verification.VerificationLockCapability
                    ):
                        __slots__ = ()

                        def __hash__(self) -> int:
                            return hash(capability)

                        def __eq__(self, other: object) -> bool:
                            return other is capability

                    equal_forged_capability = object.__new__(
                        EqualCapability
                    )
                    with self.assertRaisesRegex(
                        ValueError,
                        "active verification lock capability",
                    ):
                        verification.finalize_verification_evidence(
                            forgery_prepared,
                            root=root,
                            capability=equal_forged_capability,
                        )

                expired_capability: object
                with verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    expired_capability = capability
                    with self.assertRaisesRegex(TypeError, "cannot be copied"):
                        copy.copy(capability)
                with self.assertRaisesRegex(ValueError, "expired"):
                    verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=expired_capability,
                    )

                with verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    with self.assertRaisesRegex(
                        ValueError,
                        "different prepared",
                    ):
                        verification.finalize_verification_evidence(
                            other_prepared,
                            root=root,
                            capability=capability,
                        )
                    verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=capability,
                    )

    def test_prepared_state_is_root_bound_and_one_shot(self) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-root-one-",
        ) as first_directory, tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-root-two-",
        ) as second_directory:
            first_root = Path(first_directory)
            second_root = Path(second_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                first_root,
                baseline_commit,
                head_commit,
            )
            self._phase_fixture(
                second_root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    first_root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    first_root / ".tmp/emotion-state-001-phase-a-publication"
                )
                with verification.exclusive_verification_lock(
                    prepared,
                    root=first_root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    with self.assertRaisesRegex(
                        ValueError,
                        "prepared verification root",
                    ):
                        verification.finalize_verification_evidence(
                            prepared,
                            root=second_root,
                            capability=capability,
                        )
                    first_result = verification.finalize_verification_evidence(
                        prepared,
                        root=first_root,
                        capability=capability,
                    )
                    self.assertEqual(
                        first_result["repository_head_commit"],
                        head_commit,
                    )
                    with self.assertRaisesRegex(ValueError, "already consumed"):
                        verification.finalize_verification_evidence(
                            prepared,
                            root=first_root,
                            capability=capability,
                        )

    def test_prepared_state_rejects_replaced_directory_at_same_path(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-root-replacement-",
        ) as temporary_directory:
            parent = Path(temporary_directory)
            root = parent / "verification-root"
            root.mkdir()
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                root.rename(parent / "original-verification-root")
                root.mkdir()
                self._phase_fixture(
                    root,
                    baseline_commit,
                    head_commit,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "prepared verification root identity",
                ):
                    with verification.exclusive_verification_lock(
                        prepared,
                        root=root,
                        recovery_dir=(
                            root
                            / ".tmp/emotion-state-001-phase-a-publication"
                        ),
                    ):
                        self.fail(
                            "replacement root acquired a prepared capability"
                        )

    def test_registered_verification_state_is_pathless(self) -> None:
        from dataclasses import fields, is_dataclass

        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-pathless-state-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )

            def assert_pathless(value: object) -> None:
                self.assertNotIsInstance(value, Path)
                if isinstance(value, str):
                    self.assertNotIn(str(root), value)
                    return
                if is_dataclass(value) and not isinstance(value, type):
                    for field in fields(value):
                        assert_pathless(getattr(value, field.name))
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        assert_pathless(item)
                elif isinstance(value, dict):
                    for key, item in value.items():
                        assert_pathless(key)
                        assert_pathless(item)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                prepared_state = (
                    verification._lookup_prepared_verification_state(
                        prepared
                    )
                )
                self.assertIsNotNone(prepared_state)
                assert_pathless(prepared_state)
                self.assertRegex(
                    prepared_state.root.binding_digest,
                    r"^[0-9A-F]{64}$",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                with verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    capability_state = (
                        verification
                        ._lookup_verification_lock_capability_state(
                            capability
                        )
                    )
                    self.assertIsNotNone(capability_state)
                    assert_pathless(capability_state)
                    self.assertIsInstance(
                        capability_state.lease.handle.name,
                        int,
                    )
                    verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=capability,
                    )

    def test_prepare_requires_a_usable_stable_root_identity(self) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-stable-root-identity-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            root_key = os.path.normcase(os.path.abspath(root))
            real_stat = verification.os.stat

            def zero_inode_stat(
                path: object,
                *args: object,
                **kwargs: object,
            ) -> os.stat_result:
                status = real_stat(path, *args, **kwargs)
                try:
                    candidate_key = os.path.normcase(
                        os.path.abspath(os.fsdecode(path))
                    )
                except TypeError:
                    return status
                if candidate_key != root_key:
                    return status
                values = list(status)
                values[1] = 0
                return os.stat_result(values)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ), mock.patch.object(
                verification.os,
                "stat",
                side_effect=zero_inode_stat,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "stable filesystem identity is unavailable",
                ):
                    verification.prepare_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )

    def test_hybrid_exclusive_lock_reuses_released_persistent_sentinel(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-hybrid-lock-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            recovery_dir = (
                root / ".tmp/emotion-state-001-phase-a-publication"
            )
            lock_path = recovery_dir / "publication.lock"
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                seed = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                with verification.persistent_verification_lock(
                    seed,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as seed_capability:
                    verification.finalize_verification_evidence(
                        seed,
                        root=root,
                        capability=seed_capability,
                    )
                self.assertEqual(lock_path.read_bytes(), b"\0")

                wrapped = verification.build_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                self.assertEqual(
                    wrapped["repository_head_commit"],
                    head_commit,
                )
                self.assertEqual(lock_path.read_bytes(), b"\0")

                active = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                blocked = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                with verification.persistent_verification_lock(
                    active,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as active_capability:
                    with self.assertRaisesRegex(
                        ValueError,
                        "verification lock is already held",
                    ):
                        with verification.exclusive_verification_lock(
                            blocked,
                            root=root,
                            recovery_dir=recovery_dir,
                        ):
                            self.fail(
                                "exclusive lock overlapped persistent lock"
                            )
                    verification.finalize_verification_evidence(
                        active,
                        root=root,
                        capability=active_capability,
                    )

    def test_persistent_verification_lock_has_real_contention_and_expires(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-persistent-lock-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                first = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                second = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                legacy = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                blocked_by_legacy = (
                    verification.prepare_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )
                )
                sentinel_prepared = (
                    verification.prepare_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )
                )
                corrupt_prepared = (
                    verification.prepare_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                lock_path = recovery_dir / "publication.lock"
                with verification.exclusive_verification_lock(
                    legacy,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as legacy_capability:
                    with self.assertRaisesRegex(
                        ValueError,
                        "persistent verification lock is already held",
                    ):
                        with verification.persistent_verification_lock(
                            blocked_by_legacy,
                            root=root,
                            recovery_dir=recovery_dir,
                        ):
                            self.fail(
                                "persistent lock overlapped the legacy lock"
                            )
                    verification.finalize_verification_evidence(
                        legacy,
                        root=root,
                        capability=legacy_capability,
                    )

                with mock.patch.object(
                    verification,
                    "_acquire_persistent_verification_os_lock",
                ), mock.patch.object(
                    verification,
                    "_release_persistent_verification_os_lock",
                ):
                    with verification.persistent_verification_lock(
                        sentinel_prepared,
                        root=root,
                        recovery_dir=recovery_dir,
                    ) as sentinel_capability:
                        self.assertEqual(lock_path.read_bytes(), b"\0")
                        verification.finalize_verification_evidence(
                            sentinel_prepared,
                            root=root,
                            capability=sentinel_capability,
                        )
                self.assertEqual(lock_path.read_bytes(), b"\0")
                lock_path.write_bytes(b"X")
                with self.assertRaisesRegex(
                    ValueError,
                    "persistent verification lock contents are invalid",
                ):
                    with verification.persistent_verification_lock(
                        corrupt_prepared,
                        root=root,
                        recovery_dir=recovery_dir,
                    ):
                        self.fail("corrupt persistent lock was accepted")
                lock_path.write_bytes(b"\0")

                expired: object
                with verification.persistent_verification_lock(
                    first,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    expired = capability
                    with self.assertRaisesRegex(
                        ValueError,
                        "persistent verification lock is already held",
                    ):
                        with verification.persistent_verification_lock(
                            second,
                            root=root,
                            recovery_dir=recovery_dir,
                        ):
                            self.fail("second persistent lock was acquired")
                    verification.finalize_verification_evidence(
                        first,
                        root=root,
                        capability=capability,
                    )
                self.assertEqual(lock_path.read_bytes(), b"\0")
                with self.assertRaisesRegex(ValueError, "expired"):
                    verification.finalize_verification_evidence(
                        second,
                        root=root,
                        capability=expired,
                    )
                with verification.persistent_verification_lock(
                    second,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as reused_capability:
                    verification.finalize_verification_evidence(
                        second,
                        root=root,
                        capability=reused_capability,
                    )

    def test_verification_lock_rejects_recovery_and_lock_links(self) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-link-paths-",
        ) as temporary_directory:
            parent = Path(temporary_directory)
            recovery_root = parent / "recovery-root"
            recovery_root.mkdir()
            lock_root = parent / "lock-root"
            lock_root.mkdir()
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                recovery_root,
                baseline_commit,
                head_commit,
            )
            self._phase_fixture(
                lock_root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                recovery_prepared = (
                    verification.prepare_verification_evidence(
                        recovery_root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )
                )
                lock_prepared = verification.prepare_verification_evidence(
                    lock_root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )

                external_directory = parent / "external-recovery"
                external_directory.mkdir()
                recovery_link_created = True
                try:
                    (recovery_root / ".tmp").symlink_to(
                        external_directory,
                        target_is_directory=True,
                    )
                except OSError:
                    recovery_link_created = False
                    (recovery_root / ".tmp").mkdir()
                real_link_check = verification._path_is_link_or_reparse

                def recovery_link_check(path: Path) -> bool:
                    if (
                        not recovery_link_created
                        and os.path.normcase(os.path.abspath(path))
                        == os.path.normcase(
                            os.path.abspath(recovery_root / ".tmp")
                        )
                    ):
                        return True
                    return real_link_check(path)

                with mock.patch.object(
                    verification,
                    "_path_is_link_or_reparse",
                    side_effect=recovery_link_check,
                ), self.assertRaisesRegex(
                    ValueError,
                    "link or reparse",
                ):
                    with verification.exclusive_verification_lock(
                        recovery_prepared,
                        root=recovery_root,
                        recovery_dir=(
                            recovery_root
                            / ".tmp/emotion-state-001-phase-a-publication"
                        ),
                    ):
                        self.fail("linked recovery path acquired a lock")

                lock_recovery = (
                    lock_root
                    / ".tmp/emotion-state-001-phase-a-publication"
                )
                lock_recovery.mkdir(parents=True)
                external_lock = parent / "external-publication.lock"
                external_lock.write_bytes(b"\0")
                lock_path = lock_recovery / "publication.lock"
                lock_link_created = True
                try:
                    lock_path.symlink_to(external_lock)
                except OSError:
                    lock_link_created = False
                    lock_path.write_bytes(b"\0")

                def lock_link_check(path: Path) -> bool:
                    if (
                        not lock_link_created
                        and os.path.normcase(os.path.abspath(path))
                        == os.path.normcase(os.path.abspath(lock_path))
                    ):
                        return True
                    return real_link_check(path)

                with mock.patch.object(
                    verification,
                    "_path_is_link_or_reparse",
                    side_effect=lock_link_check,
                ), self.assertRaisesRegex(
                    ValueError,
                    "link or reparse",
                ):
                    with verification.exclusive_verification_lock(
                        lock_prepared,
                        root=lock_root,
                        recovery_dir=lock_recovery,
                    ):
                        self.fail("linked lock path acquired a lock")

    def test_verification_lock_rejects_handle_path_identity_mismatch(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-lock-handle-mismatch-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            real_fstat = verification.os.fstat
            fstat_calls = 0

            def mismatched_fstat(descriptor: int) -> os.stat_result:
                nonlocal fstat_calls
                fstat_calls += 1
                status = real_fstat(descriptor)
                if fstat_calls == 1:
                    return status
                values = list(status)
                values[1] = max(1, int(status.st_ino) + 1)
                return os.stat_result(values)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                with mock.patch.object(
                    verification.os,
                    "fstat",
                    side_effect=mismatched_fstat,
                ), self.assertRaisesRegex(
                    ValueError,
                    "lock handle/path identity mismatch",
                ):
                    with verification.exclusive_verification_lock(
                        prepared,
                        root=root,
                        recovery_dir=recovery_dir,
                    ):
                        self.fail("mismatched lock handle acquired a lease")
                self.assertFalse(
                    (recovery_dir / "publication.lock").exists()
                )
                fdopen_failure = (
                    verification.prepare_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )
                )
                with mock.patch.object(
                    verification.os,
                    "fdopen",
                    side_effect=OSError("synthetic fdopen failure"),
                ), self.assertRaisesRegex(
                    ValueError,
                    "unable to open verification publication lock",
                ):
                    with verification.exclusive_verification_lock(
                        fdopen_failure,
                        root=root,
                        recovery_dir=recovery_dir,
                    ):
                        self.fail("fdopen failure acquired a lease")
                self.assertFalse(
                    (recovery_dir / "publication.lock").exists()
                )

    def test_finalize_revalidates_the_active_lock_lease(self) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-finalize-lease-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            real_fstat = verification.os.fstat

            def mismatched_fstat(descriptor: int) -> os.stat_result:
                status = real_fstat(descriptor)
                values = list(status)
                values[1] = max(1, int(status.st_ino) + 1)
                return os.stat_result(values)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                context = verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                )
                capability = context.__enter__()
                try:
                    with mock.patch.object(
                        verification.os,
                        "fstat",
                        side_effect=mismatched_fstat,
                    ), self.assertRaisesRegex(
                        ValueError,
                        "lock handle/path identity mismatch",
                    ):
                        verification.finalize_verification_evidence(
                            prepared,
                            root=root,
                            capability=capability,
                        )
                    result = verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=capability,
                    )
                    self.assertEqual(
                        result["repository_head_commit"],
                        head_commit,
                    )
                finally:
                    context.__exit__(None, None, None)

    def test_active_lease_rejects_root_replacement_after_finalize(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-staging-lease-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            root_key = os.path.normcase(os.path.abspath(root))
            real_stat = verification.os.stat
            replaced = False

            def replacement_stat(
                path: object,
                *args: object,
                **kwargs: object,
            ) -> os.stat_result:
                status = real_stat(path, *args, **kwargs)
                try:
                    candidate_key = os.path.normcase(
                        os.path.abspath(os.fsdecode(path))
                    )
                except TypeError:
                    return status
                if not replaced or candidate_key != root_key:
                    return status
                values = list(status)
                values[1] = max(1, int(status.st_ino) + 1)
                return os.stat_result(values)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ), mock.patch.object(
                verification.os,
                "stat",
                side_effect=replacement_stat,
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                context = verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                )
                capability = context.__enter__()
                try:
                    verification.finalize_verification_evidence(
                        prepared,
                        root=root,
                        capability=capability,
                    )
                    verification.validate_active_verification_lock(
                        prepared,
                        root=root,
                        capability=capability,
                    )
                    replaced = True
                    with self.assertRaisesRegex(
                        ValueError,
                        "verification root identity mismatch",
                    ):
                        verification.validate_active_verification_lock(
                            prepared,
                            root=root,
                            capability=capability,
                        )
                finally:
                    replaced = False
                    context.__exit__(None, None, None)

    def test_lock_context_exit_revalidates_root_identity(self) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-exit-lease-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            root_key = os.path.normcase(os.path.abspath(root))
            real_stat = verification.os.stat
            replaced = False

            def replacement_stat(
                path: object,
                *args: object,
                **kwargs: object,
            ) -> os.stat_result:
                status = real_stat(path, *args, **kwargs)
                try:
                    candidate_key = os.path.normcase(
                        os.path.abspath(os.fsdecode(path))
                    )
                except TypeError:
                    return status
                if not replaced or candidate_key != root_key:
                    return status
                values = list(status)
                values[1] = max(1, int(status.st_ino) + 1)
                return os.stat_result(values)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ), mock.patch.object(
                verification.os,
                "stat",
                side_effect=replacement_stat,
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                try:
                    with self.assertRaisesRegex(
                        ValueError,
                        "verification root identity mismatch",
                    ):
                        with verification.exclusive_verification_lock(
                            prepared,
                            root=root,
                            recovery_dir=recovery_dir,
                        ) as capability:
                            verification.finalize_verification_evidence(
                                prepared,
                                root=root,
                                capability=capability,
                            )
                            replaced = True
                finally:
                    replaced = False

    def test_expired_capability_does_not_pin_prepared_state_and_pickle_rejects(
        self,
    ) -> None:
        import gc
        import pickle
        import weakref

        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-capability-gc-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                return_value=deepcopy(snapshot),
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                prepared = verification.prepare_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                with self.assertRaisesRegex(TypeError, "cannot be copied"):
                    pickle.dumps(prepared)
                prepared_identity = id(prepared)
                prepared_reference = weakref.ref(prepared)
                recovery_dir = (
                    root / ".tmp/emotion-state-001-phase-a-publication"
                )
                with verification.exclusive_verification_lock(
                    prepared,
                    root=root,
                    recovery_dir=recovery_dir,
                ) as capability:
                    with self.assertRaisesRegex(
                        TypeError,
                        "cannot be copied",
                    ):
                        pickle.dumps(capability)
                capability_identity = id(capability)
                capability_reference = weakref.ref(capability)

                del prepared
                gc.collect()
                self.assertIsNone(prepared_reference())
                self.assertNotIn(
                    prepared_identity,
                    verification._PREPARED_VERIFICATION_STATES,
                )
                self.assertIn(
                    capability_identity,
                    verification._VERIFICATION_LOCK_CAPABILITIES,
                )

                del capability
                gc.collect()
                self.assertIsNone(capability_reference())
                self.assertNotIn(
                    capability_identity,
                    verification._VERIFICATION_LOCK_CAPABILITIES,
                )

    def test_caller_locked_finalize_rejects_real_file_and_policy_races(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        for mutation in ("policy", "snapshot-file"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(
                prefix=f"emotion-state-verification-{mutation}-race-",
            ) as temporary_directory:
                root = Path(temporary_directory)
                policy_bytes, snapshot, ledger = self._phase_fixture(
                    root,
                    baseline_commit,
                    head_commit,
                )
                input_path = root / "scripts/input.py"
                input_path.parent.mkdir(parents=True)
                input_path.write_bytes(b"initial input\n")

                def collect_snapshot(**_: object) -> dict[str, object]:
                    current = deepcopy(snapshot)
                    current["uncommitted_change_inventory"][0][
                        "sha256"
                    ] = hashlib.sha256(
                        input_path.read_bytes()
                    ).hexdigest().upper()
                    return current

                with mock.patch.object(
                    verification,
                    "_collect_verification_snapshot",
                    side_effect=collect_snapshot,
                ), mock.patch.object(
                    verification,
                    "_execute_guarded_commands",
                    return_value=deepcopy(ledger),
                ):
                    prepared = verification.prepare_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )
                    if mutation == "policy":
                        (
                            root
                            / "research/sources/emotion_state/"
                            "phase_a_verification_guard_policy.json"
                        ).write_bytes(policy_bytes + b"\n")
                    else:
                        input_path.write_bytes(b"mutated after prepare\n")
                    recovery_dir = (
                        root / ".tmp/emotion-state-001-phase-a-publication"
                    )
                    with verification.exclusive_verification_lock(
                        prepared,
                        root=root,
                        recovery_dir=recovery_dir,
                    ) as capability:
                        with self.assertRaisesRegex(
                            ValueError,
                            "^verification inputs changed during locked re-read$",
                        ):
                            verification.finalize_verification_evidence(
                                prepared,
                                root=root,
                                capability=capability,
                            )
                        with self.assertRaisesRegex(
                            ValueError,
                            "already consumed",
                        ):
                            verification.finalize_verification_evidence(
                                prepared,
                                root=root,
                                capability=capability,
                            )

    def test_wrapper_signature_and_exclusive_lock_behavior_are_preserved(
        self,
    ) -> None:
        import inspect

        import scripts.emotion_state_phase_a_verification_evidence as verification

        self.assertEqual(
            str(inspect.signature(verification.build_verification_evidence)),
            (
                "(root: 'Path', baseline_commit: 'str', "
                "head_commit: 'str', mode: 'str') -> 'dict[str, object]'"
            ),
        )
        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-wrapper-lock-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            _policy_bytes, snapshot, ledger = self._phase_fixture(
                root,
                baseline_commit,
                head_commit,
            )
            recovery_dir = (
                root / ".tmp/emotion-state-001-phase-a-publication"
            )
            lock_path = recovery_dir / "publication.lock"
            lock_observations: list[bytes | None] = []

            def collect_snapshot(**_: object) -> dict[str, object]:
                lock_observations.append(
                    lock_path.read_bytes()
                    if lock_path.exists()
                    else None
                )
                return deepcopy(snapshot)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                side_effect=collect_snapshot,
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=deepcopy(ledger),
            ):
                verification.build_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )

            self.assertEqual(lock_observations, [None, b""])
            self.assertFalse(lock_path.exists())


class VerificationEvidenceTests(unittest.TestCase):
    POLICY_PATH = (
        ROOT
        / "research/sources/emotion_state/phase_a_verification_guard_policy.json"
    )
    GUARD_SITE_PATH = ROOT / "scripts/emotion_state_phase_a_guard_site"
    PARENT_ENVIRONMENT_ALLOWLIST = (
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "WINDIR",
    )
    PROVIDER_ENVIRONMENT_EXACT_NAMES = (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "CARTESIA_API_KEY",
        "DIALOGUE_REASONER_API_KEY",
        "ELEVENLABS_API_KEY",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "GROQ_API_KEY",
        "HF_TOKEN",
        "HUGGING_FACE_HUB_TOKEN",
        "LOCAL_DIALOGUE_REASONER_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_SECRET",
        "OPENROUTER_API_KEY",
        "TOGETHER_API_KEY",
        "TOOL_AUTH_TOKEN",
        "ULTRAVOX_API_KEY",
    )

    @staticmethod
    def _verification_module():
        import scripts.emotion_state_phase_a_verification_evidence as verification

        return verification

    def _guarded_child_environment(
        self,
        project_root: Path,
        *,
        allowed_subprocesses_json: str = "[]",
        extra_parent_environment: dict[str, str] | None = None,
    ) -> tuple[dict[str, str], list[str]]:
        verification = self._verification_module()
        transaction_root = project_root / "guard-runtime"
        transaction_root.mkdir(exist_ok=True)
        parent_environment = {
            name: os.environ[name]
            for name in self.PARENT_ENVIRONMENT_ALLOWLIST
            if name in os.environ
        }
        if extra_parent_environment is not None:
            parent_environment.update(extra_parent_environment)
        injected_environment = {
            "EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON": (
                allowed_subprocesses_json
            ),
            "EMOTION_STATE_PHASE_A_GUARD_POLICY": str(self.POLICY_PATH),
            "EMOTION_STATE_PHASE_A_PROJECT_ROOT": str(project_root),
            "GIT_CONFIG_GLOBAL": "NUL",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": str(transaction_root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": os.pathsep.join((
                str(self.GUARD_SITE_PATH),
                str(ROOT),
            )),
            "PYTHONUTF8": "1",
            "TEMP": str(transaction_root),
            "TMP": str(transaction_root),
            "USERPROFILE": str(transaction_root),
        }
        return verification.build_guarded_child_environment(
            parent_environment=parent_environment,
            injected_environment=injected_environment,
        )

    def _run_guarded_child(
        self,
        project_root: Path,
        source: str,
        *,
        allowed_subprocesses_json: str = "[]",
        extra_parent_environment: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        environment, removed_names = self._guarded_child_environment(
            project_root,
            allowed_subprocesses_json=allowed_subprocesses_json,
            extra_parent_environment=extra_parent_environment,
        )
        completed = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(source)],
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=(
                f"guarded child failed with exit {completed.returncode}\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            ),
        )
        return completed, removed_names

    def _run_guarded_target(
        self,
        project_root: Path,
        target_relative_path: str,
        *,
        allowed_subprocesses: object,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        allowed_json = (
            allowed_subprocesses
            if isinstance(allowed_subprocesses, str)
            else json.dumps(
                allowed_subprocesses,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        environment, _removed_names = self._guarded_child_environment(
            project_root,
            allowed_subprocesses_json=allowed_json,
        )
        return subprocess.run(
            [
                sys.executable,
                str(project_root / target_relative_path),
            ],
            cwd=project_root if cwd is None else cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

    def test_policy_exclusions_are_exact_and_outputs_do_not_self_hash(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import OUTPUT_EXCLUSIONS

        self.assertEqual(OUTPUT_EXCLUSIONS, (
            "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json",
            "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md",
            ".tmp/emotion-state-001-phase-a-publication/**",
        ))

    def test_child_environment_is_allowlisted_without_logging_values(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import (
            build_guarded_child_environment,
        )

        cleaned, removed_names = build_guarded_child_environment(
            parent_environment={
                "PATH": "safe",
                "SYSTEMROOT": r"C:\Windows",
                "DIALOGUE_REASONER_API_KEY": "fixture-only",
                "GH_TOKEN": "fixture-only",
                "GITHUB_TOKEN": "fixture-only",
                "HF_TOKEN": "fixture-only",
                "AWS_SECRET_ACCESS_KEY": "fixture-only",
                "TOOL_AUTH_TOKEN": "fixture-only",
                "UNLISTED_BENIGN": "fixture-only",
            },
            injected_environment={
                "EMOTION_STATE_PHASE_A_GUARD_POLICY": "fixture-policy",
            },
        )
        self.assertEqual(cleaned, {
            "EMOTION_STATE_PHASE_A_GUARD_POLICY": "fixture-policy",
            "PATH": "safe",
            "SYSTEMROOT": r"C:\Windows",
        })
        self.assertEqual(removed_names, [
            "AWS_SECRET_ACCESS_KEY",
            "DIALOGUE_REASONER_API_KEY",
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "HF_TOKEN",
            "TOOL_AUTH_TOKEN",
            "UNLISTED_BENIGN",
        ])
        self.assertNotIn("fixture-only", json.dumps(removed_names))

    def test_ledger_is_relative_deterministic_and_timestamp_free(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import (
            canonical_command_entry,
        )

        entry = canonical_command_entry(
            sequence_number=1,
            command_id="focused-contract-tests",
            argv=[
                "python",
                "-m",
                "unittest",
                "scripts.test_emotion_state_001_open_dataset_gate",
            ],
            working_directory=".",
            exit_status=0,
        )
        self.assertEqual(entry["working_directory"], ".")
        self.assertNotIn("timestamp", entry)
        self.assertNotIn(str(ROOT), json.dumps(entry))

    def test_repository_gates_are_derived_only_from_exact_mode_ledger(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import (
            REPOSITORY_GATE_COMMAND_IDS,
            derive_repository_gate_statuses,
            validate_completion_evidence_request,
        )

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        policy_commands = (
            (
                "focused-open-dataset-tests",
                (
                    "python",
                    "-m",
                    "unittest",
                    "scripts.test_emotion_state_001_open_dataset_gate",
                    "-v",
                ),
            ),
            (
                "closeout-hardening-tests",
                (
                    "python",
                    "-m",
                    "unittest",
                    "scripts.test_emotion_state_001_closeout_hardening",
                    "-v",
                ),
            ),
            (
                "phase-a-prepublication-validator",
                (
                    "python",
                    "scripts/validate_emotion_state_001_phase_a_contracts.py",
                    "--section",
                    "prepublication",
                    "--mode",
                    "{mode}",
                ),
            ),
            (
                "phase-a-materials-validator",
                (
                    "python",
                    "scripts/validate_emotion_state_001_phase_a_contracts.py",
                    "--section",
                    "materials",
                ),
            ),
            (
                "frozen-exp-002-validator",
                (
                    "python",
                    "scripts/validate_exp_002_frozen_response_baseline.py",
                ),
            ),
            (
                "brain-schema-validator",
                (
                    "python",
                    "scripts/validate_brain_002_runtime_state_schema.py",
                ),
            ),
            (
                "private-boundary-validator",
                (
                    "python",
                    "scripts/validate_private_data_boundary.py",
                ),
            ),
            (
                "runtime-manifest-validator",
                (
                    "python",
                    "scripts/validate_runtime_manifest.py",
                ),
            ),
            (
                "setup-validator",
                (
                    "python",
                    "scripts/validate_check_setup.py",
                ),
            ),
            (
                "drift-validator",
                (
                    "python",
                    "scripts/validate_project_drift_guard.py",
                ),
            ),
            (
                "thesis-reference-validator",
                (
                    "python",
                    "scripts/check_thesis_reference_registry.py",
                ),
            ),
            (
                "thesis-update-validator",
                (
                    "python",
                    "scripts/check_thesis_update_gate.py",
                ),
            ),
            (
                "context-policy-validator",
                (
                    "python",
                    "scripts/validate_context_reading_policy.py",
                ),
            ),
            (
                "json-validator",
                (
                    "python",
                    "scripts/emotion_state_phase_a_verification_evidence.py",
                    "--validate-json-inputs",
                ),
            ),
            (
                "git-diff-check",
                (
                    "git",
                    "diff",
                    "--check",
                    "{baseline_commit}..{head_commit}",
                ),
            ),
        )
        expected_gate_commands = {
            "focused_tests": ("focused-open-dataset-tests",),
            "closeout_hardening": ("closeout-hardening-tests",),
            "phase_a_prepublication": ("phase-a-prepublication-validator",),
            "materials": ("phase-a-materials-validator",),
            "frozen_exp_002": ("frozen-exp-002-validator",),
            "brain_schema": ("brain-schema-validator",),
            "private_boundary": ("private-boundary-validator",),
            "runtime_manifest": ("runtime-manifest-validator",),
            "setup": ("setup-validator",),
            "drift": ("drift-validator",),
            "thesis_reference_registry": ("thesis-reference-validator",),
            "thesis_update": ("thesis-update-validator",),
            "context_policy": ("context-policy-validator",),
            "json": ("json-validator",),
            "diff_check": ("git-diff-check",),
        }

        def build_ledger(mode: str) -> list[dict[str, object]]:
            commands = policy_commands
            if mode == "material-pending":
                commands = tuple(
                    command
                    for command in commands
                    if command[0] != "phase-a-materials-validator"
                )
            return [
                {
                    "sequence_number": sequence_number,
                    "command_id": command_id,
                    "argv": [
                        argument.format(
                            mode=mode,
                            baseline_commit=baseline_commit,
                            head_commit=head_commit,
                        )
                        for argument in argv_template
                    ],
                    "working_directory": ".",
                    "exit_status": 0,
                }
                for sequence_number, (command_id, argv_template) in enumerate(
                    commands,
                    start=1,
                )
            ]

        self.assertEqual(
            tuple(REPOSITORY_GATE_COMMAND_IDS.items()),
            tuple(expected_gate_commands.items()),
        )
        complete_ledger = build_ledger("complete")
        material_pending_ledger = build_ledger("material-pending")
        self.assertEqual(
            tuple(
                derive_repository_gate_statuses(
                    complete_ledger,
                    "complete",
                ).items()
            ),
            tuple((gate_id, "pass") for gate_id in expected_gate_commands),
        )
        self.assertEqual(
            tuple(
                derive_repository_gate_statuses(
                    material_pending_ledger,
                    "material-pending",
                ).items()
            ),
            tuple(
                (gate_id, "pass")
                for gate_id in expected_gate_commands
                if gate_id != "materials"
            ),
        )

        missing = deepcopy(complete_ledger)
        missing.pop(7)
        for sequence_number, entry in enumerate(missing, start=1):
            entry["sequence_number"] = sequence_number
        duplicate = deepcopy(complete_ledger)
        duplicate.append(deepcopy(duplicate[0]))
        duplicate[-1]["sequence_number"] = len(duplicate)
        reordered = deepcopy(complete_ledger)
        reordered[5], reordered[6] = reordered[6], reordered[5]
        for sequence_number, entry in enumerate(reordered, start=1):
            entry["sequence_number"] = sequence_number
        argv_mismatch = deepcopy(complete_ledger)
        argv_mismatch[2]["argv"][-1] = "material-pending"
        nonzero = deepcopy(complete_ledger)
        nonzero[9]["exit_status"] = 1
        unknown_id = deepcopy(complete_ledger)
        unknown_id[12]["command_id"] = "unknown-validator"
        invalid_ledgers = {
            "missing": missing,
            "duplicate": duplicate,
            "reordered": reordered,
            "argv_template_mismatch": argv_mismatch,
            "nonzero": nonzero,
            "unknown_id": unknown_id,
        }
        for case_name, invalid_ledger in invalid_ledgers.items():
            with self.subTest(case=case_name):
                with self.assertRaises(ValueError):
                    derive_repository_gate_statuses(
                        invalid_ledger,
                        "complete",
                    )

        derived_projection_cases = {
            "repository_gate_statuses": {
                gate_id: "pass"
                for gate_id in expected_gate_commands
            },
            "guarded_command_results": {
                entry["command_id"]: entry["exit_status"]
                for entry in complete_ledger
            },
        }
        for field_name, caller_projection in derived_projection_cases.items():
            with self.subTest(caller_projection=field_name):
                request = {
                    "mode": "complete",
                    "executed_command_ledger": deepcopy(complete_ledger),
                    field_name: caller_projection,
                }
                self.assertEqual(
                    tuple(request),
                    ("mode", "executed_command_ledger", field_name),
                )
                with self.assertRaisesRegex(ValueError, "derived-only"):
                    validate_completion_evidence_request(request)

    def test_guarded_command_is_policy_built_and_rejects_bad_substitutions(
        self,
    ) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import (
            run_guarded_command,
        )

        entry = run_guarded_command(
            "context-policy-validator",
            ROOT,
            {},
        )
        self.assertEqual(
            set(entry),
            {
                "sequence_number",
                "command_id",
                "argv",
                "working_directory",
                "exit_status",
            },
        )
        self.assertEqual(entry["sequence_number"], 1)
        self.assertEqual(entry["command_id"], "context-policy-validator")
        self.assertEqual(
            entry["argv"],
            [
                "python",
                "scripts/validate_context_reading_policy.py",
            ],
        )
        self.assertEqual(entry["working_directory"], ".")
        self.assertEqual(entry["exit_status"], 0)
        serialized_entry = json.dumps(entry, sort_keys=True)
        self.assertNotIn("timestamp", serialized_entry)
        self.assertNotIn("environment", serialized_entry)
        self.assertNotIn(str(ROOT), serialized_entry)

        invalid_calls = (
            ("unknown-validator", {}),
            ("context-policy-validator", {"mode": "complete"}),
            ("phase-a-prepublication-validator", {}),
            (
                "phase-a-prepublication-validator",
                {"mode": "not-a-reviewed-mode"},
            ),
            (
                "git-diff-check",
                {
                    "baseline_commit": "a" * 39,
                    "head_commit": "b" * 40,
                },
            ),
            (
                "git-diff-check",
                {
                    "baseline_commit": "A" * 40,
                    "head_commit": "b" * 40,
                },
            ),
            (
                "git-diff-check",
                {
                    "baseline_commit": "a" * 40,
                    "head_commit": "not-a-commit",
                },
            ),
            (
                "git-diff-check",
                {
                    "baseline_commit": "a" * 40,
                    "head_commit": "b" * 40,
                    "mode": "complete",
                },
            ),
        )
        for command_id, substitutions in invalid_calls:
            with self.subTest(
                command_id=command_id,
                substitutions=substitutions,
            ):
                with self.assertRaises(ValueError):
                    run_guarded_command(
                        command_id,
                        ROOT,
                        substitutions,
                    )

    def test_json_validation_is_derived_path_only_and_rejects_duplicate_keys(
        self,
    ) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import (
            parse_args,
            validate_json_inputs,
        )

        args = parse_args(["--validate-json-inputs"])
        self.assertTrue(args.validate_json_inputs)
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            parse_args(["--validate-json-inputs", "arbitrary.json"])
        self.assertEqual(raised.exception.code, 2)

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-json-inputs-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            (root / "changed").mkdir()
            (root / "closure").mkdir()
            (root / "changed/valid.json").write_text(
                '{"changed":true}\n',
                encoding="utf-8",
            )
            (root / "closure/valid.json").write_text(
                '{"closure":true}\n',
                encoding="utf-8",
            )
            self.assertEqual(
                validate_json_inputs(
                    root=root,
                    changed_json_paths=("changed/valid.json",),
                    closure_json_paths=("closure/valid.json",),
                ),
                (
                    "changed/valid.json",
                    "closure/valid.json",
                ),
            )

            duplicate_cases = (
                ("changed", "changed/duplicate.json"),
                ("closure", "closure/duplicate.json"),
            )
            for source, relative_path in duplicate_cases:
                with self.subTest(source=source):
                    (root / relative_path).write_text(
                        '{"duplicate":1,"duplicate":2}\n',
                        encoding="utf-8",
                    )
                    changed_paths = (
                        (relative_path,)
                        if source == "changed"
                        else ("changed/valid.json",)
                    )
                    closure_paths = (
                        (relative_path,)
                        if source == "closure"
                        else ("closure/valid.json",)
                    )
                    with self.assertRaisesRegex(
                        ValueError,
                        "duplicate JSON key",
                    ):
                        validate_json_inputs(
                            root=root,
                            changed_json_paths=changed_paths,
                            closure_json_paths=closure_paths,
                        )

            with self.assertRaisesRegex(ValueError, "escapes"):
                validate_json_inputs(
                    root=root,
                    changed_json_paths=("../outside.json",),
                    closure_json_paths=(),
                )

    def test_verification_evidence_digests_are_deterministic_and_output_free(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40

        def canonical_digest(value: object) -> str:
            payload = (
                json.dumps(
                    value,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
            return hashlib.sha256(payload).hexdigest().upper()

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-digest-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            policy_path = (
                root
                / "research/sources/emotion_state/"
                "phase_a_verification_guard_policy.json"
            )
            policy_path.parent.mkdir(parents=True)
            policy_bytes = self.POLICY_PATH.read_bytes()
            policy_path.write_bytes(policy_bytes)
            policy = json.loads(policy_bytes.decode("utf-8"))

            ledger: list[dict[str, object]] = []
            for command in policy["allowed_commands"]:
                if command["command_id"] == "phase-a-materials-validator":
                    continue
                argv = [
                    argument.format(
                        mode="material-pending",
                        baseline_commit=baseline_commit,
                        head_commit=head_commit,
                    )
                    for argument in command["argv_template"]
                ]
                ledger.append({
                    "sequence_number": len(ledger) + 1,
                    "command_id": command["command_id"],
                    "argv": argv,
                    "working_directory": ".",
                    "exit_status": 0,
                })

            committed_inventory = [{
                "path": "scripts/fixture.py",
                "git_mode": "100644",
                "sha256": "A" * 64,
            }]
            uncommitted_inventory = [{
                "path": "research/fixture.json",
                "git_state": "untracked",
                "git_mode": "100644",
                "sha256": "B" * 64,
            }]
            closure_inventory = [{
                "path": "scripts/fixture.py",
                "git_mode": "100644",
                "sha256": "A" * 64,
            }]
            closure_edges: list[dict[str, str]] = []
            closure_digest = canonical_digest({
                "edges": closure_edges,
                "inventory": closure_inventory,
            })
            snapshot = {
                "committed_change_inventory": committed_inventory,
                "uncommitted_change_inventory": uncommitted_inventory,
                "executable_dependency_closure": {
                    "inventory": closure_inventory,
                    "edges": closure_edges,
                    "digest": closure_digest,
                },
                "dataset_manifest_digests": {},
                "dataset_hash_inventory_digests": {},
            }

            def collect_snapshot(**_: object) -> dict[str, object]:
                return deepcopy(snapshot)

            def execute_commands(**_: object) -> list[dict[str, object]]:
                return deepcopy(ledger)

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                side_effect=collect_snapshot,
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                side_effect=execute_commands,
            ):
                first = verification.build_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )
                second = verification.build_verification_evidence(
                    root,
                    baseline_commit,
                    head_commit,
                    "material-pending",
                )

            self.assertEqual(first, second)
            input_inventory_digest = canonical_digest({
                "committed_change_inventory": committed_inventory,
                "uncommitted_change_inventory": uncommitted_inventory,
            })
            ledger_digest = canonical_digest(ledger)
            guard_policy_digest = hashlib.sha256(policy_bytes).hexdigest().upper()
            tree_payload = {
                "implementation_baseline_commit": baseline_commit,
                "repository_head_commit": head_commit,
                "committed_change_inventory": committed_inventory,
                "uncommitted_change_inventory": uncommitted_inventory,
                "executable_dependency_closure_inventory": closure_inventory,
                "executable_dependency_closure_edges": closure_edges,
                "dataset_manifest_digests": {},
                "dataset_hash_inventory_digests": {},
                "executed_command_ledger": ledger,
                "guard_policy_digest": guard_policy_digest,
            }
            tree_digest = canonical_digest(tree_payload)
            expected_run_id = hashlib.sha256(
                (
                    "emotion-state-phase-a-validator-v1:"
                    + tree_digest
                ).encode("utf-8")
            ).hexdigest().upper()
            self.assertEqual(
                first["verification_input_path_inventory_digest"],
                input_inventory_digest,
            )
            self.assertEqual(
                first["executable_dependency_closure_digest"],
                closure_digest,
            )
            self.assertEqual(
                first["executed_command_ledger_digest"],
                ledger_digest,
            )
            self.assertEqual(first["guard_policy_digest"], guard_policy_digest)
            self.assertEqual(first["verification_input_tree_digest"], tree_digest)
            self.assertEqual(first["verification_run_id"], expected_run_id)
            self.assertEqual(
                first["guarded_command_results"],
                {
                    entry["command_id"]: entry["exit_status"]
                    for entry in ledger
                },
            )
            self.assertTrue(
                all(
                    value == "pass"
                    for value in first["repository_gate_statuses"].values()
                )
            )
            self.assertTrue(first["provider_environment_scrubbed"])
            self.assertTrue(first["private_path_guard_enabled"])
            self.assertTrue(first["network_guard_enabled"])
            serialized = json.dumps(first, sort_keys=True)
            self.assertNotIn("timestamp", serialized)
            self.assertNotIn(str(root), serialized)
            self.assertNotIn("result.json sha256", serialized)

    def test_locked_reread_aborts_on_input_race_without_touching_valid_pair(
        self,
    ) -> None:
        import scripts.emotion_state_phase_a_verification_evidence as verification

        baseline_commit = "a" * 40
        head_commit = "b" * 40
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-verification-race-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            policy_path = (
                root
                / "research/sources/emotion_state/"
                "phase_a_verification_guard_policy.json"
            )
            policy_path.parent.mkdir(parents=True)
            policy_path.write_bytes(self.POLICY_PATH.read_bytes())
            input_path = root / "scripts/input.py"
            input_path.parent.mkdir(parents=True)
            input_path.write_bytes(b"initial input\n")
            output_root = (
                root
                / "research/experiments/generated/"
                "EMOTION-STATE-001-phase-a-contracts"
            )
            output_root.mkdir(parents=True)
            result_path = output_root / "result.json"
            report_path = output_root / "report.md"
            original_result = b'{"last_valid":true}\n'
            original_report = b"# Last valid report\n"
            result_path.write_bytes(original_result)
            report_path.write_bytes(original_report)
            recovery_dir = (
                root / ".tmp/emotion-state-001-phase-a-publication"
            )
            calls = 0

            def snapshot() -> dict[str, object]:
                content = input_path.read_bytes()
                digest = hashlib.sha256(content).hexdigest().upper()
                inventory = [{
                    "path": "scripts/input.py",
                    "git_state": "untracked",
                    "git_mode": "100644",
                    "sha256": digest,
                }]
                return {
                    "committed_change_inventory": [],
                    "uncommitted_change_inventory": inventory,
                    "executable_dependency_closure": {
                        "inventory": [],
                        "edges": [],
                        "digest": hashlib.sha256(b'{"edges":[],"inventory":[]}\n')
                        .hexdigest()
                        .upper(),
                    },
                    "dataset_manifest_digests": {},
                    "dataset_hash_inventory_digests": {},
                }

            def collect_snapshot(**_: object) -> dict[str, object]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    self.assertTrue(
                        (recovery_dir / "publication.lock").exists()
                    )
                    input_path.write_bytes(b"mutated after validation\n")
                return snapshot()

            with mock.patch.object(
                verification,
                "_collect_verification_snapshot",
                side_effect=collect_snapshot,
            ), mock.patch.object(
                verification,
                "_execute_guarded_commands",
                return_value=[],
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "verification inputs changed during locked re-read",
                ):
                    verification.build_verification_evidence(
                        root,
                        baseline_commit,
                        head_commit,
                        "material-pending",
                    )

            self.assertEqual(calls, 2)
            self.assertEqual(result_path.read_bytes(), original_result)
            self.assertEqual(report_path.read_bytes(), original_report)

    def test_guard_policy_is_exact_unique_and_substitution_closed(self) -> None:
        self._verification_module()
        policy = json.loads(self.POLICY_PATH.read_text(encoding="utf-8"))
        expected_policy = {
            "policy_id": "emotion-state-phase-a-verification-guard-v1",
            "schema_version": 1,
            "network_allowed": False,
            "private_path_prefixes": [
                "data/private",
                "data/private-restricted",
            ],
            "parent_environment_allowlist": [
                "COMSPEC",
                "PATH",
                "PATHEXT",
                "SYSTEMDRIVE",
                "SYSTEMROOT",
                "WINDIR",
            ],
            "guard_generated_environment_names": [
                "EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON",
                "EMOTION_STATE_PHASE_A_GUARD_POLICY",
                "EMOTION_STATE_PHASE_A_PROJECT_ROOT",
                "GIT_CONFIG_GLOBAL",
                "GIT_CONFIG_NOSYSTEM",
                "GIT_TERMINAL_PROMPT",
                "HOME",
                "PYTHONDONTWRITEBYTECODE",
                "PYTHONIOENCODING",
                "PYTHONPATH",
                "PYTHONUTF8",
                "TEMP",
                "TMP",
                "USERPROFILE",
            ],
            "provider_environment_exact_names": list(
                self.PROVIDER_ENVIRONMENT_EXACT_NAMES
            ),
            "provider_environment_prefixes": [
                "ASSEMBLYAI_",
                "AWS_",
                "CARTESIA_",
                "DEEPGRAM_",
                "DIALOGUE_REASONER_",
                "ELEVENLABS_",
                "GH_",
                "GITHUB_",
                "GROQ_",
                "HF_",
                "HUGGING_FACE_",
                "LOCAL_DIALOGUE_REASONER_",
                "OPENAI_",
                "OPENROUTER_",
                "TOGETHER_",
                "TWILIO_",
                "ULTRAVOX_",
            ],
            "credential_environment_name_pattern": (
                "(^|_)(API_KEY|ACCESS_KEY|ACCESS_TOKEN|AUTH_TOKEN|"
                "BEARER_TOKEN|PRIVATE_KEY|SECRET|TOKEN|PASSWORD)$"
            ),
            "forbidden_import_prefixes": [
                "_socket",
                "aiohttp",
                "assemblyai",
                "cartesia",
                "ctypes",
                "deepgram",
                "elevenlabs",
                "ftplib",
                "github",
                "groq",
                "http",
                "httpx",
                "openai",
                "openrouter",
                "requests",
                "socket",
                "together",
                "twilio",
                "ultravox",
                "urllib",
            ],
            "output_exclusions": [
                (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/result.json"
                ),
                (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/report.md"
                ),
                ".tmp/emotion-state-001-phase-a-publication/**",
            ],
            "canonical_output_files": [
                "result.json",
                "report.md",
            ],
            "allowed_commands": [
                {
                    "command_id": "focused-open-dataset-tests",
                    "argv_template": [
                        "python",
                        "-m",
                        "unittest",
                        "scripts.test_emotion_state_001_open_dataset_gate",
                        "-v",
                    ],
                },
                {
                    "command_id": "closeout-hardening-tests",
                    "argv_template": [
                        "python",
                        "-m",
                        "unittest",
                        "scripts.test_emotion_state_001_closeout_hardening",
                        "-v",
                    ],
                },
                {
                    "command_id": "phase-a-prepublication-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_emotion_state_001_phase_a_contracts.py",
                        "--section",
                        "prepublication",
                        "--mode",
                        "{mode}",
                    ],
                },
                {
                    "command_id": "phase-a-materials-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_emotion_state_001_phase_a_contracts.py",
                        "--section",
                        "materials",
                    ],
                },
                {
                    "command_id": "frozen-exp-002-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_exp_002_frozen_response_baseline.py",
                    ],
                },
                {
                    "command_id": "brain-schema-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_brain_002_runtime_state_schema.py",
                    ],
                },
                {
                    "command_id": "private-boundary-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_private_data_boundary.py",
                    ],
                },
                {
                    "command_id": "runtime-manifest-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_runtime_manifest.py",
                    ],
                },
                {
                    "command_id": "setup-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_check_setup.py",
                    ],
                },
                {
                    "command_id": "drift-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_project_drift_guard.py",
                    ],
                },
                {
                    "command_id": "thesis-reference-validator",
                    "argv_template": [
                        "python",
                        "scripts/check_thesis_reference_registry.py",
                    ],
                },
                {
                    "command_id": "thesis-update-validator",
                    "argv_template": [
                        "python",
                        "scripts/check_thesis_update_gate.py",
                    ],
                },
                {
                    "command_id": "context-policy-validator",
                    "argv_template": [
                        "python",
                        "scripts/validate_context_reading_policy.py",
                    ],
                },
                {
                    "command_id": "json-validator",
                    "argv_template": [
                        "python",
                        "scripts/emotion_state_phase_a_verification_evidence.py",
                        "--validate-json-inputs",
                    ],
                },
                {
                    "command_id": "git-diff-check",
                    "argv_template": [
                        "git",
                        "diff",
                        "--check",
                        "{baseline_commit}..{head_commit}",
                    ],
                },
            ],
        }
        self.assertEqual(policy, expected_policy)
        command_ids = [
            command["command_id"]
            for command in policy["allowed_commands"]
        ]
        command_templates = [
            tuple(command["argv_template"])
            for command in policy["allowed_commands"]
        ]
        self.assertEqual(len(command_ids), len(set(command_ids)))
        self.assertEqual(len(command_templates), len(set(command_templates)))
        substitutions = {
            substitution
            for command in policy["allowed_commands"]
            for argument in command["argv_template"]
            for substitution in re.findall(r"\{([a-z_]+)\}", argument)
        }
        self.assertEqual(
            substitutions,
            {"baseline_commit", "head_commit", "mode"},
        )

    def test_guard_denies_synthetic_private_paths_and_allows_public_fixtures(
        self,
    ) -> None:
        self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-private-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            public_directory = project_root / "public"
            public_directory.mkdir()
            public_file = public_directory / "fixture.txt"
            public_file.write_bytes(b"public-fixture")
            public_link = public_directory / "fixture-link.txt"
            try:
                public_link.symlink_to(public_file.name)
            except OSError as exc:
                if not (
                    os.name == "nt"
                    and getattr(exc, "winerror", None) == 1314
                ):
                    raise

            completed, _ = self._run_guarded_child(
                project_root,
                """
                import builtins
                import io
                import os
                from pathlib import Path

                project_root = Path(
                    os.environ["EMOTION_STATE_PHASE_A_PROJECT_ROOT"]
                )

                def expect_denied(label, operation):
                    resource = None
                    try:
                        resource = operation()
                    except PermissionError:
                        return
                    except BaseException as exc:
                        raise AssertionError(
                            f"{label} raised {type(exc).__name__}, "
                            "not PermissionError"
                        ) from exc
                    finally:
                        if isinstance(resource, int):
                            os.close(resource)
                        elif resource is not None and hasattr(resource, "close"):
                            resource.close()
                    raise AssertionError(f"{label} was not denied")

                for private_prefix in (
                    Path("data/private"),
                    Path("data/private-restricted"),
                ):
                    private_directory = project_root / private_prefix
                    private_file = private_directory / "missing.txt"
                    private_link = private_directory / "missing-link.txt"
                    operations = (
                        (
                            "builtins.open",
                            lambda path=private_file: builtins.open(path, "rb"),
                        ),
                        (
                            "io.open",
                            lambda path=private_file: io.open(path, "rb"),
                        ),
                        (
                            "os.open",
                            lambda path=private_file: os.open(path, os.O_RDONLY),
                        ),
                        (
                            "os.stat",
                            lambda path=private_file: os.stat(path),
                        ),
                        (
                            "os.lstat",
                            lambda path=private_file: os.lstat(path),
                        ),
                        (
                            "os.listdir",
                            lambda path=private_directory: os.listdir(path),
                        ),
                        (
                            "os.scandir",
                            lambda path=private_directory: os.scandir(path),
                        ),
                        (
                            "os.readlink",
                            lambda path=private_link: os.readlink(path),
                        ),
                    )
                    for operation_name, operation in operations:
                        expect_denied(
                            f"{private_prefix.as_posix()}:{operation_name}",
                            operation,
                        )

                public_directory = project_root / "public"
                public_file = public_directory / "fixture.txt"
                public_link = public_directory / "fixture-link.txt"
                with builtins.open(public_file, "rb") as handle:
                    assert handle.read() == b"public-fixture"
                with io.open(public_file, "rb") as handle:
                    assert handle.read() == b"public-fixture"
                descriptor = os.open(public_file, os.O_RDONLY)
                try:
                    assert os.read(descriptor, 14) == b"public-fixture"
                finally:
                    os.close(descriptor)
                assert os.stat(public_file).st_size == 14
                assert os.lstat(public_file).st_size == 14
                public_link_exists = os.path.lexists(public_link)
                expected_names = ["fixture.txt"]
                if public_link_exists:
                    expected_names.insert(0, "fixture-link.txt")
                assert sorted(os.listdir(public_directory)) == expected_names
                with os.scandir(public_directory) as entries:
                    assert sorted(entry.name for entry in entries) == expected_names
                if public_link_exists:
                    assert os.readlink(public_link) == "fixture.txt"
                else:
                    try:
                        os.readlink(public_link)
                    except FileNotFoundError:
                        pass
                    except PermissionError as exc:
                        raise AssertionError(
                            "public missing-link read was denied by the guard"
                        ) from exc
                    else:
                        raise AssertionError(
                            "public missing-link read unexpectedly succeeded"
                        )
                dir_fd_operations = {
                    "os.open": lambda: os.open(
                        public_file,
                        os.O_RDONLY,
                        dir_fd=0,
                    ),
                    "os.stat": lambda: os.stat(public_file, dir_fd=0),
                    "os.lstat": lambda: os.lstat(public_file, dir_fd=0),
                    "os.readlink": lambda: os.readlink(public_link, dir_fd=0),
                }
                for name, operation in dir_fd_operations.items():
                    expect_denied(f"{name}:dir_fd", operation)
                print("guarded-private-paths-ok")
                """,
            )
            self.assertEqual(
                completed.stdout.strip(),
                "guarded-private-paths-ok",
            )

    def test_guard_denies_dns_inet_construction_and_socket_io_before_use(
        self,
    ) -> None:
        self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-network-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            completed, _ = self._run_guarded_child(
                project_root,
                """
                import socket

                expected_message = (
                    "EMOTION-STATE Phase A network access is blocked"
                )

                def expect_denied(label, operation):
                    try:
                        operation()
                    except PermissionError as exc:
                        assert str(exc) == expected_message, (
                            label,
                            str(exc),
                        )
                        return
                    except BaseException as exc:
                        raise AssertionError(
                            f"{label} raised {type(exc).__name__}, "
                            "not PermissionError"
                        ) from exc
                    raise AssertionError(f"{label} was not denied")

                dns_operations = {
                    "getaddrinfo": lambda: socket.getaddrinfo(
                        object(),
                        object(),
                    ),
                    "gethostbyname": lambda: socket.gethostbyname(object()),
                    "gethostbyname_ex": lambda: socket.gethostbyname_ex(
                        object()
                    ),
                    "gethostbyaddr": lambda: socket.gethostbyaddr(object()),
                    "getnameinfo": lambda: socket.getnameinfo(object(), 0),
                }
                for name, operation in dns_operations.items():
                    expect_denied(name, operation)

                for family_name in ("AF_INET", "AF_INET6"):
                    family = getattr(socket, family_name)
                    expect_denied(
                        family_name,
                        lambda family=family: socket.socket(family, object()),
                    )

                expect_denied(
                    "create_connection",
                    lambda: socket.create_connection((object(), object())),
                )
                expect_denied(
                    "create_server",
                    lambda: socket.create_server((object(), object())),
                )
                expect_denied("socketpair", lambda: socket.socketpair())
                expect_denied(
                    "fromfd",
                    lambda: socket.fromfd(
                        -1,
                        socket.AF_INET,
                        socket.SOCK_STREAM,
                    ),
                )
                socket_operations = {
                    "connect": lambda: socket.socket.connect(None, object()),
                    "connect_ex": lambda: socket.socket.connect_ex(
                        None,
                        object(),
                    ),
                    "send": lambda: socket.socket.send(None, b"fixture"),
                    "sendto": lambda: socket.socket.sendto(
                        None,
                        b"fixture",
                        object(),
                    ),
                    "bind": lambda: socket.socket.bind(None, object()),
                    "listen": lambda: socket.socket.listen(None),
                    "accept": lambda: socket.socket.accept(None),
                }
                if hasattr(socket.socket, "sendmsg"):
                    socket_operations["sendmsg"] = (
                        lambda: socket.socket.sendmsg(None, [b"fixture"])
                    )
                for name, operation in socket_operations.items():
                    expect_denied(name, operation)
                print("guarded-network-ok")
                """,
            )
            self.assertEqual(completed.stdout.strip(), "guarded-network-ok")

    def test_guarded_child_omits_exact_and_generic_credential_names(
        self,
    ) -> None:
        self._verification_module()
        generic_credential_names = (
            "OTHERWISE_UNLISTED_API_KEY",
            "OTHERWISE_UNLISTED_ACCESS_TOKEN",
            "OTHERWISE_UNLISTED_AUTH_TOKEN",
            "OTHERWISE_UNLISTED_SECRET",
            "OTHERWISE_UNLISTED_PASSWORD",
        )
        credential_names = (
            *self.PROVIDER_ENVIRONMENT_EXACT_NAMES,
            *generic_credential_names,
        )
        synthetic_parent_environment = {
            name: f"synthetic-value-{index}"
            for index, name in enumerate(credential_names)
        }
        expected_names_json = json.dumps(list(credential_names))
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-credentials-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            completed, removed_names = self._run_guarded_child(
                project_root,
                f"""
                import json
                import os

                credential_names = json.loads({expected_names_json!r})
                present_names = [
                    name for name in credential_names if name in os.environ
                ]
                assert present_names == [], present_names
                print("guarded-credentials-ok")
                """,
                extra_parent_environment=synthetic_parent_environment,
            )
            self.assertEqual(
                completed.stdout.strip(),
                "guarded-credentials-ok",
            )
            self.assertTrue(set(credential_names).issubset(removed_names))

    def test_guard_rejects_unlisted_subprocesses_and_process_bypasses(
        self,
    ) -> None:
        self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-process-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            completed, _ = self._run_guarded_child(
                project_root,
                """
                import os
                import subprocess
                from pathlib import Path

                project_root = Path(
                    os.environ["EMOTION_STATE_PHASE_A_PROJECT_ROOT"]
                )
                missing_command = (
                    project_root / "public" / "not-allowlisted-command"
                )

                def expect_denied(label, operation):
                    try:
                        operation()
                    except PermissionError:
                        return
                    except BaseException as exc:
                        raise AssertionError(
                            f"{label} raised {type(exc).__name__}, "
                            "not PermissionError"
                        ) from exc
                    raise AssertionError(f"{label} was not denied")

                expect_denied(
                    "subprocess.Popen",
                    lambda: subprocess.Popen([str(missing_command)]),
                )
                expect_denied(
                    "subprocess.run",
                    lambda: subprocess.run(
                        [str(missing_command)],
                        check=False,
                    ),
                )
                for name in ("system", "popen"):
                    operation = getattr(os, name)
                    expect_denied(name, lambda operation=operation: operation())

                bypass_names = sorted(
                    name
                    for name in dir(os)
                    if name.startswith(("spawn", "exec"))
                    and callable(getattr(os, name))
                )
                assert bypass_names
                if hasattr(os, "startfile"):
                    bypass_names.append("startfile")
                for name in bypass_names:
                    operation = getattr(os, name)
                    expect_denied(name, lambda operation=operation: operation())
                print("guarded-process-ok")
                """,
            )
            self.assertEqual(completed.stdout.strip(), "guarded-process-ok")

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_rule_schema_accepts_empty_and_recursive_arrays(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-rule-schema-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            self._write_bytes(
                project_root,
                "scripts/schema_probe.py",
                (
                    "import subprocess\n"
                    "try:\n"
                    "    subprocess.run(['unlisted-schema-probe'], check=False)\n"
                    "except PermissionError:\n"
                    "    print('schema-accepted')\n"
                    "else:\n"
                    "    raise AssertionError('guard did not activate')\n"
                ).encode("utf-8"),
            )
            self._write_bytes(
                project_root,
                "scripts/child.py",
                b'print("child")\n',
            )
            child_rule = {
                "kind": "python_target",
                "caller": "scripts/child.py",
                "target": "scripts/child.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            recursive_rule = {
                "kind": "python_target",
                "caller": "scripts/schema_probe.py",
                "target": "scripts/child.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [child_rule],
            }
            for case_name, rules in (
                ("empty", []),
                ("recursive", [recursive_rule]),
            ):
                with self.subTest(case=case_name):
                    completed = self._run_guarded_target(
                        project_root,
                        "scripts/schema_probe.py",
                        allowed_subprocesses=rules,
                    )
                    self.assertEqual(
                        completed.returncode,
                        0,
                        completed.stdout + completed.stderr,
                    )
                    self.assertEqual(
                        completed.stdout.strip(),
                        "schema-accepted",
                    )

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_rule_schema_rejects_malformed_duplicate_and_ambiguous_rules(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-rule-rejections-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            marker_path = project_root / "schema-probe-ran.txt"
            self._write_bytes(
                project_root,
                "scripts/schema_probe.py",
                (
                    "from pathlib import Path\n"
                    f"Path({str(marker_path)!r}).write_text('ran')\n"
                ).encode("utf-8"),
            )
            base_rule = {
                "kind": "python_target",
                "caller": "scripts/schema_probe.py",
                "target": "scripts/child.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            malformed_digest_rule = {
                "kind": "python_inline",
                "caller": "scripts/schema_probe.py",
                "source_sha256": "a" * 64,
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            reviewed_process_digest = (
                "0C84AD0AB699783710EE7729306E5D8763C8013297A26BE3197EA68AE3500A67"
            )
            unreviewed_digest_rule = {
                **malformed_digest_rule,
                "caller": (
                    "scripts/test_emotion_state_001_open_dataset_gate.py"
                ),
                "source_sha256": "A" * 64,
            }
            unreviewed_caller_rule = {
                **malformed_digest_rule,
                "source_sha256": reviewed_process_digest,
            }
            ambiguous_rule = {
                **base_rule,
                "max_uses": 2,
            }
            duplicate_key_json = (
                '[{"kind":"python_target","kind":"python_inline",'
                '"caller":"scripts/schema_probe.py",'
                '"target":"scripts/child.py","args":[],'
                '"cwd_class":"project_root",'
                '"environment_class":"inherit","max_uses":1,'
                '"children":[]}]'
            )
            invalid_cases: tuple[tuple[str, object], ...] = (
                (
                    "unknown_field",
                    [{**base_rule, "unexpected": True}],
                ),
                (
                    "unknown_kind",
                    [{**base_rule, "kind": "wildcard"}],
                ),
                ("duplicate_json_key", duplicate_key_json),
                ("duplicate_rule", [base_rule, deepcopy(base_rule)]),
                ("malformed_digest", [malformed_digest_rule]),
                ("unreviewed_digest", [unreviewed_digest_rule]),
                ("unreviewed_caller", [unreviewed_caller_rule]),
                (
                    "invalid_max_uses_zero",
                    [{**base_rule, "max_uses": 0}],
                ),
                (
                    "invalid_max_uses_boolean",
                    [{**base_rule, "max_uses": True}],
                ),
                ("ambiguous_rules", [base_rule, ambiguous_rule]),
            )
            for case_name, rules in invalid_cases:
                with self.subTest(case=case_name):
                    marker_path.unlink(missing_ok=True)
                    completed = self._run_guarded_target(
                        project_root,
                        "scripts/schema_probe.py",
                        allowed_subprocesses=rules,
                    )
                    self.assertNotEqual(
                        completed.returncode,
                        0,
                        completed.stdout + completed.stderr,
                    )
                    self.assertFalse(marker_path.exists())

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_python_inline_is_digest_exact_and_child_scoped(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-inline-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            test_tree = ast.parse(
                (
                    ROOT
                    / "scripts/test_emotion_state_001_open_dataset_gate.py"
                ).read_text(encoding="utf-8")
            )
            process_test = next(
                node
                for node in ast.walk(test_tree)
                if isinstance(node, ast.FunctionDef)
                and node.name
                == "test_guard_rejects_unlisted_subprocesses_and_process_bypasses"
            )
            guarded_child_call = next(
                node
                for node in ast.walk(process_test)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_run_guarded_child"
            )
            inline_source = textwrap.dedent(
                ast.literal_eval(guarded_child_call.args[1])
            )
            reviewed_digest = (
                "0C84AD0AB699783710EE7729306E5D8763C8013297A26BE3197EA68AE3500A67"
            )
            self.assertEqual(
                hashlib.sha256(
                    inline_source.encode("utf-8")
                ).hexdigest().upper(),
                reviewed_digest,
            )
            child_rule = {
                "kind": "python_target",
                "caller": "scripts/unused-child-caller.py",
                "target": "scripts/unused-child.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            sibling_rule = {
                "kind": "python_target",
                "caller": "scripts/unused-sibling-caller.py",
                "target": "scripts/unused-sibling.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            inline_rule = {
                "kind": "python_inline",
                "caller": (
                    "scripts/test_emotion_state_001_open_dataset_gate.py"
                ),
                "source_sha256": reviewed_digest,
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [child_rule],
            }
            caller_source = (
                "import subprocess\n"
                "import sys\n"
                f"source = {inline_source!r}\n"
                "completed = subprocess.run(\n"
                "    [sys.executable, '-c', source],\n"
                "    capture_output=True,\n"
                "    text=True,\n"
                "    check=False,\n"
                ")\n"
                "assert completed.returncode == 0, completed.stderr\n"
                "assert completed.stdout.strip() == 'guarded-process-ok'\n"
                "print('guarded-process-ok')\n"
                "try:\n"
                "    subprocess.run(\n"
                "        [sys.executable, '-c', source + ' '],\n"
                "        check=False,\n"
                "    )\n"
                "except PermissionError:\n"
                "    print('mutation-denied')\n"
                "else:\n"
                "    raise AssertionError('mutated inline source launched')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/test_emotion_state_001_open_dataset_gate.py",
                caller_source.encode("utf-8"),
            )
            completed = self._run_guarded_target(
                project_root,
                "scripts/test_emotion_state_001_open_dataset_gate.py",
                allowed_subprocesses=[inline_rule, sibling_rule],
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            self.assertEqual(
                completed.stdout.splitlines(),
                [
                    "guarded-process-ok",
                    "mutation-denied",
                ],
            )

            synthetic_caller_source = (
                "import os\n"
                "import subprocess\n"
                "import sys\n"
                "from pathlib import Path\n"
                f"source = {inline_source!r}\n"
                "outer_transaction = Path(os.environ['TEMP'])\n"
                "child_root = outer_transaction / 'synthetic-project'\n"
                "child_transaction = child_root / 'runtime'\n"
                "child_transaction.mkdir(parents=True)\n"
                "def child_environment():\n"
                "    environment = dict(os.environ)\n"
                "    environment['EMOTION_STATE_PHASE_A_PROJECT_ROOT'] = (\n"
                "        str(child_root)\n"
                "    )\n"
                "    for name in ('HOME', 'USERPROFILE', 'TEMP', 'TMP'):\n"
                "        environment[name] = str(child_transaction)\n"
                "    return environment\n"
                "good = subprocess.run(\n"
                "    [sys.executable, '-c', source],\n"
                "    cwd=child_root,\n"
                "    env=child_environment(),\n"
                "    capture_output=True,\n"
                "    text=True,\n"
                "    check=False,\n"
                ")\n"
                "assert good.returncode == 0, good.stderr\n"
                "assert good.stdout.strip() == 'guarded-process-ok'\n"
                "bad_control = child_environment()\n"
                "bad_control['GIT_CONFIG_NOSYSTEM'] = '0'\n"
                "inconsistent_quartet = child_environment()\n"
                "inconsistent_quartet['TMP'] = str(child_root)\n"
                "for label, environment in (\n"
                "    ('mutated-control', bad_control),\n"
                "    ('inconsistent-quartet', inconsistent_quartet),\n"
                "):\n"
                "    try:\n"
                "        subprocess.run(\n"
                "            [sys.executable, '-c', source],\n"
                "            cwd=child_root,\n"
                "            env=environment,\n"
                "            check=False,\n"
                "        )\n"
                "    except PermissionError:\n"
                "        pass\n"
                "    else:\n"
                "        raise AssertionError(label)\n"
                "print('synthetic-anchor-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/test_emotion_state_001_open_dataset_gate.py",
                synthetic_caller_source.encode("utf-8"),
            )
            synthetic_rule = {
                "kind": "python_inline",
                "caller": (
                    "scripts/test_emotion_state_001_open_dataset_gate.py"
                ),
                "source_sha256": reviewed_digest,
                "cwd_class": "transaction_descendant",
                "environment_class": "synthetic_guard",
                "max_uses": 3,
                "children": [],
            }
            synthetic_environment, _removed_names = (
                self._guarded_child_environment(
                    project_root,
                    allowed_subprocesses_json=json.dumps(
                        [synthetic_rule],
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
            )
            synthetic_environment["PYTHONPATH"] = os.pathsep.join((
                str(self.GUARD_SITE_PATH),
                str(project_root),
            ))
            synthetic_completed = subprocess.run(
                [
                    sys.executable,
                    str(
                        project_root
                        / "scripts/test_emotion_state_001_open_dataset_gate.py"
                    ),
                ],
                cwd=project_root,
                env=synthetic_environment,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(
                synthetic_completed.returncode,
                0,
                synthetic_completed.stdout + synthetic_completed.stderr,
            )
            self.assertEqual(
                synthetic_completed.stdout.strip(),
                "synthetic-anchor-ok",
            )

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_python_target_requires_exact_target_args_and_cwd(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-target-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            transaction_root = project_root / "guard-runtime" / "nested"
            child_rule = {
                "kind": "python_target",
                "caller": "scripts/unused-child-caller.py",
                "target": "scripts/unused-child.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            expected_child_rules_json = json.dumps(
                [child_rule],
                sort_keys=True,
                separators=(",", ":"),
            )
            target_path = self._write_bytes(
                project_root,
                "scripts/target.py",
                (
                    "import os\n"
                    "import sys\n"
                    "assert sys.argv[1:] == ['--flag', 'fixture']\n"
                    "assert os.environ[\n"
                    "    'EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON'\n"
                    f"] == {expected_child_rules_json!r}\n"
                    "print('target-launched')\n"
                ).encode("utf-8"),
            )
            caller_source = (
                "import subprocess\n"
                "import sys\n"
                "from pathlib import Path\n"
                f"target = {str(target_path)!r}\n"
                f"transaction = {str(transaction_root)!r}\n"
                "Path(transaction).mkdir(parents=True, exist_ok=True)\n"
                "completed = subprocess.run(\n"
                "    [sys.executable, target, '--flag', 'fixture'],\n"
                "    capture_output=True,\n"
                "    text=True,\n"
                "    check=False,\n"
                ")\n"
                "assert completed.returncode == 0, completed.stderr\n"
                "assert completed.stdout.strip() == 'target-launched'\n"
                "denied = (\n"
                "    ([sys.executable, target, '--flag', 'changed'], None),\n"
                "    ([sys.executable, target, '--flag', 'fixture'], transaction),\n"
                ")\n"
                "for argv, cwd in denied:\n"
                "    try:\n"
                "        subprocess.run(argv, cwd=cwd, check=False)\n"
                "    except PermissionError:\n"
                "        pass\n"
                "    else:\n"
                "        raise AssertionError((argv, cwd))\n"
                "print('target-boundaries-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/target_caller.py",
                caller_source.encode("utf-8"),
            )
            rule = {
                "kind": "python_target",
                "caller": "scripts/target_caller.py",
                "target": "scripts/target.py",
                "args": ["--flag", "fixture"],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [child_rule],
            }
            sibling_rule = {
                "kind": "python_target",
                "caller": "scripts/unused-sibling-caller.py",
                "target": "scripts/unused-sibling.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            completed = self._run_guarded_target(
                project_root,
                "scripts/target_caller.py",
                allowed_subprocesses=[rule, sibling_rule],
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            self.assertEqual(
                completed.stdout.strip(),
                "target-boundaries-ok",
            )

            anchored_controls = {
                "EMOTION_STATE_PHASE_A_GUARD_POLICY": str(self.POLICY_PATH),
                "EMOTION_STATE_PHASE_A_PROJECT_ROOT": str(project_root),
                "GIT_CONFIG_GLOBAL": "NUL",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONIOENCODING": "utf-8",
                "PYTHONPATH": os.pathsep.join((
                    str(self.GUARD_SITE_PATH),
                    str(ROOT),
                )),
                "PYTHONUTF8": "1",
            }
            anchored_transaction = str(project_root / "guard-runtime")
            expected_inherit_environment = {
                **anchored_controls,
                "HOME": anchored_transaction,
                "TEMP": anchored_transaction,
                "TMP": anchored_transaction,
                "USERPROFILE": anchored_transaction,
            }
            anchor_target_path = self._write_bytes(
                project_root,
                "scripts/anchor_target.py",
                (
                    "import os\n"
                    f"expected = {expected_inherit_environment!r}\n"
                    "actual = {name: os.environ.get(name) for name in expected}\n"
                    "assert actual == expected, (actual, expected)\n"
                    "print('anchored-environment-ok')\n"
                ).encode("utf-8"),
            )
            inherit_caller_source = (
                "import os\n"
                "import subprocess\n"
                "import sys\n"
                f"target = {str(anchor_target_path)!r}\n"
                f"control_names = {tuple(anchored_controls)!r}\n"
                "for name in control_names:\n"
                "    os.environ.pop(name, None)\n"
                "completed = subprocess.run(\n"
                "    [sys.executable, target],\n"
                "    capture_output=True,\n"
                "    text=True,\n"
                "    check=False,\n"
                ")\n"
                "assert completed.returncode == 0, completed.stderr\n"
                "assert completed.stdout.strip() == 'anchored-environment-ok'\n"
                "print('inherit-anchor-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/inherit_anchor_caller.py",
                inherit_caller_source.encode("utf-8"),
            )
            inherit_anchor_rule = {
                "kind": "python_target",
                "caller": "scripts/inherit_anchor_caller.py",
                "target": "scripts/anchor_target.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            inherit_completed = self._run_guarded_target(
                project_root,
                "scripts/inherit_anchor_caller.py",
                allowed_subprocesses=[inherit_anchor_rule],
            )
            self.assertEqual(
                inherit_completed.returncode,
                0,
                inherit_completed.stdout + inherit_completed.stderr,
            )
            self.assertEqual(
                inherit_completed.stdout.strip(),
                "inherit-anchor-ok",
            )

            guarded_target_path = self._write_bytes(
                project_root,
                "scripts/guarded_anchor_target.py",
                (
                    "import os\n"
                    "from pathlib import Path\n"
                    f"expected = {anchored_controls!r}\n"
                    "actual = {name: os.environ.get(name) for name in expected}\n"
                    "assert actual == expected, (actual, expected)\n"
                    "quartet = {\n"
                    "    os.environ[name]\n"
                    "    for name in ('HOME', 'USERPROFILE', 'TEMP', 'TMP')\n"
                    "}\n"
                    "assert len(quartet) == 1, quartet\n"
                    "transaction = Path(quartet.pop()).resolve(strict=True)\n"
                    f"root = Path({str(project_root / 'guard-runtime')!r}).resolve()\n"
                    "assert transaction.is_relative_to(root)\n"
                    "assert transaction != root\n"
                    "print('fresh-guarded-child-ok')\n"
                ).encode("utf-8"),
            )
            guarded_caller_source = (
                "import os\n"
                "import subprocess\n"
                "import sys\n"
                "from pathlib import Path\n"
                f"target = {str(guarded_target_path)!r}\n"
                f"project_root = Path({str(project_root)!r})\n"
                "fresh = project_root / 'guard-runtime' / 'fresh'\n"
                "fresh.mkdir(parents=True)\n"
                "good = dict(os.environ)\n"
                "for name in ('HOME', 'USERPROFILE', 'TEMP', 'TMP'):\n"
                "    good[name] = str(fresh)\n"
                "completed = subprocess.run(\n"
                "    [sys.executable, target],\n"
                "    env=good,\n"
                "    capture_output=True,\n"
                "    text=True,\n"
                "    check=False,\n"
                ")\n"
                "assert completed.returncode == 0, completed.stderr\n"
                "assert completed.stdout.strip() == 'fresh-guarded-child-ok'\n"
                "bad = dict(good)\n"
                "bad['GIT_CONFIG_NOSYSTEM'] = '0'\n"
                "try:\n"
                "    subprocess.run(\n"
                "        [sys.executable, target], env=bad, check=False\n"
                "    )\n"
                "except PermissionError:\n"
                "    pass\n"
                "else:\n"
                "    raise AssertionError('mutated guarded-child control launched')\n"
                "print('guarded-child-anchor-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/guarded_anchor_caller.py",
                guarded_caller_source.encode("utf-8"),
            )
            guarded_anchor_rule = {
                "kind": "python_target",
                "caller": "scripts/guarded_anchor_caller.py",
                "target": "scripts/guarded_anchor_target.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "guarded_child",
                "max_uses": 2,
                "children": [],
            }
            guarded_completed = self._run_guarded_target(
                project_root,
                "scripts/guarded_anchor_caller.py",
                allowed_subprocesses=[guarded_anchor_rule],
            )
            self.assertEqual(
                guarded_completed.returncode,
                0,
                guarded_completed.stdout + guarded_completed.stderr,
            )
            self.assertEqual(
                guarded_completed.stdout.strip(),
                "guarded-child-anchor-ok",
            )

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_git_families_are_transaction_scoped_and_prefix_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-git-families-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            fixture_root = (
                project_root / "guard-runtime" / "fixture-repository"
            )
            fixture_root.mkdir(parents=True)
            outside_directory = project_root / "outside-git-operand"
            outside_directory.mkdir()
            (outside_directory / "outside.txt").write_text(
                "outside\n",
                encoding="utf-8",
            )
            escape_directory = fixture_root / "escape"
            link_supported = self._create_directory_link(
                escape_directory,
                outside_directory,
            )
            nested_links: list[Path] = []
            for bundle_name in ("bundle-add", "bundle-add-force"):
                bundle_directory = fixture_root / bundle_name
                bundle_directory.mkdir()
                (bundle_directory / "local.txt").write_text(
                    "local\n",
                    encoding="utf-8",
                )
                nested_link = bundle_directory / "nested"
                if self._create_directory_link(
                    nested_link,
                    outside_directory,
                ):
                    nested_links.append(nested_link)
            caller_source = r'''
import os
import subprocess
from pathlib import Path

project_root = Path(os.environ["EMOTION_STATE_PHASE_A_PROJECT_ROOT"])
fixture_root = Path(os.environ["TEMP"]) / "fixture-repository"
fixture_root.mkdir(exist_ok=True)

def run(argv):
    return subprocess.run(
        argv,
        cwd=fixture_root,
        capture_output=True,
        text=True,
        check=False,
    )

for argv in (
    ["git", "init"],
    ["git", "config", "user.email", "fixture@example.invalid"],
    ["git", "config", "user.name", "Fixture Author"],
    ["git", "config", "core.autocrlf", "false"],
    ["git", "config", "core.filemode", "false"],
):
    completed = run(argv)
    assert completed.returncode == 0, completed.stderr
(fixture_root / "tracked.txt").write_text("fixture\n", encoding="utf-8")
(fixture_root / "deleted.txt").write_text("delete\n", encoding="utf-8")
assert run([
    "git",
    "add",
    "--",
    "tracked.txt",
    "deleted.txt",
]).returncode == 0
assert run(["git", "commit", "-m", "baseline"]).returncode == 0
(fixture_root / "deleted.txt").unlink()
assert run(["git", "add", "--", "deleted.txt"]).returncode == 0
assert run(["git", "commit", "-m", "rename and delete"]).returncode == 0
head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
assert len(head) == 40
verified = run([
    "git",
    "--no-lazy-fetch",
    "rev-parse",
    "--verify",
    "HEAD^{commit}",
])
assert verified.returncode == 0, verified.stderr
assert verified.stdout.strip() == head

guard_violations = []
try:
    missing_parent = run([
        "git",
        "add",
        "--",
        "missing-parent/missing.txt",
    ])
except PermissionError:
    pass
else:
    guard_violations.append((
        "missing-parent",
        missing_parent.returncode,
    ))
(fixture_root / "a.txt").write_text("a\n", encoding="utf-8")
(fixture_root / "b.txt").write_text("b\n", encoding="utf-8")
pathspec_attempts = (
    ["git", "add", "--", "*"],
    ["git", "add", "-f", "--", "bundle-*"],
    ["git", "add", "--", "?.txt"],
    ["git", "add", "--", "[ab].txt"],
    ["git", "add", "--", ":tracked.txt"],
)
pathspec_launches = []
for argv in pathspec_attempts:
    try:
        completed = run(argv)
    except PermissionError:
        pass
    else:
        pathspec_launches.append((argv, completed.returncode))
        guard_violations.append(("pathspec", argv, completed.returncode))
assert len(pathspec_attempts) == 5
directory_launches = []
directory_attempt_count = 0
for argv in (
    ["git", "add", "--", "bundle-add"],
    ["git", "add", "-f", "--", "bundle-add-force"],
):
    directory_attempt_count += 1
    nested_link_present = (
        fixture_root / argv[-1] / "nested"
    ).exists()
    try:
        completed = run(argv)
    except PermissionError:
        pass
    else:
        directory_launches.append((
            argv,
            completed.returncode,
            nested_link_present,
        ))
        guard_violations.append(("directory", argv, completed.returncode))
assert directory_attempt_count == 2
if directory_launches or pathspec_launches:
    staged = run([
        "git",
        "--no-lazy-fetch",
        "diff",
        "--cached",
        "--name-status",
        "-z",
        "--find-renames",
        head,
        "--",
    ])
    assert staged.returncode == 0, staged.stderr
    if any(
        nested_link_present
        for _argv, _returncode, nested_link_present in directory_launches
    ):
        assert "outside.txt" in staged.stdout, staged.stdout
if guard_violations:
    raise AssertionError(("unsafe add reached native Git", guard_violations))

denied = (
    ["git", "rev-parse", "--verify", "HEAD^{commit}"],
    ["git", "--no-lazy-fetch", "--no-lazy-fetch", "rev-parse", "HEAD"],
    ["git", "rev-parse", "--no-lazy-fetch", "HEAD"],
    ["git", "--no-lazy-fetch", "rev-parse", "HEAD"],
)
for argv in denied:
    try:
        run(argv)
    except PermissionError:
        pass
    else:
        raise AssertionError(argv)
try:
    subprocess.run(["git", "init"], cwd=project_root, check=False)
except PermissionError:
    pass
else:
    raise AssertionError("mutable fixture Git launched at project root")
escape_directory = fixture_root / "escape"
if escape_directory.exists():
    try:
        run(["git", "add", "--", "escape/outside.txt"])
    except PermissionError:
        pass
    else:
        raise AssertionError("Git operand symlink traversal launched")
print("git-families-ok")
'''
            self._write_bytes(
                project_root,
                "scripts/git_caller.py",
                textwrap.dedent(caller_source).encode("utf-8"),
            )
            rules = [
                {
                    "kind": "git",
                    "caller": "scripts/git_caller.py",
                    "matcher_id": "transaction_fixture",
                    "cwd_class": "transaction_descendant",
                    "children": [],
                },
                {
                    "kind": "git",
                    "caller": "scripts/git_caller.py",
                    "matcher_id": "transaction_verification",
                    "cwd_class": "transaction_descendant",
                    "children": [],
                },
            ]
            try:
                completed = self._run_guarded_target(
                    project_root,
                    "scripts/git_caller.py",
                    allowed_subprocesses=rules,
                )
            finally:
                if link_supported:
                    self._remove_directory_link(escape_directory)
                for nested_link in nested_links:
                    self._remove_directory_link(nested_link)
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            self.assertEqual(completed.stdout.strip(), "git-families-ok")

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_project_root_sentinel_git_is_value_bound(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-sentinel-git-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            head_commit = self._commit_private_gitignore_sentinel(project_root)
            tree_line = self._git(
                project_root,
                "ls-tree",
                head_commit,
                "--",
                "data/private/.gitignore",
            ).stdout.strip()
            sentinel_object_id = tree_line.split()[2]
            self.assertRegex(sentinel_object_id, r"^[0-9a-f]{40,64}$")
            caller_source = (
                "import subprocess\n"
                f"head = {head_commit!r}\n"
                f"object_id = {sentinel_object_id!r}\n"
                "commands = (\n"
                "    ['git', '--no-lazy-fetch', 'rev-parse', '--verify', "
                "'HEAD^{commit}'],\n"
                "    ['git', '--no-lazy-fetch', 'ls-tree', '-z', head, '--', "
                "':(literal)data/private/.gitignore'],\n"
                "    ['git', '--no-lazy-fetch', 'cat-file', 'blob', object_id],\n"
                ")\n"
                "for argv in commands:\n"
                "    completed = subprocess.run(\n"
                "        argv,\n"
                "        capture_output=True,\n"
                "        check=False,\n"
                "    )\n"
                "    assert completed.returncode == 0, completed.stderr\n"
                "denied = (\n"
                "    ['git', '--no-lazy-fetch', 'ls-tree', '-z', '0' * 40, "
                "'--', ':(literal)data/private/.gitignore'],\n"
                "    ['git', '--no-lazy-fetch', 'ls-tree', '-z', head, '--', "
                "':(literal)data/private-restricted/.gitignore'],\n"
                "    ['git', '--no-lazy-fetch', 'cat-file', 'blob', '0' * 40],\n"
                ")\n"
                "for argv in denied:\n"
                "    try:\n"
                "        subprocess.run(argv, check=False)\n"
                "    except PermissionError:\n"
                "        pass\n"
                "    else:\n"
                "        raise AssertionError(argv)\n"
                "print('sentinel-git-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/emotion_state_phase_a_verification_evidence.py",
                caller_source.encode("utf-8"),
            )
            rule = {
                "kind": "git",
                "caller": (
                    "scripts/emotion_state_phase_a_verification_evidence.py"
                ),
                "matcher_id": "project_root_sentinel",
                "cwd_class": "project_root",
                "captured_head": head_commit,
                "sentinel_object_id": sentinel_object_id,
                "children": [],
            }
            completed = self._run_guarded_target(
                project_root,
                "scripts/emotion_state_phase_a_verification_evidence.py",
                allowed_subprocesses=[rule],
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            self.assertEqual(completed.stdout.strip(), "sentinel-git-ok")

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guard_rejects_process_options_escapes_and_exceeded_uses(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-process-options-",
        ) as temporary_directory:
            temporary_root = Path(temporary_directory)
            project_root = temporary_root / "project"
            project_root.mkdir()
            target_path = self._write_bytes(
                project_root,
                "scripts/target.py",
                b'print("target")\n',
            )
            outside_marker = temporary_root / "outside-ran.txt"
            outside_path = self._write_bytes(
                temporary_root,
                "outside.py",
                (
                    "from pathlib import Path\n"
                    f"Path({str(outside_marker)!r}).write_text('ran')\n"
                ).encode("utf-8"),
            )
            escape_relative_path: str | None = None
            escape_path = project_root / "scripts" / "escape.py"
            try:
                escape_path.symlink_to(outside_path)
            except OSError as exc:
                if not (
                    os.name == "nt"
                    and getattr(exc, "winerror", None) == 1314
                ):
                    raise
            else:
                escape_relative_path = "scripts/escape.py"

            caller_source = (
                "import os\n"
                "import subprocess\n"
                "import sys\n"
                "from pathlib import Path\n"
                f"target = {str(target_path)!r}\n"
                f"outside = {str(outside_path)!r}\n"
                "completed = subprocess.run(\n"
                "    [sys.executable, target],\n"
                "    capture_output=True,\n"
                "    text=True,\n"
                "    check=False,\n"
                ")\n"
                "assert completed.returncode == 0, completed.stderr\n"
                "assert completed.stdout.strip() == 'target'\n"
                "attempts = [\n"
                "    lambda: subprocess.run([sys.executable, target], check=False),\n"
                "    lambda: subprocess.run(sys.executable, check=False),\n"
                "    lambda: subprocess.run(\n"
                "        f'{sys.executable} {target}', shell=True, check=False\n"
                "    ),\n"
                "    lambda: subprocess.run(\n"
                "        [sys.executable, target],\n"
                "        executable=sys.executable,\n"
                "        check=False,\n"
                "    ),\n"
                "    lambda: subprocess.run(\n"
                "        [sys.executable, target], pass_fds=(1,), check=False\n"
                "    ),\n"
                "    lambda: subprocess.run(\n"
                "        [sys.executable, target],\n"
                "        preexec_fn=lambda: None,\n"
                "        check=False,\n"
                "    ),\n"
                "    lambda: subprocess.run([sys.executable, outside], check=False),\n"
                "]\n"
                "if os.name == 'nt':\n"
                "    startupinfo = subprocess.STARTUPINFO()\n"
                "    startupinfo.lpAttributeList = {'handle_list': [1]}\n"
                "    attempts.append(\n"
                "        lambda: subprocess.run(\n"
                "            [sys.executable, target],\n"
                "            startupinfo=startupinfo,\n"
                "            check=False,\n"
                "        )\n"
                "    )\n"
                f"escape = {str(escape_path) if escape_relative_path else ''!r}\n"
                "if escape:\n"
                "    attempts.append(\n"
                "        lambda: subprocess.run([sys.executable, escape], check=False)\n"
                "    )\n"
                "try:\n"
                "    cwd_escape = Path(os.environ['TEMP']) / 'cwd-escape'\n"
                f"    cwd_escape.symlink_to({str(temporary_root)!r}, target_is_directory=True)\n"
                "except OSError:\n"
                "    pass\n"
                "else:\n"
                "    attempts.append(\n"
                "        lambda: subprocess.run(\n"
                "            [sys.executable, target],\n"
                "            cwd=cwd_escape,\n"
                "            check=False,\n"
                "        )\n"
                "    )\n"
                "for operation in attempts:\n"
                "    try:\n"
                "        operation()\n"
                "    except PermissionError:\n"
                "        pass\n"
                "    else:\n"
                "        raise AssertionError(operation)\n"
                "print('process-options-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/process_options_caller.py",
                caller_source.encode("utf-8"),
            )
            rules = [
                {
                    "kind": "python_target",
                    "caller": "scripts/process_options_caller.py",
                    "target": "scripts/target.py",
                    "args": [],
                    "cwd_class": "project_root",
                    "environment_class": "inherit",
                    "max_uses": 1,
                    "children": [],
                },
                {
                    "kind": "python_target",
                    "caller": "scripts/process_options_caller.py",
                    "target": "scripts/target.py",
                    "args": [],
                    "cwd_class": "transaction_descendant",
                    "environment_class": "inherit",
                    "max_uses": 1,
                    "children": [],
                },
            ]
            if escape_relative_path is not None:
                rules.append({
                    "kind": "python_target",
                    "caller": "scripts/process_options_caller.py",
                    "target": escape_relative_path,
                    "args": [],
                    "cwd_class": "project_root",
                    "environment_class": "inherit",
                    "max_uses": 1,
                    "children": [],
                })
            completed = self._run_guarded_target(
                project_root,
                "scripts/process_options_caller.py",
                allowed_subprocesses=rules,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            self.assertEqual(completed.stdout.strip(), "process-options-ok")
            self.assertFalse(outside_marker.exists())

            concurrent_target = self._write_bytes(
                project_root,
                "scripts/concurrent_target.py",
                b'print("concurrent-target")\n',
            )
            concurrent_caller_source = (
                "import sitecustomize\n"
                "import subprocess\n"
                "import sys\n"
                "import threading\n"
                "import time\n"
                f"target = {str(concurrent_target)!r}\n"
                "original_scrub = sitecustomize._scrub_child_environment\n"
                "def slow_scrub(*args, **kwargs):\n"
                "    result = original_scrub(*args, **kwargs)\n"
                "    time.sleep(0.2)\n"
                "    return result\n"
                "sitecustomize._scrub_child_environment = slow_scrub\n"
                "start = threading.Barrier(3)\n"
                "results = []\n"
                "def launch():\n"
                "    start.wait()\n"
                "    try:\n"
                "        completed = subprocess.run(\n"
                "            [sys.executable, target],\n"
                "            capture_output=True,\n"
                "            text=True,\n"
                "            check=False,\n"
                "        )\n"
                "    except PermissionError:\n"
                "        results.append('denied')\n"
                "    else:\n"
                "        assert completed.returncode == 0, completed.stderr\n"
                "        results.append('launched')\n"
                "threads = [threading.Thread(target=launch) for _ in range(2)]\n"
                "for thread in threads:\n"
                "    thread.start()\n"
                "start.wait()\n"
                "for thread in threads:\n"
                "    thread.join(timeout=5)\n"
                "assert all(not thread.is_alive() for thread in threads)\n"
                "assert sorted(results) == ['denied', 'launched'], results\n"
                "print('concurrent-max-uses-ok')\n"
            )
            self._write_bytes(
                project_root,
                "scripts/concurrent_caller.py",
                concurrent_caller_source.encode("utf-8"),
            )
            concurrent_rule = {
                "kind": "python_target",
                "caller": "scripts/concurrent_caller.py",
                "target": "scripts/concurrent_target.py",
                "args": [],
                "cwd_class": "project_root",
                "environment_class": "inherit",
                "max_uses": 1,
                "children": [],
            }
            concurrent_completed = self._run_guarded_target(
                project_root,
                "scripts/concurrent_caller.py",
                allowed_subprocesses=[concurrent_rule],
            )
            self.assertEqual(
                concurrent_completed.returncode,
                0,
                concurrent_completed.stdout + concurrent_completed.stderr,
            )
            self.assertEqual(
                concurrent_completed.stdout.strip(),
                "concurrent-max-uses-ok",
            )

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_guarded_launcher_preserves_canonical_argv_and_safety_prefixes(
        self,
    ) -> None:
        verification = self._verification_module()
        from scripts.emotion_state_phase_a_verification_evidence import (
            run_guarded_command,
        )

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-guard-launcher-",
        ) as temporary_directory:
            project_root = Path(temporary_directory)
            canonical_policy_bytes = self.POLICY_PATH.read_bytes()

            def prepare_launcher_root(
                name: str,
                policy_bytes: bytes,
            ) -> Path:
                root = project_root / name
                self._write_bytes(
                    root,
                    "research/sources/emotion_state/"
                    "phase_a_verification_guard_policy.json",
                    policy_bytes,
                )
                self._write_bytes(
                    root,
                    "scripts/emotion_state_phase_a_guard_site/"
                    "sitecustomize.py",
                    (
                        self.GUARD_SITE_PATH / "sitecustomize.py"
                    ).read_bytes(),
                )
                self._write_bytes(
                    root,
                    "scripts/validate_context_reading_policy.py",
                    b'print("context-policy")\n',
                )
                return root

            policy_drift_cases = (
                (
                    "leading-whitespace",
                    b" " + canonical_policy_bytes,
                    "context-policy-validator",
                    {},
                ),
                (
                    "crlf-native-git",
                    canonical_policy_bytes.replace(b"\n", b"\r\n"),
                    "git-diff-check",
                    {
                        "baseline_commit": "0" * 40,
                        "head_commit": "1" * 40,
                    },
                ),
            )
            for (
                case_name,
                drifted_policy_bytes,
                command_id,
                substitutions,
            ) in policy_drift_cases:
                with self.subTest(policy_drift=case_name):
                    drift_root = prepare_launcher_root(
                        f"policy-{case_name}",
                        drifted_policy_bytes,
                    )
                    with (
                        mock.patch.object(
                            verification,
                            "_command_subprocess_rules",
                            side_effect=AssertionError(
                                "rules generated before policy rejection"
                            ),
                        ),
                        mock.patch.object(
                            verification.subprocess,
                            "run",
                            side_effect=AssertionError(
                                "process launched before policy rejection"
                            ),
                        ),
                    ):
                        with self.assertRaisesRegex(ValueError, "policy"):
                            run_guarded_command(
                                command_id,
                                drift_root,
                                substitutions,
                            )
                    self.assertFalse(
                        (
                            drift_root
                            / ".tmp/emotion-state-001-phase-a-publication"
                        ).exists()
                    )

            linked_policy_root = project_root / "linked-policy"
            linked_policy_parent = (
                linked_policy_root / "research/sources/emotion_state"
            )
            linked_policy_parent.parent.mkdir(parents=True)
            linked_policy_supported = self._create_directory_link(
                linked_policy_parent,
                self.POLICY_PATH.parent,
            )
            if linked_policy_supported:
                with self.subTest(policy_path="linked-parent"):
                    self._write_bytes(
                        linked_policy_root,
                        "scripts/emotion_state_phase_a_guard_site/"
                        "sitecustomize.py",
                        (
                            self.GUARD_SITE_PATH / "sitecustomize.py"
                        ).read_bytes(),
                    )
                    try:
                        with (
                            mock.patch.object(
                                verification,
                                "_command_subprocess_rules",
                                side_effect=AssertionError(
                                    "rules generated through linked policy path"
                                ),
                            ),
                            mock.patch.object(
                                verification.subprocess,
                                "run",
                                side_effect=AssertionError(
                                    "process launched through linked policy path"
                                ),
                            ),
                        ):
                            with self.assertRaisesRegex(ValueError, "policy"):
                                run_guarded_command(
                                    "context-policy-validator",
                                    linked_policy_root,
                                    {},
                                )
                    finally:
                        self._remove_directory_link(linked_policy_parent)
                    self.assertFalse(
                        (
                            linked_policy_root
                            / ".tmp/emotion-state-001-phase-a-publication"
                        ).exists()
                    )

            missing_site_root = project_root / "missing-site"
            missing_site_policy_path = (
                missing_site_root
                / "research/sources/emotion_state/"
                "phase_a_verification_guard_policy.json"
            )
            missing_site_policy_path.parent.mkdir(parents=True)
            missing_site_policy_path.write_bytes(self.POLICY_PATH.read_bytes())
            with self.assertRaisesRegex(ValueError, "guard site"):
                run_guarded_command(
                    "context-policy-validator",
                    missing_site_root,
                    {},
                )
            self.assertFalse(
                (
                    missing_site_root
                    / ".tmp/emotion-state-001-phase-a-publication"
                ).exists()
            )

            recovery_link_root = prepare_launcher_root(
                "linked-recovery",
                canonical_policy_bytes,
            )
            recovery_outside = project_root / "recovery-outside"
            recovery_outside.mkdir()
            recovery_marker = recovery_outside / "keep.txt"
            recovery_marker.write_text("keep", encoding="utf-8")
            recovery_link = (
                recovery_link_root
                / ".tmp/emotion-state-001-phase-a-publication"
            )
            recovery_link.parent.mkdir(parents=True)
            recovery_link_supported = self._create_directory_link(
                recovery_link,
                recovery_outside,
            )
            if recovery_link_supported:
                with self.subTest(recovery_root="linked"):
                    try:
                        with self.assertRaisesRegex(
                            ValueError,
                            "recovery|transaction",
                        ):
                            run_guarded_command(
                                "context-policy-validator",
                                recovery_link_root,
                                {},
                            )
                    finally:
                        self._remove_directory_link(recovery_link)
                    self.assertEqual(
                        recovery_marker.read_text(encoding="utf-8"),
                        "keep",
                    )

            replacement_root = project_root / "replacement-transaction"
            replacement_recovery = (
                replacement_root
                / ".tmp/emotion-state-001-phase-a-publication"
            )
            replacement_recovery.mkdir(parents=True)
            replacement_outside = project_root / "replacement-outside"
            replacement_outside.mkdir()
            replacement_marker = replacement_outside / "keep.txt"
            replacement_marker.write_text("keep", encoding="utf-8")
            replacement_link: Path | None = None
            with self.subTest(transaction_cleanup="replaced-link"):
                try:
                    with mock.patch.object(
                        verification.shutil,
                        "rmtree",
                        side_effect=AssertionError(
                            "recursive cleanup called on replaced transaction"
                        ),
                    ):
                        with self.assertRaisesRegex(ValueError, "transaction"):
                            with (
                                verification
                                ._fresh_guarded_transaction_directory(
                                    replacement_recovery
                                )
                            ) as transaction_path:
                                transaction_path.rmdir()
                                self.assertTrue(
                                    self._create_directory_link(
                                        transaction_path,
                                        replacement_outside,
                                    )
                                )
                                replacement_link = transaction_path
                finally:
                    if replacement_link is not None and (
                        replacement_link.exists()
                        or replacement_link.is_symlink()
                    ):
                        self._remove_directory_link(replacement_link)
                self.assertEqual(
                    replacement_marker.read_text(encoding="utf-8"),
                    "keep",
                )

            policy_path = (
                project_root
                / "research/sources/emotion_state/"
                "phase_a_verification_guard_policy.json"
            )
            policy_path.parent.mkdir(parents=True)
            policy_path.write_bytes(self.POLICY_PATH.read_bytes())
            self._write_bytes(
                project_root,
                "scripts/emotion_state_phase_a_guard_site/sitecustomize.py",
                (
                    self.GUARD_SITE_PATH / "sitecustomize.py"
                ).read_bytes(),
            )
            thesis_source = r'''
import subprocess

completed = subprocess.run(
    ["git", "status", "--short", "--untracked-files=all"],
    capture_output=True,
    text=True,
    check=False,
)
assert completed.returncode == 0, completed.stderr
assert completed.args == [
    "git",
    "--no-lazy-fetch",
    "status",
    "--short",
    "--untracked-files=all",
], completed.args
'''
            self._write_bytes(
                project_root,
                "scripts/check_thesis_update_gate.py",
                textwrap.dedent(thesis_source).encode("utf-8"),
            )
            self._initialize_git_repository(project_root)
            self._git(
                project_root,
                "add",
                "--",
                "research/sources/emotion_state/"
                "phase_a_verification_guard_policy.json",
                "scripts/check_thesis_update_gate.py",
            )
            self._git(project_root, "commit", "-m", "baseline")
            head_commit = self._git(
                project_root,
                "rev-parse",
                "HEAD",
            ).stdout.strip()

            thesis_entry = run_guarded_command(
                "thesis-update-validator",
                project_root,
                {},
            )
            self.assertEqual(thesis_entry["exit_status"], 0)
            self.assertEqual(
                thesis_entry["argv"],
                ["python", "scripts/check_thesis_update_gate.py"],
            )
            diff_entry = run_guarded_command(
                "git-diff-check",
                project_root,
                {
                    "baseline_commit": head_commit,
                    "head_commit": head_commit,
                },
            )
            self.assertEqual(diff_entry["exit_status"], 0)
            self.assertEqual(
                diff_entry["argv"],
                [
                    "git",
                    "diff",
                    "--check",
                    f"{head_commit}..{head_commit}",
                ],
            )
            self.assertNotIn("--no-lazy-fetch", diff_entry["argv"])
            module_source = (
                ROOT
                / "scripts/emotion_state_phase_a_verification_evidence.py"
            ).read_text(encoding="utf-8")
            self.assertIn(
                '["git", "--no-lazy-fetch", *canonical_argv[1:]]',
                module_source,
            )

    def _git(
        self,
        root: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            msg=(
                f"git {' '.join(arguments)} failed with "
                f"exit {completed.returncode}\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            ),
        )
        return completed

    def _initialize_git_repository(self, root: Path) -> None:
        self._git(root, "init")
        self._git(root, "config", "user.email", "fixture@example.invalid")
        self._git(root, "config", "user.name", "Fixture Author")
        self._git(root, "config", "core.autocrlf", "false")
        self._git(root, "config", "core.filemode", "false")

    @staticmethod
    def _sha256_bytes(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest().upper()

    @staticmethod
    def _write_bytes(root: Path, relative_path: str, content: bytes) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    @staticmethod
    def _create_directory_link(link: Path, target: Path) -> bool:
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            if not (
                os.name == "nt"
                and getattr(exc, "winerror", None) == 1314
            ):
                raise
            completed = subprocess.run(
                [
                    "cmd",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(link),
                    str(target),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                return False
        return True

    @staticmethod
    def _remove_directory_link(link: Path) -> None:
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            os.rmdir(link)

    def _commit_private_gitignore_sentinel(
        self,
        root: Path,
        *,
        content: bytes = b"*\n!.gitignore\n",
        remove_worktree_directory: bool = False,
    ) -> str:
        self._initialize_git_repository(root)
        self._write_bytes(
            root,
            ".gitignore",
            b"data/private/*\n!data/private/.gitignore\n",
        )
        sentinel_path = self._write_bytes(
            root,
            "data/private/.gitignore",
            content,
        )
        self._git(
            root,
            "add",
            "-f",
            "--",
            ".gitignore",
            "data/private/.gitignore",
        )
        self._git(root, "commit", "-m", "private sentinel fixture")
        head_commit = self._git(root, "rev-parse", "HEAD").stdout.strip()
        if remove_worktree_directory:
            sentinel_path.unlink()
            sentinel_path.parent.rmdir()
        return head_commit

    def test_tracked_private_gitignore_sentinel_is_read_from_exact_head_blob(
        self,
    ) -> None:
        verification = self._verification_module()
        sentinel_bytes = b"*\n!.gitignore\n"
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-private-sentinel-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._commit_private_gitignore_sentinel(
                root,
                content=sentinel_bytes,
                remove_worktree_directory=True,
            )
            self.assertEqual(
                verification.read_tracked_private_gitignore_sentinel(root),
                sentinel_bytes,
            )

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-missing-private-sentinel-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)
            self._write_bytes(root, "tracked.txt", b"tracked fixture\n")
            self._git(root, "add", "--", "tracked.txt")
            self._git(root, "commit", "-m", "missing sentinel fixture")
            with self.assertRaisesRegex(ValueError, "private sentinel"):
                verification.read_tracked_private_gitignore_sentinel(root)

    def test_internal_git_reads_disable_lazy_fetch_for_missing_promisor_blob(
        self,
    ) -> None:
        verification = self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-promisor-sentinel-",
        ) as temporary_directory:
            temporary_root = Path(temporary_directory)
            source_root = temporary_root / "source"
            source_root.mkdir()
            head_commit = self._commit_private_gitignore_sentinel(source_root)
            sentinel_bytes = b"*\n!.gitignore\n"
            sentinel_object_id = hashlib.sha1(
                (
                    b"blob "
                    + str(len(sentinel_bytes)).encode("ascii")
                    + b"\0"
                    + sentinel_bytes
                )
            ).hexdigest()
            source_git_dir = source_root / ".git"
            source_sentinel_object = (
                source_git_dir
                / "objects"
                / sentinel_object_id[:2]
                / sentinel_object_id[2:]
            )
            self.assertTrue(source_sentinel_object.is_file())
            source_config_path = source_git_dir / "config"
            source_config_path.write_text(
                source_config_path.read_text(encoding="utf-8")
                + "\n[uploadpack]\n"
                + "\tallowFilter = true\n"
                + "\tallowAnySHA1InWant = true\n"
                + "\tallowReachableSHA1InWant = true\n",
                encoding="utf-8",
            )

            partial_root = temporary_root / "partial"
            partial_root.mkdir()
            self._initialize_git_repository(partial_root)
            partial_git_dir = partial_root / ".git"
            copied_object_ids = set()
            for source_object in sorted(
                (source_git_dir / "objects").glob("*/*")
            ):
                if (
                    not source_object.is_file()
                    or re.fullmatch(
                        r"[0-9a-f]{2}",
                        source_object.parent.name,
                    )
                    is None
                    or re.fullmatch(
                        r"[0-9a-f]{38}",
                        source_object.name,
                    )
                    is None
                ):
                    continue
                object_id = source_object.parent.name + source_object.name
                if object_id == sentinel_object_id:
                    continue
                destination_object = (
                    partial_git_dir
                    / "objects"
                    / object_id[:2]
                    / object_id[2:]
                )
                destination_object.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                destination_object.write_bytes(source_object.read_bytes())
                copied_object_ids.add(object_id)
            self.assertNotIn(sentinel_object_id, copied_object_ids)

            partial_config = (
                "[core]\n"
                "\trepositoryformatversion = 1\n"
                "\tfilemode = false\n"
                "\tbare = false\n"
                "\tlogallrefupdates = true\n"
                "[extensions]\n"
                "\tpartialClone = origin\n"
                '[remote "origin"]\n'
                f'\turl = "{source_root.as_posix()}"\n'
                "\tpromisor = true\n"
                "\tpartialCloneFilter = blob:none\n"
            )
            (partial_git_dir / "config").write_text(
                partial_config,
                encoding="utf-8",
            )
            (partial_git_dir / "HEAD").write_text(
                "ref: refs/heads/main\n",
                encoding="ascii",
            )
            partial_head_ref = partial_git_dir / "refs" / "heads" / "main"
            partial_head_ref.parent.mkdir(parents=True, exist_ok=True)
            partial_head_ref.write_text(
                head_commit + "\n",
                encoding="ascii",
            )

            with self.assertRaises(ValueError):
                verification._run_git_bytes(
                    partial_root,
                    "cat-file",
                    "blob",
                    sentinel_object_id,
                )
            captured_error: ValueError | None = None
            try:
                verification.read_tracked_private_gitignore_sentinel(
                    partial_root
                )
            except ValueError as exc:
                captured_error = exc
            self.assertIsNotNone(captured_error)
            self.assertEqual(
                str(captured_error),
                "private sentinel Git blob is unavailable",
            )
            with self.assertRaises(ValueError):
                verification._run_git_bytes(
                    partial_root,
                    "cat-file",
                    "blob",
                    sentinel_object_id,
                )

    def test_promisor_fixture_avoids_unreviewed_git_launches(self) -> None:
        tree = ast.parse(
            (
                ROOT
                / "scripts/test_emotion_state_001_open_dataset_gate.py"
            ).read_text(encoding="utf-8")
        )
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name
            == "test_internal_git_reads_disable_lazy_fetch_for_missing_promisor_blob"
        )
        forbidden_launches = []
        evidence_git_probe_shapes = []
        for node in ast.walk(method):
            if not isinstance(node, ast.Call):
                continue
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr == "_git"
            ):
                forbidden_launches.append("self._git")
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr == "run"
            ):
                forbidden_launches.append("subprocess.run")
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "verification"
                and node.func.attr == "_run_git_bytes"
            ):
                evidence_git_probe_shapes.append([
                    argument.id
                    if isinstance(argument, ast.Name)
                    else (
                        argument.value
                        if isinstance(argument, ast.Constant)
                        else None
                    )
                    for argument in node.args
                ])
        forbidden_arguments = {
            node.value
            for node in ast.walk(method)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in {"-c", "clone", "fetch"}
        }
        self.assertEqual(forbidden_launches, [])
        self.assertEqual(forbidden_arguments, set())
        self.assertEqual(
            evidence_git_probe_shapes,
            [
                [
                    "partial_root",
                    "cat-file",
                    "blob",
                    "sentinel_object_id",
                ],
                [
                    "partial_root",
                    "cat-file",
                    "blob",
                    "sentinel_object_id",
                ],
            ],
        )

        verification_tree = ast.parse(
            (
                ROOT
                / "scripts/emotion_state_phase_a_verification_evidence.py"
            ).read_text(encoding="utf-8")
        )
        runner = next(
            node
            for node in verification_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_run_git_bytes"
        )
        subprocess_call = next(
            node
            for node in ast.walk(runner)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr == "run"
        )
        argv_expression = subprocess_call.args[0]
        self.assertIsInstance(argv_expression, ast.List)
        self.assertEqual(
            [
                element.value
                if isinstance(element, ast.Constant)
                else (
                    "*" + element.value.id
                    if isinstance(element, ast.Starred)
                    and isinstance(element.value, ast.Name)
                    else None
                )
                for element in argv_expression.elts
            ],
            ["git", "--no-lazy-fetch", "*arguments"],
        )

    def test_git_inventories_reject_all_private_states_before_byte_reads(
        self,
    ) -> None:
        verification = self._verification_module()
        private_prefixes = ("data/private", "data/private-restricted")
        git_states = ("committed", "staged", "unstaged", "untracked")

        def reject_byte_read(*_args: object, **_kwargs: object) -> None:
            raise AssertionError(
                "private Git path reached byte inventory creation"
            )

        for private_prefix in private_prefixes:
            for git_state in git_states:
                with self.subTest(
                    private_prefix=private_prefix,
                    git_state=git_state,
                ):
                    with tempfile.TemporaryDirectory(
                        prefix="emotion-state-private-inventory-",
                    ) as temporary_directory:
                        root = Path(temporary_directory)
                        self._initialize_git_repository(root)
                        self._write_bytes(root, "tracked.txt", b"baseline\n")
                        self._git(root, "add", "--", "tracked.txt")
                        self._git(root, "commit", "-m", "baseline")
                        baseline_commit = self._git(
                            root,
                            "rev-parse",
                            "HEAD",
                        ).stdout.strip()
                        relative_path = (
                            f"{private_prefix}/{git_state}-fixture.txt"
                        )

                        if git_state == "committed":
                            self._write_bytes(
                                root,
                                relative_path,
                                b"committed private fixture\n",
                            )
                            self._git(
                                root,
                                "add",
                                "-f",
                                "--",
                                relative_path,
                            )
                            self._git(root, "commit", "-m", "private change")
                            head_commit = self._git(
                                root,
                                "rev-parse",
                                "HEAD",
                            ).stdout.strip()
                        elif git_state == "staged":
                            head_commit = baseline_commit
                            self._write_bytes(
                                root,
                                relative_path,
                                b"staged private fixture\n",
                            )
                            self._git(
                                root,
                                "add",
                                "-f",
                                "--",
                                relative_path,
                            )
                        elif git_state == "unstaged":
                            self._write_bytes(
                                root,
                                relative_path,
                                b"tracked private fixture\n",
                            )
                            self._git(
                                root,
                                "add",
                                "-f",
                                "--",
                                relative_path,
                            )
                            self._git(
                                root,
                                "commit",
                                "-m",
                                "tracked private fixture",
                            )
                            head_commit = self._git(
                                root,
                                "rev-parse",
                                "HEAD",
                            ).stdout.strip()
                            baseline_commit = head_commit
                            self._write_bytes(
                                root,
                                relative_path,
                                b"unstaged private fixture\n",
                            )
                        else:
                            head_commit = baseline_commit
                            self._write_bytes(
                                root,
                                relative_path,
                                b"untracked private fixture\n",
                            )

                        with (
                            mock.patch.object(
                                verification,
                                "_tree_file_bytes",
                                side_effect=reject_byte_read,
                            ),
                            mock.patch.object(
                                verification,
                                "_index_file_bytes",
                                side_effect=reject_byte_read,
                            ),
                            mock.patch.object(
                                verification,
                                "_worktree_file_bytes",
                                side_effect=reject_byte_read,
                            ),
                        ):
                            with self.assertRaisesRegex(
                                ValueError,
                                "private data boundary",
                            ):
                                verification.build_git_change_inventories(
                                    root=root,
                                    baseline_commit=baseline_commit,
                                    head_commit=head_commit,
                                )

    def test_private_sentinel_consumers_do_not_probe_worktree_private_paths(
        self,
    ) -> None:
        import scripts.check_project_drift as project_drift
        import scripts.check_setup as check_setup
        import scripts.validate_private_data_boundary as private_boundary

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-private-consumers-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._commit_private_gitignore_sentinel(
                root,
                remove_worktree_directory=True,
            )
            root_absolute = Path(os.path.abspath(root))
            original_methods = {
                name: getattr(Path, name)
                for name in (
                    "exists",
                    "is_dir",
                    "is_file",
                    "iterdir",
                    "lstat",
                    "open",
                    "read_bytes",
                    "read_text",
                    "resolve",
                    "stat",
                )
            }

            def targets_private_path(path: Path) -> bool:
                candidate = Path(os.path.abspath(path))
                try:
                    relative_path = candidate.relative_to(root_absolute).as_posix()
                except ValueError:
                    return False
                return any(
                    relative_path == prefix
                    or relative_path.startswith(prefix + "/")
                    for prefix in (
                        "data/private",
                        "data/private-restricted",
                    )
                )

            def guarded_method(name: str):
                original = original_methods[name]

                def call(path: Path, *args: object, **kwargs: object):
                    if targets_private_path(path):
                        raise AssertionError(
                            f"ordinary private filesystem probe: {name}"
                        )
                    return original(path, *args, **kwargs)

                return call

            patches = [
                mock.patch.object(Path, name, new=guarded_method(name))
                for name in original_methods
            ]
            for patch in patches:
                patch.start()
            try:
                directory_checks = {
                    check["id"]: check
                    for check in check_setup.check_directories(root)
                }
                self.assertEqual(
                    directory_checks["dir.data_private"],
                    {
                        "id": "dir.data_private",
                        "status": "pass",
                        "severity": "required",
                        "message": (
                            "Local-only private call-center data folder exists."
                        ),
                        "path": "data/private",
                    },
                )
                self.assertEqual(
                    directory_checks["dir.data_private_restricted"],
                    {
                        "id": "dir.data_private_restricted",
                        "status": "pass",
                        "severity": "optional",
                        "message": (
                            "Restricted data folder physical presence was not "
                            "checked and is not required for default setup."
                        ),
                        "path": "data/private-restricted",
                    },
                )

                file_checks = {
                    check["id"]: check
                    for check in check_setup.check_files(root)
                }
                self.assertEqual(
                    file_checks["file.data_private_gitignore"],
                    {
                        "id": "file.data_private_gitignore",
                        "status": "pass",
                        "severity": "required",
                        "message": "Private data local ignore rule exists.",
                        "path": "data/private/.gitignore",
                    },
                )
                private_boundary.validate_gitignore(root)
                missing_issues = project_drift.detect_missing_required_files(
                    root
                )
                self.assertNotIn(
                    "data/private/.gitignore",
                    {issue.path for issue in missing_issues},
                )
            finally:
                for patch in reversed(patches):
                    patch.stop()

    def test_private_sentinel_consumers_reject_wrong_tracked_bytes(
        self,
    ) -> None:
        import scripts.check_project_drift as project_drift
        import scripts.check_setup as check_setup
        import scripts.validate_private_data_boundary as private_boundary

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-wrong-private-sentinel-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._commit_private_gitignore_sentinel(
                root,
                content=b"*\n",
                remove_worktree_directory=True,
            )
            directory_checks = {
                check["id"]: check
                for check in check_setup.check_directories(root)
            }
            file_checks = {
                check["id"]: check
                for check in check_setup.check_files(root)
            }
            self.assertEqual(
                directory_checks["dir.data_private"]["status"],
                "fail",
            )
            self.assertEqual(
                file_checks["file.data_private_gitignore"]["status"],
                "fail",
            )
            with self.assertRaises(AssertionError):
                private_boundary.validate_gitignore(root)
            self.assertIn(
                "data/private/.gitignore",
                {
                    issue.path
                    for issue in project_drift.detect_missing_required_files(
                        root
                    )
                },
            )

    def test_setup_report_accepts_explicit_value_free_environment_mapping(
        self,
    ) -> None:
        import scripts.check_setup as check_setup

        environment = {
            "OPENAI_API_KEY": "synthetic-openai-value",
            "CARTESIA_API_KEY": "synthetic-cartesia-value",
            "CARTESIA_VOICE_ID": "synthetic-voice-value",
        }
        environment_report = check_setup.build_environment_report(environment)
        environment_by_name = {
            entry["name"]: entry
            for entry in environment_report
        }
        for name, value in environment.items():
            self.assertTrue(environment_by_name[name]["present"])
            self.assertFalse(environment_by_name[name]["value_logged"])
            self.assertNotIn(value, json.dumps(environment_report))

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-setup-environment-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._commit_private_gitignore_sentinel(
                root,
                remove_worktree_directory=True,
            )
            report = check_setup.build_report(
                root,
                strict=False,
                environment=environment,
            )
        self.assertEqual(report["environment"], environment_report)
        serialized_report = json.dumps(report, sort_keys=True)
        for value in environment.values():
            self.assertNotIn(value, serialized_report)

    def test_setup_and_drift_validators_use_in_process_checker_functions(
        self,
    ) -> None:
        validator_contracts = {
            "scripts/validate_check_setup.py": {
                "required_call": "build_report",
                "forbidden_attribute": "environ",
            },
            "scripts/validate_project_drift_guard.py": {
                "required_call": "build_report",
                "forbidden_attribute": None,
            },
        }
        for relative_path, contract in validator_contracts.items():
            with self.subTest(relative_path=relative_path):
                source = (ROOT / relative_path).read_text(encoding="utf-8")
                tree = ast.parse(source, filename=relative_path)
                imported_names = {
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names
                }
                self.assertNotIn("subprocess", imported_names)
                call_attributes = {
                    node.func.attr
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                }
                self.assertIn(contract["required_call"], call_attributes)
                forbidden_attribute = contract["forbidden_attribute"]
                if forbidden_attribute is not None:
                    self.assertNotIn(
                        forbidden_attribute,
                        {
                            node.attr
                            for node in ast.walk(tree)
                            if isinstance(node, ast.Attribute)
                        },
                    )

    def test_project_drift_excludes_local_superpowers_sdd_scratch(
        self,
    ) -> None:
        import scripts.check_project_drift as project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-sdd-scratch-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)
            secret_like_content = (
                "Synthetic credential-shaped example: "
                + "sk-"
                + "SYNTHETIC"
                + ("X" * 24)
                + "\n"
            ).encode("ascii")
            tracked_review_path = self._write_bytes(
                root,
                ".superpowers/sdd/task-4-report.md",
                secret_like_content,
            )
            exact_scratch_paths = (
                ".superpowers/sdd/task"
                + "-4-targeted-correction-brief.md",
                ".superpowers/sdd/task"
                + "-6-c4-validator-refactor-brief.md",
                ".superpowers/sdd/open-dataset-task"
                + "-6-report.md",
            )
            for relative_path in exact_scratch_paths:
                self._write_bytes(
                    root,
                    relative_path,
                    secret_like_content,
                )
            unrelated_local_path = self._write_bytes(
                root,
                ".superpowers/sdd/unrelated-local.md",
                secret_like_content,
            )
            self._git(
                root,
                "add",
                "-f",
                "--",
                ".superpowers/sdd/task-4-report.md",
            )
            self._git(root, "commit", "-m", "reviewed SDD fixture")

            scanned_paths = {
                path.relative_to(root).as_posix()
                for path in project_drift.iter_scan_files(root)
            }
            self.assertIn(
                tracked_review_path.relative_to(root).as_posix(),
                scanned_paths,
            )
            self.assertIn(
                unrelated_local_path.relative_to(root).as_posix(),
                scanned_paths,
            )
            for relative_path in exact_scratch_paths:
                self.assertNotIn(relative_path, scanned_paths)

            report = project_drift.build_report(root)
            secret_issue_paths = {
                issue["path"]
                for issue in report["issues"]
                if issue["code"] == "secret_like_value"
            }
            self.assertIn(
                ".superpowers/sdd/task-4-report.md",
                secret_issue_paths,
            )
            self.assertIn(
                ".superpowers/sdd/unrelated-local.md",
                secret_issue_paths,
            )
            for relative_path in exact_scratch_paths:
                self.assertNotIn(relative_path, secret_issue_paths)

    def test_project_drift_scans_current_reviewed_superpowers_paths(
        self,
    ) -> None:
        import scripts.check_project_drift as project_drift

        tracked_review_paths = {
            ".superpowers/sdd/task-4-report.md",
            ".superpowers/sdd/task-4-review-findings.md",
        }
        self.assertTrue(
            all((ROOT / relative_path).is_file() for relative_path in tracked_review_paths)
        )
        scanned_paths = {
            path.relative_to(ROOT).as_posix()
            for path in project_drift.iter_scan_files(ROOT)
        }
        self.assertTrue(tracked_review_paths.issubset(scanned_paths))

    def test_git_inventories_bind_committed_rename_deletion_and_exact_states(
        self,
    ) -> None:
        verification = self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-git-inventory-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)

            renamed_old_bytes = (
                b"\n".join(
                    f"stable-line-{index:02d}: retained rename payload".encode(
                        "ascii"
                    )
                    for index in range(24)
                )
                + b"\n"
            )
            renamed_new_bytes = renamed_old_bytes.replace(
                b"stable-line-12: retained rename payload",
                b"stable-line-12: changed rename payload",
            )
            deleted_bytes = b"baseline-only deleted bytes\n"
            baseline_files = {
                "both.txt": b"baseline both\n",
                "deleted.txt": deleted_bytes,
                "renamed-old.py": renamed_old_bytes,
                "staged.txt": b"baseline staged\n",
                "unstaged.txt": b"baseline unstaged\n",
            }
            for relative_path, content in baseline_files.items():
                self._write_bytes(root, relative_path, content)
            self._git(root, "add", "--", *sorted(baseline_files))
            self._git(root, "commit", "-m", "baseline")
            baseline_commit = self._git(root, "rev-parse", "HEAD").stdout.strip()

            self._git(root, "mv", "--", "renamed-old.py", "renamed-new.py")
            self._write_bytes(root, "renamed-new.py", renamed_new_bytes)
            (root / "deleted.txt").unlink()
            self._git(
                root,
                "add",
                "--",
                "deleted.txt",
                "renamed-new.py",
            )
            self._git(root, "commit", "-m", "rename and delete")
            head_commit = self._git(root, "rev-parse", "HEAD").stdout.strip()
            name_status = self._git(
                root,
                "diff",
                "--name-status",
                "--find-renames",
                f"{baseline_commit}..{head_commit}",
            ).stdout.splitlines()
            self.assertTrue(
                any(
                    line.startswith("R")
                    and line.endswith("\trenamed-old.py\trenamed-new.py")
                    for line in name_status
                ),
                name_status,
            )
            self.assertIn("D\tdeleted.txt", name_status)

            staged_only_bytes = b"staged-only bytes\n"
            staged_both_bytes = b"index bytes for dual-state path\n"
            unstaged_both_bytes = b"worktree bytes for dual-state path\n"
            unstaged_only_bytes = b"unstaged-only bytes\n"
            untracked_bytes = b"untracked bytes\n"
            self._write_bytes(root, "staged.txt", staged_only_bytes)
            self._write_bytes(root, "both.txt", staged_both_bytes)
            self._git(root, "add", "--", "both.txt", "staged.txt")
            self._write_bytes(root, "both.txt", unstaged_both_bytes)
            self._write_bytes(root, "unstaged.txt", unstaged_only_bytes)
            self._write_bytes(root, "untracked.txt", untracked_bytes)

            inventories = verification.build_git_change_inventories(
                root=root,
                baseline_commit=baseline_commit,
                head_commit=head_commit,
            )
            self.assertEqual(
                set(inventories),
                {
                    "committed_change_inventory",
                    "uncommitted_change_inventory",
                },
            )
            self.assertEqual(
                inventories["committed_change_inventory"],
                [
                    {
                        "path": "deleted.txt",
                        "git_mode": "100644",
                        "sha256": self._sha256_bytes(deleted_bytes),
                    },
                    {
                        "path": "renamed-new.py",
                        "git_mode": "100644",
                        "sha256": self._sha256_bytes(renamed_new_bytes),
                    },
                    {
                        "path": "renamed-old.py",
                        "git_mode": "100644",
                        "sha256": self._sha256_bytes(renamed_old_bytes),
                    },
                ],
            )
            expected_uncommitted = [
                {
                    "path": "both.txt",
                    "git_state": "staged",
                    "git_mode": "100644",
                    "sha256": self._sha256_bytes(staged_both_bytes),
                },
                {
                    "path": "both.txt",
                    "git_state": "unstaged",
                    "git_mode": "100644",
                    "sha256": self._sha256_bytes(unstaged_both_bytes),
                },
                {
                    "path": "staged.txt",
                    "git_state": "staged",
                    "git_mode": "100644",
                    "sha256": self._sha256_bytes(staged_only_bytes),
                },
                {
                    "path": "unstaged.txt",
                    "git_state": "unstaged",
                    "git_mode": "100644",
                    "sha256": self._sha256_bytes(unstaged_only_bytes),
                },
                {
                    "path": "untracked.txt",
                    "git_state": "untracked",
                    "git_mode": "100644",
                    "sha256": self._sha256_bytes(untracked_bytes),
                },
            ]
            self.assertEqual(
                inventories["uncommitted_change_inventory"],
                expected_uncommitted,
            )
            self.assertEqual(
                [
                    (entry["path"], entry["git_state"])
                    for entry in inventories["uncommitted_change_inventory"]
                ],
                sorted(
                    (entry["path"], entry["git_state"])
                    for entry in expected_uncommitted
                ),
            )
            self.assertEqual(
                {
                    entry["git_state"]
                    for entry in inventories["uncommitted_change_inventory"]
                },
                {"staged", "unstaged", "untracked"},
            )

    def test_git_inventory_excludes_only_exact_canonical_outputs_and_transaction_tree(
        self,
    ) -> None:
        verification = self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-git-exclusions-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)
            self._write_bytes(root, "tracked.txt", b"baseline\n")
            self._git(root, "add", "--", "tracked.txt")
            self._git(root, "commit", "-m", "baseline")
            head_commit = self._git(root, "rev-parse", "HEAD").stdout.strip()

            exact_exclusions = {
                (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/result.json"
                ): b"generated result\n",
                (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/report.md"
                ): b"generated report\n",
                (
                    ".tmp/emotion-state-001-phase-a-publication/"
                    "transaction/scratch.json"
                ): b"transaction state\n",
            }
            included_near_misses = {
                ".tmp/emotion-state-001-phase-a-publication-neighbor/input.json": (
                    b"neighbor input\n"
                ),
                ".tmp/emotion-state-001-phase-a-publication.txt": (
                    b"near-miss input\n"
                ),
                (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/nested/report.md"
                ): b"nested input\n",
                (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/result.json.backup"
                ): b"backup input\n",
            }
            for relative_path, content in {
                **exact_exclusions,
                **included_near_misses,
            }.items():
                self._write_bytes(root, relative_path, content)

            inventories = verification.build_git_change_inventories(
                root=root,
                baseline_commit=head_commit,
                head_commit=head_commit,
            )
            self.assertEqual(inventories["committed_change_inventory"], [])
            self.assertEqual(
                inventories["uncommitted_change_inventory"],
                [
                    {
                        "path": relative_path,
                        "git_state": "untracked",
                        "git_mode": "100644",
                        "sha256": self._sha256_bytes(content),
                    }
                    for relative_path, content in sorted(
                        included_near_misses.items()
                    )
                ],
            )

    def test_executable_dependency_closure_is_exact_stable_and_byte_bound(
        self,
    ) -> None:
        verification = self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-dependency-closure-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)
            fixture_files = {
                "scripts/runner.py": (
                    b"import subprocess\n"
                    b"import sys\n"
                    b"from support import helper\n"
                    b"from support.constants import TOKEN\n"
                    b"subprocess.run(\n"
                    b"    [sys.executable, \"scripts/worker.py\"],\n"
                    b"    check=True,\n"
                    b")\n"
                ),
                "scripts/worker.py": (
                    b"from support.constants import TOKEN\n"
                    b"print(TOKEN)\n"
                ),
                "support/constants.py": b"TOKEN = \"fixture-token\"\n",
                "support/helper.py": (
                    b"from .constants import TOKEN\n"
                    b"HELPER_TOKEN = TOKEN\n"
                ),
            }
            for relative_path, content in fixture_files.items():
                self._write_bytes(root, relative_path, content)
            self._git(root, "add", "--", *sorted(fixture_files))
            self._git(root, "commit", "-m", "closure fixture")

            closure_arguments = {
                "root": root,
                "executable_roots": ["scripts/runner.py"],
                "forbidden_import_prefixes": (
                    "_socket",
                    "ctypes",
                    "elevenlabs",
                    "requests",
                    "socket",
                ),
                "guard_implementation_path": (
                    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py"
                ),
            }
            first = verification.build_executable_dependency_closure(
                **closure_arguments,
            )
            second = verification.build_executable_dependency_closure(
                **closure_arguments,
            )

            expected_inventory = [
                {
                    "path": relative_path,
                    "git_mode": "100644",
                    "sha256": self._sha256_bytes(content),
                }
                for relative_path, content in sorted(fixture_files.items())
            ]
            expected_edges = [
                {
                    "consumer": "scripts/runner.py",
                    "dependency": "scripts/worker.py",
                    "edge_type": "python_subprocess_target",
                },
                {
                    "consumer": "scripts/runner.py",
                    "dependency": "support/constants.py",
                    "edge_type": "python_import",
                },
                {
                    "consumer": "scripts/runner.py",
                    "dependency": "support/helper.py",
                    "edge_type": "python_import",
                },
                {
                    "consumer": "scripts/worker.py",
                    "dependency": "support/constants.py",
                    "edge_type": "python_import",
                },
                {
                    "consumer": "support/helper.py",
                    "dependency": "support/constants.py",
                    "edge_type": "python_import",
                },
            ]
            expected_digest = self._sha256_bytes(
                json.dumps(
                    {
                        "edges": expected_edges,
                        "inventory": expected_inventory,
                    },
                    ensure_ascii=True,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
            )
            self.assertEqual(
                first,
                {
                    "inventory": expected_inventory,
                    "edges": expected_edges,
                    "digest": expected_digest,
                },
            )
            self.assertEqual(second, first)

    def test_executable_dependency_closure_resolves_reviewed_subprocess_forms(
        self,
    ) -> None:
        verification = self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-reviewed-subprocess-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)
            fixture_files = {
                "scripts/test_emotion_state_001_open_dataset_gate.py": (
                    b"import subprocess\n"
                    b"import sys\n"
                    b"import textwrap\n"
                    b"source = \"print('reviewed open-dataset fixture')\"\n"
                    b"subprocess.run(\n"
                    b"    [sys.executable, \"-c\", textwrap.dedent(source)],\n"
                    b"    check=True,\n"
                    b")\n"
                ),
                "scripts/test_emotion_state_001_closeout_hardening.py": (
                    b"import subprocess\n"
                    b"import sys\n"
                    b"holder_script = \"print('reviewed closeout fixture')\"\n"
                    b"subprocess.Popen(\n"
                    b"    [sys.executable, \"-c\", holder_script],\n"
                    b")\n"
                ),
                "scripts/path_consumer.py": (
                    b"import subprocess\n"
                    b"import sys\n"
                    b"from pathlib import Path\n"
                    b"ROOT = Path(__file__).resolve().parents[1]\n"
                    b"RUNNER = ROOT / \"scripts\" / \"worker_a.py\"\n"
                    b"subprocess.run(\n"
                    b"    [sys.executable, str(ROOT / \"scripts\" / \"worker_b.py\")],\n"
                    b"    check=True,\n"
                    b")\n"
                    b"subprocess.run([sys.executable, str(RUNNER)], check=True)\n"
                    b"def invoke() -> None:\n"
                    b"    runner_path = ROOT / \"scripts\" / \"worker_c.py\"\n"
                    b"    subprocess.run(\n"
                    b"        [sys.executable, str(runner_path)],\n"
                    b"        check=True,\n"
                    b"    )\n"
                ),
                "scripts/worker_a.py": b"print(\"worker-a\")\n",
                "scripts/worker_b.py": b"print(\"worker-b\")\n",
                "scripts/worker_c.py": b"print(\"worker-c\")\n",
                "scripts/test_emotion_state_001_closeout_hardening_copy.py": (
                    b"import subprocess\n"
                    b"import sys\n"
                    b"holder_script = \"print('unreviewed inline fixture')\"\n"
                    b"subprocess.run(\n"
                    b"    [sys.executable, \"-c\", holder_script],\n"
                    b"    check=True,\n"
                    b")\n"
                ),
                "scripts/dynamic_target.py": (
                    b"import subprocess\n"
                    b"import sys\n"
                    b"target = \"scripts/worker_a.py\"\n"
                    b"subprocess.run([sys.executable, target], check=True)\n"
                ),
            }
            for relative_path, content in fixture_files.items():
                self._write_bytes(root, relative_path, content)
            self._git(root, "add", "--", *sorted(fixture_files))
            self._git(root, "commit", "-m", "reviewed subprocess fixtures")

            closure_arguments = {
                "root": root,
                "forbidden_import_prefixes": (
                    "_socket",
                    "ctypes",
                    "elevenlabs",
                    "requests",
                    "socket",
                ),
                "guard_implementation_path": (
                    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py"
                ),
            }
            closure = verification.build_executable_dependency_closure(
                executable_roots=[
                    "scripts/path_consumer.py",
                    "scripts/test_emotion_state_001_closeout_hardening.py",
                    "scripts/test_emotion_state_001_open_dataset_gate.py",
                ],
                **closure_arguments,
            )
            self.assertEqual(
                [
                    edge
                    for edge in closure["edges"]
                    if edge["edge_type"] == "python_subprocess_target"
                ],
                [
                    {
                        "consumer": "scripts/path_consumer.py",
                        "dependency": "scripts/worker_a.py",
                        "edge_type": "python_subprocess_target",
                    },
                    {
                        "consumer": "scripts/path_consumer.py",
                        "dependency": "scripts/worker_b.py",
                        "edge_type": "python_subprocess_target",
                    },
                    {
                        "consumer": "scripts/path_consumer.py",
                        "dependency": "scripts/worker_c.py",
                        "edge_type": "python_subprocess_target",
                    },
                ],
            )

            for executable_root in (
                "scripts/test_emotion_state_001_closeout_hardening_copy.py",
                "scripts/dynamic_target.py",
            ):
                with self.subTest(executable_root=executable_root):
                    with self.assertRaisesRegex(
                        ValueError,
                        r"dynamic subprocess target",
                    ):
                        verification.build_executable_dependency_closure(
                            executable_roots=[executable_root],
                            **closure_arguments,
                        )

    def test_executable_dependency_closure_runtime_consumers_are_gate_only(
        self,
    ) -> None:
        verification = self._verification_module()
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-runtime-consumer-gate-",
        ) as temporary_directory:
            root = Path(temporary_directory)
            self._initialize_git_repository(root)
            safe_root_bytes = b"STATE = \"safe executable root\"\n"
            fixture_files = {
                "scripts/safe_root.py": safe_root_bytes,
                "scripts/new_gate.py": b"STATE = \"detached gate\"\n",
                "runtime/consumer.py": (
                    b"import requests\n"
                    b"STATE = \"runtime consumer without gate import\"\n"
                ),
            }
            for relative_path, content in fixture_files.items():
                self._write_bytes(root, relative_path, content)
            self._git(root, "add", "--", *sorted(fixture_files))
            self._git(root, "commit", "-m", "runtime consumer gate fixtures")

            closure_arguments = {
                "root": root,
                "executable_roots": ["scripts/safe_root.py"],
                "forbidden_import_prefixes": (
                    "_socket",
                    "ctypes",
                    "elevenlabs",
                    "requests",
                    "socket",
                ),
                "guard_implementation_path": (
                    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py"
                ),
                "gate_module_paths": ("scripts/new_gate.py",),
                "runtime_consumer_paths": ("runtime/consumer.py",),
            }
            closure = verification.build_executable_dependency_closure(
                **closure_arguments,
            )
            self.assertEqual(
                closure["inventory"],
                [
                    {
                        "path": "scripts/safe_root.py",
                        "git_mode": "100644",
                        "sha256": self._sha256_bytes(safe_root_bytes),
                    }
                ],
            )
            self.assertEqual(closure["edges"], [])

            self._write_bytes(
                root,
                "runtime/consumer.py",
                (
                    b"from scripts import new_gate\n"
                    b"STATE = new_gate.STATE\n"
                ),
            )
            with self.assertRaisesRegex(
                ValueError,
                r"runtime consumer.*imports gate module",
            ):
                verification.build_executable_dependency_closure(
                    **closure_arguments,
                )

    def test_executable_dependency_closure_rejects_unsafe_or_unresolved_edges(
        self,
    ) -> None:
        verification = self._verification_module()
        rejection_cases = (
            {
                "name": "unresolved_local_import",
                "files": {
                    "localpkg/__init__.py": b"",
                    "scripts/entry.py": b"import localpkg.missing\n",
                },
                "error": r"unresolved local import.*localpkg\.missing",
            },
            {
                "name": "dynamic_subprocess_target",
                "files": {
                    "scripts/entry.py": (
                        b"import subprocess\n"
                        b"import sys\n"
                        b"target = \"scripts/worker.py\"\n"
                        b"subprocess.run([sys.executable, target], check=True)\n"
                    ),
                    "scripts/worker.py": b"print(\"fixture\")\n",
                },
                "error": r"dynamic subprocess target",
            },
            {
                "name": "subprocess_path_escape",
                "files": {
                    "scripts/entry.py": (
                        b"import subprocess\n"
                        b"import sys\n"
                        b"subprocess.run(\n"
                        b"    [sys.executable, \"../outside.py\"],\n"
                        b"    check=True,\n"
                        b")\n"
                    ),
                },
                "outside_file": True,
                "error": r"path escape",
            },
            {
                "name": "direct_ctypes_import",
                "files": {
                    "scripts/entry.py": b"import ctypes\n",
                },
                "error": r"forbidden import.*ctypes",
            },
            {
                "name": "direct_private_socket_import",
                "files": {
                    "scripts/entry.py": b"import _socket\n",
                },
                "error": r"forbidden import.*_socket",
            },
            {
                "name": "network_client_import",
                "files": {
                    "scripts/entry.py": b"import requests\n",
                },
                "error": r"forbidden import.*requests",
            },
            {
                "name": "provider_import_outside_guard",
                "files": {
                    "scripts/entry.py": b"import elevenlabs\n",
                },
                "error": r"forbidden import.*elevenlabs",
            },
            {
                "name": "runtime_consumer_imports_new_gate_module",
                "files": {
                    "scripts/safe_root.py": b"STATE = \"safe root\"\n",
                    "runtime/consumer.py": (
                        b"from scripts import new_gate\n"
                        b"STATE = new_gate.STATE\n"
                    ),
                    "scripts/new_gate.py": b"STATE = \"detached\"\n",
                },
                "executable_roots": ["scripts/safe_root.py"],
                "gate_module_paths": ("scripts/new_gate.py",),
                "runtime_consumer_paths": ("runtime/consumer.py",),
                "error": r"runtime consumer.*imports gate module",
            },
        )
        for case in rejection_cases:
            with self.subTest(case=case["name"]):
                with tempfile.TemporaryDirectory(
                    prefix="c-",
                ) as temporary_directory:
                    temporary_root = Path(temporary_directory)
                    root = temporary_root / "repository"
                    root.mkdir()
                    self._initialize_git_repository(root)
                    files = case["files"]
                    for relative_path, content in files.items():
                        self._write_bytes(root, relative_path, content)
                    if case.get("outside_file"):
                        self._write_bytes(
                            temporary_root,
                            "outside.py",
                            b"print(\"outside fixture\")\n",
                        )
                    self._git(root, "add", "--", *sorted(files))
                    self._git(root, "commit", "-m", "rejection fixture")

                    arguments = {
                        "root": root,
                        "executable_roots": case.get(
                            "executable_roots",
                            ["scripts/entry.py"],
                        ),
                        "forbidden_import_prefixes": (
                            "_socket",
                            "ctypes",
                            "elevenlabs",
                            "requests",
                            "socket",
                        ),
                        "guard_implementation_path": (
                            "scripts/emotion_state_phase_a_guard_site/"
                            "sitecustomize.py"
                        ),
                    }
                    if "gate_module_paths" in case:
                        arguments["gate_module_paths"] = case[
                            "gate_module_paths"
                        ]
                    if "runtime_consumer_paths" in case:
                        arguments["runtime_consumer_paths"] = case[
                            "runtime_consumer_paths"
                        ]
                    with self.assertRaisesRegex(ValueError, case["error"]):
                        verification.build_executable_dependency_closure(
                            **arguments,
                        )
