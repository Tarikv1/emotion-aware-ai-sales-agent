#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "RAG-022-universal-sales-layer-contract"
RUNNER = ROOT / "scripts" / "run_elevenlabs_agent_automation.py"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_layered_sales_package.package.json"
)
FIXTURE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "fixtures"
    / "web_design_agent_config.sanitized.json"
)
UNIVERSAL_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"
CAMPAIGN_OVERLAY = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "knowledge_base"
    / "atlas_web_studio_web_design_campaign_overlay.md"
)
CAMPAIGN_PROFILE = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "knowledge_base"
    / "atlas_web_studio_web_design_campaign_profile.md"
)
LAYER_CONTRACT = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag" / "layer_contract.json"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
FIRST_MESSAGE = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_first_message.txt"
DYNAMIC_DEFAULTS = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "variables"
    / "mikes_kitchen_dynamic_variable_defaults.json"
)
DOC = ROOT / "docs" / "product" / "RAG_022_UNIVERSAL_SALES_LAYER_CONTRACT.md"
INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"

OUT_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "validation"
PLAN = OUT_DIR / "agent_patch_plan.json"
REQUESTS = OUT_DIR / "agent_patch_requests.json"
PATCH = OUT_DIR / "agent_patch_payload.json"

EXPECTED_CATEGORIES = (
    "buyer_moves",
    "buyer_journey_jobs",
    "buyer_enablement_and_sensemaking",
    "stakeholder_mapping",
    "discovery_question_design",
    "qualification_evidence",
    "value_and_roi_framing",
    "objection_status_quo_and_competition",
    "trust_and_risk_repair",
    "proof_and_evidence_handling",
    "conversation_repair",
    "next_step_policy",
    "decision_and_paper_process",
    "negotiation_and_concession_policy",
    "disqualification_policy",
    "ethical_persuasion_boundaries",
    "motion_specific_playbooks",
    "vertical_general_playbooks",
    "post_sale_handoff",
    "success_failure_patterns",
    "call_quality_rubrics",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"Missing JSON file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)} must contain a JSON object.")
    return payload


def assert_text_markers(path: Path, markers: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"Missing file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert_condition(marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}")
    return text


def assert_no_secret_leak(payload: dict[str, Any]) -> None:
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
    )
    found = [marker for marker in blocked if marker in serialized]
    assert_condition(not found, f"Output contains blocked marker(s): {found}")


def main() -> None:
    for path in (
        RUNNER,
        FIXTURE,
        UNIVERSAL_KB,
        CAMPAIGN_OVERLAY,
        CAMPAIGN_PROFILE,
        LAYER_CONTRACT,
        PROMPT,
        FIRST_MESSAGE,
        DYNAMIC_DEFAULTS,
        MANIFEST,
        DOC,
    ):
        assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")

    contract = read_json(LAYER_CONTRACT)
    assert_condition(contract.get("contract_id") == CHECKPOINT_ID, "layer contract id mismatch")
    assert_condition(contract.get("source_of_truth") == "repo", "layer contract must keep repo as source of truth")
    assert_condition(
        contract.get("precedence_order")
        == ["campaign_profile_facts", "campaign_sales_overlay", "universal_sales_rag"],
        "precedence order must keep facts above overlay above universal RAG",
    )
    assert_condition(contract.get("elevenlabs_document_reference_imports_supported") is False, "do not rely on KB imports")
    assert_condition(contract.get("universal_sales_rag_may_create_campaign_facts") is False, "universal RAG cannot create facts")
    assert_condition(contract.get("campaign_overlay_may_override_campaign_profile") is False, "overlay cannot override facts")
    assert_condition(contract.get("private_customer_data_allowed") is False, "private data must stay blocked")
    categories = contract.get("universal_sales_categories")
    assert_condition(categories == list(EXPECTED_CATEGORIES), "universal sales category list mismatch")

    universal_text = assert_text_markers(
        UNIVERSAL_KB,
        (
            "## Three-Layer Sales Knowledge Contract",
            "Layer 1: Universal Sales RAG",
            "Layer 2: Campaign Sales Overlay",
            "Layer 3: Campaign Profile And Facts",
            "Campaign Profile facts override campaign overlay.",
            "Campaign overlay overrides universal sales guidance.",
            "Universal sales guidance never creates campaign facts.",
            "buyer_enablement_and_sensemaking",
            "decision_and_paper_process",
            "call_quality_rubrics",
        ),
    )
    for blocked in ("Atlas Web Studio is offering", "Mike's Kitchen", "$1,000", "$10-$30/month"):
        assert_condition(blocked not in universal_text, f"universal KB leaked campaign fact marker: {blocked}")

    overlay_text = assert_text_markers(
        CAMPAIGN_OVERLAY,
        (
            "Package: `RAG-022-universal-sales-layer-contract`",
            "Layer: Campaign Sales Overlay",
            "This file adapts universal sales behavior to the Atlas Web Studio web-design motion.",
            "It does not own final factual truth.",
            "Campaign profile and facts override this overlay.",
            "Discovery Question Design Overlay",
            "Value And ROI Framing Overlay",
            "Objection, Status Quo, And Competition Overlay",
            "Proof And Evidence Handling Overlay",
            "Negotiation And Concession Policy Overlay",
            "Call Quality Rubric Overlay",
        ),
    )
    for blocked in ("Simple website projects generally start", "Basic hosting", "premium or immersive work can go up"):
        assert_condition(blocked not in overlay_text, f"overlay leaked price/fact marker: {blocked}")

    profile_text = assert_text_markers(
        CAMPAIGN_PROFILE,
        (
            "Package: `RAG-022-universal-sales-layer-contract`",
            "Layer: Campaign Profile And Facts",
            "This file owns the factual truth for the Atlas Web Studio web-design campaign.",
            "Atlas Web Studio is offering a free homepage mockup idea",
            "Simple website projects generally start around `$1,000`",
            "Premium or immersive work can go up to around `$5,000`",
            "Basic hosting for a small business website is usually around `$10-$30/month`",
            "Forbidden claims",
            "Do not guarantee more customers, bookings, rankings, revenue, traffic, or SEO outcomes.",
        ),
    )
    assert_condition(
        "Campaign overlay may change these facts" not in profile_text,
        "profile must not allow overlay fact overrides",
    )

    manifest = read_json(MANIFEST)
    assert_condition(manifest.get("package_id") == CHECKPOINT_ID, "manifest package_id mismatch")
    assert_condition(manifest.get("provider") == "elevenlabs", "manifest provider mismatch")
    assert_condition(manifest.get("source_of_truth") == "repo", "manifest must keep repo as source_of_truth")
    assert_condition(manifest.get("live_provider_calls_made") is False, "manifest must stay offline")
    assert_condition(
        manifest.get("knowledge_base_docs")
        == [
            "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md",
            "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md",
            "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md",
        ],
        "manifest KB docs must preserve universal, overlay, profile order",
    )
    upload_intent = manifest.get("upload_intent", {})
    assert_condition(upload_intent.get("layered_upload_package") is True, "layered upload intent missing")
    assert_condition(upload_intent.get("campaign_facts_override_all") is True, "facts override intent missing")
    assert_condition(upload_intent.get("document_reference_imports_required") is False, "imports must not be required")

    assert_text_markers(
        PROMPT,
        (
            "## Knowledge Layer Precedence",
            "Campaign profile and facts are the highest authority.",
            "Campaign sales overlay adapts the universal sales method to this campaign.",
            "Universal sales core is advisory sales method only.",
            "If the layers conflict, follow campaign profile facts first, then campaign overlay, then universal sales core.",
        ),
    )
    assert_text_markers(
        DOC,
        (
            "Universal Sales RAG",
            "Campaign Sales Overlay",
            "Campaign Profile And Facts",
            "python scripts\\validate_rag_022_universal_sales_layer_contract.py",
            "does not make a live provider call",
        ),
    )
    assert_text_markers(
        INDEX,
        (
            "Current RAG layer-contract checkpoint",
            "`RAG-022-universal-sales-layer-contract`",
        ),
    )
    assert_text_markers(
        COMMANDS,
        (
            "Validate the RAG-022 universal sales layer contract without provider calls",
            "python scripts\\validate_rag_022_universal_sales_layer_contract.py",
        ),
    )
    assert_text_markers(
        METHODOLOGY_LOG,
        (
            "RAG-022 universal sales layer contract",
            "Universal Sales RAG",
            "Campaign Sales Overlay",
            "Campaign Profile And Facts",
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
            "RAG-022 universal sales layer contract",
            "--agent-patch-out",
            str(PATCH),
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
    assert_no_secret_leak(plan)
    assert_no_secret_leak(requests)
    assert_no_secret_leak(patch)

    assert_condition(len(plan.get("knowledge_base_upload_requests", [])) == 3, "KB upload request count mismatch")
    assert_condition(plan.get("test_create_requests") == [], "RAG-022 should not create response tests")
    assert_condition(plan.get("agent_config_patch", {}).get("status") == "ready_for_review", "patch status mismatch")

    patched_prompt = patch["conversation_config"]["agent"]["prompt"]["prompt"]
    assert_condition("## Knowledge Layer Precedence" in patched_prompt, "patched prompt missing precedence section")
    patched_kb = patch["conversation_config"]["agent"]["prompt"]["knowledge_base"]
    patched_kb_names = [item.get("name") for item in patched_kb]
    for name in (
        "universal_sales_core.md",
        "atlas_web_studio_web_design_campaign_overlay.md",
        "atlas_web_studio_web_design_campaign_profile.md",
    ):
        assert_condition(name in patched_kb_names, f"patched KB missing {name}")

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": CHECKPOINT_ID,
                "knowledge_layers": ["universal_sales_rag", "campaign_sales_overlay", "campaign_profile_facts"],
                "knowledge_base_upload_requests": 3,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
