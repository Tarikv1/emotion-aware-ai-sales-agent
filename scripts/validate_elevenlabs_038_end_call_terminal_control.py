#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-038-end-call-terminal-control"

PROMPT = ROOT / "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
CLOSE = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_close_and_followup_playbook.md"
OUTPUT = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md"
ANALYSIS_CONFIG = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_setup.md"
TESTS = ROOT / "runtime/providers/elevenlabs_agents/tests/web_design_end_call_terminal_control_tests.json"
ACTIVE_UPLOAD_MANIFEST = ROOT / "runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json"
PROCEDURES_DIR = ROOT / "runtime/providers/elevenlabs_agents/procedures"

EXPECTED_TEST_IDS = {
    "sim_038_email_confirmed_goodbye_atomic_end_call",
    "sim_038_delivery_already_stated_then_goodbye",
    "sim_038_hard_stop_ends_immediately",
    "sim_038_guarantee_only_terminal_end_call",
    "sim_038_pending_email_blocks_end_call",
    "sim_038_unresolved_price_concern_blocks_end_call",
    "sim_038_nonterminal_thanks_preserves_sales_motion",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def git_diff_names(*paths: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def validate_prompt_and_kb() -> None:
    prompt = read(PROMPT)
    close = read(CLOSE)
    output = read(OUTPUT)
    combined = "\n".join((prompt, close, output))

    assert_condition(word_count(prompt) <= 1650, f"prompt no longer compact: {word_count(prompt)} words")
    assert_markers(
        "prompt end-call control",
        prompt,
        (
            "## End Call Tool Control",
            "`end_call` is the only terminal mechanism for completed live calls",
            "Use it exactly once",
            "Put the sole final spoken line in the tool `message`",
            "Do not speak a separate farewell before invoking it",
            "A live direct question or unresolved concern outranks `end_call`",
            "Pending email confirmation blocks `end_call`",
            "Accepted mockup with no email known also blocks `end_call`",
            "by-the-end-of-day timing",
            "Never invoke `end_call` twice",
            "Never reopen the pitch after invoking it",
        ),
    )
    assert_markers(
        "close playbook tool-aware states",
        close,
        (
            "## End Call Tool Control",
            "Use `end_call` once for completed terminal states.",
            "The final spoken line must be in the tool call `message`.",
            "Do not speak a separate goodbye before invoking the tool",
            "email confirmation is pending",
            "the buyer accepted the mockup but no email is known",
            "a live direct question or unresolved price, process, capability, scope, or trust concern remains",
            "Email confirmed and goodbye same turn",
            "Great, I'll send it there by the end of the day. Take care.",
            "Buyer requested no further contact",
            "Got it. Take care.",
            "Guarantee requirement makes Atlas a bad fit and the conversation is complete",
            "Understood. Have a good one.",
            "hello@cedarridgeglass.com",
        ),
    )
    assert_markers(
        "output rules terminal quality",
        output,
        (
            "no farewell before `end_call`",
            "no second farewell after `end_call`",
            "no repeated \"Take care\"",
            "no tool-name or tool-state leakage to the buyer",
            "final tool message should be short, natural, and contain no policy language",
            "direct unresolved buyer concern must be answered before terminal action",
        ),
    )
    assert_condition("procedure_under_test" not in combined, "runtime prompt/KB references procedure_under_test")


def validate_analysis() -> int:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "analysis criteria missing")
    assert_condition(len(criteria) <= 30, "ElevenLabs Analysis criteria cap exceeded")
    combined = json.dumps(config, ensure_ascii=False) + "\n" + read(ANALYSIS_SETUP)
    assert_markers(
        "analysis end-call semantics",
        combined,
        (
            "a completed terminal state invokes `end_call` exactly once",
            "no separate farewell precedes it",
            "no pitch follows",
            "no end_call invocation occurs after a clear completed goodbye where the tool is available",
            "`end_call` is invoked more than once",
            "Emma speaks a separate confirmation or goodbye before invoking the tool",
            "unresolved concern remains",
            "pending email remains except hard-stop override",
            "accepted mockup but no email",
            "omits end-of-day delivery timing when email confirmation and goodbye occur in the same turn",
            "hard stop or do-not-call request immediately invokes one `end_call`",
            "terminal guarantee-only bad fit",
        ),
    )
    return len(criteria)


def validate_tests() -> int:
    payload = read_json(TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "038 package_id mismatch")
    assert_condition(payload.get("test_type") == "simulation", "038 tests must be simulation tests")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 7, "038 tests must contain seven simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    assert_condition(ids == EXPECTED_TEST_IDS, f"038 test IDs mismatch: {sorted(ids)}")
    serialized = json.dumps(payload, ensure_ascii=False)
    assert_condition("procedure_under_test" not in serialized, "038 tests contain procedure routing field")
    assert_condition("Procedures" not in serialized, "038 tests reference Procedures as runtime dependency")
    assert_markers(
        "038 test semantics",
        serialized,
        (
            "end_call exactly once",
            "by-the-end-of-day delivery timing",
            "message 'Take care.'",
            "Got it. Take care.",
            "Understood. Have a good one.",
            "Pending email confirmation must block terminal action",
            "no send language",
            "does not invoke end_call",
            "likely total project band, not an automatic add-on",
            "one low-friction mockup invitation",
        ),
    )
    for test in tests:
        assert_condition(test.get("simulated_user_model") == "gemini-2.5-flash", f"{test.get('test_id')} simulated_user_model mismatch")
        assert_condition(test.get("evaluation_model") == "gemini-2.5-flash", f"{test.get('test_id')} evaluation_model mismatch")
        assert_condition(isinstance(test.get("simulation_max_turns"), int), f"{test.get('test_id')} missing max turns")
        assert_condition(6 <= int(test["simulation_max_turns"]) <= 10, f"{test.get('test_id')} max turns outside 6-10")
    return len(tests)


def validate_manifest_boundaries() -> None:
    manifest = read_json(ACTIVE_UPLOAD_MANIFEST)
    recommended = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs", [])
    assert_condition(isinstance(recommended, list) and recommended, "manifest recommended upload docs missing")
    forbidden_fragments = (
        "runtime/providers/elevenlabs_agents/tests",
        "runtime/providers/elevenlabs_agents/analysis",
        "research/experiments/generated",
        "atlas_web_studio_web_design_campaign.md",
        "atlas_web_studio_web_design_campaign_overlay.md",
        "atlas_web_studio_web_design_campaign_profile.md",
    )
    for item in recommended:
        item_text = str(item)
        for forbidden in forbidden_fragments:
            assert_condition(forbidden not in item_text, f"forbidden KB upload item present: {item_text}")
    assert_condition(not git_diff_names(str(ACTIVE_UPLOAD_MANIFEST.relative_to(ROOT))), "active KB upload manifest was modified")
    procedure_diff = git_diff_names(str(PROCEDURES_DIR.relative_to(ROOT)))
    assert_condition(not procedure_diff, f"Procedures changed: {procedure_diff}")


def main() -> None:
    validate_prompt_and_kb()
    criteria_count = validate_analysis()
    test_count = validate_tests()
    validate_manifest_boundaries()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read(PROMPT)),
                "analysis_criteria_count": criteria_count,
                "test_count": test_count,
                "active_upload_manifest_changed": False,
                "procedures_changed": False,
                "dashboard_tests_created": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
