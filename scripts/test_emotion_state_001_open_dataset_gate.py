from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
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


class SplitManifestV2Tests(unittest.TestCase):
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
