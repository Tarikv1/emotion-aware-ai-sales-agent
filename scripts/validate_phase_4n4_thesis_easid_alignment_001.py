#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PHASE-4N4-THESIS-EASID-ALIGNMENT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILENAMES = [
    "result.json",
    "report.md",
    "00_thesis_alignment_overview.md",
    "01_research_question_mapping.md",
    "02_easid_schema.md",
    "03_easid_example_rows.jsonl",
    "04_emotion_signal_plan.md",
    "05_persuasion_strategy_taxonomy.md",
    "06_buyer_state_taxonomy.md",
    "07_outcome_metrics_mapping.md",
    "08_black_box_baseline_comparison_plan.md",
    "09_human_likeness_evaluation_plan.md",
    "10_latency_and_real_time_constraints_plan.md",
    "11_placeholder_result_tables.md",
    "12_thesis_methodology_bridge.md",
    "13_limitations_and_ethics.md",
]

REQUIRED_RQS = ["RQ1", "RQ2", "RQ3", "RQ4", "RQ5", "RQ6", "RQ7"]

REQUIRED_EASID_FIELDS = [
    "conversation_id",
    "turn_id",
    "agent_variant",
    "campaign_id",
    "vertical",
    "buyer_persona",
    "buyer_turn_text",
    "agent_response_text",
    "buyer_state_label",
    "emotion_label",
    "emotion_confidence",
    "sentiment_score",
    "acoustic_features_available",
    "pitch_mean",
    "pitch_range",
    "speech_rate",
    "pause_count",
    "interruption_count",
    "text_emotion_cues",
    "objection_type",
    "persuasion_strategy",
    "sales_stage",
    "recommended_next_action",
    "micro_close_attempted",
    "micro_close_outcome",
    "outcome_label",
    "hard_failure_flags",
    "safety_flags",
    "latency_ms",
    "evaluator_scores",
    "privacy_redaction_status",
    "raw_audio_stored",
    "raw_transcript_stored",
    "notes",
]

REQUIRED_EMOTION_LABELS = [
    "curious",
    "confused",
    "skeptical",
    "price_sensitive",
    "frustrated",
    "busy",
    "high_intent",
    "low_intent",
    "trust_concerned",
    "neutral",
]

REQUIRED_PERSUASION_STRATEGIES = [
    "consultative_diagnosis",
    "pain_to_value_bridge",
    "low_risk_micro_close",
    "objection_reframe",
    "trust_building",
    "social_proof_safe",
    "disqualification",
    "next_step_simplification",
    "loss_framing_without_fearmongering",
    "no_pressure_close",
]

FORBIDDEN_PERSUASION = [
    "fake scarcity",
    "fake authority",
    "emotional exploitation",
    "manipulation",
    "guarantee fabrication",
]

REQUIRED_BUYER_STATES = [
    "curious",
    "skeptical",
    "busy",
    "annoyed",
    "price_sensitive",
    "trust_concerned",
    "high_intent",
    "low_intent",
    "wrong_person",
    "no_fit",
    "compliance_sensitive",
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
    "latency_ms",
]

PLACEHOLDER_TABLES = [
    "emotion detection table",
    "agent variant comparison table",
    "persuasion strategy success table",
    "human-likeness rating table",
    "latency table",
    "safety violation table",
    "EASID feature coverage table",
]

TEMPLATE_MARKER = "Template only \u2014 no experimental results recorded yet."

FALSE_RESULT_FLAGS = [
    "fabricated_results_present",
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

FORBIDDEN_PRIVATE_EXAMPLE_MARKERS = [
    "real customer",
    "private audio",
    "raw private",
    "verbatim transcript",
    "phone number",
    "email address",
    "api key",
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


def validate_required_files() -> None:
    missing = [filename for filename in REQUIRED_FILENAMES if not (OUT_DIR / filename).is_file()]
    require(not missing, f"missing required files: {', '.join(missing)}")


def validate_research_question_mapping() -> int:
    text = read_text(OUT_DIR / "01_research_question_mapping.md")
    normalized = normalize(text)
    missing = [rq for rq in REQUIRED_RQS if rq.lower() not in normalized]
    require(not missing, f"missing mapped proposal RQs: {', '.join(missing)}")
    mapped = len(set(re.findall(r"\bRQ[1-7]\b", text)))
    require(mapped == 7, f"expected 7 mapped RQs, found {mapped}")
    for marker in [
        "manual emotion labels",
        "schema completeness",
        "successful vs unsuccessful",
        "generic baseline",
        "manual rating rubric",
        "common objections",
        "same case matrix and rubric",
    ]:
        require(marker.lower() in normalized, f"RQ mapping missing marker: {marker}")
    return mapped


def validate_schema() -> int:
    text = read_text(OUT_DIR / "02_easid_schema.md")
    normalized = normalize(text)
    missing = [field for field in REQUIRED_EASID_FIELDS if field not in normalized]
    require(not missing, f"EASID schema missing fields: {', '.join(missing)}")
    for marker in [
        "public evidence must not store raw private audio",
        "synthetic/sanitized",
        "private restricted storage",
    ]:
        require(marker.lower() in normalized, f"EASID schema missing privacy rule: {marker}")
    return len(REQUIRED_EASID_FIELDS)


def validate_examples() -> int:
    text = read_text(OUT_DIR / "03_easid_example_rows.jsonl")
    rows = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"example row {line_number} is not valid JSONL: {exc}")
        require(isinstance(row, dict), f"example row {line_number} must be an object")
        rows.append(row)

    require(len(rows) >= 5, f"expected at least 5 synthetic example rows, found {len(rows)}")
    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_EASID_FIELDS if field not in row]
        require(not missing, f"example row {index} missing fields: {', '.join(missing)}")
        require(row.get("raw_audio_stored") is False, f"example row {index} stores raw audio")
        require(row.get("raw_transcript_stored") is False, f"example row {index} stores raw transcript")
        redaction = str(row.get("privacy_redaction_status", "")).lower()
        require(
            "synthetic" in redaction or "sanitized" in redaction,
            f"example row {index} must be synthetic or sanitized",
        )

    normalized = normalize(text)
    for scenario in [
        "restaurant",
        "plumber",
        "wrong_person",
        "stop request",
        "annoyed",
    ]:
        require(scenario in normalized, f"example rows missing scenario marker: {scenario}")
    leaked = [marker for marker in FORBIDDEN_PRIVATE_EXAMPLE_MARKERS if marker in normalized]
    require(not leaked, f"example rows contain private/raw markers: {', '.join(leaked)}")
    return len(rows)


def validate_emotion_plan() -> int:
    text = read_text(OUT_DIR / "04_emotion_signal_plan.md")
    normalized = normalize(text)
    missing = [label for label in REQUIRED_EMOTION_LABELS if label not in normalized]
    require(not missing, f"emotion signal plan missing labels: {', '.join(missing)}")
    for marker in [
        "text cues",
        "manual emotion labels",
        "optional acoustic features",
        "optional ASR confidence",
        "optional speech rate / pauses",
        "optional interruption markers",
        "Do not claim accuracy until evaluated.",
    ]:
        require(marker.lower() in normalized, f"emotion plan missing marker: {marker}")
    return len(REQUIRED_EMOTION_LABELS)


def validate_persuasion_taxonomy() -> int:
    text = read_text(OUT_DIR / "05_persuasion_strategy_taxonomy.md")
    normalized = normalize(text)
    missing = [strategy for strategy in REQUIRED_PERSUASION_STRATEGIES if strategy not in normalized]
    require(not missing, f"persuasion taxonomy missing strategies: {', '.join(missing)}")
    missing_forbidden = [item for item in FORBIDDEN_PERSUASION if item not in normalized]
    require(not missing_forbidden, f"persuasion taxonomy missing forbidden items: {', '.join(missing_forbidden)}")
    return len(REQUIRED_PERSUASION_STRATEGIES)


def validate_buyer_state_taxonomy() -> int:
    text = read_text(OUT_DIR / "06_buyer_state_taxonomy.md")
    normalized = normalize(text)
    missing = [state for state in REQUIRED_BUYER_STATES if state not in normalized]
    require(not missing, f"buyer state taxonomy missing states: {', '.join(missing)}")
    return len(REQUIRED_BUYER_STATES)


def validate_metrics_mapping() -> None:
    text = read_text(OUT_DIR / "07_outcome_metrics_mapping.md")
    normalized = normalize(text)
    missing = [metric for metric in REQUIRED_METRICS if metric not in normalized]
    require(not missing, f"outcome metrics mapping missing metrics: {', '.join(missing)}")


def validate_placeholder_tables() -> int:
    text = read_text(OUT_DIR / "11_placeholder_result_tables.md")
    normalized = normalize(text)
    missing_tables = [table for table in PLACEHOLDER_TABLES if table.lower() not in normalized]
    require(not missing_tables, f"placeholder tables missing: {', '.join(missing_tables)}")
    marker_count = text.count(TEMPLATE_MARKER)
    require(marker_count >= len(PLACEHOLDER_TABLES), f"expected {len(PLACEHOLDER_TABLES)} template markers, found {marker_count}")
    return len(PLACEHOLDER_TABLES)


def validate_methodology_and_ethics() -> None:
    combined = "\n".join(
        read_text(OUT_DIR / filename)
        for filename in [
            "12_thesis_methodology_bridge.md",
            "13_limitations_and_ethics.md",
        ]
    )
    normalized = normalize(combined)
    for marker in [
        "ElevenLabs currently provides hosted voice-agent shell",
        "emotion detection may initially be manual",
        "real outbound calls are not enabled",
        "OpenAI campaign remains source-boundary benchmark",
        "no real customers in current phase",
        "no fake guarantees",
        "no manipulative persuasion",
        "hosted platform dependency",
        "manual evaluator bias",
        "synthetic-vs-real conversation gap",
    ]:
        require(marker.lower() in normalized, f"methodology/ethics missing marker: {marker}")


def validate_result_json(
    mapped_rq_count: int,
    schema_field_count: int,
    example_row_count: int,
    emotion_label_count: int,
    persuasion_strategy_count: int,
    buyer_state_count: int,
    placeholder_table_count: int,
) -> None:
    result = read_json(OUT_DIR / "result.json")
    require(result.get("checkpoint_id") == CHECKPOINT_ID, "result.json checkpoint_id mismatch")
    require(result.get("status") == "pass", "result.json status must be pass")
    require(result.get("proposal_rq_count") == 7, "result.json proposal_rq_count must be 7")
    require(result.get("mapped_rq_count") == mapped_rq_count, "result.json mapped_rq_count mismatch")
    require(result.get("easid_schema_field_count") == schema_field_count, "result.json easid_schema_field_count mismatch")
    require(result.get("synthetic_example_row_count") == example_row_count, "result.json synthetic_example_row_count mismatch")
    require(result.get("emotion_label_count") == emotion_label_count, "result.json emotion_label_count mismatch")
    require(
        result.get("persuasion_strategy_count") == persuasion_strategy_count,
        "result.json persuasion_strategy_count mismatch",
    )
    require(result.get("buyer_state_count") == buyer_state_count, "result.json buyer_state_count mismatch")
    require(
        result.get("placeholder_tables_created") == placeholder_table_count,
        "result.json placeholder_tables_created mismatch",
    )
    require(result.get("thesis_alignment_ready") is True, "result.json thesis_alignment_ready must be true")

    enabled = [flag for flag in FALSE_RESULT_FLAGS if result.get(flag) is not False]
    require(not enabled, f"unsafe or fabricated result flags must be false: {', '.join(enabled)}")


def validate_no_side_effect_claims() -> None:
    combined = "\n".join(read_text(OUT_DIR / filename) for filename in REQUIRED_FILENAMES)
    normalized = normalize(combined)
    forbidden_claims = [
        "fabricated_results_present: true",
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
    require(not leaked, f"side-effect, fabricated-result, or live-readiness claim present: {', '.join(leaked)}")


def main() -> int:
    validate_required_files()
    mapped_rq_count = validate_research_question_mapping()
    schema_field_count = validate_schema()
    example_row_count = validate_examples()
    emotion_label_count = validate_emotion_plan()
    persuasion_strategy_count = validate_persuasion_taxonomy()
    buyer_state_count = validate_buyer_state_taxonomy()
    validate_metrics_mapping()
    placeholder_table_count = validate_placeholder_tables()
    validate_methodology_and_ethics()
    validate_result_json(
        mapped_rq_count,
        schema_field_count,
        example_row_count,
        emotion_label_count,
        persuasion_strategy_count,
        buyer_state_count,
        placeholder_table_count,
    )
    validate_no_side_effect_claims()

    print(
        f"PASS {CHECKPOINT_ID}: {mapped_rq_count} RQs, "
        f"{schema_field_count} EASID fields, {example_row_count} synthetic rows, "
        f"{placeholder_table_count} placeholder tables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
