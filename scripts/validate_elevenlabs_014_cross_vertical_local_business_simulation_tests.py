#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-014-cross-vertical-local-business-simulation-tests"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_cross_vertical_local_business_simulation_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_cross_vertical_local_business_simulation_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_014_CROSS_VERTICAL_LOCAL_BUSINESS_SIMULATION_TESTS.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "simulation_tests_plan.json"
REQUESTS = OUT_DIR / "simulation_tests_requests.json"
FOLDER_NAME = "Atlas Web Studio - Cross-Vertical Local Business Simulation V1"


COMMON_DYNAMIC_VALUES = {
    "campaign_name": "atlas-web-studio-cross-vertical-local-business-simulation",
    "caller_identity": "Emma from Atlas Web Studio",
    "offer_type": "free homepage mockup",
    "website_starting_price": "$1,000",
    "website_premium_price_anchor": "$5,000",
    "website_hosting_monthly_ballpark": "$10-$30/month",
    "website_domain_cost_note": "domain costs are separate and should be confirmed before anything paid",
    "website_price_disclosure_rule": "only discuss paid website pricing when the buyer directly asks about price, cost, money, hidden fees, or what happens after the free mockup",
}

REQUIRED_VERTICALS = {
    "plumbing": "Apex Plumbing",
    "dental": "Bright Lane Dental",
    "auto_repair": "Northside Auto Repair",
    "hvac": "Summit HVAC",
    "hair_salon": "Luna Hair Studio",
    "home_cleaning": "FreshNest Cleaning",
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
        "sk_",
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def assert_text_markers(path: Path, markers: tuple[str, ...]) -> None:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")


def assert_simulation_test_shape(test: dict[str, Any], seen_ids: set[str], seen_verticals: set[str]) -> None:
    test_id = str(test.get("test_id", ""))
    assert_condition(test_id.startswith("sim_cross_vertical_"), f"test_id prefix mismatch: {test_id}")
    assert_condition(test_id not in seen_ids, f"duplicate test_id: {test_id}")
    seen_ids.add(test_id)
    assert_condition(test.get("type") == "simulation", f"{test_id} must be a simulation test")
    max_turns = test.get("simulation_max_turns")
    assert_condition(isinstance(max_turns, int) and 12 <= max_turns <= 22, f"{test_id} max turns should be 12-22")
    assert_condition("chat_history" not in test, f"{test_id} should not preload exact turns")

    scenario = str(test.get("simulation_scenario", "")).strip()
    success = str(test.get("success_condition", "")).strip()
    assert_condition(len(scenario) >= 300, f"{test_id} scenario is too thin")
    assert_condition(len(success) >= 350, f"{test_id} success condition is too thin")
    assert_condition("full conversation" in success.lower(), f"{test_id} must evaluate the full conversation")
    assert_condition("It fails if" in success, f"{test_id} must include failure conditions")
    assert_condition("natural closing" in success.lower() or "closing" in success.lower(), f"{test_id} must evaluate closing")
    assert_condition("restaurant leakage" in success.lower(), f"{test_id} must fail restaurant leakage")
    assert_condition("unapproved or nonsensical bracketed delivery tags" in success, f"{test_id} must evaluate delivery tags")
    assert_condition("Mike's Kitchen" not in scenario + success, f"{test_id} must not depend on Mike's Kitchen")

    variables = test.get("dynamic_variables")
    assert_condition(isinstance(variables, dict), f"{test_id} dynamic variables missing")
    vertical = variables.get("vertical")
    assert_condition(vertical in REQUIRED_VERTICALS, f"{test_id} vertical mismatch: {vertical}")
    seen_verticals.add(str(vertical))
    assert_condition(variables.get("business_name") == REQUIRED_VERTICALS[vertical], f"{test_id} business_name mismatch")
    for key in (
        "business_type",
        "city",
        "service_area",
        "known_website_status",
        "known_social_presence",
        "known_booking_or_ordering_path",
        "suspected_gap",
        "primary_offer_angle",
        "likely_decision_maker_role",
        "call_reason",
        "approved_value_points",
        "website_campaign_value_points",
        "optional_upsell_boundary",
        "simulation_focus",
        "buyer_temperature",
        "target_outcome",
        "scenario_expected_turns",
    ):
        assert_condition(isinstance(variables.get(key), str) and variables[key].strip(), f"{test_id} missing {key}")
    assert_condition("restaurant" not in str(variables.get("business_type", "")).lower(), f"{test_id} has restaurant business_type")
    assert_condition("menu" not in str(variables.get("approved_value_points", "")).lower(), f"{test_id} approved values leaked menu")
    assert_condition("reservation" not in str(variables.get("approved_value_points", "")).lower(), f"{test_id} approved values leaked reservation")


def main() -> None:
    for path in (RUNNER, MANIFEST, TESTS, DOC, INDEX, COMMANDS, METHODOLOGY_LOG):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    test_pack = read_json(TESTS)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(test_pack.get("package_id") == CHECKPOINT_ID, "test pack package_id mismatch")
    assert_condition(test_pack.get("test_type") == "simulation", "test pack must be marked simulation")
    assert_condition(manifest.get("upload_intent", {}).get("test_type") == "simulation", "manifest test_type mismatch")
    assert_condition(manifest.get("upload_intent", {}).get("target_test_folder_name") == FOLDER_NAME, "target folder mismatch")
    assert_condition(manifest.get("knowledge_base_docs") == [], "test pack must not upload KB docs")
    assert_condition(
        manifest.get("baseline_tests") == [str(TESTS.relative_to(ROOT)).replace("\\", "/")],
        "manifest tests mismatch",
    )

    suite_vars = test_pack.get("dynamic_variables")
    assert_condition(isinstance(suite_vars, dict), "suite dynamic variables missing")
    for key, expected in COMMON_DYNAMIC_VALUES.items():
        assert_condition(suite_vars.get(key) == expected, f"dynamic variable mismatch for {key}")

    serialized_pack = json.dumps(test_pack, ensure_ascii=False)
    assert_condition("Mike's Kitchen" not in serialized_pack, "cross-vertical pack must not depend on Mike's Kitchen")
    assert_no_secret_or_private_markers(test_pack)

    tests = test_pack.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 6, "expected exactly six cross-vertical simulation tests")
    seen_ids: set[str] = set()
    seen_verticals: set[str] = set()
    for test in tests:
        assert_condition(isinstance(test, dict), "each test must be an object")
        assert_simulation_test_shape(test, seen_ids, seen_verticals)
    assert_condition(seen_verticals == set(REQUIRED_VERTICALS), "vertical coverage mismatch")

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
    assert_condition(isinstance(create_requests, list) and len(create_requests) == 6, "create request count mismatch")
    request_verticals: set[str] = set()
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
        for key, expected in COMMON_DYNAMIC_VALUES.items():
            assert_condition(variables.get(key) == expected, f"request missing common dynamic variable {key}")
        vertical = variables.get("vertical")
        assert_condition(vertical in REQUIRED_VERTICALS, "request vertical mismatch")
        request_verticals.add(vertical)
        assert_condition(variables.get("business_name") == REQUIRED_VERTICALS[vertical], "request business_name mismatch")
        assert_condition(variables.get("source_package_id") == CHECKPOINT_ID, "source_package_id mismatch")
    assert_condition(request_verticals == set(REQUIRED_VERTICALS), "request vertical coverage mismatch")

    request_entries = requests.get("requests", [])
    assert_condition(len(request_entries) == 7, "api request bundle should contain six creates and one run-tests draft")

    assert_text_markers(
        DOC,
        (
            CHECKPOINT_ID,
            FOLDER_NAME,
            "cross-vertical",
            "synthetic evaluation fixtures",
            "not a campaign-profile replacement",
            "provider writes remain blocked",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current ElevenLabs cross-vertical simulation-test checkpoint",
            "`ELEVENLABS-014-cross-vertical-local-business-simulation-tests`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 014 cross-vertical local-business simulation tests without provider calls",
            "python scripts\\validate_elevenlabs_014_cross_vertical_local_business_simulation_tests.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "ELEVENLABS-014 cross-vertical local-business simulation tests",
            "synthetic local-business verticals",
            "provider writes remain blocked",
        ),
    )

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "test_count": len(create_requests),
                "target_folder": FOLDER_NAME,
                "verticals": sorted(request_verticals),
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
