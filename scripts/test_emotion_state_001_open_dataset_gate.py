from __future__ import annotations

import hashlib
import io
import json
import struct
import tarfile
import tempfile
import unittest
import wave
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
