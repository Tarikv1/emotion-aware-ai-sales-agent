#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from prod_050_safe_call_control_softening_regression import PROTECTED_BOUNDARY_SPECS
from prod_045_core_sales_policy_regression_rerun import TEST_CAMPAIGN
from run_realtime_turn_simulation import build_runtime_decision


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-051-safe-call-control-runtime-update"
CHECKPOINT_NAME = "Safe Call-Control Runtime Update"
SOURCE_CHECKPOINT_ID = "PROD-050-safe-call-control-softening-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

PROD_050_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
PROD_053E_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-053E-english-runtime-wording-patch"
SOURCE_FILES = {
    "prod_050_result": PROD_050_DIR / "result.json",
    "prod_050_cases": PROD_050_DIR / "softening_regression_cases.json",
    "prod_050_results": PROD_050_DIR / "softening_regression_results.json",
    "prod_049_result": ROOT / "research" / "experiments" / "generated" / "PROD-049-safe-end-call-bridge-continue-review" / "result.json",
    "prod_048c_result": ROOT / "research" / "experiments" / "generated" / "PROD-048C-german-wording-feedback-patch" / "result.json",
    "prod_047_result": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046_result": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
}

SELECTED_DIFFICULTIES = {
    "price-first-direct",
    "written-info-request",
    "stakeholder-review",
    "partner-review",
}

BOUNDARY_FLAGS = {
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
}

PRESSURE_MARKERS = [
    "must decide",
    "only available today",
    "last chance",
    "forced appointment",
    "keep selling",
    "ignore your cancellation",
    "nur heute verfügbar",
    "letzte chance",
]
PAYMENT_COLLECTION_MARKERS = ["collect payment", "payment now", "pay now", "card number", "zahlung einziehen"]
CONTRACT_SIGNING_MARKERS = ["sign a contract", "contract today", " unterschreiben", "vertragsabschluss jetzt"]
UNSUPPORTED_CLAIM_MARKERS = ["guaranteed roi", "fully compliant", "guarantee approval", "garantierter erfolg"]
TERMINAL_CLOSING_MARKERS = ["leave it there", "belasse es dabei", "goodbye", "auf wiederhören", "hang up", "end the call"]
INTERNAL_JARGON_MARKERS = [
    "approved",
    "campaign",
    "sale-ready",
    "sales path",
    "route this",
    "log this",
    "handoff",
    "freigegeben",
    "verkaufsteil",
]
LOW_PRESSURE_CONTINUATION_MARKERS = {
    "en": ["if useful", "if it helps", "so it is useful", "so it's useful", "so it is more useful", "so it's more useful", "no decision today", "no commitment today", "take a look"],
    "de": ["wenn es hilfreich ist", "wenn es hilft"],
}
LANGUAGE_CORRUPTION_MARKERS = ["Ã", "Â", "�"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def source_statuses() -> dict[str, bool]:
    return {key: read_json(path).get("validation", {}).get("passed") is True for key, path in SOURCE_FILES.items() if key.endswith("_result")}


def contains_any(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def sentence_words(sentence: str) -> list[str]:
    return [word for word in re.split(r"\s+", sentence.strip()) if word]


def sentence_list(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def short_spoken_acknowledgement(sentence: str) -> bool:
    return sentence.strip().lower().rstrip(".!?") == "of course"


def naturalness_check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def direct_answer_or_acknowledgement(response: str, difficulty: str) -> bool:
    lowered = response.lower()
    if difficulty in {"stakeholder-review", "partner-review"} and "send it over" in lowered:
        return True
    if difficulty == "price-first-direct":
        return "29" in lowered and any(marker in lowered for marker in ("per user", "pro nutzer", "terms", "bedingungen"))
    if difficulty == "written-info-request":
        return any(marker in lowered for marker in ("summary", "zusammenfassung"))
    if difficulty == "stakeholder-review":
        return any(marker in lowered for marker in ("reviewer", "manager", "prüfende person", "review summary", "zusammenfassung"))
    if difficulty == "partner-review":
        return any(marker in lowered for marker in ("partner", "spouse", "mitentscheidende person", "zusammenfassung"))
    return False


def customer_move_fit(response: str, difficulty: str) -> bool:
    lowered = response.lower()
    if difficulty in {"stakeholder-review", "partner-review"} and "send it over" in lowered and "take a look" in lowered:
        return True
    if difficulty == "price-first-direct":
        return "included" in lowered or "enthalten" in lowered
    if difficulty == "written-info-request":
        return "main point" in lowered or "wichtigsten punkt" in lowered
    if difficulty == "stakeholder-review":
        return "reviewer" in lowered or "manager" in lowered or "key points" in lowered or "prüfende person" in lowered
    if difficulty == "partner-review":
        return "partner" in lowered or "spouse" in lowered or "key points" in lowered or "mitentscheidende person" in lowered
    return False


def spoken_sentence_shape(response: str) -> bool:
    sentences = sentence_list(response)
    if not 1 <= len(sentences) <= 4:
        return False
    return all((3 <= len(sentence_words(sentence)) <= 24) or short_spoken_acknowledgement(sentence) for sentence in sentences)


def later_promoted_responses_by_case_id() -> dict[str, str]:
    result_path = PROD_053E_DIR / "result.json"
    promoted_path = PROD_053E_DIR / "promoted_runtime_responses.json"
    if not result_path.exists() or not promoted_path.exists():
        return {}
    result = read_json(result_path)
    if result.get("validation", {}).get("passed") is not True:
        return {}
    payload = read_json(promoted_path)
    return {
        item["case_id"]: item["promoted_response"]
        for item in payload.get("items", [])
        if item.get("source_bucket") == "approved_as_written"
    }


def language_specific_naturalness(response: str, language: str) -> bool:
    if contains_any(response, LANGUAGE_CORRUPTION_MARKERS):
        return False
    lowered = response.lower()
    if language == "en":
        return not any(marker in lowered for marker in ("zusammenfassung", "schriftlich", "prüf"))
    if language == "de":
        return not any(marker in lowered for marker in ("one-page", "reviewer", "if useful"))
    return False


def score_naturalness(decision: dict[str, Any]) -> dict[str, Any]:
    response = decision["agent_response"]
    difficulty = decision["sales_difficulty"]
    language = decision["response_language"]
    checks = {
        "direct_answer_or_acknowledgement": naturalness_check(
            "direct_answer_or_acknowledgement",
            direct_answer_or_acknowledgement(response, difficulty),
            "Response must answer the explicit customer move before continuing.",
        ),
        "optional_low_pressure_continuation": naturalness_check(
            "optional_low_pressure_continuation",
            contains_any(response, LOW_PRESSURE_CONTINUATION_MARKERS[language]),
            "Continuation must be framed as optional help, not a pushed next step.",
        ),
        "no_terminal_closing_phrase": naturalness_check(
            "no_terminal_closing_phrase",
            not contains_any(response, TERMINAL_CLOSING_MARKERS),
            "A continue-call response must not contain hang-up or final-close wording.",
        ),
        "no_internal_jargon": naturalness_check(
            "no_internal_jargon",
            not contains_any(response, INTERNAL_JARGON_MARKERS),
            "Customer-facing text must not expose internal approval, campaign, routing, or logging terms.",
        ),
        "spoken_sentence_shape": naturalness_check(
            "spoken_sentence_shape",
            spoken_sentence_shape(response),
            "Speech response should be short, sentence-bounded, and not overloaded.",
        ),
        "customer_move_fit": naturalness_check(
            "customer_move_fit",
            customer_move_fit(response, difficulty),
            "Continuation must be tied to the customer's actual reason for hesitating.",
        ),
        "language_specific_naturalness": naturalness_check(
            "language_specific_naturalness",
            language_specific_naturalness(response, language),
            "Language must be uncorrupted and not mix English/German fragments awkwardly.",
        ),
        "no_pressure_payment_contract_or_unsupported_claim": naturalness_check(
            "no_pressure_payment_contract_or_unsupported_claim",
            not (
                contains_any(response, PRESSURE_MARKERS)
                or contains_any(response, PAYMENT_COLLECTION_MARKERS)
                or contains_any(response, CONTRACT_SIGNING_MARKERS)
                or contains_any(response, UNSUPPORTED_CLAIM_MARKERS)
            ),
            "Naturalness cannot come from pressure, payment handling, contract signing, or unsupported claims.",
        ),
    }
    passed_count = sum(1 for check in checks.values() if check["passed"])
    score = passed_count / len(checks)
    return {"score": score, "passed": score >= 0.9, "checks": checks}


def prod_050_cases_and_results() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    cases = read_json(SOURCE_FILES["prod_050_cases"])["items"]
    results = {item["case_id"]: item for item in read_json(SOURCE_FILES["prod_050_results"])["items"]}
    return cases, results


def build_runtime_results(cases: list[dict[str, Any]], source_results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    later_promoted = later_promoted_responses_by_case_id()
    for case in cases:
        live = build_runtime_decision(case, campaign=case["campaign"])
        source = source_results[case["case_id"]]
        expected = source["proposed_runtime_decision"]
        matches_expected = (
            live["call_control"] == expected["call_control"]
            and live["agent_response"] == expected["agent_response"]
            and live["sales_difficulty"] == expected["sales_difficulty"]
        )
        matches_later_reviewed = (
            case["case_id"] in later_promoted
            and live["call_control"] == expected["call_control"]
            and live["agent_response"] == later_promoted[case["case_id"]]
            and live["sales_difficulty"] == expected["sales_difficulty"]
        )
        passed = (
            case["sales_difficulty"] in SELECTED_DIFFICULTIES
            and live["call_control"] == "bridge-then-continue"
            and live["next_action"] == "answer-and-continue"
            and live["response_mode"] == "fast-response"
            and live["bridge_response"] is None
            and "campaign-knowledge-lookup" not in live["background_modules"]
            and (matches_expected or matches_later_reviewed)
        )
        items.append(
            {
                "case_id": case["case_id"],
                "language": case["language"],
                "customer_move_id": case["customer_move_id"],
                "sales_difficulty": case["sales_difficulty"],
                "customer_utterance": case["customer_input"]["transcript"],
                "baseline_runtime_decision": source["current_runtime_decision"],
                "prod_050_proposed_decision": expected,
                "live_runtime_decision": live,
                "matches_prod_050_proposal": matches_expected,
                "matches_later_reviewed_runtime_text": matches_later_reviewed,
                "later_review_checkpoint_id": "PROD-053E-english-runtime-wording-patch" if matches_later_reviewed else None,
                "passed": passed,
            }
        )
    return items


def build_naturalness_audit(runtime_results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    audit_items = []
    before_after = []
    for item in runtime_results:
        baseline_score = score_naturalness(item["baseline_runtime_decision"])
        live_score = score_naturalness(item["live_runtime_decision"])
        audit_items.append(
            {
                "case_id": item["case_id"],
                "language": item["language"],
                "sales_difficulty": item["sales_difficulty"],
                "agent_response": item["live_runtime_decision"]["agent_response"],
                "score": live_score["score"],
                "passed": live_score["passed"],
                "checks": live_score["checks"],
            }
        )
        before_after.append(
            {
                "case_id": item["case_id"],
                "language": item["language"],
                "sales_difficulty": item["sales_difficulty"],
                "baseline_score": baseline_score["score"],
                "live_score": live_score["score"],
                "score_delta": live_score["score"] - baseline_score["score"],
                "baseline_response": item["baseline_runtime_decision"]["agent_response"],
                "live_response": item["live_runtime_decision"]["agent_response"],
                "baseline_call_control": item["baseline_runtime_decision"]["call_control"],
                "live_call_control": item["live_runtime_decision"]["call_control"],
                "changed_surface": "response_text_and_call_control",
            }
        )
    return audit_items, before_after


def boundary_case(case_id: str, move_id: str, transcript: str, expected_call_control: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "customer_move_id": move_id,
        "customer_input": {"input_type": "speech", "stage": "relevance-check", "transcript": transcript},
        "campaign": TEST_CAMPAIGN,
        "expected_call_control": expected_call_control,
    }


def build_protected_boundary_results() -> list[dict[str, Any]]:
    results = []
    for case_id, move_id, transcript, expected_call_control in PROTECTED_BOUNDARY_SPECS:
        case = boundary_case(case_id, move_id, transcript, expected_call_control)
        decision = build_runtime_decision(case, campaign=TEST_CAMPAIGN)
        passed = decision["call_control"] == expected_call_control and decision["call_control"] != "bridge-then-continue"
        results.append(
            {
                "case_id": case_id,
                "customer_move_id": move_id,
                "customer_utterance": transcript,
                "expected_call_control": expected_call_control,
                "live_runtime_decision": decision,
                "passed": passed,
            }
        )
    return results


def build_summary(
    runtime_results: list[dict[str, Any]],
    naturalness_items: list[dict[str, Any]],
    before_after: list[dict[str, Any]],
    boundaries: list[dict[str, Any]],
) -> dict[str, Any]:
    difficulty_counts = Counter(item["sales_difficulty"] for item in runtime_results)
    responses = [item["live_runtime_decision"]["agent_response"] for item in runtime_results]
    return {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_statuses": source_statuses(),
        "runtime_update_case_count": len(runtime_results),
        "runtime_update_pass_count": sum(1 for item in runtime_results if item["passed"]),
        "runtime_update_fail_count": sum(1 for item in runtime_results if not item["passed"]),
        "selected_sales_difficulty_count": len(difficulty_counts),
        "selected_sales_difficulty_counts": dict(sorted(difficulty_counts.items())),
        "live_bridge_then_continue_count": sum(1 for item in runtime_results if item["live_runtime_decision"]["call_control"] == "bridge-then-continue"),
        "live_answer_and_continue_action_count": sum(1 for item in runtime_results if item["live_runtime_decision"]["next_action"] == "answer-and-continue"),
        "response_matches_prod_050_proposal_count": sum(1 for item in runtime_results if item["matches_prod_050_proposal"]),
        "response_matches_later_reviewed_runtime_text_count": sum(
            1 for item in runtime_results if item["matches_later_reviewed_runtime_text"]
        ),
        "response_matches_prod_050_or_later_reviewed_count": sum(
            1
            for item in runtime_results
            if item["matches_prod_050_proposal"] or item["matches_later_reviewed_runtime_text"]
        ),
        "naturalness_case_count": len(naturalness_items),
        "naturalness_pass_count": sum(1 for item in naturalness_items if item["passed"]),
        "naturalness_fail_count": sum(1 for item in naturalness_items if not item["passed"]),
        "naturalness_improvement_count": sum(1 for item in before_after if item["score_delta"] > 0),
        "naturalness_average_score": round(sum(item["score"] for item in naturalness_items) / len(naturalness_items), 3)
        if naturalness_items
        else 0,
        "protected_boundary_probe_count": len(boundaries),
        "protected_boundary_pass_count": sum(1 for item in boundaries if item["passed"]),
        "protected_boundary_softened_count": sum(1 for item in boundaries if item["live_runtime_decision"]["call_control"] == "bridge-then-continue"),
        "pressure_violation_count": sum(1 for response in responses if contains_any(response, PRESSURE_MARKERS)),
        "unsupported_claim_violation_count": sum(1 for response in responses if contains_any(response, UNSUPPORTED_CLAIM_MARKERS)),
        "payment_collection_violation_count": sum(1 for response in responses if contains_any(response, PAYMENT_COLLECTION_MARKERS)),
        "contract_signing_violation_count": sum(1 for response in responses if contains_any(response, CONTRACT_SIGNING_MARKERS)),
        "internal_jargon_violation_count": sum(1 for response in responses if contains_any(response, INTERNAL_JARGON_MARKERS)),
        "terminal_closing_phrase_count": sum(1 for response in responses if contains_any(response, TERMINAL_CLOSING_MARKERS)),
        "runtime_behavior_changed": True,
        "call_control_behavior_changed": True,
        "response_text_behavior_changed": True,
        **BOUNDARY_FLAGS,
    }


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        f"- Checkpoint id: `{CHECKPOINT_ID}`",
        f"- Source checkpoint: `{SOURCE_CHECKPOINT_ID}`",
        f"- Runtime update cases: `{summary['runtime_update_case_count']}`",
        f"- Runtime update passes: `{summary['runtime_update_pass_count']}`",
        f"- PROD-050 response matches: `{summary['response_matches_prod_050_proposal_count']}`",
        f"- Later reviewed response matches: `{summary['response_matches_later_reviewed_runtime_text_count']}`",
        f"- Naturalness passes: `{summary['naturalness_pass_count']} / {summary['naturalness_case_count']}`",
        f"- Naturalness average score: `{summary['naturalness_average_score']}`",
        f"- Protected boundary probes: `{summary['protected_boundary_pass_count']} / {summary['protected_boundary_probe_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- Production runtime promotion allowed: `{str(summary['production_runtime_promotion_allowed']).lower()}`",
        "",
        "## Result",
        "",
        "`PROD-051` applies the `answer-and-continue` runtime path for the selected `bridge-then-continue` cases and validates the spoken response text through a deterministic naturalness rubric. Later explicitly reviewed response text may supersede exact `PROD-050` wording without changing the call-control contract.",
        "",
        "## Naturalness Rubric",
        "",
        "- direct answer or acknowledgement",
        "- optional low-pressure continuation",
        "- no terminal closing phrase",
        "- no internal jargon",
        "- spoken sentence shape",
        "- customer-move fit",
        "- language-specific naturalness",
        "- no pressure, payment, contract, or unsupported claim",
        "",
    ]
    return "\n".join(lines)


def build_html(summary: dict[str, Any], runtime_results: list[dict[str, Any]], naturalness_items: list[dict[str, Any]]) -> str:
    rows = []
    audit_by_id = {item["case_id"]: item for item in naturalness_items}
    for item in runtime_results:
        audit = audit_by_id[item["case_id"]]
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['language'])}</td>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['baseline_runtime_decision']['call_control'])}</td>"
            f"<td>{html.escape(item['live_runtime_decision']['call_control'])}</td>"
            f"<td>{html.escape(item['live_runtime_decision']['next_action'])}</td>"
            f"<td>{audit['score']:.3f}</td>"
            f"<td>{html.escape(item['live_runtime_decision']['agent_response'])}</td>"
            f"<td>{str(item['passed'] and audit['passed']).lower()}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-051 Safe Call-Control Runtime Update</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
  </style>
</head>
<body>
  <h1>PROD-051 Safe Call-Control Runtime Update</h1>
  <p>Runtime behavior changed: true. Provider calls made: false. Production runtime promotion allowed: false.</p>
  <p>Naturalness passed {summary['naturalness_pass_count']} of {summary['naturalness_case_count']} cases with average score {summary['naturalness_average_score']}.</p>
  <table>
    <thead><tr><th>Language</th><th>Case</th><th>Sales difficulty</th><th>Baseline control</th><th>Live control</th><th>Next action</th><th>Naturalness</th><th>Live response</th><th>Passed</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def build_payload() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    cases, source_results = prod_050_cases_and_results()
    runtime_results = build_runtime_results(cases, source_results)
    naturalness_items, before_after = build_naturalness_audit(runtime_results)
    boundaries = build_protected_boundary_results()
    summary = build_summary(runtime_results, naturalness_items, before_after, boundaries)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "validation": {
            "passed": all(summary["source_result_statuses"].values())
            and summary["runtime_update_case_count"] == 22
            and summary["runtime_update_fail_count"] == 0
            and summary["naturalness_fail_count"] == 0
            and summary["protected_boundary_pass_count"] == summary["protected_boundary_probe_count"],
        },
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "runtime_results": rel(OUT_DIR / "runtime_update_results.json"),
            "naturalness_audit": rel(OUT_DIR / "naturalness_audit_results.json"),
            "protected_boundaries": rel(OUT_DIR / "protected_boundary_results.json"),
            "before_after": rel(OUT_DIR / "before_after_naturalness.json"),
            "review_html": rel(OUT_DIR / "prod_051_review.html"),
        },
        "summary": summary,
    }
    return payload, runtime_results, naturalness_items, before_after, boundaries


def main() -> None:
    payload, runtime_results, naturalness_items, before_after, boundaries = build_payload()
    write_json(OUT_DIR / "runtime_update_results.json", {"checkpoint_id": CHECKPOINT_ID, "items": runtime_results})
    write_json(OUT_DIR / "naturalness_audit_results.json", {"checkpoint_id": CHECKPOINT_ID, "items": naturalness_items})
    write_json(OUT_DIR / "protected_boundary_results.json", {"checkpoint_id": CHECKPOINT_ID, "items": boundaries})
    write_json(OUT_DIR / "before_after_naturalness.json", {"checkpoint_id": CHECKPOINT_ID, "items": before_after})
    write_text(OUT_DIR / "report.md", build_report(payload["summary"]))
    write_text(OUT_DIR / "prod_051_review.html", build_html(payload["summary"], runtime_results, naturalness_items))
    write_json(OUT_DIR / "result.json", payload)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": payload["validation"], "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
