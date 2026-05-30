from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4L0-UNIVERSAL-SALES-ARCHITECTURE-RESET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

STRICT_UNIVERSAL_MODULES = [
    ROOT / "runtime" / "core" / "universal_conversation_policy_runtime.py",
]

SCOPED_CHANGE_ALLOWLIST = {
    "runtime/core/campaign_playbook_adapter.py",
    "runtime/core/universal_conversation_policy_runtime.py",
    "scripts/validate_phase_4l0_universal_sales_architecture_reset_001.py",
    "research/experiments/generated/PHASE-4L0-UNIVERSAL-SALES-ARCHITECTURE-RESET-001/result.json",
    "research/experiments/generated/PHASE-4L0-UNIVERSAL-SALES-ARCHITECTURE-RESET-001/report.md",
}

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
FALSE_FLAGS = [
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
    "selector_control_allowed",
    "live_selector_control_recommended",
    "response_replacement_performed",
    "side_effects_allowed",
    "raw_private_data",
    "raw_private_transcript_or_audio_added_to_public_evidence",
    "raw_transcript_or_audio_public",
]

ROUTESIGNAL_FORBIDDEN_IN_STRICT_UNIVERSAL = [
    "RouteSignal",
    "routesignal",
    "ROUTESIGNAL",
    "Northstar",
    "live-demo-001-routesignal",
    "campaign-prod-005-b2b-software",
    "inbound demo follow-up",
    "inbound demo follow up",
    "workflow review with someone from Northstar",
    "routesignal_callback_near_miss_phrase",
]

REQUIRED_INVENTORY_CATEGORIES = {
    "allowed_campaign_specific",
    "allowed_fixture_or_evidence",
    "allowed_test_or_validator",
    "universal_adapter_leak",
    "suspicious_needs_manual_review",
}

REQUIRED_ROADMAP_TOPICS = {
    "source_affiliation_boundary",
    "plan_category_explanation",
    "subscription_vs_model_product_explanation",
    "plan_fit_free_plus_pro_business_enterprise",
    "price_terms_caveat",
    "privacy_security_data_boundary",
    "competitor_context",
    "current_tool_context",
    "and_or_fidelity",
    "no_fit_disqualify",
    "self_serve_close_official_plan_page",
    "enterprise_contact_sales_route",
    "repeated_question_loop_repair",
    "spoken_naturalness_active_sales_progression",
}


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


def git_changed_files() -> set[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def validate_artifacts(failures: list[str], result: dict[str, Any]) -> None:
    if not RESULT_PATH.is_file():
        failures.append("result.json missing")
        return
    if not REPORT_PATH.is_file():
        failures.append("report.md missing")
    if result.get("checkpoint_id") != CHECKPOINT_ID:
        failures.append("checkpoint_id mismatch")
    if result.get("status") not in {"pass", "needs_manual_review"}:
        failures.append(f"status must be pass or needs_manual_review: {result.get('status')}")
    for key in FALSE_FLAGS:
        if result.get(key) is not False:
            failures.append(f"{key} must be false: {result.get(key)}")
    inventory = result.get("routesignal_leak_inventory")
    if not isinstance(inventory, dict):
        failures.append("routesignal_leak_inventory must be an object")
    else:
        missing = sorted(REQUIRED_INVENTORY_CATEGORIES - set(inventory))
        if missing:
            failures.append(f"routesignal_leak_inventory missing categories: {missing}")
        for category, payload in inventory.items():
            if category not in REQUIRED_INVENTORY_CATEGORIES:
                continue
            if not isinstance(payload, dict):
                failures.append(f"routesignal_leak_inventory.{category} must be an object")
                continue
            if not isinstance(payload.get("count"), int):
                failures.append(f"routesignal_leak_inventory.{category}.count must be an int")
            if not isinstance(payload.get("items"), list):
                failures.append(f"routesignal_leak_inventory.{category}.items must be a list")
    roadmap = result.get("openai_primary_universal_evaluation_roadmap")
    if not isinstance(roadmap, dict):
        failures.append("openai_primary_universal_evaluation_roadmap must be an object")
    else:
        missing_topics = sorted(REQUIRED_ROADMAP_TOPICS - set(roadmap))
        if missing_topics:
            failures.append(f"OpenAI-primary roadmap missing topics: {missing_topics}")


def validate_source_boundary(failures: list[str]) -> None:
    for path in STRICT_UNIVERSAL_MODULES:
        text = path.read_text(encoding="utf-8")
        hits = [needle for needle in ROUTESIGNAL_FORBIDDEN_IN_STRICT_UNIVERSAL if needle in text]
        if hits:
            failures.append(f"{path.relative_to(ROOT)} contains strict universal RouteSignal leak(s): {hits}")


def validate_script_imports(failures: list[str]) -> None:
    forbidden = sorted(imported_roots(Path(__file__)) & FORBIDDEN_IMPORT_ROOTS)
    if forbidden:
        failures.append(f"validator imports forbidden provider/network roots: {forbidden}")


def validate_changed_files(failures: list[str]) -> None:
    changed = git_changed_files()
    unexpected = sorted(changed - SCOPED_CHANGE_ALLOWLIST)
    if unexpected:
        failures.append(f"changed files outside scoped 4L0 surface: {unexpected}")


def main() -> int:
    failures: list[str] = []
    result = read_json(RESULT_PATH)
    validate_artifacts(failures, result)
    validate_source_boundary(failures)
    validate_script_imports(failures)
    validate_changed_files(failures)
    if failures:
        print(json.dumps({"status": "fail", "failures": failures}, indent=2, sort_keys=True))
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s).")
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
