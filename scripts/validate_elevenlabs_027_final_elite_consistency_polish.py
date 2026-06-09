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
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_DOC = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
MIKES_SIM_TESTS = AGENT_ROOT / "tests" / "web_design_mikes_kitchen_simulation_tests.json"
CROSS_VERTICAL_TESTS = AGENT_ROOT / "tests" / "web_design_cross_vertical_local_business_simulation_tests.json"


EMAIL_STATE_MARKERS = (
    "Send request without email -> ask for email.",
    "Buyer gives email -> confirm normalized email.",
    "Buyer confirms email -> close naturally.",
    'If the buyer already gave an email, do not ask "what\'s the best email?" Confirm the normalized email instead.',
)

NATURALNESS_MARKERS = (
    "Give the direct commercial answer, one concrete mechanism, and one next step.",
    'Do not repeat "Perfect" across consecutive turns.',
    "Use examples as patterns, not scripts. Vary wording naturally and do not repeat the same example phrase across turns.",
)

ANALYSIS_MARKERS = (
    "accepted mockup without email triggers email capture",
    "Email provided triggers normalized email confirmation.",
    "Email confirmation triggers short close.",
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


def assert_contains_casefold(label: str, text: str, markers: tuple[str, ...]) -> None:
    haystack = text.casefold()
    for marker in markers:
        assert_condition(marker.casefold() in haystack, f"{label} missing marker: {marker}")


def section_after(text: str, header: str, stop_header: str = "\n## ") -> str:
    start = text.find(header)
    assert_condition(start >= 0, f"Missing section header: {header}")
    remainder = text[start:]
    stop = remainder.find(stop_header, len(header))
    return remainder if stop < 0 else remainder[:stop]


def commitment_section(text: str) -> str:
    start = text.find("Commitment / send signal")
    assert_condition(start >= 0, "Missing section header: Commitment / send signal")
    remainder = text[start:]
    stop_candidates = [
        index
        for marker in ("\n## ", "\n- Accepted send", "\n## Send-State Rule")
        if (index := remainder.find(marker, len("Commitment / send signal"))) >= 0
    ]
    return remainder if not stop_candidates else remainder[: min(stop_candidates)]


def assert_email_state_split(prompt_text: str, overlay_text: str) -> None:
    combined = "\n".join((prompt_text, overlay_text))
    assert_contains("email state split", combined, EMAIL_STATE_MARKERS)
    for text, label in ((prompt_text, "prompt"), (overlay_text, "overlay")):
        commitment = commitment_section(text)
        assert_condition("buyer gives email" not in commitment, f"{label} commitment section still includes buyer gives email")
        assert_condition("what's the best email" in commitment.lower(), f"{label} commitment section missing email-capture prompt for send request without email")
        assert_condition(
            not re.search(r"buyer gives email.*what's the best email", commitment, flags=re.I | re.S),
            f"{label} still maps buyer gives email to best-email capture",
        )


def assert_naturalness(prompt_text: str, overlay_text: str) -> None:
    assert_contains("prompt naturalness", prompt_text, NATURALNESS_MARKERS)
    assert_contains("overlay pattern examples", overlay_text, (NATURALNESS_MARKERS[2],))


def assert_analysis_alignment() -> None:
    config = read_json(ANALYSIS_CONFIG)
    doc_text = read_text(ANALYSIS_DOC)
    config_text = json.dumps(config, ensure_ascii=False)
    assert_contains_casefold("analysis setup doc", doc_text, ANALYSIS_MARKERS)
    assert_contains(
        "analysis config",
        config_text,
        (
            "Clear send signals without an email should trigger concise email capture.",
            "appears before any email and triggers one concise email question.",
            "asks for the best email after an email was already provided",
            "A provided email belongs to email/gave_email state, not the accepted-mockup email-capture trigger.",
        ),
    )


def assert_test_alignment() -> None:
    tests_text = "\n".join((read_text(MIKES_SIM_TESTS), read_text(CROSS_VERTICAL_TESTS)))
    assert_contains_casefold("test criteria", tests_text, ANALYSIS_MARKERS)
    assert_condition("accepted mockup triggers email capture" not in tests_text, "tests still use loose accepted-mockup trigger wording")
    assert_condition("Accepted mockup signal triggers email capture." not in tests_text, "tests still use loose accepted-mockup signal wording")


def main() -> None:
    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    assert_email_state_split(prompt_text, overlay_text)
    assert_naturalness(prompt_text, overlay_text)
    assert_analysis_alignment()
    assert_test_alignment()

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-027-final-elite-consistency-polish",
                "email_state_split": True,
                "examples_as_patterns": True,
                "naturalness_final_polish": True,
                "analysis_alignment": True,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
