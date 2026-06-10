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
LIVE_FAILURE_TESTS = AGENT_ROOT / "tests" / "web_design_live_transcript_failure_hardening_tests.json"

CHECKPOINT_ID = "ELEVENLABS-030-live-transcript-failure-hardening"

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
    *[
        f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}"
        for name in FOCUSED_KB_FILES
    ],
]

PROMPT_MARKERS = (
    "Never output bracketed labels of any kind.",
    "Hard CTA limits:",
    "Do not ask to send the mockup more than twice unless the buyer gives a new clear send signal.",
    "Do not ask for email during process-risk questions.",
    "Do not ask for email more than once before the buyer clearly accepts.",
    "Do not repeat the CTA after every objection.",
    "If {{business_name}} is known, never ask for the business name.",
    "Vertical action fidelity:",
    "If the buyer says they do not do online booking",
    "Guarantee-only disqualification lock:",
)

DISQUALIFICATION_MARKERS = (
    "## Disqualification Lock",
    "After the lock, Emma may answer one final clarification, then must close.",
    "Do not ask to send the mockup",
    "For guaranteed calls or guaranteed jobs, no - I wouldn't promise that.",
    "That's right - no guarantee. I don't want to waste your time. Have a good one.",
)

CTA_PROCESS_MARKERS = (
    "Do not ask to send the mockup more than twice unless the buyer gives a new clear send signal.",
    "Do not ask for email during process-risk questions.",
    "Do not ask for email more than once before clear acceptance.",
    "If the buyer asks what happens after",
    "After answering process-risk questions, do not immediately repeat",
)

KNOWN_CONTEXT_MARKERS = (
    "## Known-Context Discipline",
    "If {{business_name}} is known, never ask for the business name.",
    "I already have {{business_name}} and the business type.",
    "the next useful missing field is usually the email",
)

VERTICAL_ACTION_MARKERS = (
    "## Vertical Action Fidelity",
    "HVAC, plumbing, and electrical: call, quote request, emergency service, service area, tap-to-call.",
    "Auto repair: call, estimate request, diagnostics or repair category, hours, location.",
    "If the buyer says they do not do online booking",
)

EXPANDED_WEAK_PHRASES = (
    "clearer online presence",
    "clearer online presentation",
    "online presence",
    "potential improvements",
    "professional website",
    "professional website could help",
    "visual representation",
    "organized information",
    "one place",
    "central hub",
    "online brochure",
    "help people understand your services",
    "help customers find your services",
    "easier to take the next step",
    "better engagement",
    "more inquiries",
)

ANALYSIS_IDS = (
    "no_bracketed_internal_labels",
    "no_cta_fatigue",
    "process_risk_before_email_capture",
    "no_follow_up_leakage",
    "concrete_mechanism_headline_value",
    "guarantee_escalation_correct",
    "disqualification_lock_respected",
    "vertical_action_fidelity",
    "known_context_not_rediscovered",
    "normalized_email_extracted",
)

LIVE_TEST_IDS = (
    "sim_030_apex_plumbing_guarantee_lock",
    "sim_030_summit_hvac_process_risk_known_context",
    "sim_030_northside_auto_angry_busy_hygiene",
    "sim_030_luna_instagram_repeated_objection_rotation",
    "sim_030_bright_lane_dental_safe_email",
)

LIVE_TEST_MARKERS = (
    "disqualification lock",
    "Hard fail if max turns are reached",
    "CTA is repeated more than twice",
    "does not ask for the business name",
    "Great to connect",
    "value angle rotates",
    "patient growth",
    "service@northsideautorepair.com",
    "info@summithvac.com",
    "lunahairstudio@email.com",
    "info@brightlanedental.com",
)

BANNED_BRACKET_LABEL = re.compile(r"\[[A-Za-z][A-Za-z0-9 _/-]{0,40}\]")


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
    assert_condition(word_count(text) <= 1450, f"Prompt is no longer compact: {word_count(text)} words")
    assert_markers("system prompt", text, PROMPT_MARKERS)
    for banned in (
        "Approved Buyer-Facing Selling Examples",
        "Website cost drivers:",
        "Vertical cost drivers:",
        "Use these sharper examples as pattern examples",
    ):
        assert_condition(banned not in text, f"Prompt reintroduced large example bank: {banned}")


def assert_kb_rules() -> None:
    objection = read_text(ATLAS_KB_ROOT / "atlas_objection_playbook.md")
    close = read_text(ATLAS_KB_ROOT / "atlas_close_and_followup_playbook.md")
    value = read_text(ATLAS_KB_ROOT / "atlas_value_mechanisms.md")
    output = read_text(ATLAS_KB_ROOT / "atlas_output_quality_rules.md")

    assert_markers("disqualification lock", objection, DISQUALIFICATION_MARKERS)
    assert_markers("CTA/process-risk close playbook", close, CTA_PROCESS_MARKERS)
    assert_markers("known-context playbook", close, KNOWN_CONTEXT_MARKERS)
    assert_markers("vertical action fidelity", value, VERTICAL_ACTION_MARKERS)
    assert_markers("expanded weak phrase ban", output, EXPANDED_WEAK_PHRASES)
    assert_condition("quote request" in output, "Output rules missing quote request as concrete mechanism")
    assert_condition("automatic failure" in output and "bracketed labels of any kind" in output, "Output rules missing bracket-label hard fail")


def assert_analysis() -> None:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "Analysis criteria missing")
    ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    setup = read_text(ANALYSIS_SETUP)
    analysis_text = json.dumps(config, ensure_ascii=False) + "\n" + setup
    for criterion_id in ANALYSIS_IDS:
        assert_condition(criterion_id in ids, f"Analysis config missing criterion: {criterion_id}")
        assert_condition(f"`{criterion_id}`" in setup, f"Analysis setup missing criterion: {criterion_id}")
    assert_condition("Hard fail" in analysis_text, "Analysis must mark bracket labels/CTA/process failures as hard fail")
    assert_markers("analysis weak phrase expansion", analysis_text, EXPANDED_WEAK_PHRASES)
    assert_markers(
        "analysis realistic email normalization",
        analysis_text,
        ("service@northsideautorepair.com", "info@summithvac.com", "lunahairstudio@email.com"),
    )
    assert_condition(
        "keeps selling after the guarantee-only disqualification lock" in analysis_text,
        "Analysis guarantee criterion must fail repitching after lock",
    )


def assert_tests() -> None:
    payload = read_json(LIVE_FAILURE_TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "030 test package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 5, "030 live failure tests must contain five simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    for test_id in LIVE_TEST_IDS:
        assert_condition(test_id in ids, f"Missing live failure test: {test_id}")
    combined = "\n".join(read_text(path) for path in active_test_paths())
    assert_markers("live failure test markers", combined, LIVE_TEST_MARKERS)
    assert_condition("placeholder-looking email" in combined, "Tests missing placeholder email realism guard")
    assert_condition("Any bracketed internal label in buyer-facing agent output is automatic failure." in combined, "Tests missing bracket label hard fail")


def assert_manifest_architecture() -> None:
    manifest = read_json(ACTIVE_MANIFEST)
    docs = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs")
    blocked = manifest.get("active_kb_recommendation", {}).get("not_recommended_for_active_upload_unless_explicitly_needed", [])
    assert_condition(docs == RECOMMENDED_UPLOAD_DOCS, "Active manifest no longer points to the focused KB chunks")
    for name in FOCUSED_KB_FILES:
        assert_condition((ATLAS_KB_ROOT / name).is_file(), f"Missing focused KB file: {name}")
    for old_doc in (
        "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
    ):
        assert_condition(old_doc not in docs, f"Old monolithic doc is recommended for upload: {old_doc}")
        assert_condition(old_doc in blocked, f"Old monolithic doc missing from blocked recommendations: {old_doc}")


def assert_no_bracketed_labels(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            for match in BANNED_BRACKET_LABEL.finditer(line):
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {match.group(0)}")
    assert_condition(not failures, "Bracketed internal labels found:\n" + "\n".join(failures[:30]))


def main() -> None:
    assert_prompt()
    assert_kb_rules()
    assert_analysis()
    assert_tests()
    assert_manifest_architecture()
    assert_no_bracketed_labels(
        [
            PROMPT,
            ANALYSIS_CONFIG,
            ANALYSIS_SETUP,
            *[ATLAS_KB_ROOT / name for name in FOCUSED_KB_FILES],
            *active_test_paths(),
        ]
    )

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read_text(PROMPT)),
                "focused_kb_architecture": True,
                "disqualification_lock": True,
                "cta_process_risk_hardening": True,
                "known_context_discipline": True,
                "vertical_action_fidelity": True,
                "weak_phrase_ban_expanded": True,
                "bracketed_labels_present": False,
                "live_failure_test_count": 5,
                "git_diff_check": "pass",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
