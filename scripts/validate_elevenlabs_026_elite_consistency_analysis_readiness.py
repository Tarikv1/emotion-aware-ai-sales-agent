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
PROMPT = AGENT_ROOT / "prompts" / "web_design_atlas_sales_prompt.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"
VALUE_AND_ROI = KB_ROOT / "universal_sales_categories" / "value_and_roi_framing.md"
MIKES_SIM_TESTS = AGENT_ROOT / "tests" / "web_design_mikes_kitchen_simulation_tests.json"
CROSS_VERTICAL_TESTS = AGENT_ROOT / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_DOC = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
PACKAGE_ROOT = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-026-elite-consistency-cleanup-analysis-readiness"


STATE_PRIORITY_MARKERS = (
    "1. stop / do-not-call",
    "2. gatekeeper / wrong person",
    "3. email provided",
    "4. email confirmation",
    "5. accepted mockup signal",
    "6. soft agreement",
    "7. direct question",
    "8. objection",
    "9. price/cost",
    "10. discovery / qualification",
    "11. close",
)

VALUE_GUIDANCE_MARKERS = (
    "If buyer asks for a guarantee, start with the boundary.",
    "If buyer asks for business impact, start with the commercial mechanism first, then add the caveat precisely.",
    "If buyer asks for measurable ROI, explain the mechanism and state exact results are not guaranteed.",
    "Always tie value to a concrete buyer action.",
)

PROFILE_OWNERSHIP_MARKERS = (
    "Campaign Profile owns:",
    "exact offer",
    "prices",
    "assurance facts",
    "approved demand-capture facts",
    "approved selling mechanisms",
    "vertical mechanisms",
    "cost drivers",
    "SEO/local search allowed and forbidden claims",
    "send/callback capabilities as facts",
    "forbidden claims",
)

PROFILE_FACT_MARKERS = (
    "## Send And Callback Capability Facts",
    "Verbal email spell-outs are valid contact details when the address is clear.",
    "The agent may normalize obvious forms such as `name at domain dot com` into `name@domain.com` and confirm the destination.",
    "Immediate send timing is approved for the free mockup link after a buyer gives a clear email address.",
    "No approved callback phone number is configured in this package. Do not invent one.",
    "The agent may confirm a callback window.",
)

PROFILE_BEHAVIOR_MARKERS = (
    "Soft agreement is not a send commitment",
    "Commitment / send signal",
    "Natural two-step email close",
    "Email confirmation example:",
    "Same-turn email confirmation example:",
    "Terminal close after email confirmation",
    "Gatekeeper pass-along note:",
    "Gatekeeper callback close:",
    "Name capture question:",
    "Accepted mockup signals include:",
    "Accepted mockup contact capture:",
    "Do not re-explain the mockup value after this signal",
)

SOFT_AGREEMENT_MARKERS = (
    "That makes sense.",
    "I get it.",
    "That's interesting.",
    "Fair enough.",
    "Okay, I see what you mean.",
    "Want me to send the mockup so you can judge it?",
)

COMMITMENT_MARKERS = (
    "How do I see it?",
    "Can I see it?",
    "Send it over.",
    "I'll take a look.",
    "Go ahead.",
    "Where do I see it?",
    "buyer gives email",
    "Sure - what's the best email for it?",
)

KEEP_EXAMPLE_MARKERS = (
    "Instagram is where people notice you. The website is where people who don't follow you yet decide whether to book.",
    "It can also cut down repetitive DMs",
    "Maps gets you discovered. The site helps someone decide you're the shop to call.",
    "Maps may get the click. The site helps someone in a stressful moment trust you fast",
    "Google Maps helps them find you. The website helps them choose.",
    "The site can work as a quote filter",
    "not as a page-one promise. A dedicated site gives Google a proper page to read",
    "Low end is usually a simple site",
    "Higher end is when you need custom copy",
)

DEDUPE_REMOVED_MARKERS = (
    "direct version",
    "alternate wording",
    "Instagram is your gallery",
    "Instagram is the gallery",
    "where strangers decide whether to book",
    "closer to ready",
)

ANALYSIS_CRITERIA_IDS = (
    "elite_sales_value_answer",
    "no_caveat_first_unless_guarantee",
    "soft_agreement_not_overclosed",
    "accepted_mockup_email_capture",
    "email_two_step_close",
    "gatekeeper_clean_close",
    "no_weak_clearer_main_value",
    "seo_confident_but_safe",
    "cost_driver_expertise",
    "natural_spoken_quality",
    "stop_request_respected",
    "no_fake_claims",
)

DATA_COLLECTION_FIELDS = (
    "buyer_role",
    "contact_name",
    "email",
    "callback_window",
    "business_name",
    "vertical",
    "buyer_state",
    "objection_type",
    "value_angle_used",
    "accepted_mockup",
    "soft_agreement_only",
    "send_signal",
    "terminal_outcome",
    "failure_reason",
    "next_step",
)

TEST_MARKERS = (
    "That makes sense alone does not trigger email capture.",
    "Okay, I see what you mean is soft agreement, not a send commitment.",
    "Accepted mockup signal triggers email capture.",
    "Email provided triggers normalized email confirmation.",
    "Email confirmation triggers short close.",
    "Business-impact answers do not start with caveat unless buyer asked for guarantee.",
    "Universal value guidance does not conflict with prompt.",
    "Campaign profile does not contain major state-machine behavior blocks.",
    "SEO answer is confident but non-guaranteed.",
    "Cost answer explains real cost drivers.",
    "No guaranteed customer/ranking/revenue claims.",
    "No clearer page/homepage/path as main value argument.",
)

TEST_IDS = (
    "sim_026_soft_agreement_okay_i_see_not_email_capture",
    "sim_026_business_impact_no_caveat_first",
    "sim_026_profile_overlay_state_authority",
    "sim_026_analysis_success_data_collection_ready",
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
    for marker in markers:
        assert_condition(marker in text, f"{label} missing marker: {marker}")


def assert_absent(label: str, text: str, markers: tuple[str, ...]) -> None:
    for marker in markers:
        assert_condition(marker not in text, f"{label} still contains disallowed marker: {marker}")


def assert_ordered(label: str, text: str, markers: tuple[str, ...]) -> None:
    cursor = -1
    for marker in markers:
        index = text.find(marker)
        assert_condition(index > cursor, f"{label} missing or out of order marker: {marker}")
        cursor = index


def section_after(text: str, header: str, stop_header: str = "\n## ") -> str:
    start = text.find(header)
    assert_condition(start >= 0, f"Missing section header: {header}")
    remainder = text[start:]
    stop = remainder.find(stop_header, len(header))
    return remainder if stop < 0 else remainder[:stop]


def assert_package_artifacts() -> None:
    required = (
        PACKAGE_ROOT / "live_agent_patch_plan.json",
        PACKAGE_ROOT / "live_agent_patch_payload.json",
        PACKAGE_ROOT / "live_agent_patch_requests.json",
        PACKAGE_ROOT / "live_agent_post_patch_snapshot.json",
    )
    for path in required:
        assert_condition(path.is_file(), f"Missing 026 package artifact: {path.relative_to(ROOT)}")
    plan = read_json(PACKAGE_ROOT / "live_agent_patch_plan.json")
    assert_condition(plan.get("package_id") == "ELEVENLABS-026-elite-consistency-cleanup-analysis-readiness", "026 plan has wrong package_id")
    assert_condition(plan.get("live_provider_calls_made") is False, "026 package must not claim live provider calls")


def assert_soft_commitment_split(prompt_text: str, overlay_text: str) -> None:
    combined = "\n".join((prompt_text, overlay_text))
    assert_contains("soft agreement signals", combined, SOFT_AGREEMENT_MARKERS)
    assert_contains("commitment/send signals", combined, COMMITMENT_MARKERS)
    for text, label in ((prompt_text, "prompt"), (overlay_text, "overlay")):
        accepted = section_after(text, "Commitment / send signal") if "Commitment / send signal" in text else section_after(text, "Accepted mockup")
        assert_condition("That makes sense" not in accepted, f"{label} accepted mockup section still treats That makes sense as a send signal")
        assert_condition("Okay, I see what you mean" not in accepted, f"{label} accepted mockup section treats Okay, I see what you mean as a send signal")


def assert_profile_ownership(profile_text: str) -> None:
    assert_contains("profile ownership", profile_text, PROFILE_OWNERSHIP_MARKERS)
    assert_contains("profile factual send/callback capabilities", profile_text, PROFILE_FACT_MARKERS)
    assert_absent("profile behavior ownership", profile_text, PROFILE_BEHAVIOR_MARKERS)


def assert_de_duplicated_examples(combined: str) -> None:
    assert_contains("kept strongest examples", combined, KEEP_EXAMPLE_MARKERS)
    assert_absent("duplicate example labels and weak duplicates", combined, DEDUPE_REMOVED_MARKERS)


def assert_analysis_config() -> None:
    config = read_json(ANALYSIS_CONFIG)
    doc_text = read_text(ANALYSIS_DOC)
    criteria = config.get("success_evaluation_criteria")
    fields = config.get("data_collection_fields")
    assert_condition(isinstance(criteria, list), "Analysis config missing success_evaluation_criteria list")
    assert_condition(isinstance(fields, list), "Analysis config missing data_collection_fields list")
    criteria_ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    field_names = {str(item.get("name")) for item in fields if isinstance(item, dict)}
    for criterion_id in ANALYSIS_CRITERIA_IDS:
        assert_condition(criterion_id in criteria_ids, f"Analysis criteria missing id: {criterion_id}")
    for field_name in DATA_COLLECTION_FIELDS:
        assert_condition(field_name in field_names, f"Analysis data collection missing field: {field_name}")
    assert_contains(
        "analysis doc",
        doc_text,
        (
            "Success Evaluation returns success, failure, or unknown with rationale.",
            "Data Collection extracts structured fields such as contact details and business data.",
            "Keep criteria specific and include edge cases.",
        ),
    )


def assert_tests() -> None:
    tests_text = "\n".join((read_text(MIKES_SIM_TESTS), read_text(CROSS_VERTICAL_TESTS)))
    assert_contains("026 test criteria", tests_text, TEST_MARKERS)
    assert_contains("026 test ids", tests_text, TEST_IDS)


def assert_no_unbounded_claims(text: str) -> None:
    risky_patterns = (
        re.compile(r"\bwill (rank|get|bring|generate|create|increase) (you )?(more )?(traffic|customers|calls|bookings|patients|jobs|revenue)\b", re.I),
        re.compile(r"\bguarantee[sd]? (page[- ]one|seo|ranking|rankings|traffic|customers|calls|bookings|patients|jobs|revenue|roi)\b", re.I),
    )
    safe_context = ("no ", "not ", "do not", "never", "forbidden", "without promising", "not as a page-one promise", "we're probably not the right fit")
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(raw_line) for pattern in risky_patterns):
            assert_condition(any(marker in line for marker in safe_context), f"Unbounded claim on line {line_number}: {raw_line}")


def main() -> None:
    assert_package_artifacts()

    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    value_text = read_text(VALUE_AND_ROI)
    combined = "\n".join((prompt_text, overlay_text, profile_text, value_text))

    assert_ordered("state priority", prompt_text, STATE_PRIORITY_MARKERS)
    assert_condition("Do not expose state labels to the buyer." in prompt_text, "Prompt must forbid exposing state labels")
    assert_condition("Start with the boundary when the buyer asks for outcomes." not in value_text, "Universal value guidance still conflicts with prompt")
    assert_contains("universal value guidance", value_text, VALUE_GUIDANCE_MARKERS)
    assert_soft_commitment_split(prompt_text, overlay_text)
    assert_profile_ownership(profile_text)
    assert_de_duplicated_examples("\n".join((prompt_text, overlay_text, profile_text)))
    assert_analysis_config()
    assert_tests()
    assert_no_unbounded_claims(combined)

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-026-elite-consistency-cleanup-analysis-readiness",
                "soft_agreement_commitment_consistent": True,
                "universal_value_guidance_aligned": True,
                "profile_behavior_blocks_removed": True,
                "analysis_config_ready": True,
                "simulation_tests_updated": True,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
