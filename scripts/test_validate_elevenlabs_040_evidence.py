#!/usr/bin/env python3
from __future__ import annotations

import json
import contextlib
import io
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_elevenlabs_040_detailed_pricing_control as patcher
import validate_elevenlabs_040_detailed_pricing_control as validator


REQUIRED_DEFAULT_KB_DOCS = (
    "atlas_offer_facts.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_output_quality_rules.md",
)
CARE_FOLLOWUP_KB_DOCS = (
    "atlas_price_scope_cost_drivers.md",
    "atlas_output_quality_rules.md",
)


def sample_preflight() -> dict[str, object]:
    return {
        "target_kb_docs": {
            name: {
                "id": doc_id,
                "source_path": f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}",
            }
            for name, doc_id in patcher.KNOWN_KB_DOC_IDS.items()
        }
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def git_show_bytes(commit: str, source_path: str) -> bytes:
    completed = validator.git(["show", f"{commit}:{source_path}"])
    return completed.stdout.encode("utf-8")


def source_evidence_for_commit(commit: str, source_path: str) -> dict[str, object]:
    source_bytes = git_show_bytes(commit, source_path)
    markers = validator.KB_REQUEST_SOURCE_MARKERS[Path(source_path).name]
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    return {
        "evidence_origin": patcher.SOURCE_EVIDENCE_ORIGIN,
        "source_path": source_path,
        "source_sha256": source_sha,
        "source_byte_length": len(source_bytes),
        "source_git_blob_sha256": source_sha,
        "source_git_blob_byte_length": len(source_bytes),
        "upload_byte_sha256": source_sha,
        "upload_byte_length": len(source_bytes),
        "newline_mode": "git_blob_lf",
        "markers": list(markers),
    }


def missing_current_markers(commit: str, target_kb_doc_names: tuple[str, ...]) -> dict[str, list[str]]:
    missing_by_doc: dict[str, list[str]] = {}
    for name in target_kb_doc_names:
        source_path = f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}"
        source_text = git_show_bytes(commit, source_path).decode("utf-8", errors="replace")
        missing = [marker for marker in validator.KB_REQUEST_SOURCE_MARKERS[name] if marker not in source_text]
        if missing:
            missing_by_doc[name] = missing
    return missing_by_doc


def reachable_commit_missing_current_markers(target_kb_doc_names: tuple[str, ...]) -> tuple[str, dict[str, list[str]]]:
    current = patcher.current_source_evidence_commit()
    commits = [line.strip() for line in validator.git(["rev-list", "HEAD"]).stdout.splitlines() if line.strip()]
    for commit in commits:
        if commit == current:
            continue
        missing_by_doc = missing_current_markers(commit, target_kb_doc_names)
        if missing_by_doc:
            return commit, missing_by_doc
    raise AssertionError("reachable history contains no commit missing current required KB markers")


def evidence_fixture(
    root: Path,
    *,
    mode: str = "plan_only",
    source_commit: str | None = None,
    target_kb_doc_names: tuple[str, ...] = REQUIRED_DEFAULT_KB_DOCS,
) -> None:
    source_commit = source_commit or patcher.current_source_evidence_commit()
    requests = patcher.patch_requests(
        validator.sample_agent_for_patcher(),
        sample_preflight(),
        target_kb_doc_names=target_kb_doc_names,
    )
    if source_commit is not None and source_commit != patcher.current_source_evidence_commit():
        for request in requests:
            if str(request.get("request_id", "")).startswith("update_kb_file::"):
                request["source_evidence"] = source_evidence_for_commit(source_commit, str(request["source_path"]))
    provenance = {
        "source_evidence_commit": source_commit,
        "source_evidence_origin": patcher.SOURCE_EVIDENCE_ORIGIN,
    }
    plan = patcher.plan_payload(
        preflight=sample_preflight(),
        requests=requests,
        target_kb_doc_names=target_kb_doc_names,
        provider_writes_allowed=(mode == "live_passed"),
        ledger_summary=None,
    )
    plan.update(provenance)
    request_payload = patcher.patch_requests_payload(
        requests=requests,
        provider_writes_allowed=(mode == "live_passed"),
        ledger_summary=None,
    )
    request_payload.update(provenance)
    result = patcher.patch_result_payload(
        status="passed" if mode == "live_passed" else "plan_only_missing_confirmation",
        provider_writes_allowed=(mode == "live_passed"),
        requests=requests,
        ledger_summary=None,
    )
    result.update(provenance)
    if mode == "live_passed":
        attempts = [
            {"request_id": request["request_id"], "method": request["method"], "endpoint": request["endpoint"], "attempted_at_utc": f"2026-07-12T00:00:0{index}Z"}
            for index, request in enumerate(requests, start=1)
        ]
        successes = [
            {"request_id": request["request_id"], "status_code": 200, "confirmed_at_utc": f"2026-07-12T00:00:1{index}Z"}
            for index, request in enumerate(requests, start=1)
        ]
        for payload in (plan, request_payload, result):
            payload.update(
                {
                    "provider_writes_made": True,
                    "provider_write_attempt_count": len(attempts),
                    "provider_write_success_count": len(successes),
                    "provider_write_attempts": attempts,
                    "provider_write_successes": successes,
                }
            )
    pre_snapshot = {
        "checkpoint_id": patcher.CHECKPOINT_ID,
        "phase": "pre_patch",
        "snapshot_serialized_at_utc": "2026-07-12T00:00:00Z",
        "live_readback_time_recorded": True,
        "live_readback_at_utc": "2026-07-12T00:00:00Z",
    }
    post_snapshot = {
        "checkpoint_id": patcher.CHECKPOINT_ID,
        "phase": "post_patch" if mode == "live_passed" else "not_written",
        "snapshot_serialized_at_utc": "2026-07-12T00:00:20Z",
        "live_readback_time_recorded": mode == "live_passed",
        "live_readback_at_utc": "2026-07-12T00:00:20Z" if mode == "live_passed" else None,
    }
    write_json(root / "live_agent_pre_patch_snapshot.json", pre_snapshot)
    write_json(root / "live_agent_post_patch_snapshot.json", post_snapshot)
    write_json(root / "live_agent_patch_plan.json", plan)
    write_json(root / "live_agent_patch_requests.json", request_payload)
    write_json(root / "live_agent_patch_result.json", result)


def copy_current_live_evidence(root: Path) -> None:
    for name in (
        "live_agent_pre_patch_snapshot.json",
        "live_agent_post_patch_snapshot.json",
        "live_agent_patch_plan.json",
        "live_agent_patch_requests.json",
        "live_agent_patch_result.json",
    ):
        shutil.copy2(validator.LIVE_EVIDENCE_DIR / name, root / name)


def update_kb_evidence(root: Path, request_id: str, mutator: object) -> None:
    for artifact in ("live_agent_patch_plan.json", "live_agent_patch_requests.json"):
        payload = json.loads((root / artifact).read_text(encoding="utf-8"))
        if artifact == "live_agent_patch_plan.json":
            mutator(payload["request_source_evidence_by_id"][request_id])
        else:
            for request in payload["requests"]:
                if request.get("request_id") == request_id:
                    mutator(request["source_evidence"])
        write_json(root / artifact, payload)


class DetailedPricingEvidenceValidationTests(unittest.TestCase):
    def test_production_default_main_fails_commitless_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root)
            for name in ("live_agent_patch_plan.json", "live_agent_patch_requests.json", "live_agent_patch_result.json"):
                payload = json.loads((root / name).read_text(encoding="utf-8"))
                payload.pop("source_evidence_commit")
                payload.pop("source_evidence_origin")
                write_json(root / name, payload)

            stderr = io.StringIO()
            stdout = io.StringIO()
            with mock.patch.object(validator, "LIVE_EVIDENCE_DIR", root):
                with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                    exit_code = validator.main()

            self.assertEqual(exit_code, 1)
            self.assertIn("source evidence commit", stderr.getvalue())

    def test_missing_source_commit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root)
            payload = json.loads((root / "live_agent_patch_requests.json").read_text(encoding="utf-8"))
            payload.pop("source_evidence_commit")
            write_json(root / "live_agent_patch_requests.json", payload)

            with self.assertRaisesRegex(AssertionError, "source evidence commit"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_plan_only_head_default_validates_zero_writes_and_current_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root)

            validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_new_historical_evidence_verifies_git_blob_and_upload_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=patcher.current_source_evidence_commit())

            summary = validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

            self.assertEqual(summary["source_evidence_mode"], "git_blob")

    def test_new_historical_evidence_rejects_tampered_upload_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=patcher.current_source_evidence_commit())
            request_id = "update_kb_file::atlas_price_scope_cost_drivers.md"
            update_kb_evidence(root, request_id, lambda evidence: evidence.update({"upload_byte_sha256": "0" * 64}))

            with self.assertRaisesRegex(AssertionError, "upload byte sha mismatch"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_live_passed_head_default_validates_declared_four_write_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed")

            validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_current_legacy_live_evidence_passes_with_visible_line_ending_mode(self) -> None:
        summary = validator.validate_live_evidence_artifacts(require_existing_evidence=True)

        self.assertEqual(summary["source_evidence_mode"], "legacy_worktree_line_endings")
        self.assertIn(
            "update_kb_file::atlas_output_quality_rules.md",
            summary["legacy_worktree_line_endings_request_ids"],
        )

    def test_current_legacy_live_evidence_rejects_tampered_upload_length(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            copy_current_live_evidence(root)
            request_id = "update_kb_file::atlas_output_quality_rules.md"
            update_kb_evidence(root, request_id, lambda evidence: evidence.update({"source_byte_length": evidence["source_byte_length"] + 1}))

            with self.assertRaisesRegex(AssertionError, "legacy upload length mismatch"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_current_legacy_live_evidence_rejects_changed_current_head_blob(self) -> None:
        source_commit = json.loads((validator.LIVE_EVIDENCE_DIR / "live_agent_patch_plan.json").read_text(encoding="utf-8"))["source_evidence_commit"]
        current_head = validator.git(["rev-parse", "HEAD"]).stdout.strip()
        target_path = validator.OUTPUT_PATH
        original_git_show = validator.git_show_file_bytes
        source_blob = validator.git_show_file_bytes(source_commit, target_path)

        def fake_git_show(commit: str, source_path: str, *, repo_root: Path = validator.ROOT) -> bytes:
            if commit == current_head and source_path == target_path:
                return source_blob + b"\nchanged\n"
            return original_git_show(commit, source_path, repo_root=repo_root)

        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            copy_current_live_evidence(root)
            with mock.patch.object(validator, "git_show_file_bytes", side_effect=fake_git_show):
                with self.assertRaisesRegex(AssertionError, "legacy current HEAD blob mismatch"):
                    validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_current_legacy_live_evidence_rejects_binary_blob(self) -> None:
        source_commit = json.loads((validator.LIVE_EVIDENCE_DIR / "live_agent_patch_plan.json").read_text(encoding="utf-8"))["source_evidence_commit"]
        target_path = validator.OUTPUT_PATH
        original_git_show = validator.git_show_file_bytes
        source_blob = validator.git_show_file_bytes(source_commit, target_path)

        def fake_git_show(commit: str, source_path: str, *, repo_root: Path = validator.ROOT) -> bytes:
            if commit == source_commit and source_path == target_path:
                return source_blob + b"\0"
            return original_git_show(commit, source_path, repo_root=repo_root)

        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            copy_current_live_evidence(root)
            with mock.patch.object(validator, "git_show_file_bytes", side_effect=fake_git_show):
                with self.assertRaisesRegex(AssertionError, "legacy binary source content"):
                    validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_care_followup_subset_validates_declared_three_write_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", target_kb_doc_names=CARE_FOLLOWUP_KB_DOCS)

            validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_malformed_live_attempt_count_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed")
            payload = json.loads((root / "live_agent_patch_result.json").read_text(encoding="utf-8"))
            payload["provider_write_attempt_count"] = 999
            write_json(root / "live_agent_patch_result.json", payload)

            with self.assertRaisesRegex(AssertionError, "provider write attempt count"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_historical_commit_missing_current_product_markers_fails_closed(self) -> None:
        historical, missing_by_doc = reachable_commit_missing_current_markers(REQUIRED_DEFAULT_KB_DOCS)
        self.assertTrue(missing_by_doc, "historical fixture precondition must prove at least one current marker is absent")
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=historical, target_kb_doc_names=REQUIRED_DEFAULT_KB_DOCS)

            with self.assertRaisesRegex(AssertionError, "historical source markers missing"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_historical_commit_bad_kb_source_hash_fails_closed(self) -> None:
        historical = patcher.current_source_evidence_commit()
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=historical, target_kb_doc_names=REQUIRED_DEFAULT_KB_DOCS)
            requests_payload = json.loads((root / "live_agent_patch_requests.json").read_text(encoding="utf-8"))
            plan_payload = json.loads((root / "live_agent_patch_plan.json").read_text(encoding="utf-8"))
            request_id = requests_payload["requests"][0]["request_id"]
            requests_payload["requests"][0]["source_evidence"]["source_sha256"] = "0" * 64
            plan_payload["request_source_evidence_by_id"][request_id]["source_sha256"] = "0" * 64
            write_json(root / "live_agent_patch_requests.json", requests_payload)
            write_json(root / "live_agent_patch_plan.json", plan_payload)

            with self.assertRaisesRegex(AssertionError, "source sha mismatch"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_historical_commit_plan_request_source_evidence_mismatch_fails_closed(self) -> None:
        historical = patcher.current_source_evidence_commit()
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=historical, target_kb_doc_names=REQUIRED_DEFAULT_KB_DOCS)
            payload = json.loads((root / "live_agent_patch_plan.json").read_text(encoding="utf-8"))
            request_id = "update_kb_file::atlas_price_scope_cost_drivers.md"
            payload["request_source_evidence_by_id"][request_id]["source_byte_length"] += 1
            write_json(root / "live_agent_patch_plan.json", payload)

            with self.assertRaisesRegex(AssertionError, "plan/request source evidence mismatch"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)


if __name__ == "__main__":
    unittest.main()
