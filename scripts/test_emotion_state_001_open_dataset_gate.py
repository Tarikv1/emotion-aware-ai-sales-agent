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

    def test_duplicate_actor_ids_deduplicate_and_contribution_is_deterministic(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )

        records = fixture_records(
            12,
            10,
            dataset_manifest_id="public-fixture-v1",
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
            fixture_records,
            fixture_request,
        )

        records = fixture_records(10, 10)
        foreign = deepcopy(records[0])
        foreign["dataset_manifest_id"] = "foreign-synthetic-corpus-v1"
        foreign["source_speaker_id"] = "foreign-fixture-speaker"
        foreign["eligible"] = False
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
