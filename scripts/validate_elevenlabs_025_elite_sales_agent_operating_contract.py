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
FIRST_MESSAGE = AGENT_ROOT / "prompts" / "web_design_first_message.txt"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"
LAYERED_MANIFEST = AGENT_ROOT / "manifests" / "web_design_sales_spine_compression.package.json"
MIKES_SIM_TESTS = AGENT_ROOT / "tests" / "web_design_mikes_kitchen_simulation_tests.json"
CROSS_VERTICAL_TESTS = AGENT_ROOT / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
PACKAGE_ROOT = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-025-elite-sales-agent-operating-contract"

FULL_CORE_UPLOAD_PATH = "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md"


TURN_POLICY_MARKERS = (
    "## Turn Decision Policy",
    "For every user turn, silently classify",
    "role_state",
    "owner",
    "manager",
    "gatekeeper",
    "unknown",
    "buyer_state",
    "skeptical",
    "busy",
    "curious",
    "objecting",
    "agreeing",
    "ready_for_mockup",
    "gave_email",
    "confirming_email",
    "disqualified",
    "stop_request",
    "turn_type",
    "question",
    "objection",
    "agreement",
    "send_request",
    "contact_detail",
    "callback_detail",
    "refusal",
    "next_action",
    "answer",
    "ask name",
    "ask one discovery question",
    "give value mechanism",
    "ask for email",
    "confirm email",
    "close",
    "stop",
    "Do not expose these labels to the buyer.",
    "Then speak one concise natural response.",
)

ARCHITECTURE_MARKERS = (
    "Campaign Profile owns exact facts and forbidden claims.",
    "Campaign Overlay owns Atlas-specific sales tactics.",
    "Universal category files stay generic.",
    "No campaign facts should live in universal category files.",
    "Do not reattach the giant universal_sales_core.md as active KB.",
    "Do not rely on hidden assumptions that belong in dynamic variables or campaign facts.",
)

SOFT_AND_COMMITMENT_MARKERS = (
    "Soft agreement",
    "That makes sense.",
    "I get it.",
    "That's interesting.",
    "Fair enough.",
    "Want me to send the mockup so you can judge it?",
    "Do not ask for email after soft agreement alone unless the buyer also indicates they want to see the mockup.",
    "Commitment / send signal",
    "How do I see it?",
    "Send it over.",
    "I'll take a look.",
    "Go ahead.",
    "Can I see the mockup?",
    "Where do I see it?",
    "buyer gives email",
    "Sure - what's the best email for it?",
)

EMAIL_CLOSE_MARKERS = (
    "Natural two-step email close",
    "Step 1 - after a clear email: confirm the exact normalized email only.",
    "Step 2 - after the buyer confirms the email: close naturally.",
    "Do not pitch again after email.",
    "Do not ask a new discovery question after email.",
    "Yeah, you can reply to that email.",
    "Got it - northsideautorepair@gmail.com. Is that right?",
    "Perfect, I've got maya@lunahair.com. Is that the right email for the mockup?",
    "Got it, info@brightlanddental.com - that's the best place to send it?",
    "Perfect, I'll send it to mike@example.com after this call. Talk soon.",
    "Perfect. I'll send it there after this call. Talk soon.",
    "Great, I'll send it over. Have a good one.",
    "Perfect, I'll send it there. Speak soon.",
)

GATEKEEPER_MARKERS = (
    "## Gatekeeper State Machine",
    "do not pitch the full value proposition",
    "ask when to reach the owner or ask whether they can pass a short note",
    "Sure. Just let them know Emma from Atlas Web Studio called about a free homepage mockup for {{business_name}}.",
    "Perfect, I'll call back after {{callback_window}} and ask for the owner. Thanks for passing that along.",
    "For an after 2 window, this becomes: \"Perfect, I'll call back after 2 and ask for the owner. Thanks for passing that along.\"",
    "Thanks. Have a good one.",
    "No extra pitch after callback window is confirmed.",
)

OWNER_NAME_MARKERS = (
    "If {{contact_name_if_known}} is empty and the person confirms they are the owner, manager, or decision-maker",
    "what this is about first, answer briefly first",
    "Got it - what's your name?",
    "Nice to meet you, {{contact_name}}. I'll keep it quick.",
    "Do not say \"Thanks for confirming.\"",
)

VALUE_ORDER_MARKERS = (
    "confident commercial answer",
    "buyer-specific mechanism",
    "status quo consequence without fear tactics",
    "caveat only if needed",
    "mockup as proof step",
    "small next step",
    "Do not open with \"Not as a guarantee\" unless the buyer explicitly asks for a guarantee.",
)

VALUE_EXAMPLES = (
    "Instagram is where people notice you. The website is where people who don't follow you yet decide whether to book.",
    "It can show services, starting prices if you want them shown, policies, FAQs, reviews, and booking rules before they DM you.",
    "It can also cut down repetitive DMs: how much, where are you, do you do color, what are your policies, how do I book?",
    "Maps may get the click. The site helps someone in a stressful moment trust you fast: emergency services, service area, reviews, and tap-to-call.",
    "Maps gets you discovered. The site helps someone decide you're the shop to call. It can show diagnostics, repairs, hours, location, reviews, and tap-to-call before they gamble on a random listing.",
    "Google Maps helps them find you. The website helps them choose: menu, hours, photos, location, reviews, and reservation or order options.",
    "The site should help people who are already looking understand your services, location, hours, and appointment options. No patient-growth claims - just a cleaner way for someone to decide whether to contact the office.",
    "The site can work as a quote filter: service area, one-time versus recurring, move-in/move-out, what's included, and how to request a quote.",
)

SEO_AND_COST_MARKERS = (
    "That's the goal, yes - not as a page-one promise. A dedicated site gives Google a proper page to read: your services, location, service area, photos, reviews, and booking or call info. Instagram can show up too, but it's not built around local search the same way a website can be.",
    "We can build basic local search foundations into the site: service sections, search-friendly headings, location wording, service-area wording, mobile structure, and clear call/book/quote actions.",
    "Basic local search setup can be part of how the site is built. Ongoing SEO is a separate conversation if you want to push that later.",
    "Low end is usually a simple site: core pages, standard layout, existing photos/copy, contact form, click-to-call, hours, location, reviews, and basic local search setup.",
    "Higher end is when you need custom copy, more pages, service-area pages, booking or quote workflows, integrations, ecommerce, content migration, advanced SEO/content work, or more custom design.",
    "From what you described, you're closer to the low end.",
    "dental: service pages, provider bios, patient forms, booking/patient-system integrations, accessibility/privacy-sensitive setup",
    "salon: service menu, prices/policies, booking path, gallery, reviews, local search setup",
    "plumber/electrician/HVAC: service-area pages, emergency pages, quote/call flow, tracking, local search setup",
    "restaurant: menu/reservation/order flow, photos, hours, location, online ordering integration if needed",
    "mechanic: service pages, diagnostics/repair categories, reviews, hours, click-to-call, quote request",
)

CLEARER_PAGE_MARKERS = (
    "clearer homepage",
    "clearer page",
    "clearer path",
    "supporting language only",
    "tied to a concrete business action",
    "If the phrase appears without a concrete action, rewrite it.",
    "The mockup would show a clearer page where people can check services, prices, policies, reviews, and booking before they DM you.",
)

NATURALNESS_MARKERS = (
    "That's the practical difference.",
    "Want me to send it over?",
    "Each answer should usually be 1 to 3 sentences.",
    "one concrete point",
    "one natural next step",
    "no more than one question",
)

DISQUALIFICATION_MARKERS = (
    "If Instagram already keeps your calendar full and you don't want more bookings, I wouldn't push a website.",
    "If your current site already gets the right quote requests and you're happy with it, there may not be a problem to solve.",
    "If you only want guaranteed SEO rankings or pay-per-lead performance, we're probably not the right fit.",
)

TEST_IDS = (
    "sim_025_soft_agreement_does_not_trigger_email_capture",
    "sim_025_accepted_mockup_triggers_email_capture",
    "sim_025_email_two_step_confirmation_close",
    "sim_025_gatekeeper_callback_clean_close",
    "sim_025_seo_confident_non_guaranteed",
    "sim_025_cost_drivers_real_project_complexity",
    "sim_025_salon_instagram_booking_filter_difference",
    "sim_025_clearer_homepage_main_value_fails",
    "sim_025_disqualify_guaranteed_seo_or_pay_per_lead",
)

TEST_CRITERIA_MARKERS = (
    "soft agreement does not immediately trigger email capture",
    "accepted mockup triggers email capture",
    "buyer gives email -> agent confirms normalized email -> buyer confirms -> agent closes",
    "gatekeeper pass-along plus callback closes cleanly",
    "SEO answer is confident but non-guaranteed",
    "cost drivers explain real project complexity",
    "salon Instagram objection gets a real difference, not generic one-place language",
    "repeated clearer homepage as main value fails",
    "disqualification when buyer only wants guaranteed SEO or pay-per-lead",
)

FORBIDDEN_BUYER_PHRASES = (
    "I understand your concern",
    "Thank you for confirming",
    "customer action path",
    "local visibility support",
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


def assert_first_message() -> None:
    first_message = read_text(FIRST_MESSAGE).strip()
    assert_condition(len(first_message) <= 220, "First message should stay short enough for spoken opener")
    assert_condition("Emma from Atlas Web Studio" in first_message, "First message must identify caller")
    assert_condition("owner" in first_message.lower(), "First message must include right-person check")
    assert_condition("{{business_name}}" in first_message and "{{business_type}}" in first_message, "First message must use dynamic variables")


def assert_active_kb_manifest() -> None:
    manifest = read_json(LAYERED_MANIFEST)
    active_docs = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs")
    assert_condition(isinstance(active_docs, list), "Manifest missing active recommended upload docs")
    assert_condition(FULL_CORE_UPLOAD_PATH not in active_docs, "Active KB recommendation must not reattach universal_sales_core.md")
    assert_condition(
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md" in active_docs,
        "Active KB recommendation missing Atlas overlay",
    )
    assert_condition(
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md" in active_docs,
        "Active KB recommendation missing Atlas profile",
    )


def assert_no_campaign_facts_in_universal_categories() -> None:
    universal_dir = KB_ROOT / "universal_sales_categories"
    assert_condition(universal_dir.is_dir(), "Missing universal category directory")
    campaign_terms = (
        "Atlas Web Studio",
        "Mike's Kitchen",
        "free homepage mockup",
        "mike@example.com",
        "northsideautorepair@gmail.com",
    )
    for path in universal_dir.glob("*.md"):
        text = read_text(path)
        for term in campaign_terms:
            assert_condition(term not in text, f"Campaign-specific term leaked into universal category {path.name}: {term}")


def assert_no_unbounded_outcome_claims(label: str, text: str) -> None:
    risky_patterns = (
        re.compile(r"\bguarantee[sd]? (page[- ]one|seo|ranking|rankings|traffic|customers|calls|bookings|patients|jobs|revenue|roi)\b", re.I),
        re.compile(r"\bwill (rank|get|bring|generate|create|increase) (you )?(more )?(traffic|customers|calls|bookings|patients|jobs|revenue)\b", re.I),
        re.compile(r"\bpage[- ]one promise\b", re.I),
        re.compile(r"\bnumerical SEO lift\b", re.I),
    )
    safe_context = (
        "no ",
        "not ",
        "do not",
        "never",
        "forbidden",
        "without promising",
        "boundary",
        "non-guaranteed",
        "not as a page-one promise",
        "not as a page-one guarantee",
        "we're probably not the right fit",
        "we're not the right fit",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(raw_line) for pattern in risky_patterns):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"{label} line {line_number} contains unbounded outcome claim: {raw_line}",
            )


def assert_clearer_page_guarded(text: str) -> None:
    phrases = ("clearer homepage", "clearer page", "clearer path")
    guard_terms = (
        "supporting",
        "not the main",
        "never as the main",
        "concrete business action",
        "can check",
        "services",
        "prices",
        "policies",
        "reviews",
        "booking",
        "tap-to-call",
        "quote",
        "call",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(phrase in line for phrase in phrases):
            assert_condition(
                any(term in line for term in guard_terms),
                f"Clearer-page phrase lacks supporting/action guard on line {line_number}: {raw_line}",
            )


def assert_forbidden_buyer_phrases(text: str) -> None:
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if "do not" in line or "avoid" in line or "forbidden" in line or "buyer-facing words to avoid" in line:
            continue
        for phrase in FORBIDDEN_BUYER_PHRASES:
            assert_condition(
                phrase.lower() not in line,
                f"Forbidden buyer-facing phrase appears outside avoid/forbid context on line {line_number}: {phrase}",
            )
        if "conversion leakage" in line:
            assert_condition(
                "internal" in line or "avoid" in line or "do not" in line,
                f"conversion leakage appears outside internal/avoid context on line {line_number}: {raw_line}",
            )


def assert_tests() -> None:
    tests_text = "\n".join((read_text(MIKES_SIM_TESTS), read_text(CROSS_VERTICAL_TESTS)))
    assert_contains("025 simulation test ids", tests_text, TEST_IDS)
    assert_contains("025 simulation criteria", tests_text, TEST_CRITERIA_MARKERS)
    for path in (MIKES_SIM_TESTS, CROSS_VERTICAL_TESTS):
        payload = read_json(path)
        tests = payload.get("tests")
        assert_condition(isinstance(tests, list), f"{path.relative_to(ROOT)} missing tests array")
        for test in tests:
            if isinstance(test, dict) and str(test.get("test_id", "")).startswith("sim_025_"):
                max_turns = test.get("simulation_max_turns")
                assert_condition(isinstance(max_turns, int) and max_turns >= 8, f"{test.get('test_id')} needs enough turns")


def assert_package_artifacts() -> None:
    required = (
        PACKAGE_ROOT / "live_agent_patch_plan.json",
        PACKAGE_ROOT / "live_agent_patch_payload.json",
        PACKAGE_ROOT / "live_agent_patch_requests.json",
        PACKAGE_ROOT / "live_agent_post_patch_snapshot.json",
    )
    for path in required:
        assert_condition(path.is_file(), f"Missing package artifact: {path.relative_to(ROOT)}")
    plan = read_json(PACKAGE_ROOT / "live_agent_patch_plan.json")
    assert_condition(plan.get("package_id") == "ELEVENLABS-025-elite-sales-agent-operating-contract", "025 plan has wrong package_id")
    assert_condition(plan.get("live_provider_calls_made") is False, "025 package must not claim live provider calls")
    scope = " ".join(plan.get("scope", []))
    assert_condition("turn-level decision policy" in scope, "025 plan scope missing turn-level decision policy")


def main() -> None:
    assert_first_message()

    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    combined = "\n".join((prompt_text, overlay_text, profile_text))

    assert_contains("turn decision policy", prompt_text, TURN_POLICY_MARKERS)
    assert_contains("architecture boundaries", combined, ARCHITECTURE_MARKERS)
    assert_contains("soft agreement and commitment split", combined, SOFT_AND_COMMITMENT_MARKERS)
    assert_contains("email close state machine", combined, EMAIL_CLOSE_MARKERS)
    assert_contains("gatekeeper state machine", combined, GATEKEEPER_MARKERS)
    assert_contains("owner name capture", combined, OWNER_NAME_MARKERS)
    assert_contains("value answer order", combined, VALUE_ORDER_MARKERS)
    assert_contains("vertical value examples", combined, VALUE_EXAMPLES)
    assert_contains("SEO and cost expertise", combined, SEO_AND_COST_MARKERS)
    assert_contains("clearer page supporting rule", combined, CLEARER_PAGE_MARKERS)
    assert_contains("naturalness policy", prompt_text, NATURALNESS_MARKERS)
    assert_contains("disqualification", combined, DISQUALIFICATION_MARKERS)
    assert_forbidden_buyer_phrases(combined)
    assert_clearer_page_guarded(combined)
    assert_no_unbounded_outcome_claims("025 active package", combined)
    assert_active_kb_manifest()
    assert_no_campaign_facts_in_universal_categories()
    assert_tests()
    assert_package_artifacts()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-025-elite-sales-agent-operating-contract",
                "turn_decision_policy": True,
                "soft_agreement_vs_commitment": True,
                "email_close_state_machine": True,
                "gatekeeper_state_machine": True,
                "value_seo_cost_logic": True,
                "simulation_tests_updated": True,
                "full_universal_core_recommended_for_active_upload": False,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
