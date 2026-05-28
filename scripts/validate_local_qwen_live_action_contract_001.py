#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.live_action_prompt import render_live_action_prompt  # noqa: E402
from runtime.llm_brain.live_action_verifier import signature, verify_live_action_output  # noqa: E402
from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    audit_side_effects,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
)


EXPERIMENT_ID = "LOCAL-QWEN-LIVE-ACTION-CONTRACT-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
CONTRACT_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_live_action_contract.json"
ANTI_LOOP_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_anti_loop_memory_contract.json"
UNCERTAINTY_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_buyer_facing_uncertainty_policy.json"
CASE_ID_RE = re.compile(r"(?:^|_)(?:case|scenario|live|paraphrase|negative)?_?\d{3,}$|_\d{3,}$", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def validate_contract(contract: dict[str, Any], failures: list[str]) -> list[str]:
    required = contract.get("required_fields") if isinstance(contract.get("required_fields"), list) else []
    if required != ["action_id", "slots", "memory_updates", "uncertainty", "say"]:
        failures.append("live action contract required fields are wrong")
    optional = set(contract.get("optional_fields") or [])
    for field in ("needs_facts", "blocked_routes", "replan_reason", "emotion_hint", "confidence"):
        if field not in optional:
            failures.append(f"live action contract missing optional field: {field}")
    output_target = contract.get("output_target") if isinstance(contract.get("output_target"), dict) else {}
    if output_target.get("normal_generated_tokens_min") != 10 or output_target.get("normal_generated_tokens_max") != 60:
        failures.append("live action token target must be 10-60 generated tokens")
    for key in ("full_compact_planner_json_allowed_in_live_mode", "verbose_reasoning_allowed", "schema_explanation_allowed", "internal_language_allowed"):
        if output_target.get(key) is not False:
            failures.append(f"output target {key} must be false")

    action_space = contract.get("action_space") if isinstance(contract.get("action_space"), dict) else {}
    if action_space.get("bounded") is not True:
        failures.append("action space must be bounded")
    if action_space.get("slots_open") is not True:
        failures.append("slots must remain open")
    if action_space.get("fixed_scripted_scenario_paths_allowed") is not False:
        failures.append("fixed scripted scenario paths must remain disallowed")
    action_ids = [str(item) for item in action_space.get("semantic_reusable_action_ids") or [] if isinstance(item, str)]
    if len(action_ids) < 12:
        failures.append("semantic action ID set is too small")
    for action_id in action_ids:
        if action_id == "generalized_sales_move":
            failures.append("generalized_sales_move is forbidden")
        if CASE_ID_RE.search(action_id):
            failures.append(f"action ID looks case-specific: {action_id}")
    return action_ids


def validate_anti_loop(contract: dict[str, Any], failures: list[str]) -> None:
    required = set(contract.get("required_memory_fields") or [])
    for field in (
        "last_action_id",
        "last_action_slot_signature",
        "last_agent_question",
        "last_response_signature",
        "answered_topics",
        "asked_topic_counts",
        "known_slots",
        "buyer_corrections",
        "buyer_said_already_told_you",
        "terminal_acceptance_seen",
        "price_answered",
        "recommendation_given",
        "current_decision_frame",
        "last_objection_handled",
    ):
        if field not in required:
            failures.append(f"anti-loop memory field missing: {field}")
    boundary = contract.get("deterministic_layer_boundary") if isinstance(contract.get("deterministic_layer_boundary"), dict) else {}
    if boundary.get("chooses_final_sales_move_in_normal_operation") is not False:
        failures.append("deterministic layer must not choose final sales move")
    if boundary.get("uses_canned_replacement_in_normal_operation") is not False:
        failures.append("deterministic layer must not use canned replacement in normal operation")


def validate_uncertainty_policy(policy: dict[str, Any], failures: list[str]) -> list[dict[str, str]]:
    forbidden = [str(item).casefold() for item in policy.get("forbidden_buyer_facing_terms") or []]
    mappings: list[dict[str, str]] = []
    for item in policy.get("mappings") or []:
        if not isinstance(item, dict):
            continue
        internal = item.get("internal")
        buyer_facing = item.get("buyer_facing")
        if isinstance(internal, str) and isinstance(buyer_facing, str):
            mappings.append({"internal": internal, "buyer_facing": buyer_facing})
            lowered = buyer_facing.casefold()
            for term in forbidden:
                if term and term in lowered:
                    failures.append(f"buyer-facing uncertainty mapping leaks forbidden term: {internal}:{term}")
    required = {"low_confidence_plan_scope", "possible_asr_claude_cloud", "missing_use_case", "repeated_question_risk", "terminal_acceptance"}
    seen = {item["internal"] for item in mappings}
    for internal in sorted(required - seen):
        failures.append(f"uncertainty mapping missing: {internal}")
    return mappings


def validate_verifier_behavior(action_ids: list[str], failures: list[str]) -> dict[str, Any]:
    approved = {"public_plan_names": "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise."}
    good_payload = {
        "action_id": "ask_usage_intensity",
        "slots": {"use_case": ["coding workflow", "voice"]},
        "memory_updates": {"use_case": ["coding workflow", "voice"]},
        "uncertainty": "none",
        "say": "Got it - coding workflow and voice. Are you using it lightly, moderately, or heavily?",
    }
    good = verify_live_action_output(
        good_payload,
        memory={"current_buyer_utterance": "I use it for coding workflow and voice.", "known_slots": {}},
        approved_fact_ids=list(approved),
        approved_fact_summaries=approved,
        allowed_action_ids=action_ids,
    ).to_dict()
    if good["status"] != "pass":
        failures.append(f"valid live-action payload did not pass verifier: {good}")

    repeat = verify_live_action_output(
        good_payload,
        memory={
            "current_buyer_utterance": "I already told you, coding and voice.",
            "last_action_id": "ask_usage_intensity",
            "last_action_slot_signature": signature({"use_case": ["coding workflow", "voice"]}),
            "known_slots": {"use_case": ["coding workflow", "voice"]},
            "buyer_said_already_told_you": True,
            "new_buyer_info_since_last_action": False,
        },
        approved_fact_ids=list(approved),
        approved_fact_summaries=approved,
        allowed_action_ids=action_ids,
    ).to_dict()
    if repeat["replan_required"] is not True:
        failures.append(f"repeat risk did not request replan: {repeat}")

    internal = verify_live_action_output(
        {**good_payload, "action_id": "clarify_question_scope", "say": "I am not confident enough to classify this."},
        memory={"current_buyer_utterance": "What do you mean?"},
        approved_fact_ids=list(approved),
        approved_fact_summaries=approved,
        allowed_action_ids=action_ids,
    ).to_dict()
    if internal["replan_required"] is not True:
        failures.append(f"internal language did not request replan: {internal}")

    side_effect = verify_live_action_output(
        {**good_payload, "action_id": "respect_boundary", "say": "I scheduled the calendar invite for you."},
        memory={"current_buyer_utterance": "Book it for me."},
        approved_fact_ids=list(approved),
        approved_fact_summaries=approved,
        allowed_action_ids=action_ids,
    ).to_dict()
    if side_effect["hard_block"] is not True:
        failures.append(f"fake side effect did not hard-block: {side_effect}")

    prompt = render_live_action_prompt(
        sanitized_buyer_utterance="Cloud, or Claude, I am not sure.",
        memory_ledger_summary={"known_slots": {}},
        approved_campaign_fact_ids=list(approved),
        approved_campaign_fact_summaries=approved,
    )
    if "Required fields: action_id, slots, memory_updates, uncertainty, say" not in prompt:
        failures.append("prompt builder does not expose live action required fields")
    return {"good": good, "repeat": repeat, "internal_language": internal, "side_effect": side_effect}


def main() -> int:
    failures: list[str] = []
    contract = read_json(CONTRACT_PATH)
    anti_loop = read_json(ANTI_LOOP_PATH)
    policy = read_json(UNCERTAINTY_PATH)
    action_ids = validate_contract(contract, failures)
    validate_anti_loop(anti_loop, failures)
    mappings = validate_uncertainty_policy(policy, failures)
    verifier_checks = validate_verifier_behavior(action_ids, failures)

    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    files_changed = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files_changed)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed outside approved offline live-action architecture files")
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "contract": rel(CONTRACT_PATH),
        "anti_loop_memory_contract": rel(ANTI_LOOP_PATH),
        "buyer_facing_uncertainty_policy": rel(UNCERTAINTY_PATH),
        "required_fields": contract.get("required_fields"),
        "optional_fields": contract.get("optional_fields"),
        "semantic_action_ids": action_ids,
        "slots_open": (contract.get("action_space") or {}).get("slots_open"),
        "buyer_facing_uncertainty_examples": mappings,
        "verifier_behavior": verifier_checks,
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "local_model_calls_made": False,
        "training_rerun": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": runtime_behavior_changed,
        "response_text_changed": response_text_changed,
        "model_or_adapter_weights_committed": bool(tracked),
        "changed_files": files_changed,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        "\n".join(
            [
                f"# {EXPERIMENT_ID}",
                "",
                f"- status: {result['status']}",
                f"- required_fields: {', '.join(result['required_fields'] or [])}",
                f"- action_id_count: {len(action_ids)}",
                f"- slots_open: {str(result['slots_open']).lower()}",
                f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
                f"- runtime_behavior_changed: {str(result['runtime_behavior_changed']).lower()}",
                f"- response_text_changed: {str(result['response_text_changed']).lower()}",
                "",
                "## Buyer-Facing Uncertainty Examples",
                "",
                *(f"- {item['internal']}: {item['buyer_facing']}" for item in mappings),
                "",
                "## Failures",
                "",
                json.dumps(failures, indent=2, ensure_ascii=False),
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
