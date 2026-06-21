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
RUNTIME_TESTS = AGENT_ROOT / "tests" / "web_design_runtime_elite_hardening_tests.json"
GENERATED_UPLOAD_ROOT = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-025-elite-sales-agent-operating-contract"

CHECKPOINT_ID = "ELEVENLABS-031-runtime-elite-hardening"

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
    "Guarantee-only lock triggers on the first turn",
    "Use Atlas Objection Playbook lock wording.",
    "After the guarantee-only lock, do not ask to send the mockup, ask for email",
    "Delivery timing is \"by the end of the day\"",
    "Buyer confirms email -> close naturally.",
    "If email comes with process or delivery question",
    "If the buyer asks why Emma is still talking",
    "Never output bracketed labels of any kind.",
)

GUARANTEE_LOCK_MARKERS = (
    "If the first buyer turn requires guaranteed page-one SEO, emergency calls, more calls, jobs, patients, rankings, traffic, revenue, or outcomes",
    "Do not pitch the mockup first.",
    "Trigger the lock on the first turn or any later turn",
    "Do not ask to send the mockup, ask for email",
    "That's right - no guarantee. I don't want to waste your time. Have a good one.",
)

DELIVERY_MARKERS = (
    "Canonical mockup delivery timing is by the end of the day.",
    "Great, I'll send it there by the end of the day. Have a good one.",
    "If anything looks off",
    "reply to that email",
)

EMAIL_MARKERS = (
    "Buyer gives email -> confirm normalized email; no send language until explicit confirmation.",
    "Buyer confirms email -> close naturally.",
    "Hard rule: confirm it before saying the mockup will be sent.",
    "I've got brightlanedental@gmail.com - is that right?",
    "email_confirmation_requires_explicit_yes",
)

ANALYSIS_EMAIL_MARKERS = (
    "email_confirmation_requires_explicit_yes",
    "before any send language",
    "brightlanedental@gmail.com",
    "luna.hair.studio.tampa@email.com",
)

WEAK_PHRASES = (
    "refreshed online presence",
    "help patients find your services",
    "better engagement",
    "inquiries",
    "clearer website",
)

ANALYSIS_IDS = (
    "guarantee_lock_first_turn",
    "no_runtime_tone_tags",
    "delivery_timing_end_of_day",
    "email_reply_path_mentioned_when_closing",
    "email_confirmation_requires_explicit_yes",
    "terminal_close_no_loop",
    "realistic_test_contact_values",
)

TEST_IDS = (
    "sim_031_apex_plumbing_first_turn_guarantee_lock",
    "sim_031_bright_lane_email_reply_path_delivery_timing",
    "sim_031_luna_spoken_email_two_step",
    "sim_031_summit_hvac_process_risk_no_email_loop",
    "sim_031_terminal_close_tag_leakage",
)

TEST_MARKERS = (
    "guarantee_lock_first_turn",
    "no_runtime_tone_tags",
    "delivery_timing_end_of_day",
    "email_reply_path",
    "email_confirmation_requires_explicit_yes",
    "terminal_close_no_loop",
    "realistic_test_contact_values",
    "brightlanedental@gmail.com",
    "info@summithvac.com",
    "luna.hair.studio.tampa@email.com",
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


def active_test_paths() -> list[Path]:
    return sorted((AGENT_ROOT / "tests").glob("web_design_*.json"))


def generated_upload_paths() -> list[Path]:
    if not GENERATED_UPLOAD_ROOT.is_dir():
        return []
    return sorted(
        path
        for path in GENERATED_UPLOAD_ROOT.glob("*.json")
        if path.name
        in {
            "live_agent_patch_plan.json",
            "live_agent_patch_payload.json",
            "live_agent_patch_requests.json",
            "live_agent_post_patch_snapshot.json",
        }
    )


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def assert_prompt() -> None:
    text = read_text(PROMPT)
    assert_condition(word_count(text) <= 1650, f"Prompt is no longer compact: {word_count(text)} words")
    assert_markers("system prompt", text, PROMPT_MARKERS)


def assert_kb_rules() -> None:
    offer = read_text(ATLAS_KB_ROOT / "atlas_offer_facts.md")
    close = read_text(ATLAS_KB_ROOT / "atlas_close_and_followup_playbook.md")
    objection = read_text(ATLAS_KB_ROOT / "atlas_objection_playbook.md")
    output = read_text(ATLAS_KB_ROOT / "atlas_output_quality_rules.md")

    assert_markers("guarantee lock", objection, GUARANTEE_LOCK_MARKERS)
    assert_markers("delivery timing", offer + "\n" + close, DELIVERY_MARKERS)
    assert_markers("email confirmation", close + "\n" + read_text(PROMPT), EMAIL_MARKERS[:-1])
    assert_markers("expanded weak phrase ban", output, WEAK_PHRASES)
    assert_condition("test failure" in output and "bracketed labels of any kind" in output, "Output rules missing bracket tag test failure")
    assert_condition("I'm not hanging up" in output and "I'll stop here" in output and "Do not use" in output, "Output rules missing unnatural terminal-close ban")
    assert_condition("Do not repeat goodbye more than once" in output, "Output rules missing goodbye-loop ban")


def assert_analysis() -> None:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "Analysis criteria missing")
    ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    setup = read_text(ANALYSIS_SETUP)
    combined = json.dumps(config, ensure_ascii=False) + "\n" + setup
    for criterion_id in ANALYSIS_IDS:
        assert_condition(criterion_id in ids, f"Analysis config missing criterion: {criterion_id}")
        assert_condition(f"`{criterion_id}`" in setup, f"Analysis setup missing criterion: {criterion_id}")
    assert_markers("analysis email confirmation", combined, ANALYSIS_EMAIL_MARKERS)
    assert_markers("analysis weak phrase expansion", combined, WEAK_PHRASES)
    assert_condition("Hard fail" in combined and "guarantee-only first turn" in combined, "Analysis must hard-fail first-turn guarantee miss")


def assert_tests() -> None:
    payload = read_json(RUNTIME_TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "031 test package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 5, "031 runtime tests must contain five simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    for test_id in TEST_IDS:
        assert_condition(test_id in ids, f"Missing runtime elite test: {test_id}")
    combined = "\n".join(read_text(path) for path in active_test_paths())
    assert_markers("runtime elite test markers", combined, TEST_MARKERS)
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
    for name in sorted(set(FOCUSED_KB_FILES)):
        assert_condition((ATLAS_KB_ROOT / name).is_file(), f"Missing focused KB file: {name}")
    for old_doc in (
        "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
    ):
        assert_condition(old_doc not in docs, f"Old monolithic Atlas doc is recommended: {old_doc}")
        assert_condition(old_doc in blocked, f"Old monolithic Atlas doc is not blocked: {old_doc}")

    checklist = "Check ElevenLabs LLM Override / voice prompt / style fields. They must not include bracketed tags such as "
    checklist += "[" + "happy" + "], [" + "calm" + "], or [" + "slow" + "]."
    assert_condition(checklist in "\n".join(manifest.get("operator_notes", [])), "Manifest missing LLM Override tag-leak checklist item")


def assert_no_bracketed_labels(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if BANNED_BRACKET_LABEL.search(line):
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
    assert_condition(not failures, "Bracketed buyer-facing/internal labels found:\n" + "\n".join(failures[:30]))


def assert_delivery_timing(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        lines = read_text(path).splitlines()
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.casefold()
            context = "\n".join(lines[max(0, line_number - 6) : line_number]).casefold()
            if "talk soon" in line:
                continue
            if any(phrase in line for phrase in RISKY_TIMING) and not any(marker in context for marker in TIMING_SAFE_CONTEXT):
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {raw_line.strip()}")
    assert_condition(not failures, "Unsafe delivery timing found:\n" + "\n".join(failures[:30]))


def main() -> None:
    focused_paths = [ATLAS_KB_ROOT / name for name in sorted(set(FOCUSED_KB_FILES))]
    buyer_facing_or_eval_paths = [
        PROMPT,
        ANALYSIS_CONFIG,
        ANALYSIS_SETUP,
        *focused_paths,
        *active_test_paths(),
        *generated_upload_paths(),
    ]

    assert_prompt()
    assert_kb_rules()
    assert_analysis()
    assert_tests()
    assert_manifest()
    assert_no_bracketed_labels(buyer_facing_or_eval_paths)
    assert_delivery_timing([PROMPT, ANALYSIS_CONFIG, ANALYSIS_SETUP, *focused_paths, *active_test_paths()])

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read_text(PROMPT)),
                "guarantee_lock_first_turn": True,
                "delivery_timing": "by the end of the day",
                "email_reply_path": True,
                "bracketed_labels_present": False,
                "runtime_test_count": 5,
                "focused_kb_architecture": True,
                "git_diff_check": "pass",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
