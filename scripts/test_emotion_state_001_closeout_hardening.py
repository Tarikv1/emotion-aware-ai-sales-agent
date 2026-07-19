from __future__ import annotations

import hashlib
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON = (
    "self-hosting guard unit runs in the direct unit gate; rerunning it under "
    "an active guard would require authority outside the frozen focused-command "
    "mapping"
)

EXPECTED_TASKS_1_7_INPUT_PATHS = (
    ".superpowers/sdd/task-4-report.md",
    ".superpowers/sdd/task-4-review-findings.md",
    "docs/product/COMMANDS.md",
    "docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md",
    (
        "docs/superpowers/plans/"
        "2026-07-15-emotion-state-phase-a-open-dataset-gate-completion.md"
    ),
    "docs/thesis/DECISION_LOG.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/ROADMAP.md",
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/third-party-inspirations.md",
    "research/experiments/EMOTION-STATE-001-phase-a.md",
    (
        "research/experiments/cases/"
        "emotion-state-001-cohort-release-fixtures.json"
    ),
    "research/experiments/cases/emotion-state-001-phase-a-contracts.json",
    "research/sources/creative_analysis_engine/source_manifest.json",
    "research/sources/creative_analysis_engine/source_notes.md",
    (
        "research/sources/emotion_state/"
        "cohort_release_evidence_v1.schema.json"
    ),
    "research/sources/emotion_state/dataset_manifest_contract.json",
    (
        "research/sources/emotion_state/"
        "phase_a_verification_guard_policy.json"
    ),
    "research/sources/emotion_state/split_manifest_v2.schema.json",
    "scripts/build_emotion_state_public_dataset_manifests.py",
    "scripts/check_project_drift.py",
    "scripts/check_setup.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/emotion_state_cohort_release_contracts.py",
    "scripts/emotion_state_phase_a_contracts.py",
    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py",
    "scripts/emotion_state_phase_a_verification_evidence.py",
    "scripts/emotion_state_public_dataset_contracts.py",
    "scripts/emotion_state_split_manifest_v2_contracts.py",
    "scripts/run_brain_002_runtime_state_schema.py",
    "scripts/run_emotion_state_001_phase_a_contracts.py",
    "scripts/run_exp_002_frozen_response_baseline.py",
    "scripts/test_emotion_state_001_closeout_hardening.py",
    "scripts/test_emotion_state_001_open_dataset_gate.py",
    "scripts/validate_check_setup.py",
    "scripts/validate_emotion_state_001_phase_a_contracts.py",
    "scripts/validate_private_data_boundary.py",
    "scripts/validate_project_drift_guard.py",
)

EXPECTED_TASKS_1_7_CLOSURE_PATHS = (
    "runtime/__init__.py",
    "runtime/contracts/__init__.py",
    "runtime/contracts/brain_runtime_state_schema.py",
    "runtime/contracts/emotion_pattern_contracts.py",
    "runtime/contracts/emotion_state_brain_extension.py",
    "runtime/contracts/emotion_state_contracts.py",
    "scripts/build_emotion_state_public_dataset_manifests.py",
    "scripts/check_project_drift.py",
    "scripts/check_setup.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/emotion_state_annotation_contracts.py",
    "scripts/emotion_state_cohort_release_contracts.py",
    "scripts/emotion_state_phase_a_contracts.py",
    "scripts/emotion_state_phase_a_guard_site/sitecustomize.py",
    "scripts/emotion_state_phase_a_verification_evidence.py",
    "scripts/emotion_state_public_dataset_contracts.py",
    "scripts/emotion_state_split_manifest_v2_contracts.py",
    "scripts/exp_002_frozen_response_baseline.py",
    "scripts/run_brain_002_runtime_state_schema.py",
    "scripts/run_emotion_state_001_phase_a_contracts.py",
    "scripts/run_exp_002_frozen_response_baseline.py",
    "scripts/run_prompt_baseline.py",
    "scripts/test_emotion_state_001_closeout_hardening.py",
    "scripts/test_emotion_state_001_open_dataset_gate.py",
    "scripts/validate_brain_002_runtime_state_schema.py",
    "scripts/validate_check_setup.py",
    "scripts/validate_emotion_state_001_phase_a_contracts.py",
    "scripts/validate_exp_002_frozen_response_baseline.py",
    "scripts/validate_private_data_boundary.py",
    "scripts/validate_project_drift_guard.py",
)

from scripts.emotion_state_phase_a_contracts import (
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_BASELINE_FINGERPRINTS,
    EXPECTED_CASE,
    EXPECTED_REVIEWED_FILES,
    render_phase_a_report,
)
from scripts.emotion_state_phase_a_verification_evidence import (
    ALLOWED_COMMAND_TEMPLATES,
    FROZEN_GUARD_POLICY_DIGEST,
    canonical_command_entry,
    canonical_json_sha256,
    derive_repository_gate_statuses,
)
from scripts import run_emotion_state_001_phase_a_contracts as publication_runner
from scripts import validate_emotion_state_001_phase_a_contracts as phase_a_validator
from scripts import validate_exp_002_frozen_response_baseline as exp_validator
from scripts.run_emotion_state_001_phase_a_contracts import (
    EvidencePublicationError,
    JOURNAL_NAME,
    publish_evidence_pair,
    recover_incomplete_publication,
    verify_evidence_pair_bytes,
)


def sample_verification_evidence() -> dict[str, object]:
    from scripts.emotion_state_phase_a_contracts import (
        TASKS_1_7_CLOSURE_EDGES,
    )

    baseline_commit = "fb0513545fc0167bcf89dbc81283b7b2a2820b67"
    head_commit = "c" * 40
    ledger: list[dict[str, object]] = []
    for sequence_number, (command_id, argv_template) in enumerate(
        (
            command
            for command in ALLOWED_COMMAND_TEMPLATES
            if command[0] != "phase-a-materials-validator"
        ),
        start=1,
    ):
        ledger.append(
            canonical_command_entry(
                sequence_number=sequence_number,
                command_id=command_id,
                argv=[
                    argument.format(
                        mode="material-pending",
                        baseline_commit=baseline_commit,
                        head_commit=head_commit,
                    )
                    for argument in argv_template
                ],
                working_directory=".",
                exit_status=0,
            )
        )
    committed_inventory: list[object] = [
        {
            "path": path,
            "git_mode": "100644",
            "sha256": "A" * 64,
        }
        for path in sorted(EXPECTED_TASKS_1_7_INPUT_PATHS)
    ]
    uncommitted_inventory: list[object] = []
    closure_inventory: list[object] = [
        {
            "path": path,
            "git_mode": "100644",
            "sha256": "B" * 64,
        }
        for path in sorted(EXPECTED_TASKS_1_7_CLOSURE_PATHS)
    ]
    closure_edges: list[object] = [
        {
            "consumer": consumer,
            "dependency": dependency,
            "edge_type": edge_type,
        }
        for consumer, dependency, edge_type in TASKS_1_7_CLOSURE_EDGES
    ]
    manifest_digests: dict[str, object] = {}
    hash_inventory_digests: dict[str, object] = {}
    tree_payload = {
        "implementation_baseline_commit": baseline_commit,
        "repository_head_commit": head_commit,
        "committed_change_inventory": committed_inventory,
        "uncommitted_change_inventory": uncommitted_inventory,
        "executable_dependency_closure_inventory": closure_inventory,
        "executable_dependency_closure_edges": closure_edges,
        "dataset_manifest_digests": manifest_digests,
        "dataset_hash_inventory_digests": hash_inventory_digests,
        "executed_command_ledger": ledger,
        "guard_policy_digest": FROZEN_GUARD_POLICY_DIGEST,
    }
    tree_digest = canonical_json_sha256(tree_payload)
    return {
        **tree_payload,
        "verification_input_path_inventory_digest": canonical_json_sha256({
            "committed_change_inventory": committed_inventory,
            "uncommitted_change_inventory": uncommitted_inventory,
        }),
        "executable_dependency_closure_digest": canonical_json_sha256({
            "edges": closure_edges,
            "inventory": closure_inventory,
        }),
        "executed_command_ledger_digest": canonical_json_sha256(ledger),
        "verification_input_tree_digest": tree_digest,
        "verification_run_id": hashlib.sha256(
            (
                "emotion-state-phase-a-validator-v1:"
                + tree_digest
            ).encode("utf-8")
        ).hexdigest().upper(),
        "guarded_command_results": {
            entry["command_id"]: entry["exit_status"]
            for entry in ledger
        },
        "repository_gate_statuses": derive_repository_gate_statuses(
            ledger,
            "material-pending",
            baseline_commit=baseline_commit,
            head_commit=head_commit,
        ),
        "provider_environment_scrubbed": True,
        "private_path_guard_enabled": True,
        "network_guard_enabled": True,
    }


def sample_payload() -> dict[str, object]:
    checks = {
        "exp_002_frozen_response_baseline": "pass",
        "emotion_state_annotation_contracts": "pass",
        "public_dataset_contract": "pass",
        "split_manifest_v2_contract": "pass",
        "cohort_release_contract": "pass",
        "emotion_state_contracts": "pass",
        "emotion_pattern_contracts": "pass",
        "emotion_state_brain_extension": "pass",
    }
    return {
        "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
        "schema_version": 2,
        "mode": "material_pending",
        "status": "material_pending",
        "selected_public_datasets": [
            "crema-d-v1.0-audio-wav",
            "ami-manual-annotations-v1.6.2",
        ],
        "dataset_download_authorized": False,
        "dataset_evaluation_started": False,
        "dataset_manifest_evidence": [],
        "source_pin": {
            "source_repository_url": (
                "https://github.com/WisdomBreathes/creative-analysis-engine"
            ),
            "source_branch": "dev",
            "source_revision": "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "source_adaptation_allowed": False,
            "code_adaptation_started": False,
        },
        "contract_checks": checks,
        "blocking_reason_codes": [
            "dataset_download_not_authorized",
            "selected_dataset_manifests_not_verified",
        ],
        "summary": {
            "contract_check_count": 8,
            "contract_checks": checks,
            "baseline_fingerprint_count": 6,
            "selected_public_dataset_count": 2,
            "dataset_download_authorized": False,
            "dataset_evaluation_started": False,
            "material_verification_status": "pending",
            "source_repository_url_status": "verified_read_only",
            "source_adaptation_allowed": False,
            "code_adaptation_started": False,
            "frozen_exp_002_evaluator_provenance_status": "not_recorded",
            "provider_operations_performed_by_runner": False,
            "private_data_read_by_runner": False,
            "runtime_behavior_changed_by_runner": False,
            "runtime_activation_allowed": False,
        },
        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "baseline_fingerprints": dict(EXPECTED_BASELINE_FINGERPRINTS),
        "readiness_boundary": {
            "phase_a_contract_artifacts_built": True,
            "phase_a_complete": False,
            "phase_a_completion_scope": (
                "source_provenance_dataset_selection_and_offline_contracts_only_"
                "material_verification_pending"
            ),
            "full_repository_gate_claimed_by_this_artifact": False,
            "live_aggregate_release_unblocked": False,
            "phase_b_unblocked": False,
            "public_dataset_evaluation_unblocked": False,
            "private_research_unblocked": False,
            "provider_feasibility_unblocked": False,
            "runtime_activation_unblocked": False,
        },
        **sample_verification_evidence(),
    }


def refresh_sample_verification_digests(payload: dict[str, object]) -> None:
    ledger = payload["executed_command_ledger"]
    payload["guarded_command_results"] = {
        entry["command_id"]: entry["exit_status"]
        for entry in ledger
    }
    payload["repository_gate_statuses"] = derive_repository_gate_statuses(
        ledger,
        "material-pending",
        baseline_commit=payload["implementation_baseline_commit"],
        head_commit=payload["repository_head_commit"],
    )
    payload["verification_input_path_inventory_digest"] = canonical_json_sha256({
        "committed_change_inventory": payload["committed_change_inventory"],
        "uncommitted_change_inventory": payload["uncommitted_change_inventory"],
    })
    payload["executable_dependency_closure_digest"] = canonical_json_sha256({
        "edges": payload["executable_dependency_closure_edges"],
        "inventory": payload["executable_dependency_closure_inventory"],
    })
    payload["executed_command_ledger_digest"] = canonical_json_sha256(ledger)
    tree_payload = {
        "implementation_baseline_commit": payload["implementation_baseline_commit"],
        "repository_head_commit": payload["repository_head_commit"],
        "committed_change_inventory": payload["committed_change_inventory"],
        "uncommitted_change_inventory": payload["uncommitted_change_inventory"],
        "executable_dependency_closure_inventory": (
            payload["executable_dependency_closure_inventory"]
        ),
        "executable_dependency_closure_edges": (
            payload["executable_dependency_closure_edges"]
        ),
        "dataset_manifest_digests": payload["dataset_manifest_digests"],
        "dataset_hash_inventory_digests": payload["dataset_hash_inventory_digests"],
        "executed_command_ledger": ledger,
        "guard_policy_digest": payload["guard_policy_digest"],
    }
    tree_digest = canonical_json_sha256(tree_payload)
    payload["verification_input_tree_digest"] = tree_digest
    payload["verification_run_id"] = hashlib.sha256(
        (
            "emotion-state-phase-a-validator-v1:"
            + tree_digest
        ).encode("utf-8")
    ).hexdigest().upper()


class DeterministicLfWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = ROOT / ".tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="emotion-state-001-lf-writer-test-",
            dir=temporary_root,
        )
        self.output_root = Path(self._temporary_directory.name)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def assert_exact_utf8_outputs(
        self,
        outputs: tuple[tuple[Path, str], ...],
    ) -> None:
        mismatches: list[str] = []
        for path, rendered in outputs:
            actual = path.read_bytes()
            expected = rendered.encode("utf-8")
            if actual == expected:
                continue
            first_difference = next(
                (
                    index
                    for index, (actual_byte, expected_byte) in enumerate(
                        zip(actual, expected)
                    )
                    if actual_byte != expected_byte
                ),
                min(len(actual), len(expected)),
            )
            mismatches.append(
                f"{path.name} bytes differ at offset {first_difference}; "
                f"actual_crlf_count={actual.count(bytes((13, 10)))}; "
                f"expected_crlf_count={expected.count(bytes((13, 10)))}"
            )
        if mismatches:
            self.fail("; ".join(mismatches))

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_exp_002_runner_writes_exact_utf8_lf_bytes(self) -> None:
        from scripts import run_exp_002_frozen_response_baseline as runner

        payload = runner.build_frozen_baseline_result(ROOT)
        rendered_result = (
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        )
        rendered_report = runner.render_frozen_baseline_report(payload)
        output_dir = self.output_root / "EXP-002"
        result_path = output_dir / "result.json"
        report_path = output_dir / "report.md"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(
            runner,
            "OUTPUT_DIR",
            output_dir,
        ), patch.object(
            runner,
            "RESULT",
            result_path,
        ), patch.object(
            runner,
            "REPORT",
            report_path,
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = runner.main()

        self.assertEqual(exit_code, 0)
        self.assert_exact_utf8_outputs((
            (result_path, rendered_result),
            (report_path, rendered_report),
        ))
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue())

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_brain_002_runner_writes_exact_utf8_lf_bytes(self) -> None:
        from scripts import run_brain_002_runtime_state_schema as runner

        payload = runner.build_brain_002_payload(
            runner.DEFAULT_CASE,
            root=ROOT,
        )
        rendered_result = json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        rendered_report = runner.render_brain_002_report(payload)
        output_dir = self.output_root / "BRAIN-002"
        result_path = output_dir / "result.json"
        report_path = output_dir / "report.md"
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(
            runner.sys,
            "argv",
            [
                "run_brain_002_runtime_state_schema.py",
                "--out",
                str(result_path),
                "--report-out",
                str(report_path),
            ],
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            runner.main()

        self.assert_exact_utf8_outputs((
            (result_path, rendered_result),
            (report_path, rendered_report),
        ))
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue())


class PublicationRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = ROOT / ".tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="emotion-state-001-publication-test-",
            dir=temporary_root,
        )
        self.test_root = Path(self._temporary_directory.name)
        self.canonical_dir = self.test_root / "canonical"
        self.result_path = self.canonical_dir / "result.json"
        self.report_path = self.canonical_dir / "report.md"
        self.recovery_dir = self.test_root / "recovery"
        self.journal_path = self.recovery_dir / JOURNAL_NAME

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _publish(self, payload: dict[str, object] | None = None) -> None:
        publish_evidence_pair(
            sample_payload() if payload is None else payload,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

    def _seed_legacy_pair(self) -> tuple[bytes, bytes]:
        old_result = b'{"generation":"old"}\r\n'
        old_report = b"legacy report without a publication marker\r\n"
        self.canonical_dir.mkdir(parents=True, exist_ok=True)
        self.result_path.write_bytes(old_result)
        self.report_path.write_bytes(old_report)
        return old_result, old_report

    def _assert_no_transaction_state(self) -> None:
        self.assertFalse(self.journal_path.exists())
        if self.recovery_dir.exists():
            self.assertEqual(list(self.recovery_dir.iterdir()), [])

    def test_immediate_helper_requires_explicit_noncanonical_paths_before_write(
        self,
    ) -> None:
        signature = inspect.signature(publish_evidence_pair)
        for parameter_name in ("result_path", "report_path", "recovery_dir"):
            self.assertIs(
                signature.parameters[parameter_name].default,
                inspect.Parameter.empty,
            )

        with patch.object(
            publication_runner,
            "_write_text_fsynced",
            side_effect=AssertionError("write boundary reached"),
        ) as write:
            with self.assertRaisesRegex(
                EvidencePublicationError,
                "canonical.*deferred acceptance",
            ):
                publish_evidence_pair(
                    sample_payload(),
                    result_path=publication_runner.DEFAULT_RESULT,
                    report_path=publication_runner.DEFAULT_REPORT,
                    recovery_dir=self.recovery_dir,
                )

        write.assert_not_called()

    @unittest.skipIf(
        "EMOTION_STATE_PHASE_A_GUARD_POLICY" in os.environ,
        ACTIVE_GUARD_SELF_HOSTING_SKIP_REASON,
    )
    def test_active_publisher_lock_blocks_second_cli_without_mutation(self) -> None:
        original_result, original_report = self._seed_legacy_pair()
        receipt_path = self.recovery_dir / "lock-holder-receipt.json"
        holder_script = r'''
import sys
from pathlib import Path

from scripts.run_emotion_state_001_phase_a_contracts import (
    publication_lock,
    stage_evidence_pair,
)
from scripts.test_emotion_state_001_closeout_hardening import sample_payload

result_path = Path(sys.argv[1])
report_path = Path(sys.argv[2])
recovery_dir = Path(sys.argv[3])
receipt_path = Path(sys.argv[4])
with publication_lock(recovery_dir=recovery_dir):
    stage_evidence_pair(
        sample_payload(),
        mode="material-pending",
        receipt_path=receipt_path,
        result_path=result_path,
        report_path=report_path,
        recovery_dir=recovery_dir,
    )
    print("READY", flush=True)
    input()
'''
        holder = subprocess.Popen(
            [
                sys.executable,
                "-c",
                holder_script,
                str(self.result_path),
                str(self.report_path),
                str(self.recovery_dir),
                str(receipt_path),
            ],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        holder_output = ""
        try:
            assert holder.stdout is not None
            ready = holder.stdout.readline().strip()
            if ready != "READY":
                assert holder.stderr is not None
                self.fail(f"lock holder did not become ready: {holder.stderr.read()}")

            live_result = self.result_path.read_bytes()
            live_report = self.report_path.read_bytes()
            live_state = {
                path.name: path.read_bytes()
                for path in self.recovery_dir.iterdir()
                if path.is_file() and path.name != publication_runner.LOCK_NAME
            }
            self.assertIn(JOURNAL_NAME, live_state)

            blocked_script = r'''
import sys
from pathlib import Path
from scripts.run_emotion_state_001_phase_a_contracts import (
    EvidencePublicationError,
    publication_lock,
    recover_incomplete_publication,
)
result_path = Path(sys.argv[1])
report_path = Path(sys.argv[2])
recovery_dir = Path(sys.argv[3])
try:
    with publication_lock(recovery_dir=recovery_dir):
        recover_incomplete_publication(
            result_path=result_path,
            report_path=report_path,
            recovery_dir=recovery_dir,
        )
except EvidencePublicationError as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(1)
raise SystemExit(0)
'''
            blocked = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    blocked_script,
                    str(self.result_path),
                    str(self.report_path),
                    str(self.recovery_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
            self.assertIn("publication lock is already held", blocked.stderr)
            self.assertNotIn("Traceback", blocked.stderr)
            self.assertEqual(self.result_path.read_bytes(), live_result)
            self.assertEqual(self.report_path.read_bytes(), live_report)
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in self.recovery_dir.iterdir()
                    if path.is_file() and path.name != publication_runner.LOCK_NAME
                },
                live_state,
            )

            holder.kill()
            holder_output, holder_error = holder.communicate(timeout=10)
            self.assertNotEqual(holder.returncode, 0, holder_output + holder_error)

            recovered = recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )
            self.assertEqual(recovered, "restored")
            self.assertEqual(self.result_path.read_bytes(), original_result)
            self.assertEqual(self.report_path.read_bytes(), original_report)
            self.assertFalse(self.journal_path.exists())
        finally:
            if holder.poll() is None:
                if holder.stdin is not None:
                    try:
                        holder.stdin.write("release\n")
                        holder.stdin.flush()
                    except OSError:
                        pass
                try:
                    holder_output, _ = holder.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    holder.kill()
                    holder.communicate(timeout=5)
            if self.journal_path.exists():
                try:
                    recover_incomplete_publication(
                        result_path=self.result_path,
                        report_path=self.report_path,
                        recovery_dir=self.recovery_dir,
                    )
                except EvidencePublicationError:
                    pass

    def test_successful_publication_uses_report_as_commit_marker(self) -> None:
        self._publish()

        self.assertEqual(
            {path.name for path in self.canonical_dir.iterdir()},
            {"result.json", "report.md"},
        )
        result_bytes = self.result_path.read_bytes()
        result_sha256 = hashlib.sha256(result_bytes).hexdigest().upper()
        report = self.report_path.read_text(encoding="utf-8")
        self.assertIn(
            f"- Publication commit marker: `result.json sha256:{result_sha256}`",
            report,
        )
        self._assert_no_transaction_state()

    def test_second_replace_failure_restores_previous_pair(self) -> None:
        old_result, old_report = self._seed_legacy_pair()
        real_replace = os.replace
        report_replacement_failed = False

        def fail_report_replacement_once(source: object, destination: object) -> None:
            nonlocal report_replacement_failed
            if Path(destination) == self.report_path and not report_replacement_failed:
                report_replacement_failed = True
                raise OSError("simulated report-target replacement failure")
            real_replace(source, destination)

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts.os.replace",
            side_effect=fail_report_replacement_once,
        ):
            with self.assertRaisesRegex(
                EvidencePublicationError,
                "evidence publication failed",
            ):
                self._publish()

        self.assertTrue(report_replacement_failed)
        self.assertEqual(self.result_path.read_bytes(), old_result)
        self.assertEqual(self.report_path.read_bytes(), old_report)
        self._assert_no_transaction_state()

    def test_hard_interrupt_after_result_replace_is_recovered_next_run(self) -> None:
        old_result, old_report = self._seed_legacy_pair()
        real_replace = os.replace

        def interrupt_after_result_replace(source: object, destination: object) -> None:
            real_replace(source, destination)
            if Path(destination) == self.result_path:
                raise KeyboardInterrupt("simulated interruption after result replacement")

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts.os.replace",
            side_effect=interrupt_after_result_replace,
        ):
            with self.assertRaises(KeyboardInterrupt):
                self._publish()

        self.assertTrue(self.journal_path.exists())
        self.assertEqual(len(list(self.recovery_dir.glob("*.result.backup"))), 1)
        self.assertEqual(len(list(self.recovery_dir.glob("*.report.backup"))), 1)
        self.assertEqual(
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            ),
            "restored",
        )
        self.assertEqual(self.result_path.read_bytes(), old_result)
        self.assertEqual(self.report_path.read_bytes(), old_report)
        self._assert_no_transaction_state()

    def test_recovery_retries_cleanup_after_previous_pair_is_restored(self) -> None:
        old_result, old_report = self._seed_legacy_pair()
        real_replace = os.replace

        def interrupt_after_result_replace(source: object, destination: object) -> None:
            real_replace(source, destination)
            if Path(destination) == self.result_path:
                raise KeyboardInterrupt("simulated interruption after result replacement")

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts.os.replace",
            side_effect=interrupt_after_result_replace,
        ):
            with self.assertRaises(KeyboardInterrupt):
                self._publish()

        result_backup = next(self.recovery_dir.glob("*.result.backup"))
        report_backup = next(self.recovery_dir.glob("*.report.backup"))
        path_type = type(report_backup)
        real_unlink = path_type.unlink
        cleanup_failure_injected = False

        def fail_after_first_backup_deleted(
            path: Path,
            missing_ok: bool = False,
        ) -> None:
            nonlocal cleanup_failure_injected
            if path == report_backup and not cleanup_failure_injected:
                cleanup_failure_injected = True
                raise OSError("simulated cleanup interruption")
            real_unlink(path, missing_ok=missing_ok)

        with patch.object(path_type, "unlink", new=fail_after_first_backup_deleted):
            with self.assertRaisesRegex(EvidencePublicationError, "recovery failed"):
                recover_incomplete_publication(
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        self.assertTrue(cleanup_failure_injected)
        self.assertEqual(self.result_path.read_bytes(), old_result)
        self.assertEqual(self.report_path.read_bytes(), old_report)
        self.assertFalse(result_backup.exists())
        self.assertTrue(report_backup.exists())
        self.assertTrue(self.journal_path.exists())
        self.assertEqual(
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            ),
            "restored",
        )
        self._assert_no_transaction_state()

    def test_hard_interrupt_after_report_replace_finalizes_committed_pair(self) -> None:
        self._seed_legacy_pair()
        real_replace = os.replace

        def interrupt_after_report_replace(source: object, destination: object) -> None:
            real_replace(source, destination)
            if Path(destination) == self.report_path:
                raise KeyboardInterrupt("simulated interruption after report replacement")

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts.os.replace",
            side_effect=interrupt_after_report_replace,
        ):
            with self.assertRaises(KeyboardInterrupt):
                self._publish()

        new_result = self.result_path.read_bytes()
        new_report = self.report_path.read_bytes()
        self.assertTrue(self.journal_path.exists())
        self.assertEqual(
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            ),
            "committed",
        )
        self.assertEqual(self.result_path.read_bytes(), new_result)
        self.assertEqual(self.report_path.read_bytes(), new_report)
        verify_evidence_pair_bytes(new_result, new_report)
        self._assert_no_transaction_state()

    def test_corrupt_backup_fails_closed_and_retains_recovery_evidence(self) -> None:
        self._seed_legacy_pair()
        real_replace = os.replace

        def interrupt_after_result_replace(source: object, destination: object) -> None:
            real_replace(source, destination)
            if Path(destination) == self.result_path:
                raise KeyboardInterrupt("simulated interruption after result replacement")

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts.os.replace",
            side_effect=interrupt_after_result_replace,
        ):
            with self.assertRaises(KeyboardInterrupt):
                self._publish()

        result_backups = list(self.recovery_dir.glob("*.result.backup"))
        self.assertEqual(len(result_backups), 1)
        result_backups[0].write_bytes(b"corrupt backup")

        with self.assertRaisesRegex(EvidencePublicationError, "backup"):
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertTrue(self.journal_path.exists())
        self.assertEqual(result_backups[0].read_bytes(), b"corrupt backup")

    def test_mismatched_report_marker_is_rejected(self) -> None:
        result_bytes = b'{"generation":"new"}\r\n'
        report_bytes = (
            b"- Publication commit marker: `result.json sha256:"
            + (b"A" * 64)
            + b"`\r\n"
        )

        with self.assertRaisesRegex(
            EvidencePublicationError,
            "publication commit marker",
        ):
            verify_evidence_pair_bytes(result_bytes, report_bytes)

    def test_report_marker_requires_uppercase_sha256(self) -> None:
        with self.assertRaisesRegex(ValueError, "uppercase SHA-256"):
            render_phase_a_report(sample_payload(), result_sha256="a" * 64)

    def test_recovery_directory_creation_failure_is_bounded(self) -> None:
        path_type = type(self.recovery_dir)
        real_mkdir = path_type.mkdir

        def fail_recovery_directory_creation(
            path: Path,
            mode: int = 0o777,
            parents: bool = False,
            exist_ok: bool = False,
        ) -> None:
            if path == self.recovery_dir:
                raise OSError("simulated recovery-directory failure")
            real_mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)

        with patch.object(path_type, "mkdir", new=fail_recovery_directory_creation):
            with self.assertRaisesRegex(EvidencePublicationError, "recovery directory"):
                self._publish()

        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())


class PublicationAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = ROOT / ".tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="emotion-state-001-acceptance-test-",
            dir=temporary_root,
        )
        self.test_root = Path(self._temporary_directory.name)
        self.canonical_dir = self.test_root / "canonical"
        self.result_path = self.canonical_dir / "result.json"
        self.report_path = self.canonical_dir / "report.md"
        self.recovery_dir = self.test_root / "recovery"
        self.receipt_path = self.recovery_dir / "material-pending-receipt.json"
        self.journal_path = self.recovery_dir / JOURNAL_NAME

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _seed_previous_pair(self) -> tuple[bytes, bytes]:
        previous_result = b'{"generation":"previous"}\r\n'
        previous_report = b"previous report bytes\r\n"
        self.canonical_dir.mkdir(parents=True, exist_ok=True)
        self.result_path.write_bytes(previous_result)
        self.report_path.write_bytes(previous_report)
        return previous_result, previous_report

    def _stage(self) -> dict[str, object]:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            stage_evidence_pair,
        )

        return stage_evidence_pair(
            sample_payload(),
            mode="material-pending",
            receipt_path=self.receipt_path,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

    def _assert_transaction_clean(self) -> None:
        self.assertFalse(self.journal_path.exists())
        self.assertFalse(self.receipt_path.exists())
        if self.recovery_dir.exists():
            self.assertEqual(list(self.recovery_dir.iterdir()), [])

    def test_staged_candidate_retains_durable_journal_and_exact_backups(self) -> None:
        previous_result, previous_report = self._seed_previous_pair()

        receipt = self._stage()

        self.assertTrue(self.journal_path.exists())
        self.assertTrue(self.receipt_path.exists())
        journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["acceptance_status"], "awaiting_acceptance")
        self.assertEqual(journal["mode"], "material-pending")
        result_backup = next(self.recovery_dir.glob("*.result.backup"))
        report_backup = next(self.recovery_dir.glob("*.report.backup"))
        self.assertEqual(result_backup.read_bytes(), previous_result)
        self.assertEqual(report_backup.read_bytes(), previous_report)
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "transaction_id",
                "candidate_result_sha256",
                "candidate_report_sha256",
                "previous_pair_present",
                "previous_result_sha256",
                "previous_report_sha256",
                "mode",
            },
        )
        receipt_text = self.receipt_path.read_text(encoding="utf-8")
        self.assertNotIn(str(self.test_root), receipt_text)
        self.assertNotIn("timestamp", receipt_text.casefold())

    def test_candidate_readback_never_invokes_runner(self) -> None:
        from scripts import validate_emotion_state_001_phase_a_contracts as validator

        self._seed_previous_pair()
        self._stage()
        canonical_before = {
            path.name: path.read_bytes()
            for path in self.canonical_dir.iterdir()
        }
        recovery_before = {
            path.name: path.read_bytes()
            for path in self.recovery_dir.iterdir()
            if path.is_file()
        }
        with (
            mock.patch.object(validator, "RESULT", self.result_path),
            mock.patch.object(validator, "REPORT", self.report_path),
            mock.patch.object(
                validator,
                "RECOVERY_DIR",
                self.recovery_dir,
                create=True,
            ),
            mock.patch.object(validator.subprocess, "run") as run,
        ):
            validator.validate_candidate_readback(self.receipt_path)
        run.assert_not_called()
        self.assertEqual(
            {
                path.name: path.read_bytes()
                for path in self.canonical_dir.iterdir()
            },
            canonical_before,
        )
        self.assertEqual(
            {
                path.name: path.read_bytes()
                for path in self.recovery_dir.iterdir()
                if path.is_file()
            },
            recovery_before,
        )

    def test_candidate_readback_requires_exact_awaiting_transaction(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        with self.assertRaises(EvidencePublicationError):
            validate_candidate_evidence_pair(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self._stage()
        wrong_receipt = self.recovery_dir / "wrong-receipt.json"
        with self.assertRaisesRegex(EvidencePublicationError, "receipt path"):
            validate_candidate_evidence_pair(
                wrong_receipt,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        journal["acceptance_status"] = "accepted"
        self.journal_path.write_text(
            json.dumps(journal, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(EvidencePublicationError, "awaiting"):
            validate_candidate_evidence_pair(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

    def test_checkpoint_readback_rejects_any_transaction_or_orphan_receipt(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-checkpoint-transaction-state-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            root = Path(temporary_directory)
            canonical = root / "canonical"
            result = canonical / "result.json"
            report = canonical / "report.md"
            recovery = root / "recovery"
            receipt = recovery / "candidate-receipt.json"
            publication_runner.stage_evidence_pair(
                sample_payload(),
                mode="material-pending",
                receipt_path=receipt,
                result_path=result,
                report_path=report,
                recovery_dir=recovery,
            )
            journal = recovery / JOURNAL_NAME
            original_journal = journal.read_bytes()

            with (
                mock.patch.object(phase_a_validator, "RESULT", result),
                mock.patch.object(phase_a_validator, "REPORT", report),
                mock.patch.object(
                    phase_a_validator,
                    "RECOVERY_DIR",
                    recovery,
                ),
            ):
                accepted = json.loads(original_journal.decode("utf-8"))
                accepted["acceptance_status"] = "accepted"
                journal.write_text(
                    json.dumps(accepted, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    AssertionError,
                    "no live publication transaction",
                ):
                    phase_a_validator.validate_checkpoint_readback()

                journal.write_bytes(b"{malformed journal")
                with self.assertRaisesRegex(
                    AssertionError,
                    "no live publication transaction",
                ):
                    phase_a_validator.validate_checkpoint_readback()

                journal.unlink()
                with self.assertRaisesRegex(
                    AssertionError,
                    "receipt|transaction",
                ):
                    phase_a_validator.validate_checkpoint_readback()

                journal.write_bytes(original_journal)
                receipt.unlink()
                with self.assertRaisesRegex(
                    AssertionError,
                    "no live publication transaction",
                ):
                    phase_a_validator.validate_checkpoint_readback()

                journal.unlink()
                for orphan_name in (
                    "orphan.result.backup",
                    "orphan.result.restore",
                ):
                    with self.subTest(orphan_residual=orphan_name):
                        orphan = recovery / orphan_name
                        orphan.write_bytes(b"synthetic orphan\n")
                        with self.assertRaisesRegex(
                            AssertionError,
                            "residual publication transaction",
                        ):
                            phase_a_validator.validate_checkpoint_readback()
                        orphan.unlink()

    def test_candidate_readback_rejects_builder_owned_status_tamper(self) -> None:
        payload = sample_payload()
        payload["status"] = "complete"
        from scripts.run_emotion_state_001_phase_a_contracts import (
            stage_evidence_pair,
        )

        with self.assertRaisesRegex(EvidencePublicationError, "status"):
            stage_evidence_pair(
                payload,
                mode="material-pending",
                receipt_path=self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )
        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())
        self.assertFalse(self.receipt_path.exists())
        self.assertFalse(self.journal_path.exists())

    def test_candidate_readback_rejects_full_semantic_mutation_matrix(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            stage_evidence_pair,
            validate_candidate_evidence_pair,
        )

        def mutate_extra(payload: dict[str, object]) -> None:
            payload["verification_evidence"] = {}

        def mutate_missing(payload: dict[str, object]) -> None:
            payload.pop("archive_sha256")

        def mutate_source(payload: dict[str, object]) -> None:
            payload["source_pin"]["source_branch"] = "main"

        def mutate_contract(payload: dict[str, object]) -> None:
            payload["contract_checks"]["emotion_state_contracts"] = "fail"

        def mutate_baseline(payload: dict[str, object]) -> None:
            payload["baseline_fingerprints"][
                "docs/thesis/EVALUATION_RUBRIC.md"
            ] = "A" * 64

        def mutate_evidence_key(payload: dict[str, object]) -> None:
            payload.pop("verification_run_id")

        def mutate_evidence_type(payload: dict[str, object]) -> None:
            payload["executed_command_ledger"] = {}

        def mutate_gate(payload: dict[str, object]) -> None:
            payload["repository_gate_statuses"]["diff_check"] = "fail"

        def mutate_tree_digest(payload: dict[str, object]) -> None:
            payload["verification_input_tree_digest"] = "A" * 64

        def mutate_material_digest(payload: dict[str, object]) -> None:
            payload["dataset_manifest_digests"] = {"unexpected": "A" * 64}

        def mutate_summary(payload: dict[str, object]) -> None:
            payload["summary"]["provider_operations_performed_by_runner"] = True

        def mutate_readiness(payload: dict[str, object]) -> None:
            payload["readiness_boundary"]["phase_b_unblocked"] = True

        mutations = {
            "extra_top_level": mutate_extra,
            "missing_top_level": mutate_missing,
            "source_pin": mutate_source,
            "contract_status": mutate_contract,
            "baseline_fingerprint": mutate_baseline,
            "evidence_key": mutate_evidence_key,
            "evidence_type": mutate_evidence_type,
            "repository_gate": mutate_gate,
            "tree_digest": mutate_tree_digest,
            "material_digest": mutate_material_digest,
            "summary_projection": mutate_summary,
            "readiness_projection": mutate_readiness,
        }
        self.assertEqual(len(sample_payload()), 35)
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory(
                    prefix=f"emotion-state-semantic-{label}-",
                    dir=ROOT / ".tmp",
                ) as temporary_directory:
                    root = Path(temporary_directory)
                    result = root / "canonical" / "result.json"
                    report = result.with_name("report.md")
                    recovery = root / "recovery"
                    receipt = recovery / "candidate-receipt.json"
                    payload = sample_payload()
                    mutate(payload)
                    try:
                        stage_evidence_pair(
                            payload,
                            mode="material-pending",
                            receipt_path=receipt,
                            result_path=result,
                            report_path=report,
                            recovery_dir=recovery,
                        )
                    except EvidencePublicationError:
                        continue
                    with self.assertRaises(EvidencePublicationError):
                        validate_candidate_evidence_pair(
                            receipt,
                            result_path=result,
                            report_path=report,
                            recovery_dir=recovery,
                        )

    def test_payload_rejects_noncanonical_excluded_and_orphan_evidence_paths(
        self,
    ) -> None:
        from scripts.emotion_state_phase_a_contracts import (
            validate_material_pending_payload,
        )

        def noncanonical_path(payload: dict[str, object]) -> None:
            payload["committed_change_inventory"] = [{
                "path": "./scripts/example.py",
                "git_mode": "100644",
                "sha256": "A" * 64,
            }]

        def private_path(payload: dict[str, object]) -> None:
            payload["committed_change_inventory"] = [{
                "path": "data/private/example.json",
                "git_mode": "100644",
                "sha256": "A" * 64,
            }]

        def canonical_output_path(payload: dict[str, object]) -> None:
            payload["committed_change_inventory"] = [{
                "path": (
                    "research/experiments/generated/"
                    "EMOTION-STATE-001-phase-a-contracts/result.json"
                ),
                "git_mode": "100644",
                "sha256": "A" * 64,
            }]

        def mixed_case_private_path(payload: dict[str, object]) -> None:
            payload["committed_change_inventory"] = [{
                "path": "DATA/PRIVATE/example.json",
                "git_mode": "100644",
                "sha256": "A" * 64,
            }]

        def mistyped_git_state(payload: dict[str, object]) -> None:
            payload["uncommitted_change_inventory"] = [{
                "path": "scripts/example.py",
                "git_mode": "100644",
                "sha256": "A" * 64,
                "git_state": [],
            }]

        def orphan_closure_edge(payload: dict[str, object]) -> None:
            payload["executable_dependency_closure_edges"] = [{
                "consumer": "scripts/consumer.py",
                "dependency": "scripts/dependency.py",
                "edge_type": "python_import",
            }]

        mutations = {
            "noncanonical_path": noncanonical_path,
            "private_path": private_path,
            "mixed_case_private_path": mixed_case_private_path,
            "canonical_output_path": canonical_output_path,
            "mistyped_git_state": mistyped_git_state,
            "orphan_closure_edge": orphan_closure_edge,
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = sample_payload()
                mutate(payload)
                refresh_sample_verification_digests(payload)
                with self.assertRaises(ValueError):
                    validate_material_pending_payload(payload)

    def test_payload_requires_exact_tasks_1_7_inventory_and_closure_scope(
        self,
    ) -> None:
        from scripts.emotion_state_phase_a_contracts import (
            TASKS_1_7_CHANGE_INVENTORY_PATHS,
            TASKS_1_7_CLOSURE_PATHS,
            _validate_evidence_path,
            validate_material_pending_payload,
        )

        self.assertEqual(
            TASKS_1_7_CHANGE_INVENTORY_PATHS,
            EXPECTED_TASKS_1_7_INPUT_PATHS,
        )
        self.assertEqual(
            TASKS_1_7_CLOSURE_PATHS,
            EXPECTED_TASKS_1_7_CLOSURE_PATHS,
        )
        payload = sample_payload()
        self.assertEqual(len(TASKS_1_7_CHANGE_INVENTORY_PATHS), 38)
        self.assertEqual(len(payload["uncommitted_change_inventory"]), 0)
        self.assertEqual(len(TASKS_1_7_CLOSURE_PATHS), 30)
        validate_material_pending_payload(payload)
        self.assertEqual(
            _validate_evidence_path(
                "data/public/emotion-statex/near-prefix.bin",
                field="near-prefix",
            ),
            "data/public/emotion-statex/near-prefix.bin",
        )

        def inventory_entry(
            path: str,
            *,
            uncommitted: bool = False,
        ) -> dict[str, object]:
            entry: dict[str, object] = {
                "path": path,
                "git_mode": "100644",
                "sha256": "C" * 64,
            }
            if uncommitted:
                entry["git_state"] = "unstaged"
            return entry

        injected_paths = (
            (
                "committed_change_inventory",
                "data/public/emotion-state",
            ),
            (
                "committed_change_inventory",
                "DATA/PUBLIC/EMOTION-STATE/crema-d-v1.0/payload.bin",
            ),
            (
                "committed_change_inventory",
                (
                    "research/sources/emotion_state/datasets/"
                    "crema-d-v1.0-audio-wav.manifest.json"
                ),
            ),
            (
                "committed_change_inventory",
                "runtime/providers/elevenlabs_live.py",
            ),
            (
                "committed_change_inventory",
                "scripts/validate_elevenlabs_040_live.py",
            ),
            (
                "executable_dependency_closure_inventory",
                "Runtime/Providers/elevenlabs_live.py",
            ),
            (
                "executable_dependency_closure_inventory",
                "scripts/validate_elevenlabs_040_live.py",
            ),
        )
        for field, path in injected_paths:
            with self.subTest(field=field, injected_path=path):
                payload = sample_payload()
                payload[field] = sorted(
                    [
                        *payload[field],
                        inventory_entry(path),
                    ],
                    key=lambda entry: entry["path"],
                )
                refresh_sample_verification_digests(payload)
                with self.assertRaisesRegex(ValueError, "scope|excluded"):
                    validate_material_pending_payload(payload)

        for field in (
            "committed_change_inventory",
            "executable_dependency_closure_inventory",
        ):
            with self.subTest(omitted_from=field):
                payload = sample_payload()
                payload[field] = payload[field][1:]
                refresh_sample_verification_digests(payload)
                with self.assertRaisesRegex(ValueError, "exact|scope"):
                    validate_material_pending_payload(payload)

        for field, replacement_path in (
            (
                "committed_change_inventory",
                "scripts/unauthorized-task-7-replacement.py",
            ),
            (
                "executable_dependency_closure_inventory",
                "scripts/unauthorized-closure-replacement.py",
            ),
        ):
            with self.subTest(same_cardinality_replacement=field):
                payload = sample_payload()
                original_count = len(payload[field])
                payload[field] = sorted(
                    [
                        *payload[field][1:],
                        inventory_entry(replacement_path),
                    ],
                    key=lambda entry: entry["path"],
                )
                self.assertEqual(len(payload[field]), original_count)
                refresh_sample_verification_digests(payload)
                with self.assertRaisesRegex(ValueError, "exact|scope"):
                    validate_material_pending_payload(payload)

        payload = sample_payload()
        payload["uncommitted_change_inventory"] = [
            inventory_entry(
                "scripts/emotion_state_phase_a_contracts.py",
                uncommitted=True,
            )
        ]
        refresh_sample_verification_digests(payload)
        with self.assertRaisesRegex(ValueError, "uncommitted|scope"):
            validate_material_pending_payload(payload)

        payload = sample_payload()
        payload["committed_change_inventory"][0]["path"] = (
            payload["committed_change_inventory"][0]["path"].upper()
        )
        payload["committed_change_inventory"] = sorted(
            payload["committed_change_inventory"],
            key=lambda entry: entry["path"],
        )
        refresh_sample_verification_digests(payload)
        with self.assertRaisesRegex(ValueError, "canonical|scope"):
            validate_material_pending_payload(payload)

    def test_payload_requires_exact_tasks_1_7_closure_edges(self) -> None:
        from scripts.emotion_state_phase_a_contracts import (
            TASKS_1_7_CLOSURE_EDGES,
            validate_material_pending_payload,
        )

        validate_material_pending_payload(sample_payload())
        self.assertEqual(len(TASKS_1_7_CLOSURE_EDGES), 77)

        payload = sample_payload()
        payload["executable_dependency_closure_edges"] = payload[
            "executable_dependency_closure_edges"
        ][1:]
        refresh_sample_verification_digests(payload)
        with self.assertRaisesRegex(ValueError, "closure.*exact|exact.*closure"):
            validate_material_pending_payload(payload)

        payload = sample_payload()
        original_edge_count = len(
            payload["executable_dependency_closure_edges"]
        )
        payload["executable_dependency_closure_edges"] = [
            *payload["executable_dependency_closure_edges"][1:],
            {
                "consumer": "runtime/__init__.py",
                "dependency": "runtime/contracts/__init__.py",
                "edge_type": "python_import",
            },
        ]
        payload["executable_dependency_closure_edges"].sort(
            key=lambda edge: (
                edge["consumer"],
                edge["dependency"],
                edge["edge_type"],
            )
        )
        self.assertEqual(
            len(payload["executable_dependency_closure_edges"]),
            original_edge_count,
        )
        refresh_sample_verification_digests(payload)
        with self.assertRaisesRegex(ValueError, "closure.*exact|exact.*closure"):
            validate_material_pending_payload(payload)

        payload = sample_payload()
        payload["executable_dependency_closure_edges"].append({
            "consumer": "runtime/__init__.py",
            "dependency": "runtime/contracts/__init__.py",
            "edge_type": "python_import",
        })
        payload["executable_dependency_closure_edges"].sort(
            key=lambda edge: (
                edge["consumer"],
                edge["dependency"],
                edge["edge_type"],
            )
        )
        refresh_sample_verification_digests(payload)
        with self.assertRaisesRegex(ValueError, "closure.*exact|exact.*closure"):
            validate_material_pending_payload(payload)

        payload = sample_payload()
        payload["executable_dependency_closure_edges"][0]["edge_type"] = (
            "python_subprocess_target"
        )
        payload["executable_dependency_closure_edges"].sort(
            key=lambda edge: (
                edge["consumer"],
                edge["dependency"],
                edge["edge_type"],
            )
        )
        refresh_sample_verification_digests(payload)
        with self.assertRaisesRegex(ValueError, "closure.*exact|exact.*closure"):
            validate_material_pending_payload(payload)

    def test_payload_rejects_ledger_commit_range_mismatch(self) -> None:
        from scripts.emotion_state_phase_a_contracts import (
            validate_material_pending_payload,
        )

        payload = sample_payload()
        diff_entry = next(
            entry
            for entry in payload["executed_command_ledger"]
            if entry["command_id"] == "git-diff-check"
        )
        diff_entry["argv"][-1] = (
            ("d" * 40)
            + ".."
            + payload["repository_head_commit"]
        )
        with self.assertRaisesRegex(ValueError, "commit|range"):
            validate_material_pending_payload(payload)

    def test_candidate_acceptance_blocks_complete_mode_contract_bypass(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            stage_evidence_pair,
        )

        payload = sample_payload()
        payload["mode"] = "complete"
        with self.assertRaisesRegex(
            EvidencePublicationError,
            "complete payload is invalid",
        ):
            stage_evidence_pair(
                payload,
                mode="complete",
                receipt_path=self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )
        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())
        self.assertFalse(self.receipt_path.exists())
        self.assertFalse(self.journal_path.exists())

    def test_incomplete_complete_payload_is_rejected_before_publication_mutation(
        self,
    ) -> None:
        payload = sample_payload()
        payload["mode"] = "complete"
        payload["status"] = "complete"
        payload["dataset_download_authorized"] = True
        payload["dataset_evaluation_started"] = False
        payload["readiness_boundary"]["phase_a_complete"] = True
        with (
            mock.patch.object(
                publication_runner,
                "_write_text_fsynced",
            ) as write_guard,
            mock.patch.object(
                publication_runner.os,
                "replace",
            ) as replace_guard,
            mock.patch.object(
                publication_runner,
                "publication_lock",
            ) as lock_guard,
        ):
            for entry_point in ("stage", "direct"):
                with self.subTest(entry_point=entry_point):
                    function = (
                        publication_runner.stage_evidence_pair
                        if entry_point == "stage"
                        else publication_runner._write_evidence_pair_transaction
                    )
                    with self.assertRaisesRegex(
                        EvidencePublicationError,
                        "complete payload is invalid",
                    ):
                        function(
                            payload,
                            mode="complete",
                            receipt_path=self.receipt_path,
                            result_path=self.result_path,
                            report_path=self.report_path,
                            recovery_dir=self.recovery_dir,
                        )
            write_guard.assert_not_called()
            replace_guard.assert_not_called()
            lock_guard.assert_not_called()
        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())
        self.assertFalse(self.receipt_path.exists())
        self.assertFalse(self.journal_path.exists())

    def test_malformed_complete_readiness_shape_leaves_no_publication_residue(
        self,
    ) -> None:
        from scripts.emotion_state_phase_a_contracts import (
            COMPLETE_PAYLOAD_FIELDS,
            COMPLETE_READINESS_BOUNDARY_FIELDS,
        )

        for mutation in ("wrong_type", "missing", "extra"):
            for entry_point in ("stage", "direct"):
                with self.subTest(mutation=mutation, entry_point=entry_point):
                    payload = {
                        field: None
                        for field in COMPLETE_PAYLOAD_FIELDS
                    }
                    payload.update({
                        "checkpoint_id": (
                            "EMOTION-STATE-001-phase-a-contracts"
                        ),
                        "schema_version": 2,
                        "mode": "complete",
                        "status": "complete",
                        "selected_public_datasets": [
                            "crema-d-v1.0-audio-wav",
                            "ami-manual-annotations-v1.6.2",
                        ],
                        "dataset_download_authorized": True,
                        "dataset_evaluation_started": False,
                        "readiness_boundary": {
                            field: False
                            for field in COMPLETE_READINESS_BOUNDARY_FIELDS
                        },
                    })
                    if mutation == "wrong_type":
                        payload["readiness_boundary"] = []
                    else:
                        readiness = dict(payload["readiness_boundary"])
                        if mutation == "missing":
                            readiness.pop("runtime_activation_unblocked")
                        else:
                            readiness["unexpected_unowned_boundary"] = False
                        payload["readiness_boundary"] = readiness
                    function = (
                        publication_runner.stage_evidence_pair
                        if entry_point == "stage"
                        else publication_runner._write_evidence_pair_transaction
                    )
                    with (
                        mock.patch.object(
                            publication_runner,
                            "_write_text_fsynced",
                        ) as write_guard,
                        mock.patch.object(
                            publication_runner.os,
                            "replace",
                        ) as replace_guard,
                        mock.patch.object(
                            publication_runner,
                            "publication_lock",
                        ) as lock_guard,
                        self.assertRaisesRegex(
                            EvidencePublicationError,
                            "complete payload is invalid.*readiness_boundary",
                        ),
                    ):
                        function(
                            payload,
                            mode="complete",
                            receipt_path=self.receipt_path,
                            result_path=self.result_path,
                            report_path=self.report_path,
                            recovery_dir=self.recovery_dir,
                        )
                    write_guard.assert_not_called()
                    replace_guard.assert_not_called()
                    lock_guard.assert_not_called()
                    self.assertFalse(self.result_path.exists())
                    self.assertFalse(self.report_path.exists())
                    self.assertFalse(self.receipt_path.exists())
                    self.assertFalse(self.journal_path.exists())

    def test_candidate_readback_rejects_third_directory_entry(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        self._stage()
        (self.canonical_dir / "unexpected-directory").mkdir()

        with self.assertRaisesRegex(EvidencePublicationError, "exactly"):
            validate_candidate_evidence_pair(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

    def test_candidate_readback_rejects_canonical_link_or_reparse_metadata(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        self._stage()
        path_type = type(self.result_path)
        real_read_bytes = path_type.read_bytes
        real_open = path_type.open
        real_replace = os.replace
        for linked_path in (
            self.canonical_dir,
            self.result_path,
            self.report_path,
        ):
            with self.subTest(linked_path=linked_path.name):
                target_accesses: list[tuple[str, Path]] = []

                def guarded_read_bytes(path: Path) -> bytes:
                    if path in {self.result_path, self.report_path}:
                        target_accesses.append(("read", path))
                        raise AssertionError("candidate target read")
                    return real_read_bytes(path)

                def guarded_open(
                    path: Path,
                    *args: object,
                    **kwargs: object,
                ) -> object:
                    if path in {self.result_path, self.report_path}:
                        target_accesses.append(("open", path))
                        raise AssertionError("candidate target opened")
                    return real_open(path, *args, **kwargs)

                def guarded_replace(
                    source: object,
                    destination: object,
                ) -> None:
                    destination_path = Path(destination)
                    if destination_path in {
                        self.result_path,
                        self.report_path,
                    }:
                        target_accesses.append(("write", destination_path))
                        raise AssertionError("candidate target written")
                    real_replace(source, destination)

                with (
                    mock.patch.object(
                        publication_runner,
                        "_path_is_link_or_reparse",
                        side_effect=lambda path, status=None, target=linked_path: (
                            Path(path) == target
                        ),
                        create=True,
                    ),
                    mock.patch.object(
                        path_type,
                        "read_bytes",
                        new=guarded_read_bytes,
                    ),
                    mock.patch.object(
                        path_type,
                        "open",
                        new=guarded_open,
                    ),
                    mock.patch.object(
                        publication_runner.os,
                        "replace",
                        side_effect=guarded_replace,
                    ),
                ):
                    with self.assertRaisesRegex(
                        EvidencePublicationError,
                        "link|reparse",
                    ):
                        validate_candidate_evidence_pair(
                            self.receipt_path,
                            result_path=self.result_path,
                            report_path=self.report_path,
                            recovery_dir=self.recovery_dir,
                        )
                self.assertEqual(target_accesses, [])

    def test_acceptance_restore_never_reads_rejected_canonical_link(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        self._seed_previous_pair()
        self._stage()
        path_type = type(self.result_path)
        real_read_bytes = path_type.read_bytes
        canonical_read_attempted = False

        def guarded_read_bytes(path: Path) -> bytes:
            nonlocal canonical_read_attempted
            if path == self.result_path:
                canonical_read_attempted = True
                raise AssertionError("canonical link target read")
            return real_read_bytes(path)

        with (
            mock.patch.object(
                publication_runner,
                "_path_is_link_or_reparse",
                side_effect=lambda path, status=None: (
                    Path(path) == self.result_path
                ),
            ),
            mock.patch.object(path_type, "read_bytes", new=guarded_read_bytes),
        ):
            with self.assertRaisesRegex(
                EvidencePublicationError,
                "restoration failed|link|reparse",
            ):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        self.assertFalse(canonical_read_attempted)
        self.assertTrue(self.journal_path.exists())
        self.assertTrue(self.receipt_path.exists())

    def test_acceptance_restore_never_writes_through_rejected_parent_link(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        self._seed_previous_pair()
        self._stage()
        real_replace = os.replace
        canonical_write_attempted = False

        def guarded_replace(source: object, destination: object) -> None:
            nonlocal canonical_write_attempted
            if Path(destination).parent == self.canonical_dir:
                canonical_write_attempted = True
                raise AssertionError("canonical parent target write")
            real_replace(source, destination)

        with (
            mock.patch.object(
                publication_runner,
                "_path_is_link_or_reparse",
                side_effect=lambda path, status=None: (
                    Path(path) == self.canonical_dir
                ),
            ),
            mock.patch.object(
                publication_runner.os,
                "replace",
                side_effect=guarded_replace,
            ),
        ):
            with self.assertRaisesRegex(
                EvidencePublicationError,
                "restoration failed|link|reparse",
            ):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        self.assertFalse(canonical_write_attempted)
        self.assertTrue(self.journal_path.exists())
        self.assertTrue(self.receipt_path.exists())

    def test_candidate_readback_rejects_ordinary_result_symlink_when_supported(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        self._stage()
        external_result = self.test_root / "external-result.json"
        external_result.write_bytes(self.result_path.read_bytes())
        self.result_path.unlink()
        try:
            self.result_path.symlink_to(external_result)
        except OSError as exc:
            self.skipTest(f"ordinary symlink creation unavailable: {exc}")

        path_type = type(self.result_path)
        real_read_bytes = path_type.read_bytes
        target_read = False

        def guarded_read_bytes(path: Path) -> bytes:
            nonlocal target_read
            if path == self.result_path:
                target_read = True
                raise AssertionError("ordinary symlink target read")
            return real_read_bytes(path)

        with mock.patch.object(
            path_type,
            "read_bytes",
            new=guarded_read_bytes,
        ):
            with self.assertRaisesRegex(EvidencePublicationError, "link|reparse"):
                validate_candidate_evidence_pair(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )
        self.assertFalse(target_read)

    def test_canonical_metadata_allows_absent_parent_only_for_restore_probe(
        self,
    ) -> None:
        missing_result = self.test_root / "missing-canonical" / "result.json"
        missing_report = missing_result.with_name("report.md")

        publication_runner._validate_canonical_pair_metadata(
            missing_result,
            missing_report,
            require_entries=False,
        )
        with self.assertRaisesRegex(EvidencePublicationError, "missing|metadata"):
            publication_runner._validate_canonical_pair_metadata(
                missing_result,
                missing_report,
                require_entries=True,
            )

    def test_recovery_handles_disappeared_canonical_parent_for_both_prior_states(
        self,
    ) -> None:
        for previous_pair_present in (False, True):
            with self.subTest(previous_pair_present=previous_pair_present):
                with tempfile.TemporaryDirectory(
                    prefix="emotion-state-missing-canonical-recovery-",
                    dir=ROOT / ".tmp",
                ) as temporary_directory:
                    root = Path(temporary_directory)
                    canonical = root / "canonical"
                    result = canonical / "result.json"
                    report = canonical / "report.md"
                    recovery = root / "recovery"
                    receipt = recovery / "candidate-receipt.json"
                    previous_result = b'{"generation":"previous"}\n'
                    previous_report = b"previous report\n"
                    if previous_pair_present:
                        canonical.mkdir()
                        result.write_bytes(previous_result)
                        report.write_bytes(previous_report)
                    publication_runner.stage_evidence_pair(
                        sample_payload(),
                        mode="material-pending",
                        receipt_path=receipt,
                        result_path=result,
                        report_path=report,
                        recovery_dir=recovery,
                    )
                    result.unlink()
                    report.unlink()
                    canonical.rmdir()

                    outcome = publication_runner.recover_incomplete_publication(
                        result_path=result,
                        report_path=report,
                        recovery_dir=recovery,
                    )

                    self.assertEqual(outcome, "restored")
                    if previous_pair_present:
                        self.assertEqual(result.read_bytes(), previous_result)
                        self.assertEqual(report.read_bytes(), previous_report)
                    else:
                        self.assertFalse(result.exists())
                        self.assertFalse(report.exists())
                    self.assertFalse(receipt.exists())
                    self.assertFalse((recovery / JOURNAL_NAME).exists())

    def test_staging_rejects_canonical_links_before_any_target_access(
        self,
    ) -> None:
        path_type = type(self.result_path)
        real_exists = path_type.exists
        real_iterdir = path_type.iterdir
        real_read_bytes = path_type.read_bytes
        real_open = path_type.open
        real_scandir = os.scandir
        real_replace = os.replace

        for linked_name in ("parent", "result", "report"):
            with self.subTest(linked_name=linked_name):
                with tempfile.TemporaryDirectory(
                    prefix="emotion-state-stage-link-boundary-",
                    dir=ROOT / ".tmp",
                ) as temporary_directory:
                    root = Path(temporary_directory)
                    canonical = root / "canonical"
                    result = canonical / "result.json"
                    report = canonical / "report.md"
                    recovery = root / "recovery"
                    receipt = recovery / "candidate-receipt.json"
                    canonical.mkdir()
                    result.write_bytes(b"previous result\n")
                    report.write_bytes(b"previous report\n")
                    linked_path = {
                        "parent": canonical,
                        "result": result,
                        "report": report,
                    }[linked_name]
                    target_accesses: list[tuple[str, Path]] = []

                    def guarded_exists(path: Path) -> bool:
                        if path in {result, report}:
                            target_accesses.append(("exists", path))
                            raise AssertionError("canonical target exists followed")
                        return real_exists(path)

                    def guarded_read_bytes(path: Path) -> bytes:
                        if path in {result, report}:
                            target_accesses.append(("read", path))
                            raise AssertionError("canonical target read")
                        return real_read_bytes(path)

                    def guarded_iterdir(path: Path):
                        if path == canonical:
                            target_accesses.append(("iterdir", path))
                            raise AssertionError("canonical parent iterated")
                        return real_iterdir(path)

                    def guarded_open(
                        path: Path,
                        *args: object,
                        **kwargs: object,
                    ) -> object:
                        if path in {result, report}:
                            target_accesses.append(("open", path))
                            raise AssertionError("canonical target opened")
                        return real_open(path, *args, **kwargs)

                    def guarded_replace(
                        source: object,
                        destination: object,
                    ) -> None:
                        destination_path = Path(destination)
                        if destination_path in {result, report}:
                            target_accesses.append(("write", destination_path))
                            raise AssertionError("canonical target written")
                        real_replace(source, destination)

                    def guarded_scandir(path: object):
                        if not isinstance(path, int) and Path(path) == canonical:
                            target_accesses.append(("scandir", canonical))
                            raise AssertionError("canonical parent scanned")
                        return real_scandir(path)

                    with (
                        mock.patch.object(
                            publication_runner,
                            "_path_is_link_or_reparse",
                            side_effect=lambda path, status=None: (
                                Path(path) == linked_path
                            ),
                        ),
                        mock.patch.object(
                            path_type,
                            "exists",
                            new=guarded_exists,
                        ),
                        mock.patch.object(
                            path_type,
                            "iterdir",
                            new=guarded_iterdir,
                        ),
                        mock.patch.object(
                            path_type,
                            "read_bytes",
                            new=guarded_read_bytes,
                        ),
                        mock.patch.object(
                            path_type,
                            "open",
                            new=guarded_open,
                        ),
                        mock.patch.object(
                            publication_runner.os,
                            "scandir",
                            side_effect=guarded_scandir,
                        ),
                        mock.patch.object(
                            publication_runner.os,
                            "replace",
                            side_effect=guarded_replace,
                        ),
                    ):
                        with self.assertRaisesRegex(
                            EvidencePublicationError,
                            "link|reparse",
                        ):
                            publication_runner.stage_evidence_pair(
                                sample_payload(),
                                mode="material-pending",
                                receipt_path=receipt,
                                result_path=result,
                                report_path=report,
                                recovery_dir=recovery,
                            )

                    self.assertEqual(target_accesses, [])

    def test_staging_rejects_mocked_intermediate_reparse_before_target_access(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-intermediate-reparse-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            root = Path(temporary_directory)
            intermediate = root / "intermediate"
            canonical = intermediate / "canonical"
            result = canonical / "result.json"
            report = canonical / "report.md"
            recovery = root / "recovery"
            receipt = recovery / "candidate-receipt.json"
            canonical.mkdir(parents=True)
            result.write_bytes(b"previous result\n")
            report.write_bytes(b"previous report\n")
            path_type = type(result)
            real_link_check = publication_runner._path_is_link_or_reparse
            real_exists = path_type.exists
            real_iterdir = path_type.iterdir
            real_mkdir = path_type.mkdir
            real_read_bytes = path_type.read_bytes
            real_open = path_type.open
            real_scandir = os.scandir
            real_replace = os.replace
            target_accesses: list[str] = []

            def is_target(value: object) -> bool:
                if isinstance(value, int):
                    return False
                path = Path(value)
                return path == canonical or canonical in path.parents

            def forbid_path_operation(
                operation: str,
                delegate: object,
            ):
                def guarded(path: Path, *args: object, **kwargs: object):
                    if is_target(path):
                        target_accesses.append(operation)
                        raise AssertionError(
                            f"canonical target {operation} attempted"
                        )
                    return delegate(path, *args, **kwargs)

                return guarded

            def guarded_scandir(path: object):
                if is_target(path):
                    target_accesses.append("scandir")
                    raise AssertionError("canonical target scandir attempted")
                return real_scandir(path)

            def guarded_replace(source: object, destination: object) -> None:
                if is_target(destination):
                    target_accesses.append("replace")
                    raise AssertionError("canonical target replace attempted")
                real_replace(source, destination)

            with (
                mock.patch.object(
                    publication_runner,
                    "_path_is_link_or_reparse",
                    side_effect=lambda path, status=None: (
                        Path(path) == intermediate
                        or real_link_check(Path(path), status=status)
                    ),
                ),
                mock.patch.object(
                    path_type,
                    "exists",
                    new=forbid_path_operation("exists", real_exists),
                ),
                mock.patch.object(
                    path_type,
                    "iterdir",
                    new=forbid_path_operation("iterdir", real_iterdir),
                ),
                mock.patch.object(
                    path_type,
                    "mkdir",
                    new=forbid_path_operation("mkdir", real_mkdir),
                ),
                mock.patch.object(
                    path_type,
                    "read_bytes",
                    new=forbid_path_operation("read", real_read_bytes),
                ),
                mock.patch.object(
                    path_type,
                    "open",
                    new=forbid_path_operation("open", real_open),
                ),
                mock.patch.object(
                    publication_runner.os,
                    "scandir",
                    side_effect=guarded_scandir,
                ),
                mock.patch.object(
                    publication_runner.os,
                    "replace",
                    side_effect=guarded_replace,
                ),
            ):
                with self.assertRaisesRegex(
                    EvidencePublicationError,
                    "link|reparse",
                ):
                    publication_runner.stage_evidence_pair(
                        sample_payload(),
                        mode="material-pending",
                        receipt_path=receipt,
                        result_path=result,
                        report_path=report,
                        recovery_dir=recovery,
                    )

            self.assertEqual(target_accesses, [])

    def test_default_cli_rejects_lexical_intermediate_reparse_before_resolution(
        self,
    ) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        marked_component = publication_runner.DEFAULT_OUTPUT_DIR.parent
        real_link_check = publication_runner._path_is_link_or_reparse
        receipt = (
            publication_runner.DEFAULT_RECOVERY_DIR
            / "synthetic-intermediate-reparse-receipt.json"
        )
        with (
            mock.patch.object(
                publication_runner,
                "_path_is_link_or_reparse",
                side_effect=lambda path, status=None: (
                    Path(path) == marked_component
                    or real_link_check(Path(path), status=status)
                ),
            ),
            mock.patch.object(
                publication_runner,
                "stage_verified_candidate",
                return_value={"acceptance_status": "awaiting_acceptance"},
            ) as stage,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = publication_runner.main([
                "--defer-acceptance",
                "--mode",
                "material-pending",
                "--receipt",
                str(receipt),
            ])

        self.assertEqual(exit_code, 1)
        self.assertIn("link", stderr.getvalue().casefold())
        stage.assert_not_called()

    def test_resolved_alias_survives_lexically_into_staging_validation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-lexical-alias-stage-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            root = Path(temporary_directory)
            allowed_root = root / "allowed"
            alias = allowed_root / "alias"
            redirected_target = allowed_root / "redirected-target"
            alias.mkdir(parents=True)
            redirected_target.mkdir()
            lexical_result = alias / "result.json"
            lexical_report = alias / "report.md"
            redirected_result = redirected_target / "result.json"
            redirected_report = redirected_target / "report.md"
            path_type = type(root)
            real_resolve = path_type.resolve

            def redirected_resolve(
                path: Path,
                strict: bool = False,
            ) -> Path:
                redirects = {
                    lexical_result: redirected_result,
                    lexical_report: redirected_report,
                }
                if path in redirects:
                    return redirects[path]
                return real_resolve(path, strict=strict)

            with mock.patch.object(
                path_type,
                "resolve",
                new=redirected_resolve,
            ):
                resolved_result = publication_runner.resolve_project_path(
                    str(lexical_result),
                    allowed_root=allowed_root,
                )
                resolved_report = publication_runner.resolve_project_path(
                    str(lexical_report),
                    allowed_root=allowed_root,
                )

            self.assertEqual(
                resolved_result,
                Path(os.path.abspath(lexical_result)),
            )
            self.assertEqual(
                resolved_report,
                Path(os.path.abspath(lexical_report)),
            )
            observed_components: list[Path] = []
            real_link_check = publication_runner._path_is_link_or_reparse

            def mark_alias(
                path: Path,
                *,
                status: os.stat_result | None = None,
            ) -> bool:
                component = Path(path)
                observed_components.append(component)
                return (
                    component == alias
                    or real_link_check(component, status=status)
                )

            with mock.patch.object(
                publication_runner,
                "_path_is_link_or_reparse",
                side_effect=mark_alias,
            ):
                with self.assertRaisesRegex(
                    EvidencePublicationError,
                    "link|reparse",
                ):
                    publication_runner.stage_evidence_pair(
                        sample_payload(),
                        mode="material-pending",
                        receipt_path=root / "recovery" / "receipt.json",
                        result_path=resolved_result,
                        report_path=resolved_report,
                        recovery_dir=root / "recovery",
                    )

            self.assertIn(alias, observed_components)

    def test_staging_rejects_ordinary_intermediate_symlink_when_supported(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-intermediate-symlink-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            root = Path(temporary_directory)
            outside = root / "outside"
            canonical = outside / "canonical"
            canonical.mkdir(parents=True)
            result_target = canonical / "result.json"
            report_target = canonical / "report.md"
            result_target.write_bytes(b"outside result\n")
            report_target.write_bytes(b"outside report\n")
            linked_component = root / "linked"
            try:
                linked_component.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(
                    f"intermediate symlink creation unavailable: {exc}"
                )

            with self.assertRaisesRegex(
                EvidencePublicationError,
                "link|reparse",
            ):
                publication_runner.stage_evidence_pair(
                    sample_payload(),
                    mode="material-pending",
                    receipt_path=root / "recovery" / "receipt.json",
                    result_path=linked_component / "canonical" / "result.json",
                    report_path=linked_component / "canonical" / "report.md",
                    recovery_dir=root / "recovery",
                )

            self.assertEqual(result_target.read_bytes(), b"outside result\n")
            self.assertEqual(report_target.read_bytes(), b"outside report\n")

    def test_drift_external_scan_rejects_mocked_link_or_reparse_entry(self) -> None:
        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-link-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            linked_entry = synthetic_root / "data" / "external" / "linked.txt"
            linked_entry.parent.mkdir(parents=True)
            linked_entry.write_text("synthetic entry\n", encoding="utf-8")
            linked_status = linked_entry.lstat()
            real_status_check = (
                check_project_drift._status_is_link_or_reparse
            )
            with mock.patch.object(
                check_project_drift,
                "_status_is_link_or_reparse",
                side_effect=lambda status: (
                    (
                        status.st_mode,
                        status.st_size,
                    )
                    == (
                        linked_status.st_mode,
                        linked_status.st_size,
                    )
                    or real_status_check(status)
                ),
                create=True,
            ):
                with self.assertRaisesRegex(ValueError, "link|reparse"):
                    check_project_drift.iter_scan_files(synthetic_root)

    def test_drift_external_entry_uses_one_supplied_no_follow_snapshot(
        self,
    ) -> None:
        from types import SimpleNamespace

        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-single-snapshot-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_file = Path(temporary_directory) / "synthetic.txt"
            synthetic_file.write_text("synthetic\n", encoding="utf-8")
            supplied_status = synthetic_file.lstat()
            path_type = type(synthetic_file)
            with mock.patch.object(
                path_type,
                "lstat",
                side_effect=AssertionError(
                    "supplied no-follow status was discarded"
                ),
            ):
                returned_status = (
                    check_project_drift._validate_external_scan_entry(
                        synthetic_file,
                        require_directory=False,
                        status=supplied_status,
                    )
                )
                self.assertIs(returned_status, supplied_status)
                with self.assertRaisesRegex(ValueError, "link|reparse"):
                    check_project_drift._validate_external_scan_entry(
                        synthetic_file,
                        require_directory=False,
                        status=SimpleNamespace(
                            st_mode=supplied_status.st_mode,
                            st_file_attributes=0x400,
                        ),
                    )

    def test_drift_external_entry_never_calls_direntry_is_symlink(self) -> None:
        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-direntry-snapshot-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            external_root = synthetic_root / "data" / "external"
            external_root.mkdir(parents=True)
            expected_file = external_root / "synthetic.txt"
            expected_file.write_text("synthetic\n", encoding="utf-8")
            real_scandir = os.scandir

            class GuardedEntry:
                def __init__(self, entry: os.DirEntry[str]) -> None:
                    self._entry = entry
                    self.name = entry.name
                    self.path = entry.path

                def is_symlink(self) -> bool:
                    raise AssertionError(
                        "DirEntry.is_symlink used a second metadata source"
                    )

                def stat(
                    self,
                    *,
                    follow_symlinks: bool = True,
                ) -> os.stat_result:
                    return self._entry.stat(
                        follow_symlinks=follow_symlinks
                    )

            class GuardedScandir:
                def __init__(self, path: object) -> None:
                    self._entries = real_scandir(path)

                def __enter__(self):
                    return iter(
                        GuardedEntry(entry)
                        for entry in self._entries
                    )

                def __exit__(
                    self,
                    exc_type: object,
                    exc_value: object,
                    traceback: object,
                ) -> None:
                    self._entries.close()

            def guarded_scandir(path: object):
                if Path(path) == external_root:
                    return GuardedScandir(path)
                return real_scandir(path)

            with mock.patch.object(
                check_project_drift.os,
                "scandir",
                side_effect=guarded_scandir,
            ):
                scanned = check_project_drift.iter_scan_files(synthetic_root)

            self.assertIn(expected_file, scanned)

    def test_drift_external_scan_rejects_linked_data_ancestor_before_traversal(
        self,
    ) -> None:
        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-data-ancestor-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            data_root = synthetic_root / "data"
            external_root = data_root / "external"
            external_root.mkdir(parents=True)
            (external_root / "synthetic.txt").write_text(
                "synthetic\n",
                encoding="utf-8",
            )
            real_walk = os.walk
            real_scandir = os.scandir
            walk_paths: list[Path] = []
            scandir_paths: list[Path] = []
            data_status = data_root.lstat()
            real_status_check = (
                check_project_drift._status_is_link_or_reparse
            )

            def guarded_walk(path: object, *args: object, **kwargs: object):
                walk_paths.append(Path(path))
                return real_walk(path, *args, **kwargs)

            def guarded_scandir(path: object):
                if not isinstance(path, int):
                    scandir_paths.append(Path(path))
                return real_scandir(path)

            with (
                mock.patch.object(
                    check_project_drift,
                    "_status_is_link_or_reparse",
                    side_effect=lambda status: (
                        (
                            status.st_dev,
                            status.st_ino,
                        )
                        == (
                            data_status.st_dev,
                            data_status.st_ino,
                        )
                        or real_status_check(status)
                    ),
                ),
                mock.patch.object(
                    check_project_drift.os,
                    "walk",
                    side_effect=guarded_walk,
                ),
                mock.patch.object(
                    check_project_drift.os,
                    "scandir",
                    side_effect=guarded_scandir,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "link|reparse"):
                    check_project_drift.iter_scan_files(synthetic_root)

            self.assertEqual(walk_paths, [])
            self.assertEqual(scandir_paths, [])

    def test_drift_external_scan_uses_manual_scandir_not_os_walk(self) -> None:
        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-manual-scandir-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            external_root = synthetic_root / "data" / "external"
            nested_root = external_root / "nested"
            nested_root.mkdir(parents=True)
            expected_file = nested_root / "synthetic.txt"
            expected_file.write_text("synthetic\n", encoding="utf-8")
            real_walk = os.walk
            external_walk_attempted = False

            def reject_external_walk(
                path: object,
                *args: object,
                **kwargs: object,
            ):
                nonlocal external_walk_attempted
                if Path(path) == external_root:
                    external_walk_attempted = True
                    raise AssertionError("os.walk used for data/external")
                return real_walk(path, *args, **kwargs)

            with mock.patch.object(
                check_project_drift.os,
                "walk",
                side_effect=reject_external_walk,
            ):
                scanned = check_project_drift.iter_scan_files(synthetic_root)

            self.assertFalse(external_walk_attempted)
            self.assertIn(expected_file, scanned)

    def test_drift_external_scan_treats_only_file_not_found_as_absence(
        self,
    ) -> None:
        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-data-inspection-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            data_root = synthetic_root / "data"
            (data_root / "external").mkdir(parents=True)
            path_type = type(data_root)
            real_lstat = path_type.lstat

            def guarded_lstat(path: Path):
                if path == data_root:
                    raise PermissionError("synthetic data ancestor denial")
                return real_lstat(path)

            with mock.patch.object(
                path_type,
                "lstat",
                new=guarded_lstat,
            ):
                with self.assertRaisesRegex(ValueError, "inspect"):
                    check_project_drift.iter_scan_files(synthetic_root)

    def test_drift_external_scan_rejects_ordinary_symlink_when_supported(
        self,
    ) -> None:
        from scripts import check_project_drift

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-drift-symlink-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            external_root = synthetic_root / "data" / "external"
            external_root.mkdir(parents=True)
            outside_file = synthetic_root / "outside.txt"
            outside_file.write_text("outside synthetic bytes\n", encoding="utf-8")
            linked_entry = external_root / "linked.txt"
            try:
                linked_entry.symlink_to(outside_file)
            except OSError as exc:
                self.skipTest(f"ordinary symlink creation unavailable: {exc}")

            with self.assertRaisesRegex(ValueError, "link|reparse"):
                check_project_drift.iter_scan_files(synthetic_root)

    def test_acceptance_digest_failure_force_restores_previous_pair(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            EvidencePublicationError,
            accept_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        self.result_path.write_bytes(b"tampered candidate result")

        with self.assertRaisesRegex(EvidencePublicationError, "digest"):
            accept_evidence_receipt(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_candidate_readback_rejects_report_marker_and_journal_digest_tamper(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        self._seed_previous_pair()
        self._stage()
        journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        result_digest = journal["candidate_pair"]["result_sha256"]
        report_bytes = self.report_path.read_bytes().replace(
            result_digest.encode("ascii"),
            b"A" * 64,
        )
        self.report_path.write_bytes(report_bytes)
        report_digest = hashlib.sha256(report_bytes).hexdigest().upper()
        journal["candidate_pair"]["report_sha256"] = report_digest
        receipt["candidate_report_sha256"] = report_digest
        self.journal_path.write_text(
            json.dumps(journal, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(EvidencePublicationError, "marker"):
            validate_candidate_evidence_pair(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

    def test_candidate_readback_rejects_previous_pair_metadata_tamper(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        self._seed_previous_pair()
        self._stage()
        journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        journal["previous_pair"]["result_sha256"] = "A" * 64
        receipt["previous_result_sha256"] = "A" * 64
        self.journal_path.write_text(
            json.dumps(journal, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(EvidencePublicationError, "backup digest"):
            validate_candidate_evidence_pair(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

    def test_candidate_readback_rejects_independent_digest_and_presence_tamper(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            validate_candidate_evidence_pair,
        )

        for mutation in (
            "journal_only_candidate_report_digest",
            "previous_report_digest",
            "previous_pair_presence",
        ):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory(
                    prefix="emotion-state-candidate-metadata-tamper-",
                    dir=ROOT / ".tmp",
                ) as temporary_directory:
                    root = Path(temporary_directory)
                    canonical = root / "canonical"
                    result = canonical / "result.json"
                    report = canonical / "report.md"
                    recovery = root / "recovery"
                    receipt_path = recovery / "candidate-receipt.json"
                    canonical.mkdir()
                    result.write_bytes(b"previous result\n")
                    report.write_bytes(b"previous report\n")
                    publication_runner.stage_evidence_pair(
                        sample_payload(),
                        mode="material-pending",
                        receipt_path=receipt_path,
                        result_path=result,
                        report_path=report,
                        recovery_dir=recovery,
                    )
                    journal_path = recovery / JOURNAL_NAME
                    journal = json.loads(
                        journal_path.read_text(encoding="utf-8")
                    )
                    receipt = json.loads(
                        receipt_path.read_text(encoding="utf-8")
                    )
                    if mutation == "journal_only_candidate_report_digest":
                        journal["candidate_pair"]["report_sha256"] = "C" * 64
                    elif mutation == "previous_report_digest":
                        journal["previous_pair"]["report_sha256"] = "C" * 64
                        receipt["previous_report_sha256"] = "C" * 64
                    else:
                        journal["previous_pair"] = {
                            "present": False,
                            "result_sha256": None,
                            "report_sha256": None,
                        }
                        receipt["previous_pair_present"] = False
                        receipt["previous_result_sha256"] = None
                        receipt["previous_report_sha256"] = None
                    journal_path.write_text(
                        json.dumps(journal, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    receipt_path.write_text(
                        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )

                    with self.assertRaises(EvidencePublicationError):
                        validate_candidate_evidence_pair(
                            receipt_path,
                            result_path=result,
                            report_path=report,
                            recovery_dir=recovery,
                        )

    def test_acceptance_receipt_failure_force_restores_previous_pair(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            EvidencePublicationError,
            accept_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        receipt["candidate_result_sha256"] = "A" * 64
        self.receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(EvidencePublicationError, "does not match"):
            accept_evidence_receipt(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_malformed_journal_acceptance_restores_previous_pair_then_errors(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        self.journal_path.write_bytes(b"{malformed journal")

        with self.assertRaisesRegex(
            EvidencePublicationError,
            "valid matching journal.*restored",
        ):
            accept_evidence_receipt(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_malformed_journal_acceptance_without_previous_pair_removes_candidate(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        self._stage()
        self.journal_path.write_bytes(b"{malformed journal")

        with self.assertRaisesRegex(
            EvidencePublicationError,
            "valid matching journal.*restored",
        ):
            accept_evidence_receipt(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())
        self._assert_transaction_clean()

    def test_malformed_journal_acceptance_retry_cleans_already_restored_pair(
        self,
    ) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        self.journal_path.write_bytes(b"{malformed journal")
        result_backup = next(self.recovery_dir.glob("*.result.backup"))
        report_backup = next(self.recovery_dir.glob("*.report.backup"))
        path_type = type(report_backup)
        real_unlink = path_type.unlink
        cleanup_interrupted = False

        def interrupt_cleanup_after_restoration(
            path: Path,
            missing_ok: bool = False,
        ) -> None:
            nonlocal cleanup_interrupted
            if path == report_backup and not cleanup_interrupted:
                cleanup_interrupted = True
                raise OSError("simulated receipt-recovery cleanup interruption")
            real_unlink(path, missing_ok=missing_ok)

        with patch.object(path_type, "unlink", new=interrupt_cleanup_after_restoration):
            with self.assertRaisesRegex(
                EvidencePublicationError,
                "restoration failed",
            ):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        self.assertTrue(cleanup_interrupted)
        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self.assertFalse(result_backup.exists())
        self.assertTrue(report_backup.exists())
        self.assertTrue(self.receipt_path.exists())
        self.assertTrue(self.journal_path.exists())

        with self.assertRaisesRegex(
            EvidencePublicationError,
            "valid matching journal.*restored",
        ):
            accept_evidence_receipt(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_valid_acceptance_keeps_candidate_and_cleans_transaction(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
            verify_evidence_pair_bytes,
        )

        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()

        accept_evidence_receipt(
            self.receipt_path,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        verify_evidence_pair_bytes(candidate_result, candidate_report)
        self._assert_transaction_clean()

    def test_reject_force_restores_valid_candidate(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            reject_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        verify_evidence_pair_bytes(
            self.result_path.read_bytes(),
            self.report_path.read_bytes(),
        )

        reject_evidence_receipt(
            self.receipt_path,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_malformed_journal_rejection_restores_from_exact_receipt(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            reject_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        self.journal_path.write_bytes(b"{malformed journal")

        reject_evidence_receipt(
            self.receipt_path,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_awaiting_acceptance_recovery_restores_previous_pair(self) -> None:
        previous_result, previous_report = self._seed_previous_pair()
        self._stage()

        outcome = recover_incomplete_publication(
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(outcome, "restored")
        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_malformed_journal_startup_discovers_one_exact_receipt_and_restores(
        self,
    ) -> None:
        previous_result, previous_report = self._seed_previous_pair()
        self._stage()
        self.journal_path.write_bytes(b"{malformed journal")

        outcome = recover_incomplete_publication(
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(outcome, "restored")
        self.assertEqual(self.result_path.read_bytes(), previous_result)
        self.assertEqual(self.report_path.read_bytes(), previous_report)
        self._assert_transaction_clean()

    def test_malformed_journal_startup_retry_cleans_already_restored_absence(
        self,
    ) -> None:
        receipt = self._stage()
        self.journal_path.write_bytes(b"{malformed journal")
        restore_result = self.recovery_dir / (
            f"{receipt['transaction_id']}.result.restore"
        )
        path_type = type(restore_result)
        real_unlink = path_type.unlink
        cleanup_interrupted = False

        def interrupt_cleanup_after_absence_restoration(
            path: Path,
            missing_ok: bool = False,
        ) -> None:
            nonlocal cleanup_interrupted
            if path == restore_result and not cleanup_interrupted:
                cleanup_interrupted = True
                raise OSError("simulated absence cleanup interruption")
            real_unlink(path, missing_ok=missing_ok)

        with patch.object(
            path_type,
            "unlink",
            new=interrupt_cleanup_after_absence_restoration,
        ):
            with self.assertRaisesRegex(
                EvidencePublicationError,
                "receipt recovery failed",
            ):
                recover_incomplete_publication(
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        self.assertTrue(cleanup_interrupted)
        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())
        self.assertTrue(self.receipt_path.exists())
        self.assertTrue(self.journal_path.exists())

        self.assertEqual(
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            ),
            "restored",
        )
        self.assertFalse(self.result_path.exists())
        self.assertFalse(self.report_path.exists())
        self._assert_transaction_clean()

    def test_ambiguous_receipt_recovery_retains_candidate_and_all_artifacts(
        self,
    ) -> None:
        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()
        self.journal_path.write_bytes(b"{malformed journal")
        second_receipt = self.recovery_dir / "second-safe-receipt.json"
        second_receipt.write_bytes(self.receipt_path.read_bytes())
        recovery_evidence = {
            path.name: path.read_bytes()
            for path in self.recovery_dir.iterdir()
            if path.is_file()
        }

        with self.assertRaisesRegex(EvidencePublicationError, "receipt recovery failed"):
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        self.assertEqual(
            {
                path.name: path.read_bytes()
                for path in self.recovery_dir.iterdir()
                if path.is_file()
            },
            recovery_evidence,
        )

    def test_malformed_journal_and_receipt_fail_closed_with_evidence_retained(
        self,
    ) -> None:
        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()
        self.journal_path.write_bytes(b"{malformed journal")
        self.receipt_path.write_bytes(b"{malformed receipt")
        recovery_evidence = {
            path.name: path.read_bytes()
            for path in self.recovery_dir.iterdir()
            if path.is_file()
        }

        with self.assertRaisesRegex(EvidencePublicationError, "receipt"):
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        self.assertEqual(
            {
                path.name: path.read_bytes()
                for path in self.recovery_dir.iterdir()
                if path.is_file()
            },
            recovery_evidence,
        )

    def test_interrupted_accepted_cleanup_finishes_candidate(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts._cleanup_transaction",
            side_effect=OSError("simulated accepted-state cleanup interruption"),
        ):
            with self.assertRaisesRegex(OSError, "cleanup interruption"):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        self.assertEqual(journal["acceptance_status"], "accepted")
        self.assertEqual(
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            ),
            "committed",
        )
        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        self._assert_transaction_clean()

    def test_recovery_never_rolls_back_invalid_accepted_candidate(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        previous_result, previous_report = self._seed_previous_pair()
        self._stage()

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts._cleanup_transaction",
            side_effect=OSError("simulated accepted-state cleanup interruption"),
        ):
            with self.assertRaisesRegex(OSError, "cleanup interruption"):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        accepted_report = self.report_path.read_bytes()
        tampered_result = b'{"accepted":"tampered"}\n'
        self.result_path.write_bytes(tampered_result)
        recovery_before = {
            path.name: path.read_bytes()
            for path in self.recovery_dir.iterdir()
            if path.is_file()
        }
        with self.assertRaisesRegex(EvidencePublicationError, "accepted"):
            recover_incomplete_publication(
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), tampered_result)
        self.assertEqual(self.report_path.read_bytes(), accepted_report)
        self.assertNotEqual(self.result_path.read_bytes(), previous_result)
        self.assertNotEqual(self.report_path.read_bytes(), previous_report)
        self.assertTrue(self.journal_path.exists())
        self.assertTrue(self.receipt_path.exists())
        self.assertEqual(
            {
                path.name: path.read_bytes()
                for path in self.recovery_dir.iterdir()
                if path.is_file()
            },
            recovery_before,
        )

    def test_archive_sha256_is_builder_owned_and_collision_blocked(self) -> None:
        from scripts import emotion_state_phase_a_contracts as contracts

        manifest = {
            "archive_sha256": EXPECTED_ARCHIVE_SHA256,
            "source_repository_url": (
                "https://github.com/WisdomBreathes/creative-analysis-engine"
            ),
            "source_repository_url_status": "verified_read_only",
            "source_branch": "dev",
            "source_revision": "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
            "source_revision_status": "verified_read_only",
            "observed_license": None,
            "observed_license_status": "absent_in_reviewed_root",
            "runtime_dependency_added": False,
            "project_local_only": True,
            "copied_material": [],
            "translated_material": [],
            "adapted_material": [],
            "independently_reimplemented_material": [],
            "adaptation_allowed": False,
            "phase_b_approval": {"approved": False},
            "reviewed_files": EXPECTED_REVIEWED_FILES,
        }
        with tempfile.TemporaryDirectory(
            prefix="emotion-state-builder-collision-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            synthetic_root = Path(temporary_directory)
            with mock.patch.object(
                contracts,
                "read_json",
                side_effect=(dict(EXPECTED_CASE), manifest),
            ):
                with self.assertRaisesRegex(ValueError, "collides"):
                    contracts.build_phase_a_payload(
                        synthetic_root / "case.json",
                        root=synthetic_root,
                        verification_evidence={"archive_sha256": "A" * 64},
                    )

    def test_accept_retry_finishes_accepted_cleanup_without_rollback(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts._cleanup_transaction",
            side_effect=OSError("simulated accepted-state cleanup interruption"),
        ):
            with self.assertRaisesRegex(OSError, "cleanup interruption"):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        accept_evidence_receipt(
            self.receipt_path,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        self._assert_transaction_clean()

    def test_accept_retry_allows_missing_receipt_after_accepted_cleanup(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
        )

        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts._cleanup_transaction",
            side_effect=OSError("simulated accepted-state cleanup interruption"),
        ):
            with self.assertRaisesRegex(OSError, "cleanup interruption"):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )
        self.receipt_path.unlink()

        accept_evidence_receipt(
            self.receipt_path,
            result_path=self.result_path,
            report_path=self.report_path,
            recovery_dir=self.recovery_dir,
        )

        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        self._assert_transaction_clean()

    def test_reject_refuses_accepted_transaction_without_rollback(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            accept_evidence_receipt,
            reject_evidence_receipt,
        )

        self._seed_previous_pair()
        self._stage()
        candidate_result = self.result_path.read_bytes()
        candidate_report = self.report_path.read_bytes()

        with patch(
            "scripts.run_emotion_state_001_phase_a_contracts._cleanup_transaction",
            side_effect=OSError("simulated accepted-state cleanup interruption"),
        ):
            with self.assertRaisesRegex(OSError, "cleanup interruption"):
                accept_evidence_receipt(
                    self.receipt_path,
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                )

        with self.assertRaisesRegex(EvidencePublicationError, "accepted"):
            reject_evidence_receipt(
                self.receipt_path,
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

        self.assertEqual(self.result_path.read_bytes(), candidate_result)
        self.assertEqual(self.report_path.read_bytes(), candidate_report)
        self._assert_transaction_clean()

    def test_transaction_and_receipt_discriminators_are_type_strict(self) -> None:
        self._seed_previous_pair()
        self._stage()
        original_journal = json.loads(self.journal_path.read_text(encoding="utf-8"))
        original_receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))

        journal_mutations = {
            "schema_version": lambda value: value.__setitem__(
                "schema_version",
                "2",
            ),
            "transaction_id": lambda value: value.__setitem__(
                "transaction_id",
                [],
            ),
            "mode": lambda value: value.__setitem__("mode", []),
            "acceptance_status": lambda value: value.__setitem__(
                "acceptance_status",
                {},
            ),
            "previous_pair_present": lambda value: value["previous_pair"].__setitem__(
                "present",
                1,
            ),
            "previous_result_sha256": lambda value: value["previous_pair"].__setitem__(
                "result_sha256",
                [],
            ),
            "previous_report_sha256": lambda value: value["previous_pair"].__setitem__(
                "report_sha256",
                {},
            ),
            "candidate_result_sha256": lambda value: value["candidate_pair"].__setitem__(
                "result_sha256",
                [],
            ),
            "candidate_report_sha256": lambda value: value["candidate_pair"].__setitem__(
                "report_sha256",
                {},
            ),
        }
        for label, mutate in journal_mutations.items():
            with self.subTest(journal_field=label):
                journal = json.loads(json.dumps(original_journal))
                mutate(journal)
                self.journal_path.write_text(
                    json.dumps(journal, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(EvidencePublicationError):
                    publication_runner._load_transaction(self.journal_path)

        self.journal_path.write_text(
            json.dumps(original_journal, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        receipt_mutations = {
            "schema_version": ("schema_version", "2"),
            "transaction_id": ("transaction_id", []),
            "candidate_result_sha256": ("candidate_result_sha256", []),
            "candidate_report_sha256": ("candidate_report_sha256", {}),
            "previous_pair_present": ("previous_pair_present", 1),
            "previous_result_sha256": ("previous_result_sha256", []),
            "previous_report_sha256": ("previous_report_sha256", {}),
            "mode": ("mode", []),
        }
        for label, (field, value) in receipt_mutations.items():
            with self.subTest(receipt_field=label):
                receipt = json.loads(json.dumps(original_receipt))
                receipt[field] = value
                self.receipt_path.write_text(
                    json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaises(EvidencePublicationError):
                    publication_runner._load_receipt(self.receipt_path)

        with self.assertRaises(EvidencePublicationError):
            publication_runner.stage_evidence_pair(
                sample_payload(),
                mode=[],
                receipt_path=self.recovery_dir / "wrong-mode-receipt.json",
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
            )

    def test_material_pending_main_uses_fixed_default_material_root(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        receipt_path = (
            publication_runner.DEFAULT_RECOVERY_DIR / "task-7-default-root-test.json"
        )
        expected_material_root = (
            publication_runner.ROOT / "data" / "public" / "emotion-state"
        )

        with (
            patch.object(
                publication_runner,
                "stage_verified_candidate",
                return_value={"acceptance_status": "awaiting_acceptance"},
            ) as stage,
            patch.object(
                publication_runner,
                "_current_repository_head",
                return_value="c" * 40,
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = publication_runner.main(
                [
                    "--defer-acceptance",
                    "--mode",
                    "material-pending",
                    "--receipt",
                    str(receipt_path),
                ]
            )

        self.assertEqual(exit_code, 0, stderr.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            stage.call_args.kwargs["material_root"],
            expected_material_root,
        )

    def test_accept_reject_cli_dispatch_never_checks_material_root(self) -> None:
        receipt_path = (
            publication_runner.DEFAULT_RECOVERY_DIR
            / "task-7-cli-dispatch-test.json"
        )
        material_root = (
            publication_runner.ROOT / "data" / "public" / "emotion-state"
        )
        path_type = type(material_root)
        real_exists = path_type.exists
        real_is_dir = path_type.is_dir
        real_iterdir = path_type.iterdir
        real_read_bytes = path_type.read_bytes
        real_open = path_type.open

        def is_material_path(path: Path) -> bool:
            return path == material_root or material_root in path.parents

        def guarded_path_call(
            operation: str,
            delegate: object,
        ):
            def guarded(path: Path, *args: object, **kwargs: object):
                if is_material_path(path):
                    raise AssertionError(
                        f"accept/reject attempted material {operation}"
                    )
                return delegate(path, *args, **kwargs)

            return guarded

        project_paths = (
            publication_runner.DEFAULT_CASE.resolve(strict=False),
            publication_runner.DEFAULT_RESULT.resolve(strict=False),
            publication_runner.DEFAULT_REPORT.resolve(strict=False),
        )
        for action, handler_name, expected_status in (
            ("--accept-receipt", "accept_evidence_receipt", "accepted"),
            ("--reject-receipt", "reject_evidence_receipt", "rejected"),
        ):
            with self.subTest(action=action):
                stdout = io.StringIO()
                stderr = io.StringIO()
                lock = mock.MagicMock()
                with (
                    patch.object(
                        publication_runner,
                        "resolve_project_path",
                        side_effect=project_paths,
                    ),
                    patch.object(
                        publication_runner,
                        "resolve_receipt_path",
                        return_value=receipt_path,
                    ) as resolve_receipt,
                    patch.object(
                        publication_runner,
                        "publication_lock",
                        return_value=lock,
                    ),
                    patch.object(
                        publication_runner,
                        handler_name,
                    ) as handler,
                    patch.object(
                        publication_runner,
                        "validate_material_pending_dataset_absence",
                    ) as absence,
                    patch.object(
                        publication_runner,
                        "stage_evidence_pair",
                    ) as stage_pair,
                    patch.object(
                        publication_runner,
                        "stage_verified_candidate",
                    ) as stage_verified,
                    patch.object(
                        path_type,
                        "exists",
                        new=guarded_path_call("exists", real_exists),
                    ),
                    patch.object(
                        path_type,
                        "is_dir",
                        new=guarded_path_call("is_dir", real_is_dir),
                    ),
                    patch.object(
                        path_type,
                        "iterdir",
                        new=guarded_path_call("iterdir", real_iterdir),
                    ),
                    patch.object(
                        path_type,
                        "read_bytes",
                        new=guarded_path_call("read", real_read_bytes),
                    ),
                    patch.object(
                        path_type,
                        "open",
                        new=guarded_path_call("open", real_open),
                    ),
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                ):
                    exit_code = publication_runner.main(
                        [action, str(receipt_path)]
                    )

                self.assertEqual(exit_code, 0, stderr.getvalue())
                self.assertEqual(
                    json.loads(stdout.getvalue())["acceptance_status"],
                    expected_status,
                )
                resolve_receipt.assert_called()
                handler.assert_called_once()
                absence.assert_not_called()
                stage_pair.assert_not_called()
                stage_verified.assert_not_called()

    def test_stage_uses_accepted_verification_lease_apis_in_order(self) -> None:
        from scripts.run_emotion_state_001_phase_a_contracts import (
            stage_verified_candidate,
        )

        events: list[str] = []
        prepared = object()
        capability = object()
        verification_evidence = {"verification_run_id": "A" * 64}
        lock = mock.MagicMock()
        lock.__enter__.return_value = capability
        payload = sample_payload()
        material_root = self.test_root / "synthetic-material-root"

        with (
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "validate_material_pending_dataset_absence",
                side_effect=lambda *_args, **_kwargs: events.append("absence"),
            ) as absence,
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "prepare_verification_evidence",
                side_effect=lambda *_args, **_kwargs: (
                    events.append("prepare") or prepared
                ),
            ),
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "persistent_verification_lock",
                side_effect=lambda *_args, **_kwargs: (
                    events.append("lock") or lock
                ),
            ),
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "finalize_verification_evidence",
                side_effect=lambda *_args, **_kwargs: (
                    events.append("finalize") or verification_evidence
                ),
            ),
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "validate_active_verification_lock",
                side_effect=lambda *_args, **_kwargs: events.append("lease"),
            ),
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "recover_incomplete_publication",
                side_effect=lambda *_args, **_kwargs: events.append("recover"),
            ),
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts."
                "_current_repository_head",
                side_effect=lambda *_args, **_kwargs: (
                    events.append("head") or "c" * 40
                ),
            ),
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts.build_phase_a_payload",
                side_effect=lambda *_args, **_kwargs: (
                    events.append("payload") or payload
                ),
            ) as build_payload,
            patch(
                "scripts.run_emotion_state_001_phase_a_contracts.stage_evidence_pair",
                side_effect=lambda *_args, **_kwargs: events.append("stage") or {},
            ),
        ):
            stage_verified_candidate(
                root=self.test_root,
                case_path=self.test_root / "case.json",
                result_path=self.result_path,
                report_path=self.report_path,
                recovery_dir=self.recovery_dir,
                receipt_path=self.receipt_path,
                material_root=material_root,
                baseline_commit="b" * 40,
                head_commit="c" * 40,
                mode="material-pending",
            )

        self.assertEqual(
            events,
            [
                "absence",
                "recover",
                "head",
                "prepare",
                "lock",
                "recover",
                "finalize",
                "payload",
                "head",
                "lease",
                "absence",
                "stage",
            ],
        )
        self.assertIs(
            build_payload.call_args.kwargs["verification_evidence"],
            verification_evidence,
        )
        self.assertEqual(
            publication_runner.MATERIAL_PENDING_DATASET_DIRECTORIES,
            {
                "crema-d-v1.0-audio-wav": "crema-d-v1.0",
                "ami-manual-annotations-v1.6.2": (
                    "ami-manual-annotations-v1.6.2"
                ),
            },
        )
        self.assertEqual(absence.call_count, 2)
        self.assertEqual(
            [call.args[0] for call in absence.call_args_list],
            [material_root, material_root],
        )

    def test_first_material_failure_recovers_once_then_reraises(self) -> None:
        lock = mock.MagicMock()
        with (
            patch.object(
                publication_runner,
                "validate_material_pending_dataset_absence",
                side_effect=ValueError("synthetic material is present"),
            ) as absence,
            patch.object(
                publication_runner,
                "publication_lock",
                return_value=lock,
            ),
            patch.object(
                publication_runner,
                "recover_incomplete_publication",
            ) as recover,
            patch.object(
                publication_runner,
                "prepare_verification_evidence",
            ) as prepare,
        ):
            with self.assertRaisesRegex(ValueError, "synthetic material is present"):
                publication_runner.stage_verified_candidate(
                    root=self.test_root,
                    case_path=self.test_root / "case.json",
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                    receipt_path=self.receipt_path,
                    material_root=self.test_root / "synthetic-material-root",
                    baseline_commit="b" * 40,
                    head_commit="c" * 40,
                    mode="material-pending",
                )

        absence.assert_called_once()
        recover.assert_called_once()
        prepare.assert_not_called()

    def test_repository_head_move_prevents_second_absence_and_staging(self) -> None:
        lock = mock.MagicMock()
        lock.__enter__.return_value = object()
        expected_head = "c" * 40
        moved_head = "d" * 40
        with (
            patch.object(
                publication_runner,
                "validate_material_pending_dataset_absence",
            ) as absence,
            patch.object(
                publication_runner,
                "publication_lock",
                return_value=mock.MagicMock(),
            ),
            patch.object(
                publication_runner,
                "recover_incomplete_publication",
            ),
            patch.object(
                publication_runner,
                "_current_repository_head",
                side_effect=(expected_head, moved_head),
            ),
            patch.object(
                publication_runner,
                "prepare_verification_evidence",
                return_value=object(),
            ),
            patch.object(
                publication_runner,
                "persistent_verification_lock",
                return_value=lock,
            ),
            patch.object(
                publication_runner,
                "finalize_verification_evidence",
                return_value=sample_verification_evidence(),
            ),
            patch.object(
                publication_runner,
                "build_phase_a_payload",
                return_value=sample_payload(),
            ),
            patch.object(
                publication_runner,
                "validate_active_verification_lock",
            ) as lease,
            patch.object(
                publication_runner,
                "stage_evidence_pair",
            ) as stage,
        ):
            with self.assertRaisesRegex(ValueError, "HEAD"):
                publication_runner.stage_verified_candidate(
                    root=self.test_root,
                    case_path=self.test_root / "case.json",
                    result_path=self.result_path,
                    report_path=self.report_path,
                    recovery_dir=self.recovery_dir,
                    receipt_path=self.receipt_path,
                    material_root=self.test_root / "synthetic-material-root",
                    baseline_commit="b" * 40,
                    head_commit=expected_head,
                    mode="material-pending",
                )

        self.assertEqual(absence.call_count, 1)
        lease.assert_not_called()
        stage.assert_not_called()


class ValidatorTimeoutTests(unittest.TestCase):
    @staticmethod
    def _prepublication_validators():
        return patch.multiple(
            phase_a_validator,
            validate_source=mock.DEFAULT,
            validate_contracts=mock.DEFAULT,
            validate_split_v2=mock.DEFAULT,
            validate_cohort=mock.DEFAULT,
            validate_patterns=mock.DEFAULT,
            validate_brain_extension=mock.DEFAULT,
        )

    @classmethod
    def _prepublication_baseline_call_count(
        cls,
        sitecustomize: object,
    ) -> int:
        policy_path = ROOT / (
            "research/sources/emotion_state/"
            "phase_a_verification_guard_policy.json"
        )
        with patch.dict(
            phase_a_validator.os.environ,
            {
                "EMOTION_STATE_PHASE_A_GUARD_POLICY": str(policy_path),
                "EMOTION_STATE_PHASE_A_PROJECT_ROOT": str(ROOT),
            },
        ), patch.dict(
            phase_a_validator.sys.modules,
            {"sitecustomize": sitecustomize},
        ), cls._prepublication_validators(), patch.object(
            phase_a_validator.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(
                ["baseline-validator"], 0, stdout="", stderr=""
            ),
        ) as baseline_gate:
            phase_a_validator.validate_prepublication_inputs("material-pending")
        return baseline_gate.call_count

    def test_phase_a_prepublication_active_guard_does_not_relaunch_baseline(
        self,
    ) -> None:
        guard_module = mock.Mock(
            __file__=str(
                ROOT
                / "scripts/emotion_state_phase_a_guard_site/sitecustomize.py"
            ),
            _GuardedPopen=phase_a_validator.subprocess.Popen,
        )
        self.assertEqual(
            self._prepublication_baseline_call_count(guard_module),
            0,
        )

    def test_phase_a_prepublication_environment_anchors_alone_do_not_bypass(
        self,
    ) -> None:
        self.assertEqual(
            self._prepublication_baseline_call_count(None),
            1,
        )

    def test_exp_runner_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch(
            "scripts.validate_exp_002_frozen_response_baseline.subprocess.run",
            side_effect=timeout,
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = exp_validator.main()

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "EXP-002 frozen-response baseline validation failed:",
            stdout.getvalue(),
        )
        self.assertIn("timed out after 60 seconds", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_exp_prompt_render_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        completed = subprocess.CompletedProcess(
            ["stable-test-label"],
            returncode=0,
            stdout="",
            stderr="",
        )
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch(
            "scripts.validate_exp_002_frozen_response_baseline.subprocess.run",
            side_effect=[completed, timeout],
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = exp_validator.main()

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "EXP-002 frozen-response baseline validation failed:",
            stdout.getvalue(),
        )
        self.assertIn("timed out after 60 seconds", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_phase_a_brain_validator_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch.object(
            phase_a_validator.sys,
            "argv",
            ["validator", "--section", "brain"],
        ), patch.dict(
            phase_a_validator.sys.modules,
            {"sitecustomize": None},
        ), patch(
            "scripts.validate_emotion_state_001_phase_a_contracts.subprocess.run",
            side_effect=timeout,
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = phase_a_validator.main()

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "EMOTION-STATE-001 Phase A validation failed:",
            stdout.getvalue(),
        )
        self.assertIn("timed out after 60 seconds", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_phase_a_prepublication_baseline_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch.object(
            phase_a_validator.sys,
            "argv",
            [
                "validator",
                "--section",
                "prepublication",
                "--mode",
                "material-pending",
            ],
        ), patch.dict(
            phase_a_validator.sys.modules,
            {"sitecustomize": None},
        ), self._prepublication_validators(), patch(
            "scripts.validate_emotion_state_001_phase_a_contracts.subprocess.run",
            side_effect=timeout,
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = phase_a_validator.main()

        self.assertEqual(exit_code, 1)
        self.assertIn(
            "EMOTION-STATE-001 Phase A validation failed:",
            stdout.getvalue(),
        )
        self.assertIn("timed out after 60 seconds", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_phase_a_checkpoint_readback_never_launches_subprocess(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-checkpoint-timeout-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            root = Path(temporary_directory)
            result = root / "canonical" / "result.json"
            report = result.with_name("report.md")
            recovery = root / "recovery"
            publish_evidence_pair(
                sample_payload(),
                result_path=result,
                report_path=report,
                recovery_dir=recovery,
            )
            with patch.object(
                phase_a_validator.sys,
                "argv",
                ["validator", "--section", "checkpoint"],
            ), patch.object(
                phase_a_validator,
                "RESULT",
                result,
            ), patch.object(
                phase_a_validator,
                "REPORT",
                report,
            ), patch.object(
                phase_a_validator,
                "RECOVERY_DIR",
                recovery,
            ), patch(
                "scripts.validate_emotion_state_001_phase_a_contracts.subprocess.run",
                side_effect=timeout,
            ) as run, redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = phase_a_validator.main()

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "EMOTION-STATE-001 Phase A validation passed: checkpoint",
            stdout.getvalue(),
        )
        run.assert_not_called()
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_phase_a_candidate_readback_never_launches_subprocess(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-candidate-timeout-",
            dir=ROOT / ".tmp",
        ) as temporary_directory:
            root = Path(temporary_directory)
            result = root / "canonical" / "result.json"
            report = result.with_name("report.md")
            recovery = root / "recovery"
            receipt = recovery / "candidate-receipt.json"
            from scripts.run_emotion_state_001_phase_a_contracts import (
                stage_evidence_pair,
            )

            stage_evidence_pair(
                sample_payload(),
                mode="material-pending",
                receipt_path=receipt,
                result_path=result,
                report_path=report,
                recovery_dir=recovery,
            )
            with patch.object(
                phase_a_validator.sys,
                "argv",
                [
                    "validator",
                    "--section",
                    "candidate",
                    "--receipt",
                    str(receipt),
                ],
            ), patch.object(
                phase_a_validator,
                "RESULT",
                result,
            ), patch.object(
                phase_a_validator,
                "REPORT",
                report,
            ), patch.object(
                phase_a_validator,
                "RECOVERY_DIR",
                recovery,
            ), patch(
                "scripts.validate_emotion_state_001_phase_a_contracts.subprocess.run",
                side_effect=timeout,
            ) as run, redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = phase_a_validator.main()

        self.assertEqual(exit_code, 0)
        self.assertIn(
            "EMOTION-STATE-001 Phase A validation passed: candidate",
            stdout.getvalue(),
        )
        run.assert_not_called()
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
