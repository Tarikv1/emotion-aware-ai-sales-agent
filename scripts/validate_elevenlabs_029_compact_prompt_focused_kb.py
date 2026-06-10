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
ATLAS_KB_ROOT = KB_ROOT / "atlas_web_studio"
PROMPT = AGENT_ROOT / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = AGENT_ROOT / "prompts" / "web_design_first_message.txt"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
ACTIVE_MANIFEST = AGENT_ROOT / "manifests" / "web_design_sales_spine_compression.package.json"
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
GENERATED_UPLOAD_ROOT = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-025-elite-sales-agent-operating-contract"

CHECKPOINT_ID = "ELEVENLABS-029-compact-system-prompt-focused-kb"

FOCUSED_KB_FILES = (
    "atlas_offer_facts.md",
    "atlas_value_mechanisms.md",
    "atlas_vertical_playbooks.md",
    "atlas_objection_playbook.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_close_and_followup_playbook.md",
    "atlas_output_quality_rules.md",
)

RECOMMENDED_UPLOAD_DOCS = [
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core_summary.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/buyer_moves.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/value_and_roi_framing.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/objection_status_quo_and_competition.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/trust_and_risk_repair.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/conversation_repair.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/next_step_policy.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/disqualification_policy.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/ethical_persuasion_boundaries.md",
    "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/call_quality_rubrics.md",
    *[
        f"runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/{name}"
        for name in FOCUSED_KB_FILES
    ],
]

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

PROMPT_KERNEL_MARKERS = (
    "Role: Emma from Atlas Web Studio.",
    "Mission: sell the free homepage mockup as the first low-risk next step.",
    "Layer precedence: Campaign Profile/Facts > Campaign Overlay > Universal Sales Summary/Categories.",
    "## Turn Decision Policy",
    "## State Priority",
    "## Natural Speech Rules",
    "## Output Hygiene",
    "## Anti-Repetition",
    "## Email And Callback State Machine",
    "## Core Boundaries",
    "Emma must not repeat the same value angle in consecutive turns.",
    "Fair point - the practical difference is",
    "Do not expose state labels to the buyer.",
)

VALUE_ANGLES = (
    "local search foundation",
    "booking filter",
    "quote filter",
    "trust-before-call page",
    "after-hours answer page",
    "tap-to-call page",
    "FAQ / price / policy filter",
    "service-area page",
    "comparison page",
    "DM reduction",
    "pre-qualification",
)

EMAIL_STATE_MARKERS = (
    "Soft agreement is not email capture.",
    "Send request without email -> ask for email.",
    "Buyer gives email -> confirm normalized email; no send language until explicit confirmation.",
    "Buyer confirms email -> close naturally.",
    "If the buyer already gave an email, do not ask for the email again.",
    "Gatekeeper callback closes cleanly.",
    "No extra pitch after a callback window is confirmed.",
)

ANALYSIS_REQUIRED_IDS = (
    "no_bracketed_internal_labels",
    "no_repeated_value_angle",
    "no_scripted_example_echo",
)

TEST_HARDENING_MARKERS = (
    "no buyer-facing output contains bracketed emotion, tone, stage, source, policy, or internal labels",
    "uses a different mechanism or disqualifies when the buyer asks for a clearer answer",
    "uses clearer page, clearer homepage, or clearer path as the headline value",
    "asks for email after soft agreement only",
    "asks for email again after email was already provided",
    "continues selling after email confirmation",
    "keeps pitching after stop request",
    "gives a full pitch to a gatekeeper after a callback window",
    "Do not fail solely because the simulated user ends immediately after providing an email address before another agent response is generated.",
)

BANNED_BRACKET_LABEL = re.compile(r"\[(?:happy|slow|neutral|curious|confused|thinking|sales|policy|source|great|perfect|email|stage|tone|emotion|internal|callback|close|value|objection|calm|friendly)[^\]\r\n]*\]", re.I)

RISKY_GUARANTEE_PATTERNS = (
    re.compile(r"\bguarantee[sd]? (?:more )?(?:customers|calls|bookings|jobs|patients|revenue|rankings|traffic|seo|roi|leads|page[- ]one)\b", re.I),
    re.compile(r"\bwill (?:rank|get|bring|generate|increase|deliver) (?:you )?(?:more )?(?:customers|calls|bookings|jobs|patients|revenue|traffic|leads)\b", re.I),
    re.compile(r"\bpage[- ]one promise\b", re.I),
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


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def active_prompt_and_kb_paths() -> list[Path]:
    paths = [PROMPT, FIRST_MESSAGE, PROFILE, OVERLAY, KB_ROOT / "universal_sales_core_summary.md"]
    paths.extend(ATLAS_KB_ROOT / name for name in FOCUSED_KB_FILES)
    return paths


def active_test_paths() -> list[Path]:
    return sorted((AGENT_ROOT / "tests").glob("web_design_*.json"))


def generated_upload_paths() -> list[Path]:
    if not GENERATED_UPLOAD_ROOT.is_dir():
        return []
    return sorted(
        path
        for path in GENERATED_UPLOAD_ROOT.glob("*.json")
        if path.name
        in {
            "live_agent_patch_plan.json",
            "live_agent_patch_payload.json",
            "live_agent_patch_requests.json",
            "live_agent_post_patch_snapshot.json",
        }
    )


def assert_no_bracketed_labels(paths: list[Path]) -> None:
    failures: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = BANNED_BRACKET_LABEL.search(line)
            if match:
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {match.group(0)}")
    assert_condition(not failures, "Bracketed buyer-facing/internal labels found:\n" + "\n".join(failures[:30]))


def assert_no_forbidden_guarantees(label: str, text: str) -> None:
    safe_context = (
        "no ",
        "not ",
        "do not",
        "never",
        "forbidden",
        "without promising",
        "non-guaranteed",
        "not as a page-one promise",
        "not as a page-one guarantee",
        "not the right fit",
        "must not",
        "fail",
    )
    failures: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.casefold()
        if any(pattern.search(raw_line) for pattern in RISKY_GUARANTEE_PATTERNS):
            if not any(marker in line for marker in safe_context):
                failures.append(f"{label}:{line_number}: {raw_line}")
    assert_condition(not failures, "Forbidden guarantee-like claims found:\n" + "\n".join(failures[:20]))


def assert_prompt_compact() -> None:
    prompt_text = read_text(PROMPT)
    assert_condition(word_count(prompt_text) <= 1450, f"Prompt is not compact enough: {word_count(prompt_text)} words")
    assert_contains("compact prompt", prompt_text, PROMPT_KERNEL_MARKERS)
    assert_contains("state priority", prompt_text, STATE_PRIORITY_MARKERS)
    assert_contains("email state machine", prompt_text, EMAIL_STATE_MARKERS)
    for angle in VALUE_ANGLES:
        assert_condition(angle in prompt_text, f"Prompt missing anti-repetition angle: {angle}")

    banned_prompt_sections = (
        "## Price And Scope",
        "## Common Turn Shapes",
        "## Website-Vs-Current-Channel Answers",
        "Approved Buyer-Facing Selling Examples",
        "Website cost drivers:",
        "Vertical cost drivers:",
        "Use these sharper examples as pattern examples",
        "Core cost answer:",
        "Dental cost answer:",
    )
    for marker in banned_prompt_sections:
        assert_condition(marker not in prompt_text, f"Prompt still contains KB-style section: {marker}")

    large_example_lines = [
        line
        for line in prompt_text.splitlines()
        if line.strip().startswith(("- \"", "Business-impact", "Salon /", "Restaurant:", "Mechanic:", "Plumber:"))
    ]
    assert_condition(len(large_example_lines) <= 6, "Prompt still contains a large example bank")
    assert_no_forbidden_guarantees("prompt", prompt_text)


def assert_focused_kb_files() -> None:
    assert_condition(ATLAS_KB_ROOT.is_dir(), f"Missing directory: {ATLAS_KB_ROOT.relative_to(ROOT)}")
    required_markers = {
        "atlas_offer_facts.md": (
            "free homepage mockup",
            "what it is / is not",
            "no obligation",
            "send/callback capability facts",
            "exact prices",
            "forbidden claims",
        ),
        "atlas_value_mechanisms.md": VALUE_ANGLES,
        "atlas_vertical_playbooks.md": (
            "salon/barber",
            "plumber/electrician/HVAC",
            "mechanic/auto repair",
            "restaurant/cafe",
            "dental/clinic",
            "cleaning",
            "real estate",
            "law office",
            "gym/trainer",
            "main buyer pain",
            "strongest website mechanism",
            "current-channel objection",
            "concise example answer",
            "disqualification signal",
        ),
        "atlas_objection_playbook.md": (
            "Instagram already works",
            "Google Maps already works",
            "referrals already work",
            "current website already works",
            "too expensive",
            "no time",
            "is this a scam",
            "guarantee demand",
            "pay-per-lead demand",
            "SEO guarantee demand",
            "previous bad agency experience",
        ),
        "atlas_price_scope_cost_drivers.md": (
            "low-end website scope",
            "high-end scope drivers",
            "vertical cost examples",
            "hosting/domain basics",
            "what is included in free mockup",
            "what becomes paid scope",
        ),
        "atlas_close_and_followup_playbook.md": (
            "accepted mockup -> ask email",
            "email provided -> confirm normalized email",
            "email confirmed -> close",
            "gatekeeper note",
            "callback window",
            "stop request",
            "buyer says thanks/bye",
        ),
        "atlas_output_quality_rules.md": (
            "no bracketed labels",
            "no repeated value angle",
            "no robotic phrases",
            "no over-explaining",
            "no repeated Perfect",
            "no clearer page as main value",
            "natural closing lines",
        ),
    }
    for name, markers in required_markers.items():
        path = ATLAS_KB_ROOT / name
        text = read_text(path)
        assert_contains(name, text, tuple(markers))
        assert_no_forbidden_guarantees(name, text)


def assert_profile_and_overlay_reduced() -> None:
    profile_text = read_text(PROFILE)
    overlay_text = read_text(OVERLAY)
    assert_condition(word_count(profile_text) <= 900, f"Campaign profile still too large: {word_count(profile_text)} words")
    assert_condition(word_count(overlay_text) <= 1000, f"Campaign overlay still too large: {word_count(overlay_text)} words")
    assert_contains("campaign profile", profile_text, ("Layer: Campaign Profile And Facts", "facts only", "exact offer", "exact prices", "forbidden claims"))
    assert_contains("campaign overlay", overlay_text, ("Layer: Campaign Sales Overlay", "Atlas-specific tactic summary", "Do not duplicate focused KB examples"))
    for text, label in ((profile_text, "campaign profile"), (overlay_text, "campaign overlay")):
        for marker in (
            "Approved Buyer-Facing Selling Examples",
            "Campaign-Safe Selling Point Bank",
            "Buyer-facing examples:",
            "Website Cost Driver Handling",
            "Vertical cost drivers:",
            "Email confirmation examples:",
        ):
            assert_condition(marker not in text, f"{label} still contains long duplicated bank: {marker}")


def assert_manifest() -> None:
    manifest = read_json(ACTIVE_MANIFEST)
    active = manifest.get("active_kb_recommendation", {})
    docs = active.get("recommended_upload_docs")
    assert_condition(isinstance(docs, list), "Manifest missing active recommended_upload_docs")
    assert_condition(docs == RECOMMENDED_UPLOAD_DOCS, "Manifest active docs do not match focused KB recommendation")
    assert_condition(active.get("active_upload_count") == len(RECOMMENDED_UPLOAD_DOCS), "Manifest active_upload_count mismatch")
    blocked_docs = active.get("not_recommended_for_active_upload_unless_explicitly_needed", [])
    for blocked in (
        "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
        "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
    ):
        assert_condition(blocked in blocked_docs, f"Manifest missing blocked old doc: {blocked}")
        assert_condition(blocked not in docs, f"Manifest still recommends old/superseded doc: {blocked}")
    prompt_files = manifest.get("prompt_files")
    assert_condition(
        prompt_files
        == [
            "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md",
            "runtime/providers/elevenlabs_agents/prompts/web_design_first_message.txt",
        ],
        "Manifest prompt_files mismatch",
    )


def assert_analysis() -> None:
    config = read_json(ANALYSIS_CONFIG)
    setup_text = read_text(ANALYSIS_SETUP)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "Analysis criteria missing")
    ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    for required_id in ANALYSIS_REQUIRED_IDS:
        assert_condition(required_id in ids, f"Analysis config missing criterion: {required_id}")
        assert_condition(f"`{required_id}`" in setup_text, f"Analysis setup missing criterion: {required_id}")
    config_text = json.dumps(config, ensure_ascii=False)
    for marker in (
        "no agent response contains bracketed emotion, tone, stage, source, policy, or internal labels",
        "Emma uses a different mechanism or disqualifies",
        "Emma repeats the same canned phrase",
    ):
        assert_condition(marker in config_text or marker in setup_text, f"Analysis missing marker: {marker}")


def assert_tests_hardened() -> None:
    combined = "\n".join(read_text(path) for path in active_test_paths())
    for marker in TEST_HARDENING_MARKERS:
        assert_condition(marker in combined, f"Active tests missing hardening marker: {marker}")
    for path in active_test_paths():
        payload = read_json(path)
        tests = payload.get("tests")
        assert_condition(isinstance(tests, list) and tests, f"{path.relative_to(ROOT)} must contain tests")


def main() -> None:
    assert_condition(PROMPT.is_file(), "Prompt missing")
    assert_condition(FIRST_MESSAGE.is_file(), "First message missing")

    assert_prompt_compact()
    assert_focused_kb_files()
    assert_profile_and_overlay_reduced()
    assert_manifest()
    assert_analysis()
    assert_tests_hardened()

    label_scan_paths = active_prompt_and_kb_paths() + active_test_paths() + [ANALYSIS_CONFIG, ANALYSIS_SETUP] + generated_upload_paths()
    assert_no_bracketed_labels(label_scan_paths)

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "prompt_word_count": word_count(read_text(PROMPT)),
                "focused_kb_files": list(FOCUSED_KB_FILES),
                "active_upload_count": len(RECOMMENDED_UPLOAD_DOCS),
                "bracketed_labels_present": False,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
