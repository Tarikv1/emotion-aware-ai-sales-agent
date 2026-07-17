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

from scripts.emotion_state_phase_a_contracts import render_phase_a_report
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


def sample_payload() -> dict[str, object]:
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
        "blocking_reason_codes": [
            "dataset_download_not_authorized",
            "selected_dataset_manifests_not_verified",
        ],
        "summary": {
            "contract_check_count": 3,
            "contract_checks": {
                "public_dataset_contract": "pass",
                "split_manifest_v2_contract": "pass",
                "cohort_release_contract": "pass",
            },
            "baseline_fingerprint_count": 6,
            "selected_public_dataset_count": 2,
            "source_repository_url_status": "verified_read_only",
            "source_adaptation_allowed": False,
            "code_adaptation_started": False,
            "frozen_exp_002_evaluator_provenance_status": "not_recorded",
            "provider_operations_performed_by_runner": False,
            "private_data_read_by_runner": False,
            "runtime_behavior_changed_by_runner": False,
            "runtime_activation_allowed": False,
        },
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
    }


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
            ),
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
                "prepare",
                "lock",
                "recover",
                "finalize",
                "payload",
                "lease",
                "absence",
                "stage",
            ],
        )
        self.assertIs(
            build_payload.call_args.kwargs["verification_evidence"],
            verification_evidence,
        )

class ValidatorTimeoutTests(unittest.TestCase):
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
        ), patch.object(
            phase_a_validator,
            "validate_source",
        ), patch.object(
            phase_a_validator,
            "validate_contracts",
        ), patch.object(
            phase_a_validator,
            "validate_split_v2",
        ), patch.object(
            phase_a_validator,
            "validate_cohort",
        ), patch.object(
            phase_a_validator,
            "validate_patterns",
        ), patch.object(
            phase_a_validator,
            "validate_brain_extension",
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
