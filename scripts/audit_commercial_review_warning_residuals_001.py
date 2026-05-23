"""Audit residual commercial review warnings and ASR matrix findings.

This script is evidence-only. It classifies existing generated warning
instances so runtime patches stay scoped to true defects instead of raw warning
counts.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "COMMERCIAL-REVIEW-WARNING-RESIDUAL-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
REVIEW_PACKET = ROOT / "research" / "experiments" / "generated" / "COMMERCIAL-SALES-CONVERSATION-REVIEW-001" / "review_packet.json"
CROSS_CAMPAIGN = ROOT / "research" / "experiments" / "generated" / "UNIVERSAL-BUYER-MOVES-CROSS-CAMPAIGN-001" / "result.json"

TARGET_WARNINGS = {
    "no_acknowledgement",
    "over_deferential_stop_offer",
    "repeated_full_menu",
}
STOP_MOVES = {"stop_request", "permission_to_continue_denied"}
FRICTION_MOVES = {"emotional_frustration", "abusive_or_hostile_buyer", "language_mismatch"}
DIRECT_QUESTION_MOVES = {
    "product_detail_question",
    "what_problem_do_you_solve",
    "why_should_i_care",
    "what_makes_you_different",
    "who_is_this_for",
    "is_this_worth_my_time",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in patterns)


def classify_warning(conversation: dict[str, Any], turn: dict[str, Any], warning: str) -> str:
    arc = str(conversation.get("arc_type") or "")
    buyer = str(turn.get("buyer_utterance") or "").lower()
    response = str(turn.get("final_response") or "")
    lower = response.lower()
    frame = turn.get("universal_policy_frame") or {}
    buyer_move = str(frame.get("buyer_move_id") or "")
    source = str((turn.get("selected_action") or {}).get("source") or "")

    if buyer_move in STOP_MOVES or arc == "no_fit_stop" or contains_any(
        buyer,
        ("not interested", "stop calling", "don't want to continue", "do not want to continue"),
    ):
        return "intentional_no_fit_or_stop"
    if buyer_move in FRICTION_MOVES or contains_any(buyer, ("annoying", "frustrating", "speak english")):
        return "intentional_friction_deescalation"
    if buyer_move == "asr_garbled_or_low_confidence":
        if contains_any(lower, ("repeat", "rephrase", "misheard", "caught")):
            return "false_positive_warning"
        return "asr_residual_defect"
    if warning == "repeated_full_menu" and (
        arc == "confusion_loop_resistance"
        or buyer_move in {"confusion_not_clear", "already_answered_challenge"}
        or source == "pre_speech_conversation_stability_guard"
    ):
        return "confusion_loop_defect"
    if warning == "repeated_full_menu" and buyer_move in DIRECT_QUESTION_MOVES:
        return "direct_question_answer_quality_defect"
    if warning == "repeated_full_menu":
        return "true_sales_defect"
    if warning == "no_acknowledgement" and buyer_move in DIRECT_QUESTION_MOVES:
        if not contains_any(lower, ("which part should i check", "premium, coverage", "manual work, integration")):
            return "false_positive_warning"
        return "direct_question_answer_quality_defect"
    if warning == "over_deferential_stop_offer" and buyer_move in {
        "why_should_i_care",
        "is_this_worth_my_time",
        "no_clear_need",
        "timing_objection",
        "buyer_defers_to_later",
    }:
        return "needs_human_sales_review"
    if warning == "no_acknowledgement" and buyer_move in {
        "callback_time_provided",
        "appointment_time_confirmed",
        "send_info_request",
    }:
        return "false_positive_warning"
    if warning == "over_deferential_stop_offer":
        return "needs_human_sales_review"
    return "false_positive_warning"


def classify_asr_residual(result: dict[str, Any]) -> str:
    transcript = str(result.get("transcript") or "").lower()
    campaign = str(result.get("campaign") or "")
    move = str(result.get("actual_buyer_move_id") or "")
    response = str(result.get("final_response") or "").lower()
    failures = {str(item.get("failure_type") or "") for item in result.get("failures") or []}

    if move == "asr_garbled_or_low_confidence" and not contains_any(response, ("repeat", "rephrase", "misheard", "caught")):
        return "true_asr_repair_defect"
    if transcript == "yeah that would be good":
        return "clean_control_context_missing"
    if transcript == "repair timings are usually pretty long" and campaign != "synthetic-automotive-service-review":
        return "out_of_campaign_pain_correctly_rejected_but_bad_response"
    if "asr_garble_not_repaired" in failures:
        return "true_asr_repair_defect"
    return "false_positive"


def commercial_warning_instances(packet: dict[str, Any]) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []
    for conversation in packet.get("conversations") or []:
        for turn in conversation.get("turns") or []:
            for warning in turn.get("mechanical_warning_flags") or []:
                if warning not in TARGET_WARNINGS:
                    continue
                classification = classify_warning(conversation, turn, warning)
                instances.append(
                    {
                        "conversation_id": conversation.get("conversation_id"),
                        "campaign_id": conversation.get("campaign_id"),
                        "arc_type": conversation.get("arc_type"),
                        "turn_index": turn.get("turn_index"),
                        "buyer_utterance": turn.get("buyer_utterance"),
                        "warning": warning,
                        "classification": classification,
                        "buyer_move_id": (turn.get("universal_policy_frame") or {}).get("buyer_move_id"),
                        "selected_action_source": (turn.get("selected_action") or {}).get("source"),
                        "final_response": turn.get("final_response"),
                    }
                )
    return instances


def asr_residual_instances(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    instances: list[dict[str, Any]] = []
    for result in matrix.get("results") or []:
        if not result.get("failures"):
            continue
        if result.get("buyer_move_category") != "asr_repair":
            continue
        classification = classify_asr_residual(result)
        instances.append(
            {
                "campaign": result.get("campaign"),
                "transcript": result.get("transcript"),
                "context": result.get("context"),
                "classification": classification,
                "actual_buyer_move_id": result.get("actual_buyer_move_id"),
                "recognition_reason": result.get("recognition_reason"),
                "failure_types": [item.get("failure_type") for item in result.get("failures") or []],
                "final_response": result.get("final_response"),
            }
        )
    return instances


def count_by(items: list[dict[str, Any]], *keys: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in items:
        counter[" / ".join(str(item.get(key) or "") for key in keys)] += 1
    return dict(counter.most_common())


def build_result() -> dict[str, Any]:
    packet = load_json(REVIEW_PACKET)
    matrix = load_json(CROSS_CAMPAIGN)
    warnings = commercial_warning_instances(packet)
    asr = asr_residual_instances(matrix)
    true_warning_defects = [
        item
        for item in warnings
        if item["classification"]
        in {
            "true_sales_defect",
            "asr_residual_defect",
            "direct_question_answer_quality_defect",
            "confusion_loop_defect",
        }
    ]
    true_asr_defects = [item for item in asr if item["classification"] == "true_asr_repair_defect"]
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass",
        "runtime_behavior_changed": False,
        "source_files": {
            "commercial_review_packet": REVIEW_PACKET.as_posix(),
            "cross_campaign_matrix": CROSS_CAMPAIGN.as_posix(),
        },
        "commercial_packet_warning_counts": packet.get("mechanical_warning_counts") or {},
        "commercial_warning_instance_count": len(warnings),
        "commercial_warning_classification_counts": count_by(warnings, "warning", "classification"),
        "commercial_warning_classification_counts_by_class": count_by(warnings, "classification"),
        "true_sales_defect_count": len(true_warning_defects),
        "true_sales_defects": true_warning_defects[:20],
        "false_positive_or_intentional_examples": [
            item
            for item in warnings
            if item["classification"]
            in {"false_positive_warning", "intentional_no_fit_or_stop", "intentional_friction_deescalation"}
        ][:20],
        "asr_residual_count": len(asr),
        "asr_residual_classification_counts": count_by(asr, "classification"),
        "true_asr_repair_defect_count": len(true_asr_defects),
        "asr_residuals": asr,
        "recommended_patch_scope": recommended_patch_scope(true_warning_defects, asr),
    }
    return result


def recommended_patch_scope(true_warning_defects: list[dict[str, Any]], asr: list[dict[str, Any]]) -> list[str]:
    scope: list[str] = []
    classifications = {item.get("classification") for item in asr}
    warning_classes = {item.get("classification") for item in true_warning_defects}
    if "true_asr_repair_defect" in classifications:
        scope.append("Ensure recognized ASR garble always renders repeat/rephrase repair.")
    if "clean_control_context_missing" in classifications:
        scope.append("Treat unsupported positive control replies as permission/acknowledgement, not menu fallback.")
    if "out_of_campaign_pain_correctly_rejected_but_bad_response" in classifications:
        scope.append("Render one scope/relevance clarification for out-of-campaign pain phrases.")
    if "confusion_loop_defect" in warning_classes:
        scope.append("Recognize already-asked challenges and prevent stability guard menu takeover.")
    if not scope:
        scope.append("No runtime patch recommended; update warning classification only.")
    return scope


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## 1. Summary",
        "Audited commercial packet warnings and cross-campaign ASR residuals before runtime patching.",
        "",
        "## 2. Commercial Packet Warning Counts",
    ]
    for warning, count in sorted((result.get("commercial_packet_warning_counts") or {}).items()):
        if warning in TARGET_WARNINGS:
            lines.append(f"- {warning}: {count}")
    lines.extend(["", "## 3. Classification Counts By Warning Type"])
    for key, count in result["commercial_warning_classification_counts"].items():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## 4. True Sales Defects"])
    if result["true_sales_defects"]:
        for item in result["true_sales_defects"][:10]:
            lines.append(
                f"- {item['campaign_id']} | {item['arc_type']} | {item['buyer_utterance']} | "
                f"{item['warning']} -> {item['classification']} | source={item['selected_action_source']}"
            )
    else:
        lines.append("- None from the audited commercial warning instances.")
    lines.extend(["", "## 5. False Positives / Intentional Warnings"])
    for item in result["false_positive_or_intentional_examples"][:10]:
        lines.append(
            f"- {item['campaign_id']} | {item['arc_type']} | {item['buyer_utterance']} | "
            f"{item['warning']} -> {item['classification']}"
        )
    lines.extend(["", "## 6. ASR Residual Classification"])
    for key, count in result["asr_residual_classification_counts"].items():
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## 7. Recommended Patch Scope"])
    for item in result["recommended_patch_scope"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 8. Whether Runtime Behavior Changed", "- No. This audit is read-only."])
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    result = build_result()
    write_evidence(result)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "commercial_warning_instance_count": result["commercial_warning_instance_count"],
                "true_sales_defect_count": result["true_sales_defect_count"],
                "asr_residual_count": result["asr_residual_count"],
                "true_asr_repair_defect_count": result["true_asr_repair_defect_count"],
                "output_dir": OUT_DIR.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
