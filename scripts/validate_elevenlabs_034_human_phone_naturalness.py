#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents"
ATLAS_KB_ROOT = AGENT_ROOT / "knowledge_base" / "atlas_web_studio"
PROMPT = AGENT_ROOT / "prompts" / "web_design_atlas_sales_prompt.md"
OUTPUT_RULES = ATLAS_KB_ROOT / "atlas_output_quality_rules.md"
CLOSE_PLAYBOOK = ATLAS_KB_ROOT / "atlas_close_and_followup_playbook.md"
PRICE_KB = ATLAS_KB_ROOT / "atlas_price_scope_cost_drivers.md"
OBJECTION_KB = ATLAS_KB_ROOT / "atlas_objection_playbook.md"
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
HUMAN_TESTS = AGENT_ROOT / "tests" / "web_design_human_phone_naturalness_tests.json"
ACTIVE_MANIFEST = AGENT_ROOT / "manifests" / "web_design_sales_spine_compression.package.json"

CHECKPOINT_ID = "ELEVENLABS-034-human-phone-naturalness"

TEST_IDS = (
    "sim_034_freshnest_price_pressure_cost_driver",
    "sim_034_luna_instagram_soft_agreement_no_repeated_cta",
    "sim_034_apex_guarantee_lock_no_reopen",
    "sim_034_known_context_phrasing",
    "sim_034_terminal_close_take_care_only",
    "sim_034_bright_lane_email_plus_free_question",
)

ANALYSIS_MARKERS = (
    "AI monologue",
    "residue loop",
    "price ballpark after repeated ask",
    "terminal \"Take care\"",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_text(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_contains(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def assert_tests() -> None:
    payload = read_json(HUMAN_TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "034 test package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 6, "034 tests must contain six simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    for test_id in TEST_IDS:
        assert_condition(test_id in ids, f"Missing 034 test: {test_id}")
    text = read_text(HUMAN_TESTS)
    assert_contains(
        "034 tests",
        text,
        (
            "FreshNest Cleaning",
            "service area",
            "one-time versus recurring",
            "move-in/move-out",
            "custom copy",
            "Yeah, exactly. I can send it over - best email?",
            "be careful with anyone selling",
            "I've got enough for the first version. Best email?",
            "Take care.",
            "brightlanedental@gmail.com",
        ),
    )


def assert_prompt_and_kb() -> None:
    prompt = read_text(PROMPT)
    output = read_text(OUTPUT_RULES)
    close = read_text(CLOSE_PLAYBOOK)
    price = read_text(PRICE_KB)
    objection = read_text(OBJECTION_KB)

    for label, text in (("prompt", prompt), ("output rules", output)):
        assert_condition("Human Phone Call Standard" in text, f"{label} missing Human Phone Call Standard")
        assert_condition("Residue Loop" in text, f"{label} missing Residue Loop")
    assert_condition("Residue Loop" in close, "close playbook missing Residue Loop")
    assert_condition("first or second price ask" in price, "price KB missing first or second price ask")
    assert_condition("Best email?" in close, "close playbook missing short Best email ask")
    assert_condition(
        "I already have {{business_name}} and the business type" not in close,
        "close playbook still contains old CRM-ish known-context phrase",
    )
    assert_condition("Be careful with anyone selling it that way" in objection, "objection KB missing guarantee warning")


def assert_analysis() -> None:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "Analysis criteria missing")
    assert_condition(len(criteria) <= 30, "ElevenLabs live Analysis supports at most 30 criteria")
    setup = read_text(ANALYSIS_SETUP)
    combined = json.dumps(config, ensure_ascii=False) + "\n" + setup
    assert_contains("analysis", combined, ANALYSIS_MARKERS)
    assert_contains(
        "analysis tightened failures",
        combined,
        (
            "buyer asks price twice",
            "max turns because Emma avoided price",
            "spoken at/dot form",
            "guarantee-only buyer receives any mockup pitch after lock",
            "I already have {{business_name}} and the business type",
            "You're welcome. Have a great day",
        ),
    )


def assert_manifest_unchanged() -> None:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--", str(ACTIVE_MANIFEST.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(diff.returncode == 0, diff.stderr or diff.stdout)
    assert_condition(not diff.stdout.strip(), "Active upload manifest changed without validator requirement")


def main() -> None:
    assert_tests()
    assert_prompt_and_kb()
    assert_analysis()
    assert_manifest_unchanged()
    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "human_phone_call_standard": True,
                "residue_loop_guard": True,
                "analysis_criteria_count": len(read_json(ANALYSIS_CONFIG)["success_evaluation_criteria"]),
                "focused_test_count": 6,
                "active_upload_manifest_changed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
