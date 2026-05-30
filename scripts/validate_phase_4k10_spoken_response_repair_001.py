#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_spoken_human_naturalness_001 import (  # noqa: E402
    CATEGORY_IDS,
    audit_cases,
    total_issue_count,
)
from scripts.run_non_llm_action_selector_runtime_shadow_expansion_001 import (  # noqa: E402
    build_safe_fixture_cases,
)

CHECKPOINT_ID = "PHASE-4K10-SPOKEN-RESPONSE-REPAIR-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
OUT_DIR = GENERATED / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

BEFORE_NATURALNESS_COUNTS = {
    "empty_candidate_response": 4,
    "good_human_spoken_examples": 6,
    "missing_human_acknowledgment": 9,
    "missing_sales_progression": 7,
    "overly_formal_or_policy_like": 2,
    "premature_scheduling_or_callback_push": 1,
    "repetitive_review_language": 0,
    "robotic_internal_wording": 1,
    "too_long_for_spoken_call": 0,
    "weak_value_framing": 13,
}
BEFORE_NATURALNESS_ISSUE_COUNT = 37

TARGET_CASE_IDS = {
    "phase_4k8_public_openai_001_price",
    "phase_4k8_public_openai_002_plan_fit",
    "phase_4k8_public_openai_003_privacy",
    "phase_4k8_public_openai_004_signup",
    "phase_4k8_public_openai_005_boundary",
    "phase_4k8_b2b_saas_003",
    "phase_4k8_routesignal_004",
}

PUBLIC_OPENAI_EMPTY_REPAIR_CASE_IDS = {
    "phase_4k8_public_openai_003_privacy",
    "phase_4k8_public_openai_004_signup",
    "phase_4k8_public_openai_005_boundary",
}

FORBIDDEN_BUYER_FACING_PATTERNS = [
    r"\bi should still tie that\b",
    r"\bcheck the plan page before upgrading\b",
    r"\bi cannot verify that claim here\b",
    r"\bbefore i claim it\b",
    r"\bexact setup fit needs verified material\b",
    r"\bcandidate response\b",
    r"\bpolicy boundary\b",
    r"\bselector\b",
    r"\bruntime\b",
    r"\bprosody\b",
    r"\bfish\b",
]

FALSE_EVIDENCE_KEYS = [
    "provider_calls_made",
    "model_calls_made",
    "local_llm_calls_made",
    "tts_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "audio_data_used",
    "raw_private_data",
    "private_live_transcripts_inspected",
    "runtime_response_replacement_performed",
    "automatic_runtime_rewrite_performed",
    "live_selector_control_recommended",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(str(text or "").casefold().split())


def categories_by_case(categories: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    by_case: dict[str, list[str]] = {}
    for category in CATEGORY_IDS:
        if category == "good_human_spoken_examples":
            continue
        payload = categories.get(category) if isinstance(categories.get(category), dict) else {}
        for example in payload.get("examples") or []:
            case_id = str(example.get("case_id") or "")
            if case_id:
                by_case.setdefault(case_id, []).append(category)
    return by_case


def false_flags_from_results(*payloads: dict[str, Any]) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for key in FALSE_EVIDENCE_KEYS:
        values = [payload.get(key) for payload in payloads if key in payload]
        flags[key] = bool(values) and all(value is False for value in values)
    return flags


def selector_config_confirmations() -> dict[str, bool]:
    shadow_mode = read_json(ROOT / "runtime" / "action_selector" / "shadow_mode_config.json")
    shadow_import = read_json(ROOT / "runtime" / "action_selector" / "shadow_runtime_import_config.json")
    shadow_logging = read_json(ROOT / "runtime" / "action_selector" / "shadow_runtime_logging_config.json")
    return {
        "live_selector_control_remains_false": (
            shadow_mode.get("enabled_for_live_runtime") is False
            and shadow_mode.get("live_runtime_wiring_allowed") is False
            and shadow_import.get("selector_control_allowed") is False
        ),
        "selector_response_replacement_remains_false": (
            shadow_mode.get("buyer_facing_text_generation_allowed") is False
            and shadow_import.get("response_text_change_allowed") is False
            and shadow_logging.get("response_text_change_allowed") is False
        ),
        "selector_side_effect_paths_remain_false": (
            shadow_mode.get("side_effects_allowed") is False
            and shadow_import.get("side_effects_allowed") is False
            and shadow_logging.get("side_effects_allowed") is False
        ),
    }


def live_demo_status(checkpoint_id: str) -> dict[str, Any]:
    payload = read_json(GENERATED / checkpoint_id / "result.json")
    passed = payload.get("passed")
    if passed is True:
        status = "pass"
    elif passed is False:
        status = "deferred_or_fail"
    else:
        status = "not_run"
    return {
        "checkpoint_id": checkpoint_id,
        "status": status,
        "failure_count": payload.get("failure_count"),
        "failures": payload.get("failures") or [],
        "provider_calls_made": payload.get("provider_calls_made"),
    }


def build_result() -> dict[str, Any]:
    cases = build_safe_fixture_cases()
    by_id = {str(case.get("case_id")): case for case in cases}
    categories = audit_cases(cases)
    after_counts = {
        category: int((categories.get(category) or {}).get("count") or 0)
        for category in CATEGORY_IDS
    }
    after_by_case = categories_by_case(categories)
    failures: list[str] = []

    for case_id in PUBLIC_OPENAI_EMPTY_REPAIR_CASE_IDS:
        if not normalized(str((by_id.get(case_id) or {}).get("candidate_response") or "")):
            failures.append(f"{case_id} still has an empty candidate_response")

    for case_id in TARGET_CASE_IDS:
        case = by_id.get(case_id)
        if not case:
            failures.append(f"{case_id} missing from safe fixture cases")
            continue
        response = str(case.get("candidate_response") or "")
        lowered = normalized(response)
        if not lowered:
            failures.append(f"{case_id} response is empty")
        for pattern in FORBIDDEN_BUYER_FACING_PATTERNS:
            if re.search(pattern, lowered, flags=re.I):
                failures.append(f"{case_id} still contains forbidden buyer-facing wording: {pattern}")

    routesignal_response = normalized(str((by_id.get("phase_4k8_routesignal_004") or {}).get("candidate_response") or ""))
    if "callback preference" in routesignal_response or "first i need to check relevance" in routesignal_response:
        failures.append("phase_4k8_routesignal_004 still accepts callback/time language before sales progression")
    if "workflow" not in routesignal_response or "issue" not in routesignal_response or "?" not in routesignal_response:
        failures.append("phase_4k8_routesignal_004 must preserve a compact workflow issue progression question")

    repaired_case_ids = sorted(case_id for case_id in TARGET_CASE_IDS if not after_by_case.get(case_id))
    unrepaired_target_case_ids = sorted(case_id for case_id in TARGET_CASE_IDS if after_by_case.get(case_id))
    remaining_unrepaired_case_ids = sorted(
        case_id for case_id, case_categories in after_by_case.items() if case_categories
    )
    for case_id in unrepaired_target_case_ids:
        failures.append(f"{case_id} still has naturalness issue(s): {after_by_case.get(case_id)}")

    naturalness = read_json(GENERATED / "SPOKEN-HUMAN-NATURALNESS-AUDIT-001" / "result.json")
    expansion = read_json(GENERATED / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001" / "result.json")
    evidence_false_flags = false_flags_from_results(naturalness, expansion)
    confirmations = selector_config_confirmations()
    for key, value in confirmations.items():
        if value is not True:
            failures.append(f"{key} must be true")

    side_effect_keys = [
        "provider_calls_made",
        "model_calls_made",
        "local_llm_calls_made",
        "tts_calls_made",
        "openai_api_calls_made",
        "ultravox_calls_made",
        "elevenlabs_calls_made",
        "crm_calls_made",
        "email_calls_made",
        "calendar_calls_made",
    ]
    side_effect_paths_enabled = any(evidence_false_flags.get(key) is False for key in side_effect_keys)
    private_raw_added_to_public_evidence = any(
        evidence_false_flags.get(key) is False
        for key in ["raw_private_data", "private_live_transcripts_inspected", "audio_data_used"]
    )
    response_replacement_enabled = confirmations["selector_response_replacement_remains_false"] is not True
    live_selector_control_enabled = confirmations["live_selector_control_remains_false"] is not True

    if side_effect_paths_enabled:
        failures.append("provider/model/TTS/CRM/email/calendar evidence flags must remain false")
    if private_raw_added_to_public_evidence:
        failures.append("public evidence must not add private raw transcript/audio")
    if response_replacement_enabled:
        failures.append("selector response replacement must remain false")
    if live_selector_control_enabled:
        failures.append("live selector control must remain false")

    live_demo_results = {
        "LIVE-DEMO-002": live_demo_status("LIVE-DEMO-002-conversation-stability-callback-disambiguation"),
        "LIVE-DEMO-009": live_demo_status("LIVE-DEMO-009-appointment-lead-close"),
        "LIVE-DEMO-014": live_demo_status("LIVE-DEMO-014-clear-pain-callback-followup"),
    }

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "before_naturalness_issue_count": BEFORE_NATURALNESS_ISSUE_COUNT,
        "after_naturalness_issue_count": total_issue_count(categories),
        "before_naturalness_counts": BEFORE_NATURALNESS_COUNTS,
        "after_naturalness_counts": after_counts,
        "target_case_ids": sorted(TARGET_CASE_IDS),
        "repaired_case_ids": repaired_case_ids,
        "unrepaired_target_case_ids": unrepaired_target_case_ids,
        "remaining_unrepaired_case_ids": remaining_unrepaired_case_ids,
        "remaining_unrepaired_case_issues": {case_id: after_by_case[case_id] for case_id in remaining_unrepaired_case_ids},
        "live_demo_results": live_demo_results,
        "confirmations": {
            **confirmations,
            "no_provider_model_tts_crm_email_calendar_side_effect_path_enabled": not side_effect_paths_enabled,
            "no_private_raw_transcript_or_audio_added_to_public_evidence": not private_raw_added_to_public_evidence,
            "selector_response_replacement_remains_false": not response_replacement_enabled,
            "live_selector_control_remains_false": not live_selector_control_enabled,
        },
        "evidence_false_flags": evidence_false_flags,
        "private_live_transcripts_inspected": False,
        "provider_calls_made": False,
        "model_calls_made": False,
        "local_llm_calls_made": False,
        "tts_calls_made": False,
        "crm_calls_made": False,
        "email_calls_made": False,
        "calendar_calls_made": False,
        "audio_data_used": False,
        "raw_private_data": False,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Before/after naturalness issue count: {result['before_naturalness_issue_count']}/{result['after_naturalness_issue_count']}",
        f"- Repaired case IDs: {', '.join(result['repaired_case_ids']) or 'None'}",
        f"- Remaining unrepaired target case IDs: {', '.join(result['unrepaired_target_case_ids']) or 'None'}",
        f"- Remaining unrepaired case IDs: {', '.join(result['remaining_unrepaired_case_ids']) or 'None'}",
        f"- Live selector control remains false: {str(result['confirmations']['live_selector_control_remains_false']).lower()}",
        f"- Selector response replacement remains false: {str(result['confirmations']['selector_response_replacement_remains_false']).lower()}",
        f"- Provider/model/TTS/CRM/email/calendar side-effect path enabled: {str(not result['confirmations']['no_provider_model_tts_crm_email_calendar_side_effect_path_enabled']).lower()}",
        f"- Private raw transcript/audio added to public evidence: {str(not result['confirmations']['no_private_raw_transcript_or_audio_added_to_public_evidence']).lower()}",
        "",
        "## Before/After Naturalness Counts",
        "",
    ]
    for category in sorted(BEFORE_NATURALNESS_COUNTS):
        before = result["before_naturalness_counts"].get(category)
        after = result["after_naturalness_counts"].get(category)
        lines.append(f"- {category}: {before} -> {after}")
    lines.extend(["", "## Live Demo RouteSignal Status", ""])
    for demo_id, payload in result["live_demo_results"].items():
        lines.append(
            f"- {demo_id}: {payload['status']} "
            f"(failure_count={payload.get('failure_count')}, provider_calls_made={payload.get('provider_calls_made')})"
        )
    lines.extend(["", "## Remaining Unrepaired Case Details", ""])
    if result["remaining_unrepaired_case_issues"]:
        for case_id, issues in result["remaining_unrepaired_case_issues"].items():
            lines.append(f"- {case_id}: {', '.join(issues)}")
    else:
        lines.append("- None")
    lines.extend(["", "## Failures", ""])
    if result["failures"]:
        lines.extend(f"- {failure}" for failure in result["failures"])
    else:
        lines.append("- None")
    return "\n".join(lines)


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "failure_count": result["failure_count"],
                "before_naturalness_issue_count": result["before_naturalness_issue_count"],
                "after_naturalness_issue_count": result["after_naturalness_issue_count"],
                "repaired_case_ids": result["repaired_case_ids"],
                "unrepaired_target_case_ids": result["unrepaired_target_case_ids"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["failures"]:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(result['failures'])} issue(s). See {RESULT_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
