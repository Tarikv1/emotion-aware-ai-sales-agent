#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001" / "result.json"
QUALITY_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001"
QUALITY_RESULT_PATH = QUALITY_DIR / "result.json"
QUALITY_REPORT_PATH = QUALITY_DIR / "report.md"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def agent_text_join(sandbox: dict[str, Any]) -> str:
    parts = []
    for transcript in sandbox.get("final_transcripts_sanitized", []):
        if isinstance(transcript, dict) and transcript.get("role") == "agent":
            parts.append(str(transcript.get("text") or ""))
    parts.extend(str(text) for text in sandbox.get("agent_response_texts_sanitized", []))
    return "\n".join(parts).lower()


def expected_response_match(sandbox: dict[str, Any]) -> bool:
    joined = agent_text_join(sandbox)
    if not joined.strip():
        return False
    for response in sandbox.get("expected_tool_responses_sanitized", []):
        text = str(response.get("buyer_facing_response") or "").strip().lower()
        if text and (text in joined or joined in text):
            return True
    for response in sandbox.get("tool_responses_sanitized", []):
        text = str(response.get("buyer_facing_response") or "").strip().lower()
        if text and (text in joined or joined in text):
            return True
    return False


def classify_blocker(sandbox: dict[str, Any], project_tool_called: bool, response_follows_project_tool: bool) -> str | None:
    if sandbox.get("synthetic_turns_attempted", 0) == 0:
        return "websocket_client_blocker"
    if sandbox.get("websocket_connected") is not True:
        return "websocket_client_blocker"
    if sandbox.get("synthetic_turns_completed", 0) == 0:
        return "user_text_message_unsupported_or_ignored"
    if not project_tool_called:
        return "tool_invocation_not_observed"
    if not response_follows_project_tool:
        return "project_tool_response_not_observed_in_agent_text"
    if sandbox.get("product_truth_drift_count", 0) or sandbox.get("fake_side_effect_count", 0):
        return "quality_boundary_failed"
    return None


def build_quality_result(sandbox: dict[str, Any]) -> dict[str, Any]:
    project_tool_called = sandbox.get("http_tool_endpoint_request_count", 0) > 0 or sandbox.get("tool_result_sent_count", 0) > 0
    invented_product_facts = sandbox.get("product_truth_drift_count", 0) > 0 or sandbox.get("unsupported_claim_count", 0) > 0
    claimed_side_effects = sandbox.get("fake_side_effect_count", 0) > 0
    no_crm_claims = sandbox.get("fake_side_effect_count", 0) == 0
    no_openai_affiliation = "openai" not in agent_text_join(sandbox)
    response_follows = expected_response_match(sandbox)
    source_boundary_respected = not invented_product_facts and sandbox.get("source_boundary_violation_count", 0) == 0
    tool_boundary_enforced = (
        project_tool_called
        and response_follows
        and source_boundary_respected
        and not claimed_side_effects
        and sandbox.get("internal_label_leak_count", 0) == 0
    )
    blocker_classification = classify_blocker(sandbox, project_tool_called, response_follows)
    return {
        "evaluation_id": "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001",
        "phase": "4J4",
        "source_sandbox_evaluation_id": sandbox.get("evaluation_id"),
        "sandbox_run_status": sandbox.get("run_status"),
        "tool_boundary_enforced": tool_boundary_enforced,
        "project_tool_called": project_tool_called,
        "ultravox_invented_product_facts": invented_product_facts,
        "ultravox_claimed_side_effects": claimed_side_effects,
        "source_boundary_respected": source_boundary_respected,
        "no_crm_email_calendar_claims": no_crm_claims,
        "no_openai_affiliation_claim": no_openai_affiliation,
        "response_follows_project_tool": response_follows,
        "memory_conflict_count": int(sandbox.get("memory_conflict_count", 0)),
        "transcript_quality_notes": transcript_quality_notes(sandbox, response_follows),
        "latency_notes": latency_notes(sandbox),
        "blocker_classification": blocker_classification,
        "agent_transcript_count": sandbox.get("agent_transcript_count", 0),
        "user_transcript_count": sandbox.get("user_transcript_count", 0),
        "synthetic_turns_attempted": sandbox.get("synthetic_turns_attempted", 0),
        "synthetic_turns_completed": sandbox.get("synthetic_turns_completed", 0),
        "http_tool_endpoint_request_count": sandbox.get("http_tool_endpoint_request_count", 0),
        "tool_result_sent_count": sandbox.get("tool_result_sent_count", 0),
        "product_truth_drift_count": sandbox.get("product_truth_drift_count", 0),
        "unsupported_claim_count": sandbox.get("unsupported_claim_count", 0),
        "fake_side_effect_count": sandbox.get("fake_side_effect_count", 0),
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def transcript_quality_notes(sandbox: dict[str, Any], response_follows: bool) -> list[str]:
    notes: list[str] = []
    if sandbox.get("agent_transcript_count", 0) == 0:
        notes.append("No agent transcript was observed, so response quality cannot be accepted.")
    if sandbox.get("user_transcript_count", 0) == 0 and sandbox.get("synthetic_turns_attempted", 0) > 0:
        notes.append("Synthetic user_text_message turns were sent but no user transcript echo was observed.")
    if not response_follows:
        notes.append("No observed agent text matched the project sales-brain buyer_facing_response.")
    if not notes:
        notes.append("Observed transcript stayed within the project-tool response boundary.")
    return notes


def latency_notes(sandbox: dict[str, Any]) -> list[str]:
    metrics = sandbox.get("latency_metrics", {})
    notes = []
    for key in ("tunnel_start_latency_ms", "public_endpoint_valid_request_latency_ms", "create_call_latency_ms", "websocket_connect_latency_ms", "ping_round_trip_ms"):
        if metrics.get(key) is not None:
            notes.append(f"{key}: {metrics[key]}")
    if not notes:
        notes.append("No latency metrics were available.")
    return notes


def recommendation_for(sandbox: dict[str, Any], quality: dict[str, Any]) -> str:
    if sandbox.get("websocket_connected") is not True:
        return "fix joinUrl/WebSocket client"
    if sandbox.get("synthetic_turns_attempted", 0) > 0 and sandbox.get("synthetic_turns_completed", 0) == 0:
        return "audio-input WebSocket sandbox or browser WebRTC SDK next"
    if quality.get("project_tool_called") is not True:
        return "fix tool declaration/prompt/session payload"
    if quality.get("tool_boundary_enforced") is True:
        return "limited synthetic voice/audio sandbox next"
    return "keep Ultravox as research only"


def build_decision(sandbox: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
        "phase": "4J4",
        "recommendation": recommendation_for(sandbox, quality),
        "blocker": sandbox.get("blocker") or quality.get("blocker_classification"),
        "websocket_text_sandbox_run_status": sandbox.get("run_status"),
        "websocket_quality_blocker_classification": quality.get("blocker_classification"),
        "sandbox_run": sandbox.get("sandbox_run"),
        "provider_call_made": sandbox.get("provider_call_made"),
        "provider_call_attempted": sandbox.get("provider_call_attempted"),
        "ultravox_session_created": sandbox.get("ultravox_session_created"),
        "join_url_received": sandbox.get("join_url_received"),
        "websocket_connected": sandbox.get("websocket_connected"),
        "synthetic_turns_attempted": sandbox.get("synthetic_turns_attempted"),
        "synthetic_turns_completed": sandbox.get("synthetic_turns_completed"),
        "tool_call_attempted": sandbox.get("tool_call_attempted"),
        "tool_call_succeeded": sandbox.get("tool_call_succeeded"),
        "tool_boundary_enforced": quality.get("tool_boundary_enforced"),
        "project_tool_called": quality.get("project_tool_called"),
        "response_follows_project_tool": quality.get("response_follows_project_tool"),
        "http_tool_endpoint_request_count": sandbox.get("http_tool_endpoint_request_count"),
        "tool_result_sent_count": sandbox.get("tool_result_sent_count"),
        "agent_transcript_count": sandbox.get("agent_transcript_count"),
        "user_transcript_count": sandbox.get("user_transcript_count"),
        "product_truth_drift_count": sandbox.get("product_truth_drift_count"),
        "unsupported_claim_count": sandbox.get("unsupported_claim_count"),
        "fake_side_effect_count": sandbox.get("fake_side_effect_count"),
        "crm_email_calendar_claim_count": 0 if quality.get("no_crm_email_calendar_claims") is True else sandbox.get("crm_email_calendar_claim_count"),
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "memory_ownership_decision": "project_runtime_owns_canonical_memory",
        "sales_brain_ownership_decision": "project_runtime_owns_sales_brain_and_campaign_truth",
        "ultravox_product_truth_owner": False,
        "side_effects_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "decision_logic": [
            "If WebSocket connection fails: recommend fixing joinUrl/WebSocket client.",
            "If user_text_message is unsupported or ignored: recommend audio-input WebSocket sandbox or browser WebRTC SDK next.",
            "If tool invocation is not observed: recommend fixing tool declaration/prompt/session payload.",
            "If tool boundary works and no drift/fake side effects occur: recommend limited synthetic voice/audio sandbox next.",
            "If Ultravox cannot be made to respect project tool boundary: keep Ultravox as research only.",
            "Always keep live wiring, production calls, and real customer data disallowed.",
        ],
    }


def render_quality_report(quality: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001",
            "",
            f"Tool boundary enforced: `{str(quality['tool_boundary_enforced']).lower()}`",
            f"Project tool called: `{str(quality['project_tool_called']).lower()}`",
            f"Ultravox invented product facts: `{str(quality['ultravox_invented_product_facts']).lower()}`",
            f"Ultravox claimed side effects: `{str(quality['ultravox_claimed_side_effects']).lower()}`",
            f"Source boundary respected: `{str(quality['source_boundary_respected']).lower()}`",
            f"No CRM/email/calendar claims: `{str(quality['no_crm_email_calendar_claims']).lower()}`",
            f"No OpenAI affiliation claim: `{str(quality['no_openai_affiliation_claim']).lower()}`",
            f"Response follows project tool: `{str(quality['response_follows_project_tool']).lower()}`",
            f"Memory conflict count: `{quality['memory_conflict_count']}`",
            f"Blocker classification: `{quality['blocker_classification']}`",
            "",
            "## Transcript Notes",
            *[f"- {note}" for note in quality["transcript_quality_notes"]],
            "",
            "## Latency Notes",
            *[f"- {note}" for note in quality["latency_notes"]],
            "",
            "## Boundaries",
            f"Live wiring allowed: `{str(quality['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(quality['production_call_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(quality['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(quality['response_text_changed']).lower()}`",
            "",
        ]
    )


def render_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Blocker: `{decision['blocker']}`",
            f"WebSocket sandbox run status: `{decision['websocket_text_sandbox_run_status']}`",
            f"WebSocket quality blocker classification: `{decision['websocket_quality_blocker_classification']}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(decision['ultravox_session_created']).lower()}`",
            f"Join URL received: `{str(decision['join_url_received']).lower()}`",
            f"WebSocket connected: `{str(decision['websocket_connected']).lower()}`",
            f"Synthetic turns attempted: `{decision['synthetic_turns_attempted']}`",
            f"Synthetic turns completed: `{decision['synthetic_turns_completed']}`",
            f"Tool call attempted: `{str(decision['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(decision['tool_call_succeeded']).lower()}`",
            f"Tool boundary enforced: `{str(decision['tool_boundary_enforced']).lower()}`",
            f"Project tool called: `{str(decision['project_tool_called']).lower()}`",
            f"Response follows project tool: `{str(decision['response_follows_project_tool']).lower()}`",
            f"HTTP tool endpoint request count: `{decision['http_tool_endpoint_request_count']}`",
            f"Tool result sent count: `{decision['tool_result_sent_count']}`",
            f"Product truth drift count: `{decision['product_truth_drift_count']}`",
            f"Fake side effect count: `{decision['fake_side_effect_count']}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            "",
            "Project runtime owns canonical memory.",
            "Project runtime owns the sales brain and campaign truth.",
            "",
        ]
    )


def main() -> None:
    sandbox = load_json(SANDBOX_RESULT_PATH)
    quality = build_quality_result(sandbox)
    decision = build_decision(sandbox, quality)
    write_json(QUALITY_RESULT_PATH, quality)
    write_text(QUALITY_REPORT_PATH, render_quality_report(quality))
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_decision_report(decision))
    print(json.dumps(quality, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
