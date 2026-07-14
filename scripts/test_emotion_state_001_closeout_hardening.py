from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.emotion_state_phase_a_contracts import render_phase_a_report
from scripts.run_emotion_state_001_phase_a_contracts import (
    EvidencePublicationError,
    JOURNAL_NAME,
    publish_evidence_pair,
    recover_incomplete_publication,
    verify_evidence_pair_bytes,
)


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
