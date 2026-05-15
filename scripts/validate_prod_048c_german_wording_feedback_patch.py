#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from prod_046a_german_naturalized_policy_regression import GERMAN_CAMPAIGN
from run_realtime_turn_simulation import build_runtime_decision


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048C-german-wording-feedback-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

PATCHED_PRICE = "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich."
OLD_PAYMENT_SENTENCE = "In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_048c_german_wording_feedback_patch.py",
    "runner": ROOT / "scripts" / "run_prod_048c_german_wording_feedback_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_048c_german_wording_feedback_patch.py",
    "doc": ROOT / "docs" / "product" / "PROD_048C_GERMAN_WORDING_FEEDBACK_PATCH.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "before_after": OUT_DIR / "price_feedback_patch_before_after.json",
    "patch_results": OUT_DIR / "price_feedback_patch_results.json",
    "safety": OUT_DIR / "safety_boundary_preservation_results.json",
    "review_html": OUT_DIR / "prod_048c_review.html",
    "followup_html": OUT_DIR / "native_german_followup_review.html",
    "followup_packet": OUT_DIR / "native_german_followup_review_packet.json",
    "readme_de": OUT_DIR / "native_german_followup_review_readme_de.md",
    "table_csv": OUT_DIR / "native_german_followup_review_table.csv",
    "export_schema": OUT_DIR / "native_german_followup_review_export_schema.json",
}

DEPENDENCY_RESULTS = {
    "prod_048b": ROOT / "research" / "experiments" / "generated" / "PROD-048B-native-german-review-import" / "result.json",
    "prod_048a": ROOT / "research" / "experiments" / "generated" / "PROD-048A-german-review-html-and-brevity-packet" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
}

BOUNDARY_FALSE_FIELDS = [
    "full_native_german_approval_claimed",
    "legal_compliance_claimed",
    "runtime_policy_changed",
    "call_control_behavior_changed",
    "customer_move_classification_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
]

REQUIRED_GERMAN_LABELS = [
    "Prüfung deutscher Telefonantworten",
    "Erneut prüfen",
    "Bereits teilweise geprüft",
    "Noch nicht geprüft",
    "Thema",
    "Kundensätze",
    "Antwort des Assistenten",
    "Passt diese Antwort zu allen Kundensätzen?",
    "Klingt natürlich?",
    "Ist die Antwort klar verständlich?",
    "Bewertung als JSON herunterladen",
    "Bewertung als CSV herunterladen",
    "Bewertung aus JSON laden",
    "Zwischenstand im Browser speichern",
    "Zwischenstand laden",
    "Alle Eingaben löschen",
    "Druckansicht",
]

VISIBLE_FORBIDDEN_TERMS = [
    "sales_difficulty",
    "call_control",
    "runtime",
    "checkpoint",
    "regression",
    "policy surface",
    "campaign field",
    "validator",
    "synthetic",
    "provider",
    "llm",
]


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth and data.strip():
            self.parts.append(data.strip())


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def visible_text(html_text: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html_text)
    return "\n".join(parser.parts)


def runtime_decision_for(transcript: str, case_id: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": case_id,
            "customer_input": {
                "input_type": "speech",
                "stage": "early_call",
                "transcript": transcript,
            },
        },
        campaign=GERMAN_CAMPAIGN,
    )


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_dependency_results() -> None:
    for key, path in DEPENDENCY_RESULTS.items():
        payload = read_json(path)
        assert_condition(payload.get("validation", {}).get("passed") is True, f"{key} must pass")


def validate_runtime_price_patch() -> None:
    decision = runtime_decision_for("Was kostet mich das denn?", "validate-prod-048c-price")
    response = decision["agent_response"]
    assert_condition(decision["response_language"] == "de", decision)
    assert_condition(decision["sales_difficulty"] == "price-first-direct", decision)
    assert_condition(decision["call_control"] in {"end-call", "bridge-then-continue"}, decision)
    assert_condition(response.startswith(PATCHED_PRICE), response)
    assert_condition("29 Euro" in response, response)
    assert_condition("schriftlich" in response.lower(), response)
    assert_condition(OLD_PAYMENT_SENTENCE not in response, response)
    assert_condition("Vertragsabschluss" not in response, response)


def validate_result_summary() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["price_first_wording_patched"] is True, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["runtime_behavior_change_scope"] == "german_plain_price_first_wording_only", summary)
    assert_condition(summary["followup_group_count"] == 22, summary)
    assert_condition(summary["original_german_case_count"] == 99, summary)
    assert_condition(summary["erneut_pruefen_group_count"] == 1, summary)
    assert_condition(summary["bereits_teilweise_geprueft_group_count"] >= 4, summary)
    assert_condition(summary["noch_nicht_geprueft_group_count"] > 0, summary)
    assert_condition(summary["safety_boundary_preservation_passed"] is True, summary)
    assert_condition(summary["json_import_enabled"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return summary


def validate_patch_artifacts() -> None:
    before_after = read_json(REQUIRED_FILES["before_after"])["items"]
    patch_results = read_json(REQUIRED_FILES["patch_results"])["items"]
    safety = read_json(REQUIRED_FILES["safety"])["items"]
    assert_condition(before_after, "before/after evidence required")
    price = next(item for item in before_after if item["customer_move_id"] == "price_first")
    assert_condition(OLD_PAYMENT_SENTENCE in price["before_response"], price)
    assert_condition(price["after_response"] == PATCHED_PRICE, price)
    assert_condition(OLD_PAYMENT_SENTENCE not in price["after_response"], price)
    assert_condition(all(item["passed"] is True for item in patch_results), patch_results)
    assert_condition(any(item["case_id"] == "prod-048c-price-first" for item in patch_results), patch_results)
    assert_condition(all(item["passed"] is True for item in safety), safety)
    by_move = {item["customer_move_id"]: item for item in safety}
    for move_id in ("payment_safety_fear", "scam_or_card_fear", "sale_ready_interest"):
        assert_condition(move_id in by_move, by_move)
    assert_condition("zahlungsdaten" in by_move["payment_safety_fear"]["agent_response"].lower(), by_move["payment_safety_fear"])
    assert_condition("passw" in by_move["scam_or_card_fear"]["agent_response"].lower(), by_move["scam_or_card_fear"])
    assert_condition("vertragsunterzeichnung" in by_move["sale_ready_interest"]["agent_response"].lower(), by_move["sale_ready_interest"])


def validate_followup_packet() -> None:
    packet = read_json(REQUIRED_FILES["followup_packet"])
    groups = packet["review_groups"]
    assert_condition(len(groups) == 22, len(groups))
    represented_cases = []
    for group in groups:
        represented_cases.extend(group["original_case_ids"])
        assert_condition(group["customer_utterances"], group)
        assert_condition(group["agent_response"], group)
        assert_condition(group["status_de"] in {"Erneut prüfen", "Bereits teilweise geprüft", "Noch nicht geprüft"}, group)
        assert_condition(group["native_german_approval_claimed"] is False, group)
        assert_condition(group["legal_compliance_claimed"] is False, group)
    assert_condition(len(represented_cases) == 99, len(represented_cases))
    assert_condition(len(set(represented_cases)) == 99, "case ids must be unique across groups")
    price_group = next(group for group in groups if group["topic_title_de"] == "Preisfrage")
    assert_condition(price_group["status_de"] == "Erneut prüfen", price_group)
    assert_condition(price_group["agent_response"] == PATCHED_PRICE, price_group)
    assert_condition(OLD_PAYMENT_SENTENCE not in price_group["agent_response"], price_group)
    accepted_statuses = {group["topic_title_de"]: group["status_de"] for group in groups if group["status_de"] == "Bereits teilweise geprüft"}
    for topic in ("Wer ruft an?", "Schriftliche Informationen", "Nur E-Mail"):
        assert_condition(accepted_statuses.get(topic) == "Bereits teilweise geprüft", accepted_statuses)
    assert_condition(any(group["status_de"] == "Noch nicht geprüft" for group in groups), groups)
    assert_condition(packet["review_boundary"]["full_native_german_approval_claimed"] is False, packet)
    assert_condition(packet["review_boundary"]["legal_compliance_claimed"] is False, packet)


def validate_followup_html() -> None:
    html_text = REQUIRED_FILES["followup_html"].read_text(encoding="utf-8")
    text = visible_text(html_text)
    lowered = text.lower()
    assert_condition("<script src=" not in html_text.lower(), "external script not allowed")
    assert_condition("<link" not in html_text.lower(), "external CSS not allowed")
    for label in REQUIRED_GERMAN_LABELS:
        assert_condition(label in text, f"missing German label: {label}")
    for term in VISIBLE_FORBIDDEN_TERMS:
        assert_condition(term not in lowered, f"visible technical term found: {term}")
    assert_condition(PATCHED_PRICE in text, "patched price response missing")
    assert_condition(OLD_PAYMENT_SENTENCE not in text, "old payment sentence visible in follow-up HTML")
    assert_condition("Diese Antwort wurde nach der ersten Rückmeldung gekürzt" in text, "price note missing")
    assert_condition("downloadJson" in html_text and "downloadCsv" in html_text, "export functions missing")
    assert_condition("importJsonFile" in html_text and "FileReader" in html_text, "JSON import function missing")
    assert_condition('id="jsonImportFile"' in html_text, "JSON import file input missing")
    assert_condition("localStorage" in html_text, "localStorage save/load missing")
    card_count = len(re.findall(r'class="review-card"', html_text))
    assert_condition(card_count == 22, f"expected 22 grouped cards, found {card_count}")


def validate_docs() -> None:
    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    readme = REQUIRED_FILES["readme_de"].read_text(encoding="utf-8")
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8")
    for text in (doc, report):
        assert_condition("No full native German approval is claimed" in text, text[:500])
        assert_condition("No legal compliance is claimed" in text, text[:500])
    for marker in ("erste Rückmeldung", "Preisantwort", "nicht um eine Rechtsprüfung", "Bewertung aus JSON laden", "JSON", "CSV"):
        assert_condition(marker in readme, f"README missing {marker}")


def main() -> None:
    validate_required_files()
    validate_dependency_results()
    validate_runtime_price_patch()
    summary = validate_result_summary()
    validate_patch_artifacts()
    validate_followup_packet()
    validate_followup_html()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
