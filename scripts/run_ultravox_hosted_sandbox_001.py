#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.load_local_ultravox_env_001 import (  # noqa: E402
    ALLOW_GATE,
    API_KEY_ENV,
    ENABLE_GATE,
    UnsafeUltravoxEnvFile,
    load_local_ultravox_env,
)


CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_hosted_backend_config.json"
MOCK_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001" / "result.json"
HOSTED_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001"
HOSTED_RESULT_PATH = HOSTED_DIR / "result.json"
HOSTED_REPORT_PATH = HOSTED_DIR / "report.md"
QUALITY_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-QUALITY-001"
QUALITY_RESULT_PATH = QUALITY_DIR / "result.json"
QUALITY_REPORT_PATH = QUALITY_DIR / "report.md"
NOTE_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-DASHBOARD-VS-API-NOTE-001"
NOTE_RESULT_PATH = NOTE_DIR / "result.json"
NOTE_REPORT_PATH = NOTE_DIR / "report.md"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"

CREATE_CALL_URL = "https://api.ultravox.ai/api/calls"
DELETE_CALL_URL_TEMPLATE = "https://api.ultravox.ai/api/calls/{call_id}"
MAX_SYNTHETIC_CASES = 3
SYNTHETIC_CASES = [
    "What is this?",
    "I use ChatGPT and other AI tools.",
    "Don't put me in CRM.",
]
SOURCE_GROUNDING = [
    {
        "url": "https://docs.ultravox.ai/gettingstarted/how-ultravox-works",
        "claim": "Ultravox supports REST call creation and joining through SDKs, telephony, or WebSockets; API integration gives control over custom tools and call flows."
    },
    {
        "url": "https://docs.ultravox.ai/tools/overview",
        "claim": "Tools connect agents to external systems and can retrieve information or perform actions."
    },
    {
        "url": "https://docs.ultravox.ai/tools/custom/http-vs-client-tools",
        "claim": "HTTP tools run on your server and Ultravox calls them via HTTP; client tools run in the client application."
    },
    {
        "url": "https://docs.ultravox.ai/tools/custom/durable-vs-temporary-tools",
        "claim": "Temporary tools are defined inline for API-created calls; durable tools are reusable and can be managed through API or web app."
    },
    {
        "url": "https://docs.ultravox.ai/agents/call-stages",
        "claim": "Call stages can use tools for stage changes and need explicit prompt/tool configuration."
    },
    {
        "url": "https://docs.ultravox.ai/gettingstarted/prompting",
        "claim": "Prompts should contain full voice-agent behavior, including tool use and spoken-response guidance."
    }
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def redact_error(error: BaseException) -> str:
    text = str(error)
    key = os.environ.get(API_KEY_ENV)
    if key:
        text = text.replace(key, "<redacted>")
    return text[:800]


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        raw = error.read(2048)
    except Exception:
        raw = b""
    text = raw.decode("utf-8", errors="replace")
    key = os.environ.get(API_KEY_ENV)
    if key:
        text = text.replace(key, "<redacted>")
    return " ".join(text.split())[:800]


def gate_status(metadata: dict[str, bool]) -> dict[str, bool]:
    return {
        "ENABLE_ULTRAVOX_SANDBOX=1": os.environ.get(ENABLE_GATE) == "1",
        "ULTRAVOX_API_KEY present": metadata["api_key_present"],
        "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1": os.environ.get(ALLOW_GATE) == "1",
    }


def public_tool_endpoint() -> tuple[bool, str | None]:
    value = os.environ.get("ULTRAVOX_PUBLIC_TOOL_URL", "").strip()
    if not value:
        return False, None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return False, "unsafe_non_https_tool_endpoint"
    return True, parsed.netloc


def build_temporary_tool_definition(tool_url: str) -> dict[str, Any]:
    fields = [
        ("session_id", "Synthetic session id."),
        ("buyer_utterance_text", "Sanitized buyer utterance text."),
        ("ultravox_session_summary", "Sanitized short-term Ultravox context."),
        ("project_memory_summary", "Project-owned memory summary."),
        ("current_campaign_id", "Current synthetic campaign id."),
        ("detected_emotion_hint", "Optional emotion hint."),
        ("turn_index", "Turn index."),
        ("requested_action_context", "Requested action context."),
    ]
    return {
        "temporaryTool": {
            "modelToolName": "project_sales_brain_next_move",
            "description": (
                "Call the project-owned sales brain for every sales move. Use only its buyer_facing_response. "
                "Do not invent product facts or claim CRM, email, calendar, or other side effects."
            ),
            "dynamicParameters": [
                {
                    "name": name,
                    "location": "PARAMETER_LOCATION_BODY",
                    "schema": {"type": "string", "description": description},
                    "required": True,
                }
                for name, description in fields
            ],
            "http": {
                "baseUrlPattern": tool_url,
                "httpMethod": "POST",
            },
        }
    }


def build_call_body(tool_url: str) -> dict[str, Any]:
    return {
        "model": "fixie-ai/ultravox",
        "recordingEnabled": False,
        "firstSpeaker": "FIRST_SPEAKER_AGENT",
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": 48000,
                "outputSampleRate": 48000,
                "clientBufferSizeMs": 60,
                "dataMessages": {
                    "callStarted": True,
                    "transcript": True,
                    "callEvent": True,
                    "debug": False,
                },
            }
        },
        "maxDuration": "20s",
        "systemPrompt": (
            "You are Ultravox, the voice interface for a synthetic sandbox. "
            "Use project_sales_brain_next_move for sales guidance before buyer-facing sales answers. "
            "The project tool owns product truth, campaign truth, verifier decisions, side-effect boundaries, and canonical memory. "
            "Do not invent product facts, do not claim OpenAI affiliation, and do not claim email, calendar, CRM, or follow-up actions. "
            "Keep responses short and phone-friendly. If the buyer says stop or no contact, respect it immediately."
        ),
        "selectedTools": [build_temporary_tool_definition(tool_url)],
        "metadata": {
            "project": "emotion-aware-ai-sales-agent",
            "milestone": "ULTRAVOX-HOSTED-SANDBOX-001",
            "synthetic": "true",
            "realCustomerData": "false",
            "outboundPhoneCall": "false",
        },
    }


def create_provider_call(tool_url: str, api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        CREATE_CALL_URL,
        data=json.dumps(build_call_body(tool_url), ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
            call_id = payload.get("callId") or payload.get("call_id") or payload.get("id")
            join_url = payload.get("joinUrl") or payload.get("join_url")
            return {
                "api_call_made": True,
                "http_status": response.status,
                "latency_ms": elapsed_ms(start),
                "call_id_suffix": str(call_id)[-8:] if call_id else None,
                "join_url_received": bool(join_url),
                "join_url_host": urlparse(join_url).netloc if join_url else None,
                "provider_error": None,
                "call_id_for_cleanup": call_id,
            }
    except urllib.error.HTTPError as error:
        return {
            "api_call_made": True,
            "http_status": error.code,
            "latency_ms": elapsed_ms(start),
            "call_id_suffix": None,
            "join_url_received": False,
            "join_url_host": None,
            "provider_error": read_error_body(error),
            "call_id_for_cleanup": None,
        }
    except Exception as error:
        return {
            "api_call_made": True,
            "http_status": None,
            "latency_ms": elapsed_ms(start),
            "call_id_suffix": None,
            "join_url_received": False,
            "join_url_host": None,
            "provider_error": redact_error(error),
            "call_id_for_cleanup": None,
        }


def delete_provider_call(call_id: str | None, api_key: str) -> dict[str, Any]:
    if not call_id:
        return {"delete_api_call_made": False, "delete_http_status": None, "delete_latency_ms": None, "deleted": False}
    request = urllib.request.Request(
        DELETE_CALL_URL_TEMPLATE.replace("{call_id}", call_id),
        method="DELETE",
        headers={"X-API-Key": api_key},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return {
                "delete_api_call_made": True,
                "delete_http_status": response.status,
                "delete_latency_ms": elapsed_ms(start),
                "deleted": 200 <= response.status < 300,
            }
    except Exception as error:
        return {
            "delete_api_call_made": True,
            "delete_http_status": None,
            "delete_latency_ms": elapsed_ms(start),
            "deleted": False,
            "delete_error": redact_error(error),
        }


def boundary_fields() -> dict[str, Any]:
    return {
        "outbound_phone_call_made": False,
        "outbound_phone_calls_made": False,
        "real_customer_data_used": False,
        "synthetic_prompts_only": True,
        "raw_private_audio_or_transcripts_used": False,
        "transcripts_sanitized": True,
        "raw_audio_stored": False,
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
    }


def build_hosted_result() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    try:
        env_metadata = load_local_ultravox_env()
        unsafe_secret_file = False
    except UnsafeUltravoxEnvFile:
        env_metadata = {
            "env_file_exists": True,
            "env_file_ignored_by_git": False,
            "env_file_loaded": False,
            "api_key_present": bool(os.environ.get(API_KEY_ENV)),
            "gates_enabled": False,
        }
        unsafe_secret_file = True

    gates = gate_status(env_metadata)
    enable_flags_set = gates["ENABLE_ULTRAVOX_SANDBOX=1"] and gates["LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1"]
    endpoint_available, endpoint_host_or_error = public_tool_endpoint()

    run_status = "not_run"
    sandbox_run = False
    provider_call_made = False
    provider_call_attempted = False
    blocker = "Ultravox env gates were not enabled; provider sandbox skipped by default."
    tool_call_supported: bool | str = "unknown"
    tool_call_attempted = False
    tool_call_succeeded = False
    tool_boundary_supported = None
    tool_calls_work = None
    browser_websocket_session_mode_used = "none"
    latency_metrics: dict[str, Any] = {}
    response_metadata: dict[str, Any] = {}
    create_call: dict[str, Any] = {"api_call_made": False}
    delete_call: dict[str, Any] = {"delete_api_call_made": False}

    if unsafe_secret_file:
        run_status = "unsafe_secret_file"
        blocker = "runtime/config/local/ultravox.env exists but is not ignored by Git; script refused to read it."
    elif not enable_flags_set:
        blocker = "Ultravox env gates were not enabled; provider sandbox skipped by default."
    elif not env_metadata["api_key_present"]:
        run_status = "blocked_missing_api_key"
        blocker = "Ultravox provider gates were enabled, but no API key was present in process env or ignored local env file."
    elif endpoint_host_or_error == "unsafe_non_https_tool_endpoint":
        run_status = "unsafe_tool_endpoint"
        blocker = "ULTRAVOX_PUBLIC_TOOL_URL was present but was not a public HTTPS URL."
    elif not endpoint_available:
        run_status = "blocked_no_public_tool_endpoint"
        blocker = "Ultravox hosted HTTP tools require a public HTTPS tool endpoint or a client-tool strategy; none is available in this phase."
    else:
        provider_call_attempted = True
        create_call = create_provider_call(os.environ["ULTRAVOX_PUBLIC_TOOL_URL"].strip(), os.environ[API_KEY_ENV])
        provider_call_made = create_call["api_call_made"]
        delete_call = delete_provider_call(create_call.get("call_id_for_cleanup"), os.environ[API_KEY_ENV])
        create_call.pop("call_id_for_cleanup", None)
        sandbox_run = create_call.get("http_status") is not None and 200 <= int(create_call["http_status"]) < 300
        run_status = "provider_session_created" if sandbox_run else "provider_create_failed"
        blocker = (
            "Provider session was created but no interactive audio turns were run; tool invocation was not attempted."
            if sandbox_run
            else "Provider create-call request failed before any interactive turn."
        )
        browser_websocket_session_mode_used = "server_websocket_session_creation_only"
        latency_metrics = {
            "create_call_latency_ms": create_call.get("latency_ms"),
            "delete_call_latency_ms": delete_call.get("delete_latency_ms"),
        }
        response_metadata = {
            "create_http_status": create_call.get("http_status"),
            "join_url_received": create_call.get("join_url_received"),
            "join_url_host": create_call.get("join_url_host"),
            "call_id_suffix": create_call.get("call_id_suffix"),
            "provider_error": create_call.get("provider_error"),
        }

    return {
        "evaluation_id": "ULTRAVOX-HOSTED-SANDBOX-001",
        "phase": "4J1",
        "backend_id": config["backend_id"],
        "run_status": run_status,
        "sandbox_run": sandbox_run,
        "blocker": blocker,
        "env_file_exists": env_metadata["env_file_exists"],
        "env_file_ignored_by_git": env_metadata["env_file_ignored_by_git"],
        "env_file_loaded": env_metadata["env_file_loaded"],
        "env_file_used": env_metadata["env_file_loaded"],
        "api_key_present": env_metadata["api_key_present"],
        "env_gates": gates,
        "provider_call_made": provider_call_made,
        "provider_call_attempted": provider_call_attempted,
        "browser_websocket_session_mode_used": browser_websocket_session_mode_used,
        "public_tool_endpoint_required": True,
        "public_tool_endpoint_available": endpoint_available,
        "public_tool_endpoint_host": endpoint_host_or_error if endpoint_available else None,
        "tool_call_supported": tool_call_supported,
        "tool_call_attempted": tool_call_attempted,
        "tool_call_succeeded": tool_call_succeeded,
        "tool_boundary_supported": tool_boundary_supported,
        "tool_calls_work": tool_calls_work,
        "synthetic_case_count": 0,
        "synthetic_cases_planned": SYNTHETIC_CASES[:MAX_SYNTHETIC_CASES],
        "provider_minutes_budget_note": "user reported about 30 minutes free use; phase intentionally minimal",
        "product_truth_drift_count": 0,
        "unsupported_claim_count": 0,
        "fake_side_effect_count": 0,
        "crm_email_calendar_claim_count": 0,
        "internal_label_leak_count": 0,
        "source_boundary_violation_count": 0,
        "memory_conflict_count": 0,
        "latency_metrics": latency_metrics,
        "transcript_metadata": {"available": False, "stored": False, "sanitized": True},
        "response_metadata": response_metadata,
        "create_call": create_call,
        "delete_call": delete_call,
        **boundary_fields(),
        "source_grounding": SOURCE_GROUNDING,
        "notes": [
            "No outbound phone call is supported or attempted.",
            "No real customer audio or transcript is accepted.",
            "No API key value is printed or written to evidence.",
            "Provider call is skipped unless env gates and a public HTTPS tool endpoint are both available."
        ],
    }


def render_hosted_report(result: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-HOSTED-SANDBOX-001 Report",
        "",
        f"Run status: `{result['run_status']}`",
        f"Sandbox run: `{str(result['sandbox_run']).lower()}`",
        f"Blocker: {result['blocker']}",
        f"Env file exists: `{str(result['env_file_exists']).lower()}`",
        f"Env file ignored by Git: `{str(result['env_file_ignored_by_git']).lower()}`",
        f"Env file loaded: `{str(result['env_file_loaded']).lower()}`",
        f"API key present: `{str(result['api_key_present']).lower()}`",
        f"Provider call made: `{str(result['provider_call_made']).lower()}`",
        f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
        f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
        f"Public tool endpoint required: `{str(result['public_tool_endpoint_required']).lower()}`",
        f"Public tool endpoint available: `{str(result['public_tool_endpoint_available']).lower()}`",
        f"Synthetic cases attempted: `{result['synthetic_case_count']}`",
        f"Outbound phone calls made: `{str(result['outbound_phone_call_made']).lower()}`",
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
            f"Tool-call behavior: `{result['tool_call_supported']}` support, attempted `{str(result['tool_call_attempted']).lower()}`.",
            "The project runtime remains the sales brain, campaign truth source, verifier, and canonical memory owner.",
            "",
            "## Source Grounding",
            "",
        ]
    )
    for source in result["source_grounding"]:
        lines.append(f"- [{source['url']}]({source['url']}): {source['claim']}")
    lines.append("")
    return "\n".join(lines)


def expected_recommendation(mock: dict[str, Any], hosted: dict[str, Any]) -> str:
    mock_passed = mock.get("summary", {}).get("tool_boundary_passed") is True
    provider_run = hosted.get("provider_call_made") is True and hosted.get("sandbox_run") is True
    provider_tool_calls_work = hosted.get("tool_calls_work") is True
    provider_failed_boundary = hosted.get("tool_boundary_supported") is False or hosted.get("run_status") == "failed"
    if hosted.get("run_status") in {"blocked_missing_api_key", "not_run"}:
        return "provide Ultravox key and rerun gated sandbox when ready"
    if hosted.get("run_status") == "blocked_no_public_tool_endpoint":
        return "design safe temporary HTTPS tool endpoint or client-tool strategy next"
    if not mock_passed:
        return "fix tool contract before any provider sandbox"
    if provider_run and hosted.get("tool_call_attempted") is False:
        return "do not proceed; keep Ultravox as research only until tool boundary works"
    if provider_run and provider_tool_calls_work:
        return "limited synthetic voice conversation test next, still no real customers and no phone calls"
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
        "phase": "4J1",
        "recommendation": recommendation,
        "mock_boundary_passed": mock.get("summary", {}).get("tool_boundary_passed") is True,
        "hosted_sandbox_run_status": hosted["run_status"],
        "sandbox_run": hosted["sandbox_run"],
        "provider_call_made": hosted["provider_call_made"],
        "tool_call_attempted": hosted["tool_call_attempted"],
        "tool_call_succeeded": hosted["tool_call_succeeded"],
        "public_tool_endpoint_required": hosted["public_tool_endpoint_required"],
        "public_tool_endpoint_available": hosted["public_tool_endpoint_available"],
        "latency_metrics": hosted["latency_metrics"],
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
            "If sandbox did not run because gates or key are missing: provide Ultravox key and rerun gated sandbox when ready.",
            "If sandbox did not run because public tool endpoint is required: design safe temporary HTTPS tool endpoint or client-tool strategy next.",
            "If provider sandbox runs but tool boundary cannot be enforced: do not proceed; keep Ultravox as research only until tool boundary works.",
            "If provider sandbox runs and tool boundary works: limited synthetic voice conversation test next, still no real customers and no phone calls.",
            "If latency or voice quality is poor: keep as architecture candidate only."
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
            f"Sandbox run: `{str(decision['sandbox_run']).lower()}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Tool call attempted: `{str(decision['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(decision['tool_call_succeeded']).lower()}`",
            f"Public tool endpoint required: `{str(decision['public_tool_endpoint_required']).lower()}`",
            f"Public tool endpoint available: `{str(decision['public_tool_endpoint_available']).lower()}`",
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


def build_quality_result(hosted: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-HOSTED-SANDBOX-QUALITY-001",
        "phase": "4J1",
        "sandbox_run": hosted["sandbox_run"],
        "provider_call_made": hosted["provider_call_made"],
        "env_file_exists": hosted["env_file_exists"],
        "env_file_ignored_by_git": hosted["env_file_ignored_by_git"],
        "env_file_loaded": hosted["env_file_loaded"],
        "api_key_present": hosted["api_key_present"],
        "env_gates": hosted["env_gates"],
        "outbound_phone_call_made": False,
        "browser_websocket_session_mode_used": hosted["browser_websocket_session_mode_used"],
        "public_tool_endpoint_required": hosted["public_tool_endpoint_required"],
        "public_tool_endpoint_available": hosted["public_tool_endpoint_available"],
        "tool_call_supported": hosted["tool_call_supported"],
        "tool_call_attempted": hosted["tool_call_attempted"],
        "tool_call_succeeded": hosted["tool_call_succeeded"],
        "synthetic_case_count": hosted["synthetic_case_count"],
        "provider_minutes_budget_note": hosted["provider_minutes_budget_note"],
        "product_truth_drift_count": hosted["product_truth_drift_count"],
        "unsupported_claim_count": hosted["unsupported_claim_count"],
        "fake_side_effect_count": hosted["fake_side_effect_count"],
        "crm_email_calendar_claim_count": hosted["crm_email_calendar_claim_count"],
        "internal_label_leak_count": hosted["internal_label_leak_count"],
        "source_boundary_violation_count": hosted["source_boundary_violation_count"],
        "memory_conflict_count": hosted["memory_conflict_count"],
        "latency_metrics": hosted["latency_metrics"],
        "transcript_metadata": hosted["transcript_metadata"],
        "raw_audio_stored": False,
        "audio_committed": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "quality_decision": "blocked_before_provider_minutes" if not hosted["provider_call_made"] else "provider_create_only_no_tool_quality",
    }


def render_quality_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-HOSTED-SANDBOX-QUALITY-001 Report",
            "",
            f"Sandbox run: `{str(result['sandbox_run']).lower()}`",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Synthetic cases attempted: `{result['synthetic_case_count']}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Unsupported claim count: `{result['unsupported_claim_count']}`",
            f"Fake side-effect count: `{result['fake_side_effect_count']}`",
            f"Internal label leak count: `{result['internal_label_leak_count']}`",
            f"Latency metrics: `{json.dumps(result['latency_metrics'], sort_keys=True)}`",
            f"Quality decision: `{result['quality_decision']}`",
            "",
        ]
    )


def build_dashboard_note_result() -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-DASHBOARD-VS-API-NOTE-001",
        "phase": "4J1",
        "dashboard_may_be_useful_later": True,
        "api_script_path_used_first": True,
        "reason_api_first": "repo evidence and reproducibility come before durable dashboard setup",
        "durable_dashboard_setup_waits_for": [
            "tool schema is stable",
            "public HTTPS tool endpoint or client-tool strategy is decided",
            "secret handling is confirmed",
            "synthetic sandbox passes",
        ],
        "manual_dashboard_upload_performed": False,
        "secrets_recorded": False,
        "no_manual_dashboard_upload_note": "No manual dashboard upload was performed in this phase.",
    }


def render_dashboard_note_report(result: dict[str, Any]) -> str:
    waits = "\n".join(f"- {item}" for item in result["durable_dashboard_setup_waits_for"])
    return "\n".join(
        [
            "# ULTRAVOX-DASHBOARD-VS-API-NOTE-001 Report",
            "",
            "Dashboard may be useful later for durable agents and reusable tools.",
            "",
            "The API/script path is used first because it leaves reproducible repo evidence and keeps secret handling explicit.",
            "",
            "Durable dashboard setup should wait until:",
            waits,
            "",
            "No manual dashboard upload was performed in this phase.",
            "No secrets were recorded.",
            "",
        ]
    )


def main() -> None:
    result = build_hosted_result()
    write_json(HOSTED_RESULT_PATH, result)
    write_text(HOSTED_REPORT_PATH, render_hosted_report(result))
    quality = build_quality_result(result)
    write_json(QUALITY_RESULT_PATH, quality)
    write_text(QUALITY_REPORT_PATH, render_quality_report(quality))
    dashboard_note = build_dashboard_note_result()
    write_json(NOTE_RESULT_PATH, dashboard_note)
    write_text(NOTE_REPORT_PATH, render_dashboard_note_report(dashboard_note))
    decision = build_decision(result)
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_decision_report(decision))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
