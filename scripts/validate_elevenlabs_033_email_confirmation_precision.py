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
PRECISION_TESTS = AGENT_ROOT / "tests" / "web_design_email_confirmation_precision_tests.json"

CHECKPOINT_ID = "ELEVENLABS-033-email-confirmation-precision"

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
    "Only yes, correct, that's right/correct, right email, or right place count.",
    "I'll take a look",
    "I'll keep an eye out",
    "hidden fees?",
    "send it there",
    "Lead with concrete mechanism first.",
    "Guarantee-only exact sequence:",
)

EMAIL_CONFIRMATION_MARKERS = (
    "Only these count as email confirmation:",
    "\"yes\"",
    "\"correct\"",
    "\"that's right\"",
    "\"that's correct\"",
    "\"yes, that's the right email\"",
    "\"that's the right place\"",
    "\"that email is right\"",
    "These do not count as email confirmation:",
    "I'll take a look when I can.",
    "I'll keep an eye out.",
    "No hidden fees, right?",
    "And this is really free, right?",
    "I'm not committing to anything.",
    "Just send it there.",
    "That's where you can send it.",
    "I'll check it later.",
    "Send it there.",
)

FORBIDDEN_SEND_MARKERS = (
    "No send language is allowed before explicit email confirmation.",
    "I'll send it",
    "I'll send the mockup",
    "I'll send it there",
    "You'll receive it",
    "I'll get that sent",
    "I'll send that over",
    "It'll be in your inbox",
)

MECHANISM_MARKERS = (
    "Lead with concrete mechanism first.",
    "Generic website language can only follow the mechanism.",
    "clearer online presence",
    "clearer online experience",
    "professional homepage",
    "professional website",
    "central hub",
    "convert visitors into customers",
    "more engagement",
    "refreshed online presence",
    "for a salon, it can cut down repetitive DMs",
)

ANALYSIS_IDS = (
    "email_confirmation_requires_explicit_yes",
    "concrete_mechanism_headline_value",
    "no_follow_up_leakage",
    "delivery_timing_end_of_day",
    "guarantee_lock_first_turn",
)

TEST_IDS = (
    "sim_033_summit_email_take_a_look_not_confirmation",
    "sim_033_freshnest_keep_eye_out_not_confirmation",
    "sim_033_apex_free_question_not_confirmation",
    "sim_033_bright_lane_hidden_fees_not_confirmation",
    "sim_033_salon_mechanism_led_value",
)

TEST_MARKERS = (
    "summithvac@gmail.com",
    "I'll take a look when I can",
    "freshnestowner@gmail.com",
    "I'll keep an eye out",
    "apexplumbingdenver@gmail.com",
    "this is really free",
    "brightlanedental@gmail.com",
    "No hidden fees",
    "central hub",
    "convert visitors into customers",
)

BANNED_BRACKET_LABEL = re.compile(
    r"\[(?:happy|calm|slow|neutral|thinking|sales|policy|source|tone|stage|emotion|pacing|internal)[^\]\r\n]*\]",
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
    "too soon",
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


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def active_test_paths() -> list[Path]:
    return sorted((AGENT_ROOT / "tests").glob("web_design_*.json"))


def assert_prompt() -> None:
    text = read_text(PROMPT)
    assert_condition(word_count(text) <= 1900, f"Prompt is no longer compact: {word_count(text)} words")
    assert_markers("prompt", text, PROMPT_MARKERS)


def assert_kb() -> None:
    close = read_text(ATLAS_KB_ROOT / "atlas_close_and_followup_playbook.md")
    output = read_text(ATLAS_KB_ROOT / "atlas_output_quality_rules.md")
    offer = read_text(ATLAS_KB_ROOT / "atlas_offer_facts.md")
    objection = read_text(ATLAS_KB_ROOT / "atlas_objection_playbook.md")
    assert_markers("email confirmation precision", close, EMAIL_CONFIRMATION_MARKERS)
    assert_markers("forbidden send language", close, FORBIDDEN_SEND_MARKERS)
    assert_condition("Incorrect before buyer confirmation" not in close, "Removed bad send-before-confirmation example returned")
    assert_markers("mechanism-led value", output, MECHANISM_MARKERS)
    assert_condition("No automatic call, check-back, or follow-up is promised by default." in offer, "No automatic callback/follow-up default missing")
    assert_condition("by the end of the day" in offer and "by the end of the day" in close, "End-of-day delivery timing missing")
    assert_condition("Trigger the lock on the first turn" in objection, "Guarantee lock missing")


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
    assert_markers("analysis non-confirmation comments", combined, EMAIL_CONFIRMATION_MARKERS[9:])
    assert_markers("analysis forbidden send phrases", combined, FORBIDDEN_SEND_MARKERS[1:])
    assert_condition("Lead with concrete mechanism first" in combined, "Analysis missing mechanism-led value rule")


def assert_tests() -> None:
    payload = read_json(PRECISION_TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "033 test package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 5, "033 tests must contain five simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    for test_id in TEST_IDS:
        assert_condition(test_id in ids, f"Missing 033 test: {test_id}")
    text = read_text(PRECISION_TESTS)
    assert_markers("033 tests", text, TEST_MARKERS)
    assert_markers("033 tests forbidden send language", text, FORBIDDEN_SEND_MARKERS[1:])


def assert_manifest() -> None:
    manifest = read_json(ACTIVE_MANIFEST)
    active = manifest.get("active_kb_recommendation", {})
    docs = active.get("recommended_upload_docs")
    blocked = active.get("not_recommended_for_active_upload_unless_explicitly_needed", [])
    assert_condition(docs == RECOMMENDED_UPLOAD_DOCS, "Active manifest no longer points to focused KB chunks")
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
    checked_paths = [PROMPT, ANALYSIS_CONFIG, ANALYSIS_SETUP, PRECISION_TESTS, *focused_paths]
    assert_prompt()
    assert_kb()
    assert_analysis()
    assert_tests()
    assert_manifest()
    assert_no_bracketed_labels(checked_paths)
    assert_delivery_timing([PROMPT, ANALYSIS_CONFIG, ANALYSIS_SETUP, PRECISION_TESTS, *focused_paths, *active_test_paths()])

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read_text(PROMPT)),
                "analysis_criteria_count": len(read_json(ANALYSIS_CONFIG)["success_evaluation_criteria"]),
                "email_confirmation_requires_explicit_yes": True,
                "non_confirmation_comments_listed": True,
                "mechanism_led_value": True,
                "focused_kb_architecture": True,
                "git_diff_check": "pass",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
