#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

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
    def test_target_kb_doc_subset_is_guarded_and_defaults_to_all_docs(self) -> None:
        self.assertEqual(patcher.parse_target_kb_docs(None), tuple(patcher.KB_DOCS))
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


if __name__ == "__main__":
    unittest.main()
