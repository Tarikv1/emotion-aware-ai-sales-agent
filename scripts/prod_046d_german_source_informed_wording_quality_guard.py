#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from prod_046a_german_naturalized_policy_regression import (
    STRICT_REQUIRED_MOVES,
    build_false_positive_cases,
    build_positive_cases,
    run_case,
)
from prod_046c_german_campaign_field_interpolation_guard import (
    MALFORMED_GERMAN_MARKERS,
    build_interpolation_cases,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046D-german-source-informed-wording-quality-guard"
CHECKPOINT_NAME = "German Source-Informed Wording Quality Guard"
NEXT_CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

PROD_045_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json"
PROD_046A_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json"
PROD_046B_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json"
PROD_046C_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-046C-german-campaign-field-interpolation-guard" / "result.json"

ACCEPTED_SOURCES = [
    {
        "source_title": "Bundesnetzagentur - Unerlaubte Telefonwerbung",
        "url": "https://www.bundesnetzagentur.de/DE/Vportal/TK/Aerger/Faelle/UEW/start.html",
        "source_type": "official regulator",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Conservative identity, consent sensitivity, complaint and do-not-call awareness.",
        "claim_supported": "German outbound runtime wording should be cautious, clear about identity, and respectful of stop/refusal signals.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/METHODOLOGY_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "external-reference evidence",
    },
    {
        "source_title": "Verbraucherzentrale - Ungewollte Werbeanrufe",
        "url": "https://www.verbraucherzentrale.de/wissen/vertraege-reklamation/werbung/ungewollte-werbeanrufe-hilfe-gegen-telefonwerbung-13857",
        "source_type": "consumer protection",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Avoid phone pressure, respect refusal, and prefer clear written follow-up.",
        "claim_supported": "German runtime wording should honor written-info and channel-boundary requests without pushing a call.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/METHODOLOGY_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "thesis-methodology",
    },
    {
        "source_title": "Verbraucherzentrale - Abzocke am Telefon: möglichst nicht Ja sagen",
        "url": "https://www.verbraucherzentrale.de/wissen/digitale-welt/mobilfunk-und-festnetz/abzocke-am-telefon-moeglichst-nicht-ja-sagen-13496",
        "source_type": "consumer protection",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Do not pressure customers into verbal agreement; prefer low-pressure written review.",
        "claim_supported": "Sale-ready and review wording should avoid sounding like a forced verbal close.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/DECISION_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "thesis-methodology",
    },
    {
        "source_title": "Verbraucherzentrale - Unerwarteter Anruf / Vorsicht Falle",
        "url": "https://www.verbraucherzentrale.de/wissen/vertraege-reklamation/abzocke/unerwarteter-anruf-von-der-verbraucherzentrale-vorsicht-falle-11112",
        "source_type": "consumer protection",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Identity repair, verification path, and safe ending when the customer is unsure.",
        "claim_supported": "A German agent response should explain who is calling and give a safe verification path when trust is low.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "external-reference evidence",
    },
    {
        "source_title": "Polizeiliche Kriminalprävention - Fake-Kundenservice / Support Scams",
        "url": "https://www.polizei-beratung.de/themen-und-tipps/sicher-handeln/onlinebetrug-maschen/fake-kundenservice-support-scams/",
        "source_type": "public-service",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Scam and support concerns should avoid sensitive-data requests, remote-access pressure, and unsafe support routing.",
        "claim_supported": "German payment/scam/support responses should state no sensitive data is collected and route safely.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "external-reference evidence",
    },
    {
        "source_title": "Polizeiliche Kriminalprävention - Betrug durch falsche Polizisten",
        "url": "https://www.polizei-beratung.de/themen-und-tipps/betrug/betrug-durch-falsche-polizisten/",
        "source_type": "public-service",
        "reuse_decision": "background only",
        "relevance_to_german_wording": "Background safety tone: no pressure, no money transfer, and official verification.",
        "claim_supported": "German trust-repair wording should stay low-pressure and avoid payment or value-transfer framing.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "external-reference evidence",
    },
    {
        "source_title": "Service Standard - Verständlich schreiben mit Einfacher Sprache",
        "url": "https://servicestandard.gov.de/handbuch/anleitungen/verstaendlich-schreiben-mit-einfacher-sprache/",
        "source_type": "public-service",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Use direct Sie, put important information first, and prefer simple active sentences.",
        "claim_supported": "German runtime wording QA can deterministically reject bureaucratic or internal-sounding phrasing.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/METHODOLOGY_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "thesis-methodology",
    },
    {
        "source_title": "AFZ Bremen - Verständliche Sprache",
        "url": "https://www.afz.bremen.de/verwaltung-nbspentwickeln/buerger-innenservice-und-kommunikation/kommunikation/verstaendliche-sprache-25926",
        "source_type": "public-service",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Clear spoken/customer-service language, short sentences, and direct verbs.",
        "claim_supported": "German response templates should favor active customer-facing verbs over internal process nouns.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/METHODOLOGY_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "thesis-methodology",
    },
    {
        "source_title": "Berlin - Standards für verständliche Sprache",
        "url": "https://www.berlin.de/lb/digitale-barrierefreiheit/anforderungen/berliner-standards/fuer-verstaendliche-sprache-1463990.php",
        "source_type": "public-service",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Avoid Amtsdeutsch, passive constructions, and nominalizations.",
        "claim_supported": "German wording checks should reject internal/bureaucratic phrasing where simpler customer-facing language is available.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/METHODOLOGY_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "thesis-methodology",
    },
    {
        "source_title": "Verbraucherzentrale - Unerwünschte Energieverträge am Telefon",
        "url": "https://www.verbraucherzentrale.de/wissen/energie/achtung-unerwuenschte-energievertraege-am-telefon-58483",
        "source_type": "consumer protection",
        "reuse_decision": "background only",
        "relevance_to_german_wording": "Background pattern for written confirmation and phone-contract anxiety.",
        "claim_supported": "German price and review wording should prefer written conditions and avoid implying a phone contract.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "external-reference evidence",
    },
    {
        "source_title": "Verbraucherzentrale - Hilfe bei Werbe-Anrufen, Leichte Sprache",
        "url": "https://www.verbraucherzentrale.de/vertraege-reklamation/hilfe-bei-werbeanrufen-100996",
        "source_type": "consumer protection / plain-language",
        "reuse_decision": "accept",
        "relevance_to_german_wording": "Simple and clear German wording patterns for unwanted advertising-call situations.",
        "claim_supported": "German runtime output should prefer short, clear customer-facing phrases before human review.",
        "thesis_destination": "docs/thesis/THESIS_REFERENCE_REGISTRY.md; docs/thesis/METHODOLOGY_LOG.md",
        "product_doc_destination": "docs/product/PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
        "evidence_class": "thesis-methodology",
    },
]

REJECTED_SOURCE_TYPES = [
    "sales guru blogs",
    "cold-call scripts",
    "aggressive closing scripts",
    "affiliate SEO pages",
    "copied competitor or insurer wording",
    "random news articles when an official source exists",
    "legal or compliance pages unless handled in a separate compliance checkpoint",
]

SOURCE_INFORMED_INTERNAL_MARKERS = [
    "freigegeben",
    "vertriebsteil",
    "verkaufspfad",
    "rückrufwunsch dokumentieren",
    "dokumentiere einen rückruf",
    "dokumentiere einen follow-up",
    "kampagnenregeln",
    "compliance-zusagen",
    "pauschalen compliance",
    "verifizierungsweg",
    "prüfinformationen",
]

ENGLISH_OPERATIONAL_MARKERS = [
    "sale-ready",
    "unknown-runtime-signal",
    "support queue",
    "specialist route",
    "approved specialist path",
    "payment details",
    "contract signing",
    "follow-up",
    "callback",
    "compliance",
    "campaign",
]

UTF8_GERMAN_MARKERS = ["Ãƒ", "Ã‚", "Kuendigungsweg", "fuer", "Rueckruf", "naechst", "pruef"]

PROD_046C_BASELINE_RESPONSES = {
    "price-first-direct": "Nach den freigegebenen Informationen liegt der Preisrahmen beim Starter-Paket bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen erhalten Sie schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsunterzeichnung.",
    "identity-repair": "Hier ist Maya von RouteSignal. Ich rufe kurz an, um zu klären, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist. Wenn das für Sie nicht relevant ist, beende ich den Anruf.",
    "written-info-request": "Ich kann Ihnen eine kurze freigegebene Zusammenfassung zusenden und es dabei belassen.",
    "email-only-boundary": "Verstanden. Ich halte es bei E-Mail, sende Ihnen eine kurze freigegebene E-Mail-Zusammenfassung und dränge nicht auf ein Telefonat.",
    "scam-safety-boundary": "Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen den offiziellen Verifizierungsweg und die schriftlichen Informationen zusenden.",
    "payment-safety-boundary": "Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen eine kurze freigegebene Zusammenfassung zusenden.",
    "support-route": "Das ist ein Support-Thema. Ich stoppe den Vertriebsteil hier und leite Sie an den zuständigen Support weiter.",
    "cancellation-route": "Dann stoppe ich den Vertriebsteil hier und leite Sie an die zuständige Stelle für Kündigungen weiter.",
    "technical-specialist-route": "Was ich sicher sagen kann: das System kann Zuständigkeiten für Rückrufe und Nachverfolgung abbilden; Integrationsdetails müssen geprüft werden. Für weitere Details kann ich das an eine zuständige Fachperson weiterleiten.",
    "security-review-route": "Für eine Sicherheitsprüfung braucht es freigegebene Unterlagen oder eine zuständige Fachperson. Ich mache hier keine pauschalen Compliance-Zusagen.",
    "coverage-boundary-route": "Ich darf in diesem Gespräch keine medizinische Beratung und keine Beratung zum Versicherungsschutz geben. Ich kann das an eine zuständige Fachperson weiterleiten.",
    "healthcare-boundary-route": "Ich darf in diesem Gespräch keine medizinische Beratung und keine Beratung zum Versicherungsschutz geben. Ich kann das an eine zuständige Fachperson weiterleiten.",
    "existing-provider-gap": "Ich möchte nicht behaupten, dass das Ihren Anbieter ersetzt. Sinnvoll wäre nur zu prüfen, ob trotz Ihrer aktuellen Lösung noch Rückrufe oder Nachverfolgungen liegen bleiben.",
    "stakeholder-review": "Ich kann Ihnen eine kurze freigegebene Zusammenfassung zur Prüfung schicken. Heute müssen Sie nichts entscheiden und gehen keine Verpflichtung ein.",
    "partner-review": "Ich kann Ihnen eine kurze freigegebene Zusammenfassung zur Prüfung schicken. Heute müssen Sie nichts entscheiden und gehen keine Verpflichtung ein.",
    "sale-ready-commitment": "Gut, ich halte fest, dass Sie den nächsten Schritt möchten. Es findet hier keine Zahlung und keine Vertragsunterzeichnung statt.",
    "do-not-call": "Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhören.",
    "callback-request": "Ich kann einen Rückrufwunsch dokumentieren und halte ihn optional. Keine feste Verpflichtung in diesem Anruf.",
    "claim-boundary": "Ich möchte nichts garantieren, was von den Details abhängt. Ich kann das an eine zuständige Fachperson weiterleiten.",
    "product-detail-lookup": "Einen Moment, ich prüfe die freigegebenen Produktinformationen.",
    "scheduling-confirmation": "Bestätigt. Ich notiere den Rückruf so. Auf Wiederhören.",
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


def marker_hit_count(texts: list[str], markers: list[str]) -> int:
    return sum(len(find_hits(text, markers)) for text in texts)


def build_source_informed_cases() -> list[dict[str, Any]]:
    cases = []
    for case in build_positive_cases():
        cases.append(
            {
                **case,
                "case_id": f"source-informed-{case['case_id']}",
                "example_type": "synthetic_source_informed_de_wording_case",
                "source_quote": False,
                "from_single_transcript": False,
                "source_informed_not_source_phrase": True,
            }
        )
    for case in build_interpolation_cases():
        cases.append(
            {
                **case,
                "case_id": f"source-informed-{case['case_id']}",
                "example_type": "synthetic_source_informed_de_wording_case",
                "source_quote": False,
                "from_single_transcript": False,
                "source_informed_not_source_phrase": True,
            }
        )
    return cases


def run_source_informed_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [run_case(case) for case in cases]


def collect_response_findings(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for item in results:
        response = response_text(item)
        internal_hits = find_hits(response, SOURCE_INFORMED_INTERNAL_MARKERS)
        malformed_hits = find_hits(response, MALFORMED_GERMAN_MARKERS)
        english_hits = find_hits(response, ENGLISH_OPERATIONAL_MARKERS)
        utf8_hits = find_hits(response, UTF8_GERMAN_MARKERS)
        if internal_hits or malformed_hits or english_hits or utf8_hits:
            findings.append(
                {
                    "case_id": item["case_id"],
                    "customer_move_id": item.get("customer_move_id"),
                    "sales_difficulty": item["runtime_decision"]["sales_difficulty"],
                    "source_informed_internal_hits": internal_hits,
                    "malformed_german_hits": malformed_hits,
                    "english_operational_hits": english_hits,
                    "utf8_german_hits": utf8_hits,
                    "agent_response": response,
                }
            )
    return findings


def unique_after_by_sales_difficulty(results: list[dict[str, Any]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in results:
        difficulty = item["runtime_decision"]["sales_difficulty"]
        output.setdefault(difficulty, response_text(item))
    return output


def build_before_after(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    after = unique_after_by_sales_difficulty(results)
    entries = []
    for difficulty, before in PROD_046C_BASELINE_RESPONSES.items():
        after_response = after.get(difficulty, "")
        entries.append(
            {
                "sales_difficulty": difficulty,
                "prod_046c_response": before,
                "prod_046d_response": after_response,
                "changed": before != after_response,
                "source_informed_internal_hits_before": find_hits(before, SOURCE_INFORMED_INTERNAL_MARKERS),
                "source_informed_internal_hits_after": find_hits(after_response, SOURCE_INFORMED_INTERNAL_MARKERS),
                "malformed_hits_after": find_hits(after_response, MALFORMED_GERMAN_MARKERS),
                "example_type": "synthetic_source_informed_before_after_example",
                "source_quote": False,
                "from_single_transcript": False,
            }
        )
    return entries


def source_map() -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_use_boundary": {
            "source_informed_wording_guidance_only": True,
            "legal_compliance_claim": False,
            "uses_source_quotes": False,
            "copies_source_wording": False,
            "uses_sales_scripts": False,
        },
        "accepted_sources": [
            {
                **source,
                "source_quote": False,
                "copied_source_text": False,
                "product_only_or_thesis": source["evidence_class"],
            }
            for source in ACCEPTED_SOURCES
        ],
        "rejected_or_avoided_sources": REJECTED_SOURCE_TYPES,
    }


def build_summary(
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    before_after: list[dict[str, Any]],
) -> dict[str, Any]:
    positive_required = [
        item for item in results if item.get("customer_move_id") in STRICT_REQUIRED_MOVES and not item["case_id"].startswith("source-informed-interp-legacy-")
    ]
    responses_before = list(PROD_046C_BASELINE_RESPONSES.values())
    responses_after = [response_text(item) for item in results]
    passed_count = sum(1 for item in results if item.get("passed") is True)
    return {
        "german_source_informed_case_count": len(cases),
        "german_source_informed_pass_count": passed_count,
        "german_source_informed_fail_count": len(results) - passed_count,
        "source_informed_wording_rewrite_count": sum(1 for item in before_after if item["changed"]),
        "source_informed_internal_hit_count_before": marker_hit_count(responses_before, SOURCE_INFORMED_INTERNAL_MARKERS),
        "source_informed_internal_hit_count_after": marker_hit_count(responses_after, SOURCE_INFORMED_INTERNAL_MARKERS),
        "malformed_german_response_count": sum(1 for item in findings if item["malformed_german_hits"]),
        "english_operational_wording_hit_count": sum(1 for item in findings if item["english_operational_hits"]),
        "utf8_german_marker_hit_count": sum(1 for item in findings if item["utf8_german_hits"]),
        "customer_facing_freigegeben_hit_count": sum(response.lower().count("freigegeben") for response in responses_after),
        "german_positive_unknown_runtime_signal_count": sum(1 for item in positive_required if item["runtime_decision"]["sales_difficulty"] == "unknown-runtime-signal"),
        "german_positive_response_language_mismatch_count": sum(1 for item in positive_required if item["runtime_decision"]["response_language"] != "de"),
        "source_traceability_source_count": len(ACCEPTED_SOURCES),
        "source_traceability_map_complete": len(ACCEPTED_SOURCES) == 11,
        "sales_script_sources_used": False,
        "legal_compliance_claim_made": False,
        "english_prod_045_regression_still_passed": read_json(PROD_045_RESULT).get("validation", {}).get("passed") is True,
        "german_prod_046a_regression_still_passed": read_json(PROD_046A_RESULT).get("validation", {}).get("passed") is True,
        "german_prod_046b_wording_regression_still_passed": read_json(PROD_046B_RESULT).get("validation", {}).get("passed") is True,
        "german_prod_046c_interpolation_guard_still_passed": read_json(PROD_046C_RESULT).get("validation", {}).get("passed") is True,
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
    before_rows = []
    for item in review_data["before_after"]:
        before_rows.append(
            "<tr>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['prod_046c_response'])}</td>"
            f"<td>{html.escape(item['prod_046d_response'])}</td>"
            f"<td>{html.escape(', '.join(item['source_informed_internal_hits_before']) or 'none')}</td>"
            f"<td>{html.escape(', '.join(item['source_informed_internal_hits_after']) or 'none')}</td>"
            "</tr>"
        )
    source_rows = []
    for source in review_data["source_traceability"]["accepted_sources"]:
        source_rows.append(
            "<tr>"
            f"<td>{html.escape(source['source_title'])}</td>"
            f"<td>{html.escape(source['source_type'])}</td>"
            f"<td><a href=\"{html.escape(source['url'])}\">{html.escape(source['url'])}</a></td>"
            f"<td>{html.escape(source['claim_supported'])}</td>"
            "</tr>"
        )
    finding_rows = []
    for item in review_data["response_findings"]:
        finding_rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(', '.join(item['source_informed_internal_hits']) or 'none')}</td>"
            f"<td>{html.escape(', '.join(item['malformed_german_hits']) or 'none')}</td>"
            f"<td>{html.escape(item['agent_response'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>PROD-046D German Source-Informed Wording Quality Guard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-046D German Source-Informed Wording Quality Guard</h1>
  <section class="summary">
    <h2>Summary</h2>
    <p>Source-informed cases: <code>{summary['german_source_informed_case_count']}</code></p>
    <p>Internal wording hits before/after: <code>{summary['source_informed_internal_hit_count_before']}</code> / <code>{summary['source_informed_internal_hit_count_after']}</code></p>
    <p>Customer-facing freigegeben hits: <code>{summary['customer_facing_freigegeben_hit_count']}</code></p>
    <p>Source traceability source count: <code>{summary['source_traceability_source_count']}</code></p>
    <p>Retrieval enabled: <code>false</code> | Provider calls: <code>false</code> | LLM used: <code>false</code></p>
  </section>
  <h2>Before / After</h2>
  <table><tr><th>Sales difficulty</th><th>PROD-046C</th><th>PROD-046D</th><th>Before hits</th><th>After hits</th></tr>{''.join(before_rows)}</table>
  <h2>Source Traceability</h2>
  <table><tr><th>Source</th><th>Type</th><th>URL</th><th>Claim supported</th></tr>{''.join(source_rows)}</table>
  <h2>Response Findings</h2>
  <table><tr><th>Case</th><th>Sales difficulty</th><th>Internal hits</th><th>Malformed hits</th><th>Agent response</th></tr>{''.join(finding_rows) or '<tr><td colspan="5">No findings.</td></tr>'}</table>
  <h2>Boundary Status</h2>
  <p>This checkpoint uses source-informed wording guidance only. It does not claim legal compliance and does not use sales scripts.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any], before_after: list[dict[str, Any]]) -> str:
    lines = [
        "# PROD-046D German Source-Informed Wording Quality Guard",
        "",
        "PROD-046D narrows German customer-facing runtime wording after PROD-046C. It uses GER-001 accepted sources as source-informed wording guidance only, not as legal-compliance evidence.",
        "",
        "The checkpoint rejects cold-call scripts and aggressive sales sources. It keeps retrieval, providers, LLM calls, private data, voice playback, public demo polish, payment collection, contract signing, and production promotion blocked.",
        "",
        "## Results",
        "",
        f"- German source-informed cases: {summary['german_source_informed_case_count']}",
        f"- German source-informed pass/fail: {summary['german_source_informed_pass_count']} / {summary['german_source_informed_fail_count']}",
        f"- Source-informed wording rewrites: {summary['source_informed_wording_rewrite_count']}",
        f"- Internal wording hits before: {summary['source_informed_internal_hit_count_before']}",
        f"- Internal wording hits after: {summary['source_informed_internal_hit_count_after']}",
        f"- Customer-facing `freigegeben` hits after: {summary['customer_facing_freigegeben_hit_count']}",
        f"- Source traceability source count: {summary['source_traceability_source_count']}",
        f"- English PROD-045 still passed: `{summary['english_prod_045_regression_still_passed']}`",
        f"- German PROD-046A still passed: `{summary['german_prod_046a_regression_still_passed']}`",
        f"- German PROD-046B still passed: `{summary['german_prod_046b_wording_regression_still_passed']}`",
        f"- German PROD-046C still passed: `{summary['german_prod_046c_interpolation_guard_still_passed']}`",
        "",
        "## Before / After",
        "",
    ]
    for item in before_after:
        if item["changed"]:
            lines.extend(
                [
                    f"### {item['sales_difficulty']}",
                    "",
                    f"- PROD-046C: {item['prod_046c_response']}",
                    f"- PROD-046D: {item['prod_046d_response']}",
                    "",
                ]
            )
    lines.extend(
        [
            "## Source Guidance",
            "",
            "- Accepted sources are official regulator, consumer-protection, public-service, and plain-language sources.",
            "- Rejected sources are sales guru blogs, cold-call scripts, aggressive closing scripts, affiliate SEO pages, and copied competitor wording.",
            "- The sources support wording style and safety posture only. PROD-046D does not claim legal compliance.",
            "",
            "## Campaign Field Shape Rules",
            "",
            "- Prefer full customer-facing sentence fields for identity, pricing, and verification responses.",
            "- Use noun phrase fields only when the template is explicitly written for a noun phrase.",
            "- Keep internal labels such as approved, route, boundary, campaign, or source status out of customer-facing German.",
            "- Use active verbs and short sentences before human review.",
            "",
            "## Remaining Wording Risks",
            "",
            "- German wording still needs human/product review by a German speaker.",
            "- This is a single-turn wording guard, not full conversation realism.",
            "- This is not a legal-compliance checkpoint.",
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
    for required in (PROD_045_RESULT, PROD_046A_RESULT, PROD_046B_RESULT, PROD_046C_RESULT):
        if not required.exists():
            raise SystemExit(f"Missing required source result: {rel(required)}")

    cases = build_source_informed_cases()
    results = run_source_informed_cases(cases)
    findings = collect_response_findings(results)
    before_after = build_before_after(results)
    traceability = source_map()
    summary = build_summary(cases, results, findings, before_after)

    passed = (
        summary["german_source_informed_fail_count"] == 0
        and summary["source_informed_internal_hit_count_after"] == 0
        and summary["malformed_german_response_count"] == 0
        and summary["english_operational_wording_hit_count"] == 0
        and summary["utf8_german_marker_hit_count"] == 0
        and summary["customer_facing_freigegeben_hit_count"] == 0
        and summary["source_traceability_map_complete"]
        and summary["english_prod_045_regression_still_passed"]
        and summary["german_prod_046a_regression_still_passed"]
        and summary["german_prod_046b_wording_regression_still_passed"]
        and summary["german_prod_046c_interpolation_guard_still_passed"]
    )

    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "source_informed_internal_markers": SOURCE_INFORMED_INTERNAL_MARKERS,
        "before_after": before_after,
        "response_findings": findings,
        "source_traceability": traceability,
        "source_informed_results": results,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_ids": [
            "GER-001-german-customer-facing-wording-source-audit",
            "PROD-045-core-sales-policy-regression-rerun",
            "PROD-046A-german-naturalized-policy-regression",
            "PROD-046B-german-response-wording-quality-pass",
            "PROD-046C-german-campaign-field-interpolation-guard",
        ],
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "german_source_informed_before_after": rel(OUT_DIR / "german_source_informed_before_after.json"),
            "german_source_informed_results": rel(OUT_DIR / "german_source_informed_results.json"),
            "german_source_informed_review_data": rel(OUT_DIR / "german_source_informed_review_data.json"),
            "german_source_informed_review_html": rel(OUT_DIR / "german_source_informed_review.html"),
            "source_traceability_map": rel(OUT_DIR / "source_traceability_map.json"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }

    write_json(OUT_DIR / "german_source_informed_results.json", {"items": results})
    write_json(OUT_DIR / "german_source_informed_before_after.json", {"items": before_after})
    write_json(OUT_DIR / "german_source_informed_review_data.json", review_data)
    write_text(OUT_DIR / "german_source_informed_review.html", render_html(review_data))
    write_json(OUT_DIR / "source_traceability_map.json", traceability)
    write_text(OUT_DIR / "report.md", build_report(summary, before_after))
    write_json(OUT_DIR / "result.json", result)

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": passed}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
