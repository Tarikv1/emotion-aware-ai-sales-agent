#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents"
KB_ROOT = AGENT_ROOT / "knowledge_base"
ATLAS_KB_ROOT = KB_ROOT / "atlas_web_studio"
PROMPT = AGENT_ROOT / "prompts" / "web_design_atlas_sales_prompt.md"
ACTIVE_MANIFEST = AGENT_ROOT / "manifests" / "web_design_sales_spine_compression.package.json"
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
FINAL_TESTS = AGENT_ROOT / "tests" / "web_design_final_runtime_polish_tests.json"

CHECKPOINT_ID = "ELEVENLABS-032-final-runtime-polish"

FOCUSED_KB_FILES = (
    "atlas_offer_facts.md",
    "atlas_value_mechanisms.md",
    "atlas_vertical_playbooks.md",
    "atlas_objection_playbook.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_close_and_followup_playbook.md",
    "atlas_output_quality_rules.md",
)

RECOMMENDED_UPLOAD_DOCS = [
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core_summary.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/buyer_moves.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/value_and_roi_framing.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/objection_status_quo_and_competition.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/trust_and_risk_repair.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/conversation_repair.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/next_step_policy.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/disqualification_policy.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/ethical_persuasion_boundaries.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/call_quality_rubrics.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_value_mechanisms.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_vertical_playbooks.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_objection_playbook.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_close_and_followup_playbook.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md",
]

PROMPT_MARKERS = (
    "Buyer gives email -> confirm normalized email; no send language until explicit confirmation.",
    "process or delivery question",
    "Buyer confirms email without goodbye ->",
    "Do not claim Emma will call, follow up, check back, or reach out",
    "Lead with concrete mechanism first.",
    "Weak-phrase examples and mockup-scope examples live in Atlas Output Quality Rules.",
    "You're right. Have a good one.",
    "Guarantee-only lock triggers on the first turn",
)

KB_MARKERS = (
    "confirm the normalized email before saying the mockup will be sent",
    "Hard rule: confirm it before saying the mockup will be sent.",
    "No send language is allowed before explicit email confirmation.",
    "It'll be in your inbox",
    "Only after the buyer confirms the email should Emma say it will be sent.",
    "No automatic call, check-back, follow-up, or later reach-out is promised",
    "I can follow up later",
    "I'll check back",
    "I'll call after you review it",
    "I'll reach out later",
    "clearer online experience",
    "professional homepage",
    "convert visitors into customers",
    "Required headline mechanisms",
    "call path",
    "I'm not hanging up",
    "Do not repeat goodbye more than once",
    "by the end of the day",
    "reply to that email",
)

ANALYSIS_IDS = (
    "email_confirmation_requires_explicit_yes",
    "no_follow_up_leakage",
    "concrete_mechanism_headline_value",
    "terminal_close_no_loop",
    "delivery_timing_end_of_day",
    "guarantee_lock_first_turn",
    "email_reply_path_mentioned_when_closing",
)

TEST_IDS = (
    "sim_032_northside_email_no_send_before_confirm",
    "sim_032_bright_lane_email_plus_process_no_follow_up",
    "sim_032_apex_delivery_question_before_confirmation",
    "sim_032_plumbing_concrete_mechanism_no_generic_headline",
    "sim_032_terminal_close_no_loop",
)

TEST_MARKERS = (
    "email_confirmation_requires_explicit_yes",
    "no_follow_up_leakage",
    "concrete_mechanism_headline_value",
    "terminal_close_no_loop",
    "delivery_timing_end_of_day",
    "service@northsideautorepair.com",
    "brightlanedental@gmail.com",
    "apexplumbingdenver@email.com",
    "I can follow up later",
    "convert visitors into customers",
    "I'm not hanging up",
)

BANNED_BRACKET_LABEL = re.compile(
    r"\[(?:happy|calm|slow|neutral|thinking|sales|policy|source|tone|stage|emotion|pacing|internal)[^\]\r\n]*\]",
    re.I,
)

PLACEHOLDER_EMAIL = re.compile(
    r"\[your email address\]|\[email protected\]|\[my email address\]|\b[\w.+-]+@example\.com\b",
    re.I,
)

RISKY_TIMING = ("in a few days", "shortly", "soon", "within a few business days")
TIMING_SAFE_CONTEXT = (
    "do not",
    "forbidden",
    "fail",
    "failure",
    "hard fail",
    "treat",
    "unless",
    "disallow",
    "wrong delivery timing",
    "conflicts",
    "another conflicting timing",
    "active timing",
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


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert_condition(not missing, f"{label} missing markers: {missing}")


def active_test_paths() -> list[Path]:
    return sorted((AGENT_ROOT / "tests").glob("web_design_*.json"))


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def assert_prompt() -> None:
    text = read_text(PROMPT)
    assert_condition(word_count(text) <= 1650, f"Prompt is no longer compact: {word_count(text)} words")
    assert_markers("system prompt", text, PROMPT_MARKERS)


def assert_kb_rules() -> None:
    combined = "\n".join(read_text(ATLAS_KB_ROOT / name) for name in FOCUSED_KB_FILES)
    assert_markers("focused Atlas KB rules", combined, KB_MARKERS)


def assert_analysis() -> None:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "Analysis criteria missing")
    assert_condition(len(criteria) <= 30, "ElevenLabs live Analysis supports at most 30 criteria")
    ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    setup = read_text(ANALYSIS_SETUP)
    combined = json.dumps(config, ensure_ascii=False) + "\n" + setup
    for criterion_id in ANALYSIS_IDS:
        assert_condition(criterion_id in ids, f"Analysis config missing criterion: {criterion_id}")
        assert_condition(f"`{criterion_id}`" in setup, f"Analysis setup missing criterion: {criterion_id}")
    assert_markers("analysis markers", combined, TEST_MARKERS[:5])
    assert_condition("I can follow up later" in combined and "Hard fail" in combined, "Analysis missing follow-up leakage hard fail")
    assert_condition("convert visitors into customers" in combined, "Analysis missing generic conversion phrase ban")


def assert_tests() -> None:
    payload = read_json(FINAL_TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "032 test package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 5, "032 final polish tests must contain five simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    for test_id in TEST_IDS:
        assert_condition(test_id in ids, f"Missing final polish test: {test_id}")
    combined = read_text(FINAL_TESTS)
    assert_markers("032 tests", combined, TEST_MARKERS)
    placeholder_hits: list[str] = []
    for path in active_test_paths():
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if PLACEHOLDER_EMAIL.search(line):
                placeholder_hits.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
    assert_condition(not placeholder_hits, "Active web-design tests contain placeholder-looking emails:\n" + "\n".join(placeholder_hits[:20]))


def assert_manifest() -> None:
    manifest = read_json(ACTIVE_MANIFEST)
    active = manifest.get("active_kb_recommendation", {})
    docs = active.get("recommended_upload_docs")
    blocked = active.get("not_recommended_for_active_upload_unless_explicitly_needed", [])
    assert_condition(docs == RECOMMENDED_UPLOAD_DOCS, "Active manifest no longer points to the focused KB chunks")
    for name in FOCUSED_KB_FILES:
        assert_condition((ATLAS_KB_ROOT / name).is_file(), f"Missing focused KB file: {name}")
    for old_doc in (
        "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
    ):
        assert_condition(old_doc not in docs, f"Old monolithic Atlas doc is recommended: {old_doc}")
        assert_condition(old_doc in blocked, f"Old monolithic Atlas doc is not blocked: {old_doc}")


def assert_no_bracketed_labels(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if BANNED_BRACKET_LABEL.search(line):
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
    assert_condition(not failures, "Bracketed labels found:\n" + "\n".join(failures[:30]))


def assert_delivery_timing(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        lines = read_text(path).splitlines()
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.casefold()
            context = "\n".join(lines[max(0, line_number - 6) : line_number]).casefold()
            if any(phrase in line for phrase in RISKY_TIMING) and not any(marker in context for marker in TIMING_SAFE_CONTEXT):
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {raw_line.strip()}")
    assert_condition(not failures, "Unsafe delivery timing found:\n" + "\n".join(failures[:30]))


def main() -> None:
    focused_paths = [ATLAS_KB_ROOT / name for name in FOCUSED_KB_FILES]
    checked_paths = [PROMPT, ANALYSIS_CONFIG, ANALYSIS_SETUP, FINAL_TESTS, *focused_paths]
    assert_prompt()
    assert_kb_rules()
    assert_analysis()
    assert_tests()
    assert_manifest()
    assert_no_bracketed_labels(checked_paths)
    assert_delivery_timing([PROMPT, ANALYSIS_CONFIG, ANALYSIS_SETUP, FINAL_TESTS, *focused_paths])

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read_text(PROMPT)),
                "analysis_criteria_count": len(read_json(ANALYSIS_CONFIG)["success_evaluation_criteria"]),
                "final_runtime_test_count": 5,
                "email_confirmation_hardening": True,
                "follow_up_leakage_guard": True,
                "concrete_mechanism_headline_value": True,
                "terminal_close_no_loop": True,
                "delivery_timing": "by the end of the day",
                "focused_kb_architecture": True,
                "git_diff_check": "pass",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
