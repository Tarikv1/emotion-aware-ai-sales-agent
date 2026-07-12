#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def evidence_fixture(
    root: Path,
    *,
    mode: str = "plan_only",
    source_commit: str | None = None,
    target_kb_doc_names: tuple[str, ...] = ("atlas_output_quality_rules.md",),
) -> None:
    source_commit = source_commit or patcher.current_source_evidence_commit()
    requests = patcher.patch_requests(
        validator.sample_agent_for_patcher(),
        sample_preflight(),
        target_kb_doc_names=target_kb_doc_names,
    )
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


class DetailedPricingEvidenceValidationTests(unittest.TestCase):
    def test_missing_source_commit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root)
            payload = json.loads((root / "live_agent_patch_requests.json").read_text(encoding="utf-8"))
            payload.pop("source_evidence_commit")
            write_json(root / "live_agent_patch_requests.json", payload)

            with self.assertRaisesRegex(AssertionError, "source evidence commit"):
                validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_plan_only_head_subset_validates_zero_writes_and_current_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root)

            validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)

    def test_live_passed_head_subset_validates_declared_two_write_set(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed")

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

    def test_valid_historical_commit_excludes_stale_hash_checks_only_after_shape_validation(self) -> None:
        historical = validator.git(["rev-parse", "HEAD^"]).stdout.strip()
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            evidence_fixture(root, mode="live_passed", source_commit=historical, target_kb_doc_names=tuple(patcher.KB_DOCS))

            validator.validate_live_evidence_artifacts(evidence_dir=root, require_existing_evidence=True)


if __name__ == "__main__":
    unittest.main()
