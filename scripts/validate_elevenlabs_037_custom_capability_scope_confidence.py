#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "ELEVENLABS-037-custom-capability-scope-confidence"

PROMPT = ROOT / "runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md"
OFFER = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md"
PRICE = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md"
OUTPUT = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md"
CLOSE = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_close_and_followup_playbook.md"
OBJECTION = ROOT / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_objection_playbook.md"
ANALYSIS_CONFIG = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_config.json"
ANALYSIS_SETUP = ROOT / "runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_setup.md"
ACTIVE_UPLOAD_MANIFEST = ROOT / "runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_markers(path: Path, markers: tuple[str, ...]) -> None:
    text = read(path)
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")


def git_diff_names(*paths: Path) -> list[str]:
    command = ["git", "diff", "--name-only", "--", *[str(path.relative_to(ROOT)) for path in paths]]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def main() -> None:
    assert_markers(
        OFFER,
        (
            "## Atlas Website And Custom System Capabilities",
            "Atlas Web Studio is not limited to brochure websites.",
            "standard business websites",
            "premium one-page websites",
            "Jobber and similar field-service integrations",
            "customer logins",
            "user accounts",
            "databases",
            "customer portals",
            "dashboards",
            "memberships",
            "API integrations",
            "workflow automation",
            "web applications",
            "connected functionality",
            "advanced SEO/content structures",
            "analytics",
            "tracking",
            "Scoping is not a refusal or lack of confidence.",
            "available API, webhooks, account access",
            "Yes, we can build that. The exact setup would need to be scoped.",
            "I don't want to invent a case study on the call.",
        ),
    )
    assert_markers(
        PROMPT,
        (
            "## Capability And Scope Confidence",
            "Atlas is not limited to brochure websites.",
            "answer capability first: \"Yes, we can build that.\"",
            "Scoping is not a refusal or lack of confidence.",
            "Do not sound overly cautious, apologetic, defensive, or vague.",
            "Do not invent named clients, project details, testimonials, prior implementations, outcomes, or case studies.",
        ),
    )
    assert_markers(
        PRICE,
        (
            "Capability questions get a confident capability answer first.",
            "Scoping defines exact workflow and final quote; it is not a refusal or lack of confidence.",
            "Integrations may depend on the platform's available API, webhooks, account access, or supported integration methods.",
            "Emma: \"Yes, we can build that. I wouldn't price it cleanly on a quick call, though.",
            "Scoping determines the exact workflow, data, permissions, APIs, security, integrations, and implementation; it does not mean Atlas is unsure or unwilling to build it.",
        ),
    )
    assert_markers(
        OUTPUT,
        (
            "## Capability Confidence Without Fake Proof",
            "When the buyer asks whether Atlas can build custom functionality, answer capability first and scope second.",
            "Yes, we can build that. The exact setup would need to be scoped.",
            "I don't want to invent a case study on the call.",
        ),
    )
    assert_markers(
        CLOSE,
        (
            "If buyer explicitly wants to scope a custom system later, Emma may say:",
            "Do not make booking a Google Meet, paid consultation, or scoping call the default first-call next step.",
        ),
    )
    assert_markers(
        OBJECTION,
        (
            "## can you actually build that",
            "Answer capability confidently when the buyer asks about custom functionality",
            "If the buyer asks for a named client, case study, exact prior implementation, or measurable proof that is not supplied in campaign facts, do not invent it.",
        ),
    )

    config = read_json(ANALYSIS_CONFIG)
    criteria = config.get("success_evaluation_criteria")
    assert_condition(isinstance(criteria, list), "analysis criteria missing")
    assert_condition(len(criteria) <= 30, "ElevenLabs Analysis criteria cap exceeded")
    serialized = json.dumps(config, ensure_ascii=False)
    for marker in (
        "yes, we can build that",
        "custom portals, dashboards, databases, connected functionality, or web applications",
        "sounds unsure about approved Atlas capabilities",
        "I don't want to invent a case study",
        "named clients, exact prior implementations, case studies",
    ):
        assert_condition(marker in serialized, f"analysis config missing marker: {marker}")

    setup = read(ANALYSIS_SETUP)
    for marker in (
        "CRM/payment/calendar/custom-system questions should get a confident capability-first answer before price",
        "Capability posture: Atlas is not limited to brochure websites.",
        "Fail overly cautious approved-capability answers",
        "does not want to invent one while still confirming Atlas can build the described system",
    ):
        assert_condition(marker in setup, f"analysis setup missing marker: {marker}")

    tests_diff = subprocess.run(
        ["git", "diff", "--name-only", "--", "runtime/providers/elevenlabs_agents/tests", "research/experiments/generated"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(tests_diff.returncode == 0, tests_diff.stderr or tests_diff.stdout)
    assert_condition(not tests_diff.stdout.strip(), "Dashboard tests or generated live evidence were modified")
    assert_condition(not git_diff_names(ACTIVE_UPLOAD_MANIFEST), "active KB upload manifest was modified")

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "analysis_criteria_count": len(criteria),
                "capability_confidence": True,
                "fake_case_study_guard": True,
                "dashboard_tests_changed": False,
                "active_upload_manifest_changed": False,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
