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
MIKES_SIM_TESTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_mikes_kitchen_simulation_tests.json"
CROSS_VERTICAL_TESTS = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"
)
PACKAGE_ROOT = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "ELEVENLABS-024-natural-two-step-email-close-value-language-polish"
)


TWO_STEP_EMAIL_MARKERS = (
    "Natural two-step email close",
    "Step 1 - after a clear email: confirm the email only.",
    "Step 2 - after the buyer confirms the email: close naturally.",
    "normalize obvious email spell-outs before confirming",
    "Do not ask another discovery question after email is provided.",
    "Do not re-pitch after email is provided.",
    "Do not over-explain the reply path unless the buyer asks.",
    "If the buyer asks whether they can reply to the email, answer yes briefly.",
    'If the buyer gives email and says "send it there" or "that\'s correct" in the same turn, Emma may close in one turn.',
    "Got it - northsideautorepair@gmail.com. Is that right?",
    "Perfect, I've got maya@lunahair.com. Is that the best email for the mockup?",
    "Got it, info@brightlanddental.com - that's the right place to send it?",
)

TERMINAL_CONFIRMATION_MARKERS = (
    "Terminal close after email confirmation",
    "yes",
    "correct",
    "that's right",
    "sounds good",
    "got it",
    "thanks",
    "talk soon",
    "okay bye",
    "Perfect. I'll send it over. Talk soon.",
    "Thanks, have a good one.",
    "Great, I'll send it there. Speak soon.",
)

GATEKEEPER_MARKERS = (
    "Gatekeeper callback close",
    "Perfect, I'll call back after 2 and ask for the owner. Thanks for passing that along.",
    'If the gatekeeper then says "ok" or "got it," close with: "Thanks. Have a good one."',
    "Do not add extra pitch details to the gatekeeper note unless asked.",
)

SUPPORTING_CLARITY_MARKERS = (
    "clearer homepage",
    "clearer page",
    "clearer path",
    "may be used once per conversation as supporting language",
    "never as the main value argument",
    "The mockup would show a clearer page where people can check services, starting prices, policies, reviews, and booking before they DM you.",
    "For an auto shop, it can make the page clearer around diagnostics, hours, reviews, location, and tap-to-call before someone chooses who to call.",
)

MAIN_VALUE_MARKERS = (
    "booking filter",
    "quote filter",
    "trust-before-call page",
    "local search foundation",
    "after-hours answer page",
    "tap-to-call page",
    "FAQ / price / policy filter",
    "page people can check before calling or booking",
    "service-area page",
    "comparison page for people already checking the business",
)

NATURAL_SPEECH_MARKERS = (
    "Got it.",
    "Perfect.",
    "Makes sense.",
    "That's fair.",
    "Exactly.",
    "That's the right idea.",
    "Talk soon.",
    "Have a good one.",
)

OLD_ONE_TURN_MARKERS = (
    "confirm delivery timing, confirm they can reply there with questions, and close naturally",
    "confirm send timing, confirm the reply path, and close naturally",
    "confirm the exact destination, link delivery timing, and reply path",
    "confirm destination, timing, and reply path",
    "Perfect, I'm sending it to mike@northsideauto.com, and you can reply there with questions. Thanks, Mike.",
    "Perfect, I'll send it to mike@northsideauto.com after this call, and you can reply there with questions. Thanks, Mike.",
    "I understand your point",
    "Thanks for confirming",
)

TEST_CRITERIA_MARKERS = (
    "buyer provides email; agent confirms normalized email; buyer confirms; agent closes",
    "do not fail if the simulated conversation ends immediately after the buyer provides the email and the agent never receives another turn",
    "fail if the agent receives a turn after email and does not confirm the normalized email",
    "fail if the agent continues discovery after email",
    "fail if the agent re-pitches after email",
    "fail if the agent ignores buyer confirmation and keeps talking",
    "fail if the agent never closes after email confirmation",
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
        assert_condition(marker not in text, f"{label} still contains old marker: {marker}")


def assert_clarity_phrases_guarded(text: str) -> None:
    clarity_phrases = ("clearer homepage", "clearer page", "clearer path")
    guard_words = (
        "supporting",
        "not the main",
        "never as the main",
        "once per conversation",
        "can check",
        "tap-to-call",
        "booking",
        "quote",
        "call",
        "before",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if not any(phrase in line for phrase in clarity_phrases):
            continue
        assert_condition(
            any(word in line for word in guard_words),
            f"Clarity phrase lacks supporting/action guard on line {line_number}: {raw_line}",
        )


def assert_test_criteria() -> None:
    test_text = "\n".join((read_text(MIKES_SIM_TESTS), read_text(CROSS_VERTICAL_TESTS)))
    assert_contains("natural two-step email close test criteria", test_text, TEST_CRITERIA_MARKERS)
    assert_absent("test criteria", test_text, ("confirm destination, timing, and reply path",))
    assert_absent("test criteria", test_text, ("confirm the exact destination, link delivery timing, and reply path",))


def assert_package_artifacts() -> None:
    required = (
        PACKAGE_ROOT / "live_agent_patch_plan.json",
        PACKAGE_ROOT / "live_agent_patch_payload.json",
        PACKAGE_ROOT / "live_agent_patch_requests.json",
        PACKAGE_ROOT / "live_agent_post_patch_snapshot.json",
    )
    for path in required:
        assert_condition(path.is_file(), f"Missing generated package artifact: {path.relative_to(ROOT)}")
    plan = read_json(PACKAGE_ROOT / "live_agent_patch_plan.json")
    assert_condition(plan.get("package_id") == "ELEVENLABS-024-natural-two-step-email-close-value-language-polish", "024 plan has wrong package_id")
    assert_condition(plan.get("live_provider_calls_made") is False, "024 plan must not claim live provider calls")


def main() -> None:
    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    combined = "\n".join((prompt_text, overlay_text, profile_text))

    assert_contains("two-step email close", combined, TWO_STEP_EMAIL_MARKERS)
    assert_contains("terminal email confirmation close", combined, TERMINAL_CONFIRMATION_MARKERS)
    assert_contains("gatekeeper close", combined, GATEKEEPER_MARKERS)
    assert_contains("supporting clarity language", combined, SUPPORTING_CLARITY_MARKERS)
    assert_contains("main value mechanisms", combined, MAIN_VALUE_MARKERS)
    assert_contains("natural speech replacements", combined, NATURAL_SPEECH_MARKERS)
    assert_absent("active package", combined, OLD_ONE_TURN_MARKERS)
    assert_clarity_phrases_guarded(combined)
    assert_test_criteria()
    assert_package_artifacts()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-024-natural-two-step-email-close-value-language-polish",
                "two_step_email_close": True,
                "terminal_confirmation_close": True,
                "gatekeeper_callback_close": True,
                "clearer_page_supporting_language_only": True,
                "test_criteria_updated": True,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
