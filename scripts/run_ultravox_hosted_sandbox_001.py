#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_hosted_backend_config.json"
MOCK_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001" / "result.json"
HOSTED_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001"
HOSTED_RESULT_PATH = HOSTED_DIR / "result.json"
HOSTED_REPORT_PATH = HOSTED_DIR / "report.md"
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


def gate_status() -> dict[str, bool]:
    return {
        "ENABLE_ULTRAVOX_SANDBOX=1": os.environ.get("ENABLE_ULTRAVOX_SANDBOX") == "1",
        "ULTRAVOX_API_KEY present": bool(os.environ.get("ULTRAVOX_API_KEY")),
        "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1": os.environ.get("LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS") == "1",
    }


def gates_enabled(gates: dict[str, bool]) -> bool:
    return all(gates.values())


def build_hosted_result() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    gates = gate_status()
    if not gates_enabled(gates):
        run_status = "not_run"
        provider_call_made = False
        blocker = "Ultravox env gates were not enabled; provider sandbox skipped by default."
    else:
        run_status = "blocked"
        provider_call_made = False
        blocker = (
            "Env gates are enabled, but Phase 4J0 has no reviewed no-audio hosted tool-call adapter. "
            "Stop here rather than creating a live provider session without a verified tool boundary."
        )

    return {
        "evaluation_id": "ULTRAVOX-HOSTED-SANDBOX-001",
        "phase": "4J0",
        "backend_id": config["backend_id"],
        "run_status": run_status,
        "blocker": blocker,
        "env_gates": gates,
        "provider_call_made": provider_call_made,
        "provider_call_attempted": False,
        "tool_boundary_supported": None,
        "tool_calls_work": None,
        "latency_ms": None,
        "response_metadata": {},
        "tool_call_behavior": "not_observed_without_provider_run",
        "outbound_phone_calls_made": False,
        "real_customer_data_used": False,
        "synthetic_prompts_only": True,
        "raw_private_audio_or_transcripts_used": False,
        "transcripts_sanitized": True,
        "audio_committed": False,
        "model_weights_downloaded": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": False,
        "training_performed": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "notes": [
            "Default path produces not_run evidence only.",
            "No outbound phone call is supported by this phase.",
            "No real customer audio or transcript is accepted.",
            "Provider-call branch remains gated and blocked until the hosted tool-call boundary is reviewed."
        ],
    }


def render_hosted_report(result: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-HOSTED-SANDBOX-001 Report",
        "",
        f"Run status: `{result['run_status']}`",
        f"Blocker: {result['blocker']}",
        f"Provider call made: `{str(result['provider_call_made']).lower()}`",
        f"Outbound phone calls made: `{str(result['outbound_phone_calls_made']).lower()}`",
        f"Real customer data used: `{str(result['real_customer_data_used']).lower()}`",
        f"Raw private audio or transcripts used: `{str(result['raw_private_audio_or_transcripts_used']).lower()}`",
        f"Audio committed: `{str(result['audio_committed']).lower()}`",
        f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
        f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
        f"Runtime behavior changed: `{str(result['runtime_behavior_changed']).lower()}`",
        f"Response text changed: `{str(result['response_text_changed']).lower()}`",
        "",
        "## Env Gates",
        "",
    ]
    for gate, enabled in result["env_gates"].items():
        lines.append(f"- {gate}: `{str(enabled).lower()}`")
    lines.extend(
        [
            "",
            "## Tool Boundary",
            "",
            "Tool-call behavior was not observed because no provider run occurred.",
            "The project runtime remains the sales brain, campaign truth source, verifier, and canonical memory owner.",
            "",
        ]
    )
    return "\n".join(lines)


def expected_recommendation(mock: dict[str, Any], hosted: dict[str, Any]) -> str:
    mock_passed = mock.get("summary", {}).get("tool_boundary_passed") is True
    provider_run = hosted.get("provider_call_made") is True and hosted.get("run_status") == "provider_run"
    provider_tool_calls_work = hosted.get("tool_calls_work") is True
    provider_failed_boundary = hosted.get("tool_boundary_supported") is False or hosted.get("run_status") == "failed"
    if not mock_passed:
        return "fix tool contract before any provider sandbox"
    if mock_passed and not provider_run:
        return "optional gated Ultravox hosted sandbox next"
    if provider_run and provider_tool_calls_work:
        return "limited synthetic voice call evaluation next"
    if provider_failed_boundary:
        return "keep Ultravox as research/reference only"
    return "keep Ultravox as research/reference only"


def build_decision(hosted: dict[str, Any]) -> dict[str, Any]:
    if MOCK_RESULT_PATH.is_file():
        mock = load_json(MOCK_RESULT_PATH)
    else:
        mock = {"summary": {"tool_boundary_passed": False}}
    recommendation = expected_recommendation(mock, hosted)
    return {
        "evaluation_id": "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
        "phase": "4J0",
        "recommendation": recommendation,
        "mock_boundary_passed": mock.get("summary", {}).get("tool_boundary_passed") is True,
        "hosted_sandbox_run_status": hosted["run_status"],
        "provider_call_made": hosted["provider_call_made"],
        "tool_calls_work": hosted["tool_calls_work"],
        "tool_boundary_supported": hosted["tool_boundary_supported"],
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
            "If mock boundary fails: fix tool contract before any provider sandbox.",
            "If mock boundary passes and provider call not run: optional gated Ultravox hosted sandbox next.",
            "If provider sandbox runs and tool calls work: limited synthetic voice call evaluation next.",
            "If provider sandbox fails or cannot support the tool boundary: keep Ultravox as research/reference only."
        ],
    }


def render_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001 Report",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Mock boundary passed: `{str(decision['mock_boundary_passed']).lower()}`",
            f"Hosted sandbox run status: `{decision['hosted_sandbox_run_status']}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Tool calls work: `{str(decision['tool_calls_work']).lower()}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(decision['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(decision['response_text_changed']).lower()}`",
            "",
            "Project runtime owns canonical memory.",
            "Project runtime owns the sales brain and campaign truth.",
            "Ultravox remains a hosted speech-native interface candidate only.",
            "Side effects remain blocked.",
            "",
        ]
    )


def main() -> None:
    result = build_hosted_result()
    write_json(HOSTED_RESULT_PATH, result)
    write_text(HOSTED_REPORT_PATH, render_hosted_report(result))
    decision = build_decision(result)
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_decision_report(decision))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
