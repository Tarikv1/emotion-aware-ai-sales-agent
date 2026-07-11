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
OFFER_FACTS = ATLAS_KB_ROOT / "atlas_offer_facts.md"
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
HUMAN_TESTS = AGENT_ROOT / "tests" / "web_design_human_phone_naturalness_tests.json"
DYNAMIC_DEFAULTS = AGENT_ROOT / "variables" / "mikes_kitchen_dynamic_variable_defaults.json"
ACTIVE_MANIFEST = AGENT_ROOT / "manifests" / "web_design_sales_spine_compression.package.json"
README = AGENT_ROOT / "README.md"

CHECKPOINT_ID = "ELEVENLABS-034-human-phone-naturalness"

TEST_IDS = (
    "sim_034_freshnest_price_pressure_cost_driver",
    "sim_034_luna_instagram_soft_agreement_no_repeated_cta",
    "sim_034_apex_guarantee_lock_no_reopen",
    "sim_034_known_context_phrasing",
    "sim_034_terminal_close_take_care_only",
    "sim_034_bright_lane_email_plus_free_question",
    "sim_034_stale_script_leakage_opening",
    "sim_034_quote_filtering_range_not_fixed_price",
    "sim_034_premium_one_page_range",
    "sim_034_booking_integration_range",
    "sim_034_crm_payment_integration_range",
    "sim_034_advanced_seo_pages_range",
    "sim_034_custom_portal_scoped_quote",
    "sim_034_mockup_advanced_feature_placeholder",
    "sim_034_specialize_phrase_allowed_when_mechanism_led",
)

ANALYSIS_MARKERS = (
    "AI monologue",
    "residue loop",
    "Price ballpark after repeated ask",
    "end_call",
)

WEAK_HEADLINE_PHRASES = (
    "Great to connect",
    "complimentary",
    "professional homepage",
    "enhance your online presence",
    "visual representation",
    "We specialize",
    "fresh perspective",
    "potential design/layout",
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


def section_text(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    next_heading = text.find("\n## ", start + len(marker))
    return text[start:] if next_heading == -1 else text[start:next_heading]


def assert_tests() -> None:
    payload = read_json(HUMAN_TESTS)
    assert_condition(payload.get("package_id") == CHECKPOINT_ID, "034 test package_id mismatch")
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 15, "034 tests must contain fifteen simulations")
    ids = {str(test.get("test_id")) for test in tests if isinstance(test, dict)}
    for test_id in TEST_IDS:
        assert_condition(test_id in ids, f"Missing 034 test: {test_id}")
    text = read_text(HUMAN_TESTS)
    assert_contains(
        "034 tests",
        text,
        (
            "FreshNest Cleaning",
            "closest relevant complexity range",
            "one or two relevant drivers",
            "Yeah, exactly. I can send it over - best email?",
            "be careful with anyone selling",
            "I've got enough for the first version. Best email?",
            "Take care.",
            "brightlanedental@gmail.com",
            "sim_034_stale_script_leakage_opening",
            "Great to connect",
            "complimentary",
            "professional homepage",
            "enhance your online presence",
            "visual representation",
            "We specialize",
            "fresh perspective",
            "potential design/layout",
            "generic opening/pitch/headline",
            "sim_034_quote_filtering_range_not_fixed_price",
            "sim_034_premium_one_page_range",
            "sim_034_booking_integration_range",
            "sim_034_crm_payment_integration_range",
            "sim_034_advanced_seo_pages_range",
            "sim_034_custom_portal_scoped_quote",
            "sim_034_mockup_advanced_feature_placeholder",
            "sim_034_specialize_phrase_allowed_when_mechanism_led",
            "{{website_light_feature_range}}",
            "{{website_workflow_content_range}}",
            "{{website_integration_heavy_range}}",
            "exactly $3,000",
            "dumps the whole menu",
            "scoped pricing",
            "we don't do filtering",
            "capability first",
            "Are you still there?",
            "Is there anything else I can help you with today?",
            "I'm not saying your current site is broken",
            "not working functionality",
        ),
    )


def assert_prompt_and_kb() -> None:
    prompt = read_text(PROMPT)
    output = read_text(OUTPUT_RULES)
    close = read_text(CLOSE_PLAYBOOK)
    price = read_text(PRICE_KB)
    objection = read_text(OBJECTION_KB)
    offer = read_text(OFFER_FACTS)

    for label, text in (("prompt", prompt), ("output rules", output)):
        assert_condition("Human Phone Call Standard" in text, f"{label} missing Human Phone Call Standard")
        assert_condition("Residue Loop" in text, f"{label} missing Residue Loop")
        assert_condition(
            "Use a short spoken transition when it helps the turn feel natural" in text,
            f"{label} missing transition overcorrection guard",
        )
        assert_condition(
            "Do not force a transition on every turn" in text,
            f"{label} missing no-forced-transition rule",
        )
    assert_condition(
        "Mission: sell the free homepage mockup" not in prompt,
        "prompt still frames mission as selling the free homepage mockup",
    )
    assert_condition(
        "Mission: earn permission for the owner to receive the free homepage mockup" in prompt,
        "prompt missing permission-based mission wording",
    )
    assert_condition("Residue Loop" in close, "close playbook missing Residue Loop")
    assert_condition("first or second price ask" in price, "price KB missing first or second price ask")
    assert_condition("Best email?" in close, "close playbook missing short Best email ask")
    assert_condition(
        "I already have {{business_name}} and the business type" not in close,
        "close playbook still contains old CRM-ish known-context phrase",
    )
    assert_condition("Be careful with anyone selling it that way" in objection, "objection KB missing guarantee warning")
    assert_condition("I'd be careful with anyone selling it that way" in objection, "objection KB missing spoken guarantee warning example")
    assert_contains(
        "offer facts complexity menu",
        offer,
        (
            "Website Complexity Ballpark Menu",
            "{{website_basic_site_range}}",
            "default `$900-$1,500`",
            "{{website_light_feature_range}}",
            "default `$1,800-$3,000`",
            "{{website_workflow_content_range}}",
            "default `$2,800-$4,500`",
            "{{website_integration_heavy_range}}",
            "default `$4,000-$6,500`",
            "{{website_custom_scope_note}}",
            "ballpark ranges, not final quotes",
            "One feature does not automatically determine the price",
            "{{website_starting_price}}` is the starting point",
        ),
    )
    fixed_quote_filtering_sources = "\n".join((offer, price, prompt, read_text(HUMAN_TESTS)))
    assert_condition(
        "{{website_quote_filtering_ballpark}}" not in fixed_quote_filtering_sources,
        "old website_quote_filtering_ballpark still appears in active pricing prompt/KB/tests",
    )
    assert_condition(
        "default value `$3,000`" not in fixed_quote_filtering_sources,
        "old fixed $3,000 quote-filtering default still appears in active pricing prompt/KB/tests",
    )
    assert_condition("Website Complexity Ballpark Menu" in prompt, "prompt missing Website Complexity Ballpark Menu rule")
    assert_condition("Feature-Complexity Ballpark Policy" in price, "price KB missing Feature-Complexity Ballpark Policy")
    combined_policy = "\n".join((prompt, output, price, offer, close, objection))
    assert_contains(
        "contextual weak-phrase policy",
        combined_policy,
        (
            "weak headline phrases, not forbidden words",
            "support after a concrete mechanism",
            "precise mockup-scope explanation",
            "We specialize in creating professional homepages to improve your online presence.",
            "We work with local service businesses on pages that make quote requests, service areas, reviews, and call paths easier to judge.",
            "The mockup is a visual representation, not a working site.",
            "That can improve the online presence, but the mechanism is the booking/filter path.",
        ),
    )
    for marker in WEAK_HEADLINE_PHRASES:
        assert_condition(marker in combined_policy, f"contextual weak-phrase policy missing marker: {marker}")
    assert_contains(
        "price KB offer-facts boundary",
        price,
        (
            "Atlas Offer Facts owns approved pricing facts",
            "Do not create pricing facts outside atlas_offer_facts.md",
            "Give one relevant range only",
            "Do not read the whole pricing menu unless the buyer asks for a breakdown",
            "Do not give a final fixed quote for custom work",
        ),
    )
    assert_contains(
        "custom portal scoped pricing",
        combined_policy,
        (
            "Yes, we can build that.",
            "That needs a proper scope before I give you a real number.",
            "secure login",
            "user accounts",
            "database",
            "permissions",
            "cloud setup",
            "show where the login or portal entry would sit",
            "not working functionality",
            "Do not volunteer the {{website_starting_price}}-{{website_premium_price_anchor}} range",
            "Do not force \"beyond {{website_premium_price_anchor}}\" in every portal/dashboard answer",
        ),
    )
    assert_contains(
        "advanced feature mockup scope",
        combined_policy,
        (
            "The free mockup is visual, not a live website",
            "It can show where that would sit on the homepage, but it would not be working functionality in the free mockup.",
            "It can show where the login or portal entry would sit, but the working portal would be scoped separately.",
            "working login, database, CRM/payment integration, live calendar, portal, dashboard, booking engine, ecommerce",
        ),
    )
    assert_contains(
        "simple vs integrated feature split",
        combined_policy,
        (
            "Do not say \"we don't do filtering.\"",
            "Simple quote filtering is usually around {{website_light_feature_range}}",
            "Live calendar booking can move toward {{website_workflow_content_range}} or {{website_integration_heavy_range}}",
            "Yes, we can build that. The exact setup depends on whether it's a simple form handoff or a real integration.",
            "Fail if Emma jumps into a price range before answering the capability question clearly.",
        ),
    )
    assert_contains(
        "first-call outcome and existing-website guards",
        combined_policy,
        (
            "one low-friction move toward the free mockup",
            "Do not force booking",
            "I can at least send the homepage mockup so you can see the direction.",
            "I'm not saying your current site is broken. The mockup is just a comparison point.",
            "Do not imply the current site is bad without approved evidence.",
            "Are you still there?",
            "Is there anything else I can help you with today?",
        ),
    )
    preferred = section_text(output, "No Robotic Phrases")
    assert_condition(
        "Want me to send it over?" not in preferred,
        "output rules list 'Want me to send it over?' as unrestricted preferred language",
    )
    assert_condition(
        "allowed only once as a renewed send invitation" in output,
        "output rules missing restricted send-invitation language",
    )
    assert_contains(
        "repair phrase cap",
        prompt + "\n" + output,
        (
            "may be used at most once per call",
            "Yeah, let me answer the part I missed.",
            "Right - the useful part is...",
            "Gotcha - here's the concrete version.",
        ),
    )
    approved_sections = "\n".join(
        section_text(output, heading)
        for heading in ("No Robotic Phrases", "Natural Closing Lines")
    )
    for marker in WEAK_HEADLINE_PHRASES:
        assert_condition(
            marker not in approved_sections,
            f"weak headline marker appears in unrestricted approved/preferred output example: {marker}",
        )


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
            "buyer asks price, cost, range, budget, fee, add-on cost, or total twice",
            "max turns because Emma avoided price",
            "fixed feature price",
            "quote filtering is always exactly $3,000",
            "dumps the whole pricing menu",
            "final fixed price for custom work without scope",
            "spoken at/dot form",
            "guarantee-only buyer receives any mockup pitch after lock",
            "I already have {{business_name}} and the business type",
            "You're welcome. Have a great day",
            "mechanically starts nearly every turn with the same transition",
            "jumps into price before answering a capability question clearly",
            "we don't do filtering",
            "forces beyond $5k language when the buyer did not ask about the normal/high-end range",
            "Are you still there?",
            "Is there anything else I can help you with today?",
            "non-terminal information answer",
            "current site is broken",
            "not working functionality",
        ),
    )


def assert_operator_notes() -> None:
    readme = read_text(README)
    assert_contains(
        "dashboard drift operator note",
        readme,
        (
            "Dashboard Drift Check",
            "ElevenLabs system prompt",
            "LLM Override",
            "voice/style fields",
            "stale old KB attachments",
            "old generated upload package",
            "old test folder using stale agent version",
            "Do not upload this note as active KB",
        ),
    )


def assert_dynamic_defaults() -> None:
    defaults = read_json(DYNAMIC_DEFAULTS)
    expected = {
        "website_basic_site_range": "$900-$1,500",
        "website_light_feature_range": "$1,800-$3,000",
        "website_workflow_content_range": "$2,800-$4,500",
        "website_integration_heavy_range": "$4,000-$6,500",
    }
    for key, value in expected.items():
        assert_condition(defaults.get(key) == value, f"dynamic defaults missing {key}: {value}")
    assert_condition(
        "custom portals, dashboards" in str(defaults.get("website_custom_scope_note", "")),
        "dynamic defaults missing website_custom_scope_note",
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
    assert_operator_notes()
    assert_dynamic_defaults()
    assert_manifest_unchanged()
    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "human_phone_call_standard": True,
                "residue_loop_guard": True,
                "analysis_criteria_count": len(read_json(ANALYSIS_CONFIG)["success_evaluation_criteria"]),
                "focused_test_count": 15,
                "stale_script_leakage_guard": True,
                "complexity_band_pricing_guard": True,
                "active_upload_manifest_changed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
