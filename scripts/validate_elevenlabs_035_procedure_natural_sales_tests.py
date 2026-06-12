#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-035-procedure-natural-sales-simulation-tests"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_procedure_natural_sales_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_procedure_natural_sales_tests.json"
)
ACTIVE_UPLOAD_MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_spine_compression.package.json"
)
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "simulation_tests_plan.json"
REQUESTS = OUT_DIR / "simulation_tests_requests.json"
FOLDER_NAME = "ELEVENLABS-035-procedure-natural-sales"
MODEL_ID = "gemini-2.5-flash"


EXPECTED_TESTS = {
    "sim_035_email_confirmation_spoken_email_two_step": "Email Provided",
    "sim_035_email_process_risk_overlap": "Email Provided plus Process-Risk",
    "sim_035_future_pricing_no_overpricing": "Feature Pricing",
    "sim_035_appointment_scheduling_simple_vs_integrated": "Feature Pricing - Appointment Scheduling Split",
    "sim_035_crm_payment_capability_first": "Feature Pricing - CRM and Payment Capability First",
    "sim_035_custom_portal_dashboard_scoped_work": "Custom Portal",
    "sim_035_mockup_scope_visual_placeholder": "Mockup Scope",
    "sim_035_process_risk_chain_no_cta_fatigue": "Process-Risk",
    "sim_035_guarantee_only_disqualification_lock": "Guarantee-Only",
    "sim_035_terminal_close_no_loop": "Terminal Close",
}

COMMON_DYNAMIC_VALUES = {
    "campaign_name": "atlas-web-studio-procedure-natural-sales-simulation",
    "caller_identity": "Emma from Atlas Web Studio",
    "offer_type": "free homepage mockup",
    "website_starting_price": "$1,000",
    "website_premium_price_anchor": "$5,000",
    "website_basic_site_range": "$1,000-$2,000",
    "website_light_feature_range": "$2,000-$3,000",
    "website_workflow_content_range": "$3,000-$4,000",
    "website_integration_heavy_range": "$4,000-$5,000",
}

REQUIRED_BUSINESSES = {
    "Northside Auto Repair",
    "Bright Lane Dental",
    "Harbor Cafe",
    "Luna Hair Studio",
    "Ridgeway Auto Service",
    "FreshNest Cleaning",
    "Riverside Bistro",
    "Summit HVAC",
    "Apex Plumbing",
    "Maple Street Bakery",
}

SUITE_MARKERS = (
    "natural phone behavior",
    "sales progression",
    "active ElevenLabs Procedures",
)

PROCEDURE_MARKERS = (
    "normalized",
    "process-risk",
    "ballpark",
    "simple appointment request",
    "live calendar",
    "capability before price",
    "simple form handoff",
    "custom scoped work",
    "show where the login or portal entry would sit",
    "not working functionality",
    "no automatic call",
    "CTA fatigue",
    "guarantee-only lock",
    "Take care",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_no_private_or_secret_markers(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    blocked = (
        "xi-api-key",
        "api key value",
        "creator_email",
        "creator_name",
        "access_info",
        "phone_numbers",
        "whatsapp_accounts",
        "shareable_token",
        "data/private/",
        "data/private-restricted/",
        "private transcript",
        "\"sk-",
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def assert_simulation_shape(test: dict[str, Any], seen_ids: set[str], seen_businesses: set[str], seen_verticals: set[str]) -> None:
    test_id = str(test.get("test_id", "")).strip()
    assert_condition(test_id in EXPECTED_TESTS, f"unexpected test_id: {test_id}")
    assert_condition(test_id not in seen_ids, f"duplicate test_id: {test_id}")
    seen_ids.add(test_id)
    assert_condition(test.get("type") == "simulation", f"{test_id} must be simulation")
    assert_condition(test.get("simulated_user_model") == MODEL_ID, f"{test_id} simulated_user_model mismatch")
    assert_condition(test.get("evaluation_model") == MODEL_ID, f"{test_id} evaluation_model mismatch")
    assert_condition(test.get("simulation_max_turns") == 20, f"{test_id} must use simulation_max_turns 20")
    assert_condition(test.get("procedure_under_test") == EXPECTED_TESTS[test_id], f"{test_id} procedure_under_test mismatch")
    assert_condition("chat_history" not in test, f"{test_id} should not preload exact turns")

    scenario = str(test.get("simulation_scenario", "")).strip()
    success = str(test.get("success_condition", "")).strip()
    assert_condition(len(scenario) >= 220, f"{test_id} scenario is too thin")
    assert_condition(len(success) >= 450, f"{test_id} success condition is too thin")
    combined = f"{scenario}\n{success}".lower()
    for marker in ("full conversation passes", "it fails if"):
        assert_condition(marker in combined, f"{test_id} missing full-conversation marker: {marker}")
    assert_condition(
        any(marker in combined for marker in ("natural", "short", "live phone", "human", "compact")),
        f"{test_id} must evaluate natural spoken shape",
    )
    assert_condition(
        "sales" in combined or "next step" in combined or "close" in combined or "outcome" in combined,
        f"{test_id} must evaluate sales progression or closing",
    )

    variables = test.get("dynamic_variables")
    assert_condition(isinstance(variables, dict), f"{test_id} dynamic variables missing")
    business = str(variables.get("business_name", "")).strip()
    vertical = str(variables.get("vertical", "")).strip()
    assert_condition(business in REQUIRED_BUSINESSES, f"{test_id} unexpected business: {business}")
    assert_condition(vertical, f"{test_id} missing vertical")
    seen_businesses.add(business)
    seen_verticals.add(vertical)
    for key in (
        "business_type",
        "city",
        "service_area",
        "known_website_status",
        "known_social_presence",
        "known_booking_or_ordering_path",
        "primary_offer_angle",
        "approved_value_points",
        "buyer_temperature",
        "conversation_pressure",
        "target_outcome",
        "scenario_expected_turns",
    ):
        assert_condition(isinstance(variables.get(key), str) and variables[key].strip(), f"{test_id} missing {key}")


def assert_dry_run_plan() -> tuple[dict[str, Any], dict[str, Any]]:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(MANIFEST),
            "--agent-id",
            "agent_7801kt0g32zxf4f8x5zkykj7syty",
            "--test-folder-name",
            FOLDER_NAME,
            "--out",
            str(PLAN),
            "--api-requests-out",
            str(REQUESTS),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    plan = read_json(PLAN)
    requests = read_json(REQUESTS)
    assert_no_private_or_secret_markers(plan)
    assert_no_private_or_secret_markers(requests)
    assert_condition(plan.get("mode") == "dry_run", "validator must not call provider")
    assert_condition(plan.get("package_id") == CHECKPOINT_ID, "plan package_id mismatch")
    assert_condition(plan.get("live_provider_calls_made") is False, "dry run must not call provider")
    assert_condition(plan.get("knowledge_base_upload_requests") == [], "test package must not upload KB docs")
    assert_condition(plan.get("test_folder", {}).get("folder_name") == FOLDER_NAME, "plan folder name mismatch")

    create_requests = plan.get("test_create_requests")
    assert_condition(isinstance(create_requests, list) and len(create_requests) == 10, "create request count mismatch")
    request_ids = set()
    for request in create_requests:
        body = request.get("body", {})
        variables = body.get("dynamic_variables", {})
        test_id = str(body.get("name", "")).split("::")[-1]
        request_ids.add(test_id)
        assert_condition(body.get("type") == "simulation", f"{test_id} request type mismatch")
        assert_condition(body.get("simulation_max_turns") == 20, f"{test_id} request max-turns mismatch")
        assert_condition(body.get("simulated_user_model") == MODEL_ID, f"{test_id} request simulated_user_model mismatch")
        assert_condition(body.get("evaluation_model") == MODEL_ID, f"{test_id} request evaluation_model mismatch")
        assert_condition("chat_history" not in body, f"{test_id} request should not preload exact turns")
        assert_condition(str(body.get("name", "")).startswith(f"{CHECKPOINT_ID}::"), f"{test_id} request name mismatch")
        for key, expected in COMMON_DYNAMIC_VALUES.items():
            assert_condition(variables.get(key) == expected, f"{test_id} missing suite dynamic variable: {key}")
        assert_condition(variables.get("source_package_id") == CHECKPOINT_ID, f"{test_id} source_package_id mismatch")

    assert_condition(request_ids == set(EXPECTED_TESTS), "request test IDs mismatch")
    request_entries = requests.get("requests", [])
    assert_condition(len(request_entries) == 11, "api request bundle should contain ten creates and one run-tests draft")
    return plan, requests


def assert_active_upload_manifest_unchanged() -> None:
    assert_condition(ACTIVE_UPLOAD_MANIFEST.is_file(), "active upload manifest missing")
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", str(ACTIVE_UPLOAD_MANIFEST.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    assert_condition(not completed.stdout.strip(), "active Atlas upload manifest was modified")


def main() -> None:
    for path in (RUNNER, MANIFEST, TESTS):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    test_pack = read_json(TESTS)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(test_pack.get("package_id") == CHECKPOINT_ID, "test pack package_id mismatch")
    assert_condition(test_pack.get("test_type") == "simulation", "test pack must be simulation")
    assert_condition(manifest.get("knowledge_base_docs") == [], "test-only package must not upload KB docs")
    assert_condition(
        manifest.get("baseline_tests") == [str(TESTS.relative_to(ROOT)).replace("\\", "/")],
        "manifest baseline_tests mismatch",
    )
    upload_intent = manifest.get("upload_intent", {})
    assert_condition(upload_intent.get("target_test_folder_name") == FOLDER_NAME, "target folder mismatch")
    assert_condition(upload_intent.get("simulation_max_turns") == 20, "manifest max-turns mismatch")
    assert_condition(upload_intent.get("knowledge_base_upload_required") is False, "manifest must not require KB upload")

    serialized_pack = json.dumps(test_pack, ensure_ascii=False)
    lower_pack = serialized_pack.lower()
    for marker in SUITE_MARKERS:
        assert_condition(marker.lower() in lower_pack, f"test pack missing suite marker: {marker}")
    for marker in PROCEDURE_MARKERS:
        assert_condition(marker.lower() in lower_pack, f"test pack missing procedure marker: {marker}")
    assert_no_private_or_secret_markers(test_pack)

    suite_vars = test_pack.get("dynamic_variables")
    assert_condition(isinstance(suite_vars, dict), "suite dynamic variables missing")
    for key, expected in COMMON_DYNAMIC_VALUES.items():
        assert_condition(suite_vars.get(key) == expected, f"suite dynamic variable mismatch: {key}")

    tests = test_pack.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 10, "expected exactly ten procedure simulations")
    seen_ids: set[str] = set()
    seen_businesses: set[str] = set()
    seen_verticals: set[str] = set()
    for test in tests:
        assert_condition(isinstance(test, dict), "each test must be an object")
        assert_simulation_shape(test, seen_ids, seen_businesses, seen_verticals)
    assert_condition(seen_ids == set(EXPECTED_TESTS), "test ID coverage mismatch")
    assert_condition(seen_businesses == REQUIRED_BUSINESSES, "business coverage mismatch")
    assert_condition(len(seen_verticals) >= 8, "expected at least eight distinct vertical labels")

    assert_dry_run_plan()
    assert_active_upload_manifest_unchanged()
    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "test_count": 10,
                "target_folder": FOLDER_NAME,
                "simulated_user_model": MODEL_ID,
                "evaluation_model": MODEL_ID,
                "simulation_max_turns": 20,
                "businesses": sorted(seen_businesses),
                "vertical_count": len(seen_verticals),
                "live_provider_calls_made": False,
                "active_upload_manifest_changed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
