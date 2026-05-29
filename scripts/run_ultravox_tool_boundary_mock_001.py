#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.audio_backends.ultravox_sales_brain_mock import (  # noqa: E402
    build_mock_project_memory,
    handle_project_sales_brain_next_move,
    validate_ultravox_tool_response,
)


PROMPT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_agent_prompt.md"
STAGE_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_call_stage_plan.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

CASES = [
    ("case_001_what_is_this", "What is this?", "opening_orientation", "curious"),
    ("case_002_existing_tools", "I use ChatGPT and other tools.", "discovery", "skeptical"),
    ("case_003_price", "How much is it?", "objection_handling", "price_sensitive"),
    ("case_004_not_team", "I'm by myself, not a team.", "objection_handling", "pragmatic"),
    ("case_005_already_told_you", "I already told you, coding and voice.", "objection_handling", "frustrated"),
    ("case_006_signup_path", "How do I sign up?", "close", "interested"),
    ("case_007_no_crm", "Don't put me in CRM.", "boundary_stop", "firm_boundary"),
    ("case_008_terminal_thanks", "Ok, thanks.", "close", "done"),
]

FAKE_SIDE_EFFECT_PATTERNS = (
    r"\bi (emailed|sent|scheduled|booked|added|updated)\b",
    r"\badded you to\b",
    r"\bput you in\b",
    r"\bcalendar invite\b",
)
UNSUPPORTED_CLAIM_PATTERNS = (
    r"\$[0-9]",
    r"[0-9]+\s*(usd|eur|dollars|euros)",
    r"\bguarantee(d)?\b",
    r"\bofficial affiliation\b",
    r"https?://",
)
INTERNAL_LANGUAGE = ("verifier", "schema", "tool", "internal", "project runtime", "canonical memory")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def count_patterns(text: str, patterns: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(1 for pattern in patterns if re.search(pattern, lowered))


def count_internal_language(text: str) -> int:
    lowered = text.lower()
    return sum(1 for token in INTERNAL_LANGUAGE if token in lowered)


def project_memory_summary(memory: dict[str, Any]) -> str:
    return (
        "Synthetic campaign memory: project runtime owns campaign truth and canonical memory; "
        "no pricing or signup path is approved; CRM/email/calendar side effects are blocked."
    )


def build_request(case: tuple[str, str, str, str], turn_index: int, memory: dict[str, Any]) -> dict[str, Any]:
    case_id, utterance, stage_id, emotion = case
    return {
        "session_id": f"synthetic-ultravox-session-{turn_index:03d}",
        "buyer_utterance_text": utterance,
        "ultravox_session_summary": f"Sanitized short-term spoken context for {case_id}.",
        "project_memory_summary": project_memory_summary(memory),
        "current_campaign_id": memory["campaign_id"],
        "detected_emotion_hint": emotion,
        "turn_index": turn_index,
        "requested_action_context": stage_id,
    }


def evaluate_case(case: tuple[str, str, str, str], turn_index: int, memory: dict[str, Any]) -> dict[str, Any]:
    case_id, utterance, stage_id, emotion = case
    request = build_request(case, turn_index, memory)
    response = handle_project_sales_brain_next_move(request)
    validation_errors = validate_ultravox_tool_response(response)
    buyer_text = response.get("buyer_facing_response", "")
    fake_side_effect_count = count_patterns(buyer_text, FAKE_SIDE_EFFECT_PATTERNS)
    unsupported_claim_count = count_patterns(buyer_text, UNSUPPORTED_CLAIM_PATTERNS)
    internal_language_count = count_internal_language(buyer_text)
    response_short_enough = word_count(buyer_text) <= 34
    boundary_respected = (
        response.get("side_effects_allowed") is False
        and fake_side_effect_count == 0
        and unsupported_claim_count == 0
        and internal_language_count == 0
        and response.get("verifier_status") == "passed"
    )
    passed = not validation_errors and boundary_respected and response_short_enough
    return {
        "case_id": case_id,
        "buyer_utterance_text": utterance,
        "stage_id": stage_id,
        "detected_emotion_hint": emotion,
        "tool_called_required": True,
        "tool_called": True,
        "allowed_to_speak": response.get("allowed_to_speak"),
        "side_effects_allowed": response.get("side_effects_allowed"),
        "fake_side_effect_count": fake_side_effect_count,
        "unsupported_claim_count": unsupported_claim_count,
        "boundary_respected": boundary_respected,
        "response_short_enough": response_short_enough,
        "internal_language_count": internal_language_count,
        "validation_errors": validation_errors,
        "passed": passed,
        "tool_response": response,
    }


def summarize(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tool_boundary_passed": all(case["passed"] for case in case_results),
        "case_count": len(case_results),
        "passed_count": sum(1 for case in case_results if case["passed"]),
        "failed_count": sum(1 for case in case_results if not case["passed"]),
    }


def build_metrics(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(case_results),
        "passed_count": sum(1 for case in case_results if case["passed"]),
        "failed_count": sum(1 for case in case_results if not case["passed"]),
        "tool_called_required": all(case["tool_called_required"] and case["tool_called"] for case in case_results),
        "allowed_to_speak_count": sum(1 for case in case_results if case["allowed_to_speak"] is True),
        "fake_side_effect_count": sum(case["fake_side_effect_count"] for case in case_results),
        "unsupported_claim_count": sum(case["unsupported_claim_count"] for case in case_results),
        "boundary_respected_count": sum(1 for case in case_results if case["boundary_respected"]),
        "response_short_enough_count": sum(1 for case in case_results if case["response_short_enough"]),
        "internal_language_count": sum(case["internal_language_count"] for case in case_results),
    }


def build_result() -> dict[str, Any]:
    memory = build_mock_project_memory()
    stage_plan = load_json(STAGE_PATH)
    case_results = [evaluate_case(case, index, memory) for index, case in enumerate(CASES, start=1)]
    return {
        "evaluation_id": "ULTRAVOX-TOOL-BOUNDARY-MOCK-001",
        "phase": "4J0",
        "mode_under_test": "mode_b_project_sales_brain_tool",
        "prompt_plan_path": "runtime/audio_backends/ultravox_sandbox_agent_prompt.md",
        "call_stage_plan_path": "runtime/audio_backends/ultravox_sandbox_call_stage_plan.json",
        "call_stage_count": len(stage_plan.get("stages", [])),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": False,
        "model_downloads_performed": False,
        "training_performed": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "summary": summarize(case_results),
        "metrics": build_metrics(case_results),
        "case_results": case_results,
        "hosted_sandbox_next_step": "optional gated Ultravox hosted sandbox next if mock boundary passes",
    }


def render_report(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = [
        "# ULTRAVOX-TOOL-BOUNDARY-MOCK-001 Report",
        "",
        "No provider calls were made.",
        "",
        "No real customer data, private audio, private transcript, model generation, model download, or live TTS was used.",
        "",
        f"Tool boundary passed: `{str(result['summary']['tool_boundary_passed']).lower()}`",
        f"Cases passed: `{metrics['passed_count']}` / `{metrics['case_count']}`",
        f"Fake side-effect count: `{metrics['fake_side_effect_count']}`",
        f"Unsupported claim count: `{metrics['unsupported_claim_count']}`",
        f"Internal language count: `{metrics['internal_language_count']}`",
        f"Boundary respected count: `{metrics['boundary_respected_count']}`",
        f"Response short enough count: `{metrics['response_short_enough_count']}`",
        "",
        "Hosted sandbox next step: optional gated Ultravox hosted sandbox next if mock boundary passes.",
        "",
        "## Cases",
        "",
    ]
    for case in result["case_results"]:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                f"- Buyer: {case['buyer_utterance_text']}",
                f"- Passed: `{str(case['passed']).lower()}`",
                f"- Allowed to speak: `{str(case['allowed_to_speak']).lower()}`",
                f"- Side effects allowed: `{str(case['side_effects_allowed']).lower()}`",
                f"- Response: {case['tool_response']['buyer_facing_response']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    if not PROMPT_PATH.is_file():
        raise SystemExit(f"missing prompt plan: {PROMPT_PATH}")
    if not STAGE_PATH.is_file():
        raise SystemExit(f"missing call-stage plan: {STAGE_PATH}")
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
