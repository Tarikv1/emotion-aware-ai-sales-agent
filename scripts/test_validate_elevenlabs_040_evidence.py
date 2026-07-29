#!/usr/bin/env python3
from __future__ import annotations

import json
import contextlib
import io
import hashlib
import subprocess
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
REQUIRED_NEW_SOURCE_FIELDS = (
    "source_git_blob_sha256",
    "source_git_blob_length",
    "upload_sha256",
    "upload_length",
    "newline_mode",
)
LEGACY_SOURCE_COMMIT = "1e8af8510b072d5fe08501af7229abac5208bdf8"
LEGACY_SOURCE_EVIDENCE_FIXTURES = {
    "update_kb_file::atlas_price_scope_cost_drivers.md": {
        "request_id": "update_kb_file::atlas_price_scope_cost_drivers.md",
        "source_path": "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md",
        "source_sha256": "df6f06af92ad57ca5679b848c909f56cc34905fc78fa3a3fd888861913cbfd54",
        "source_byte_length": 14394,
        "mode": "legacy_git_blob_old_fields",
    },
    "update_kb_file::atlas_output_quality_rules.md": {
        "request_id": "update_kb_file::atlas_output_quality_rules.md",
        "source_path": "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md",
        "source_sha256": "5f6f68f5ec26640a55658d374c5729bfdc23d10745a4c194ed245d4aa486425e",
        "source_byte_length": 19064,
        "mode": "legacy_worktree_line_endings",
    },
}
# Historical output worktree preserved a mixed-ending file: most lines were CRLF,
# but these line numbers remained LF-only in the legacy artifact.
LEGACY_OUTPUT_LF_ONLY_LINE_NUMBERS = (
    5,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    88,
    89,
    90,
    91,
    92,
    93,
    94,
)
REAL_REPO_ROOT = validator.ROOT


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
    return validator.git_show_file_bytes(commit, source_path)


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
        "source_git_blob_length": len(source_bytes),
        "upload_sha256": source_sha,
        "upload_length": len(source_bytes),
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
        source_commit=patcher.current_source_evidence_commit(),
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
        source_commit=source_commit,
    )
    plan.update(provenance)
    request_payload = patcher.patch_requests_payload(
        requests=requests,
        provider_writes_allowed=(mode == "live_passed"),
        ledger_summary=None,
        source_commit=source_commit,
    )
    request_payload.update(provenance)
    result = patcher.patch_result_payload(
        status="passed" if mode == "live_passed" else "plan_only_missing_confirmation",
        provider_writes_allowed=(mode == "live_passed"),
        requests=requests,
        ledger_summary=None,
        source_commit=source_commit,
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


def replace_kb_evidence(root: Path, request_id: str, source_evidence: dict[str, object]) -> None:
    for artifact in ("live_agent_patch_plan.json", "live_agent_patch_requests.json"):
        payload = json.loads((root / artifact).read_text(encoding="utf-8"))
        if artifact == "live_agent_patch_plan.json":
            payload["request_source_evidence_by_id"][request_id] = dict(source_evidence)
        else:
            for request in payload["requests"]:
                if request.get("request_id") == request_id:
                    request["source_evidence"] = dict(source_evidence)
                    break
        write_json(root / artifact, payload)


def legacy_git_blob_bytes(source_path: str) -> bytes:
    return git_show_bytes(LEGACY_SOURCE_COMMIT, source_path)


def legacy_worktree_bytes(source_path: str, *, mode: str) -> bytes:
    source_blob_bytes = legacy_git_blob_bytes(source_path)
    if mode == "legacy_worktree_line_endings":
        assert b"\r\n" not in source_blob_bytes, f"{source_path} legacy blob unexpectedly already contains CRLF"
        source_lines = source_blob_bytes.splitlines(keepends=True)
        assert source_lines and all(line.endswith(b"\n") for line in source_lines), f"{source_path} legacy blob line structure changed"
        lf_only = set(LEGACY_OUTPUT_LF_ONLY_LINE_NUMBERS)
        assert max(lf_only) <= len(source_lines), f"{source_path} legacy LF-only map exceeds line count"
        return b"".join(
            line[:-1] + (b"\n" if index in lf_only else b"\r\n")
            for index, line in enumerate(source_lines, start=1)
        )
    return source_blob_bytes


def legacy_source_evidence(fixture: dict[str, object]) -> dict[str, object]:
    source_path = str(fixture["source_path"])
    source_name = Path(source_path).name
    return {
        "evidence_origin": patcher.SOURCE_EVIDENCE_ORIGIN,
        "source_path": source_path,
        "source_sha256": fixture["source_sha256"],
        "source_byte_length": fixture["source_byte_length"],
        "markers": list(validator.KB_REQUEST_SOURCE_MARKERS[source_name]),
    }


def write_legacy_historical_worktree(root: Path) -> None:
    for fixture in LEGACY_SOURCE_EVIDENCE_FIXTURES.values():
        source_path = str(fixture["source_path"])
        mode = str(fixture["mode"])
        source_bytes = legacy_worktree_bytes(source_path, mode=mode)
        assert hashlib.sha256(source_bytes).hexdigest() == fixture["source_sha256"], f"{source_path} legacy sha fixture drifted"
        assert len(source_bytes) == fixture["source_byte_length"], f"{source_path} legacy length fixture drifted"
        target = root / source_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_bytes)


def legacy_evidence_fixture(evidence_root: Path, historical_root: Path) -> None:
    write_legacy_historical_worktree(historical_root)
    evidence_fixture(
        evidence_root,
        mode="live_passed",
        source_commit=LEGACY_SOURCE_COMMIT,
        target_kb_doc_names=CARE_FOLLOWUP_KB_DOCS,
    )
    for request_id, fixture in LEGACY_SOURCE_EVIDENCE_FIXTURES.items():
        replace_kb_evidence(evidence_root, request_id, legacy_source_evidence(fixture))


def validate_legacy_fixture(
    evidence_root: Path,
    historical_root: Path,
    *,
    source_bytes_overrides: dict[str, bytes] | None = None,
    current_head_blob_overrides: dict[str, bytes] | None = None,
) -> dict[str, object]:
    original_git = validator.git
    original_git_show = validator.git_show_file_bytes

    def fake_git(args: list[str], *, repo_root: Path = REAL_REPO_ROOT) -> subprocess.CompletedProcess[str]:
        if args == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(args, 0, stdout=f"{LEGACY_SOURCE_COMMIT}\n", stderr="")
        return original_git(args, repo_root=repo_root)

    def fake_source_bytes_for_commit(source_commit: str, source_path: str, current_head: str) -> bytes:
        if source_bytes_overrides and source_path in source_bytes_overrides:
            return source_bytes_overrides[source_path]
        return original_git_show(source_commit, source_path, repo_root=REAL_REPO_ROOT)

    def fake_git_show(commit: str, source_path: str, *, repo_root: Path = REAL_REPO_ROOT) -> bytes:
        if current_head_blob_overrides and commit == LEGACY_SOURCE_COMMIT and source_path in current_head_blob_overrides:
            return current_head_blob_overrides[source_path]
        return original_git_show(commit, source_path, repo_root=repo_root)

    with (
        mock.patch.object(validator, "ROOT", historical_root),
        mock.patch.object(validator, "git", side_effect=fake_git),
        mock.patch.object(validator, "source_bytes_for_commit", side_effect=fake_source_bytes_for_commit),
        mock.patch.object(validator, "git_show_file_bytes", side_effect=fake_git_show),
    ):
        return validator.validate_live_evidence_artifacts(evidence_dir=evidence_root, require_existing_evidence=True)


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
            update_kb_evidence(root, request_id, lambda evidence: evidence.update({"upload_sha256": "0" * 64}))

            with self.assertRaisesRegex(AssertionError, "upload byte sha mismatch"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_old_field_only_non_allowlisted_evidence_fails_even_when_hash_matches_blob(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=patcher.current_source_evidence_commit())
            request_id = "update_kb_file::atlas_price_scope_cost_drivers.md"

            def remove_new_fields(evidence: dict[str, object]) -> None:
                for field in REQUIRED_NEW_SOURCE_FIELDS + ("source_git_blob_byte_length", "upload_byte_sha256", "upload_byte_length"):
                    evidence.pop(field, None)

            update_kb_evidence(root, request_id, remove_new_fields)

            with self.assertRaisesRegex(AssertionError, "missing required source evidence field"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_missing_each_required_new_source_field_fails_closed(self) -> None:
        for missing_field in REQUIRED_NEW_SOURCE_FIELDS:
            with self.subTest(missing_field=missing_field):
                with tempfile.TemporaryDirectory() as raw_tmp:
                    root = Path(raw_tmp)
                    evidence_fixture(root, mode="live_passed", source_commit=patcher.current_source_evidence_commit())
                    request_id = "update_kb_file::atlas_price_scope_cost_drivers.md"
                    update_kb_evidence(root, request_id, lambda evidence, field=missing_field: evidence.pop(field, None))

                    with self.assertRaisesRegex(AssertionError, f"missing required source evidence field {missing_field}"):
                        validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_live_passed_head_default_validates_declared_four_write_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed")

            validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_legacy_fixture_passes_with_visible_line_ending_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            evidence_root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            evidence_root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(evidence_root, historical_root)
            summary = validate_legacy_fixture(evidence_root, historical_root)

            self.assertEqual(summary["source_evidence_mode"], "legacy_worktree_line_endings")
            self.assertEqual(
                summary["legacy_allowlisted_request_ids"],
                [
                    "update_kb_file::atlas_price_scope_cost_drivers.md",
                    "update_kb_file::atlas_output_quality_rules.md",
                ],
            )
            self.assertIn(
                "update_kb_file::atlas_output_quality_rules.md",
                summary["legacy_worktree_line_endings_request_ids"],
            )

    def test_legacy_price_blob_old_fields_passes_when_head_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            evidence_root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            evidence_root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(evidence_root, historical_root)
            summary = validate_legacy_fixture(evidence_root, historical_root)

            self.assertIn(
                "update_kb_file::atlas_price_scope_cost_drivers.md",
                summary["legacy_allowlisted_request_ids"],
            )
            self.assertNotIn(
                "update_kb_file::atlas_price_scope_cost_drivers.md",
                summary["legacy_worktree_line_endings_request_ids"],
            )

    def test_legacy_fixture_rejects_tampered_upload_length(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(root, historical_root)
            request_id = "update_kb_file::atlas_output_quality_rules.md"
            update_kb_evidence(root, request_id, lambda evidence: evidence.update({"source_byte_length": evidence["source_byte_length"] + 1}))

            with self.assertRaisesRegex(AssertionError, "legacy allowlist mismatch"):
                validate_legacy_fixture(root, historical_root)

    def test_legacy_line_ending_mode_is_restricted_to_exact_completed_artifact_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(root, historical_root)
            request_id = "update_kb_file::atlas_output_quality_rules.md"
            update_kb_evidence(root, request_id, lambda evidence: evidence.update({"source_sha256": "0" * 64}))

            with self.assertRaisesRegex(AssertionError, "legacy allowlist mismatch"):
                validate_legacy_fixture(root, historical_root)

    def test_request_source_path_must_match_request_id_doc_name(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=patcher.current_source_evidence_commit())
            request_id = "update_kb_file::atlas_price_scope_cost_drivers.md"
            update_kb_evidence(
                root,
                request_id,
                lambda evidence: evidence.update(
                    {"source_path": "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md"}
                ),
            )

            with self.assertRaisesRegex(AssertionError, "source path mismatch"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_legacy_fixture_rejects_changed_current_head_blob(self) -> None:
        target_path = validator.OUTPUT_PATH
        source_blob = legacy_git_blob_bytes(target_path)

        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(root, historical_root)
            with self.assertRaisesRegex(AssertionError, "legacy current HEAD blob mismatch"):
                validate_legacy_fixture(root, historical_root, current_head_blob_overrides={target_path: source_blob + b"\nchanged\n"})

    def test_legacy_price_blob_old_fields_rejects_changed_current_head_blob(self) -> None:
        target_path = validator.PRICE_PATH
        source_blob = legacy_git_blob_bytes(target_path)

        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(root, historical_root)
            with self.assertRaisesRegex(AssertionError, "legacy current HEAD blob mismatch"):
                validate_legacy_fixture(root, historical_root, current_head_blob_overrides={target_path: source_blob + b"\nchanged\n"})

    def test_legacy_fixture_rejects_binary_blob(self) -> None:
        target_path = validator.OUTPUT_PATH
        source_blob = legacy_git_blob_bytes(target_path) + b"\0"

        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_root = Path(raw_tmp)
            root = temp_root / "evidence"
            historical_root = temp_root / "historical"
            root.mkdir()
            historical_root.mkdir()
            legacy_evidence_fixture(root, historical_root)
            with self.assertRaisesRegex(AssertionError, "legacy binary source content"):
                validate_legacy_fixture(root, historical_root, source_bytes_overrides={target_path: source_blob})

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
