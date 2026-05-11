#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-044-core-sales-policy-update"
SOURCE_CHECKPOINT_ID = "PROD-043-sales-playbook-runtime-adapter"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_044_core_sales_policy_update.py",
    "runner": ROOT / "scripts" / "run_prod_044_core_sales_policy_update.py",
    "validator": ROOT / "scripts" / "validate_prod_044_core_sales_policy_update.py",
    "doc": ROOT / "docs" / "product" / "PROD_044_CORE_SALES_POLICY_UPDATE.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "packet": OUT_DIR / "core_sales_policy_review_packet.json",
    "review_data": OUT_DIR / "prod_044_review_data.json",
    "review_html": OUT_DIR / "prod_044_review.html",
}

SOURCE_FILES = {
    "result": SOURCE_DIR / "result.json",
    "report": SOURCE_DIR / "report.md",
    "agent_response_evaluations": SOURCE_DIR / "agent_response_evaluations.json",
    "runtime_adapter_review_data": SOURCE_DIR / "runtime_adapter_review_data.json",
}

DOC_FILES = [
    ROOT / "docs" / "product" / "COMMANDS.md",
    ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    ROOT / "docs" / "thesis" / "ROADMAP.md",
    ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    ROOT / "docs" / "thesis" / "DECISION_LOG.md",
]

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "retrieval_enabled",
    "runtime_agent_modified",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "production_runtime_promotion_allowed",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
]

FORBIDDEN_SCOPE_KEYS = {
    "conversation_sequence",
    "interaction_traces",
    "scenario_diversity_traces",
    "full_conversations",
    "voice_playback_enabled",
}

PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\-\(\) ]{7,}\d)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(all_keys(item))
    return keys


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_existence() -> None:
    missing = [str(path.relative_to(ROOT)) for path in [*REQUIRED_FILES.values(), *SOURCE_FILES.values()] if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_source() -> None:
    result = read_json(SOURCE_FILES["result"])
    summary = result.get("summary", {})
    assert_condition(result.get("validation", {}).get("passed") is True, "PROD-043 result must be validator-passed")
    assert_condition(summary.get("runtime_behavior_changed") is False, "PROD-043 runtime boundary failed")
    assert_condition(summary.get("retrieval_enabled") is False, "PROD-043 retrieval boundary failed")
    assert_condition(summary.get("provider_calls_made") is False, "PROD-043 provider boundary failed")
    assert_condition(summary.get("llm_used") is False, "PROD-043 LLM boundary failed")


def validate_packet(result: dict[str, Any], packet: dict[str, Any], review_data: dict[str, Any]) -> None:
    assert_condition(result.get("checkpoint_id") == CHECKPOINT_ID, result)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet)
    assert_condition(result.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, result)
    assert_condition(packet.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, packet)
    assert_condition(result.get("validation", {}).get("passed") is True, result)
    summary = result.get("summary", {})
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary.get(field) is False, f"{field} must remain false")
    assert_condition(summary.get("runtime_policy_update_justified") is True, summary)
    assert_condition(summary.get("runtime_changes_performed") is False, summary)
    assert_condition(summary.get("candidate_policy_update_count") == len(packet.get("candidate_policy_updates", [])), summary)
    assert_condition(summary.get("blocked_update_count") == len(packet.get("blocked_updates", [])), summary)
    assert_condition(summary.get("required_campaign_fact_guard_count") == len(packet.get("required_campaign_fact_guards", [])), summary)
    assert_condition(summary.get("current_runtime_probe_count", 0) > 0, summary)
    assert_condition(summary.get("current_runtime_probe_fail_count", 0) > 0, summary)

    candidates = packet.get("candidate_policy_updates", [])
    assert_condition(candidates, "candidate policy updates must exist")
    for candidate in candidates:
        assert_condition(candidate.get("status") == "candidate_not_applied", candidate)
        assert_condition(candidate.get("justified_by_prod_043_evidence") is True, candidate)
        assert_condition(candidate.get("prod_043_evidence"), candidate)
        assert_condition(candidate.get("current_runtime_probe_evidence"), candidate)
        assert_condition(candidate.get("required_campaign_fact_guard_ids"), candidate)
        assert_condition(candidate.get("runtime_change_performed") is False, candidate)
        assert_condition(candidate.get("deterministic_regression_required_before_apply") is True, candidate)

    guard_ids = {guard["guard_id"] for guard in packet.get("required_campaign_fact_guards", [])}
    for candidate in candidates:
        assert_condition(set(candidate["required_campaign_fact_guard_ids"]).issubset(guard_ids), candidate)

    assert_condition(packet.get("blocked_updates"), "blocked updates must be visible")
    assert_condition(review_data.get("summary", {}).get("candidate_policy_update_count") == len(candidates), "review data summary mismatch")


def validate_no_scope_creep() -> None:
    generated_keys = {"result", "report", "packet", "review_data", "review_html", "doc"}
    for key in generated_keys:
        path = REQUIRED_FILES[key]
        if path.suffix == ".json":
            payload = read_json(path)
            assert_condition(not (all_keys(payload) & FORBIDDEN_SCOPE_KEYS), f"forbidden scope key in {key}")
        text = path.read_text(encoding="utf-8")
        assert_condition(not PHONE_PATTERN.search(text), f"phone-like string found in {key}")
        if key != "review_html":
            assert_condition(not EMAIL_PATTERN.search(text), f"email-like string found in {key}")
        lowered = text.lower()
        for forbidden in ("raw transcript", '"provider_calls_made": true', '"llm_used": true', '"retrieval_enabled": true'):
            assert_condition(forbidden not in lowered, f"forbidden text {forbidden!r} found in {key}")


def validate_docs() -> None:
    for path in DOC_FILES:
        assert_condition(path.exists(), f"missing doc {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        assert_condition("PROD-044" in text or "prod_044" in text, f"missing PROD-044 note in {path.relative_to(ROOT)}")
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    for marker in (
        "PROD-044",
        "candidate policy updates",
        "blocked updates",
        "campaign-fact guards",
        "runtime behavior changed: `false`",
        "retrieval enabled: `false`",
    ):
        assert_condition(marker.lower() in doc_text.lower(), f"product doc missing {marker}")


def validate_html() -> None:
    html_text = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    for marker in ("candidate policy updates", "blocked updates", "required campaign-fact guards", "current runtime probe evidence", "boundary summary"):
        assert_condition(marker in html_text, f"HTML missing {marker}")


def main() -> None:
    validate_existence()
    validate_source()
    run_runner()
    validate_existence()
    result = read_json(REQUIRED_FILES["result"])
    packet = read_json(REQUIRED_FILES["packet"])
    review_data = read_json(REQUIRED_FILES["review_data"])
    validate_packet(result, packet, review_data)
    validate_no_scope_creep()
    validate_docs()
    validate_html()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
