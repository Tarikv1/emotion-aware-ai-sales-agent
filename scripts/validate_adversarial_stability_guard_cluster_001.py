#!/usr/bin/env python3
"""Validate the 4F4 adversarial stability-guard cluster fixes."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "ADVERSARIAL-STABILITY-GUARD-CLUSTER-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]

FORBIDDEN_MENU = [
    "which part should i check first",
    "premium or budget, coverage fit, or renewal",
    "manual work, integration risk, or visibility gap",
    "plan fit, coverage or availability, or contract or switching",
    "if not, i can stop here",
]

FORBIDDEN_INTERNAL = [
    "i should not",
    "approved qualified reviewer path",
    "approved scope",
    "transfer-or-escalate",
    "i can send this to",
]


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    campaign_id: str
    campaign_config_path: Path | None
    buyer_script: tuple[str, ...]
    expected_gap: str | None
    expected_terms: tuple[str, ...]
    category: str


SCENARIOS = [
    Scenario(
        "insurance-coverage-thing-impact",
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        ("__agent_open__", "yeah", "coverage thing is confusing", "it wastes time"),
        "coverage_fit",
        ("coverage",),
        "near_miss_configured_gap",
    ),
    Scenario(
        "insurance-payment-pressure-impact",
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        ("__agent_open__", "yeah", "payment pressure is a problem", "it wastes time"),
        "premium_or_budget",
        ("premium", "budget", "payment"),
        "near_miss_configured_gap",
    ),
    Scenario(
        "b2b-integration-thing",
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        ("__agent_open__", "yeah", "integration thing is confusing"),
        "integration_risk",
        ("integration",),
        "near_miss_configured_gap",
    ),
    Scenario(
        "b2b-visibility-thing-impact",
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        ("__agent_open__", "yeah", "visibility thing is unclear", "it wastes time"),
        "visibility_gap",
        ("visibility",),
        "near_miss_configured_gap",
    ),
    Scenario(
        "telecom-plane-fit",
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        ("__agent_open__", "yeah", "plane fit is confusing"),
        "plan_fit",
        ("plan",),
        "near_miss_configured_gap",
    ),
    Scenario(
        "membership-plan-thing",
        "synthetic-membership-plan-review",
        EXAMPLES / "synthetic-membership-plan-review.json",
        ("__agent_open__", "yeah", "plan thing is confusing"),
        "plan_fit",
        ("plan",),
        "near_miss_configured_gap",
    ),
    Scenario(
        "routesignal-coverage-mismatch-boundary",
        "routesignal_live_demo",
        None,
        ("__agent_open__", "can you tell me exactly what coverage I need"),
        None,
        ("coverage", "call", "scope"),
        "customer_facing_scope_boundary",
    ),
    Scenario(
        "telecom-plan-fit-coverage-boundary",
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        ("__agent_open__", "yeah start with how much is your product", "how about the plane fit and coverage"),
        None,
        ("plan", "coverage"),
        "customer_facing_scope_boundary",
    ),
    Scenario(
        "b2b-integration-boundary",
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        ("__agent_open__", "yeah", "integration thing is confusing"),
        "integration_risk",
        ("integration",),
        "customer_facing_scope_boundary",
    ),
]


def norm(text: Any) -> str:
    return " ".join(str(text or "").lower().replace("'", " ").split())


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    action = (packet.get("dialogue_manager") or {}).get("selected_action") or {}
    return action if isinstance(action, dict) else {}


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or selected_action(packet).get("call_control") or "")


def universal_frame(packet: dict[str, Any]) -> dict[str, Any]:
    frame = packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}
    return frame if isinstance(frame, dict) else {}


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "live_tts_used": bool(packet.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or tts.get("provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "conversation_continuity": packet.get("conversation_continuity") or packet.get("demo_session_continuity") or {},
            "conversation_memory": packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
            "universal_policy_frame": universal_frame(packet),
        }
    )


def build_turn(transcript: str, state: dict[str, Any], scenario: Scenario) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / scenario.scenario_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=scenario.campaign_config_path,
        session_id=scenario.scenario_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def evaluate(scenario: Scenario) -> dict[str, Any]:
    state: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    failures: list[str] = []
    for index, transcript in enumerate(scenario.buyer_script, start=1):
        packet = build_turn(transcript, state, scenario)
        action = selected_action(packet)
        frame = universal_frame(packet)
        response = final_response(packet)
        turns.append(
            {
                "turn_index": index,
                "buyer_utterance": transcript,
                "final_response": response,
                "call_control": call_control(packet),
                "selected_action_source": action.get("source"),
                "semantic": action.get("semantic"),
                "target_gap": action.get("target_gap"),
                "universal_policy_frame": frame,
                "buyer_move_id": frame.get("buyer_move_id"),
                "side_effect_flags": side_effect_flags(packet),
            }
        )

    final = turns[-1]
    response_norm = norm(final["final_response"])
    source = str(final.get("selected_action_source") or "")
    target_gap = str(final.get("target_gap") or "")
    frame = final.get("universal_policy_frame") or {}
    frame_gap = str(frame.get("selected_gap") or frame.get("confirmed_gap_id") or "")
    side_effects = {key: any(bool((turn.get("side_effect_flags") or {}).get(key)) for turn in turns) for key in SIDE_EFFECT_KEYS}

    if any(value in response_norm for value in FORBIDDEN_MENU):
        failures.append("full_menu_or_stop_offer_reopened")
    if any(value in response_norm for value in FORBIDDEN_INTERNAL):
        failures.append("internal_wording_leak")
    if source == "pre_speech_conversation_stability_guard":
        failures.append("stability_guard_selected_final_action")
    if scenario.expected_gap and scenario.expected_gap not in {target_gap, frame_gap}:
        failures.append(f"expected_gap_not_preserved:{scenario.expected_gap}")
    if scenario.expected_terms and not any(term in response_norm for term in scenario.expected_terms):
        failures.append("response_does_not_reference_expected_context")
    if final["call_control"] == "transfer-or-escalate":
        failures.append("fake_or_premature_escalation")
    if final["call_control"] not in {"continue-call", "end-call"}:
        failures.append(f"unexpected_call_control:{final['call_control']}")
    for key, value in side_effects.items():
        if value:
            failures.append(f"side_effect_true:{key}")

    return {
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "campaign_id": scenario.campaign_id,
        "campaign_config_path": str(scenario.campaign_config_path.relative_to(ROOT)).replace("\\", "/") if scenario.campaign_config_path else None,
        "buyer_script": list(scenario.buyer_script),
        "expected_gap": scenario.expected_gap,
        "turns": turns,
        "final_response": final["final_response"],
        "selected_action_source": source,
        "call_control": final["call_control"],
        "failures": failures,
        "passed": not failures,
        "side_effect_flags": side_effects,
    }


def generate() -> dict[str, Any]:
    scenarios = [evaluate(scenario) for scenario in SCENARIOS]
    failure_counts = Counter(failure for scenario in scenarios for failure in scenario["failures"])
    by_category = Counter(str(scenario["category"]) for scenario in scenarios)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if all(scenario["passed"] for scenario in scenarios) else "fail",
        "scenario_count": len(scenarios),
        "pass_count": sum(1 for scenario in scenarios if scenario["passed"]),
        "failure_count": sum(1 for scenario in scenarios if not scenario["passed"]),
        "failure_types": dict(sorted(failure_counts.items())),
        "category_counts": dict(sorted(by_category.items())),
        "scenarios": scenarios,
        "side_effect_boundary": {
            key: any(bool((scenario.get("side_effect_flags") or {}).get(key)) for scenario in scenarios)
            for key in SIDE_EFFECT_KEYS
        },
        "runtime_behavior_changed": True,
    }
    return result


def write_outputs(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Scenario count: `{result['scenario_count']}`",
        f"- Pass count: `{result['pass_count']}`",
        f"- Failure count: `{result['failure_count']}`",
        "",
        "## Failure Types",
        *(f"- `{key}`: `{value}`" for key, value in result["failure_types"].items()),
        "",
        "## Scenarios",
    ]
    for scenario in result["scenarios"]:
        lines.extend(
            [
                f"### {scenario['scenario_id']}",
                f"- Status: `{'pass' if scenario['passed'] else 'fail'}`",
                f"- Campaign: `{scenario['campaign_id']}`",
                f"- Category: `{scenario['category']}`",
                f"- Source: `{scenario['selected_action_source']}`",
                f"- Call control: `{scenario['call_control']}`",
                f"- Failures: `{', '.join(scenario['failures'])}`",
                f"- Final response: {scenario['final_response']}",
                "",
            ]
        )
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = generate()
    write_outputs(result)
    print(json.dumps({
        "checkpoint_id": CHECKPOINT_ID,
        "status": result["status"],
        "scenario_count": result["scenario_count"],
        "pass_count": result["pass_count"],
        "failure_count": result["failure_count"],
        "failure_types": result["failure_types"],
    }, indent=2, sort_keys=True))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
