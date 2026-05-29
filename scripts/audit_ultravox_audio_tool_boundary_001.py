#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
QUALITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001" / "result.json"
LISTENING_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-001" / "result.json"
TRANSCRIPT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001" / "result.json"
LATENCY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LATENCY-AUDIT-001" / "result.json"
RESULT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001"
RESULT_PATH = RESULT_DIR / "result.json"
REPORT_PATH = RESULT_DIR / "report.md"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clip(text: Any, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def boundary_response(sandbox: dict[str, Any]) -> str:
    agent_after_boundary: list[str] = []
    saw_boundary = False
    for item in sandbox.get("final_transcripts_sanitized", []):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "")
        if item.get("role") == "user" and "crm" in text.lower():
            saw_boundary = True
            continue
        if saw_boundary and item.get("role") == "agent" and text:
            agent_after_boundary.append(text)
    return clip(agent_after_boundary[0] if agent_after_boundary else "")


def build_result(sandbox: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    completed_turns = int(sandbox.get("synthetic_audio_turns_completed", 0))
    request_count = int(sandbox.get("local_http_tool_request_count", 0))
    tool_boundary_passed = (
        request_count >= completed_turns
        and sandbox.get("tool_call_attempted") is True
        and sandbox.get("tool_call_succeeded") is True
        and quality.get("tool_boundary_enforced") is True
        and int(sandbox.get("fake_side_effect_count", 0)) == 0
        and int(sandbox.get("unsupported_claim_count", 0)) == 0
        and int(sandbox.get("product_truth_drift_count", 0)) == 0
    )
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001",
        "phase": "4J6",
        "source_sandbox_evaluation_id": sandbox.get("evaluation_id"),
        "source_quality_evaluation_id": quality.get("evaluation_id"),
        "local_http_tool_request_count": request_count,
        "synthetic_audio_turns_completed": completed_turns,
        "tool_call_attempted": sandbox.get("tool_call_attempted") is True,
        "tool_call_succeeded": sandbox.get("tool_call_succeeded") is True,
        "tool_called_for_each_relevant_turn": request_count >= completed_turns and completed_turns > 0,
        "tool_boundary_passed": tool_boundary_passed,
        "side_effects_allowed": False,
        "fake_side_effect_count": int(sandbox.get("fake_side_effect_count", 0)),
        "unsupported_claim_count": int(sandbox.get("unsupported_claim_count", 0)),
        "product_truth_drift_count": int(sandbox.get("product_truth_drift_count", 0)),
        "crm_email_calendar_claim_count": int(sandbox.get("crm_email_calendar_claim_count", 0)),
        "boundary_response_for_dont_put_me_in_crm": boundary_response(sandbox),
        "canonical_memory_owner": sandbox.get("canonical_memory_owner"),
        "sales_brain_owner": sandbox.get("project_sales_brain_owner"),
        "ultravox_session_memory_limited_to_session_context": sandbox.get("canonical_memory_owner") == "project_runtime" and int(sandbox.get("memory_conflict_count", 0)) == 0,
        "ultravox_session_memory_note": "Project runtime remains canonical memory owner; Ultravox evidence is limited to the provider session context.",
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def recommendation_for(listening: dict[str, Any], transcript: dict[str, Any], latency: dict[str, Any], tool: dict[str, Any], user_audio_review_good: bool | None) -> str:
    if listening.get("status") == "pending_manual_review":
        return "user_listen_to_ultravox_agent_audio"
    if transcript.get("transcript_quality_passed") is not True:
        return "fix audio format / turn timing before another provider run"
    if tool.get("tool_boundary_passed") is not True:
        return "fix tool declaration/prompt before more audio testing"
    if latency.get("live_ready_latency") is not True:
        return "run warm-session latency benchmark next, still synthetic only"
    if user_audio_review_good is True:
        return "limited synthetic voice conversation evaluation next"
    return "user_listen_to_ultravox_agent_audio"


def build_decision(listening: dict[str, Any], transcript: dict[str, Any], latency: dict[str, Any], tool: dict[str, Any]) -> dict[str, Any]:
    user_audio_review_good: bool | None = None
    recommendation = recommendation_for(listening, transcript, latency, tool, user_audio_review_good)
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001",
        "phase": "4J6",
        "recommendation": recommendation,
        "manual_listening_review_status": listening.get("status"),
        "user_audio_review_good": user_audio_review_good,
        "next_provider_run_allowed_now": False,
        "transcript_quality_passed": transcript.get("transcript_quality_passed") is True,
        "tool_boundary_passed": tool.get("tool_boundary_passed") is True,
        "live_ready_latency": latency.get("live_ready_latency") is True,
        "needs_warm_turn_benchmark": latency.get("needs_warm_turn_benchmark") is True,
        "current_observed_latency_seconds": latency.get("current_observed_latency_seconds"),
        "decision_logic": [
            "If audio listening review is pending: user_listen_to_ultravox_agent_audio.",
            "If transcript quality is poor: fix audio format / turn timing before another provider run.",
            "If transcript quality is good but latency high: run warm-session latency benchmark next, still synthetic only.",
            "If tool boundary failed: fix tool declaration/prompt before more audio testing.",
            "If transcript quality and tool boundary pass, and user audio review is good: limited synthetic voice conversation evaluation next.",
            "Always keep live wiring, production calls, and real customer data disallowed.",
        ],
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def render_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001",
            "",
            f"Local HTTP tool request count: `{result['local_http_tool_request_count']}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Tool called for each relevant turn: `{str(result['tool_called_for_each_relevant_turn']).lower()}`",
            f"Tool boundary passed: `{str(result['tool_boundary_passed']).lower()}`",
            f"Side effects allowed: `{str(result['side_effects_allowed']).lower()}`",
            f"Fake side effect count: `{result['fake_side_effect_count']}`",
            f"Unsupported claim count: `{result['unsupported_claim_count']}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"CRM/email/calendar claim count: `{result['crm_email_calendar_claim_count']}`",
            f"Boundary response for 'Don't put me in CRM.': `{result['boundary_response_for_dont_put_me_in_crm']}`",
            f"Canonical memory owner: `{result['canonical_memory_owner']}`",
            f"Sales brain owner: `{result['sales_brain_owner']}`",
            f"Ultravox session memory limited to session context: `{str(result['ultravox_session_memory_limited_to_session_context']).lower()}`",
            "",
            "## Boundaries",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )


def render_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Manual listening review status: `{decision['manual_listening_review_status']}`",
            f"User audio review good: `{decision['user_audio_review_good']}`",
            f"Next provider run allowed now: `{str(decision['next_provider_run_allowed_now']).lower()}`",
            f"Transcript quality passed: `{str(decision['transcript_quality_passed']).lower()}`",
            f"Tool boundary passed: `{str(decision['tool_boundary_passed']).lower()}`",
            f"Live-ready latency: `{str(decision['live_ready_latency']).lower()}`",
            f"Needs warm-turn benchmark: `{str(decision['needs_warm_turn_benchmark']).lower()}`",
            f"Current observed latency seconds: `{decision['current_observed_latency_seconds']}`",
            "",
            "## Boundaries",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Real customer data allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )


def main() -> None:
    sandbox = load_json(SANDBOX_RESULT_PATH)
    quality = load_json(QUALITY_RESULT_PATH)
    listening = load_json(LISTENING_RESULT_PATH)
    transcript = load_json(TRANSCRIPT_RESULT_PATH)
    latency = load_json(LATENCY_RESULT_PATH)
    result = build_result(sandbox, quality)
    decision = build_decision(listening, transcript, latency, result)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_decision_report(decision))
    print(json.dumps({"tool_boundary_passed": result["tool_boundary_passed"], "recommendation": decision["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
