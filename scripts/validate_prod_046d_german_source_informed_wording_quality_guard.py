#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046D-german-source-informed-wording-quality-guard"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_046d_german_source_informed_wording_quality_guard.py",
    "runner": ROOT / "scripts" / "run_prod_046d_german_source_informed_wording_quality_guard.py",
    "validator": ROOT / "scripts" / "validate_prod_046d_german_source_informed_wording_quality_guard.py",
    "doc": ROOT / "docs" / "product" / "PROD_046D_GERMAN_SOURCE_INFORMED_WORDING_QUALITY_GUARD.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "before_after": OUT_DIR / "german_source_informed_before_after.json",
    "results": OUT_DIR / "german_source_informed_results.json",
    "review_data": OUT_DIR / "german_source_informed_review_data.json",
    "review_html": OUT_DIR / "german_source_informed_review.html",
    "source_traceability": OUT_DIR / "source_traceability_map.json",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
    "prod_046a_result": ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json",
    "prod_046b_result": ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json",
    "prod_046c_result": ROOT / "research" / "experiments" / "generated" / "PROD-046C-german-campaign-field-interpolation-guard" / "result.json",
    "reference_registry": ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "decision_log": ROOT / "docs" / "thesis" / "DECISION_LOG.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
}

BOUNDARY_FALSE_FIELDS = [
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "sales_script_sources_used",
    "legal_compliance_claim_made",
]

DISALLOWED_RESPONSE_MARKERS = [
    "freigegeben",
    "vertriebsteil",
    "verkaufspfad",
    "rückrufwunsch dokumentieren",
    "dokumentiere einen rückruf",
    "dokumentiere einen follow-up",
    "kampagnenregeln",
    "compliance-zusagen",
    "pauschalen compliance",
    "sale-ready",
    "support-warteschlange",
    "kündigungs-warteschlange",
    "sichere passungsfrage",
    "überlegenheitsaussage",
    "unknown-runtime-signal",
    "support queue",
    "specialist route",
    "approved specialist path",
    "payment details",
    "contract signing",
    "follow-up",
    "callback",
    "campaign",
    "Ãƒ",
    "Ã‚",
    "fuer",
    "Rueckruf",
    "naechst",
    "pruef",
]

EXPECTED_SOURCE_URLS = [
    "https://www.bundesnetzagentur.de/DE/Vportal/TK/Aerger/Faelle/UEW/start.html",
    "https://www.verbraucherzentrale.de/wissen/vertraege-reklamation/werbung/ungewollte-werbeanrufe-hilfe-gegen-telefonwerbung-13857",
    "https://www.verbraucherzentrale.de/wissen/digitale-welt/mobilfunk-und-festnetz/abzocke-am-telefon-moeglichst-nicht-ja-sagen-13496",
    "https://www.verbraucherzentrale.de/wissen/vertraege-reklamation/abzocke/unerwarteter-anruf-von-der-verbraucherzentrale-vorsicht-falle-11112",
    "https://www.polizei-beratung.de/themen-und-tipps/sicher-handeln/onlinebetrug-maschen/fake-kundenservice-support-scams/",
    "https://www.polizei-beratung.de/themen-und-tipps/betrug/betrug-durch-falsche-polizisten/",
    "https://servicestandard.gov.de/handbuch/anleitungen/verstaendlich-schreiben-mit-einfacher-sprache/",
    "https://www.afz.bremen.de/verwaltung-nbspentwickeln/buerger-innenservice-und-kommunikation/kommunikation/verstaendliche-sprache-25926",
    "https://www.berlin.de/lb/digitale-barrierefreiheit/anforderungen/berliner-standards/fuer-verstaendliche-sprache-1463990.php",
    "https://www.verbraucherzentrale.de/wissen/energie/achtung-unerwuenschte-energievertraege-am-telefon-58483",
    "https://www.verbraucherzentrale.de/vertraege-reklamation/hilfe-bei-werbeanrufen-100996",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def contains_marker(text: str, markers: list[str]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker.lower() in lowered]


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_source_results() -> None:
    for key in ("prod_045_result", "prod_046a_result", "prod_046b_result", "prod_046c_result"):
        result = read_json(REQUIRED_FILES[key])
        assert_condition(result.get("validation", {}).get("passed") is True, f"{key} must pass")


def validate_summary() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["german_source_informed_case_count"] > 0, summary)
    assert_condition(summary["german_source_informed_fail_count"] == 0, summary)
    assert_condition(summary["source_informed_wording_rewrite_count"] >= 8, summary)
    assert_condition(summary["source_informed_internal_hit_count_before"] > 0, summary)
    assert_condition(summary["source_informed_internal_hit_count_after"] == 0, summary)
    assert_condition(summary["malformed_german_response_count"] == 0, summary)
    assert_condition(summary["english_operational_wording_hit_count"] == 0, summary)
    assert_condition(summary["utf8_german_marker_hit_count"] == 0, summary)
    assert_condition(summary["customer_facing_freigegeben_hit_count"] == 0, summary)
    assert_condition(summary["source_traceability_source_count"] == len(EXPECTED_SOURCE_URLS), summary)
    assert_condition(summary["source_traceability_map_complete"] is True, summary)
    assert_condition(summary["english_prod_045_regression_still_passed"] is True, summary)
    assert_condition(summary["german_prod_046a_regression_still_passed"] is True, summary)
    assert_condition(summary["german_prod_046b_wording_regression_still_passed"] is True, summary)
    assert_condition(summary["german_prod_046c_interpolation_guard_still_passed"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return summary


def validate_results() -> None:
    results = read_json(REQUIRED_FILES["results"])["items"]
    assert_condition(results, "missing source-informed results")
    for item in results:
        decision = item["runtime_decision"]
        response = decision["agent_response"]
        assert_condition(item["passed"] is True, item)
        assert_condition(decision["response_language"] == "de", item)
        hits = contains_marker(response, DISALLOWED_RESPONSE_MARKERS)
        assert_condition(not hits, f"disallowed response markers {hits} in {item['case_id']}: {response}")


def validate_before_after() -> None:
    items = read_json(REQUIRED_FILES["before_after"])["items"]
    assert_condition(items, "missing before/after evidence")
    assert_condition(any(item["source_informed_internal_hits_before"] for item in items), "before examples must show internal wording risk")
    for item in items:
        assert_condition(not item["source_informed_internal_hits_after"], item)
        assert_condition(not item["malformed_hits_after"], item)


def validate_source_traceability() -> None:
    traceability = read_json(REQUIRED_FILES["source_traceability"])
    boundary = traceability["source_use_boundary"]
    assert_condition(boundary["source_informed_wording_guidance_only"] is True, boundary)
    assert_condition(boundary["legal_compliance_claim"] is False, boundary)
    assert_condition(boundary["uses_source_quotes"] is False, boundary)
    assert_condition(boundary["copies_source_wording"] is False, boundary)
    assert_condition(boundary["uses_sales_scripts"] is False, boundary)
    urls = [source["url"] for source in traceability["accepted_sources"]]
    assert_condition(sorted(urls) == sorted(EXPECTED_SOURCE_URLS), urls)
    for source in traceability["accepted_sources"]:
        assert_condition(source["source_quote"] is False, source)
        assert_condition(source["copied_source_text"] is False, source)
        assert_condition(source["reuse_decision"] in {"accept", "background only"}, source)


def validate_docs() -> None:
    registry = REQUIRED_FILES["reference_registry"].read_text(encoding="utf-8")
    methodology = REQUIRED_FILES["methodology_log"].read_text(encoding="utf-8").lower()
    decision = REQUIRED_FILES["decision_log"].read_text(encoding="utf-8").lower()
    roadmap = REQUIRED_FILES["roadmap"].read_text(encoding="utf-8").lower()
    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8").lower()
    html = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    for url in EXPECTED_SOURCE_URLS:
        assert_condition(url in registry, f"source URL missing from registry: {url}")
    assert_condition("prod-046d" in methodology and "source-informed" in methodology, "methodology log missing PROD-046D source-informed entry")
    assert_condition("sales scripts" in methodology and "rejected" in methodology, "methodology log must record rejection of sales scripts")
    assert_condition("german runtime wording" in decision and "sales scripts" in decision, "decision log missing German wording source decision")
    assert_condition("prod-046d" in roadmap and "prod-046-core-sales-policy-human-review" in roadmap, "roadmap missing PROD-046D / next checkpoint")
    for marker in ("source-informed wording guidance", "not legal compliance", "sales scripts"):
        assert_condition(marker in doc or marker in report or marker in html, f"missing {marker}")


def main() -> None:
    validate_required_files()
    validate_source_results()
    summary = validate_summary()
    validate_results()
    validate_before_after()
    validate_source_traceability()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
