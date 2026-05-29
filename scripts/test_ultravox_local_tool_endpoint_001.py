#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.audio_backends.ultravox_local_tool_server import build_server  # noqa: E402
from runtime.audio_backends.ultravox_sales_brain_mock import validate_ultravox_tool_response  # noqa: E402
from scripts.load_local_ultravox_env_001 import load_local_ultravox_env  # noqa: E402


CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_endpoint_config.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LOCAL-TOOL-ENDPOINT-001"
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


def build_request(case: tuple[str, str, str, str], index: int) -> dict[str, Any]:
    case_id, utterance, stage_id, emotion = case
    return {
        "session_id": f"local-http-tool-test-{index:03d}",
        "buyer_utterance_text": utterance,
        "ultravox_session_summary": f"Sanitized short-term context for {case_id}.",
        "project_memory_summary": "Synthetic project memory: project owns canonical memory, campaign truth, and side-effect boundaries.",
        "current_campaign_id": "synthetic_voice_sandbox",
        "detected_emotion_hint": emotion,
        "turn_index": index,
        "requested_action_context": stage_id,
    }


def post_json(url: str, payload: dict[str, Any], token: str | None) -> tuple[int, dict[str, Any]]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["X-Project-Tool-Token"] = token
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, json.loads(body) if body else {}


def evaluate_case(response: dict[str, Any], status: int) -> dict[str, Any]:
    buyer_text = str(response.get("buyer_facing_response") or "")
    validation_errors = validate_ultravox_tool_response(response)
    fake_side_effect_count = count_patterns(buyer_text, FAKE_SIDE_EFFECT_PATTERNS)
    unsupported_claim_count = count_patterns(buyer_text, UNSUPPORTED_CLAIM_PATTERNS)
    internal_label_leak_count = count_internal_language(buyer_text)
    response_short_enough = word_count(buyer_text) <= 34
    passed = (
        status == 200
        and not validation_errors
        and response.get("allowed_to_speak") is True
        and response.get("side_effects_allowed") is False
        and fake_side_effect_count == 0
        and unsupported_claim_count == 0
        and internal_label_leak_count == 0
        and response_short_enough
    )
    return {
        "http_status": status,
        "allowed_to_speak": response.get("allowed_to_speak"),
        "side_effects_allowed": response.get("side_effects_allowed"),
        "fake_side_effect_count": fake_side_effect_count,
        "unsupported_claim_count": unsupported_claim_count,
        "internal_label_leak_count": internal_label_leak_count,
        "response_short_enough": response_short_enough,
        "validation_errors": validation_errors,
        "passed": passed,
        "next_action_id": response.get("next_action_id"),
        "call_should_end": response.get("call_should_end"),
    }


def build_result() -> dict[str, Any]:
    load_local_ultravox_env()
    token = os.environ.get("PROJECT_ULTRAVOX_TOOL_TOKEN") or f"local-test-token-{secrets.token_hex(16)}"
    config = load_json(CONFIG_PATH)
    server = build_server(auth_token=token)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    url = f"http://{config['host']}:{config['port']}{config['path']}"
    case_results: list[dict[str, Any]] = []
    auth_results: dict[str, Any] = {}
    try:
        sample_request = build_request(CASES[0], 1)
        missing_status, _ = post_json(url, sample_request, None)
        invalid_status, _ = post_json(url, sample_request, "invalid-token")
        auth_results = {
            "missing_token_status": missing_status,
            "invalid_token_status": invalid_status,
            "missing_token_rejected": missing_status == 401,
            "invalid_token_rejected": invalid_status == 401,
            "auth_token_printed": False,
        }
        for index, case in enumerate(CASES, start=1):
            status, response = post_json(url, build_request(case, index), token)
            evaluation = evaluate_case(response, status)
            case_results.append(
                {
                    "case_id": case[0],
                    "buyer_utterance_text": case[1],
                    **evaluation,
                }
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    return {
        "evaluation_id": "ULTRAVOX-LOCAL-TOOL-ENDPOINT-001",
        "phase": "4J2",
        "endpoint_id": config["endpoint_id"],
        "host": config["host"],
        "port": config["port"],
        "path": config["path"],
        "localhost_only": True,
        "public_exposure_allowed": False,
        "public_tunnel_opened": False,
        "provider_calls_made": False,
        "ultravox_hosted_call_made": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "auth_required": True,
        "auth_token_present": True,
        "auth_token_printed": False,
        "auth_tests": auth_results,
        "case_count": len(case_results),
        "passed_count": sum(1 for case in case_results if case["passed"]),
        "failed_count": sum(1 for case in case_results if not case["passed"]),
        "synthetic_cases_passed": all(case["passed"] for case in case_results),
        "side_effects_allowed": False,
        "side_effect_safety_result": "pass" if all(case["side_effects_allowed"] is False for case in case_results) else "fail",
        "fake_side_effect_count": sum(case["fake_side_effect_count"] for case in case_results),
        "unsupported_claim_count": sum(case["unsupported_claim_count"] for case in case_results),
        "internal_label_leak_count": sum(case["internal_label_leak_count"] for case in case_results),
        "crm_email_calendar_actions_allowed": False,
        "project_sales_brain_owner": "project_runtime",
        "canonical_memory_owner": "project_runtime",
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "server_sanitized_event_count": len(server.sanitized_events),
        "case_results": case_results,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-LOCAL-TOOL-ENDPOINT-001 Report",
        "",
        "No Ultravox provider call was made.",
        "No public tunnel was opened.",
        "No real customer data, private audio, private transcripts, or side effects were used.",
        "",
        f"Endpoint: `http://{result['host']}:{result['port']}{result['path']}`",
        f"Cases passed: `{result['passed_count']}` / `{result['case_count']}`",
        f"Missing token rejected: `{str(result['auth_tests']['missing_token_rejected']).lower()}`",
        f"Invalid token rejected: `{str(result['auth_tests']['invalid_token_rejected']).lower()}`",
        f"Fake side-effect count: `{result['fake_side_effect_count']}`",
        f"Unsupported claim count: `{result['unsupported_claim_count']}`",
        f"Internal label leak count: `{result['internal_label_leak_count']}`",
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
                f"- HTTP status: `{case['http_status']}`",
                f"- Passed: `{str(case['passed']).lower()}`",
                f"- Next action: `{case['next_action_id']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
