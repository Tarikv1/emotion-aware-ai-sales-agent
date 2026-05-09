#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-028-synthetic-campaign-knowledge-grounding"
EXPECTED_NEXT = "PROD-029-grounded-full-scenario-rerun"

MODULE = ROOT / "scripts" / "prod_028_synthetic_campaign_knowledge_grounding.py"
RUNNER = ROOT / "scripts" / "run_prod_028_synthetic_campaign_knowledge_grounding.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_028_SYNTHETIC_CAMPAIGN_KNOWLEDGE_GROUNDING.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
CAMPAIGN_PATH = OUT_DIR / "synthetic_campaign.json"
TRACE_PATH = OUT_DIR / "grounded_answer_trace.html"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"
REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    CAMPAIGN_PATH,
    TRACE_PATH,
]

REQUIRED_SOURCE_URLS = {
    "https://www.hubspot.com/products/sales",
    "https://www.pipedrive.com/en/pricing",
    "https://www.salesforce.com/sales/pricing/",
    "https://www.zendesk.com/pricing/",
}

REQUIRED_BOUNDARY_FALSE_KEYS = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "raw_transcript_text_stored",
    "copied_real_company_text",
    "real_company_brand_used_as_campaign",
    "real_customer_data_used",
    "payment_collection_enabled",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
]

REAL_COMPANY_NAMES = {
    "hubspot",
    "pipedrive",
    "salesforce",
    "zendesk",
}

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "credit card",
    "card number",
    "take your payment",
    '"provider_calls_made": true',
    '"private_data_read": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"payment_collection_enabled": true',
    '"copied_real_company_text": true',
    '"real_company_brand_used_as_campaign": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def normalized_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def validate_campaign(campaign: dict[str, Any]) -> None:
    assert_condition(campaign.get("campaign_id") == "campaign-prod-028-routesignal-crm", campaign)
    identity_text = " ".join(
        str(campaign.get(key, ""))
        for key in [
            "campaign_id",
            "client_name",
            "product_name",
            "product_category",
            "approved_opening",
        ]
    ).lower()
    for name in REAL_COMPANY_NAMES:
        assert_condition(name not in identity_text, f"campaign identity uses real brand name: {name}")

    knowledge = campaign.get("product_knowledge", {})
    assert_condition(len(knowledge.get("plans", [])) == 3, knowledge)
    assert_condition(knowledge.get("trial", {}).get("length_days") == 14, knowledge)
    assert_condition(knowledge.get("billing", {}).get("annual_discount_percent") == 15, knowledge)
    assert_condition(knowledge.get("contract", {}).get("payment_collection_allowed_on_call") is False, knowledge)
    assert_condition("guaranteed revenue increase" in campaign.get("forbidden_claims", []), campaign)
    assert_condition("collect payment or card details on this call" in campaign.get("forbidden_claims", []), campaign)

    sources = campaign.get("source_inspiration", [])
    source_urls = {source.get("url") for source in sources}
    assert_condition(REQUIRED_SOURCE_URLS.issubset(source_urls), source_urls)
    for source in sources:
        assert_condition(source.get("reuse_label") == "inspiration only", source)
        assert_condition(source.get("directly_copied_material") == "none", source)


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == EXPECTED_NEXT, payload.get("next_checkpoint_recommended"))

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_BOUNDARY_FALSE_KEYS:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized_path(RESULT_PATH), outputs)
    assert_condition(outputs.get("campaign_path") == normalized_path(CAMPAIGN_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized_path(REPORT_PATH), outputs)
    assert_condition(outputs.get("trace_html_path") == normalized_path(TRACE_PATH), outputs)

    validate_campaign(payload.get("synthetic_campaign", {}))
    validate_campaign(read_json(CAMPAIGN_PATH))

    summary = payload.get("summary", {})
    assert_condition(summary.get("question_count") == 12, summary)
    assert_condition(summary.get("reality_based_source_count") >= 4, summary)
    assert_condition(summary.get("synthetic_campaign_facts_visible") is True, summary)
    assert_condition(summary.get("same_questions_compared") is True, summary)
    assert_condition(summary.get("direct_answer_rate") >= 0.9, summary)
    assert_condition(summary.get("factual_correctness_rate") == 1.0, summary)
    assert_condition(summary.get("price_correctness_rate") == 1.0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("question_overuse_rate") == 0.0, summary)
    assert_condition(summary.get("safe_unknown_handling_rate") == 1.0, summary)
    assert_condition(summary.get("grounded_answer_better_than_baseline") is True, summary)

    metrics = payload.get("metrics", {})
    for metric in [
        "direct_answer_rate",
        "factual_correctness_rate",
        "price_correctness_rate",
        "question_overuse_rate",
        "unsupported_claim_rate",
        "answer_then_ask_balance_rate",
        "safe_unknown_handling_rate",
        "baseline_question_overuse_rate",
    ]:
        assert_condition(metric in metrics, f"missing metric {metric}")
        assert_condition(isinstance(metrics[metric].get("value"), (int, float)), metrics[metric])

    cases = payload.get("evaluation_cases", [])
    assert_condition(len(cases) == 12, len(cases))
    assert_condition({case.get("case_id") for case in cases} == {f"PROD-028-Q{i:02d}" for i in range(1, 13)}, cases)
    for case in cases:
        for key in [
            "customer_question",
            "baseline_answer",
            "grounded_answer",
            "decision_snapshot",
            "expected_fact_refs",
            "fact_refs_used",
            "direct_answer",
            "factual_correct",
            "unsupported_claim",
            "question_overuse",
            "safe_unknown_handled",
        ]:
            assert_condition(key in case, f"{case.get('case_id')} missing {key}")
        assert_condition(case["direct_answer"] is True, case)
        assert_condition(case["factual_correct"] is True, case)
        assert_condition(case["unsupported_claim"] is False, case)
        assert_condition(case["question_overuse"] is False, case)
        assert_condition(case["payment_collection_detected"] is False, case)
        assert_condition(len(case["grounded_answer"].split()) <= 55, case["grounded_answer"])

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + CAMPAIGN_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_028_synthetic_campaign_knowledge_grounding.py" in commands, "PROD-028 runner missing from COMMANDS.md")
    assert_condition("validate_prod_028_synthetic_campaign_knowledge_grounding.py" in commands, "PROD-028 validator missing from COMMANDS.md")
    assert_condition("PROD_028_SYNTHETIC_CAMPAIGN_KNOWLEDGE_GROUNDING.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-028 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-028 missing from roadmap")
    assert_condition("PROD-028 synthetic campaign knowledge grounding" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-028 missing from methodology log")
    assert_condition("Use a synthetic reality-based product campaign before demo polish" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-028 decision missing from decision log")
    registry = REFERENCE_REGISTRY.read_text(encoding="utf-8")
    assert_condition("PROD-028 synthetic CRM product grounding sources" in registry, "PROD-028 source registry entry missing")
    for url in REQUIRED_SOURCE_URLS:
        assert_condition(url in registry, f"registry missing {url}")

    for path in [DOC_PATH, REPORT_PATH, TRACE_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-028",
            "synthetic campaign knowledge grounding",
            "reality-based source patterning: `true`",
            "fictional product: `true`",
            "same questions compared: `true`",
            "direct answer rate",
            "factual correctness rate",
            "question overuse rate",
            "provider calls made: `false`",
            "runtime behavior changed: `false`",
            EXPECTED_NEXT,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-028 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-028 synthetic campaign knowledge grounding validation passed.")


if __name__ == "__main__":
    main()
