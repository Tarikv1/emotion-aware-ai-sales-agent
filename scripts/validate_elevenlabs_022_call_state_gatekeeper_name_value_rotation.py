#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"


GATEKEEPER_MARKERS = (
    "Just let them know Emma from Atlas Web Studio called about a free homepage mockup for {{business_name}}.",
    "Perfect, I'll call back after {{callback_window}} and ask for the owner. Thanks for passing that along.",
    "When is usually a better time to reach the owner?",
    "Perfect, I'll call back after 2 and ask for the owner. Thanks for passing that along.",
    "Do not add extra sales pitch details to the gatekeeper note unless asked.",
)

OWNER_NAME_MARKERS = (
    "If {{contact_name_if_known}} is empty and the person confirms they are the owner, manager, or decision-maker, ask their name before pitching.",
    "Got it - what's your name?",
    "Nice to meet you, {{contact_name}}. I'll keep it quick.",
    "If the buyer asks what this is about first, answer briefly first. Ask for the name later only if the call continues.",
)

ACCEPTED_MOCKUP_MARKERS = (
    "How do I see the mockup?",
    "Can I see it?",
    "Send it over.",
    "How do I get it?",
    "I'll take a look.",
    "Show me the mockup.",
    "Where do I see it?",
    "Sure - what's the best email for it?",
    "Absolutely. What's the best email for the mockup?",
    "Do not re-explain the mockup value after this signal unless the buyer asks another objection.",
)

EMAIL_CLOSE_MARKERS = (
    "Perfect, I'll send it to mike@example.com after this call. Talk soon.",
    "Yeah, you can reply to that email.",
    "Do not ask another discovery question after email is provided unless the email is unclear or the buyer asks a new question.",
)

VALUE_ROTATION_MARKERS = (
    "First answer: acknowledge the current channel is useful, then add one concrete missing function.",
    "Second challenge: use a different mechanism.",
    "Third challenge: answer with the most practical operational benefit or disqualify.",
    "Instagram is where people notice you. The website is where people who don't follow you yet decide whether to book.",
    "It can show services, starting prices if you want them shown, policies, FAQs, reviews, and booking rules before they DM you.",
    "It can also cut down repetitive DMs: how much, where are you, do you do color, what are your policies, how do I book?",
    "Google Maps helps people find you. The website helps them decide: services, proof, hours, location, FAQs, and what to do next.",
    "Maps may get the click. The site helps someone in a stressful moment trust you fast: emergency services, service area, reviews, and tap-to-call.",
    "The site can work as a quote filter: service area, one-time versus recurring, move-in/move-out, what's included, and how to request a quote.",
)

SEO_MARKERS = (
    "That's the goal, yes - not as a page-one guarantee, but a real website gives Google a proper page to read: your services, location, service area, photos, reviews, and booking info.",
    "Basic local SEO setup can be part of the website build. Ongoing SEO is separate.",
)

FORBIDDEN_SEO_PATTERNS = (
    re.compile(r"\bguaranteed? (ranking|traffic|customers|calls)\b"),
    re.compile(r"\bwill (rank|get|bring|generate) (you )?(more )?(traffic|customers|calls)\b"),
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_text(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def assert_contains(label: str, text: str, markers: tuple[str, ...]) -> None:
    for marker in markers:
        assert_condition(marker in text, f"{label} missing marker: {marker}")


def assert_absent(label: str, text: str, markers: tuple[str, ...]) -> None:
    lower = text.lower()
    for marker in markers:
        assert_condition(marker.lower() not in lower, f"{label} contains disallowed buyer-facing phrase: {marker}")


def assert_no_unbounded_seo_claims(label: str, text: str) -> None:
    safe_context = ("not ", "no ", "do not", "never", "forbidden", "without promising", "boundary")
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(line) for pattern in FORBIDDEN_SEO_PATTERNS):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"{label} line {line_number} contains unbounded SEO/customer claim: {raw_line}",
            )


def assert_no_forbidden_positive_phrases(label: str, text: str) -> None:
    forbidden = ("thanks for confirming", "organized information")
    safe_context = ("do not", "avoid", "forbidden", "buyer-facing words to avoid")
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if not any(phrase in line for phrase in forbidden):
            continue
        assert_condition(
            any(marker in line for marker in safe_context),
            f"{label} line {line_number} contains disallowed buyer-facing phrase: {raw_line}",
        )


def main() -> None:
    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    combined = "\n".join((prompt_text, overlay_text, profile_text))

    assert_contains("gatekeeper pass-along note", combined, GATEKEEPER_MARKERS)
    assert_contains("owner name capture", combined, OWNER_NAME_MARKERS)
    assert_contains("accepted mockup contact capture", combined, ACCEPTED_MOCKUP_MARKERS)
    assert_contains("terminal email close", combined, EMAIL_CLOSE_MARKERS)
    assert_contains("value angle rotation", combined, VALUE_ROTATION_MARKERS)
    assert_contains("SEO local search repair", combined, SEO_MARKERS)
    assert_no_forbidden_positive_phrases("buyer-facing package", combined)
    for line_number, raw_line in enumerate(combined.splitlines(), start=1):
        line = raw_line.lower()
        if "clearer online presence" in line:
            assert_condition(
                "do not use" in line or "forbidden" in line,
                f"buyer-facing package line {line_number} contains positive clearer-online-presence wording: {raw_line}",
            )
    assert_no_unbounded_seo_claims("ELEVENLABS-022 package", combined)

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-022-call-state-gatekeeper-name-value-rotation",
                "gatekeeper_pass_along_note": True,
                "owner_name_capture": True,
                "accepted_mockup_contact_capture": True,
                "terminal_email_close": True,
                "value_angle_rotation": True,
                "local_search_safe_wording": True,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
