#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053A-english-sales-psychology-deep-dive"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_053a_english_sales_psychology_deep_dive.py",
    "runner": ROOT / "scripts" / "run_prod_053a_english_sales_psychology_deep_dive.py",
    "validator": ROOT / "scripts" / "validate_prod_053a_english_sales_psychology_deep_dive.py",
    "doc": ROOT / "docs" / "product" / "PROD_053A_ENGLISH_SALES_PSYCHOLOGY_DEEP_DIVE.md",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "source_register": OUT_DIR / "source_register.json",
    "topic_findings": OUT_DIR / "topic_findings.json",
    "compact_candidate_rules": OUT_DIR / "compact_candidate_rules.json",
    "rejected_or_deferred_tactics": OUT_DIR / "rejected_or_deferred_tactics.json",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "response_text_behavior_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_judging_used",
    "private_data_read",
    "source_excerpt_text_stored",
    "copied_scripts_stored",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
]

REQUIRED_TOPICS = {
    "adaptive_selling",
    "listening_and_trust",
    "buyer_confidence",
    "autonomy_and_reactance",
    "behavior_friction",
    "trust_repair",
    "conversation_repair",
    "spoken_brevity",
    "ethical_insight",
}

REQUIRED_RULE_IDS = {
    "english_psych_001_listen_answer_then_continue",
    "english_psych_002_relief_without_policy_dump",
    "english_psych_003_mirror_only_for_repair_or_discovery",
    "english_psych_004_one_small_decision",
    "english_psych_005_diagnose_friction_not_personality",
    "english_psych_006_autonomy_visible",
    "english_psych_007_trust_gap_specific",
    "english_psych_008_stop_after_question",
}

FORBIDDEN_TEXT = [
    '"runtime_behavior_changed": true',
    '"response_text_behavior_changed": true',
    '"provider_calls_made": true',
    '"source_excerpt_text_stored": true',
    '"copied_scripts_stored": true',
    "hidden emotion diagnosis",
    "fake urgency",
    "false scarcity",
    "pressure the customer",
    "commitment trap allowed",
    "data/private",
]

PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\-\(\) ]{7,}\d)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_PATTERN = re.compile(r"http" + r"s://\S+")


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")


def validate_result() -> dict[str, Any]:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["checked_date"] == "2026-05-15", result)
    assert_condition(summary["source_count"] >= 25, summary)
    assert_condition(summary["topic_finding_count"] >= 9, summary)
    assert_condition(summary["compact_candidate_rule_count"] >= 8, summary)
    assert_condition(summary["rejected_or_deferred_tactic_count"] >= 6, summary)
    assert_condition(summary["candidate_rules_ready_for_review"] == summary["compact_candidate_rule_count"], summary)
    assert_condition(summary["high_value_topic_count"] >= 7, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_sources(result: dict[str, Any]) -> None:
    sources = read_json(GENERATED_FILES["source_register"])["items"]
    source_ids = {source["source_id"] for source in sources}
    assert_condition(len(sources) == result["summary"]["source_count"], sources)
    assert_condition(len(source_ids) == len(sources), "duplicate source IDs")
    for source in sources:
        assert_condition(source["url"].startswith("https://"), source)
        assert_condition(source["checked_date"] == "2026-05-15", source)
        assert_condition(source["source_excerpt_text_copied"] is False, source)
        assert_condition(source["copied_script_text_stored"] is False, source)
        assert_condition(source["evidence_weight"] in {"high", "medium"}, source)
        assert_condition(source["usefulness"].strip(), source)


def validate_findings_and_rules() -> None:
    findings = read_json(GENERATED_FILES["topic_findings"])["items"]
    rules = read_json(GENERATED_FILES["compact_candidate_rules"])["items"]
    rejected = read_json(GENERATED_FILES["rejected_or_deferred_tactics"])["items"]
    finding_ids = {finding["finding_id"] for finding in findings}
    topics = {finding["topic"] for finding in findings}
    rule_ids = {rule["rule_id"] for rule in rules}
    assert_condition(REQUIRED_TOPICS.issubset(topics), sorted(REQUIRED_TOPICS - topics))
    assert_condition(REQUIRED_RULE_IDS.issubset(rule_ids), sorted(REQUIRED_RULE_IDS - rule_ids))
    for finding in findings:
        assert_condition(finding["source_ids"], finding)
        assert_condition(finding["finding"].strip(), finding)
        assert_condition(finding["agent_use"].strip(), finding)
        assert_condition(finding["avoid"].strip(), finding)
        assert_condition(finding["runtime_value"] in {"high", "medium"}, finding)
    for rule in rules:
        assert_condition(rule["source_finding_ids"], rule)
        assert_condition(all(finding_id in finding_ids for finding_id in rule["source_finding_ids"]), rule)
        assert_condition(rule["runtime_cost"] == "low", rule)
        assert_condition(rule["promotion_readiness"] == "candidate_for_prod_053b_review", rule)
        assert_condition(rule["example_good"].strip(), rule)
        assert_condition(rule["example_bad"].strip(), rule)
    assert_condition(any(item["decision"] == "reject" for item in rejected), rejected)
    assert_condition(any(item["decision"] == "defer" for item in rejected), rejected)


def validate_docs_and_report() -> None:
    combined = ""
    for key, path in (("doc", REQUIRED_FILES["doc"]), ("report", GENERATED_FILES["report"])):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        combined += "\n" + lowered
        for marker in (
            "prod-053a",
            "sales psychology",
            "compact",
            "runtime behavior",
            "provider calls",
            "prod-053b",
        ):
            assert_condition(marker in lowered, f"{key} missing {marker}")
        text_without_urls = URL_PATTERN.sub("", text)
        assert_condition(not PHONE_PATTERN.search(text_without_urls), f"phone-like string found in {key}")
        assert_condition(not EMAIL_PATTERN.search(text_without_urls), f"email-like string found in {key}")
    for phrase in FORBIDDEN_TEXT:
        if phrase in {"hidden emotion diagnosis", "fake urgency", "false scarcity"}:
            continue
        assert_condition(phrase not in combined.replace("\\", "/"), phrase)
    assert_condition("no source excerpts" in combined, "source excerpt boundary missing")
    assert_condition("no runtime behavior" in combined, "runtime boundary missing")


def validate_no_forbidden_payload_text() -> None:
    payload_text = json.dumps(read_json(GENERATED_FILES["result"]), sort_keys=True).lower()
    payload_text += "\n" + GENERATED_FILES["report"].read_text(encoding="utf-8").lower()
    normalized = payload_text.replace("\\", "/")
    for phrase in FORBIDDEN_TEXT:
        if phrase in {"hidden emotion diagnosis", "fake urgency", "false scarcity"}:
            assert_condition(phrase in normalized, f"expected rejected tactic reference missing: {phrase}")
        else:
            assert_condition(phrase not in normalized, phrase)


def main() -> None:
    validate_required_files()
    run_runner()
    validate_required_files()
    validate_generated_files()
    result = validate_result()
    validate_sources(result)
    validate_findings_and_rules()
    validate_docs_and_report()
    validate_no_forbidden_payload_text()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
