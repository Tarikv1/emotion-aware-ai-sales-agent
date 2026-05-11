#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from prod_046a_german_naturalized_policy_regression import (
    EXPECTED_BY_MOVE,
    GERMAN_CAMPAIGN,
    build_false_positive_cases,
    build_positive_cases,
    run_case,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046B-german-response-wording-quality-pass"
CHECKPOINT_NAME = "German Response Wording Quality Pass"
SOURCE_CHECKPOINT_ID = "PROD-046A-german-naturalized-policy-regression"
ENGLISH_SOURCE_CHECKPOINT_ID = "PROD-045-core-sales-policy-regression-rerun"
NEXT_CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PROD_045_RESULT = ROOT / "research" / "experiments" / "generated" / ENGLISH_SOURCE_CHECKPOINT_ID / "result.json"

BANNED_INTERNAL_TERMS = [
    "sale-ready",
    "freigegebener spezialistenweg",
    "freigegebenen spezialistenweg",
    "support-warteschlange",
    "kündigungs-warteschlange",
    "sichere passungsfrage",
    "überlegenheitsaussage",
    "freigegebene übergabe zum nächsten schritt",
]

GERMAN_MOJIBAKE_MARKERS = ["Ã", "Â", "â", "Kuendigungsweg", "fuer", "pruef", "naechst", "Rueck"]

ENGLISH_OPERATIONAL_TERMS = [
    "sale-ready",
    "support queue",
    "specialist route",
    "approved specialist path",
    "payment details",
    "contract signing",
]

BASELINE_BEFORE_RESPONSES = {
    "price-first-direct": "Der freigegebene Preisrahmen liegt beim Starter-Paket bei 29 Euro pro Nutzer und Monat; die genauen Bedingungen kommen schriftlich. Keine Zahlung und keine Verpflichtung in diesem Anruf.",
    "identity-repair": "Hier ist Maya von RouteSignal. Der Grund für den Anruf ist ein kurzer Abgleich zur Zuständigkeit für Rückrufe und Nachverfolgung. Wenn das nicht relevant ist, höre ich hier auf.",
    "written-info-request": "Ich kann die freigegebene schriftliche Zusammenfassung senden und es dabei belassen.",
    "email-only-boundary": "Verstanden. Nur per E-Mail. Ich kann die freigegebene E-Mail-Zusammenfassung senden und dränge nicht auf einen Anruf.",
    "scam-safety-boundary": "In diesem Anruf werden keine Zahlungs-, Karten- oder sensiblen Daten aufgenommen. Ich kann die öffentliche Verifizierungsseite und die schriftliche Zusammenfassung zur Verifizierung senden.",
    "payment-safety-boundary": "Hier werden keine Karten- oder Zahlungsdaten benötigt. Ich halte den nächsten Schritt nur bei sicheren schriftlichen Informationen: die freigegebene einseitige Zusammenfassung.",
    "support-route": "Das ist ein Support-Thema. Ich stoppe den Verkaufspfad und leite das an die Support-Warteschlange weiter.",
    "cancellation-route": "Ich stoppe den Verkaufspfad und leite das an die Kündigungs-Warteschlange weiter.",
    "technical-specialist-route": "Im freigegebenen Rahmen: das System kann Zuständigkeiten für Rückrufe und Nachverfolgung abbilden; Integrationsdetails müssen geprüft werden. Für weitere Details kann ich das an den freigegebenen Spezialistenweg weiterleiten.",
    "security-review-route": "Für eine Sicherheitsprüfung braucht es freigegebene Unterlagen oder einen Spezialisten. Ich kann das an den freigegebenen Spezialistenweg weiterleiten und mache hier keine breiten Compliance-Zusagen.",
    "coverage-boundary-route": "Ich darf in diesem Anruf keine medizinische, gesundheitliche oder Deckungsberatung geben. Ich kann das an den freigegebenen Spezialistenweg weiterleiten.",
    "healthcare-boundary-route": "Ich darf in diesem Anruf keine medizinische, gesundheitliche oder Deckungsberatung geben. Ich kann das an den freigegebenen Spezialistenweg weiterleiten.",
    "existing-provider-gap": "Ich behaupte nicht, dass dies Ihren Anbieter ersetzt. Die sichere Passungsfrage ist, ob trotz Ihres aktuellen Anbieters noch Rückrufe oder Nachverfolgungen liegen bleiben.",
    "stakeholder-review": "Ich kann die freigegebene Zusammenfassung zur Prüfung senden. Keine Entscheidung und keine Verpflichtung heute.",
    "partner-review": "Ich kann die freigegebene Zusammenfassung zur Prüfung senden. Keine Entscheidung und keine Verpflichtung heute.",
    "sale-ready-commitment": "Bestätigt. Ich markiere das als sale-ready für die freigegebene Übergabe zum nächsten Schritt. Keine Zahlung und keine Vertragsunterzeichnung in diesem Anruf.",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def count_terms(texts: list[str], terms: list[str]) -> int:
    total = 0
    for text in texts:
        lowered = text.lower()
        total += sum(lowered.count(term) for term in terms)
    return total


def find_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if term in lowered]


def after_responses(results: list[dict[str, Any]]) -> list[str]:
    return [item["runtime_decision"]["agent_response"] for item in results]


def unique_after_by_sales_difficulty(results: list[dict[str, Any]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in results:
        difficulty = item["runtime_decision"]["sales_difficulty"]
        output.setdefault(difficulty, item["runtime_decision"]["agent_response"])
    return output


def build_before_after(positive_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    after_map = unique_after_by_sales_difficulty(positive_results)
    entries: list[dict[str, Any]] = []
    for difficulty, before in BASELINE_BEFORE_RESPONSES.items():
        after = after_map.get(difficulty)
        if after is None:
            continue
        entries.append(
            {
                "sales_difficulty": difficulty,
                "before_response": before,
                "after_response": after,
                "changed": before != after,
                "banned_terms_before": find_terms(before, BANNED_INTERNAL_TERMS),
                "banned_terms_after": find_terms(after, BANNED_INTERNAL_TERMS),
                "example_type": "synthetic_wording_quality_review_example",
                "source_quote": False,
                "from_single_transcript": False,
            }
        )
    return entries


def build_findings(before_after: list[dict[str, Any]], positive_results: list[dict[str, Any]], false_results: list[dict[str, Any]]) -> dict[str, Any]:
    response_findings = []
    for item in positive_results + false_results:
        response = item["runtime_decision"]["agent_response"]
        hits = find_terms(response, BANNED_INTERNAL_TERMS)
        mojibake = find_terms(response, [marker.lower() for marker in GERMAN_MOJIBAKE_MARKERS])
        english_hits = find_terms(response, ENGLISH_OPERATIONAL_TERMS)
        if hits or mojibake or english_hits:
            response_findings.append(
                {
                    "case_id": item["case_id"],
                    "customer_move_id": item.get("customer_move_id"),
                    "sales_difficulty": item["runtime_decision"]["sales_difficulty"],
                    "banned_internal_term_hits": hits,
                    "mojibake_or_ascii_hits": mojibake,
                    "english_operational_wording_hits": english_hits,
                    "agent_response": response,
                }
            )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "banned_internal_terms": BANNED_INTERNAL_TERMS,
        "before_after_count": len(before_after),
        "response_findings": response_findings,
        "remaining_wording_risks": [
            "German wording is improved deterministically but still needs human/product review by a German speaker.",
            "The response surface remains single-turn and campaign-field-driven; this checkpoint does not validate full live conversation naturalness.",
            "The borrowed German term Support remains allowed because the preferred wording explicitly uses zuständiger Support.",
        ],
        "boundaries": {
            "retrieval_enabled": False,
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "payment_collection_allowed": False,
            "contract_signing_allowed": False,
            "production_runtime_promotion_allowed": False,
        },
    }


def render_html(review_data: dict[str, Any]) -> str:
    summary = review_data["summary"]
    rows = []
    for item in review_data["before_after"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['before_response'])}</td>"
            f"<td>{html.escape(item['after_response'])}</td>"
            f"<td>{html.escape(', '.join(item['banned_terms_before']) or 'none')}</td>"
            f"<td>{html.escape(', '.join(item['banned_terms_after']) or 'none')}</td>"
            "</tr>"
        )
    finding_rows = []
    for item in review_data["findings"]["response_findings"]:
        finding_rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(', '.join(item['banned_internal_term_hits']) or 'none')}</td>"
            f"<td>{html.escape(', '.join(item['mojibake_or_ascii_hits']) or 'none')}</td>"
            f"<td>{html.escape(item['agent_response'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>PROD-046B German Response Wording Quality Pass</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-046B German Response Wording Quality Pass</h1>
  <section class="summary">
    <h2>Summary</h2>
    <p>German wording rewrites: <code>{summary['german_wording_rewrite_count']}</code></p>
    <p>Banned internal terms before: <code>{summary['banned_internal_term_count_before']}</code></p>
    <p>Banned internal terms after: <code>{summary['banned_internal_term_count_after']}</code></p>
    <p>German positive regression passed: <code>{str(summary['german_positive_regression_passed']).lower()}</code></p>
    <p>German false-positive regression passed: <code>{str(summary['german_false_positive_regression_passed']).lower()}</code></p>
    <p>English PROD-045 regression still passed: <code>{str(summary['english_prod_045_regression_still_passed']).lower()}</code></p>
    <p>Retrieval enabled: <code>false</code> | Provider calls: <code>false</code> | LLM used: <code>false</code></p>
  </section>
  <h2>Before / After German Response Examples</h2>
  <table><tr><th>Sales difficulty</th><th>Before</th><th>After</th><th>Banned before</th><th>Banned after</th></tr>{''.join(rows)}</table>
  <h2>Response Findings After Rewrite</h2>
  <table><tr><th>Case</th><th>Sales difficulty</th><th>Banned terms</th><th>Mojibake/ASCII hits</th><th>Agent response</th></tr>{''.join(finding_rows) or '<tr><td colspan="5">No findings.</td></tr>'}</table>
  <h2>Remaining Risk</h2>
  <p>This is a deterministic wording-quality pass, not final German human review. No retrieval, providers, LLMs, private data, voice playback, payment collection, contract signing, or production promotion is enabled.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any], before_after: list[dict[str, Any]], findings: dict[str, Any]) -> str:
    examples = []
    for item in before_after[:8]:
        examples.extend(
            [
                f"### {item['sales_difficulty']}",
                "",
                f"- Before: {item['before_response']}",
                f"- After: {item['after_response']}",
                "",
            ]
        )
    return "\n".join(
        [
            "# PROD-046B German Response Wording Quality Pass",
            "",
            "PROD-046B keeps PROD-046A routing intact and improves German customer-facing response wording so the output is less internal-policy-like.",
            "",
            "This is not final German human review. It is a deterministic wording pass over synthetic de-DE regression cases and campaign fixture wording.",
            "",
            "## Results",
            "",
            f"- German wording rewrites: {summary['german_wording_rewrite_count']}",
            f"- Banned internal terms before: {summary['banned_internal_term_count_before']}",
            f"- Banned internal terms after: {summary['banned_internal_term_count_after']}",
            f"- German positive regression passed: `{summary['german_positive_regression_passed']}`",
            f"- German false-positive regression passed: `{summary['german_false_positive_regression_passed']}`",
            f"- English PROD-045 regression still passed: `{summary['english_prod_045_regression_still_passed']}`",
            f"- German sale-ready term count after: {summary['german_customer_facing_sale_ready_term_count']}",
            f"- German internal route term count after: {summary['german_internal_route_term_count']}",
            "",
            "## Before / After Examples",
            "",
            *examples,
            "## Remaining German Wording Risks",
            "",
            *[f"- {risk}" for risk in findings["remaining_wording_risks"]],
            "",
            "## Boundaries",
            "",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- Private data read: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "",
            f"Next recommended checkpoint: `{NEXT_CHECKPOINT_ID}`.",
        ]
    )


def main() -> None:
    if not PROD_045_RESULT.exists():
        raise SystemExit(f"Missing English source result: {rel(PROD_045_RESULT)}")
    prod_045_result = json.loads(PROD_045_RESULT.read_text(encoding="utf-8"))

    positive_cases = build_positive_cases()
    false_cases = build_false_positive_cases()
    positive_results = [run_case(case) for case in positive_cases]
    false_results = [run_case(case) for case in false_cases]
    all_after_responses = after_responses(positive_results + false_results)
    before_after = build_before_after(positive_results)
    findings = build_findings(before_after, positive_results, false_results)

    before_texts = [item["before_response"] for item in before_after]
    after_texts = [item["after_response"] for item in before_after]
    internal_route_terms = [term for term in BANNED_INTERNAL_TERMS if term != "sale-ready"]

    summary = {
        "german_wording_rewrite_count": sum(1 for item in before_after if item["changed"]),
        "banned_internal_term_count_before": count_terms(before_texts, BANNED_INTERNAL_TERMS),
        "banned_internal_term_count_after": count_terms(all_after_responses, BANNED_INTERNAL_TERMS),
        "german_positive_regression_passed": all(item["passed"] for item in positive_results),
        "german_false_positive_regression_passed": all(item["passed"] for item in false_results),
        "english_prod_045_regression_still_passed": prod_045_result.get("validation", {}).get("passed") is True,
        "german_customer_facing_sale_ready_term_count": count_terms(all_after_responses, ["sale-ready"]),
        "german_internal_route_term_count": count_terms(all_after_responses, internal_route_terms),
        "runtime_behavior_changed": True,
        "german_localized_responses_changed": True,
        "retrieval_enabled": False,
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "payment_collection_allowed": False,
        "contract_signing_allowed": False,
        "production_runtime_promotion_allowed": False,
        "voice_playback_unblocked": False,
        "public_demo_polish_unblocked": False,
    }
    passed = (
        summary["german_positive_regression_passed"]
        and summary["german_false_positive_regression_passed"]
        and summary["english_prod_045_regression_still_passed"]
        and summary["banned_internal_term_count_after"] == 0
        and summary["german_customer_facing_sale_ready_term_count"] == 0
        and summary["german_internal_route_term_count"] == 0
        and not findings["response_findings"]
    )
    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "german_campaign_fixture_after": GERMAN_CAMPAIGN,
        "expected_by_move": EXPECTED_BY_MOVE,
        "before_after": before_after,
        "findings": findings,
        "german_positive_regression_results": positive_results,
        "german_false_positive_regression_results": false_results,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "german_wording_before_after": rel(OUT_DIR / "german_wording_before_after.json"),
            "german_wording_findings": rel(OUT_DIR / "german_wording_findings.json"),
            "german_regression_rerun_results": rel(OUT_DIR / "german_regression_rerun_results.json"),
            "review_data": rel(OUT_DIR / "prod_046b_review_data.json"),
            "review_html": rel(OUT_DIR / "prod_046b_review.html"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }

    write_json(OUT_DIR / "german_wording_before_after.json", {"items": before_after})
    write_json(OUT_DIR / "german_wording_findings.json", findings)
    write_json(
        OUT_DIR / "german_regression_rerun_results.json",
        {"positive_results": positive_results, "false_positive_results": false_results},
    )
    write_json(OUT_DIR / "prod_046b_review_data.json", review_data)
    write_text(OUT_DIR / "prod_046b_review.html", render_html(review_data))
    write_text(OUT_DIR / "report.md", build_report(summary, before_after, findings) + "\n")
    write_json(OUT_DIR / "result.json", result)


if __name__ == "__main__":
    main()
