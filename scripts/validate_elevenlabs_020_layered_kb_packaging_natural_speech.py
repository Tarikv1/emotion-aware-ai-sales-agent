#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base"
CATEGORY_ROOT = KB_ROOT / "universal_sales_categories"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
SUMMARY = KB_ROOT / "universal_sales_core_summary.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"
FULL_CORE = KB_ROOT / "universal_sales_core.md"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_spine_compression.package.json"
)
DOC = ROOT / "docs" / "product" / "ELEVENLABS_020_LAYERED_KB_PACKAGING_AND_NATURAL_SPEECH_COMPRESSION.md"

CATEGORY_FILES = [
    "buyer_moves.md",
    "buyer_journey_jobs.md",
    "buyer_enablement_and_sensemaking.md",
    "stakeholder_mapping.md",
    "discovery_question_design.md",
    "qualification_evidence.md",
    "value_and_roi_framing.md",
    "objection_status_quo_and_competition.md",
    "trust_and_risk_repair.md",
    "proof_and_evidence_handling.md",
    "conversation_repair.md",
    "next_step_policy.md",
    "decision_and_paper_process.md",
    "negotiation_and_concession_policy.md",
    "disqualification_policy.md",
    "ethical_persuasion_boundaries.md",
    "motion_specific_playbooks.md",
    "vertical_general_playbooks.md",
    "post_sale_handoff.md",
    "success_failure_patterns.md",
    "call_quality_rubrics.md",
]

CATEGORY_REQUIRED_SECTIONS = (
    "## Purpose",
    "## Owns",
    "## Does Not Own",
    "## When To Retrieve",
    "## Operating Rules",
    "## Failure Modes",
    "## Handoff To Campaign Overlay/Profile",
)

ATLAS_FACT_MARKERS = (
    "atlas web studio",
    "emma from atlas",
    "mike's kitchen",
    "mikes kitchen",
    "homepage mockup",
    "free mockup",
    "$1,000",
    "$5,000",
    "$10-$30",
    "google maps, instagram",
    "restaurant / cafe",
    "plumber / urgent service",
    "salon / barber",
    "dental / clinic",
    "law office",
    "hvac / electrician",
)

PROMPT_PATCH_MARKERS = (
    "ELEVENLABS-017",
    "ELEVENLABS-018",
    "ELEVENLABS-019",
    "Update marker:",
)

WEAK_VALUE_PHRASES = (
    "clearer page",
    "clear path",
    "one place",
    "organized information",
    "online presence",
    "something to judge",
    "local visibility",
)

FORBIDDEN_SIDE_EFFECT_MARKERS = (
    '"live_provider_calls_made": true',
    '"openai_api_calls_made": true',
    '"live_outbound_calls_enabled": true',
    '"lead_scraping_enabled": true',
    '"crm_tools_enabled": true',
    '"email_tools_enabled": true',
    '"calendar_tools_enabled": true',
    '"payment_tools_enabled": true',
    '"account_tools_enabled": true',
    "production_ready",
    "production readiness is claimed",
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


def section_index(text: str, heading: str) -> int:
    index = text.find(heading)
    assert_condition(index >= 0, f"Missing section heading: {heading}")
    return index


def assert_no_unbounded_guarantee_claims(label: str, text: str) -> None:
    risky_patterns = (
        re.compile(r"\bwill (bring|get|create|generate) (you )?(more )?(customers|calls|bookings|patients|jobs|leads|rankings|traffic|revenue)\b"),
        re.compile(r"\bguarantee[sd]? (more )?(customers|calls|bookings|patients|jobs|leads|rankings|traffic|revenue)\b"),
        re.compile(r"\bwill rank (you|your business|the business) higher\b"),
        re.compile(r"\bguaranteed (lead|customer|revenue|ranking|traffic|call|booking)"),
    )
    safe_context = (
        "no ",
        "not ",
        "do not",
        "never",
        "can't",
        "cannot",
        "forbidden",
        "boundary",
        "guarantee boundary",
        "asks whether",
        "no-guarantee",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(line) for pattern in risky_patterns):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"{label} line {line_number} contains an unbounded guarantee claim: {raw_line}",
            )


def assert_categories() -> None:
    assert_condition(CATEGORY_ROOT.is_dir(), f"Missing category directory: {CATEGORY_ROOT.relative_to(ROOT)}")
    files = sorted(path.name for path in CATEGORY_ROOT.glob("*.md"))
    assert_condition(files == sorted(CATEGORY_FILES), f"Universal category file set mismatch: {files}")

    for file_name in CATEGORY_FILES:
        path = CATEGORY_ROOT / file_name
        text = read_text(path)
        label = str(path.relative_to(ROOT))
        for section in CATEGORY_REQUIRED_SECTIONS:
            assert_condition(section in text, f"{label} missing section: {section}")
        word_count = len(re.findall(r"\b\w+\b", text))
        assert_condition(word_count <= 650, f"{label} is too long for focused retrieval: {word_count} words")
        lower = text.lower()
        found = [marker for marker in ATLAS_FACT_MARKERS if marker in lower]
        assert_condition(not found, f"{label} contains campaign-specific Atlas fact markers: {found}")
        assert_condition("transcript" not in lower, f"{label} must not be transcript-shaped")
        assert_condition("test criteria" not in lower, f"{label} must not include test criteria")
        assert_condition("patch history" not in lower, f"{label} must not include patch history")
        assert_contains(
            label,
            text,
            (
                "Universal guidance only",
                "Hand off campaign facts to the campaign overlay and campaign profile.",
            ),
        )


def assert_summary(summary_text: str) -> None:
    assert_contains(
        "universal_sales_core_summary.md",
        summary_text,
        (
            "Campaign Profile And Facts override Campaign Sales Overlay.",
            "Campaign Sales Overlay overrides Universal Sales guidance.",
            "Universal Sales guidance never creates campaign facts.",
            "## Three-Layer Contract",
            "## Buyer-Move Recognition",
            "## Discovery Rules",
            "## Value Framing Rules",
            "## Objection Handling Rules",
            "## Trust Repair Rules",
            "## Next-Step Policy",
            "## Disqualification Rules",
            "## Ethical Persuasion Boundaries",
            "## Call-Quality Rules",
        ),
    )
    assert_condition("Atlas Web Studio" not in summary_text, "Universal summary must not contain Atlas campaign facts")
    assert_condition(len(summary_text.split()) <= 900, "Universal summary should stay lightweight")


def assert_prompt(prompt_text: str) -> None:
    assert_contains(
        "web_design_atlas_sales_prompt.md",
        prompt_text,
        (
            "Role: Emma from Atlas Web Studio.",
            "Mission: sell the free homepage mockup as the first low-risk next step for local businesses.",
            "Layer precedence: Campaign Profile And Facts > Campaign Sales Overlay > Universal Sales Summary.",
            "Use contractions by default",
            "Not as a guarantee. The point is not magic new traffic.",
            "existing attention source",
            "where attention leaks",
            "buyer action",
            "mockup proof step",
            "If the buyer accepts the mockup and no destination is known",
            "Present-action send wording is allowed only if the current campaign process actually supports immediate send.",
            "Never claim an email, booking, CRM update, payment, or mockup has already happened unless it has actually happened.",
            "no guaranteed customers, calls, bookings, jobs, patients, revenue, rankings, traffic, SEO, or ROI",
            "{{business_name}}",
            "{{business_type}}",
            "{{city}}",
            "{{website_starting_price}}",
            "If a variable is known, do not rediscover it.",
            "Confirm known information instead.",
        ),
    )
    for marker in PROMPT_PATCH_MARKERS:
        assert_condition(marker not in prompt_text, f"Prompt contains patch/update marker: {marker}")
    for phrase in (
        "customer decision path",
        "customer action path",
        "campaign",
        "RAG",
        "conversion leakage",
        "owned indexable page",
        "local visibility support",
        "value proposition",
        "proof object",
        "demand capture",
        "vertical wedge",
        "hard boundary",
        "tool state",
        "fulfillment mode",
        "acceptance criteria",
        "system prompt",
        "instruction",
        "validator",
        "test case",
    ):
        assert_condition(phrase in prompt_text, f"Prompt missing forbidden robotic wording entry: {phrase}")
    assert_no_unbounded_guarantee_claims("prompt", prompt_text)


def assert_first_message(first_message: str) -> None:
    assert_condition(len(first_message.split()) <= 45, "First message must stay short")
    for marker in ("{{business_name}}", "{{business_type}}", "{{city}}"):
        assert_condition(marker in first_message, f"First message missing dynamic variable: {marker}")
    assert_condition("Am I speaking with the owner or someone who handles the website there?" in first_message, "First message must ask for owner/website handler")
    assert_condition("free homepage mockup" not in first_message.lower(), "First message should not pitch everything immediately")


def assert_profile(profile_text: str) -> None:
    demand_index = section_index(profile_text, "## Approved Demand Capture And Existing-Attention Conversion Facts")
    value_index = section_index(profile_text, "## Approved Supporting Value Facts")
    assert_condition(demand_index < value_index, "Demand-capture mechanism must be primary before supporting value facts")
    assert_contains(
        "campaign profile",
        profile_text,
        (
            "This file owns facts, not generic prompt rules.",
            "The primary cross-vertical value mechanism is existing-attention conversion support.",
            "help people who already find you take the next step",
            "waste less of the attention you already get",
            "Approved Prices",
            "Approved Assurance Facts",
            "Approved Vertical Mechanisms",
            "Approved Send And Callback Facts",
            "Approved Next Steps",
            "Forbidden Claims",
        ),
    )
    assert_no_unbounded_guarantee_claims("campaign profile", profile_text)


def assert_overlay(overlay_text: str) -> None:
    assert_contains(
        "campaign overlay",
        overlay_text,
        (
            "Demand Capture Sales Ladder",
            "The overlay adapts only the relevant universal categories",
            "discovery question design",
            "value and ROI framing",
            "objection/status quo/competition",
            "trust and risk repair",
            "proof handling",
            "conversation repair",
            "next-step policy",
            "disqualification",
            "motion-specific outbound playbook",
            "vertical playbook adaptation",
            "call quality",
            "No overclosing while the buyer is actively objecting",
            "No restaurant leakage into other verticals",
        ),
    )
    assert_no_unbounded_guarantee_claims("campaign overlay", overlay_text)


def assert_manifest(manifest: dict[str, Any]) -> None:
    assert_condition(manifest.get("package_id") == "ELEVENLABS-020-layered-kb-packaging-natural-speech", "manifest package_id mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must not claim provider calls")
    active_docs = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs")
    assert_condition(isinstance(active_docs, list), "manifest missing active recommended upload docs")
    assert_condition(str(SUMMARY.relative_to(ROOT)).replace("\\", "/") in active_docs, "manifest must recommend universal summary")
    assert_condition(str(FULL_CORE.relative_to(ROOT)).replace("\\", "/") not in active_docs, "manifest must not recommend full universal core for active Atlas upload")
    refs = manifest.get("source_reference_category_files")
    assert_condition(isinstance(refs, list) and len(refs) == 21, "manifest must list 21 source/reference category files")
    for file_name in CATEGORY_FILES:
        expected = str((CATEGORY_ROOT / file_name).relative_to(ROOT)).replace("\\", "/")
        assert_condition(expected in refs, f"manifest missing reference category: {expected}")
    serialized = json.dumps(manifest, ensure_ascii=False).lower()
    for marker in FORBIDDEN_SIDE_EFFECT_MARKERS:
        assert_condition(marker not in serialized, f"manifest introduces forbidden side-effect marker: {marker}")
    for marker in ("elevenlabs api calls", "openai api calls", "live outbound calls", "scrape leads", "crm tools", "email tools", "calendar tools", "payment tools", "account tools"):
        assert_condition(marker in serialized, f"manifest must explicitly block {marker}")


def assert_weak_phrase_policy(*texts: str) -> None:
    combined = "\n".join(texts)
    assert_condition(
        "Weak phrases are supporting language only, never standalone main value answers." in combined,
        "Missing weak-phrase standalone-answer policy",
    )
    for raw_line in combined.splitlines():
        line = raw_line.strip().lower().strip("-* `\"'")
        if line in WEAK_VALUE_PHRASES:
            fail(f"Weak phrase appears as a standalone line: {raw_line}")


def assert_doc(doc_text: str) -> None:
    assert_contains(
        "ELEVENLABS-020 doc",
        doc_text,
        (
            "## Why The Universal KB Was Split",
            "## Active Agent Package",
            "## Campaign Profile Owns Facts",
            "## Prompt Compression",
            "## Natural Spoken Style",
            "## Provider And Readiness Boundary",
            "No ElevenLabs API calls were made.",
            "No OpenAI API calls were made.",
            "No live outbound calls were enabled.",
            "Production readiness is not claimed.",
        ),
    )


def main() -> None:
    assert_categories()
    summary_text = read_text(SUMMARY)
    prompt_text = read_text(PROMPT)
    first_message = read_text(FIRST_MESSAGE).strip()
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    doc_text = read_text(DOC)
    manifest = read_json(MANIFEST)

    assert_summary(summary_text)
    assert_prompt(prompt_text)
    assert_first_message(first_message)
    assert_profile(profile_text)
    assert_overlay(overlay_text)
    assert_manifest(manifest)
    assert_weak_phrase_policy(prompt_text, overlay_text, profile_text)
    assert_doc(doc_text)

    combined_runtime_text = "\n".join((summary_text, prompt_text, overlay_text, profile_text, json.dumps(manifest, ensure_ascii=False)))
    for marker in FORBIDDEN_SIDE_EFFECT_MARKERS:
        assert_condition(marker not in combined_runtime_text.lower(), f"Forbidden side-effect marker introduced: {marker}")
    assert_no_unbounded_guarantee_claims("runtime package", combined_runtime_text)

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-020-layered-kb-packaging-natural-speech",
                "universal_category_file_count": len(CATEGORY_FILES),
                "universal_summary_kb": str(SUMMARY.relative_to(ROOT)).replace("\\", "/"),
                "active_kb_docs": manifest["active_kb_recommendation"]["recommended_upload_docs"],
                "prompt_compressed": True,
                "natural_speech_contractions": True,
                "demand_capture_primary": True,
                "live_provider_calls_made": False,
                "production_readiness_claimed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
