#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"
VALUE_PRICING_TESTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_mikes_kitchen_value_pricing_tests.json"
MIKES_SIM_TESTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_mikes_kitchen_simulation_tests.json"
CROSS_VERTICAL_TESTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_spine_compression.package.json"
)

FULL_CORE_UPLOAD_PATH = "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md"


LOW_END_COST_MARKERS = (
    "homepage or small brochure site",
    "few pages",
    "standard layout",
    "existing logo, photos, and copy",
    "simple contact form",
    "click-to-call",
    "hours, location, and reviews",
    "basic local search setup",
    "no custom integrations",
)

HIGH_END_COST_MARKERS = (
    "custom design system",
    "more pages",
    "service-area pages",
    "custom copywriting",
    "SEO landing pages",
    "booking or quote workflows",
    "CRM, calendar, email, payment, ordering, or reservation integrations",
    "ecommerce",
    "memberships or client portals",
    "multi-location structure",
    "content migration",
    "custom photography or video",
    "accessibility, performance, security, or privacy-sensitive setup",
    "analytics or tracking setup",
    "ongoing SEO or content strategy",
)

COST_ANSWER = (
    "Closer to the low end is usually a simple site: homepage, a few service sections, reviews, contact form, "
    "click-to-call, hours, location, and basic local search setup. Closer to the high end is when it needs custom "
    "design, more pages, custom copy, service-area pages, booking or quote workflows, integrations, content "
    "migration, advanced SEO work, or more technical setup. If you just need basic info and a way for people to "
    "call, that sounds closer to the low end."
)

DENTAL_COST_ANSWER = (
    "For a dental office, low end is services, location, hours, appointment request, and basic trust elements. "
    "Higher end is multiple service pages, provider bios, patient forms, booking or patient-system integrations, "
    "accessibility/privacy-sensitive setup, and more custom design."
)

LOCAL_SEO_ANSWER = (
    "That's the goal, yes - not as a page-one promise. A dedicated site gives Google a proper page to read: "
    "your services, location, service area, photos, reviews, and booking or call info. Instagram can show up too, "
    "but it's not built around local search the same way a website can be."
)

LOCAL_SEO_MECHANISMS = (
    "search-friendly headings",
    "service sections",
    "service-area wording",
    "location information",
    "local business schema if appropriate",
    "mobile-friendly structure",
    "fast page basics",
    "links from Google Business Profile and social profiles",
    "clear call, book, or quote actions",
)

SEO_FORBIDDEN_MARKERS = (
    "guaranteed ranking",
    "guaranteed traffic",
    "guaranteed customers",
    "guaranteed calls",
    "guaranteed page-one placement",
    "numerical SEO lift claims",
)

WEAK_PHRASE_RULE_MARKERS = (
    "\"clearer homepage,\" \"clearer page,\" and \"clearer path\" may be used once per conversation as supporting language, but never as the main value argument.",
    "The main value must be one of these concrete mechanisms",
    "Instagram is where people notice you. The website is where people who don't follow you yet decide whether to book.",
    "Google Maps helps them find you. The website helps them choose.",
    "Maps may get the click. The site helps them trust and call faster.",
    "The site lets people check services, hours, reviews, and call before they gamble on a shop.",
    "The site can work as a quote filter",
)

TERMINAL_EMAIL_MARKERS = (
    "Natural two-step email close",
    "Step 1 - after a clear email: confirm the exact normalized email only.",
    "Step 2 - after the buyer confirms the email: close naturally.",
    "Do not ask another discovery question after email is provided.",
    "Do not re-pitch after email is provided.",
    "No more \"what else should we focus on?\" after email.",
    "Got it - northsideautorepair@gmail.com. Is that right?",
    "Perfect. I'll send it over. Talk soon.",
)

TEST_CRITERIA_MARKERS = (
    "buyer provides email; agent confirms normalized email; buyer confirms; agent closes",
    "do not fail if the simulated conversation ends immediately after the buyer provides the email and the agent never receives another turn",
    "do not fail if the buyer gave their name earlier in the call",
    "fail if the agent receives a turn after email and does not confirm the normalized email",
    "fail if the agent continues discovery after email",
    "fail if the agent re-pitches after email",
    "fail if the agent ignores buyer confirmation and keeps talking",
    "fail if the agent never closes after email confirmation",
    "cost-driver tests expect real scope drivers, not gallery or testimonials alone",
    "SEO answers should be sales-forward but non-guaranteed",
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


def assert_no_unbounded_seo_or_outcome_claims(label: str, text: str) -> None:
    risky_patterns = (
        re.compile(r"\bwill (rank|get|bring|generate|create|increase) (you )?(more )?(traffic|customers|calls|bookings|patients|jobs|revenue)\b"),
        re.compile(r"\bguarantee[sd]? (page-one|seo|ranking|rankings|traffic|customers|calls|bookings|patients|jobs|revenue|roi)\b"),
        re.compile(r"\bpage-one guarantee\b"),
        re.compile(r"\bnumerical seo lift\b"),
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
        "non-guarantee",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(line) for pattern in risky_patterns):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"{label} line {line_number} contains an unbounded SEO or outcome claim: {raw_line}",
            )


def assert_package(prompt_text: str, overlay_text: str, profile_text: str) -> None:
    combined = "\n".join((prompt_text, overlay_text, profile_text))
    assert_contains("website cost drivers low end", combined, LOW_END_COST_MARKERS)
    assert_contains("website cost drivers high end", combined, HIGH_END_COST_MARKERS)
    assert_contains("website cost buyer answer", combined, (COST_ANSWER, DENTAL_COST_ANSWER))
    assert_contains(
        "local SEO repair",
        combined,
        (
            LOCAL_SEO_ANSWER,
            "Basic local SEO setup can be part of the website build. Ongoing SEO is separate.",
        ),
    )
    assert_contains("local SEO mechanisms", combined, LOCAL_SEO_MECHANISMS)
    assert_contains("SEO forbidden markers", combined, SEO_FORBIDDEN_MARKERS)
    assert_contains("weak phrase reduction", combined, WEAK_PHRASE_RULE_MARKERS)
    assert_contains("terminal email close", combined, TERMINAL_EMAIL_MARKERS)
    assert_condition(
        "Buyer-facing local search shape: \"We can structure the site so Google has a clearer page" not in combined,
        "Old clearer-page local search main answer is still present",
    )
    for line_number, raw_line in enumerate(combined.splitlines(), start=1):
        line = raw_line.lower()
        if "what else should we focus on" in line:
            assert_condition(
                "no more" in line or "do not" in line,
                f"Package line {line_number} contains positive post-email discovery wording: {raw_line}",
            )
    assert_no_unbounded_seo_or_outcome_claims("ELEVENLABS-022B package", combined)


def assert_tests() -> None:
    value_pricing = read_text(VALUE_PRICING_TESTS)
    mikes_sim = read_text(MIKES_SIM_TESTS)
    cross_vertical = read_text(CROSS_VERTICAL_TESTS)
    test_text = "\n".join((value_pricing, mikes_sim, cross_vertical))
    assert_contains("022B test criteria repair", test_text, TEST_CRITERIA_MARKERS)
    assert_condition(
        "gallery/testimonials alone" not in test_text.lower(),
        "Tests should reject gallery/testimonials alone, not preserve it as acceptable wording",
    )
    assert_condition(
        '"simulation_max_turns": 19' in cross_vertical or '"simulation_max_turns": 20' in cross_vertical,
        "Cross-vertical tests should allow a final agent response after email",
    )


def assert_manifest() -> None:
    manifest = read_json(MANIFEST)
    active_docs = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs")
    assert_condition(isinstance(active_docs, list), "Manifest missing active recommended upload docs")
    assert_condition(FULL_CORE_UPLOAD_PATH not in active_docs, "Manifest must not recommend the full universal core for active upload")


def main() -> None:
    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)

    assert_package(prompt_text, overlay_text, profile_text)
    assert_tests()
    assert_manifest()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-022B-cost-seo-terminal-email-close",
                "website_cost_drivers": True,
                "local_seo_sales_forward_no_guarantees": True,
                "weak_phrase_reduction": True,
                "natural_two_step_email_close": True,
                "test_criteria_repair": True,
                "full_universal_core_recommended_for_active_upload": False,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
