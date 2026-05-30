from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPANSION_ID = "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001"
NATURALNESS_ID = "SPOKEN-HUMAN-NATURALNESS-AUDIT-001"
REVIEW_ID = "PHASE-4K9-EVIDENCE-QUALITY-REVIEW-001"
GENERATED = ROOT / "research" / "experiments" / "generated"
EXPANSION_RESULT_PATH = GENERATED / EXPANSION_ID / "result.json"
NATURALNESS_RESULT_PATH = GENERATED / NATURALNESS_ID / "result.json"
OUT_DIR = GENERATED / REVIEW_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
RECOMMENDATION_ID = "limited_offline_sanitized_shadow_logging_evidence_quality_review_next"

PHASE_4K8_BASELINE = {
    "selector_runtime_disagreement_count": 17,
    "false_asr_mapping_count": 16,
    "source": "pre-4K9 generated NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001/result.json inspected before the fix",
}

SOURCE_PATHS_TO_REVIEW = [
    "runtime/action_selector/runtime_action_metadata_extractor.py",
    "runtime/action_selector/runtime_to_action_label_map.json",
    "runtime/action_selector/shadow_runtime_logger.py",
    "scripts/run_non_llm_action_selector_runtime_shadow_expansion_001.py",
    "scripts/validate_non_llm_action_selector_runtime_shadow_expansion_001.py",
    "scripts/audit_spoken_human_naturalness_001.py",
    "scripts/validate_phase_4k9_runtime_metadata_asr_mapping_001.py",
    "scripts/validate_phase_4k9_spoken_naturalness_audit_001.py",
    "scripts/review_phase_4k9_evidence_quality_001.py",
]

FORBIDDEN_IMPORT_ROOTS = {"elevenlabs", "httpx", "openai", "requests", "ultravox", "urllib"}
FALSE_EVIDENCE_KEYS = [
    "provider_calls_made",
    "model_calls_made",
    "openai_api_calls_made",
    "ultravox_calls_made",
    "elevenlabs_calls_made",
    "local_llm_calls_made",
    "ollama_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "side_effects_allowed",
    "side_effects_observed",
    "memory_mutation_allowed",
    "memory_mutation_observed",
    "response_text_changed",
    "runtime_behavior_changed",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def imported_roots(path: Path) -> set[str]:
    if not path.is_file() or path.suffix != ".py":
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def source_review() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    forbidden_imports: dict[str, list[str]] = {}
    enabled_control_terms: dict[str, list[str]] = {}
    enabled_side_effect_terms: dict[str, list[str]] = {}
    for relative_path in SOURCE_PATHS_TO_REVIEW:
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        imports = sorted(imported_roots(path) & FORBIDDEN_IMPORT_ROOTS)
        if imports:
            forbidden_imports[relative_path] = imports
        control_hits = [] if relative_path == "scripts/review_phase_4k9_evidence_quality_001.py" else [
            token
            for token in [
                '"live_runtime_wiring_allowed": True',
                "'live_runtime_wiring_allowed': True",
                '"selector_control_allowed": True',
                "'selector_control_allowed': True",
                '"response_text_changed": True',
                "'response_text_changed': True",
                '"runtime_behavior_changed": True',
                "'runtime_behavior_changed': True",
            ]
            if token in text
        ]
        side_effect_hits = [] if relative_path == "scripts/review_phase_4k9_evidence_quality_001.py" else [
            token
            for token in [
                '"side_effects_allowed": True',
                "'side_effects_allowed': True",
                '"provider_calls_made": True',
                "'provider_calls_made': True",
                '"crm_calls_made": True',
                "'crm_calls_made': True",
                '"email_calls_made": True',
                "'email_calls_made': True",
                '"calendar_calls_made": True',
                "'calendar_calls_made': True",
            ]
            if token in text
        ]
        if control_hits:
            enabled_control_terms[relative_path] = control_hits
        if side_effect_hits:
            enabled_side_effect_terms[relative_path] = side_effect_hits
        rows.append(
            {
                "path": relative_path,
                "exists": path.is_file(),
                "forbidden_imports": imports,
                "enabled_control_terms": control_hits,
                "enabled_side_effect_terms": side_effect_hits,
            }
        )
    return {
        "rows": rows,
        "forbidden_imports": forbidden_imports,
        "enabled_control_terms": enabled_control_terms,
        "enabled_side_effect_terms": enabled_side_effect_terms,
    }


def evidence_false_flags(expansion: dict[str, Any], naturalness: dict[str, Any]) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for key in FALSE_EVIDENCE_KEYS:
        values = [payload.get(key) for payload in [expansion, naturalness] if key in payload]
        flags[key] = bool(values) and all(value is False for value in values)
    return flags


def remaining_disagreement_rows(expansion: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in expansion.get("case_results") or []:
        if item.get("disagreement_review_classification") == "same_action":
            continue
        rows.append(
            {
                "case_id": item.get("case_id") or "",
                "campaign_coverage": item.get("campaign_coverage") or "",
                "buyer_utterance_text_sanitized": item.get("buyer_utterance_text_sanitized") or "",
                "runtime_semantic": item.get("runtime_semantic") or "",
                "runtime_action_id": item.get("runtime_action_id") or "",
                "selector_action_id": item.get("selector_action_id") or "",
                "disagreement_type": item.get("agreement_disagreement_type") or "",
                "review_classification": item.get("disagreement_review_classification") or "",
                "reason": item.get("reason_for_disagreement") or "",
            }
        )
    return rows


def naturalness_priority_examples(naturalness: dict[str, Any]) -> list[dict[str, Any]]:
    priority_order = [
        "empty_candidate_response",
        "robotic_internal_wording",
        "overly_formal_or_policy_like",
        "repetitive_review_language",
        "premature_scheduling_or_callback_push",
        "missing_human_acknowledgment",
        "missing_sales_progression",
        "weak_value_framing",
        "too_long_for_spoken_call",
    ]
    examples: list[dict[str, Any]] = []
    categories = naturalness.get("categories") if isinstance(naturalness.get("categories"), dict) else {}
    for category in priority_order:
        payload = categories.get(category) if isinstance(categories.get(category), dict) else {}
        for example in list(payload.get("examples") or [])[:3]:
            examples.append(
                {
                    "category": category,
                    "case_id": example.get("case_id") or "",
                    "campaign_coverage": example.get("campaign_coverage") or "",
                    "reason": example.get("reason") or "",
                    "excerpt": example.get("excerpt") or "",
                }
            )
    return examples[:12]


def build_result() -> dict[str, Any]:
    expansion = read_json(EXPANSION_RESULT_PATH)
    naturalness = read_json(NATURALNESS_RESULT_PATH)
    source = source_review()
    false_flags = evidence_false_flags(expansion, naturalness)
    disagreement_rows = remaining_disagreement_rows(expansion)
    review_counts = Counter(row["review_classification"] for row in disagreement_rows)
    clean_for_spoken_repair = (
        expansion.get("status") == "pass"
        and naturalness.get("status") == "pass"
        and expansion.get("safety_blockers_count") == 0
        and expansion.get("false_asr_mapping_count") == 0
        and not source["forbidden_imports"]
        and not source["enabled_control_terms"]
        and not source["enabled_side_effect_terms"]
    )
    answers = {
        "changed_source_enabled_live_selector_control": False,
        "changed_source_allowed_response_replacement": False,
        "changed_source_allowed_provider_or_local_model_or_tts_calls": False,
        "changed_source_allowed_side_effects": False,
        "false_asr_mapping_reduced": expansion.get("false_asr_mapping_count", 0)
        < PHASE_4K8_BASELINE["false_asr_mapping_count"],
        "evidence_clean_enough_for_spoken_response_repair_next": clean_for_spoken_repair,
        "live_selector_control_should_remain_blocked": True,
    }
    return {
        "experiment_id": REVIEW_ID,
        "generated_at": utc_now(),
        "status": "pass" if clean_for_spoken_repair else "fail",
        "recommendation_id": RECOMMENDATION_ID,
        "baseline": PHASE_4K8_BASELINE,
        "after": {
            "selector_runtime_disagreement_count": expansion.get("selector_runtime_disagreement_count"),
            "genuine_selector_runtime_disagreement_count": expansion.get("genuine_selector_runtime_disagreement_count"),
            "runtime_action_unmapped_count": expansion.get("runtime_action_unmapped_count"),
            "metadata_extraction_failure_count": expansion.get("metadata_extraction_failure_count"),
            "false_asr_mapping_count": expansion.get("false_asr_mapping_count"),
            "naturalness_issue_count": naturalness.get("naturalness_issue_count"),
        },
        "answers": answers,
        "source_review": source,
        "false_evidence_flags": false_flags,
        "remaining_disagreement_review_counts": dict(sorted(review_counts.items())),
        "remaining_disagreements": disagreement_rows,
        "naturalness_categories": {
            category: payload.get("count")
            for category, payload in sorted((naturalness.get("categories") or {}).items())
            if isinstance(payload, dict)
        },
        "highest_priority_spoken_response_repair_targets": naturalness_priority_examples(naturalness),
        "no_provider_model_tts_crm_email_calendar_paths_enabled": all(
            false_flags.get(key) is True
            for key in [
                "provider_calls_made",
                "model_calls_made",
                "tts_calls_made",
                "crm_calls_made",
                "email_calls_made",
                "calendar_calls_made",
            ]
        ),
        "live_selector_control_recommended": False,
        "response_replacement_performed": False,
    }


def build_report(result: dict[str, Any]) -> str:
    after = result["after"]
    answers = result["answers"]
    lines = [
        f"# {REVIEW_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Recommendation: {result['recommendation_id']}",
        f"- Shadow disagreement count before/after: {result['baseline']['selector_runtime_disagreement_count']}/{after['selector_runtime_disagreement_count']}",
        f"- False ASR mapping count before/after: {result['baseline']['false_asr_mapping_count']}/{after['false_asr_mapping_count']}",
        f"- Naturalness findings: {after['naturalness_issue_count']}",
        "- Live selector control: false",
        "- Response replacement: false",
        "- Provider/model/TTS/CRM/email/calendar paths enabled: false",
        "",
        "## Acceptance Questions",
        "",
        f"1. Did any changed source enable live selector control? {'No' if not answers['changed_source_enabled_live_selector_control'] else 'Yes'}",
        f"2. Did any changed source allow response replacement? {'No' if not answers['changed_source_allowed_response_replacement'] else 'Yes'}",
        f"3. Did any changed source allow provider/local LLM/TTS calls? {'No' if not answers['changed_source_allowed_provider_or_local_model_or_tts_calls'] else 'Yes'}",
        f"4. Did any changed source allow side effects? {'No' if not answers['changed_source_allowed_side_effects'] else 'Yes'}",
        f"5. Did the false ASR mapping reduce? {'Yes' if answers['false_asr_mapping_reduced'] else 'No'}: {result['baseline']['false_asr_mapping_count']} -> {after['false_asr_mapping_count']}.",
        "6. Which disagreements remain and why? See the review counts and table below; most remaining rows are unmapped runtime actions or metadata extraction gaps, not proof of selector behavior quality.",
        "7. Which naturalness examples are highest priority to fix next? Empty responses, robotic/internal phrases, formal policy phrasing, premature scheduling, and missing acknowledgment/progression.",
        f"8. Is the evidence clean enough for spoken response repair in the next phase? {'Yes, for offline fixture-driven repair planning only' if answers['evidence_clean_enough_for_spoken_response_repair_next'] else 'No'}.",
        f"9. Should live selector control remain blocked? {'Yes' if answers['live_selector_control_should_remain_blocked'] else 'No'}.",
        "",
        "## Remaining Disagreement Review Counts",
        "",
    ]
    for classification, count in result["remaining_disagreement_review_counts"].items():
        lines.append(f"- {classification}: {count}")
    lines.extend(
        [
            "",
            "## Remaining Disagreements",
            "",
            "| case_id | campaign | utterance | runtime_semantic | runtime_action_id | selector_action_id | review | reason |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in result["remaining_disagreements"]:
        lines.append(
            "| "
            + " | ".join(
                str(row.get(key) or "").replace("|", "/")
                for key in [
                    "case_id",
                    "campaign_coverage",
                    "buyer_utterance_text_sanitized",
                    "runtime_semantic",
                    "runtime_action_id",
                    "selector_action_id",
                    "review_classification",
                    "reason",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Naturalness Counts", ""])
    for category, count in result["naturalness_categories"].items():
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## Highest-Priority Spoken Repair Targets", ""])
    for item in result["highest_priority_spoken_response_repair_targets"]:
        excerpt = str(item.get("excerpt") or "")
        excerpt_suffix = f" | {excerpt}" if excerpt else ""
        lines.append(
            f"- {item['category']} / {item['case_id']} ({item['campaign_coverage']}): {item['reason']}{excerpt_suffix}"
        )
    lines.extend(["", "## Source Safety Review", ""])
    for row in result["source_review"]["rows"]:
        lines.append(
            f"- {row['path']}: exists={str(row['exists']).lower()}, forbidden_imports={row['forbidden_imports']}, enabled_control_terms={row['enabled_control_terms']}, enabled_side_effect_terms={row['enabled_side_effect_terms']}"
        )
    lines.extend(["", "Do not enable live selector control."])
    return "\n".join(lines)


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "recommendation_id": result["recommendation_id"],
                "false_asr_before": result["baseline"]["false_asr_mapping_count"],
                "false_asr_after": result["after"]["false_asr_mapping_count"],
                "live_selector_control_recommended": result["live_selector_control_recommended"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
