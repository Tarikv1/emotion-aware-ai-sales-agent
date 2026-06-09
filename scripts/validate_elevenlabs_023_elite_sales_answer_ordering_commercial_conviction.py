#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"


ORDER_MARKERS = (
    "Direct commercial answer first",
    "Specific buyer mechanism second",
    "No-guarantee caveat third, only if needed",
    "Mockup proof step fourth",
    "Small next step fifth",
)

BUSINESS_IMPACT_EXAMPLES = (
    "Yes, that's one of the main reasons to have a site. If someone searches 'hair salon Tampa,' Instagram might show up, but a dedicated website gives Google a proper page for your services, location, reviews, policies, and booking. I'm not promising page one, but relying only on Instagram makes new clients find you the hard way. The mockup would show how that could look for your salon.",
    "It can help with the people who are already looking. If they find you on Google, Maps, Instagram, or through a referral, the site can make it easier to trust you and call instead of bouncing to another business. I won't promise a number, but the mockup shows whether that call path is stronger.",
)

CONSEQUENCE_MARKERS = (
    "Right now, some people may be checking you out but not getting enough information to act.",
    "If they have to DM for every basic question, some will just move on.",
    "If they're comparing three options, the business that answers trust, price, location, and booking questions fastest often feels safer to choose.",
    "The site is not magic demand. It's reducing friction for people already considering you.",
)

CHANNEL_EXAMPLES = (
    "Instagram is where people notice you. The website is where strangers decide whether to book. If they don't follow you yet, they're probably searching Google, checking reviews, comparing prices, or trying to find your policy before they DM. A site gives them that in one flow and can reduce the back-and-forth.",
    "Google Maps helps them find you. The site helps them choose. Menu, hours, photos, location, reviews, and reservation or order options are what turn curiosity into action.",
    "Maps gets you discovered. The site helps someone decide you're the shop to call. If they're comparing three mechanics, the site can show diagnostics, repairs, reviews, hours, location, and tap-to-call before they gamble on a random listing.",
    "Maps might get the click. The site helps someone in a stressful moment trust you fast: emergency services, service area, reviews, and tap-to-call.",
    "The site can filter quote requests before you spend time replying: service areas, recurring vs one-time, move-in/move-out, what's included, and how to request a quote.",
)

COST_JUDGMENT_MARKERS = (
    "If you just need basic info and click-to-call, that's low-end. The $5k side is when you want a more complete lead system: custom copy, multiple service pages, service-area pages, booking or quote workflows, integrations, tracking, SEO pages, or custom design. From what you described, you're closer to the low end.",
    "For a dental office, basic services, location, hours, appointment request, and trust elements are closer to the low end. Multiple treatment pages, provider bios, forms, booking or patient-system integrations, accessibility/privacy-sensitive setup, and custom copy/design push it higher.",
)

ACCEPTED_INTEREST_MARKERS = (
    "That makes sense",
    "Go ahead",
    "stop selling and ask for the send path",
    "Sure - what email should I send it to?",
)

DISQUALIFICATION_MARKERS = (
    "If Instagram already keeps your calendar full and you don't want more bookings, I wouldn't push a website.",
    "If your current site already gets the right quote requests and you're happy with it, there may not be a problem to solve.",
    "If you only want guaranteed SEO rankings, we're not the right fit.",
)

NATURAL_SPEECH_MARKERS = (
    "That's fair.",
    "Exactly.",
    "That's the point.",
    "Here's the practical difference.",
    "You're not wrong.",
    "If you already get enough bookings from Instagram, you may not need this.",
)

TERMINAL_EMAIL_MARKERS = (
    "Natural two-step email close",
    "normalize obvious email spell-outs",
    "confirm the email only",
    "Terminal close after email confirmation",
    "Do not re-pitch after email is provided.",
    "Do not over-explain the reply path unless the buyer asks.",
    "Got it - northsideautorepair@gmail.com. Is that right?",
    "Perfect. I'll send it over. Talk soon.",
)

WEAK_PHRASES = (
    "clearer homepage",
    "clearer page",
    "clearer path",
    "online presence",
    "one place",
    "organized information",
    "local visibility",
    "something to judge",
)

CONCRETE_ACTIONS = (
    "call",
    "book",
    "request a quote",
    "order",
    "visit",
    "message",
    "request consultation",
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


def assert_no_caveat_first_examples(text: str) -> None:
    bad_patterns = (
        re.compile(r"(?im)^\\s*(?:[-*]\\s*)?(?:Approved shape|Why a website|Auto repair[^:]*|Buyer-facing[^:]*|Good shape)?\\s*:?\\s*\"?Not as a guarantee\\."),
        re.compile(r"(?im)^\\s*1\\.\\s*Start with a short boundary"),
        re.compile(r"(?im)^\\s*-\\s*no-guarantee boundary\\s*$"),
    )
    for pattern in bad_patterns:
        match = pattern.search(text)
        assert_condition(match is None, f"Package still teaches caveat-first ordering near: {match.group(0) if match else ''}")


def assert_weak_phrases_guarded(text: str) -> None:
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if not any(phrase in line for phrase in WEAK_PHRASES):
            continue
        if (
            "do not use" in line
            or "do not say" in line
            or "avoid" in line
            or "weak phrases" in line
            or "supporting" in line
            or "not as the main" in line
            or "never as the main" in line
            or "once per conversation" in line
            or "guarantee" in line
            or "guaranteed" in line
            or "forbidden" in line
        ):
            continue
        assert_condition(
            any(action in line for action in CONCRETE_ACTIONS),
            f"Weak phrase lacks immediate concrete action on line {line_number}: {raw_line}",
        )


def assert_no_unbounded_guarantees(text: str) -> None:
    risky_patterns = (
        re.compile(r"\bwill (rank|get|bring|generate|create|increase) (you )?(more )?(traffic|customers|calls|bookings|patients|jobs|revenue)\b", re.I),
        re.compile(r"\bguarantee[sd]? (page-one|seo|ranking|rankings|traffic|customers|calls|bookings|patients|jobs|revenue|roi)\b", re.I),
        re.compile(r"\bpage-one guarantee\b", re.I),
        re.compile(r"\bnumerical seo lift\b", re.I),
    )
    safe_context = (
        "no ",
        "not ",
        "do not",
        "never",
        "forbidden",
        "without promising",
        "boundary",
        "won't promise",
        "i won't promise",
        "i'm not promising",
        "non-guaranteed",
        "guaranteed seo rankings",
        "we're not the right fit",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(raw_line) for pattern in risky_patterns):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"Unbounded guarantee-like claim on line {line_number}: {raw_line}",
            )


def main() -> None:
    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    combined = "\n".join((prompt_text, overlay_text, profile_text))

    assert_contains("answer ordering", combined, ORDER_MARKERS)
    assert_contains("business impact examples", combined, BUSINESS_IMPACT_EXAMPLES)
    assert_contains("commercial consequence framing", combined, CONSEQUENCE_MARKERS)
    assert_contains("channel objection examples", combined, CHANNEL_EXAMPLES)
    assert_contains("cost driver sales judgment", combined, COST_JUDGMENT_MARKERS)
    assert_contains("accepted interest moves forward", combined, ACCEPTED_INTEREST_MARKERS)
    assert_contains("pushback disqualification", combined, DISQUALIFICATION_MARKERS)
    assert_contains("natural speech", combined, NATURAL_SPEECH_MARKERS)
    assert_contains("terminal email close", combined, TERMINAL_EMAIL_MARKERS)
    assert_no_caveat_first_examples(combined)
    assert_weak_phrases_guarded(combined)
    assert_no_unbounded_guarantees(combined)

    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False, env=env)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-023-elite-sales-answer-ordering-commercial-conviction",
                "commercial_answer_ordering": True,
                "commercial_consequence_framing": True,
                "no_guarantee_boundaries_preserved": True,
                "accepted_interest_send_path": True,
                "natural_two_step_email_close": True,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
