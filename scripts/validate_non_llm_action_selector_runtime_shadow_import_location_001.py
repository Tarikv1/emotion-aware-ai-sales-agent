from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-HOOK-LOCATION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SELECTED_FILE = ROOT / "runtime" / "campaigns" / "public_openai_chatgpt_plans_dialogue.py"
SELECTED_FUNCTION = "_frame"
IMPORT_CONFIG_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_import_config.json"
HOOK_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_hook.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def build_result() -> dict[str, Any]:
    selected_source = read_text(SELECTED_FILE)
    hook_source = read_text(HOOK_PATH)
    config = json.loads(IMPORT_CONFIG_PATH.read_text(encoding="utf-8")) if IMPORT_CONFIG_PATH.is_file() else {}
    failures: list[str] = []
    if "def _frame(" not in selected_source:
        failures.append("selected function _frame missing")
    if "_observe_action_selector_shadow_frame(frame)" not in selected_source:
        failures.append("selected function does not call shadow observer")
    if "maybe_log_action_selector_shadow_turn" not in selected_source:
        failures.append("selected file does not import shadow hook")
    if "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED" not in hook_source:
        failures.append("hook does not use runtime shadow import env gate")
    if config.get("enabled_by_default") is not False:
        failures.append("import config enabled_by_default must be false")
    if config.get("env_gate") != "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED=1":
        failures.append("import config env_gate mismatch")
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "selected_file": str(SELECTED_FILE.relative_to(ROOT)).replace("\\", "/"),
        "selected_function": SELECTED_FUNCTION,
        "selected_call_site": "_observe_action_selector_shadow_frame(frame) inside _frame after final frame construction",
        "alternatives_considered": [
            {
                "file": "runtime/core/contextual_buyer_semantics.py",
                "function": "classify_contextual_buyer_semantics",
                "decision": "rejected",
                "reason": "broader cross-campaign semantic router; higher blast radius than the public OpenAI campaign adapter.",
            },
            {
                "file": "runtime/core/realtime_turns.py",
                "function": "build_runtime_decision",
                "decision": "rejected",
                "reason": "runtime harness includes background-module/call-control decisions and side-effect labels; not the narrow campaign post-decision location.",
            },
            {
                "file": "runtime/action_selector/shadow_runtime_hook.py",
                "function": "maybe_log_action_selector_shadow_turn",
                "decision": "supporting hook only",
                "reason": "safe import target, but not a runtime observation point by itself.",
            },
            {
                "file": "runtime/action_selector/runtime_action_metadata_extractor.py",
                "function": "extract_runtime_action_metadata",
                "decision": "supporting extractor only",
                "reason": "extracts metadata from a supplied runtime result but should not decide where runtime observation occurs.",
            },
        ],
        "why_selected": [
            "The campaign _frame helper is reached only after the campaign response frame has been selected.",
            "It has buyer utterance metadata, normalized text, semantic family, action_id, candidate_response, dialogue focus, and campaign id.",
            "The hook result can be ignored without changing response text, memory, call control, TTS, provider calls, or side effects.",
        ],
        "available_metadata": [
            "campaign_id",
            "buyer transcript hash",
            "normalized buyer text for in-memory selector input",
            "semantic",
            "action_id",
            "dialogue_focus",
            "target_gap",
            "polarity",
            "confidence",
            "candidate_response hash via extractor",
            "response_strategy",
            "next_best_sales_action",
        ],
        "unavailable_metadata": [
            "provider response internals",
            "TTS/prosody output",
            "CRM/email/calendar execution state",
            "raw private audio",
            "raw private transcript in public evidence",
            "stable external turn id when caller does not provide one",
        ],
        "safety_risks": [
            "Hook import must remain fail-closed so a selector failure cannot alter runtime output.",
            "Enabled runtime records must not be used for selector control or response replacement.",
            "Public evidence must not include raw private transcript or audio.",
        ],
        "default_behavior_with_env_disabled": "Fast no-op: no selector run, no file write, no record, no runtime output change.",
        "expected_validators_if_changed": [
            "python scripts\\validate_non_llm_action_selector_runtime_shadow_import_noop_001.py",
            "python scripts\\run_non_llm_action_selector_runtime_shadow_import_gated_001.py",
            "python scripts\\validate_non_llm_action_selector_runtime_shadow_import_gated_001.py",
            "python scripts\\validate_runtime_manifest.py",
            "python scripts\\validate_project_drift_guard.py",
        ],
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "ultravox_calls_made": False,
        "elevenlabs_calls_made": False,
        "local_llm_calls_made": False,
        "ollama_calls_made": False,
        "tts_calls_made": False,
        "side_effects_allowed": False,
        "memory_mutation_allowed": False,
        "buyer_facing_text_generated": False,
        "selector_control_allowed": False,
        "live_runtime_wiring_allowed": False,
        "raw_private_data": False,
        "audio_data_used": False,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    return result


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Selected file/function: {result['selected_file']}::{result['selected_function']}",
        f"- Selected call site: {result['selected_call_site']}",
        f"- Default env-disabled behavior: {result['default_behavior_with_env_disabled']}",
        f"- Safety blockers: {result['failure_count']}",
        "- Runtime behavior changed: false",
        "- Response text changed: false",
        "- Selector control allowed: false",
        "- Live wiring allowed: false",
        "",
        "## Why Selected",
        "",
    ]
    for item in result["why_selected"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Alternatives", ""])
    for item in result["alternatives_considered"]:
        lines.append(f"- {item['file']}::{item['function']}: {item['decision']} - {item['reason']}")
    return "\n".join(lines)


def main() -> int:
    result = build_result()
    print(json.dumps({"status": result["status"], "failures": result["failures"]}, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
