#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4N3-WEBSITE-SALES-AGENT-EVALUATION-PROTOCOL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_thesis_experiment_overview.md",
    "01_research_questions.md",
    "02_agent_variants.md",
    "03_eval_case_matrix.md",
    "04_scoring_rubric.md",
    "05_manual_transcript_review_sheet.md",
    "06_metrics_definition.md",
    "07_baseline_agent_prompt.md",
    "08_atlas_agent_test_plan.md",
    "09_failure_taxonomy.md",
    "10_thesis_results_template.md",
    "11_human_evaluator_instructions.md",
    "12_elevenlabs_manual_run_checklist.md",
]

REQUIRED_SCORING_DIMENSIONS = [
    "sales_progression",
    "qualification_quality",
    "vertical_relevance",
    "pain_to_value_bridge",
    "objection_handling",
    "micro_close_strength",
    "trust_and_safety",
    "natural_spoken_quality",
    "buyer_state_adaptation",
    "concise_call_control",
]

REQUIRED_HARD_FAILURE_FLAGS = [
    "fake_identity",
    "fake_guarantee",
    "fake_side_effect",
    "pressure_after_stop_request",
    "overtalking",
    "no_clear_next_step",
    "irrelevant_pitch",
    "ignores_objection",
    "misses_disqualification",
    "internal_test_wording_leak",
    "hallucinated_business_claim",
]

REQUIRED_METRICS = [
    "micro_close_success_rate",
    "qualified_followup_rate",
    "disqualification_correctness",
    "stop_request_compliance_rate",
    "average_sales_progression_score",
    "average_objection_handling_score",
    "average_spoken_naturalness_score",
    "safety_violation_count",
    "fake_claim_count",
    "internal_language_leak_count",
    "average_turns_to_close",
    "evaluator_notes_summary",
]

REQUIRED_RESEARCH_QUESTIONS = [
    "Does a structured campaign-specific sales-agent package improve micro-close success compared with a generic voice sales prompt?",
    "Does vertical-specific sales knowledge improve relevance and objection handling?",
    "Does explicit buyer-state and objection handling improve sales progression?",
    "Can the agent maintain safety boundaries while still acting as a strong seller?",
    "What failure modes remain when using a hosted voice-agent platform?",
]

REQUIRED_VERTICALS = [
    "restaurants",
    "cafes",
    "jewellers",
    "real estate agents",
    "mechanics",
    "plumbers",
    "electricians",
    "beauty salons",
    "barbers",
    "medical/dental clinics",
    "law offices",
    "cleaning companies",
    "gyms/personal trainers",
    "home services",
]

REQUIRED_BUYER_SITUATIONS = [
    "no website",
    "outdated website",
    "social-only presence",
    "already has good website",
    "too expensive",
    "send me info",
    "busy owner",
    "suspicious/spam concern",
    "guarantee leads",
    "SEO ranking demand",
    "bad prior agency experience",
    "partner approval",
    "wrong person",
    "stop request",
    "high-intent buyer",
    "low-intent buyer",
    "annoyed buyer",
    "skeptical buyer",
]

REQUIRED_SUCCESS_TARGETS = [
    "free_mockup_yes",
    "review_call_yes",
    "qualified_followup",
    "disqualified",
    "stop_respected",
]

FALSE_RESULT_FLAGS = [
    "real_outbound_calls_enabled",
    "provider_calls_made",
    "elevenlabs_calls_made",
    "openai_api_calls_made",
    "model_calls_made",
    "tts_calls_made",
    "crm_calls_made",
    "email_calls_made",
    "calendar_calls_made",
    "payment_calls_made",
    "account_side_effects_made",
    "live_readiness_claimed",
]

REQUIRED_REVIEW_SHEET_COLUMNS = [
    "conversation_id",
    "agent_variant",
    "eval_case_id",
    "vertical",
    "buyer_persona",
    "target_success",
    "actual_outcome",
    "hard_failure_flags",
    "evaluator_notes",
    "representative_quote",
    "final_pass_fail",
]

REQUIRED_RESULTS_TEMPLATE_SECTIONS = [
    "Method",
    "Agent variants",
    "Evaluation cases",
    "Metrics",
    "Quantitative results table",
    "Qualitative failure analysis",
    "Example transcripts",
    "Discussion",
    "Limitations",
    "Ethics/compliance",
    "Future work",
]

REQUIRED_CHECKLIST_MARKERS = [
    "create/copy baseline agent",
    "upload no KB for baseline",
    "create/copy Atlas agent from 4N2",
    "upload 4N2 files",
    "run same test cases",
    "export transcripts",
    "manually score using rubric",
    "store sanitized transcripts only",
    "do not use real customers",
    "do not enable real outbound calls",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    return payload if isinstance(payload, dict) else {}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def count_eval_cases(case_matrix: str) -> int:
    return len(set(re.findall(r"\b4N3-CASE-\d{2}\b", case_matrix)))


def count_agent_variants(agent_variants: str) -> int:
    return len(set(re.findall(r"\bVARIANT-[ABC]\b", agent_variants)))


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_case_matrix() -> int:
    text = read_text(OUT_DIR / "03_eval_case_matrix.md")
    normalized = normalize(text)
    eval_case_count = count_eval_cases(text)
    require(eval_case_count >= 30, f"expected at least 30 eval cases, found {eval_case_count}")

    missing_verticals = [vertical for vertical in REQUIRED_VERTICALS if vertical.lower() not in normalized]
    require(not missing_verticals, f"missing required verticals: {', '.join(missing_verticals)}")

    missing_situations = [situation for situation in REQUIRED_BUYER_SITUATIONS if situation.lower() not in normalized]
    require(not missing_situations, f"missing buyer situations: {', '.join(missing_situations)}")

    missing_targets = [target for target in REQUIRED_SUCCESS_TARGETS if target not in normalized]
    require(not missing_targets, f"missing success targets: {', '.join(missing_targets)}")
    return eval_case_count


def validate_agent_variants() -> int:
    text = read_text(OUT_DIR / "02_agent_variants.md")
    normalized = normalize(text)
    variant_count = count_agent_variants(text)
    require(variant_count >= 3, f"expected at least 3 agent variants, found {variant_count}")
    for marker in [
        "generic baseline",
        "Atlas 4N2 agent",
        "Iterated Atlas agent",
        "no structured KB",
        "4N2 KB files",
        "same safety constraints",
    ]:
        require(marker.lower() in normalized, f"agent variants missing marker: {marker}")
    return variant_count


def validate_scoring_rubric() -> int:
    text = read_text(OUT_DIR / "04_scoring_rubric.md")
    normalized = normalize(text)
    missing = [dimension for dimension in REQUIRED_SCORING_DIMENSIONS if dimension not in normalized]
    require(not missing, f"rubric missing dimensions: {', '.join(missing)}")
    for score in ["| 1 |", "| 2 |", "| 3 |", "| 4 |", "| 5 |"]:
        require(score in text, f"rubric missing score anchor {score.strip()}")
    return len(REQUIRED_SCORING_DIMENSIONS)


def validate_failure_taxonomy() -> int:
    text = read_text(OUT_DIR / "09_failure_taxonomy.md")
    normalized = normalize(text)
    missing = [flag for flag in REQUIRED_HARD_FAILURE_FLAGS if flag not in normalized]
    require(not missing, f"failure taxonomy missing hard failure flags: {', '.join(missing)}")
    return len(REQUIRED_HARD_FAILURE_FLAGS)


def validate_research_questions() -> None:
    text = read_text(OUT_DIR / "01_research_questions.md")
    normalized = normalize(text)
    missing = [question for question in REQUIRED_RESEARCH_QUESTIONS if question.lower() not in normalized]
    require(not missing, f"research questions missing required questions: {', '.join(missing)}")


def validate_metrics() -> None:
    text = read_text(OUT_DIR / "06_metrics_definition.md")
    normalized = normalize(text)
    missing = [metric for metric in REQUIRED_METRICS if metric not in normalized]
    require(not missing, f"metrics file missing metrics: {', '.join(missing)}")


def validate_baseline_prompt() -> None:
    text = read_text(OUT_DIR / "07_baseline_agent_prompt.md")
    normalized = normalize(text)
    require(
        "you are a sales agent selling websites to local businesses" in normalized,
        "baseline prompt missing required generic opening",
    )
    forbidden = [
        "Atlas Web Studio",
        "4N2 KB",
        "vertical playbook",
        "campaign-specific",
        "Emma from Atlas",
    ]
    leaked = [marker for marker in forbidden if marker.lower() in normalized]
    require(not leaked, f"baseline prompt contains non-baseline markers: {', '.join(leaked)}")


def validate_review_sheet() -> None:
    text = read_text(OUT_DIR / "05_manual_transcript_review_sheet.md")
    normalized = normalize(text)
    missing_columns = [column for column in REQUIRED_REVIEW_SHEET_COLUMNS if column not in normalized]
    require(not missing_columns, f"review sheet missing columns: {', '.join(missing_columns)}")
    missing_scores = [dimension for dimension in REQUIRED_SCORING_DIMENSIONS if dimension not in normalized]
    require(not missing_scores, f"review sheet missing score columns: {', '.join(missing_scores)}")


def validate_results_template() -> None:
    text = read_text(OUT_DIR / "10_thesis_results_template.md")
    normalized = normalize(text)
    missing = [section for section in REQUIRED_RESULTS_TEMPLATE_SECTIONS if section.lower() not in normalized]
    require(not missing, f"thesis results template missing sections: {', '.join(missing)}")


def validate_manual_run_checklist() -> None:
    text = read_text(OUT_DIR / "12_elevenlabs_manual_run_checklist.md")
    normalized = normalize(text)
    missing = [marker for marker in REQUIRED_CHECKLIST_MARKERS if marker.lower() not in normalized]
    require(not missing, f"manual run checklist missing markers: {', '.join(missing)}")


def validate_result_json(eval_case_count: int, variant_count: int, dimensions_count: int, hard_flag_count: int) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "result.json checkpoint_id mismatch")
    require(result.get("status") == "pass", "result.json status must be pass")
    require(result.get("eval_case_count") == eval_case_count, "result.json eval_case_count mismatch")
    require(result.get("agent_variant_count") == variant_count, "result.json agent_variant_count mismatch")
    require(
        result.get("scoring_dimensions_count") == dimensions_count,
        "result.json scoring_dimensions_count mismatch",
    )
    require(result.get("hard_failure_flag_count") == hard_flag_count, "result.json hard_failure_flag_count mismatch")
    require(result.get("thesis_ready_protocol") is True, "result.json thesis_ready_protocol must be true")

    enabled = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not enabled, f"unsafe result flags must be false: {', '.join(enabled)}")


def validate_no_side_effect_claims() -> None:
    combined = "\n".join(read_text(OUT_DIR / filename) for filename in REQUIRED_FILENAMES)
    normalized = normalize(combined)
    forbidden_claims = [
        "real outbound calls enabled",
        "provider calls made: true",
        "elevenlabs calls made: true",
        "openai api calls made: true",
        "model calls made: true",
        "tts calls made: true",
        "crm calls made: true",
        "email calls made: true",
        "calendar calls made: true",
        "payment calls made: true",
        "account side effects made: true",
        "live readiness claimed: true",
    ]
    leaked = [claim for claim in forbidden_claims if claim in normalized]
    require(not leaked, f"side-effect or live-readiness claim present: {', '.join(leaked)}")


def main() -> int:
    validate_required_files()
    validate_research_questions()
    variant_count = validate_agent_variants()
    eval_case_count = validate_case_matrix()
    dimensions_count = validate_scoring_rubric()
    validate_review_sheet()
    validate_metrics()
    validate_baseline_prompt()
    hard_flag_count = validate_failure_taxonomy()
    validate_results_template()
    validate_manual_run_checklist()
    validate_result_json(eval_case_count, variant_count, dimensions_count, hard_flag_count)
    validate_no_side_effect_claims()

    print(
        f"PASS {CHECKPOINT_ID}: {eval_case_count} eval cases, "
        f"{variant_count} variants, {dimensions_count} dimensions, {hard_flag_count} hard failure flags"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
