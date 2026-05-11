#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from prod_045_core_sales_policy_regression_rerun import is_generic_clarification
from prod_046a_german_naturalized_policy_regression import (
    GERMAN_CAMPAIGN,
    STRICT_REQUIRED_MOVES,
    build_false_positive_cases,
    build_positive_cases,
    run_case,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046C-german-campaign-field-interpolation-guard"
CHECKPOINT_NAME = "German Campaign Field Interpolation Guard"
NEXT_CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

PROD_045_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json"
PROD_046A_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json"
PROD_046B_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json"

MALFORMED_GERMAN_MARKERS = [
    "bei beim",
    "bei bei",
    "um ein kurzer",
    "um ein Abgleich",
    "um der Grund",
    "Support-Warteschlange",
    "Kündigungs-Warteschlange",
    "freigegebener Spezialistenweg",
    "freigegebenen Spezialistenweg",
    "sichere Passungsfrage",
    "Überlegenheitsaussage",
    "sale-ready",
    "freigegebene Übergabe",
]

ENGLISH_OPERATIONAL_MARKERS = [
    "support queue",
    "specialist route",
    "approved specialist path",
    "payment details",
    "contract signing",
    "unknown-runtime-signal",
]

UTF8_GERMAN_MARKERS = ["Ã", "Kuendigungsweg", "fuer", "Rueckruf", "naechst", "pruef"]

INTERPOLATION_MOVES = {
    "price_first",
    "who_are_you",
    "security_review",
    "technical_question",
    "coverage_confusion",
    "sensitive_healthcare_concern",
    "existing_provider",
    "sale_ready_interest",
}

PROD_046B_MALFORMED_BASELINE_RESPONSES = {
    "price-first-direct": "Nach den freigegebenen Informationen liegt der Preisrahmen bei beim Starter-Paket 29 Euro pro Nutzer und Monat; die genauen Bedingungen kommen schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsunterzeichnung.",
    "identity-repair": "Hier ist Maya von RouteSignal. Ich rufe kurz an, um ein kurzer Abgleich zur Zuständigkeit für Rückrufe und Nachverfolgung. Wenn das für Sie nicht relevant ist, beende ich den Anruf.",
    "security-review-route": "Für eine Sicherheitsprüfung braucht es freigegebene Unterlagen oder eine zuständige Fachperson. Ich kann das an eine zuständige Fachperson weiterleiten und mache hier keine pauschalen Compliance-Zusagen.",
    "sale-ready-commitment": "Gut, ich halte fest, dass Sie den nächsten freigegebenen Schritt möchten. Es findet hier keine Zahlung und keine Vertragsunterzeichnung statt.",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def response_text(result: dict[str, Any]) -> str:
    return result["runtime_decision"]["agent_response"]


def find_hits(text: str, markers: list[str]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker.lower() in lowered]


def has_duplicate_specialist_phrase(text: str) -> bool:
    for sentence in re.split(r"[.!?]", text):
        if sentence.lower().count("zuständige fachperson") > 1:
            return True
    return False


def is_required_boundary_positive(result: dict[str, Any]) -> bool:
    return result.get("customer_move_id") in STRICT_REQUIRED_MOVES


def run_positive_and_false_cases() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    positive_results = [run_case(case) for case in build_positive_cases()]
    false_positive_results = [run_case(case) for case in build_false_positive_cases()]
    return positive_results, false_positive_results


def build_interpolation_cases() -> list[dict[str, Any]]:
    selected = []
    for case in build_positive_cases():
        if case["customer_move_id"] in INTERPOLATION_MOVES:
            selected.append(
                {
                    **case,
                    "case_id": f"interp-{case['case_id']}",
                    "example_type": "synthetic_naturalized_de_interpolation_guard_case",
                    "source_quote": False,
                    "from_single_transcript": False,
                    "translation_mode": "intent_equivalent_not_literal",
                }
            )
    legacy_fragment_campaign = {
        **GERMAN_CAMPAIGN,
        "campaign_id": "campaign-prod-046c-de-legacy-fragment-guard",
        "approved_pricing_response": "",
        "approved_identity_reason_sentence": "",
        "pricing_summary": "beim Starter-Paket 29 Euro pro Nutzer und Monat; die genauen Bedingungen kommen schriftlich.",
        "approved_reason_for_call": "ein kurzer Abgleich zur Zuständigkeit für Rückrufe und Nachverfolgung",
        "specialist_handoff_route": "eine zuständige Fachperson",
    }
    for source_case in build_positive_cases():
        if source_case["customer_move_id"] in {"price_first", "who_are_you", "security_review"}:
            selected.append(
                {
                    **source_case,
                    "case_id": f"interp-legacy-{source_case['case_id']}",
                    "campaign": legacy_fragment_campaign,
                    "example_type": "synthetic_naturalized_de_interpolation_guard_case",
                    "source_quote": False,
                    "from_single_transcript": False,
                    "translation_mode": "intent_equivalent_not_literal",
                }
            )
    return selected


def run_interpolation_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [run_case(case) for case in cases]


def collect_response_findings(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for item in results:
        response = response_text(item)
        malformed_hits = find_hits(response, MALFORMED_GERMAN_MARKERS)
        english_hits = find_hits(response, ENGLISH_OPERATIONAL_MARKERS)
        utf8_hits = find_hits(response, UTF8_GERMAN_MARKERS)
        duplicate_specialist = has_duplicate_specialist_phrase(response)
        if malformed_hits or english_hits or utf8_hits or duplicate_specialist:
            findings.append(
                {
                    "case_id": item["case_id"],
                    "customer_move_id": item.get("customer_move_id"),
                    "sales_difficulty": item["runtime_decision"]["sales_difficulty"],
                    "malformed_german_hits": malformed_hits,
                    "english_operational_hits": english_hits,
                    "utf8_german_hits": utf8_hits,
                    "duplicate_zustaendige_fachperson_same_sentence": duplicate_specialist,
                    "agent_response": response,
                }
            )
    return findings


def build_before_after(current_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_by_difficulty: dict[str, str] = {}
    for result in current_results:
        difficulty = result["runtime_decision"]["sales_difficulty"]
        current_by_difficulty.setdefault(difficulty, response_text(result))

    output = []
    for difficulty, previous_after in PROD_046B_MALFORMED_BASELINE_RESPONSES.items():
        current_after = current_by_difficulty.get(difficulty, "")
        output.append(
            {
                "sales_difficulty": difficulty,
                "prod_046b_after_response": previous_after,
                "prod_046c_after_response": current_after,
                "changed": previous_after != current_after,
                "prod_046b_malformed_hits": find_hits(previous_after, MALFORMED_GERMAN_MARKERS),
                "prod_046c_malformed_hits": find_hits(current_after, MALFORMED_GERMAN_MARKERS),
                "duplicate_specialist_before": has_duplicate_specialist_phrase(previous_after),
                "duplicate_specialist_after": has_duplicate_specialist_phrase(current_after),
            }
        )
    return output


def count_unknown(results: list[dict[str, Any]]) -> int:
    return sum(1 for item in results if item["runtime_decision"]["sales_difficulty"] == "unknown-runtime-signal")


def count_generic(results: list[dict[str, Any]]) -> int:
    return sum(1 for item in results if is_generic_clarification(response_text(item)))


def build_summary(
    positive_results: list[dict[str, Any]],
    false_positive_results: list[dict[str, Any]],
    interpolation_results: list[dict[str, Any]],
    response_findings: list[dict[str, Any]],
    before_after: list[dict[str, Any]],
) -> dict[str, Any]:
    required_positive = [item for item in positive_results if is_required_boundary_positive(item)]
    all_results = positive_results + false_positive_results + interpolation_results
    return {
        "german_positive_case_count": len(positive_results),
        "german_false_positive_case_count": len(false_positive_results),
        "german_interpolation_case_count": len(interpolation_results),
        "german_positive_unknown_runtime_signal_count": count_unknown(required_positive),
        "german_positive_generic_clarification_count": count_generic(required_positive),
        "german_false_positive_unknown_runtime_signal_count": count_unknown(false_positive_results),
        "german_false_positive_generic_clarification_count": count_generic(false_positive_results),
        "malformed_german_response_count": len(response_findings),
        "duplicate_specialist_phrase_count": sum(1 for item in response_findings if item["duplicate_zustaendige_fachperson_same_sentence"]),
        "response_language_mismatch_count": sum(1 for item in all_results if item["runtime_decision"]["response_language"] != "de"),
        "german_interpolation_rewrite_count": sum(1 for item in before_after if item["changed"]),
        "english_prod_045_regression_still_passed": read_json(PROD_045_RESULT).get("validation", {}).get("passed") is True,
        "german_prod_046a_regression_still_passed": read_json(PROD_046A_RESULT).get("validation", {}).get("passed") is True,
        "german_prod_046b_wording_regression_still_passed": read_json(PROD_046B_RESULT).get("validation", {}).get("passed") is True,
        "runtime_behavior_changed": True,
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


def render_html(review_data: dict[str, Any]) -> str:
    summary = review_data["summary"]
    before_after_rows = []
    for item in review_data["before_after"]:
        before_after_rows.append(
            "<tr>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['prod_046b_after_response'])}</td>"
            f"<td>{html.escape(item['prod_046c_after_response'])}</td>"
            f"<td>{html.escape(', '.join(item['prod_046b_malformed_hits']) or 'none')}</td>"
            f"<td>{html.escape(', '.join(item['prod_046c_malformed_hits']) or 'none')}</td>"
            "</tr>"
        )
    finding_rows = []
    for item in review_data["response_findings"]:
        finding_rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(', '.join(item['malformed_german_hits']) or 'none')}</td>"
            f"<td>{html.escape(item['agent_response'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>PROD-046C German Campaign Field Interpolation Guard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-046C German Campaign Field Interpolation Guard</h1>
  <section class="summary">
    <h2>Summary</h2>
    <p>Malformed German response count: <code>{summary['malformed_german_response_count']}</code></p>
    <p>German positive unknown-runtime-signal count: <code>{summary['german_positive_unknown_runtime_signal_count']}</code></p>
    <p>German positive generic clarification count: <code>{summary['german_positive_generic_clarification_count']}</code></p>
    <p>False-positive unknown/generic counts are reported separately: <code>{summary['german_false_positive_unknown_runtime_signal_count']}</code> / <code>{summary['german_false_positive_generic_clarification_count']}</code></p>
    <p>Retrieval enabled: <code>false</code> | Provider calls: <code>false</code> | LLM used: <code>false</code></p>
  </section>
  <h2>Before / After Interpolation Fixes</h2>
  <table><tr><th>Sales difficulty</th><th>PROD-046B output</th><th>PROD-046C output</th><th>Before hits</th><th>After hits</th></tr>{''.join(before_after_rows)}</table>
  <h2>Response Findings</h2>
  <table><tr><th>Case</th><th>Sales difficulty</th><th>Malformed hits</th><th>Agent response</th></tr>{''.join(finding_rows) or '<tr><td colspan="4">No findings.</td></tr>'}</table>
  <h2>Boundary Status</h2>
  <p>No retrieval, provider calls, LLM calls, private-data reads, voice playback, public demo polish, payment collection, contract signing, or production promotion is enabled.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any], before_after: list[dict[str, Any]]) -> str:
    lines = [
        "# PROD-046C German Campaign Field Interpolation Guard",
        "",
        "PROD-046C fixes narrow German campaign-field interpolation bugs found after PROD-046B.",
        "",
        "This is not a runtime-policy expansion checkpoint and not a German realism pass. It keeps the PROD-045, PROD-046A, and PROD-046B regression surfaces intact while adding deterministic guards for malformed German customer-facing strings.",
        "",
        "## Results",
        "",
        f"- German positive cases: {summary['german_positive_case_count']}",
        f"- German false-positive cases: {summary['german_false_positive_case_count']}",
        f"- German interpolation guard cases: {summary['german_interpolation_case_count']}",
        f"- Malformed German response count: {summary['malformed_german_response_count']}",
        f"- Duplicate `zuständige Fachperson` same-sentence count: {summary['duplicate_specialist_phrase_count']}",
        f"- Positive unknown-runtime-signal count: {summary['german_positive_unknown_runtime_signal_count']}",
        f"- Positive generic clarification count: {summary['german_positive_generic_clarification_count']}",
        f"- False-positive unknown-runtime-signal count: {summary['german_false_positive_unknown_runtime_signal_count']}",
        f"- False-positive generic clarification count: {summary['german_false_positive_generic_clarification_count']}",
        f"- English PROD-045 still passed: `{summary['english_prod_045_regression_still_passed']}`",
        f"- German PROD-046A still passed: `{summary['german_prod_046a_regression_still_passed']}`",
        f"- German PROD-046B still passed: `{summary['german_prod_046b_wording_regression_still_passed']}`",
        "",
        "## Before / After",
        "",
    ]
    for item in before_after:
        lines.extend(
            [
                f"### {item['sales_difficulty']}",
                "",
                f"- PROD-046B: {item['prod_046b_after_response']}",
                f"- PROD-046C: {item['prod_046c_after_response']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Remaining Wording Risks",
            "",
            "- German response quality still needs human/product review by a German speaker.",
            "- The guard catches known malformed interpolation classes, not every possible grammar issue.",
            "- Campaign fields remain a product-quality bottleneck unless future profiles clearly separate full customer-facing sentences from fragments.",
            "",
            "## Boundaries",
            "",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- Private data read: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "",
            f"Next recommended checkpoint: `{NEXT_CHECKPOINT_ID}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    for required in (PROD_045_RESULT, PROD_046A_RESULT, PROD_046B_RESULT):
        if not required.exists():
            raise SystemExit(f"Missing required source result: {rel(required)}")

    positive_results, false_positive_results = run_positive_and_false_cases()
    interpolation_cases = build_interpolation_cases()
    interpolation_results = run_interpolation_cases(interpolation_cases)
    all_results = positive_results + false_positive_results + interpolation_results

    response_findings = collect_response_findings(all_results)
    before_after = build_before_after(positive_results)
    summary = build_summary(positive_results, false_positive_results, interpolation_results, response_findings, before_after)

    passed = (
        summary["english_prod_045_regression_still_passed"]
        and summary["german_prod_046a_regression_still_passed"]
        and summary["german_prod_046b_wording_regression_still_passed"]
        and summary["malformed_german_response_count"] == 0
        and summary["duplicate_specialist_phrase_count"] == 0
        and summary["response_language_mismatch_count"] == 0
        and summary["german_positive_unknown_runtime_signal_count"] == 0
        and summary["german_positive_generic_clarification_count"] == 0
    )

    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "malformed_german_markers": MALFORMED_GERMAN_MARKERS,
        "english_operational_markers": ENGLISH_OPERATIONAL_MARKERS,
        "before_after": before_after,
        "response_findings": response_findings,
        "positive_results": positive_results,
        "false_positive_results": false_positive_results,
        "interpolation_results": interpolation_results,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "german_interpolation_cases": rel(OUT_DIR / "german_interpolation_cases.json"),
            "german_interpolation_results": rel(OUT_DIR / "german_interpolation_results.json"),
            "german_interpolation_before_after": rel(OUT_DIR / "german_interpolation_before_after.json"),
            "german_interpolation_review_data": rel(OUT_DIR / "german_interpolation_review_data.json"),
            "german_interpolation_review_html": rel(OUT_DIR / "german_interpolation_review.html"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }

    write_json(OUT_DIR / "german_interpolation_cases.json", {"items": interpolation_cases})
    write_json(OUT_DIR / "german_interpolation_results.json", {"items": interpolation_results})
    write_json(OUT_DIR / "german_interpolation_before_after.json", {"items": before_after})
    write_json(OUT_DIR / "german_interpolation_review_data.json", review_data)
    write_text(OUT_DIR / "german_interpolation_review.html", render_html(review_data))
    write_text(OUT_DIR / "report.md", build_report(summary, before_after))
    write_json(OUT_DIR / "result.json", result)

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": passed}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
