#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import hashlib
import io
import re
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


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def make_blob_repo(blob_bytes: bytes, *, filename: str = "atlas_output_quality_rules.md") -> tuple[tempfile.TemporaryDirectory[str], Path, bytes]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    source_path = root / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio" / filename
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(blob_bytes)
    run_git(root, "init")
    run_git(root, "config", "user.email", "codex@example.invalid")
    run_git(root, "config", "user.name", "Codex Test")
    run_git(root, "add", str(source_path.relative_to(root)).replace("\\", "/"))
    run_git(root, "commit", "-m", "fixture")
    return tmp, source_path, blob_bytes


class DetailedPricingPatcherSubsetTests(unittest.TestCase):
    def test_target_kb_doc_subset_is_guarded_and_defaults_to_literal_three_doc_contract(self) -> None:
        self.assertEqual(tuple(patcher.KB_DOCS), REQUIRED_DEFAULT_KB_DOCS)
        self.assertEqual(patcher.parse_target_kb_docs(None), REQUIRED_DEFAULT_KB_DOCS)
        self.assertEqual(
            patcher.parse_target_kb_docs(["atlas_output_quality_rules.md"]),
            ("atlas_output_quality_rules.md",),
        )

        for bad_targets in ([""], ["atlas_output_quality_rules.md", "atlas_output_quality_rules.md"], ["unknown.md"]):
            with self.subTest(bad_targets=bad_targets):
                with self.assertRaises(ValueError):
                    patcher.parse_target_kb_docs(bad_targets)

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                patcher.parse_args(["--target-kb-doc", ""])

    def test_default_dry_run_plans_three_kb_writes_and_agent_patch(self) -> None:
        requests = patcher.patch_requests(
            validator.sample_agent_for_patcher(),
            sample_preflight(),
        )

        self.assertEqual(
            [request["request_id"] for request in requests],
            [
                "update_kb_file::atlas_offer_facts.md",
                "update_kb_file::atlas_price_scope_cost_drivers.md",
                "update_kb_file::atlas_output_quality_rules.md",
                "patch_agent::prompt_dynamic_variables",
            ],
        )

        plan = patcher.plan_payload(
            preflight=sample_preflight(),
            requests=requests,
            target_kb_doc_names=REQUIRED_DEFAULT_KB_DOCS,
            provider_writes_allowed=False,
            ledger_summary=None,
        )

        self.assertEqual(plan["planned_provider_write_count"], 4)
        self.assertEqual(plan["planned_kb_write_count"], 3)
        self.assertEqual(plan["planned_agent_patch_count"], 1)
        self.assertEqual(
            plan["kb_documents_planned_for_in_place_update"],
            list(REQUIRED_DEFAULT_KB_DOCS),
        )

    def test_care_followup_explicit_subset_plans_two_kb_writes_and_agent_patch(self) -> None:
        requests = patcher.patch_requests(
            validator.sample_agent_for_patcher(),
            sample_preflight(),
            target_kb_doc_names=CARE_FOLLOWUP_KB_DOCS,
        )

        self.assertEqual(
            [request["request_id"] for request in requests],
            [
                "update_kb_file::atlas_price_scope_cost_drivers.md",
                "update_kb_file::atlas_output_quality_rules.md",
                "patch_agent::prompt_dynamic_variables",
            ],
        )

        plan = patcher.plan_payload(
            preflight=sample_preflight(),
            requests=requests,
            target_kb_doc_names=CARE_FOLLOWUP_KB_DOCS,
            provider_writes_allowed=False,
            ledger_summary=None,
        )

        self.assertEqual(plan["planned_provider_write_count"], 3)
        self.assertEqual(plan["planned_kb_write_count"], 2)
        self.assertEqual(plan["planned_agent_patch_count"], 1)
        self.assertEqual(
            plan["kb_documents_planned_for_in_place_update"],
            list(CARE_FOLLOWUP_KB_DOCS),
        )

    def test_subset_dry_run_plans_exactly_one_kb_write_and_agent_patch(self) -> None:
        requests = patcher.patch_requests(
            validator.sample_agent_for_patcher(),
            sample_preflight(),
            target_kb_doc_names=("atlas_output_quality_rules.md",),
        )

        self.assertEqual(
            [request["request_id"] for request in requests],
            ["update_kb_file::atlas_output_quality_rules.md", "patch_agent::prompt_dynamic_variables"],
        )

        plan = patcher.plan_payload(
            preflight=sample_preflight(),
            requests=requests,
            target_kb_doc_names=("atlas_output_quality_rules.md",),
            provider_writes_allowed=False,
            ledger_summary=None,
        )

        self.assertEqual(plan["provider_writes_allowed"], False)
        self.assertEqual(plan["provider_writes_made"], False)
        self.assertEqual(plan["planned_provider_write_count"], 2)
        self.assertEqual(plan["planned_kb_write_count"], 1)
        self.assertEqual(plan["planned_agent_patch_count"], 1)
        self.assertEqual(plan["kb_documents_planned_for_in_place_update"], ["atlas_output_quality_rules.md"])
        self.assertRegex(plan["source_evidence_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(plan["source_evidence_commit"], patcher.current_source_evidence_commit())
        self.assertEqual(plan["source_evidence_origin"], patcher.SOURCE_EVIDENCE_ORIGIN)

    def test_plan_only_request_and_result_payloads_bind_source_commit(self) -> None:
        requests = patcher.patch_requests(
            validator.sample_agent_for_patcher(),
            sample_preflight(),
            target_kb_doc_names=("atlas_output_quality_rules.md",),
        )
        provenance = patcher.source_provenance_fields()

        request_payload = patcher.patch_requests_payload(
            requests=requests,
            provider_writes_allowed=False,
            ledger_summary=None,
        )
        result_payload = patcher.patch_result_payload(
            status="plan_only_missing_confirmation",
            provider_writes_allowed=False,
            requests=requests,
            ledger_summary=None,
        )

        self.assertEqual(request_payload["source_evidence_commit"], provenance["source_evidence_commit"])
        self.assertEqual(result_payload["source_evidence_commit"], provenance["source_evidence_commit"])
        self.assertEqual(request_payload["source_evidence_origin"], provenance["source_evidence_origin"])
        self.assertEqual(result_payload["source_evidence_origin"], provenance["source_evidence_origin"])
        self.assertRegex(request_payload["source_evidence_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(request_payload["provider_write_attempt_count"], 0)
        self.assertEqual(result_payload["provider_write_attempts"], [])
        self.assertEqual(result_payload["planned_provider_write_count"], 2)

    def test_source_guard_rejects_repo_sources_that_differ_from_head(self) -> None:
        completed = type("Completed", (), {"returncode": 1, "stdout": "", "stderr": "dirty"})()
        with mock.patch.object(patcher, "git", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, re.escape("repo source files differ from HEAD")):
                patcher.assert_repo_sources_match_head(("atlas_output_quality_rules.md",))

    def test_source_evidence_uses_git_blob_bytes_when_worktree_has_crlf(self) -> None:
        marker = "Pricing Quote Discipline"
        blob_bytes = f"# Rules\n\n{marker}\n".encode("utf-8")
        tmp, source_path, expected_blob = make_blob_repo(blob_bytes)
        self.addCleanup(tmp.cleanup)
        source_path.write_bytes(expected_blob.replace(b"\n", b"\r\n"))

        with (
            mock.patch.object(patcher, "ROOT", Path(tmp.name)),
            mock.patch.object(patcher, "KB_REQUEST_SOURCE_MARKERS", {source_path.name: (marker,)}),
        ):
            evidence = patcher.source_file_evidence(source_path)

        expected_sha = hashlib.sha256(expected_blob).hexdigest()
        self.assertEqual(evidence["source_sha256"], expected_sha)
        self.assertEqual(evidence["source_byte_length"], len(expected_blob))
        self.assertEqual(evidence["source_git_blob_sha256"], expected_sha)
        self.assertEqual(evidence["source_git_blob_byte_length"], len(expected_blob))
        self.assertEqual(evidence["upload_byte_sha256"], expected_sha)
        self.assertEqual(evidence["upload_byte_length"], len(expected_blob))
        self.assertEqual(evidence["newline_mode"], "worktree_crlf_normalized_to_git_lf")

    def test_provider_kb_write_uploads_git_blob_bytes_not_worktree_bytes(self) -> None:
        requests = patcher.patch_requests(
            validator.sample_agent_for_patcher(),
            sample_preflight(),
            target_kb_doc_names=("atlas_output_quality_rules.md",),
        )
        source_path = patcher.KB_ROOT / "atlas_output_quality_rules.md"
        git_blob = subprocess.run(
            ["git", "show", f"HEAD:{source_path.relative_to(patcher.ROOT).as_posix()}"],
            cwd=patcher.ROOT,
            capture_output=True,
            check=True,
        ).stdout
        self.assertNotEqual(source_path.read_bytes(), git_blob, "fixture must keep CRLF worktree bytes distinct")
        uploaded: list[bytes] = []

        def fake_blob_upload(**kwargs: object) -> dict[str, object]:
            file_bytes = kwargs.get("file_bytes")
            self.assertIsInstance(file_bytes, bytes)
            uploaded.append(file_bytes)
            return {"status_code": 200, "response": {}}

        agent = validator.sample_agent_for_patcher()
        with (
            mock.patch.object(patcher, "multipart_update_file", return_value={"status_code": 200, "response": {}}),
            mock.patch.object(patcher, "multipart_update_file_from_bytes", side_effect=fake_blob_upload, create=True),
            mock.patch.object(patcher, "json_request", return_value={"response": agent}),
            mock.patch.object(patcher, "validate_preflight", return_value=sample_preflight()),
            mock.patch.object(patcher, "protected_fingerprint", return_value={}),
            mock.patch.object(patcher, "assert_fingerprint_matches"),
            mock.patch.object(patcher, "get_prompt", return_value={"prompt": patcher.PROMPT_PATH.read_text(encoding="utf-8").strip()}),
            mock.patch.object(patcher, "actual_dynamic_variable_placeholders", return_value=dict(patcher.TARGET_PRICE_VARIABLES)),
        ):
            patcher.write_provider_changes(
                api_key="test",
                agent=agent,
                preflight=sample_preflight(),
                requests=requests,
                ledger=patcher.ProviderWriteLedger(),
                target_kb_doc_names=("atlas_output_quality_rules.md",),
            )

        self.assertEqual(uploaded, [git_blob])


if __name__ == "__main__":
    unittest.main()
