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
ACTIVE_MANIFEST = AGENT_ROOT / "manifests" / "web_design_sales_spine_compression.package.json"
ANALYSIS_CONFIG = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = AGENT_ROOT / "analysis" / "atlas_web_studio_analysis_setup.md"
GENERATED_UPLOAD_ROOT = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-025-elite-sales-agent-operating-contract"

CHECKPOINT_ID = "ELEVENLABS-029-cta-process-risk-no-callback"

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

CTA_MARKERS = (
    "Emma must not create CTA fatigue.",
    "one initial mockup offer",
    "one renewed send invitation after a meaningful value answer",
    "one email request after clear acceptance",
    "stop repeating the CTA until a clear send signal",
)

PROCESS_RISK_MARKERS = (
    "## Process-Risk Questions",
    "are process-risk questions. They are not email-capture signals by themselves.",
    "answer the process concern",
    "do not keep asking for email",
    "ask for email only after clear consent",
    "What's the best email?",
    "And then what?",
    "No automatic follow-up call.",
    "So no pressure?",
    "What do I do with it?",
)

NO_CALLBACK_MARKERS = (
    "Default follow-up after the mockup is email reply, not an automatic call.",
    "Do not claim Emma will call, follow up later, check back, or reach out after sending the mockup unless the buyer asks for or agrees to a callback.",
    "Default post-mockup path: send mockup by email, buyer reviews it, and if interested the buyer replies to the email.",
    "No automatic call, check-back, or follow-up is promised by default.",
    "Callback is allowed only if the buyer asks for or agrees to a callback.",
)

WEAK_PHRASES = (
    "clearer online presence",
    "clearer online presentation",
    "online presence",
    "potential improvements",
    "professional website could help",
    "help customers find your services",
    "help people understand your services",
    "make it easier to take the next step",
    "visual representation",
    "organized information",
    "one place",
    "central hub",
    "online brochure",
)

CONCRETE_MECHANISMS = (
    "emergency service check",
    "service-area check",
    "tap-to-call",
    "booking filter",
    "quote filter",
    "price/policy FAQ",
    "trust-before-call",
    "local search foundation",
    "after-hours answer page",
    "comparison page",
    "DM reduction",
    "pre-qualification",
)

GUARANTEE_MARKERS = (
    "If you want guaranteed page-one SEO or guaranteed emergency calls, I can't honestly offer that.",
    "service pages, service-area wording, technical basics, mobile structure, clear calls to action",
    "Serious SEO is usually an ongoing paid effort",
    "If you only want a guarantee, we're not the right fit.",
    "If the guarantee is the deal-breaker, I don't want to waste your time.",
    "We can help with the foundation and the site experience. We can't help with guaranteed outcomes.",
)

EMAIL_MARKERS = (
    "Buyer gives email -> confirm normalized email; no send language until explicit confirmation.",
    "Buyer confirms email -> close naturally.",
    "If the buyer already gave an email, do not ask for the email again.",
    "When the buyer gives a realistic email, confirm the normalized address only.",
    "Spoken emails such as \"service at northside auto repair dot com\"",
    "service@northsideautorepair.com",
)

ANALYSIS_IDS = (
    "no_cta_fatigue",
    "process_risk_before_email_capture",
    "no_follow_up_leakage",
    "concrete_mechanism_headline_value",
    "guarantee_escalation_correct",
)

TEST_MARKERS = (
    "asks to send the mockup more than twice without a new buyer commitment",
    "asks for email during process-risk objections before clear consent",
    "asks for email repeatedly",
    "I can follow up later",
    "weak generic headline value",
    "fails to normalize a realistic spoken email",
    "keeps explaining after disqualifying a guarantee-only buyer",
    "process-risk objections are answered directly",
    "no automatic callback is promised",
    "a clear send signal triggers one email request",
    "guarantee-only buyer gets clean disqualification",
)

BANNED_BRACKET_LABEL = re.compile(
    r"\[(?:happy|slow|neutral|curious|confused|thinking|sales|policy|source|great|perfect|email|stage|tone|emotion|internal|callback|close|value|objection|calm|friendly)[^\]\r\n]*\]",
    re.I,
)

PLACEHOLDER_EMAIL = re.compile(r"\b[\w.+-]+@example\.com\b|\[email[^\]\r\n]*\]", re.I)

RISKY_CLAIM_PATTERNS = (
    re.compile(r"\bwill (?:rank|get|bring|generate|increase|deliver) (?:you )?(?:more )?(?:customers|calls|bookings|jobs|patients|revenue|traffic|leads)\b", re.I),
    re.compile(r"\bvery high chance\b", re.I),
    re.compile(r"\bwe(?:'| have)ve used systems in the past\b", re.I),
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


def assert_markers(label: str, text: str, markers: tuple[str, ...]) -> None:
    for marker in markers:
        assert_condition(marker in text, f"{label} missing marker: {marker}")


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


def assert_no_risky_claims(paths: list[Path]) -> None:
    safe_context = (
        "do not",
        "never",
        "forbidden",
        "fail",
        "failure",
        "not offered",
        "cannot",
        "can't",
        "wouldn't promise",
        "without promising",
        "unless approved proof",
    )
    failures: list[str] = []
    for path in paths:
        text = read_text(path)
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.casefold()
            if any(pattern.search(raw_line) for pattern in RISKY_CLAIM_PATTERNS) and not any(marker in line for marker in safe_context):
                failures.append(f"{path.relative_to(ROOT)}:{line_number}: {raw_line}")
    assert_condition(not failures, "Risky guarantee/proof claims found:\n" + "\n".join(failures[:20]))


def assert_prompt_rules() -> None:
    prompt = read_text(PROMPT)
    assert_markers("prompt CTA discipline", prompt, CTA_MARKERS)
    assert_markers("prompt no automatic callback", prompt, NO_CALLBACK_MARKERS[:2])
    assert_markers("prompt email state", prompt, EMAIL_MARKERS[:3])
    assert_condition("Process-risk questions are not email capture signals." in prompt, "Prompt missing process-risk email-capture boundary")
    assert_condition("If the buyer wants guaranteed page-one SEO, guaranteed rankings, or guaranteed calls" in prompt, "Prompt missing SEO guarantee escalation boundary")


def assert_kb_rules() -> None:
    close = read_text(ATLAS_KB_ROOT / "atlas_close_and_followup_playbook.md")
    offer = read_text(ATLAS_KB_ROOT / "atlas_offer_facts.md")
    output = read_text(ATLAS_KB_ROOT / "atlas_output_quality_rules.md")
    objection = read_text(ATLAS_KB_ROOT / "atlas_objection_playbook.md")

    assert_markers("close playbook process-risk", close, PROCESS_RISK_MARKERS)
    assert_markers("close playbook CTA", close, CTA_MARKERS[1:])
    assert_markers("offer facts no callback", offer, NO_CALLBACK_MARKERS[2:])
    assert_markers("output weak phrase ban", output, WEAK_PHRASES)
    assert_markers("output concrete mechanism list", output, CONCRETE_MECHANISMS)
    assert_markers("objection guarantee escalation", objection, GUARANTEE_MARKERS)
    assert_markers("email normalization", close + "\n" + read_text(ANALYSIS_SETUP), EMAIL_MARKERS[3:])


def assert_analysis_rules() -> None:
    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "Analysis success_evaluation_criteria missing")
    ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    setup = read_text(ANALYSIS_SETUP)
    for criterion_id in ANALYSIS_IDS:
        assert_condition(criterion_id in ids, f"Analysis config missing criterion: {criterion_id}")
        assert_condition(f"`{criterion_id}`" in setup, f"Analysis setup missing criterion: {criterion_id}")
    analysis_text = json.dumps(config, ensure_ascii=False) + "\n" + setup
    assert_markers("analysis CTA/process rules", analysis_text, TEST_MARKERS[:5])


def assert_tests_hardened() -> None:
    test_paths = active_test_paths()
    assert_condition(test_paths, "No active web_design test files found")
    combined = "\n".join(read_text(path) for path in test_paths)
    assert_markers("active tests discipline markers", combined, TEST_MARKERS)
    assert_condition("protected placeholder email strings do not count as real normalization tests" in combined, "Tests missing placeholder email realism rule")

    placeholder_failures: list[str] = []
    for path in test_paths:
        payload = read_json(path)
        tests = payload.get("tests")
        assert_condition(isinstance(tests, list) and tests, f"{path.relative_to(ROOT)} must contain tests")
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if PLACEHOLDER_EMAIL.search(line):
                placeholder_failures.append(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
    assert_condition(not placeholder_failures, "Active web-design tests contain placeholder-looking emails:\n" + "\n".join(placeholder_failures[:20]))


def assert_focused_architecture() -> None:
    manifest = read_json(ACTIVE_MANIFEST)
    docs = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs")
    assert_condition(docs == RECOMMENDED_UPLOAD_DOCS, "Active manifest no longer points to the focused KB architecture")
    for name in FOCUSED_KB_FILES:
        assert_condition((ATLAS_KB_ROOT / name).is_file(), f"Missing focused KB file: {name}")
    prompt_word_count = len(re.findall(r"\b\S+\b", read_text(PROMPT)))
    assert_condition(prompt_word_count <= 1500, f"Prompt stopped being compact: {prompt_word_count} words")


def main() -> None:
    tracked_paths = [
        PROMPT,
        ANALYSIS_CONFIG,
        ANALYSIS_SETUP,
        KB_ROOT / "universal_sales_core_summary.md",
        *[ATLAS_KB_ROOT / name for name in FOCUSED_KB_FILES],
        *active_test_paths(),
        *generated_upload_paths(),
    ]

    assert_prompt_rules()
    assert_kb_rules()
    assert_analysis_rules()
    assert_tests_hardened()
    assert_focused_architecture()
    assert_no_bracketed_labels(tracked_paths)
    assert_no_risky_claims([PROMPT, ANALYSIS_CONFIG, ANALYSIS_SETUP, *[ATLAS_KB_ROOT / name for name in FOCUSED_KB_FILES], *active_test_paths()])

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "focused_kb_architecture": True,
                "cta_fatigue_rule_present": True,
                "process_risk_rule_present": True,
                "no_automatic_callback_default": True,
                "weak_phrase_ban_present": True,
                "guarantee_escalation_present": True,
                "bracketed_labels_present": False,
                "git_diff_check": "pass",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
