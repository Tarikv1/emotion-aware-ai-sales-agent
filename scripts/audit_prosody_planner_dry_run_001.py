#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from prosody_quality_common import (
    DRY_RUN_AUDIT_DIR,
    ELEVENLABS_READINESS_DIR,
    ELEVENLABS_READINESS_PATH,
    MAPPING_AUDIT_DIR,
    QUALITY_DECISION_DIR,
    TAXONOMY_AUDIT_DIR,
    TAXONOMY_PATH,
    base_boundary_flags,
    label_index,
    load_json,
    status_counts,
    write_json,
    write_report,
)


def load_planner() -> Any:
    planner_path = Path(__file__).resolve().parents[1] / "runtime" / "audio_backends" / "prosody_planner.py"
    spec = importlib.util.spec_from_file_location("prosody_planner_dry_run", planner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import prosody planner")
    module = importlib.util.module_from_spec(spec)
    sys.modules["prosody_planner_dry_run"] = module
    spec.loader.exec_module(module)
    return module


def dry_run_contexts() -> list[dict[str, Any]]:
    base = [
        ("confused_plan", {"buyer_emotion": "confused", "buyer_confusion_level": "high", "sales_move": "plan_explanation"}),
        ("confused_price", {"buyer_emotion": "confused", "buyer_confusion_level": "high", "sales_move": "price_answer"}),
        ("skeptical_source", {"buyer_emotion": "skeptical", "buyer_skepticism_level": "high", "sales_move": "source_affiliation_answer"}),
        ("skeptical_competitor", {"buyer_emotion": "skeptical", "buyer_skepticism_level": "high", "objection_type": "competitor"}),
        ("impatient_price", {"buyer_emotion": "impatient", "buyer_friction_level": "medium", "sales_move": "price_answer"}),
        ("price_heavy_use", {"buyer_emotion": "price_sensitive", "buyer_engagement_level": "high", "sales_move": "recommendation", "objection_type": "price"}),
        ("price_low_budget", {"buyer_emotion": "price_sensitive", "buyer_friction_level": "high", "objection_type": "price"}),
        ("frustrated", {"buyer_emotion": "frustrated", "buyer_friction_level": "high"}),
        ("interested", {"buyer_emotion": "interested", "buyer_engagement_level": "high"}),
        ("disengaged", {"buyer_emotion": "disengaged", "buyer_engagement_level": "low"}),
        ("privacy", {"buyer_emotion": "skeptical", "objection_type": "privacy", "safety_boundary_detected": True}),
        ("already_told_you", {"buyer_emotion": "frustrated", "buyer_said_already_told_you": True}),
        ("buyer_correction", {"buyer_emotion": "neutral", "sales_move": "correction_repair"}),
        ("asr_uncertainty", {"buyer_emotion": "neutral", "asr_uncertainty_detected": True}),
        ("same_question", {"buyer_emotion": "confused", "sales_move": "repeat_answer"}),
        ("use_case", {"buyer_emotion": "neutral", "sales_move": "use_case_discovery"}),
        ("intensity", {"buyer_emotion": "neutral", "sales_move": "intensity_discovery"}),
        ("team_individual", {"buyer_emotion": "neutral", "sales_move": "team_clarification"}),
        ("recommendation", {"buyer_emotion": "interested", "sales_move": "recommendation", "decision_stage": "recommendation"}),
        ("plus_pro", {"buyer_emotion": "curious", "sales_move": "compare_plus_pro"}),
        ("pro_tier", {"buyer_emotion": "interested", "sales_move": "pro_tier_selection"}),
        ("no_fit", {"buyer_emotion": "neutral", "sales_move": "close", "close_readiness": "no_fit"}),
        ("terminal_acceptance", {"buyer_emotion": "interested", "sales_move": "close", "close_readiness": "accepted"}),
        ("boundary_no_email", {"buyer_emotion": "neutral", "safety_boundary_detected": True, "objection_type": "no_email"}),
        ("boundary_no_crm", {"buyer_emotion": "neutral", "safety_boundary_detected": True, "objection_type": "no_crm"}),
        ("boundary_no_calendar", {"buyer_emotion": "neutral", "safety_boundary_detected": True, "objection_type": "no_calendar"}),
        ("opening", {"buyer_emotion": "neutral", "sales_move": "opening_permission_check"}),
        ("barge_in", {"buyer_emotion": "impatient", "sales_move": "barge_in_recovery"}),
        ("not_using_ai", {"buyer_emotion": "neutral", "objection_type": "not_using_ai"}),
        ("many_tools", {"buyer_emotion": "skeptical", "objection_type": "using_chatgpt_and_other_tools"}),
        ("chatgpt_or_claude", {"buyer_emotion": "confused", "objection_type": "chatgpt_or_claude_uncertain"}),
        ("subscription_model", {"buyer_emotion": "confused", "sales_move": "subscription_vs_model"}),
        ("signup_path", {"buyer_emotion": "interested", "sales_move": "signup_path"}),
        ("upgrade_path", {"buyer_emotion": "interested", "sales_move": "upgrade_path"}),
        ("privacy_training", {"buyer_emotion": "skeptical", "sales_move": "privacy_training_answer"}),
        ("wrong_product", {"buyer_emotion": "confused", "sales_move": "wrong_product_repair"}),
        ("unsupported_claim", {"buyer_emotion": "skeptical", "sales_move": "unsupported_claim"}),
        ("final_goodbye", {"buyer_emotion": "neutral", "sales_move": "final_goodbye"}),
        ("api_vs_chatgpt", {"buyer_emotion": "confused", "sales_move": "api_boundary", "objection_type": "api_vs_chatgpt"}),
        ("business_enterprise", {"buyer_emotion": "interested", "sales_move": "enterprise_recommendation"}),
        ("free_enough", {"buyer_emotion": "neutral", "objection_type": "free_is_enough"}),
        ("too_busy", {"buyer_emotion": "impatient", "objection_type": "too_busy"}),
        ("anxious", {"buyer_emotion": "anxious", "buyer_friction_level": "medium"}),
        ("curious", {"buyer_emotion": "curious", "buyer_engagement_level": "high"}),
        ("annoyed", {"buyer_emotion": "annoyed", "buyer_friction_level": "high"}),
        ("direct_price_neutral", {"buyer_emotion": "neutral", "sales_move": "price_answer"}),
        ("competitor_neutral", {"buyer_emotion": "neutral", "objection_type": "competitor"}),
        ("source_neutral", {"buyer_emotion": "neutral", "sales_move": "source_affiliation_answer"}),
        ("plan_change", {"buyer_emotion": "interested", "sales_move": "upgrade_path", "decision_stage": "plan_change"}),
        ("team_no_team", {"buyer_emotion": "neutral", "sales_move": "team_clarification", "objection_type": "not_team"}),
        ("plan_explain_api", {"buyer_emotion": "confused", "sales_move": "subscription_vs_model", "objection_type": "api_boundary"}),
        ("low_budget_no_fit", {"buyer_emotion": "price_sensitive", "buyer_friction_level": "high", "sales_move": "close", "close_readiness": "no_fit"}),
        ("close_soft", {"buyer_emotion": "interested", "sales_move": "close", "close_readiness": "ready"}),
        ("boundary_stop", {"buyer_emotion": "annoyed", "safety_boundary_detected": True, "objection_type": "stop"}),
        ("privacy_boundary", {"buyer_emotion": "anxious", "safety_boundary_detected": True, "objection_type": "privacy"}),
        ("repeat_price", {"buyer_emotion": "confused", "sales_move": "repeat_answer", "objection_type": "price"}),
        ("current_tool_gap", {"buyer_emotion": "skeptical", "objection_type": "already_have_tool"}),
        ("source_price", {"buyer_emotion": "skeptical", "sales_move": "price_answer", "objection_type": "source_affiliation"}),
        ("enterprise_security", {"buyer_emotion": "skeptical", "sales_move": "enterprise_recommendation", "objection_type": "privacy"}),
        ("goodbye_after_no", {"buyer_emotion": "neutral", "sales_move": "final_goodbye", "close_readiness": "no_fit"}),
    ]
    contexts = []
    for name, context in base[:60]:
        item = {
            "case_id": f"dry_run.{len(contexts)+1:03d}.{name}",
            "backend_id": "elevenlabs_existing_provider",
            **context,
        }
        contexts.append(item)
    return contexts


def classify_case(context: dict[str, Any], plan: dict[str, Any], labels_by_id: dict[str, dict[str, Any]]) -> tuple[str, list[str], bool, bool]:
    selected = plan.get("selected_prosody_labels", [])
    unsafe_selected = any(labels_by_id.get(label_id, {}).get("category") == "unsafe_or_disallowed" for label_id in selected)
    loop_risk = False
    reasons: list[str] = []
    if unsafe_selected:
        reasons.append("unsafe label selected")
    if plan.get("spoken_text_tag_injection_allowed") is not False:
        reasons.append("spoken text tag injection not blocked")
    if plan.get("live_runtime_wiring_changed") is not False:
        reasons.append("live runtime wiring changed")
    if not plan.get("matched_rule_ids"):
        reasons.append("no composition rule matched")
    if context.get("close_readiness") == "accepted" and (
        any(label_id.startswith("clarify.") for label_id in selected) or "sales.advance_after_answer" in selected
    ):
        loop_risk = True
        reasons.append("terminal acceptance may continue selling")
    if context.get("buyer_said_already_told_you") is True and any(label_id.startswith("clarify.") for label_id in selected):
        loop_risk = True
        reasons.append("already-told-you case may repeat clarification")
    if context.get("sales_move") == "price_answer" and "clarify.price_question" in selected:
        loop_risk = True
        reasons.append("price answer may repeat price qualification")
    if len(selected) > 10:
        reasons.append("too many labels selected")
    if unsafe_selected or plan.get("spoken_text_tag_injection_allowed") is not False or plan.get("live_runtime_wiring_changed") is not False:
        return "fail", reasons, unsafe_selected, loop_risk
    if loop_risk or not plan.get("matched_rule_ids") or len(selected) > 10:
        return "warning", reasons, unsafe_selected, loop_risk
    return "pass", ["planner selected a bounded internal prosody plan"], unsafe_selected, loop_risk


def write_elevenlabs_readiness(taxonomy_audit: dict[str, Any], mapping_audit: dict[str, Any], dry_result: dict[str, Any]) -> dict[str, Any]:
    readiness = {
        "schema_version": 1,
        "readiness_id": "elevenlabs-prosody-mapping-readiness-001",
        "phase": "4I3",
        "current_voice_path": "ElevenLabs",
        "fish_tags_in_elevenlabs_text_allowed": False,
        "current_integration_status": "not_wired",
        "future_mapping_layers": [
            "text shaping",
            "punctuation/pause shaping",
            "sentence length control",
            "optional style prompt if supported",
            "optional voice settings if already available",
        ],
        "disallowed": [
            "raw bracket tags",
            "fake emotions",
            "fake laughter",
            "manipulative urgency",
            "internal policy language",
            "unsupported claims",
        ],
        "required_future_gate_before_live": [
            "sample generation",
            "listening review",
            "regression against current ElevenLabs behavior",
            "no raw tag leakage",
            "no response text behavior change unless explicitly approved",
        ],
        "quality_inputs": {
            "taxonomy_blocker_count": taxonomy_audit.get("blocker_count"),
            "mapping_failure_count": mapping_audit.get("failure_count"),
            "planner_failure_count": dry_result.get("dry_run_status_counts", {}).get("fail", 0),
        },
        "recommended_now": "plan_only_not_wired",
        "provider_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(ELEVENLABS_READINESS_PATH, readiness)
    result = {
        "experiment_id": "ELEVENLABS-PROSODY-MAPPING-READINESS-001",
        "phase": "4I3",
        "status": "pass",
        "plan": "runtime/audio_backends/elevenlabs_prosody_mapping_readiness.json",
        **readiness,
    }
    write_json(ELEVENLABS_READINESS_DIR / "result.json", result)
    write_report(
        ELEVENLABS_READINESS_DIR / "report.md",
        "ELEVENLABS-PROSODY-MAPPING-READINESS-001",
        [
            "Status: pass",
            "- current_voice_path: ElevenLabs",
            "- current_integration_status: not_wired",
            "- fish_tags_in_elevenlabs_text_allowed: false",
            "- future mapping must start with no-provider text/punctuation/sentence-shape evidence.",
            "- live mapping requires sample generation, listening review, regression, no tag leakage, and explicit approval for any response text change.",
        ],
    )
    return result


def write_quality_decision(taxonomy_audit: dict[str, Any], mapping_audit: dict[str, Any], dry_result: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    blocker_count = int(taxonomy_audit.get("blocker_count", 0)) + int(mapping_audit.get("failure_count", 0)) + int(dry_result.get("dry_run_status_counts", {}).get("fail", 0))
    warning_count = int(taxonomy_audit.get("warning_count", 0)) + int(mapping_audit.get("warning_count", 0)) + int(dry_result.get("dry_run_status_counts", {}).get("warning", 0))
    if blocker_count:
        recommendation = "taxonomy cleanup before integration"
        prototype_recommended = False
    elif warning_count:
        recommendation = "targeted taxonomy and mapping cleanup before any ElevenLabs mapping prototype"
        prototype_recommended = False
    else:
        recommendation = "ElevenLabs prosody mapping prototype, no provider calls"
        prototype_recommended = True
    decision = {
        "experiment_id": "PROSODY-TAXONOMY-QUALITY-DECISION-001",
        "phase": "4I3",
        "status": "pass",
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "quality_decision_recommendation": recommendation,
        "taxonomy_cleanup_needed": bool(blocker_count or warning_count),
        "elevenlabs_mapping_prototype_recommended": prototype_recommended,
        "live_wiring_allowed": False,
        "elevenlabs_calls_made": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "does_not_claim_live_readiness": True,
        "decision_inputs": {
            "taxonomy_audit": "research/experiments/generated/PROSODY-TAXONOMY-QUALITY-AUDIT-001/result.json",
            "mapping_audit": "research/experiments/generated/SALES-PROSODY-MAPPING-QUALITY-AUDIT-001/result.json",
            "planner_dry_run_audit": "research/experiments/generated/PROSODY-PLANNER-DRY-RUN-AUDIT-001/result.json",
            "elevenlabs_readiness": "research/experiments/generated/ELEVENLABS-PROSODY-MAPPING-READINESS-001/result.json",
        },
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(QUALITY_DECISION_DIR / "result.json", decision)
    write_report(
        QUALITY_DECISION_DIR / "report.md",
        "PROSODY-TAXONOMY-QUALITY-DECISION-001",
        [
            "Status: pass",
            f"- blocker_count: {blocker_count}",
            f"- warning_count: {warning_count}",
            f"- recommendation: {recommendation}",
            f"- taxonomy_cleanup_needed: {decision['taxonomy_cleanup_needed']}",
            f"- elevenlabs_mapping_prototype_recommended: {prototype_recommended}",
            "- live_wiring_allowed: false",
            "- response_text_changed: false",
            "- runtime_behavior_changed: false",
        ],
    )
    return decision


def main() -> int:
    planner = load_planner()
    taxonomy = load_json(TAXONOMY_PATH)
    labels_by_id = label_index(taxonomy)
    cases = []
    for context in dry_run_contexts():
        plan = planner.plan_prosody_for_sales_turn(context)
        status, reasons, unsafe_selected, loop_risk = classify_case(context, plan, labels_by_id)
        cases.append(
            {
                "case_id": context["case_id"],
                "input_context": context,
                "selected_labels": plan.get("selected_prosody_labels", []),
                "selected_composition_rule": plan.get("matched_rule_ids", []),
                "backend_hints": plan.get("backend_hints", {}),
                "spoken_text_tag_injection_allowed": plan.get("spoken_text_tag_injection_allowed"),
                "unsafe_labels_selected": unsafe_selected,
                "loop_risk_labels_selected": loop_risk,
                "status": status,
                "reason": reasons,
            }
        )

    counts = status_counts(cases)
    dry_result = {
        "experiment_id": "PROSODY-PLANNER-DRY-RUN-AUDIT-001",
        "phase": "4I3",
        "status": "pass" if counts["fail"] == 0 else "fail",
        "case_count": len(cases),
        "dry_run_status_counts": counts,
        "cases": cases,
        "unsafe_label_case_count": sum(1 for item in cases if item["unsafe_labels_selected"]),
        "loop_risk_case_count": sum(1 for item in cases if item["loop_risk_labels_selected"]),
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "spoken_text_tag_injection_allowed": False,
        "provider_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(DRY_RUN_AUDIT_DIR / "result.json", dry_result)
    write_report(
        DRY_RUN_AUDIT_DIR / "report.md",
        "PROSODY-PLANNER-DRY-RUN-AUDIT-001",
        [
            f"Status: {dry_result['status']}",
            f"- case_count: {len(cases)}",
            f"- dry_run_status_counts: {counts}",
            f"- unsafe_label_case_count: {dry_result['unsafe_label_case_count']}",
            f"- loop_risk_case_count: {dry_result['loop_risk_case_count']}",
            "- No provider calls, audio generation, Fish inference, Liquid inference, Kokoro inference, live wiring, runtime behavior change, or response text change.",
        ],
    )

    taxonomy_audit = load_json(TAXONOMY_AUDIT_DIR / "result.json")
    mapping_audit = load_json(MAPPING_AUDIT_DIR / "result.json")
    readiness = write_elevenlabs_readiness(taxonomy_audit, mapping_audit, dry_result)
    write_quality_decision(taxonomy_audit, mapping_audit, dry_result, readiness)
    print(__import__("json").dumps(dry_result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
