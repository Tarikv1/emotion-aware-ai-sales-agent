#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-019-demand-capture-conversion-leakage-repair"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_demand_capture_conversion_leakage_repair.package.json"
)
V4_TESTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "tests"
    / "web_design_demand_capture_conversion_leakage_v4_simulation_tests.json"
)
FIXTURE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "fixtures" / "web_design_agent_config.sanitized.json"
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CAMPAIGN_OVERLAY = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_overlay.md"
)
CAMPAIGN_PROFILE = (
    ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio_web_design_campaign_profile.md"
)
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DYNAMIC_DEFAULTS = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "variables" / "mikes_kitchen_dynamic_variable_defaults.json"
DOC = ROOT / "docs" / "product" / "ELEVENLABS_019_DEMAND_CAPTURE_CONVERSION_LEAKAGE_REPAIR.md"

OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "agent_patch_and_v4_tests_plan.json"
REQUESTS = OUT_DIR / "agent_patch_and_v4_tests_requests.json"
PATCH = OUT_DIR / "agent_patch_payload.json"
V4_FOLDER_NAME = "Atlas Web Studio - Cross-Vertical Local Business Simulation V4"

APPROVED_ANSWER_PATTERN = (
    "Not as a guarantee. The real point is not magic new traffic. It is helping you waste less of the attention you "
    "already get. If someone finds you through Google, Instagram, a referral, or a shared link, the page should "
    "quickly show why they should trust you, what you offer, and what to do next."
)

VERTICAL_MECHANISMS = {
    "Restaurant / cafe": (
        "Google Maps, Instagram, referrals, walk-by interest",
        "menu, hours, photos, location, reservation/order/call path",
        "reserve, order, call, visit",
        "Google and Instagram may already get people curious",
    ),
    "Salon / barber": (
        "Instagram, referrals, Google search",
        "services, service range, reviews, or booking path",
        "book appointment",
        "Instagram gets attention",
    ),
    "Plumber / urgent service": (
        "Google emergency search, referrals, local maps",
        "service area, emergency work, trust, and click-to-call",
        "call",
        "already searching and stressed",
    ),
    "Mechanic / repair shop": (
        "Google, referrals, reviews",
        "services, diagnostics, hours, location, reviews, phone path",
        "call or request estimate",
        "already needs repairs",
    ),
    "Law office": (
        "Google, referral, local search",
        "practice area, credibility, location, and consultation path",
        "request consultation",
        "without promising rankings or outcomes",
    ),
    "Dental / clinic": (
        "Google, referral, insurance/provider search",
        "services, location, hours, appointment path",
        "call/request appointment",
        "Not as a guarantee of new patients",
    ),
    "Real estate": (
        "broker page, referral, Google, social",
        "agent credibility, local expertise, listings, valuation/consultation path",
        "seller inquiry/consultation",
        "broker page may show listings",
    ),
    "Gym / trainer": (
        "Instagram, referrals, local search",
        "programs, trainer proof, schedule, trial step",
        "book trial/session",
        "Social can create interest",
    ),
    "Home cleaning": (
        "Google, referrals, local groups",
        "service types, areas, reviews, quote path",
        "quote request",
        "already comparing cleaners",
    ),
    "HVAC / electrician": (
        "urgent search, referrals, Google Maps",
        "service area, job type, trust, and call/quote path",
        "call/request quote",
        "already needs help and is comparing who to call",
    ),
}

REQUIRED_TEST_IDS = {
    "sim_v4_plumber_emergency_calls_demand_capture",
    "sim_v4_salon_more_bookings_instagram_attention",
    "sim_v4_restaurant_more_customers_google_instagram",
    "sim_v4_mechanic_trust_and_estimate_path",
    "sim_v4_dental_new_patients_office_basics",
    "sim_v4_law_office_ranking_consultation_inquiries",
    "sim_v4_google_instagram_status_quo_objection",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    assert_condition(path.is_file(), f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_markers(path: Path, markers: tuple[str, ...]) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")
    return text


def markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    assert_condition(match is not None, f"Missing section: ## {heading}")
    start = match.end()
    next_heading = re.search(r"^## ", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def assert_no_secret_or_private_markers(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    blocked = (
        "xi-api-key",
        "api key value",
        "creator_email",
        "creator_name",
        "access_info",
        "phone_numbers",
        "whatsapp_accounts",
        "shareable_token",
        "data/private/",
        "data/private-restricted/",
        "private transcript",
        "sk-",
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def assert_no_unbounded_guarantee_claims(label: str, text: str) -> None:
    risky_patterns = (
        re.compile(r"\bwill (bring|get|create|generate) (you )?(more )?(customers|calls|bookings|patients|jobs|leads|traffic|revenue)\b"),
        re.compile(r"\bguarantee[sd]? (more )?(customers|calls|bookings|patients|jobs|leads|rankings|traffic|revenue)\b"),
        re.compile(r"\bwill rank (you|your business|the business) higher\b"),
        re.compile(r"\bguaranteed (lead|customer|revenue|ranking|traffic|call|booking)"),
    )
    safe_context = (
        "does not",
        "do not",
        "not ",
        "no ",
        "can't",
        "cannot",
        "without",
        "forbidden",
        "blocked",
        "asks",
        "whether",
        "question",
        "boundary",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(line) for pattern in risky_patterns):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"{label} line {line_number} contains an unbounded guarantee claim: {raw_line}",
            )


def assert_profile(profile_text: str) -> int:
    section = markdown_section(profile_text, "Approved Demand Capture And Conversion Leakage Facts")
    for marker in (
        "Update marker: `ELEVENLABS-019-demand-capture-conversion-leakage-repair`",
        "A website does not guarantee more customers, bookings, calls, jobs, quote requests, rankings, traffic, or revenue.",
        "A website can help the business convert existing attention into action.",
        "Existing attention can come from Google searches, Google Maps, Instagram, Facebook, referrals, QR codes, print material, word of mouth, ads, direct search, or shared links.",
        "The useful question is not",
        "does the business give them enough reason and enough convenience to take the next step?",
        "A website can reduce conversion leakage by answering buyer questions before they drop off:",
        "Do I trust this business?",
        "Do they provide what I need?",
        "Are they close enough or do they serve my area?",
        "Can I see proof, photos, reviews, service details, pricing/service ranges, or examples?",
        "What should I do next: call, book, order, request a quote, message, or visit?",
        "The free mockup is the proof object.",
        APPROVED_ANSWER_PATTERN,
        "forbidden: guaranteed outcomes",
        "allowed: conversion-path support for existing attention",
    ):
        assert_condition(marker in section, f"profile demand-capture section missing marker: {marker}")

    vertical_count = 0
    for heading, markers in VERTICAL_MECHANISMS.items():
        if f"### {heading}" in section:
            vertical_count += 1
        for marker in markers:
            assert_condition(marker in section, f"profile vertical {heading} missing marker: {marker}")
    assert_condition(vertical_count >= 9, f"expected at least 9 vertical mechanisms, found {vertical_count}")
    assert_no_unbounded_guarantee_claims("profile demand-capture section", section)
    return vertical_count


def assert_overlay(overlay_text: str) -> None:
    section = markdown_section(overlay_text, "Demand Capture Sales Ladder")
    for marker in (
        "Update marker: `ELEVENLABS-019-demand-capture-conversion-leakage-repair`",
        "No, I can't promise that.",
        "Not as a guarantee.",
        "The point is not magic new traffic. The point is wasting less of the attention you already get.",
        "People may already find you through Google, Instagram, referrals, or shared links.",
        "The page helps them trust you, understand the service, and take the next step.",
        "The mockup shows whether that path looks stronger before you pay for anything.",
        "Do not answer with only:",
        "clearer page",
        "something to judge",
        "customer decision path",
        "online presence",
        "local visibility support",
        "owned indexable page",
        "Those phrases are allowed only when connected to a concrete buyer action.",
    ):
        assert_condition(marker in section, f"overlay demand ladder missing marker: {marker}")
    assert_no_unbounded_guarantee_claims("overlay demand ladder", section)


def assert_prompt(prompt_text: str) -> None:
    for marker in (
        "Update marker: `ELEVENLABS-019-demand-capture-conversion-leakage-repair`",
        "No, I can't promise that. The point is not magic new traffic. It is helping you waste less of the attention you already get.",
        "If the buyer asks for business impact, Emma must include:",
        "one existing attention source",
        "one leakage problem",
        "one buyer action",
        "one proof step",
        "If someone finds you through [channel], the page should quickly show [trust/service/location/action detail] so they can [call/book/request quote/order/visit]. The mockup shows whether that path is stronger before you pay.",
        "If a draft answer says only",
        "who is already looking",
        "what they need to decide",
        "what action they should take",
        "If someone finds Apex Plumbing on Google, the page can help them quickly see emergency service, service area, reviews, and tap-to-call.",
    ):
        assert_condition(marker in prompt_text, f"prompt missing marker: {marker}")
    assert_no_unbounded_guarantee_claims("prompt", prompt_text)


def assert_v4_tests(test_pack: dict[str, Any]) -> None:
    assert_condition(test_pack.get("package_id") == CHECKPOINT_ID, "V4 test pack package_id mismatch")
    assert_condition(test_pack.get("test_type") == "simulation", "V4 test pack must be simulation")
    notes = test_pack.get("evaluation_repair_notes")
    assert_condition(isinstance(notes, dict), "V4 evaluation notes missing")
    for marker in (
        "no_guarantee_boundary",
        "existing_attention_source",
        "conversion_leakage_action_mechanism",
        "proof_before_purchase_step",
    ):
        assert_condition(marker in notes, f"V4 evaluation notes missing {marker}")

    tests = test_pack.get("tests")
    assert_condition(isinstance(tests, list) and len(tests) == 7, "expected seven V4 demand-capture simulation tests")
    seen_ids: set[str] = set()
    for item in tests:
        assert_condition(isinstance(item, dict), "each V4 test must be an object")
        test_id = str(item.get("test_id", ""))
        seen_ids.add(test_id)
        assert_condition(test_id in REQUIRED_TEST_IDS, f"unexpected V4 test_id: {test_id}")
        assert_condition(item.get("type") == "simulation", f"{test_id} must be simulation")
        max_turns = item.get("simulation_max_turns")
        assert_condition(isinstance(max_turns, int) and 12 <= max_turns <= 24, f"{test_id} max turns should be 12-24")
        scenario = str(item.get("simulation_scenario", ""))
        success = str(item.get("success_condition", ""))
        variables = item.get("dynamic_variables")
        assert_condition(len(scenario) >= 250, f"{test_id} scenario is too thin")
        assert_condition(len(success) >= 500, f"{test_id} success condition is too thin")
        assert_condition(isinstance(variables, dict), f"{test_id} dynamic variables missing")
        for marker in (
            "no-guarantee boundary",
            "existing attention source",
            "leakage problem",
            "buyer action",
            "proof step",
            "mockup",
            "It fails if",
        ):
            assert_condition(marker in success, f"{test_id} success condition missing marker: {marker}")
        for key in (
            "business_name",
            "business_type",
            "vertical",
            "existing_attention_source",
            "conversion_leakage_problem",
            "target_buyer_action",
            "proof_step",
            "status_quo_channel",
            "simulation_focus",
        ):
            assert_condition(isinstance(variables.get(key), str) and variables[key].strip(), f"{test_id} missing {key}")
        assert_no_unbounded_guarantee_claims(test_id, scenario + "\n" + success + "\n" + json.dumps(variables, ensure_ascii=False))
    assert_condition(seen_ids == REQUIRED_TEST_IDS, "V4 test coverage mismatch")


def main() -> None:
    for path in (
        RUNNER,
        MANIFEST,
        V4_TESTS,
        FIXTURE,
        UNIVERSAL_KB,
        CAMPAIGN_OVERLAY,
        CAMPAIGN_PROFILE,
        PROMPT,
        FIRST_MESSAGE,
        DYNAMIC_DEFAULTS,
        DOC,
    ):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("status") == "offline-repair-ready", "manifest status mismatch")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must stay offline by default")
    assert_condition(manifest.get("private_customer_data_used") is False, "manifest must not use private customer data")
    assert_condition(manifest.get("api_key_required_for_generation") is False, "manifest must not require API key generation")
    assert_condition("live_application" not in manifest, "019 manifest must not claim live application")
    assert_condition(
        manifest.get("baseline_tests") == [str(V4_TESTS.relative_to(ROOT)).replace("\\", "/")],
        "manifest must point at the 019 V4 simulation criteria",
    )
    assert_condition(
        manifest.get("upload_intent", {}).get("target_test_folder_name") == V4_FOLDER_NAME,
        "V4 target folder name mismatch",
    )
    assert_condition(
        manifest.get("repair_basis", {}).get("previous_checkpoint") == "ELEVENLABS-018-sales-value-and-contact-control-repair",
        "previous checkpoint mismatch",
    )

    serialized_manifest = json.dumps(manifest, ensure_ascii=False).lower()
    assert_condition('"live_provider_calls_made": true' not in serialized_manifest, "manifest enables live provider calls")
    for marker in ("crm", "calendar", "payment", "account tool", "live outbound calls", "scrape leads"):
        assert_condition(marker in serialized_manifest, f"manifest must explicitly block {marker}")

    profile_text = CAMPAIGN_PROFILE.read_text(encoding="utf-8")
    overlay_text = CAMPAIGN_OVERLAY.read_text(encoding="utf-8")
    prompt_text = PROMPT.read_text(encoding="utf-8")
    vertical_count = assert_profile(profile_text)
    assert_overlay(overlay_text)
    assert_prompt(prompt_text)

    test_pack = read_json(V4_TESTS)
    assert_v4_tests(test_pack)
    assert_no_secret_or_private_markers(test_pack)

    assert_markers(
        DOC,
        (
            CHECKPOINT_ID,
            "demand capture",
            "conversion leakage",
            "existing attention",
            V4_FOLDER_NAME,
            "No ElevenLabs API calls",
            "No OpenAI API calls",
            "No live outbound calls",
            "production readiness is not claimed",
        ),
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--package-manifest",
            str(MANIFEST),
            "--agent-config",
            str(FIXTURE),
            "--kb-document-id",
            "kbdoc_validation_universal_sales_core",
            "--kb-document-name",
            "universal_sales_core.md",
            "--kb-document-id",
            "kbdoc_validation_atlas_web_studio_web_design_campaign_overlay",
            "--kb-document-name",
            "atlas_web_studio_web_design_campaign_overlay.md",
            "--kb-document-id",
            "kbdoc_validation_atlas_web_studio_web_design_campaign_profile",
            "--kb-document-name",
            "atlas_web_studio_web_design_campaign_profile.md",
            "--agent-prompt-file",
            str(PROMPT),
            "--first-message-file",
            str(FIRST_MESSAGE),
            "--dynamic-variable-defaults",
            str(DYNAMIC_DEFAULTS),
            "--agent-temperature",
            "0.25",
            "--agent-patch-version-scope",
            "ELEVENLABS-019 demand capture conversion leakage repair",
            "--agent-patch-out",
            str(PATCH),
            "--test-folder-name",
            V4_FOLDER_NAME,
            "--out",
            str(PLAN),
            "--api-requests-out",
            str(REQUESTS),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    plan = read_json(PLAN)
    requests = read_json(REQUESTS)
    patch = read_json(PATCH)
    for payload in (plan, requests, patch):
        assert_no_secret_or_private_markers(payload)
    assert_condition(plan.get("mode") == "dry_run", "validator must stay dry-run")
    assert_condition(plan.get("live_provider_calls_made") is False, "validator must not call provider")
    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 3, "expected three KB upload drafts")
    assert_condition(len(plan.get("test_create_requests", [])) == 7, "expected seven V4 test create drafts")
    assert_condition(plan.get("test_folder", {}).get("folder_name") == V4_FOLDER_NAME, "plan V4 folder name mismatch")

    diff_check = subprocess.run(
        ["git", "diff", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "vertical_demand_capture_mechanism_count": vertical_count,
                "v4_simulation_test_count": len(plan.get("test_create_requests", [])),
                "knowledge_base_upload_count": len(plan.get("knowledge_base_upload_requests", [])),
                "live_provider_calls_made": False,
                "production_green_claimed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
