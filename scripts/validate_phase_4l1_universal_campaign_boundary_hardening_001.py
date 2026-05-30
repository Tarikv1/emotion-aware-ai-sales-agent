from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4L1-UNIVERSAL-CAMPAIGN-BOUNDARY-HARDENING-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SUSPICIOUS_MODULES = [
    "runtime/core/live_voice_session_policy.py",
    "runtime/core/contextual_buyer_semantics.py",
    "runtime/core/dialogue_manager.py",
    "runtime/core/dialogue_reasoner.py",
    "runtime/core/dialogue_pragmatics.py",
    "runtime/entrypoints/generate_guarded_response.py",
    "runtime/entrypoints/generic_campaign_turn.py",
]

CLASSIFICATIONS = {
    "allowed_legacy_regression_fixture",
    "allowed_campaign_adapter_access",
    "universal_boundary_leak",
    "needs_future_migration",
}

FALSE_FLAGS = [
    "selector_control_allowed",
    "live_selector_control_recommended",
    "response_replacement_performed",
    "provider_calls_made",
    "model_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "payment_calls_made",
    "account_side_effects_made",
    "raw_private_transcript_or_audio_added_to_public_evidence",
]

REQUIRED_UNIVERSAL_CONTRACT = {
    "neutral buyer moves",
    "neutral sales-stage states",
    "neutral campaign adapter fields",
    "neutral response capability keys",
    "neutral source/claim/side-effect boundaries",
}

REQUIRED_CAMPAIGN_CONTRACT = {
    "campaign product/company names",
    "campaign-specific diagnostic gaps",
    "campaign-specific close route",
    "campaign-specific human follow-up owner",
    "campaign-specific response capability text",
}

REQUIRED_REPORT_PHRASES = [
    "OpenAI remains the primary benchmark campaign",
    "RouteSignal remains a secondary regression fixture only",
    "No live selector control was enabled",
    "No response replacement was enabled",
    "No provider/model/TTS/CRM/email/calendar/payment/account path was enabled",
    "No raw private transcript/audio was added to public evidence",
]

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def validate_artifacts(failures: list[str], result: dict[str, Any]) -> None:
    if not RESULT_PATH.is_file():
        failures.append("result.json missing")
        return
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    if result.get("checkpoint_id") != CHECKPOINT_ID:
        failures.append("checkpoint_id mismatch")
    if result.get("status") not in {"pass", "needs_future_migration"}:
        failures.append(f"status must be pass or needs_future_migration: {result.get('status')}")

    for key in FALSE_FLAGS:
        if result.get(key) is not False:
            failures.append(f"{key} must be false: {result.get(key)}")

    inspected = result.get("inspected_suspicious_modules")
    if inspected != SUSPICIOUS_MODULES:
        failures.append(f"inspected_suspicious_modules mismatch: {inspected}")

    counts = result.get("classification_counts")
    if not isinstance(counts, dict):
        failures.append("classification_counts must be an object")
    else:
        missing = sorted(CLASSIFICATIONS - set(counts))
        if missing:
            failures.append(f"classification_counts missing categories: {missing}")
        for category in CLASSIFICATIONS:
            if not isinstance(counts.get(category), int):
                failures.append(f"classification_counts.{category} must be an int")

    items = result.get("module_classifications")
    if not isinstance(items, list) or not items:
        failures.append("module_classifications must be a populated list")
    else:
        modules = {str(item.get("module") or "") for item in items if isinstance(item, dict)}
        missing_modules = [module for module in SUSPICIOUS_MODULES if module not in modules]
        if missing_modules:
            failures.append(f"module_classifications missing modules: {missing_modules}")
        for item in items:
            if not isinstance(item, dict):
                failures.append("module_classifications entries must be objects")
                continue
            classification = item.get("classification")
            if classification not in CLASSIFICATIONS:
                failures.append(f"invalid classification {classification!r} for {item.get('module')}")

    boundary = result.get("boundary_contract")
    if not isinstance(boundary, dict):
        failures.append("boundary_contract must be an object")
    else:
        universal = set(str(item) for item in boundary.get("universal_modules_may_use") or [])
        campaign = set(str(item) for item in boundary.get("campaign_specific_modules_may_define") or [])
        if not REQUIRED_UNIVERSAL_CONTRACT.issubset(universal):
            failures.append("boundary_contract.universal_modules_may_use missing required items")
        if not REQUIRED_CAMPAIGN_CONTRACT.issubset(campaign):
            failures.append("boundary_contract.campaign_specific_modules_may_define missing required items")

    scope_decision = result.get("route_signal_scope_boundary_decision")
    if not isinstance(scope_decision, dict):
        failures.append("route_signal_scope_boundary_decision must be an object")
    elif scope_decision.get("decision") != "renamed_to_campaign_scope_boundary":
        failures.append(f"route_signal_scope_boundary_decision.decision mismatch: {scope_decision.get('decision')}")

    default_decision = result.get("default_campaign_adapter_decision")
    if not isinstance(default_decision, dict):
        failures.append("default_campaign_adapter_decision must be an object")
    elif default_decision.get("decision") != "keep_legacy_routesignal_default":
        failures.append(f"default_campaign_adapter_decision.decision mismatch: {default_decision.get('decision')}")

    if result.get("openai_primary_benchmark_campaign") != "public OpenAI ChatGPT plans":
        failures.append("OpenAI primary benchmark campaign not preserved")
    if result.get("routesignal_role") != "secondary regression fixture only":
        failures.append("RouteSignal role not restricted to secondary regression fixture")


def validate_report(failures: list[str]) -> None:
    if not REPORT_PATH.is_file():
        return
    text = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in REQUIRED_REPORT_PHRASES:
        if phrase not in text:
            failures.append(f"report missing phrase: {phrase}")
    for module in SUSPICIOUS_MODULES:
        if module not in text:
            failures.append(f"report missing inspected module: {module}")


def validate_source_boundary(failures: list[str]) -> None:
    universal = ROOT / "runtime" / "core" / "universal_conversation_policy_runtime.py"
    contextual = ROOT / "runtime" / "core" / "contextual_buyer_semantics.py"
    for path in [universal, contextual]:
        text = path.read_text(encoding="utf-8")
        if "route_signal_scope_boundary" in text:
            failures.append(f"{path.relative_to(ROOT)} still contains route_signal_scope_boundary")
        if "campaign_scope_boundary" not in text:
            failures.append(f"{path.relative_to(ROOT)} missing campaign_scope_boundary")

    reasoner = (ROOT / "runtime" / "core" / "dialogue_reasoner.py").read_text(encoding="utf-8")
    pragmatics = (ROOT / "runtime" / "core" / "dialogue_pragmatics.py").read_text(encoding="utf-8")
    for path_label, text in [
        ("runtime/core/dialogue_reasoner.py", reasoner),
        ("runtime/core/dialogue_pragmatics.py", pragmatics),
    ]:
        for needle in ["RouteSignal", "Northstar Workflow Labs"]:
            if needle in text:
                failures.append(f"{path_label} contains direct campaign-specific copy: {needle}")

    adapter = (ROOT / "runtime" / "core" / "campaign_playbook_adapter.py").read_text(encoding="utf-8")
    if 'DEFAULT_CAMPAIGN_ID = "live-demo-001-routesignal"' not in adapter:
        failures.append("campaign_playbook_adapter legacy default changed")
    for key in ["scope_boundary_coverage_response", "scope_boundary_specialist_response"]:
        if key not in adapter:
            failures.append(f"campaign_playbook_adapter missing response capability key: {key}")

    generic_turn = (ROOT / "runtime" / "entrypoints" / "generic_campaign_turn.py").read_text(encoding="utf-8")
    if "generic campaign resolved to the default playbook" not in generic_turn:
        failures.append("generic_campaign_turn no longer blocks default playbook fallback for generic configs")


def validate_script_imports(failures: list[str]) -> None:
    forbidden = sorted(imported_roots(Path(__file__)) & FORBIDDEN_IMPORT_ROOTS)
    if forbidden:
        failures.append(f"validator imports forbidden provider/network roots: {forbidden}")


def main() -> int:
    failures: list[str] = []
    result = read_json(RESULT_PATH)
    validate_artifacts(failures, result)
    validate_report(failures)
    validate_source_boundary(failures)
    validate_script_imports(failures)
    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s).")
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
