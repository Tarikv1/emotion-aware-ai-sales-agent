#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-009-mikes-kitchen-simulation-tests"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_mikes_kitchen_simulation_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_mikes_kitchen_simulation_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_009_MIKES_KITCHEN_SIMULATION_TESTS.md"
LIVE_RESULT_SUMMARY = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / CHECKPOINT_ID
    / "simulation_results_summary.json"
)
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "simulation_tests_plan.json"
REQUESTS = OUT_DIR / "simulation_tests_requests.json"
FOLDER_NAME = "Atlas Web Studio - Mike's Kitchen Simulation Repair V22"


REQUIRED_DYNAMIC_VALUES = {
    "business_name": "Mike's Kitchen",
    "business_type": "restaurant",
    "vertical": "restaurant",
    "city": "Austin",
    "service_area": "Austin",
    "known_website_status": "no full website known",
    "known_social_presence": "Instagram and Google Maps",
    "known_booking_or_ordering_path": "reservations by phone",
    "call_reason": "free homepage mockup for a clearer homepage direction",
    "website_starting_price": "$1,000",
    "website_premium_price_anchor": "$5,000",
    "website_hosting_monthly_ballpark": "$10-$30/month",
    "website_domain_cost_note": "domain costs are separate and should be confirmed before anything paid",
    "website_campaign_value_points": "owner-controlled homepage layout; one shareable link for Instagram, Google, texts, emails, QR codes, and print; first-time visitor clarity before customers call; easier-to-scan menu than posts or profile photos when menu is the concern; fewer basic staff calls; Google Maps and Instagram can stay useful; reservation phone number can be easier to notice when phone path is the concern; optional future scope only when the buyer opens the door; mockup gives a concrete direction before paid work",
    "optional_upsell_boundary": "online booking is optional future scope only when the buyer is neutral, curious, or complains about phone/admin workload; never push it after the buyer rejects online booking",
}


REQUIRED_FOCI = {
    "skeptical_owner_value_path",
    "price_and_catch",
    "busy_callback",
    "gatekeeper_callback_note",
    "phone_only_booking_boundary",
    "plain_language",
    "instagram_google_maps_objection",
    "clear_refusal_do_not_call",
    "optional_booking_future_scope",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object.")
    return payload


def assert_no_secret_or_private_markers(payload: dict[str, Any]) -> None:
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
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def assert_simulation_test_shape(test: dict[str, Any], seen_ids: set[str], seen_foci: set[str]) -> None:
    test_id = str(test.get("test_id", ""))
    assert_condition(test_id.startswith("sim_"), f"test_id should start with sim_: {test_id}")
    assert_condition(test_id not in seen_ids, f"duplicate test_id: {test_id}")
    seen_ids.add(test_id)
    assert_condition(test.get("type") == "simulation", f"{test_id} must be a simulation test")
    max_turns = test.get("simulation_max_turns")
    assert_condition(isinstance(max_turns, int) and 12 <= max_turns <= 22, f"{test_id} max turns should be 12-22")
    scenario = str(test.get("simulation_scenario", "")).strip()
    success = str(test.get("success_condition", "")).strip()
    assert_condition(len(scenario) >= 250, f"{test_id} scenario is too thin")
    assert_condition(len(success) >= 220, f"{test_id} success condition is too thin")
    assert_condition("full conversation" in success.lower(), f"{test_id} must evaluate the full conversation")
    assert_condition("It fails if" in success, f"{test_id} must include failure conditions")
    assert_condition("natural closing" in success.lower() or "closing" in success.lower(), f"{test_id} must evaluate call closing")
    assert_condition("unapproved or nonsensical bracketed delivery tags" in success, f"{test_id} must evaluate delivery tag misuse")
    assert_condition("chat_history" not in test, f"{test_id} should not preload exact turns")
    variables = test.get("dynamic_variables")
    assert_condition(isinstance(variables, dict), f"{test_id} dynamic variables missing")
    focus = variables.get("simulation_focus")
    assert_condition(isinstance(focus, str) and focus in REQUIRED_FOCI, f"{test_id} simulation_focus mismatch")
    seen_foci.add(focus)
    for key in ("buyer_temperature", "target_outcome", "scenario_expected_turns"):
        assert_condition(isinstance(variables.get(key), str) and variables[key].strip(), f"{test_id} missing {key}")


def main() -> None:
    for path in (RUNNER, MANIFEST, TESTS, DOC, LIVE_RESULT_SUMMARY):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    test_pack = read_json(TESTS)
    assert_condition(test_pack.get("package_id") == CHECKPOINT_ID, "test pack package_id mismatch")
    assert_condition(test_pack.get("test_type") == "simulation", "test pack must be marked simulation")
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("upload_intent", {}).get("test_type") == "simulation", "manifest test_type mismatch")
    assert_condition(manifest.get("upload_intent", {}).get("target_test_folder_name") == FOLDER_NAME, "target folder mismatch")
    assert_condition(manifest.get("baseline_tests") == [str(TESTS.relative_to(ROOT)).replace("\\", "/")], "manifest tests mismatch")

    suite_vars = test_pack.get("dynamic_variables")
    assert_condition(isinstance(suite_vars, dict), "suite dynamic variables missing")
    for key, expected in REQUIRED_DYNAMIC_VALUES.items():
        assert_condition(suite_vars.get(key) == expected, f"dynamic variable mismatch for {key}")

    tests = test_pack.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 9, "expected exactly nine simulation tests")
    seen_ids: set[str] = set()
    seen_foci: set[str] = set()
    for test in tests:
        assert_condition(isinstance(test, dict), "each test must be an object")
        assert_simulation_test_shape(test, seen_ids, seen_foci)
    assert_condition(seen_foci == REQUIRED_FOCI, "simulation focus coverage mismatch")

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
    assert_no_secret_or_private_markers(plan)
    assert_no_secret_or_private_markers(requests)

    assert_condition(plan.get("mode") == "dry_run", "validator must not call provider")
    assert_condition(plan.get("package_id") == CHECKPOINT_ID, "plan package_id mismatch")
    assert_condition(plan.get("live_provider_calls_made") is False, "dry run must not call provider")
    assert_condition(plan.get("knowledge_base_upload_requests") == [], "simulation pack must not upload KB docs")
    assert_condition(plan.get("test_folder", {}).get("folder_name") == FOLDER_NAME, "plan folder name mismatch")

    create_requests = plan.get("test_create_requests")
    assert_condition(isinstance(create_requests, list) and len(create_requests) == 9, "create request count mismatch")
    for request in create_requests:
        body = request.get("body", {})
        variables = body.get("dynamic_variables", {})
        assert_condition(body.get("type") == "simulation", "expected simulation test payload")
        assert_condition(str(body.get("name", "")).startswith(f"{CHECKPOINT_ID}::"), "test name prefix mismatch")
        assert_condition("simulation_scenario" in body, "simulation_scenario missing")
        assert_condition("simulation_max_turns" in body, "simulation_max_turns missing")
        assert_condition("success_condition" in body, "success_condition missing")
        assert_condition("success_examples" not in body, "simulation payload should not use next-reply examples")
        assert_condition("failure_examples" not in body, "simulation payload should not use next-reply examples")
        assert_condition("chat_history" not in body, "simulation payload should not preload exact turns")
        assert_condition(12 <= body["simulation_max_turns"] <= 22, "request max turns should be 12-22")
        for key, expected in REQUIRED_DYNAMIC_VALUES.items():
            assert_condition(variables.get(key) == expected, f"request missing dynamic variable {key}")
        assert_condition(variables.get("source_package_id") == CHECKPOINT_ID, "source_package_id mismatch")
        assert_condition(variables.get("simulation_focus") in REQUIRED_FOCI, "request simulation_focus mismatch")

    request_entries = requests.get("requests", [])
    assert_condition(len(request_entries) == 10, "api request bundle should contain nine creates and one run-tests draft")

    live_result = read_json(LIVE_RESULT_SUMMARY)
    assert_no_secret_or_private_markers(live_result)
    assert_condition(live_result.get("checkpoint_id") == CHECKPOINT_ID, "live result checkpoint mismatch")
    assert_condition(live_result.get("test_type") == "simulation", "live result test type mismatch")
    assert_condition(str(live_result.get("test_folder_id", "")).startswith("tfld_"), "live folder id mismatch")
    assert_condition(str(live_result.get("suite_id", "")).startswith("suite_"), "live suite id mismatch")
    assert_condition(live_result.get("test_count") == 9, "live test count mismatch")
    passed_count = int(live_result.get("passed_count", -1))
    failed_count = int(live_result.get("failed_count", -1))
    pending_count = int(live_result.get("pending_count", -1))
    assert_condition(passed_count + failed_count + pending_count == 9, "live result counts do not add up")
    assert_condition(pending_count == 0, "live pending count mismatch")
    if failed_count:
        assert_condition(live_result.get("production_green") is False, "failed run must not be marked production-green")
        remaining = live_result.get("remaining_failure_modes")
        assert_condition(
            isinstance(remaining, list) and len(remaining) == failed_count,
            "remaining failure modes must match failed count",
        )
    else:
        assert_condition(passed_count == 9, "green run must pass all tests")
        assert_condition(live_result.get("production_green") is True, "green run must be marked production-green")
    created_tests = live_result.get("created_tests")
    assert_condition(isinstance(created_tests, list) and len(created_tests) == 9, "live created test count mismatch")
    seen_statuses = {"passed": 0, "failed": 0, "pending": 0}
    for item in created_tests:
        assert_condition(isinstance(item, dict), "live created test item must be an object")
        assert_condition(str(item.get("source_test_id", "")).startswith("sim_"), "live source_test_id mismatch")
        assert_condition(str(item.get("provider_test_id", "")).startswith("test_"), "live provider_test_id mismatch")
        assert_condition(str(item.get("test_run_id", "")).startswith("trun_"), "live test_run_id mismatch")
        assert_condition(item.get("status") in seen_statuses, "live test status mismatch")
        seen_statuses[item["status"]] += 1
    assert_condition(seen_statuses["passed"] == passed_count, "created test passed count mismatch")
    assert_condition(seen_statuses["failed"] == failed_count, "created test failed count mismatch")
    assert_condition(seen_statuses["pending"] == pending_count, "created test pending count mismatch")

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        FOLDER_NAME,
        "dashboard Simulation Tests",
        "not next-reply tests",
        "human-reviewed repair",
        "Simulation Repair V22",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "test_count": len(create_requests),
                "target_folder": FOLDER_NAME,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
