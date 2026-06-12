#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_natural_sales_scenarios_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_natural_sales_scenarios_tests.json"
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
FOLDER_NAME = "ELEVENLABS-036-natural-sales-scenarios"
MODEL_ID = "gemini-2.5-flash"


EXPECTED_TESTS = {
    "sim_036_email_confirmation_spoken_email_two_step": 12,
    "sim_036_email_plus_free_question_confirmation": 14,
    "sim_036_future_price_ballpark_no_overpricing": 16,
    "sim_036_scheduling_simple_request_vs_live_integration": 16,
    "sim_036_crm_payment_capability_before_price": 16,
    "sim_036_custom_dashboard_scoped_separately": 16,
    "sim_036_free_mockup_visual_not_working_site": 12,
    "sim_036_next_step_questions_no_cta_fatigue": 18,
    "sim_036_guarantee_required_clean_disqualify": 10,
    "sim_036_goodbye_take_care_no_loop": 12,
}

COMMON_DYNAMIC_VALUES = {
    "campaign_name": "atlas-web-studio-natural-sales-scenarios",
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
    "Cedar Ridge Auto Glass",
    "Oakwood Pediatric Dentistry",
    "Blue Harbor Kayak Rentals",
    "Velvet Paw Grooming",
    "Iron Gate Garage Doors",
    "ClearPath Tutoring",
    "Mesa Fit Studio",
    "Pine & Stone Landscaping",
    "RapidRooter Plumbing",
    "Sunrise Bagel Shop",
}

FORBIDDEN_ALPHA_MARKERS = (
    "procedure_under_test",
    "procedures",
    "procedure",
    "email provided",
    "process-risk",
    "feature pricing",
    "custom portal",
    "mockup scope",
    "terminal close",
    "guarantee-only",
    "covered_procedures",
)

REQUIRED_BEHAVIOR_MARKERS = (
    "normalized",
    "no automatic follow-up call",
    "ballpark",
    "simple appointment request",
    "live calendar",
    "capability before price",
    "simple form handoff",
    "secure login",
    "visual, not a working website",
    "CTA fatigue",
    "be careful with anyone selling it that way",
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


def assert_no_alpha_markers(*payloads: dict[str, Any]) -> None:
    serialized = "\n".join(json.dumps(payload, ensure_ascii=False).lower() for payload in payloads)
    found = [marker for marker in FORBIDDEN_ALPHA_MARKERS if marker in serialized]
    assert_condition(not found, f"new tests must not contain alpha routing markers: {found}")


def assert_simulation_shape(
    test: dict[str, Any],
    *,
    seen_ids: set[str],
    seen_businesses: set[str],
    seen_verticals: set[str],
    seen_focus: set[str],
) -> None:
    test_id = str(test.get("test_id", "")).strip()
    assert_condition(test_id in EXPECTED_TESTS, f"unexpected test_id: {test_id}")
    assert_condition(test_id not in seen_ids, f"duplicate test_id: {test_id}")
    seen_ids.add(test_id)
    assert_condition(test.get("type") == "simulation", f"{test_id} must be simulation")
    assert_condition(test.get("simulated_user_model") == MODEL_ID, f"{test_id} simulated_user_model mismatch")
    assert_condition(test.get("evaluation_model") == MODEL_ID, f"{test_id} evaluation_model mismatch")
    assert_condition(test.get("simulation_max_turns") == EXPECTED_TESTS[test_id], f"{test_id} max turns mismatch")
    assert_condition("chat_history" not in test, f"{test_id} should not preload exact turns")
    assert_condition("procedure_under_test" not in test, f"{test_id} must not use alpha routing fields")

    scenario = str(test.get("simulation_scenario", "")).strip()
    success = str(test.get("success_condition", "")).strip()
    assert_condition(len(scenario) >= 220, f"{test_id} scenario is too thin")
    assert_condition(len(success) >= 420, f"{test_id} success condition is too thin")
    combined = f"{scenario}\n{success}".lower()
    for marker in ("the full conversation passes", "it fails if"):
        assert_condition(marker in combined, f"{test_id} missing evaluator marker: {marker}")
    assert_condition(
        any(marker in combined for marker in ("natural", "short", "real phone", "human", "compact")),
        f"{test_id} must evaluate spoken naturalness",
    )
    assert_condition(
        "next-step" in combined or "next step" in combined or "close" in combined or "outcome" in combined,
        f"{test_id} must evaluate sales progression or closing",
    )

    variables = test.get("dynamic_variables")
    assert_condition(isinstance(variables, dict), f"{test_id} dynamic variables missing")
    business = str(variables.get("business_name", "")).strip()
    vertical = str(variables.get("vertical", "")).strip()
    focus = str(variables.get("test_focus", "")).strip()
    assert_condition(business in REQUIRED_BUSINESSES, f"{test_id} unexpected business: {business}")
    assert_condition(vertical, f"{test_id} missing vertical")
    assert_condition(focus, f"{test_id} missing test_focus")
    seen_businesses.add(business)
    seen_verticals.add(vertical)
    seen_focus.add(focus)
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


def assert_dry_run_plan() -> None:
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
        assert_condition(body.get("simulation_max_turns") == EXPECTED_TESTS[test_id], f"{test_id} request max-turns mismatch")
        assert_condition(body.get("simulated_user_model") == MODEL_ID, f"{test_id} request simulated_user_model mismatch")
        assert_condition(body.get("evaluation_model") == MODEL_ID, f"{test_id} request evaluation_model mismatch")
        assert_condition("chat_history" not in body, f"{test_id} request should not preload exact turns")
        assert_condition("procedure_under_test" not in body, f"{test_id} request must not use alpha routing fields")
        assert_condition(str(body.get("name", "")).startswith(f"{CHECKPOINT_ID}::"), f"{test_id} request name mismatch")
        for key, expected in COMMON_DYNAMIC_VALUES.items():
            assert_condition(variables.get(key) == expected, f"{test_id} missing suite dynamic variable: {key}")
        assert_condition(variables.get("source_package_id") == CHECKPOINT_ID, f"{test_id} source_package_id mismatch")
    assert_condition(request_ids == set(EXPECTED_TESTS), "request test IDs mismatch")
    assert_condition(len(requests.get("requests", [])) == 11, "api request bundle should contain ten creates and one run-tests draft")


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
    assert_condition(upload_intent.get("knowledge_base_upload_required") is False, "manifest must not require KB upload")
    assert_no_alpha_markers(manifest, test_pack)
    assert_no_private_or_secret_markers(test_pack)

    serialized_pack = json.dumps(test_pack, ensure_ascii=False)
    lower_pack = serialized_pack.lower()
    for marker in REQUIRED_BEHAVIOR_MARKERS:
        assert_condition(marker.lower() in lower_pack, f"test pack missing behavior marker: {marker}")

    suite_vars = test_pack.get("dynamic_variables")
    assert_condition(isinstance(suite_vars, dict), "suite dynamic variables missing")
    for key, expected in COMMON_DYNAMIC_VALUES.items():
        assert_condition(suite_vars.get(key) == expected, f"suite dynamic variable mismatch: {key}")

    tests = test_pack.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 10, "expected exactly ten simulations")
    seen_ids: set[str] = set()
    seen_businesses: set[str] = set()
    seen_verticals: set[str] = set()
    seen_focus: set[str] = set()
    for test in tests:
        assert_condition(isinstance(test, dict), "each test must be an object")
        assert_simulation_shape(
            test,
            seen_ids=seen_ids,
            seen_businesses=seen_businesses,
            seen_verticals=seen_verticals,
            seen_focus=seen_focus,
        )
    assert_condition(seen_ids == set(EXPECTED_TESTS), "test ID coverage mismatch")
    assert_condition(seen_businesses == REQUIRED_BUSINESSES, "business coverage mismatch")
    assert_condition(len(seen_verticals) >= 8, "expected at least eight distinct vertical labels")
    assert_condition(len(seen_focus) == 10, "each test should have a distinct test_focus")

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
                "max_turns_by_test": EXPECTED_TESTS,
                "businesses": sorted(seen_businesses),
                "vertical_count": len(seen_verticals),
                "alpha_routing_markers_present": False,
                "live_provider_calls_made": False,
                "active_upload_manifest_changed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
