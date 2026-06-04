#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-004-mikes-kitchen-dynamic-tests"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_mikes_kitchen_tests.package.json"
)
TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_mikes_kitchen_dynamic_tests.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_004_MIKES_KITCHEN_DYNAMIC_TESTS.md"
OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "automation_plan.json"
REQUESTS = OUT_DIR / "api_requests.json"


REQUIRED_DYNAMIC_VALUES = {
    "business_name": "Mike's Kitchen",
    "business_type": "restaurant",
    "vertical": "restaurant",
    "city": "Austin",
    "service_area": "Austin",
    "known_website_status": "no full website known",
    "known_social_presence": "Instagram and Google Maps",
    "known_booking_or_ordering_path": "reservations by phone",
    "suspected_gap": "no clear menu, hours, location, and reservation path in one place",
    "primary_offer_angle": "menu, hours, location, and reservation calls",
    "likely_decision_maker_role": "owner or manager",
    "contact_name_if_known": "",
    "call_reason": "free homepage mockup for a clearer customer action path",
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


def main() -> None:
    assert_condition(MANIFEST.is_file(), "Mike's Kitchen manifest is missing.")
    assert_condition(TESTS.is_file(), "Mike's Kitchen test pack is missing.")
    assert_condition(DOC.is_file(), "ELEVENLABS-004 doc is missing.")

    test_pack = read_json(TESTS)
    assert_condition(test_pack.get("package_id") == CHECKPOINT_ID, "test pack package_id mismatch")
    tests = test_pack.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 10, "expected exactly ten dynamic tests")
    suite_vars = test_pack.get("dynamic_variables")
    assert_condition(isinstance(suite_vars, dict), "suite dynamic variables missing")
    for key, expected in REQUIRED_DYNAMIC_VALUES.items():
        assert_condition(suite_vars.get(key) == expected, f"dynamic variable mismatch for {key}")

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(MANIFEST),
            "--agent-id",
            "agent_7801kt0g32zxf4f8x5zkykj7syty",
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
    assert_condition(plan.get("knowledge_base_upload_requests") == [], "test pack must not upload KB docs")

    create_requests = plan.get("test_create_requests")
    assert_condition(isinstance(create_requests, list) and len(create_requests) == 10, "create request count mismatch")
    for request in create_requests:
        body = request.get("body", {})
        variables = body.get("dynamic_variables", {})
        assert_condition(body.get("type") == "llm", "expected llm response tests")
        assert_condition(str(body.get("name", "")).startswith(f"{CHECKPOINT_ID}::"), "test name prefix mismatch")
        assert_condition(body["success_examples"][0].get("type") == "success", "success example type mismatch")
        assert_condition(body["failure_examples"][0].get("type") == "failure", "failure example type mismatch")
        for key, expected in REQUIRED_DYNAMIC_VALUES.items():
            assert_condition(variables.get(key) == expected, f"request missing dynamic variable {key}")
        assert_condition(variables.get("source_package_id") == CHECKPOINT_ID, "source_package_id mismatch")
        assert_condition(isinstance(variables.get("scenario_focus"), str), "per-test scenario_focus missing")

    request_entries = requests.get("requests", [])
    assert_condition(len(request_entries) == 11, "api request bundle should contain ten creates and one run-tests draft")
    create_entries = [item for item in request_entries if item.get("request_id", "").startswith("create_test::")]
    assert_condition(len(create_entries) == 10, "api request bundle create count mismatch")

    doc_text = DOC.read_text(encoding="utf-8")
    for marker in (
        CHECKPOINT_ID,
        "Create the tests in ElevenLabs",
        "The tests are not attached to the agent by PATCH in this checkpoint.",
    ):
        assert_condition(marker in doc_text, f"Doc missing marker: {marker}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "test_count": len(create_requests),
                "dynamic_business_name": REQUIRED_DYNAMIC_VALUES["business_name"],
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
