#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from prosody_quality_common import base_boundary_flags, load_json, write_json, write_report


ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "runtime" / "audio_backends"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
PROTOTYPE_DIR = GENERATED_DIR / "ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001"
AUDIT_DIR = GENERATED_DIR / "ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001"
DECISION_DIR = GENERATED_DIR / "ELEVENLABS-PROSODY-MAPPING-DECISION-001"
PROTOTYPE_RESULT = PROTOTYPE_DIR / "result.json"
TAXONOMY_AUDIT = GENERATED_DIR / "PROSODY-TAXONOMY-QUALITY-AUDIT-001" / "result.json"
MAPPING_AUDIT = GENERATED_DIR / "SALES-PROSODY-MAPPING-QUALITY-AUDIT-001" / "result.json"
DRY_RUN_AUDIT = GENERATED_DIR / "PROSODY-PLANNER-DRY-RUN-AUDIT-001" / "result.json"

RAW_TAG_RE = re.compile(r"\[[^\]\n]{2,80}\]")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
INTERNAL_LABEL_RE = re.compile(
    r"\b(?:clarity|tone|sales|source|unsafe|emotion_response|pacing|pause|repair|boundary|trust|closing|plan)\.[a-z0-9_.-]+",
    re.IGNORECASE,
)
INTERNAL_LANGUAGE_RE = re.compile(r"\b(classifier|confidence score|internal label|prosody label|fish tag|mapping layer)\b", re.IGNORECASE)
UNSAFE_STYLE_RE = re.compile(r"\b(manipulative|fake laughter|pressure them|must buy|guarantee outcome|force the buyer)\b", re.IGNORECASE)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i have sent|i sent|i booked|i scheduled|i added you|i updated your crm)\b", re.IGNORECASE)
OVEREXCITED_RE = re.compile(r"\b(amazing|incredible|game changer|unbeatable)\b|!{2,}", re.IGNORECASE)
URGENCY_RE = re.compile(r"\b(last chance|limited time|buy now|today only|act now)\b", re.IGNORECASE)
OVERCLAIM_RE = re.compile(r"\b(official partner|official representative|guaranteed|guarantee results|approved reseller)\b", re.IGNORECASE)


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def question_count(text: str) -> int:
    return text.count("?")


def context_name(example: dict[str, Any]) -> str:
    context = example.get("input_context", {})
    if isinstance(context, dict):
        return str(context.get("name") or context.get("case_id") or example.get("example_id") or "")
    return str(example.get("example_id") or "")


def has_boundary_context(example: dict[str, Any]) -> bool:
    context = example.get("input_context", {})
    return isinstance(context, dict) and context.get("safety_boundary_detected") is True


def source_affiliation_overclaims(text: str) -> bool:
    if not OVERCLAIM_RE.search(text):
        return False
    lowered = text.lower()
    negated_markers = (
        "not claiming",
        "not presenting myself as an official representative",
        "not an official representative",
        "not an official statement",
        "general guidance",
    )
    return not any(marker in lowered for marker in negated_markers)


def classify_example(example: dict[str, Any]) -> dict[str, Any]:
    shaped = str(example.get("shaped_text") or "")
    style = str(example.get("style_prompt_hint") or "")
    settings = example.get("voice_settings_hint")
    name = context_name(example).lower()
    context = example.get("input_context", {}) if isinstance(example.get("input_context"), dict) else {}
    reasons: list[str] = []
    blocking = False
    warning = False

    checks = {
        "shaped_text_contains_raw_fish_tags": bool(RAW_TAG_RE.search(shaped)),
        "shaped_text_contains_internal_labels": bool(INTERNAL_LABEL_RE.search(shaped) or INTERNAL_LANGUAGE_RE.search(shaped)),
        "style_prompt_contains_unsafe_instruction": bool(UNSAFE_STYLE_RE.search(style)),
        "voice_settings_hint_missing": not isinstance(settings, dict) or not settings,
        "provider_call_required": example.get("provider_call_required") is not False,
        "live_wiring_allowed": example.get("live_wiring_allowed") is not False,
        "terminal_close_asks_new_question": any(marker in name for marker in ("terminal acceptance", "no-fit close", "final goodbye", "goodbye after no")) and "?" in shaped,
        "boundary_response_continues_pressure": has_boundary_context(example) and bool(re.search(r"\b(sign up|upgrade|buy|deal|still should)\b", shaped, re.IGNORECASE)),
        "already_told_you_repeats_question": context.get("buyer_said_already_told_you") is True and "?" in shaped,
        "asr_uncertainty_uses_internal_confidence_language": context.get("asr_uncertainty_detected") is True and bool(re.search(r"\b(asr|classifier|confidence)\b", shaped, re.IGNORECASE)),
        "source_affiliation_overclaims": ("source" in name or context.get("objection_type") == "source_affiliation") and source_affiliation_overclaims(shaped),
        "fake_side_effect": bool(FAKE_SIDE_EFFECT_RE.search(shaped)),
        "raw_url_speech": bool(URL_RE.search(shaped)),
        "overexcited_sales_voice": bool(OVEREXCITED_RE.search(shaped) or OVEREXCITED_RE.search(style)),
        "manipulative_urgency": bool(URGENCY_RE.search(shaped) or URGENCY_RE.search(style)),
        "too_long_for_phone": word_count(shaped) > 42,
        "too_many_questions": question_count(shaped) > 1,
        "unnatural_text_shape": "  " in shaped or "..." in shaped or shaped.count(";") > 1,
    }

    blocking_keys = {
        "shaped_text_contains_raw_fish_tags",
        "shaped_text_contains_internal_labels",
        "style_prompt_contains_unsafe_instruction",
        "provider_call_required",
        "live_wiring_allowed",
        "fake_side_effect",
        "raw_url_speech",
        "manipulative_urgency",
    }
    warning_keys = set(checks) - blocking_keys
    for key, value in checks.items():
        if not value:
            continue
        reasons.append(key)
        if key in blocking_keys:
            blocking = True
        elif key in warning_keys:
            warning = True

    if blocking:
        status = "fail"
    elif warning:
        status = "warning"
    else:
        status = "pass"
        reasons.append("no quality issue detected")
    return {
        "example_id": example.get("example_id"),
        "input_context": example.get("input_context"),
        "status": status,
        "reasons": reasons,
        "provider_call_required": False,
        "live_wiring_allowed": False,
        **checks,
    }


def count_field(classifications: list[dict[str, Any]], key: str) -> int:
    return sum(1 for item in classifications if item.get(key) is True)


def write_decision(audit: dict[str, Any]) -> dict[str, Any]:
    blocking_failure_count = int(audit.get("blocking_failure_count") or 0)
    warning_count = int(audit.get("warning_count") or 0)
    if blocking_failure_count:
        recommendation = "Mapping cleanup before any provider test; blockers include raw tags, internal labels, provider-call requirement, or live wiring risk."
        human_review_needed = True
        future_provider_sample_generation_recommended = False
    elif warning_count:
        recommendation = "No-provider human review of shaped text before any future provider test."
        human_review_needed = True
        future_provider_sample_generation_recommended = False
    else:
        recommendation = "Future ElevenLabs offline sample generation phase only after explicit provider-call approval; not current phase."
        human_review_needed = False
        future_provider_sample_generation_recommended = True

    decision = {
        "experiment_id": "ELEVENLABS-PROSODY-MAPPING-DECISION-001",
        "phase": "4I5",
        "status": "pass",
        "recommendation": recommendation,
        "human_review_needed": human_review_needed,
        "future_provider_sample_generation_recommended": future_provider_sample_generation_recommended,
        "live_wiring_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "does_not_claim_live_readiness": True,
        "provider_test_current_phase_allowed": False,
        "provider_test_future_phase_requires_explicit_approval": True,
        "decision_inputs": {
            "prototype": "research/experiments/generated/ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001/result.json",
            "quality_audit": "research/experiments/generated/ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001/result.json",
        },
        "quality_summary": {
            "example_count": audit.get("example_count"),
            "status_counts": audit.get("status_counts"),
            "blocking_failure_count": blocking_failure_count,
            "warning_count": warning_count,
        },
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(DECISION_DIR / "result.json", decision)
    write_report(
        DECISION_DIR / "report.md",
        "ELEVENLABS-PROSODY-MAPPING-DECISION-001",
        [
            f"Status: {decision['status']}",
            f"- Recommendation: {recommendation}",
            f"- Human review needed: {human_review_needed}",
            f"- Future provider sample generation recommended: {future_provider_sample_generation_recommended}",
            "- Provider calls made: false",
            "- ElevenLabs calls made: false",
            "- Live wiring allowed: false",
            "- Runtime behavior changed: false",
            "- Response text changed: false",
        ],
    )
    return decision


def main() -> int:
    prototype = load_json(PROTOTYPE_RESULT)
    for path in (TAXONOMY_AUDIT, MAPPING_AUDIT, DRY_RUN_AUDIT):
        load_json(path)
    examples = prototype.get("examples", [])
    if not isinstance(examples, list):
        raise ValueError("prototype examples must be a list")

    classifications = [classify_example(example) for example in examples]
    status_counter = Counter(str(item.get("status")) for item in classifications)
    status_counts = {
        "pass": status_counter.get("pass", 0),
        "warning": status_counter.get("warning", 0),
        "fail": status_counter.get("fail", 0),
        "needs_human_review": status_counter.get("needs_human_review", 0),
    }
    blocking_fields = [
        "shaped_text_contains_raw_fish_tags",
        "shaped_text_contains_internal_labels",
        "style_prompt_contains_unsafe_instruction",
        "provider_call_required",
        "live_wiring_allowed",
        "fake_side_effect",
        "raw_url_speech",
        "manipulative_urgency",
    ]
    warning_fields = [
        "voice_settings_hint_missing",
        "terminal_close_asks_new_question",
        "boundary_response_continues_pressure",
        "already_told_you_repeats_question",
        "asr_uncertainty_uses_internal_confidence_language",
        "source_affiliation_overclaims",
        "overexcited_sales_voice",
        "too_long_for_phone",
        "too_many_questions",
        "unnatural_text_shape",
    ]
    blocking_failure_count = sum(count_field(classifications, key) for key in blocking_fields)
    warning_count = sum(count_field(classifications, key) for key in warning_fields)
    audit = {
        "experiment_id": "ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001",
        "phase": "4I5",
        "status": "pass" if blocking_failure_count == 0 else "fail",
        "example_count": len(examples),
        "status_counts": status_counts,
        "blocking_failure_count": blocking_failure_count,
        "warning_count": warning_count,
        "shaped_text_contains_raw_fish_tags_count": count_field(classifications, "shaped_text_contains_raw_fish_tags"),
        "shaped_text_contains_internal_labels_count": count_field(classifications, "shaped_text_contains_internal_labels"),
        "style_prompt_contains_unsafe_instruction_count": count_field(classifications, "style_prompt_contains_unsafe_instruction"),
        "voice_settings_hint_missing_count": count_field(classifications, "voice_settings_hint_missing"),
        "provider_call_required_count": count_field(classifications, "provider_call_required"),
        "live_wiring_allowed_count": count_field(classifications, "live_wiring_allowed"),
        "terminal_close_asks_new_question_count": count_field(classifications, "terminal_close_asks_new_question"),
        "boundary_response_continues_pressure_count": count_field(classifications, "boundary_response_continues_pressure"),
        "already_told_you_repeats_question_count": count_field(classifications, "already_told_you_repeats_question"),
        "asr_uncertainty_uses_internal_confidence_language_count": count_field(classifications, "asr_uncertainty_uses_internal_confidence_language"),
        "source_affiliation_overclaims_count": count_field(classifications, "source_affiliation_overclaims"),
        "fake_side_effect_count": count_field(classifications, "fake_side_effect"),
        "raw_url_speech_count": count_field(classifications, "raw_url_speech"),
        "overexcited_sales_voice_count": count_field(classifications, "overexcited_sales_voice"),
        "manipulative_urgency_count": count_field(classifications, "manipulative_urgency"),
        "too_long_for_phone_count": count_field(classifications, "too_long_for_phone"),
        "too_many_questions_count": count_field(classifications, "too_many_questions"),
        "unnatural_text_shape_count": count_field(classifications, "unnatural_text_shape"),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "fish_inference_performed": False,
        "liquid_inference_performed": False,
        "kokoro_inference_performed": False,
        "local_model_generation_made": False,
        "ollama_generation_made": False,
        "training_performed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "boundary_flags": base_boundary_flags(),
        "example_classifications": classifications,
    }
    write_json(AUDIT_DIR / "result.json", audit)
    write_report(
        AUDIT_DIR / "report.md",
        "ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001",
        [
            f"Status: {audit['status']}",
            f"- Examples audited: {len(examples)}",
            f"- Status counts: {dict(status_counts)}",
            f"- Blocking failure count: {blocking_failure_count}",
            f"- Warning count: {warning_count}",
            f"- Raw Fish tag leakage: {audit['shaped_text_contains_raw_fish_tags_count']}",
            f"- Internal label leakage: {audit['shaped_text_contains_internal_labels_count']}",
            f"- Provider call required: {audit['provider_call_required_count']}",
            f"- Live wiring allowed: {audit['live_wiring_allowed_count']}",
        ],
    )
    decision = write_decision(audit)
    print(
        json.dumps(
            {
                "status": audit["status"],
                "example_count": len(examples),
                "status_counts": status_counts,
                "blocking_failure_count": blocking_failure_count,
                "warning_count": warning_count,
                "decision": decision["recommendation"],
            },
            indent=2,
        )
    )
    return 0 if blocking_failure_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
