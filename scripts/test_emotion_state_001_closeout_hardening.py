from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
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
        "schema_version": 1,
        "status": "test-only",
        "summary": {
            "contract_check_count": 5,
            "baseline_fingerprint_count": 6,
            "selected_public_dataset_count": 0,
            "source_repository_url_status": "unverified",
            "code_adaptation_started": False,
            "frozen_exp_002_evaluator_provenance_status": "not_recorded",
            "provider_operations_performed_by_runner": False,
            "private_data_read_by_runner": False,
            "runtime_behavior_changed_by_runner": False,
        },
        "readiness_boundary": {"phase_a_complete": False},
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

    def test_active_publisher_lock_blocks_second_cli_without_mutation(self) -> None:
        runner_path = ROOT / "scripts" / "run_emotion_state_001_phase_a_contracts.py"
        result_path = publication_runner.DEFAULT_RESULT
        report_path = publication_runner.DEFAULT_REPORT
        recovery_dir = publication_runner.DEFAULT_RECOVERY_DIR
        journal_path = recovery_dir / JOURNAL_NAME
        self.assertFalse(journal_path.exists())
        original_result = result_path.read_bytes()
        original_report = report_path.read_bytes()
        holder_script = r'''
import json
import os
from pathlib import Path
from unittest.mock import patch

from scripts.run_emotion_state_001_phase_a_contracts import (
    DEFAULT_RECOVERY_DIR,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    JOURNAL_NAME,
    publication_lock,
    publish_evidence_pair,
)

payload = json.loads(DEFAULT_RESULT.read_bytes().decode("utf-8"))
payload["status"] = "concurrency_test_incomplete_publication"
real_replace = os.replace

def interrupt_after_result_replace(source, destination):
    real_replace(source, destination)
    if Path(destination) == DEFAULT_RESULT:
        raise KeyboardInterrupt("leave a live journal while retaining the lock")

with publication_lock(recovery_dir=DEFAULT_RECOVERY_DIR):
    with patch(
        "scripts.run_emotion_state_001_phase_a_contracts.os.replace",
        side_effect=interrupt_after_result_replace,
    ):
        try:
            publish_evidence_pair(
                payload,
                result_path=DEFAULT_RESULT,
                report_path=DEFAULT_REPORT,
                recovery_dir=DEFAULT_RECOVERY_DIR,
            )
        except KeyboardInterrupt:
            pass
    if not (DEFAULT_RECOVERY_DIR / JOURNAL_NAME).exists():
        raise RuntimeError("expected a durable live journal")
    print("READY", flush=True)
    input()
'''
        holder = subprocess.Popen(
            [sys.executable, "-c", holder_script],
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

            live_result = result_path.read_bytes()
            live_report = report_path.read_bytes()
            live_state = {
                path.name: path.read_bytes()
                for path in recovery_dir.iterdir()
                if path.is_file() and path.name != publication_runner.LOCK_NAME
            }
            self.assertIn(JOURNAL_NAME, live_state)

            blocked = subprocess.run(
                [sys.executable, str(runner_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
            self.assertIn("publication lock is already held", blocked.stderr)
            self.assertNotIn("Traceback", blocked.stderr)
            self.assertEqual(result_path.read_bytes(), live_result)
            self.assertEqual(report_path.read_bytes(), live_report)
            self.assertEqual(
                {
                    path.name: path.read_bytes()
                    for path in recovery_dir.iterdir()
                    if path.is_file() and path.name != publication_runner.LOCK_NAME
                },
                live_state,
            )

            holder.kill()
            holder_output, holder_error = holder.communicate(timeout=10)
            self.assertNotEqual(holder.returncode, 0, holder_output + holder_error)

            recovered = subprocess.run(
                [sys.executable, str(runner_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
            self.assertEqual(result_path.read_bytes(), original_result)
            self.assertEqual(report_path.read_bytes(), original_report)
            self.assertFalse(journal_path.exists())
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
            if journal_path.exists():
                try:
                    recover_incomplete_publication(
                        result_path=result_path,
                        report_path=report_path,
                        recovery_dir=recovery_dir,
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

    def test_phase_a_checkpoint_baseline_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch.object(
            phase_a_validator.sys,
            "argv",
            ["validator", "--section", "checkpoint"],
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

    def test_phase_a_checkpoint_runner_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        completed = subprocess.CompletedProcess(
            ["stable-test-label"],
            returncode=0,
            stdout="",
            stderr="",
        )
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch.object(
            phase_a_validator.sys,
            "argv",
            ["validator", "--section", "checkpoint"],
        ), patch(
            "scripts.validate_emotion_state_001_phase_a_contracts.subprocess.run",
            side_effect=[completed, timeout],
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

    def test_phase_a_checkpoint_prompt_render_timeout_is_controlled(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        completed = subprocess.CompletedProcess(
            ["stable-test-label"],
            returncode=0,
            stdout="",
            stderr="",
        )
        timeout = subprocess.TimeoutExpired(["stable-test-label"], 60)

        with patch.object(
            phase_a_validator.sys,
            "argv",
            ["validator", "--section", "checkpoint"],
        ), patch(
            "scripts.validate_emotion_state_001_phase_a_contracts.subprocess.run",
            side_effect=[completed, completed, timeout],
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


if __name__ == "__main__":
    unittest.main()
