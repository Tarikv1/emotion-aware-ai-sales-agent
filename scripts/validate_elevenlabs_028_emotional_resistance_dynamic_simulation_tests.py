#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-028-emotional-resistance-dynamic-simulation-tests"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_emotional_resistance_dynamic_simulation_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_emotional_resistance_dynamic_simulation_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_028_EMOTIONAL_RESISTANCE_DYNAMIC_SIMULATION_TESTS.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "simulation_tests_plan.json"
REQUESTS = OUT_DIR / "simulation_tests_requests.json"
FOLDER_NAME = "Atlas Web Studio - Emotional Resistance Dynamic Simulation V1"
MODEL_ID = "gemini-2.5-flash"


COMMON_DYNAMIC_VALUES = {
    "campaign_name": "atlas-web-studio-emotional-resistance-dynamic-simulation",
    "caller_identity": "Emma from Atlas Web Studio",
    "offer_type": "free homepage mockup",
    "website_starting_price": "$1,000",
    "website_premium_price_anchor": "$5,000",
    "website_hosting_monthly_ballpark": "$10-$30/month",
    "website_domain_cost_note": "domain costs are separate and should be confirmed before anything paid",
    "target_offer_objective": "earn permission to send the free mockup, secure a callback, disqualify cleanly, or stop immediately when required",
}

REQUIRED_FOCI = {
    "angry_owner_interrupts",
    "refusal_not_dnc_persuasion",
    "trust_scam_suspicion",
    "silent_minimal_buyer",
    "rapid_fire_status_quo_objections",
    "price_hostile_hidden_costs",
    "angry_email_spellout_two_step_close",
    "guarantee_only_bad_fit_disqualification",
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
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def read_text(path: Path) -> str:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def assert_no_private_or_secret_markers(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    blocked = (
        "xi-api-key",
        "api key value",
        "creator_email",
        "creator_name",
        "access_info",
        "data/private/",
        "data/private-restricted/",
        "private transcript",
        "sk_",
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def assert_text_markers(path: Path, markers: tuple[str, ...]) -> None:
    text = read_text(path)
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")


def assert_simulation_shape(test: dict[str, Any], seen_ids: set[str], seen_focus: set[str]) -> None:
    test_id = str(test.get("test_id", ""))
    assert_condition(test_id.startswith("sim_028_"), f"test_id prefix mismatch: {test_id}")
    assert_condition(test_id not in seen_ids, f"duplicate test_id: {test_id}")
    seen_ids.add(test_id)
    assert_condition(test.get("type") == "simulation", f"{test_id} must be simulation")
    assert_condition(test.get("simulated_user_model") == MODEL_ID, f"{test_id} simulated_user_model mismatch")
    assert_condition(test.get("evaluation_model") == MODEL_ID, f"{test_id} evaluation_model mismatch")
    max_turns = test.get("simulation_max_turns")
    assert_condition(isinstance(max_turns, int) and 16 <= max_turns <= 20, f"{test_id} max turns must be 16-20")
    assert_condition("chat_history" not in test, f"{test_id} should not preload exact turns")

    scenario = str(test.get("simulation_scenario", "")).strip()
    success = str(test.get("success_condition", "")).strip()
    assert_condition(len(scenario) >= 350, f"{test_id} scenario is too thin")
    assert_condition(len(success) >= 550, f"{test_id} success condition is too thin")
    for marker in (
        "The full conversation passes",
        "It fails if",
        "hard stop",
        "email",
        "normalized email",
        "guarantee",
    ):
        assert_condition(marker.lower() in success.lower(), f"{test_id} success missing marker: {marker}")

    variables = test.get("dynamic_variables")
    assert_condition(isinstance(variables, dict), f"{test_id} dynamic variables missing")
    focus = str(variables.get("simulation_focus", ""))
    assert_condition(focus in REQUIRED_FOCI, f"{test_id} unexpected simulation_focus: {focus}")
    seen_focus.add(focus)
    for key in (
        "business_name",
        "business_type",
        "vertical",
        "city",
        "service_area",
        "known_website_status",
        "known_social_presence",
        "known_booking_or_ordering_path",
        "primary_value_mechanism",
        "buyer_temperature",
        "buyer_emotional_state",
        "conversation_pressure",
        "persuasion_boundary",
        "target_outcome",
        "scenario_expected_turns",
    ):
        assert_condition(isinstance(variables.get(key), str) and variables[key].strip(), f"{test_id} missing {key}")


def main() -> None:
    for path in (RUNNER, MANIFEST, TESTS, DOC, INDEX, COMMANDS):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    tests_payload = read_json(TESTS)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(tests_payload.get("package_id") == CHECKPOINT_ID, "test package_id mismatch")
    assert_condition(tests_payload.get("test_type") == "simulation", "test_type mismatch")
    assert_condition(manifest.get("knowledge_base_docs") == [], "test-only package must not upload KB docs")
    assert_condition(
        manifest.get("baseline_tests") == [str(TESTS.relative_to(ROOT)).replace("\\", "/")],
        "manifest baseline_tests mismatch",
    )
    upload_intent = manifest.get("upload_intent", {})
    assert_condition(upload_intent.get("target_test_folder_name") == FOLDER_NAME, "target folder mismatch")
    assert_condition(upload_intent.get("simulated_user_model") == MODEL_ID, "manifest simulated_user_model mismatch")
    assert_condition(upload_intent.get("evaluation_model") == MODEL_ID, "manifest evaluation_model mismatch")
    assert_condition(upload_intent.get("simulation_max_turns") == "16-20", "manifest max-turns mismatch")

    suite_vars = tests_payload.get("dynamic_variables")
    assert_condition(isinstance(suite_vars, dict), "suite dynamic variables missing")
    for key, expected in COMMON_DYNAMIC_VALUES.items():
        assert_condition(suite_vars.get(key) == expected, f"suite dynamic variable mismatch: {key}")

    tests = tests_payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 8, "expected exactly eight new emotional-resistance simulations")
    seen_ids: set[str] = set()
    seen_focus: set[str] = set()
    for test in tests:
        assert_condition(isinstance(test, dict), "each test must be an object")
        assert_simulation_shape(test, seen_ids, seen_focus)
    assert_condition(seen_focus == REQUIRED_FOCI, "scenario focus coverage mismatch")
    assert_no_private_or_secret_markers(tests_payload)

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
    assert_condition(plan.get("live_provider_calls_made") is False, "dry run must not call provider")
    create_requests = plan.get("test_create_requests")
    assert_condition(isinstance(create_requests, list) and len(create_requests) == 8, "create request count mismatch")
    for request in create_requests:
        body = request.get("body", {})
        assert_condition(body.get("type") == "simulation", "request type mismatch")
        assert_condition(body.get("simulated_user_model") == MODEL_ID, "request simulated_user_model mismatch")
        assert_condition(body.get("evaluation_model") == MODEL_ID, "request evaluation_model mismatch")
        assert_condition(16 <= body.get("simulation_max_turns", 0) <= 20, "request max-turns mismatch")
        variables = body.get("dynamic_variables", {})
        for key, expected in COMMON_DYNAMIC_VALUES.items():
            assert_condition(variables.get(key) == expected, f"request missing suite dynamic variable: {key}")
        assert_condition(variables.get("source_package_id") == CHECKPOINT_ID, "source_package_id mismatch")

    assert_text_markers(
        DOC,
        (
            CHECKPOINT_ID,
            MODEL_ID,
            FOLDER_NAME,
            "angry, avoidant, suspicious, terse, and bad-fit buyer behavior",
            "provider writes remain blocked",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current ElevenLabs emotional-resistance simulation-test checkpoint",
            f"`{CHECKPOINT_ID}`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the ElevenLabs 028 emotional-resistance dynamic simulation tests without provider calls",
            "python scripts\\validate_elevenlabs_028_emotional_resistance_dynamic_simulation_tests.py",
        ),
    )

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "test_count": len(create_requests),
                "simulated_user_model": MODEL_ID,
                "evaluation_model": MODEL_ID,
                "simulation_max_turns": "16-20",
                "target_folder": FOLDER_NAME,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
