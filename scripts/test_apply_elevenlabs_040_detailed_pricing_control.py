#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import apply_elevenlabs_040_detailed_pricing_control as patcher
import validate_elevenlabs_040_detailed_pricing_control as validator


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


class DetailedPricingPatcherSubsetTests(unittest.TestCase):
    def test_target_kb_doc_subset_is_guarded_and_defaults_to_active_docs(self) -> None:
        self.assertEqual(patcher.parse_target_kb_docs(None), tuple(patcher.KB_DOCS))
        self.assertEqual(
            tuple(patcher.KB_DOCS),
            ("atlas_price_scope_cost_drivers.md", "atlas_output_quality_rules.md"),
        )
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

    def test_default_dry_run_plans_two_kb_writes_and_agent_patch(self) -> None:
        requests = patcher.patch_requests(
            validator.sample_agent_for_patcher(),
            sample_preflight(),
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
            target_kb_doc_names=tuple(patcher.KB_DOCS),
            provider_writes_allowed=False,
            ledger_summary=None,
        )

        self.assertEqual(plan["planned_provider_write_count"], 3)
        self.assertEqual(plan["planned_kb_write_count"], 2)
        self.assertEqual(plan["planned_agent_patch_count"], 1)
        self.assertEqual(
            plan["kb_documents_planned_for_in_place_update"],
            ["atlas_price_scope_cost_drivers.md", "atlas_output_quality_rules.md"],
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


if __name__ == "__main__":
    unittest.main()
